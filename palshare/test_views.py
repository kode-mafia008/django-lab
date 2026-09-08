"""The HTML half: does every page render, and does it obey the rules?

The contract these check is `demo.py` — the keys each template reads. A view is
correct when its context has the same shape the shell was built against, which
is why several of these assert on rendered markup rather than on a queryset.
"""

from django.contrib.auth.models import User
from django.db import connection
from django.test.utils import CaptureQueriesContext
from django.test import TestCase
from django.urls import reverse

from .models import Comment, Conversation, Follow, Like, Post, Profile, Save

PASSWORD = "lab-passphrase-2026"


class PalShareTestCase(TestCase):
    """Two accounts and a handful of rows — the same fixture every test wants."""

    def setUp(self):
        self.asha = User.objects.create_user("asha", password=PASSWORD, first_name="Asha")
        self.bello = User.objects.create_user("bello", password=PASSWORD, first_name="Bello")
        Profile.objects.create(user=self.asha, bio="workshop")
        Profile.objects.create(user=self.bello)
        self.public = Post.objects.create(author=self.asha, text="a public post")
        self.private = Post.objects.create(author=self.asha, text="a followers-only post",
                                           followers_only=True)
        self.client.login(username="bello", password=PASSWORD)


class PageTests(PalShareTestCase):
    def test_every_page_renders(self):
        urls = [
            reverse("palshare:feed"),
            reverse("palshare:post-create"),
            reverse("palshare:post-detail", args=[self.public.pk]),
            reverse("palshare:profile", args=["asha"]),
            reverse("palshare:profile-edit", args=["bello"]),
            reverse("palshare:connections", args=["asha"]),
            reverse("palshare:saved"),
            reverse("palshare:search") + "?q=post",
            reverse("palshare:inbox"),
            reverse("palshare:assistant"),
            reverse("palshare:settings"),
        ]
        for url in urls:
            with self.subTest(url=url):
                response = self.client.get(url)
                self.assertEqual(response.status_code, 200)
                # An unrendered tag means a context key the view forgot.
                self.assertNotContains(response, "{{")
                self.assertNotContains(response, "{%")

    def test_pages_require_a_login_and_send_you_to_palshares_own(self):
        self.client.logout()
        response = self.client.get(reverse("palshare:feed"))
        self.assertRedirects(response, "/palshare/login/?next=/palshare/")

    def test_feed_shows_real_rows_not_demo_data(self):
        response = self.client.get(reverse("palshare:feed"))
        self.assertContains(response, "a public post")
        self.assertNotContains(response, "Menuka")  # demo.py's placeholder user

    def test_post_card_gets_every_key_the_template_reads(self):
        post = self.client.get(reverse("palshare:feed")).context["posts"][0]
        for key in ["id", "author", "age", "text", "media", "likes", "comments",
                    "shares", "liked", "saved"]:
            self.assertIn(key, post, f"`{key}` is in demo.py and _post_card.html reads it")
        for key in ["id", "username", "name", "avatar"]:
            self.assertIn(key, post["author"])


class VisibilityTests(PalShareTestCase):
    def test_followers_only_post_is_hidden_until_you_follow(self):
        response = self.client.get(reverse("palshare:feed"))
        self.assertNotContains(response, "a followers-only post")

        Follow.objects.create(follower=self.bello, following=self.asha)
        response = self.client.get(reverse("palshare:feed"))
        self.assertContains(response, "a followers-only post")

    def test_search_respects_visibility(self):
        """Search is the classic way private data leaks."""
        response = self.client.get(reverse("palshare:search"), {"q": "followers-only"})
        self.assertNotContains(response, "a followers-only post")

    def test_a_two_character_query_is_not_a_search(self):
        response = self.client.get(reverse("palshare:search"), {"q": "a"})
        self.assertEqual(response.context["posts"], [])
        self.assertEqual(response.context["people"], [])

    def test_private_profile_shows_the_header_and_nothing_else(self):
        Profile.objects.filter(user=self.asha).update(is_private=True)
        response = self.client.get(reverse("palshare:profile", args=["asha"]))
        self.assertContains(response, "This account is private")
        self.assertNotContains(response, "a public post")

    def test_private_profile_opens_up_to_a_follower(self):
        Profile.objects.filter(user=self.asha).update(is_private=True)
        Follow.objects.create(follower=self.bello, following=self.asha)
        response = self.client.get(reverse("palshare:profile", args=["asha"]))
        self.assertContains(response, "a public post")


class WriteTests(PalShareTestCase):
    def test_the_composer_creates_a_post_and_redirects(self):
        response = self.client.post(reverse("palshare:feed"), {"text": "from the composer"})
        self.assertRedirects(response, reverse("palshare:feed"))
        self.assertTrue(Post.objects.filter(text="from the composer",
                                            author=self.bello).exists())

    def test_a_post_is_authored_by_the_credential_not_the_form(self):
        self.client.post(reverse("palshare:post-create"),
                         {"text": "mine", "author": self.asha.pk})
        self.assertEqual(Post.objects.get(text="mine").author, self.bello)

    def test_you_cannot_edit_someone_elses_post(self):
        response = self.client.post(reverse("palshare:post-edit", args=[self.public.pk]),
                                    {"text": "hijacked"})
        self.assertEqual(response.status_code, 403)
        self.public.refresh_from_db()
        self.assertEqual(self.public.text, "a public post")

    def test_a_post_you_cannot_see_is_a_404_not_a_403(self):
        """A 403 confirms the row exists. A 404 says nothing."""
        response = self.client.get(reverse("palshare:post-detail", args=[self.private.pk]))
        self.assertEqual(response.status_code, 404)

    def test_commenting_bumps_the_counter_cache(self):
        self.client.post(reverse("palshare:post-detail", args=[self.public.pk]),
                         {"text": "nice one"})
        self.public.refresh_from_db()
        self.assertEqual(self.public.comment_count, 1)
        self.assertEqual(Comment.objects.filter(post=self.public).count(), 1)

    def test_saved_page_lists_what_you_starred(self):
        Save.objects.create(user=self.bello, post=self.public)
        response = self.client.get(reverse("palshare:saved"))
        self.assertContains(response, "a public post")

    def test_you_cannot_edit_someone_elses_profile(self):
        response = self.client.post(reverse("palshare:profile-edit", args=["asha"]),
                                    {"name": "Not Asha", "bio": ""})
        self.assertEqual(response.status_code, 403)
        self.asha.refresh_from_db()
        self.assertEqual(self.asha.first_name, "Asha")

    def test_the_privacy_switch_saves(self):
        self.client.post(reverse("palshare:settings"), {"is_private": "on"})
        self.assertTrue(Profile.objects.get(user=self.bello).is_private)
        self.client.post(reverse("palshare:settings"), {})
        self.assertFalse(Profile.objects.get(user=self.bello).is_private)


class MessagingTests(PalShareTestCase):
    def setUp(self):
        super().setUp()
        self.conversation = Conversation.objects.create()
        self.conversation.participants.add(self.asha, self.bello)
        self.conversation.messages.create(sender=self.asha, text="are you there")

    def test_mine_comes_from_the_server(self):
        url = reverse("palshare:thread", args=[self.conversation.pk])
        sent = self.client.get(url).context["thread_messages"]
        self.assertEqual([m["mine"] for m in sent], [False])
        self.client.post(url, {"text": "I am"})
        self.assertEqual([m["mine"] for m in self.client.get(url).context["thread_messages"]],
                         [False, True])

    def test_the_thread_list_is_not_called_messages(self):
        """`messages` belongs to django.contrib.messages; a thread under that
        name renders itself as flash messages in base.html."""
        response = self.client.get(reverse("palshare:thread", args=[self.conversation.pk]))
        self.assertIn("thread_messages", response.context)

    def test_a_conversation_you_are_not_in_does_not_exist(self):
        theirs = Conversation.objects.create()
        theirs.participants.add(self.asha)
        response = self.client.get(reverse("palshare:thread", args=[theirs.pk]))
        self.assertEqual(response.status_code, 404)

    def test_opening_a_thread_clears_the_unread_badge(self):
        inbox = self.client.get(reverse("palshare:inbox")).context["conversations"]
        self.assertEqual(inbox[0]["unread"], 1)
        self.client.get(reverse("palshare:thread", args=[self.conversation.pk]))
        inbox = self.client.get(reverse("palshare:inbox")).context["conversations"]
        self.assertEqual(inbox[0]["unread"], 0)


class AuthTests(TestCase):
    def test_registering_creates_a_profile_and_signs_you_in(self):
        response = self.client.post(reverse("palshare:register"),
                                    {"username": "kaushal", "email": "k@lab.test",
                                     "password": PASSWORD})
        self.assertRedirects(response, reverse("palshare:feed"))
        self.assertTrue(Profile.objects.filter(user__username="kaushal").exists())

    def test_a_taken_username_says_so(self):
        User.objects.create_user("kaushal", password=PASSWORD)
        response = self.client.post(reverse("palshare:register"),
                                    {"username": "kaushal", "password": PASSWORD})
        self.assertContains(response, "That username is taken")

    def test_a_bad_password_renders_the_login_error(self):
        User.objects.create_user("kaushal", password=PASSWORD)
        response = self.client.post(reverse("palshare:login"),
                                    {"username": "kaushal", "password": "wrong"})
        self.assertContains(response, "did not match")

    def test_logout_is_a_post(self):
        user = User.objects.create_user("kaushal", password=PASSWORD)
        Profile.objects.create(user=user)
        self.client.login(username="kaushal", password=PASSWORD)
        # A GET logout can be triggered by any <img> tag on the internet.
        self.assertEqual(self.client.get(reverse("palshare:settings")).status_code, 200)
        response = self.client.post(reverse("palshare:settings"), {"logout": "1"})
        self.assertRedirects(response, reverse("palshare:login"))


class QueryCountTests(PalShareTestCase):
    """The habit of measuring is the deliverable.

    These numbers are allowed to change; what is not allowed is for them to
    change *with the number of rows*, which is what each test actually pins.
    """

    def make_posts(self, n):
        for i in range(n):
            post = Post.objects.create(author=self.asha, text=f"post {i}")
            Like.objects.create(user=self.bello, post=post)

    def test_the_feed_costs_the_same_for_three_rows_and_thirty(self):
        # Eight, not six. Both extra queries are per-page, not per-row, which
        # is the property this test actually pins:
        #   +1  the reactions prefetch, one query for every row on the page
        #   +1  your own profile, read once by the header's avatar
        # `request.user` arrives from the auth middleware without its profile,
        # so that hop cannot be select_related away from here.
        self.make_posts(3)
        with self.assertNumQueries(8):
            self.client.get(reverse("palshare:feed"))
        self.make_posts(27)
        with self.assertNumQueries(8):
            self.client.get(reverse("palshare:feed"))

    def test_search_does_not_pay_per_person(self):
        """`profile.bio` is a OneToOne hop, which is an N+1 spelled as an
        attribute access. `queries.people()` select_relates it away."""
        def cost():
            with CaptureQueriesContext(connection) as queries:
                self.client.get(reverse("palshare:search"), {"q": "Findme"})
            return len(queries)

        for i in range(2):
            Profile.objects.create(
                user=User.objects.create_user(f"early{i}", first_name="Findme"), bio="hello")
        two_people = cost()
        for i in range(10):
            Profile.objects.create(
                user=User.objects.create_user(f"later{i}", first_name="Findme"), bio="hello")
        self.assertEqual(cost(), two_people)
