"""Feature: uploading media, end to end.

The failure this file exists to prevent is the one it was written after: every
piece of the upload path looked present — a `multipart/form-data` form, a
`multiple` file input, a `Media` model with a `FileField`, a `MediaSerializer`
— and none of them were connected. The form posted files to a view that never
read `request.FILES`, into a project with no `MEDIA_ROOT` to write them to and
no URL to serve them from. Nothing raised. The upload just went nowhere.

So these tests assert the whole path rather than any one link of it: the file
is stored, the row exists, the page renders a `<img src>` that points at
MEDIA_URL, and the API can do the same thing the page can.
"""

import shutil
import tempfile

from django.conf import settings
from django.contrib.auth.models import User
from django.core.exceptions import ValidationError
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase, override_settings
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase

from .models import Media, Post
from .services import attach_media
from .validators import MAX_BYTES, MAX_FILES, kind_for, validate_uploads


# Uploads in tests are real files on a real disk. A temporary MEDIA_ROOT keeps
# them out of the developer's working copy and lets the class delete the lot.
MEDIA_ROOT = tempfile.mkdtemp(prefix="palshare-test-media-")


def a_file(name="shot.png", size=12, content_type="image/png"):
    return SimpleUploadedFile(name, b"x" * size, content_type=content_type)


@override_settings(MEDIA_ROOT=MEDIA_ROOT)
class MediaUploadTests(TestCase):

    @classmethod
    def tearDownClass(cls):
        shutil.rmtree(MEDIA_ROOT, ignore_errors=True)
        super().tearDownClass()

    def setUp(self):
        self.user = User.objects.create_user("kaushal", password="pw")
        self.client.force_login(self.user)

    def post_to_create(self, **data):
        return self.client.post(reverse("palshare:post-create"), data)

    # --- the settings the whole thing rests on ------------------------------

    def test_media_root_and_url_are_configured(self):
        # Without these a FileField writes into the current working directory
        # and `.url` raises. Both are silent until something reads them.
        self.assertTrue(settings.MEDIA_URL)
        self.assertTrue(str(settings.MEDIA_ROOT))
        self.assertTrue(settings.MEDIA_URL.endswith("/"))

    # --- the page -----------------------------------------------------------

    def test_creating_a_post_with_a_file_stores_it(self):
        response = self.post_to_create(text="hour three", media=a_file())

        post = Post.objects.get()
        self.assertRedirects(response, reverse("palshare:post-detail", args=[post.pk]))
        media = post.media.get()
        self.assertEqual(media.kind, "image")
        # Stored under the model's upload_to, and readable back off disk.
        self.assertTrue(media.file.name.startswith("posts/"))
        with media.file.open("rb") as handle:
            self.assertEqual(handle.read(), b"x" * 12)

    def test_all_four_files_are_stored_not_just_the_last(self):
        # `request.FILES["media"]` returns one file for a `multiple` input.
        # This is the test that catches the dict access.
        response = self.post_to_create(
            text="four", media=[a_file(f"{i}.png") for i in range(4)])

        self.assertEqual(Post.objects.get().media.count(), 4)
        self.assertEqual(response.status_code, 302)

    def test_a_video_is_stored_as_a_video(self):
        self.post_to_create(text="clip", media=a_file("demo.mp4", content_type="video/mp4"))
        self.assertEqual(Post.objects.get().media.get().kind, "video")

    def test_a_file_with_no_caption_is_still_a_post(self):
        self.post_to_create(text="", media=a_file())
        self.assertEqual(Post.objects.count(), 1)

    def test_an_empty_post_is_still_rejected(self):
        response = self.post_to_create(text="")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(Post.objects.count(), 0)

    def test_a_rejected_file_leaves_no_post_behind(self):
        response = self.post_to_create(text="here you go", media=a_file("payload.svg"))

        self.assertEqual(response.status_code, 200)
        # Not "the post exists without its file" — the whole write is undone.
        self.assertEqual(Post.objects.count(), 0)
        self.assertEqual(Media.objects.count(), 0)
        self.assertContains(response, "payload.svg")

    def test_one_bad_file_in_four_stores_none_of_them(self):
        self.post_to_create(text="mixed",
                            media=[a_file("ok.png"), a_file("bad.exe"),
                                   a_file("fine.jpg"), a_file("also.png")])
        self.assertEqual(Media.objects.count(), 0)

    def test_editing_a_post_adds_files_and_keeps_the_old_ones(self):
        self.post_to_create(text="first", media=a_file("one.png"))
        post = Post.objects.get()

        self.client.post(reverse("palshare:post-edit", args=[post.pk]),
                         {"text": "first", "media": a_file("two.png")})

        self.assertEqual(post.media.count(), 2)

    def test_editing_cannot_push_a_post_past_the_file_limit(self):
        self.post_to_create(text="three", media=[a_file(f"{i}.png") for i in range(3)])
        post = Post.objects.get()

        self.client.post(reverse("palshare:post-edit", args=[post.pk]),
                         {"text": "three", "media": [a_file("d.png"), a_file("e.png")]})

        self.assertEqual(post.media.count(), 3)

    def test_the_feed_renders_the_file_and_not_the_placeholder(self):
        self.post_to_create(text="rendered", media=a_file())

        response = self.client.get(reverse("palshare:feed"))

        html = response.content.decode()
        self.assertIn(settings.MEDIA_URL + "posts/", html)
        self.assertIn("<img class=\"media-item\"", html)
        self.assertNotIn("media-placeholder", html)

    # --- the rules, on their own --------------------------------------------

    def test_kind_is_read_from_the_extension_case_insensitively(self):
        self.assertEqual(kind_for("HOLIDAY.JPG"), "image")
        self.assertEqual(kind_for("clip.MOV"), "video")
        self.assertIsNone(kind_for("notes"))

    def test_a_content_type_header_does_not_make_a_file_allowed(self):
        # The browser sends content_type, so the caller sends it. Claiming
        # image/png over a .exe must not get the file written.
        with self.assertRaises(ValidationError):
            validate_uploads([a_file("shell.exe", content_type="image/png")])

    def test_a_file_over_the_size_cap_is_rejected(self):
        with self.assertRaises(ValidationError) as caught:
            validate_uploads([a_file("huge.png", size=MAX_BYTES + 1)])
        self.assertIn("limit", caught.exception.messages[0])

    def test_every_bad_file_is_reported_not_only_the_first(self):
        with self.assertRaises(ValidationError) as caught:
            validate_uploads([a_file("a.exe"), a_file("b.sh")])
        self.assertEqual(len(caught.exception.messages), 2)

    def test_more_than_the_limit_is_rejected_as_a_batch(self):
        with self.assertRaises(ValidationError):
            validate_uploads([a_file(f"{i}.png") for i in range(MAX_FILES + 1)])

    def test_attach_media_with_nothing_to_attach_is_a_no_op(self):
        post = Post.objects.create(author=self.user, text="text only")
        self.assertEqual(attach_media(post, []), [])
        self.assertEqual(post.media.count(), 0)

    def test_a_traversing_file_name_does_not_escape_media_root(self):
        # Django's own `validate_file_name` handles this; the test is here so
        # that a future change to upload_to cannot quietly remove it.
        self.post_to_create(text="nice try", media=a_file("../../escaped.png"))
        media = Media.objects.get()
        self.assertNotIn("..", media.file.name)


@override_settings(MEDIA_ROOT=MEDIA_ROOT)
class MediaAPITests(APITestCase):
    """The API uploads through the same `services.attach_media` as the page."""

    @classmethod
    def tearDownClass(cls):
        shutil.rmtree(MEDIA_ROOT, ignore_errors=True)
        super().tearDownClass()

    def setUp(self):
        self.user = User.objects.create_user("ranjan", password="pw")
        self.client.force_authenticate(self.user)
        self.url = reverse("palshare-api:post-list")

    def test_a_post_can_be_created_with_files(self):
        response = self.client.post(
            self.url, {"text": "from the api", "upload": [a_file(), a_file("b.png")]},
            format="multipart")

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(len(response.data["media"]), 2)
        self.assertEqual(Post.objects.get().media.count(), 2)

    def test_the_response_carries_a_usable_url(self):
        response = self.client.post(
            self.url, {"text": "url please", "upload": a_file()}, format="multipart")

        self.assertIn(settings.MEDIA_URL, response.data["media"][0]["file"])

    def test_a_rejected_file_is_a_400_and_not_a_500(self):
        response = self.client.post(
            self.url, {"text": "nope", "upload": a_file("script.js")}, format="multipart")

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("upload", response.data)
        self.assertEqual(Post.objects.count(), 0)

    def test_a_post_without_files_still_works(self):
        response = self.client.post(self.url, {"text": "text only"}, format="json")
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

    def test_upload_is_write_only(self):
        self.client.post(self.url, {"text": "x", "upload": a_file()}, format="multipart")
        response = self.client.get(self.url)
        self.assertNotIn("upload", response.data["results"][0])
