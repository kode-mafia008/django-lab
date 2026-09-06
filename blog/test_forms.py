from django.contrib.auth.models import User
from django.core.cache import cache
from django.test import TestCase
from django.urls import reverse

from blog.forms import BlogForm
from blog.models import Author, Blog


class BlogFormCRUDTests(TestCase):
    """Day 9's CRUD, re-run as a logged-in owner.

    Every one of these tests used to pass anonymously. That was the bug: the
    pages were open to anyone who knew the URL. The only change here is a
    login in `setUp` and an `owner` on the rows — the assertions are Day 9's.
    """

    @classmethod
    def setUpTestData(cls):
        cls.austen = Author.objects.create(name="Jane Austen")
        cls.herbert = Author.objects.create(name="Frank Herbert")
        cls.user = User.objects.create_user("asha", password="lab-passphrase-2026")

    def setUp(self):
        self.client.force_login(self.user)
        # `blog_detail` is rate-limited; the counter lives in the cache, and
        # the cache is not rolled back between tests.
        cache.clear()

    def test_pages_render(self):
        for name, args in [("blog:post-list", []), ("blog:post-create", [])]:
            with self.subTest(name=name):
                self.assertEqual(self.client.get(reverse(name, args=args)).status_code, 200)

    def test_empty_list_offers_the_create_link(self):
        r = self.client.get(reverse("blog:post-list"))
        self.assertContains(r, "No posts yet")
        self.assertContains(r, reverse("blog:post-create"))

    def test_form_renders_csrf_and_four_fields(self):
        r = self.client.get(reverse("blog:post-create"))
        self.assertContains(r, "csrfmiddlewaretoken")
        self.assertEqual(list(r.context["form"].fields), ["title", "author", "content", "published"])

    def test_create_valid(self):
        r = self.client.post(reverse("blog:post-create"), {
            "title": "On the second sentence", "author": self.austen.pk,
            "content": "It does the work.", "published": "on",
        })
        blog = Blog.objects.get()
        self.assertRedirects(r, reverse("blog:post-detail", args=[blog.pk]))
        self.assertTrue(blog.published)
        self.assertEqual(blog.author, self.austen)

    def test_create_unpublished_when_checkbox_absent(self):
        self.client.post(reverse("blog:post-create"), {
            "title": "A quiet draft", "author": self.austen.pk, "content": "x",
        })
        self.assertFalse(Blog.objects.get().published)

    def test_clean_title_rejects_short_titles(self):
        r = self.client.post(reverse("blog:post-create"), {
            "title": "Hi", "author": self.austen.pk, "content": "x",
        })
        self.assertEqual(r.status_code, 200)
        self.assertIn("title", r.context["form"].errors)
        self.assertFalse(Blog.objects.exists())

    def test_clean_title_strips_whitespace(self):
        form = BlogForm(data={"title": "  Padded title  ", "author": self.austen.pk, "content": "x"})
        self.assertTrue(form.is_valid(), form.errors)
        self.assertEqual(form.cleaned_data["title"], "Padded title")

    def test_clean_rejects_duplicate_title_for_same_author(self):
        Blog.objects.create(title="Same title", content="x", author=self.austen, owner=self.user)
        r = self.client.post(reverse("blog:post-create"), {
            "title": "Same title", "author": self.austen.pk, "content": "y",
        })
        self.assertEqual(r.status_code, 200)
        self.assertTrue(r.context["form"].non_field_errors())
        self.assertEqual(Blog.objects.count(), 1)

    def test_same_title_is_fine_for_a_different_author(self):
        Blog.objects.create(title="Same title", content="x", author=self.austen, owner=self.user)
        self.client.post(reverse("blog:post-create"), {
            "title": "Same title", "author": self.herbert.pk, "content": "y",
        })
        self.assertEqual(Blog.objects.count(), 2)

    def test_empty_post_reports_every_required_field(self):
        r = self.client.post(reverse("blog:post-create"), {})
        self.assertEqual(set(r.context["form"].errors), {"title", "author", "content"})

    def test_update_prefills_and_saves(self):
        blog = Blog.objects.create(title="Original title", content="x", author=self.austen, owner=self.user)
        get = self.client.get(reverse("blog:post-update", args=[blog.pk]))
        self.assertEqual(get.context["form"].initial["title"], "Original title")

        r = self.client.post(reverse("blog:post-update", args=[blog.pk]), {
            "title": "Corrected title", "author": self.austen.pk,
            "content": "x", "published": "on",
        })
        self.assertRedirects(r, reverse("blog:post-detail", args=[blog.pk]))
        blog.refresh_from_db()
        self.assertEqual(blog.title, "Corrected title")
        self.assertEqual(Blog.objects.count(), 1)

    def test_update_may_keep_its_own_title(self):
        blog = Blog.objects.create(title="Keeping this", content="x", author=self.austen, owner=self.user)
        r = self.client.post(reverse("blog:post-update", args=[blog.pk]), {
            "title": "Keeping this", "author": self.austen.pk, "content": "changed",
        })
        self.assertEqual(r.status_code, 302)
        blog.refresh_from_db()
        self.assertEqual(blog.content, "changed")

    def test_delete_needs_a_post(self):
        blog = Blog.objects.create(title="Doomed post", content="x", author=self.austen, owner=self.user)
        get = self.client.get(reverse("blog:post-delete", args=[blog.pk]))
        self.assertEqual(get.status_code, 200)
        self.assertContains(get, "Doomed post")
        self.assertTrue(Blog.objects.filter(pk=blog.pk).exists())

        r = self.client.post(reverse("blog:post-delete", args=[blog.pk]))
        self.assertRedirects(r, reverse("blog:post-list"))
        self.assertFalse(Blog.objects.filter(pk=blog.pk).exists())

    def test_missing_post_is_404(self):
        for name in ["blog:post-detail", "blog:post-update", "blog:post-delete"]:
            with self.subTest(name=name):
                self.assertEqual(self.client.get(reverse(name, args=[9999])).status_code, 404)

    def test_success_message_survives_the_redirect(self):
        r = self.client.post(reverse("blog:post-create"), {
            "title": "Message check", "author": self.austen.pk, "content": "x",
        }, follow=True)
        self.assertContains(r, "Created &#x27;Message check&#x27;.")

    def test_html_and_api_live_in_separate_namespaces(self):
        # HTML pages: the `blog:` namespace, mounted at /blogs/.
        self.assertEqual(reverse("blog:author-list"), "/blogs/")
        self.assertEqual(reverse("blog:post-list"), "/blogs/posts/")
        # JSON API: the `api:` namespace, mounted at /api/.
        self.assertEqual(reverse("api:author-list"), "/api/authors/")
        self.assertEqual(reverse("api:blog-list"), "/api/blogs/")

    def test_templates_leak_no_comment_text_and_render_one_form(self):
        """`{# ... #}` is single-line only.

        Spread over two lines it stops being a comment: the prose lands in the
        page and any tag inside it is executed. Multi-line comments must use
        `{% comment %}`, and this test is what catches a regression.
        """
        blog = Blog.objects.create(title="Comment check", content="x", author=self.austen, owner=self.user)
        pages = [
            reverse("blog:post-create"),
            reverse("blog:post-update", args=[blog.pk]),
            reverse("blog:post-delete", args=[blog.pk]),
            reverse("blog:post-detail", args=[blog.pk]),
            reverse("blog:post-list"),
        ]
        for url in pages:
            with self.subTest(url=url):
                body = self.client.get(url).content.decode()
                self.assertNotIn("{#", body)
                self.assertNotIn("#}", body)
                self.assertNotIn("{%", body)
                self.assertNotIn("{{", body)

        for url in pages[:2]:
            with self.subTest(url=url):
                body = self.client.get(url).content.decode()
                self.assertEqual(body.count('name="title"'), 1)
                self.assertEqual(body.count("<form "), 1)

