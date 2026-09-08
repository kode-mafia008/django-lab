"""The six things QA reported after the media upload landed.

Four of them were features that had never been built and two were defects in
features that had. They are tested together because they were reported
together, and because the pattern behind four of them is the same one: a
control that exists in the markup and nothing behind it. That pattern is what
this file is really guarding against.
"""

import shutil
import tempfile
from unittest.mock import patch

from django.contrib.auth.models import User
from django.core.exceptions import ValidationError
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase, override_settings
from django.urls import reverse
from rest_framework.test import APIClient

from .models import Conversation, Follow, Like, Message, Post, Profile, Reaction
from .services import edit_message, set_avatar, set_reaction, unsend_message

MEDIA_ROOT = tempfile.mkdtemp(prefix="palshare-social-media-")


def an_image(name="face.png"):
    return SimpleUploadedFile(name, b"x" * 16, content_type="image/png")


class SocialTestCase(TestCase):
    def setUp(self):
        self.me = User.objects.create_user("bello", password="pw", first_name="Bello",
                                           last_name="Ferrante")
        self.other = User.objects.create_user("asha", password="pw", first_name="Asha",
                                              last_name="Kandel")
        Profile.objects.create(user=self.me)
        Profile.objects.create(user=self.other, bio="Ships things on Fridays")
        self.client.force_login(self.me)


# --- 1. reaching other people's profiles ----------------------------------

class ProfileAccessTests(SocialTestCase):

    def test_another_persons_profile_opens(self):
        response = self.client.get(reverse("palshare:profile", args=["asha"]))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Asha")

    def test_a_profile_opens_for_a_user_who_has_no_profile_row(self):
        # Anyone created by `createsuperuser`, the admin or a fixture — which
        # in a workshop database is most people.
        User.objects.create_user("kaushal", password="pw")
        response = self.client.get(reverse("palshare:profile", args=["kaushal"]))
        self.assertEqual(response.status_code, 200)

    def test_the_followers_and_following_links_go_to_different_tabs(self):
        """They were the same bare URL, and `connections` defaults to
        followers — so "following" showed you followers."""
        body = self.client.get(reverse("palshare:profile", args=["asha"])).content.decode()
        base = reverse("palshare:connections", args=["asha"])
        self.assertIn(f'href="{base}?tab=followers"', body)
        self.assertIn(f'href="{base}?tab=following"', body)

    def test_the_following_tab_lists_who_they_follow(self):
        third = User.objects.create_user("menuka", password="pw")
        Follow.objects.create(follower=self.other, following=third)

        body = self.client.get(reverse("palshare:connections", args=["asha"]),
                               {"tab": "following"}).content.decode()

        self.assertIn("menuka", body)

    def test_the_media_tab_shows_only_posts_with_files(self):
        Post.objects.create(author=self.other, text="just words")
        with_media = Post.objects.create(author=self.other, text="with a picture")
        with_media.media.create(file="posts/x.png", kind="image")

        body = self.client.get(reverse("palshare:profile", args=["asha"]),
                               {"tab": "media"}).content.decode()

        self.assertIn("with a picture", body)
        self.assertNotIn("just words", body)

    def test_the_media_tab_shows_a_post_once_per_post_not_once_per_file(self):
        post = Post.objects.create(author=self.other, text="three files")
        for i in range(3):
            post.media.create(file=f"posts/{i}.png", kind="image")

        body = self.client.get(reverse("palshare:profile", args=["asha"]),
                               {"tab": "media"}).content.decode()

        self.assertEqual(body.count("three files"), 1)

    def test_the_likes_tab_shows_what_they_liked(self):
        mine = Post.objects.create(author=self.me, text="they liked this")
        Like.objects.create(user=self.other, post=mine)
        Post.objects.create(author=self.other, text="their own post")

        body = self.client.get(reverse("palshare:profile", args=["asha"]),
                               {"tab": "likes"}).content.decode()

        self.assertIn("they liked this", body)
        self.assertNotIn("their own post", body)

    def test_the_active_tab_follows_the_url(self):
        body = self.client.get(reverse("palshare:profile", args=["asha"]),
                               {"tab": "likes"}).content.decode()
        self.assertIn('class="tab tab-active" href="?tab=likes"', body)

    def test_an_invented_tab_falls_back_to_posts(self):
        response = self.client.get(reverse("palshare:profile", args=["asha"]),
                                   {"tab": "../../etc/passwd"})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context["tab"], "posts")

    def test_a_private_account_still_hides_its_posts_on_every_tab(self):
        self.other.profile.is_private = True
        self.other.profile.save()
        Post.objects.create(author=self.other, text="secret")

        for tab in ("posts", "media", "likes"):
            body = self.client.get(reverse("palshare:profile", args=["asha"]),
                                   {"tab": tab}).content.decode()
            self.assertNotIn("secret", body)
            self.assertIn("This account is private", body)


# --- 2. messages you can take back ----------------------------------------

class MessageEditTests(SocialTestCase):
    def setUp(self):
        super().setUp()
        self.conversation = Conversation.objects.create()
        self.conversation.participants.add(self.me, self.other)
        self.mine = Message.objects.create(conversation=self.conversation,
                                           sender=self.me, text="ment to say this")
        self.theirs = Message.objects.create(conversation=self.conversation,
                                             sender=self.other, text="their words")

    def edit(self, message, text):
        return self.client.post(reverse("palshare:message-edit", args=[message.pk]),
                                {"text": text})

    def unsend(self, message):
        return self.client.post(reverse("palshare:message-unsend", args=[message.pk]))

    def test_editing_changes_the_text_and_stamps_it(self):
        self.edit(self.mine, "meant to say this")
        self.mine.refresh_from_db()
        self.assertEqual(self.mine.text, "meant to say this")
        self.assertIsNotNone(self.mine.edited_at)

    def test_an_edited_message_says_so_in_the_thread(self):
        self.edit(self.mine, "fixed")
        body = self.client.get(reverse("palshare:thread",
                                       args=[self.conversation.pk])).content.decode()
        self.assertIn("· edited", body)

    def test_you_cannot_edit_somebody_elses_message(self):
        self.edit(self.theirs, "words I put in their mouth")
        self.theirs.refresh_from_db()
        self.assertEqual(self.theirs.text, "their words")

    def test_unsending_removes_the_text_from_the_database(self):
        self.unsend(self.mine)
        self.mine.refresh_from_db()
        # Not hidden in the template — gone. A message the server still stores
        # is not unsent.
        self.assertEqual(self.mine.text, "")
        self.assertTrue(self.mine.is_deleted)

    def test_an_unsent_message_keeps_its_place_in_the_thread(self):
        self.unsend(self.mine)
        body = self.client.get(reverse("palshare:thread",
                                       args=[self.conversation.pk])).content.decode()
        self.assertIn("This message was unsent.", body)
        self.assertNotIn("ment to say this", body)

    def test_you_cannot_unsend_somebody_elses_message(self):
        self.unsend(self.theirs)
        self.theirs.refresh_from_db()
        self.assertEqual(self.theirs.text, "their words")

    def test_unsending_twice_is_not_an_error(self):
        self.unsend(self.mine)
        response = self.unsend(self.mine)
        self.assertEqual(response.status_code, 302)

    def test_an_unsent_message_cannot_be_edited_back_into_existence(self):
        unsend_message(self.me, self.mine)
        with self.assertRaises(ValidationError):
            edit_message(self.me, self.mine, "back from the dead")

    def test_an_edit_cannot_be_used_to_empty_a_message(self):
        with self.assertRaises(ValidationError):
            edit_message(self.me, self.mine, "   ")

    def test_a_stranger_cannot_reach_a_message_at_all(self):
        stranger = User.objects.create_user("nosy", password="pw")
        self.client.force_login(stranger)
        response = self.unsend(self.mine)
        self.assertEqual(response.status_code, 404)

    def test_the_edit_form_opens_on_your_own_bubble_only(self):
        url = reverse("palshare:thread", args=[self.conversation.pk])
        body = self.client.get(url, {"edit": self.mine.pk}).content.decode()
        self.assertIn(f'action="{reverse("palshare:message-edit", args=[self.mine.pk])}"', body)

        body = self.client.get(url, {"edit": self.theirs.pk}).content.decode()
        self.assertNotIn("bubble-edit", body)

    def test_editing_refuses_a_get(self):
        response = self.client.get(reverse("palshare:message-edit", args=[self.mine.pk]))
        self.assertEqual(response.status_code, 405)


# --- 3. profile pictures ---------------------------------------------------

@override_settings(MEDIA_ROOT=MEDIA_ROOT)
class AvatarTests(SocialTestCase):

    @classmethod
    def tearDownClass(cls):
        shutil.rmtree(MEDIA_ROOT, ignore_errors=True)
        super().tearDownClass()

    def edit_profile(self, **extra):
        return self.client.post(reverse("palshare:profile-edit", args=["bello"]),
                                {"name": "Bello", "bio": "", **extra})

    def test_uploading_a_picture_stores_it(self):
        """The view read `request.POST` and never `request.FILES`, so this
        input was discarded on every save without a word."""
        self.edit_profile(avatar=an_image())
        self.assertTrue(Profile.objects.get(user=self.me).avatar)

    def test_the_picture_is_rendered_instead_of_the_initial(self):
        self.edit_profile(avatar=an_image())
        body = self.client.get(reverse("palshare:profile", args=["bello"])).content.decode()
        self.assertIn("avatars/", body)
        self.assertIn('class="avatar-img"', body)

    def test_your_own_picture_shows_in_the_header_and_the_composer(self):
        """`shell()` hand-built `current_user` with three of the four keys the
        avatar partial reads, so your own picture was the one avatar on the
        page that stayed an initial."""
        self.edit_profile(avatar=an_image())
        body = self.client.get(reverse("palshare:feed")).content.decode()
        header = body[:body.index('class="shell"')]
        self.assertIn("avatar-img", header)
        composer = body[body.index('class="composer"'):body.index("composer-body")]
        self.assertIn("avatar-img", composer)

    def test_it_shows_up_on_other_peoples_screens_too(self):
        self.edit_profile(avatar=an_image())
        self.client.force_login(self.other)
        body = self.client.get(reverse("palshare:profile", args=["bello"])).content.decode()
        self.assertIn("avatars/", body)

    def test_saving_without_a_new_picture_keeps_the_old_one(self):
        self.edit_profile(avatar=an_image())
        self.edit_profile(bio="changed my mind about the bio")
        self.assertTrue(Profile.objects.get(user=self.me).avatar)

    def test_someone_with_no_picture_still_gets_their_initial(self):
        body = self.client.get(reverse("palshare:profile", args=["asha"])).content.decode()
        self.assertNotIn('class="avatar-img"', body)
        self.assertIn(">\n\n  A\n\n<", body)

    def test_a_video_is_not_a_profile_picture(self):
        with self.assertRaises(ValidationError):
            set_avatar(self.me.profile, SimpleUploadedFile("me.mp4", b"x" * 8))

    def test_a_rejected_picture_says_why_and_changes_nothing(self):
        response = self.edit_profile(avatar=SimpleUploadedFile("resume.pdf", b"x" * 8))
        self.assertEqual(response.status_code, 200)
        self.assertFalse(Profile.objects.get(user=self.me).avatar)
        self.assertContains(response, "resume.pdf")

    def test_you_cannot_edit_somebody_elses_profile(self):
        response = self.client.post(reverse("palshare:profile-edit", args=["asha"]),
                                    {"name": "Not Asha"})
        self.assertEqual(response.status_code, 403)

    def test_a_user_with_no_profile_row_does_not_break_a_byline(self):
        stray = User.objects.create_user("kaushal", password="pw")
        Post.objects.create(author=stray, text="from someone with no profile row")
        response = self.client.get(reverse("palshare:feed"))
        self.assertEqual(response.status_code, 200)


# --- 4. emoji --------------------------------------------------------------

class ReactionTests(SocialTestCase):
    def setUp(self):
        super().setUp()
        self.post = Post.objects.create(author=self.other, text="react to me")
        self.thumbs, self.heart = Reaction.EMOJI[0][0], Reaction.EMOJI[1][0]

    def react(self, emoji):
        return self.client.post(reverse("palshare:post-react", args=[self.post.pk]),
                                {"emoji": emoji})

    def test_reacting_stores_the_emoji(self):
        self.react(self.thumbs)
        self.assertEqual(Reaction.objects.get(user=self.me, post=self.post).emoji,
                         self.thumbs)

    def test_pressing_the_same_one_again_takes_it_back(self):
        self.react(self.thumbs)
        self.react(self.thumbs)
        self.assertEqual(Reaction.objects.count(), 0)

    def test_a_different_emoji_replaces_rather_than_adds(self):
        self.react(self.thumbs)
        self.react(self.heart)
        self.assertEqual(Reaction.objects.count(), 1)
        self.assertEqual(Reaction.objects.get().emoji, self.heart)

    def test_two_people_can_react_to_the_same_post(self):
        self.react(self.thumbs)
        self.client.force_login(self.other)
        self.react(self.thumbs)
        self.assertEqual(Reaction.objects.filter(post=self.post).count(), 2)

    def test_an_emoji_outside_the_palette_is_refused(self):
        with self.assertRaises(ValidationError):
            set_reaction(self.me, self.post, "\U0001f4a3")
        self.assertEqual(Reaction.objects.count(), 0)

    def test_the_endpoint_refuses_it_too_not_just_the_service(self):
        # The palette is enforced by the server, not by the five buttons the
        # template happens to render.
        self.react("\U0001f4a3")
        self.assertEqual(Reaction.objects.count(), 0)

    def test_the_bar_shows_the_whole_palette_with_counts(self):
        self.react(self.thumbs)
        body = self.client.get(reverse("palshare:feed")).content.decode()
        self.assertEqual(body.count('class="reaction '), len(Reaction.EMOJI))
        self.assertIn("reaction-on", body)

    def test_reacting_refuses_a_get(self):
        response = self.client.get(reverse("palshare:post-react", args=[self.post.pk]))
        self.assertEqual(response.status_code, 405)

    def test_you_cannot_react_to_a_post_you_cannot_see(self):
        hidden = Post.objects.create(author=self.other, text="followers only",
                                     followers_only=True)
        response = self.client.post(reverse("palshare:post-react", args=[hidden.pk]),
                                    {"emoji": self.thumbs})
        self.assertEqual(response.status_code, 404)
        self.assertEqual(Reaction.objects.count(), 0)

    def test_the_picker_is_offered_on_every_box_you_can_type_in(self):
        conversation = Conversation.objects.create()
        conversation.participants.add(self.me, self.other)
        pages = [
            (reverse("palshare:feed"), "composer-text"),
            (reverse("palshare:post-detail", args=[self.post.pk]), "comment-text"),
            (reverse("palshare:thread", args=[conversation.pk]), "message-text"),
            (reverse("palshare:post-create"), "id_text"),
        ]
        for url, target in pages:
            body = self.client.get(url).content.decode()
            self.assertIn(f'data-emoji-picker="{target}"', body, msg=url)

    def test_typed_emoji_survive_a_round_trip(self):
        self.client.post(reverse("palshare:feed"), {"text": "shipped it \U0001f680"})
        body = self.client.get(reverse("palshare:feed")).content.decode()
        self.assertIn("\U0001f680", body)


# --- 5. the assistant ------------------------------------------------------

class AssistantTests(SocialTestCase):

    @override_settings(NVIDIA_API_KEY="")
    def test_an_unconfigured_assistant_says_so_and_names_the_key(self):
        """It was not broken, it was unconfigured — and the page said
        "unavailable, try again", which is advice that never comes true."""
        response = self.client.post(reverse("palshare:assistant"), {"prompt": "hi"})
        self.assertContains(response, "NVIDIA_API_KEY")

    @override_settings(NVIDIA_API_KEY="a-key-that-will-not-answer")
    @patch("palshare.views.ask_assistant", return_value=None)
    def test_a_configured_assistant_that_fails_gets_the_other_message(self, asked):
        """Patched, not called for real. A test that reaches the internet fails
        on a train, and this one was posting to NVIDIA on every run."""
        response = self.client.post(reverse("palshare:assistant"), {"prompt": "hi"})
        self.assertContains(response, "unavailable right now")
        self.assertNotContains(response, "NVIDIA_API_KEY")
        self.assertTrue(asked.called)

    @override_settings(NVIDIA_API_KEY="a-key-that-works")
    @patch("palshare.views.ask_assistant", return_value="Try: golden hour, no filter.")
    def test_a_working_assistant_puts_the_reply_in_the_thread(self, asked):
        response = self.client.post(reverse("palshare:assistant"),
                                    {"prompt": "caption this"}, follow=True)
        self.assertContains(response, "golden hour")
        asked.assert_called_once_with("caption this")

    @override_settings(NVIDIA_API_KEY="")
    def test_your_own_prompt_is_kept_even_when_the_model_does_not_answer(self):
        self.client.post(reverse("palshare:assistant"), {"prompt": "write me a caption"})
        body = self.client.get(reverse("palshare:assistant")).content.decode()
        self.assertIn("write me a caption", body)


# --- 6. search -------------------------------------------------------------

class SearchTests(SocialTestCase):

    def find(self, q):
        return self.client.get(reverse("palshare:search"), {"q": q}).content.decode()

    def test_a_person_is_found_by_their_last_name(self):
        """`last_name` was missing from the query, so searching for someone by
        the half of their name they were introduced by found nobody."""
        self.assertIn("asha", self.find("Kandel"))

    def test_a_person_is_found_by_their_first_name(self):
        self.assertIn("asha", self.find("Asha"))

    def test_a_person_is_found_by_their_username(self):
        self.assertIn("asha", self.find("ash"))

    def test_a_person_is_found_by_their_bio(self):
        self.assertIn("asha", self.find("Fridays"))

    def test_search_is_case_insensitive(self):
        self.assertIn("asha", self.find("KANDEL"))

    def test_a_person_is_listed_once_even_when_two_fields_match(self):
        """Two OR'd `icontains` across a joined table returns the same row
        twice without `.distinct()`. Counted inside the People section only —
        the right rail suggests the same person, and that is not a duplicate."""
        body = self.find("asha")
        section = body[body.index(">People<"):body.index(">Posts<")]
        self.assertEqual(section.count('href="/palshare/u/asha/"'), 2)  # avatar + name

    def test_posts_are_found_too(self):
        Post.objects.create(author=self.other, text="a post about migrations")
        self.assertIn("a post about migrations", self.find("migrations"))

    def test_search_still_does_not_leak_a_private_post(self):
        Post.objects.create(author=self.other, text="secret migrations",
                            followers_only=True)
        self.assertNotIn("secret migrations", self.find("migrations"))

    def test_one_character_is_not_a_search(self):
        body = self.find("a")
        self.assertIn("No people matched", body)


# --- the API half of the same two writes ----------------------------------

class ReactionApiTests(SocialTestCase):
    """`react` exists on the API for the same reason `like` does: the page and
    the API share `services.set_reaction`, so they cannot disagree about it."""

    def setUp(self):
        super().setUp()
        self.post = Post.objects.create(author=self.other, text="react to me")
        self.url = f"/api/palshare/posts/{self.post.pk}/react/"
        self.thumbs = Reaction.EMOJI[0][0]
        # DRF's SessionAuthentication enforces CSRF on unsafe methods, which
        # the plain test client does not carry. `force_authenticate` is how the
        # rest of `test_api.py` does it.
        self.client = APIClient()
        self.client.force_authenticate(self.me)

    def test_reacting_through_the_api_stores_the_same_row(self):
        response = self.client.post(self.url, {"emoji": self.thumbs},
                                    content_type="application/json")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["emoji"], self.thumbs)
        self.assertEqual(Reaction.objects.get().emoji, self.thumbs)

    def test_the_api_toggles_the_same_way_the_page_does(self):
        for _ in range(2):
            self.client.post(self.url, {"emoji": self.thumbs},
                             content_type="application/json")
        self.assertEqual(Reaction.objects.count(), 0)

    def test_an_emoji_outside_the_palette_is_a_400_not_a_500(self):
        response = self.client.post(self.url, {"emoji": "\U0001f4a3"},
                                    content_type="application/json")
        self.assertEqual(response.status_code, 400)
        self.assertIn("emoji", response.json())

    def test_the_feed_serializer_reports_reactions(self):
        set_reaction(self.me, self.post, self.thumbs)
        row = self.client.get("/api/palshare/posts/").json()["results"][0]
        mine = [r for r in row["reactions"] if r["mine"]]
        self.assertEqual([r["emoji"] for r in mine], [self.thumbs])
        self.assertEqual(sum(r["count"] for r in row["reactions"]), 1)


class InteractionPermissionApiTests(SocialTestCase):
    """You could only like your own posts through the API.

    `IsAuthorOrReadOnly` was on the whole viewset, so every interaction on
    somebody else's post was a 403 — while the same interaction on the same
    post worked fine from the page, because the pages never used that
    permission class. Page and API disagreeing about a write is exactly what
    `services.py` was written to make impossible.
    """

    def setUp(self):
        super().setUp()
        self.theirs = Post.objects.create(author=self.other, text="not mine")
        self.client = APIClient()
        self.client.force_authenticate(self.me)

    def act(self, action, post=None):
        post = post or self.theirs
        return self.client.post(f"/api/palshare/posts/{post.pk}/{action}/",
                                {"emoji": Reaction.EMOJI[0][0]} if action == "react" else None,
                                format="json")

    def test_every_interaction_works_on_somebody_elses_post(self):
        for action in sorted(("like", "unlike", "save", "unsave",
                              "share", "unshare", "react")):
            with self.subTest(action=action):
                self.assertEqual(self.act(action).status_code, 200)

    def test_editing_somebody_elses_post_is_still_forbidden(self):
        # The permission was not removed, only narrowed to what it is about.
        response = self.client.patch(f"/api/palshare/posts/{self.theirs.pk}/",
                                     {"text": "rewritten by me"}, format="json")
        self.assertEqual(response.status_code, 403)
        self.theirs.refresh_from_db()
        self.assertEqual(self.theirs.text, "not mine")

    def test_deleting_somebody_elses_post_is_still_forbidden(self):
        response = self.client.delete(f"/api/palshare/posts/{self.theirs.pk}/")
        self.assertEqual(response.status_code, 403)
        self.assertTrue(Post.objects.filter(pk=self.theirs.pk).exists())

    def test_you_still_cannot_interact_with_a_post_you_cannot_see(self):
        hidden = Post.objects.create(author=self.other, text="followers only",
                                     followers_only=True)
        self.assertEqual(self.act("like", hidden).status_code, 404)
