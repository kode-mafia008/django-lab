"""The seven controls that used to render and do nothing.

Each one is a form now, so each one is testable the way a form is: post to it
and look at the row it was supposed to create. The pair of tests that matters
most in here is the toggle pair — press once, press again, and end up where
you started, with the counter cache still telling the truth.
"""

from django.contrib.auth.models import User
from django.test import TestCase
from django.urls import reverse

from .models import (Comment, CommentLike, Conversation, Follow, Like, Post,
                     Profile, Save, Share)
from .services import set_like

PASSWORD = "lab-passphrase-2026"


class InteractionTestCase(TestCase):
    def setUp(self):
        self.asha = User.objects.create_user("asha", password=PASSWORD, first_name="Asha")
        self.bello = User.objects.create_user("bello", password=PASSWORD, first_name="Bello")
        Profile.objects.create(user=self.asha)
        Profile.objects.create(user=self.bello)
        self.post = Post.objects.create(author=self.asha, text="press things on me")
        self.comment = Comment.objects.create(post=self.post, author=self.asha, text="a comment")
        self.client.login(username="bello", password=PASSWORD)
        self.feed = reverse("palshare:feed")

    def press(self, name, args, **data):
        return self.client.post(reverse(name, args=args), {"next": self.feed, **data})


class PostActionTests(InteractionTestCase):
    def test_like_toggles_and_the_counter_follows(self):
        self.press("palshare:post-like", [self.post.pk])
        self.post.refresh_from_db()
        self.assertEqual((self.post.like_count, Like.objects.count()), (1, 1))

        self.press("palshare:post-like", [self.post.pk])
        self.post.refresh_from_db()
        self.assertEqual((self.post.like_count, Like.objects.count()), (0, 0))

    def test_a_drifted_counter_cannot_go_negative(self):
        """A PositiveIntegerField underflows to four billion, not to -1.

        Counter caches drift — that is the price of caching them — so removal
        has to cope with "the row is here but the counter already says zero".
        """
        set_like(self.bello, self.post, True)
        Post.objects.filter(pk=self.post.pk).update(like_count=0)  # drift
        set_like(self.bello, self.post, False)
        self.post.refresh_from_db()
        self.assertEqual(self.post.like_count, 0)

    def test_share_toggles(self):
        self.press("palshare:post-share", [self.post.pk])
        self.post.refresh_from_db()
        self.assertEqual((self.post.share_count, Share.objects.count()), (1, 1))
        self.press("palshare:post-share", [self.post.pk])
        self.post.refresh_from_db()
        self.assertEqual((self.post.share_count, Share.objects.count()), (0, 0))

    def test_save_toggles_and_the_saved_page_follows(self):
        self.press("palshare:post-save", [self.post.pk])
        self.assertEqual(Save.objects.count(), 1)
        self.assertContains(self.client.get(reverse("palshare:saved")), "press things on me")
        self.press("palshare:post-save", [self.post.pk])
        self.assertEqual(Save.objects.count(), 0)

    def test_you_cannot_like_a_post_you_cannot_see(self):
        hidden = Post.objects.create(author=self.asha, text="hidden", followers_only=True)
        response = self.press("palshare:post-like", [hidden.pk])
        self.assertEqual(response.status_code, 404)
        self.assertEqual(Like.objects.count(), 0)

    def test_an_action_route_refuses_a_get(self):
        """A GET that writes is a GET any <img> tag can trigger."""
        response = self.client.get(reverse("palshare:post-like", args=[self.post.pk]))
        self.assertEqual(response.status_code, 405)

    def test_next_cannot_send_you_off_site(self):
        response = self.client.post(reverse("palshare:post-like", args=[self.post.pk]),
                                    {"next": "https://evil.test/steal"})
        self.assertRedirects(response, self.feed)

    def test_the_card_has_no_inert_buttons_left(self):
        body = self.client.get(self.feed).content.decode()
        self.assertNotIn('type="button"', body)
        self.assertIn(reverse("palshare:post-like", args=[self.post.pk]), body)


class CommentActionTests(InteractionTestCase):
    def test_comment_like_toggles(self):
        self.press("palshare:comment-like", [self.comment.pk])
        self.comment.refresh_from_db()
        self.assertEqual((self.comment.like_count, CommentLike.objects.count()), (1, 1))
        self.press("palshare:comment-like", [self.comment.pk])
        self.comment.refresh_from_db()
        self.assertEqual((self.comment.like_count, CommentLike.objects.count()), (0, 0))

    def test_replying_sets_the_parent(self):
        self.client.post(reverse("palshare:post-detail", args=[self.post.pk]),
                         {"text": "a reply", "parent": self.comment.pk})
        self.assertEqual(Comment.objects.get(text="a reply").parent_id, self.comment.pk)

    def test_a_reply_to_a_reply_flattens_to_one_level(self):
        """The model allows any depth — a CheckConstraint cannot walk a tree —
        so the rule lives in the service."""
        self.client.post(reverse("palshare:post-detail", args=[self.post.pk]),
                         {"text": "a reply", "parent": self.comment.pk})
        reply = Comment.objects.get(text="a reply")
        self.client.post(reverse("palshare:post-detail", args=[self.post.pk]),
                         {"text": "deeper", "parent": reply.pk})
        self.assertEqual(Comment.objects.get(text="deeper").parent_id, self.comment.pk)

    def test_you_cannot_reply_onto_another_posts_comment(self):
        other = Post.objects.create(author=self.asha, text="another post")
        response = self.client.post(reverse("palshare:post-detail", args=[other.pk]),
                                    {"text": "smuggled", "parent": self.comment.pk})
        self.assertEqual(response.status_code, 404)


class FollowActionTests(InteractionTestCase):
    def test_follow_toggles(self):
        self.press("palshare:user-follow", ["asha"])
        self.assertEqual(Follow.objects.count(), 1)
        self.press("palshare:user-follow", ["asha"])
        self.assertEqual(Follow.objects.count(), 0)

    def test_following_yourself_is_refused_with_a_sentence(self):
        response = self.client.post(reverse("palshare:user-follow", args=["bello"]),
                                    {"next": self.feed}, follow=True)
        self.assertEqual(Follow.objects.count(), 0)
        self.assertContains(response, "You cannot follow yourself")

    def test_the_follow_button_is_absent_from_your_own_row(self):
        body = self.client.get(reverse("palshare:search"), {"q": "bello"}).content.decode()
        self.assertNotIn(reverse("palshare:user-follow", args=["bello"]), body)


class MessageActionTests(InteractionTestCase):
    def test_messaging_someone_opens_one_conversation_and_keeps_it(self):
        response = self.press("palshare:message-user", ["asha"])
        conversation = Conversation.objects.get()
        self.assertRedirects(response, reverse("palshare:thread", args=[conversation.pk]))

        self.press("palshare:message-user", ["asha"])
        self.assertEqual(Conversation.objects.count(), 1)

    def test_it_is_the_same_conversation_from_either_side(self):
        self.press("palshare:message-user", ["asha"])
        self.client.login(username="asha", password=PASSWORD)
        self.press("palshare:message-user", ["bello"])
        self.assertEqual(Conversation.objects.count(), 1)

    def test_you_cannot_message_yourself(self):
        response = self.press("palshare:message-user", ["bello"])
        self.assertRedirects(response, reverse("palshare:inbox"))
        self.assertEqual(Conversation.objects.count(), 0)


class PagerTests(InteractionTestCase):
    def test_paging_keeps_the_rest_of_the_query_string(self):
        """A bare `?page=2` silently drops the tab you were on."""
        Follow.objects.create(follower=self.bello, following=self.asha)
        for i in range(25):
            Post.objects.create(author=self.asha, text=f"post {i}")
        body = self.client.get(self.feed, {"filter": "following"}).content.decode()
        self.assertIn("filter=following&amp;page=2", body)

    def test_the_following_tab_means_people_you_follow(self):
        mine = Post.objects.create(author=self.bello, text="my own post")
        body = self.client.get(self.feed, {"filter": "following"}).content.decode()
        self.assertNotIn("my own post", body)
        self.assertNotIn("press things on me", body)  # asha, not followed yet

        Follow.objects.create(follower=self.bello, following=self.asha)
        body = self.client.get(self.feed, {"filter": "following"}).content.decode()
        self.assertIn("press things on me", body)
        self.assertNotIn(mine.text, body)
