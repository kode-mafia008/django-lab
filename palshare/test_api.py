"""The JSON half, and the reason both halves exist.

Every expectation in here is one the guide states out loud: a 401 for
anonymous, an author taken from the credential and not the payload, a 403 for
somebody else's row, idempotent likes and follows, and a query count that does
not grow with the number of rows.
"""

from django.contrib.auth.models import User
from django.db import IntegrityError, transaction
from rest_framework.test import APIClient, APITestCase

from .models import Follow, Like, Post, Profile, Save

PASSWORD = "lab-passphrase-2026"


class ApiTestCase(APITestCase):
    def setUp(self):
        self.asha = User.objects.create_user("asha", password=PASSWORD, first_name="Asha")
        self.bello = User.objects.create_user("bello", password=PASSWORD, first_name="Bello")
        Profile.objects.create(user=self.asha)
        Profile.objects.create(user=self.bello)
        self.client.force_authenticate(user=self.asha)


class PostApiTests(ApiTestCase):
    def test_anonymous_gets_a_401(self):
        response = APIClient().get("/api/palshare/posts/")
        self.assertEqual(response.status_code, 401)

    def test_the_author_comes_from_the_credential_not_the_payload(self):
        response = self.client.post("/api/palshare/posts/",
                                    {"text": "mine", "author": self.bello.pk})
        self.assertEqual(response.status_code, 201)
        self.assertEqual(response.data["author"]["username"], "asha")

    def test_you_cannot_edit_someone_elses_post(self):
        post = Post.objects.create(author=self.asha, text="asha's")
        self.client.force_authenticate(user=self.bello)
        response = self.client.patch(f"/api/palshare/posts/{post.pk}/", {"text": "hijacked"})
        self.assertEqual(response.status_code, 403)
        self.assertEqual(response.data["detail"], "You can only change things you created.")

    def test_likes_are_idempotent(self):
        post = Post.objects.create(author=self.asha, text="like me")
        for _ in range(3):
            response = self.client.post(f"/api/palshare/posts/{post.pk}/like/")
            self.assertEqual(response.status_code, 200)
            self.assertEqual(response.data, {"liked": True})
        post.refresh_from_db()
        self.assertEqual(post.like_count, 1)
        self.assertEqual(Like.objects.filter(post=post).count(), 1)

    def test_unlike_puts_the_counter_back(self):
        post = Post.objects.create(author=self.asha, text="like me")
        self.client.post(f"/api/palshare/posts/{post.pk}/like/")
        response = self.client.post(f"/api/palshare/posts/{post.pk}/unlike/")
        self.assertEqual(response.data, {"liked": False})
        post.refresh_from_db()
        self.assertEqual(post.like_count, 0)

    def test_the_counter_never_goes_negative(self):
        post = Post.objects.create(author=self.asha, text="never liked")
        self.client.post(f"/api/palshare/posts/{post.pk}/unlike/")
        post.refresh_from_db()
        self.assertEqual(post.like_count, 0)

    def test_saving_is_idempotent_too(self):
        post = Post.objects.create(author=self.asha, text="save me")
        for _ in range(3):
            self.assertEqual(self.client.post(f"/api/palshare/posts/{post.pk}/save/").data,
                             {"saved": True})
        self.assertEqual(Save.objects.filter(post=post).count(), 1)

    def test_a_followers_only_post_is_invisible_until_you_follow(self):
        Post.objects.create(author=self.asha, text="public")
        Post.objects.create(author=self.asha, text="just for my followers",
                            followers_only=True)
        self.client.force_authenticate(user=self.bello)

        texts = [p["text"] for p in self.client.get("/api/palshare/posts/").data["results"]]
        self.assertEqual(texts, ["public"])

        Follow.objects.create(follower=self.bello, following=self.asha)
        texts = [p["text"] for p in self.client.get("/api/palshare/posts/").data["results"]]
        self.assertEqual(sorted(texts), ["just for my followers", "public"])

    def test_ten_rows_do_not_cost_ten_queries(self):
        for i in range(10):
            post = Post.objects.create(author=self.asha, text=f"post {i}")
            Like.objects.create(user=self.asha, post=post)
        with self.assertNumQueries(3):
            response = self.client.get("/api/palshare/posts/")
        self.assertEqual(len(response.data["results"]), 10)


class FollowApiTests(ApiTestCase):
    def test_follow_is_idempotent(self):
        for _ in range(3):
            response = self.client.post("/api/palshare/users/bello/follow/")
            self.assertEqual(response.status_code, 200)
            self.assertEqual(response.data, {"following": True})
        self.assertEqual(Follow.objects.count(), 1)

    def test_you_cannot_follow_yourself(self):
        """The constraint is the guarantee; the view is the error message."""
        response = self.client.post("/api/palshare/users/asha/follow/")
        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.data["detail"], "You cannot follow yourself.")

    def test_and_the_database_refuses_it_too(self):
        with self.assertRaises(IntegrityError), transaction.atomic():
            Follow.objects.create(follower=self.asha, following=self.asha)

    def test_unfollow(self):
        self.client.post("/api/palshare/users/bello/follow/")
        response = self.client.post("/api/palshare/users/bello/unfollow/")
        self.assertEqual(response.data, {"following": False})
        self.assertEqual(Follow.objects.count(), 0)

    def test_a_profile_is_addressed_by_username(self):
        response = self.client.get("/api/palshare/users/bello/")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["username"], "bello")
        self.assertFalse(response.data["is_following"])


class OneRuleTwoConsumersTests(ApiTestCase):
    """Day 10's confession was one rule written twice. This is the test that
    the two consumers still agree."""

    def test_the_page_and_the_api_return_the_same_post(self):
        post = Post.objects.create(author=self.asha, text="one shape, two consumers")
        Like.objects.create(user=self.asha, post=post)
        Post.objects.filter(pk=post.pk).update(like_count=1)

        api = self.client.get(f"/api/palshare/posts/{post.pk}/").data

        page = APIClient()
        page.login(username="asha", password=PASSWORD)
        html = page.get(f"/palshare/posts/{post.pk}/").context["post"]

        for key in ["id", "text", "likes", "liked", "saved", "shares", "age"]:
            self.assertEqual(api[key], html[key], f"page and API disagree about `{key}`")
        self.assertEqual(api["author"]["username"], html["author"]["username"])
