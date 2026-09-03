"""Tests for the stylesheet wiring.

These are cheap and they cover the failure modes that produce a page which
still returns 200 while looking wrong: a stylesheet that 404s, a `{% static %}`
tag that was never loaded, or a CSS class that a template stopped emitting.
"""

from django.contrib.staticfiles import finders
from django.contrib.auth.models import User
from django.test import TestCase
from django.urls import reverse

from blog.models import Author, Blog

PAGES_NEEDING_A_POST = ["blog:post-detail", "blog:post-update", "blog:post-delete"]


class StylesheetTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.austen = Author.objects.create(name="Jane Austen", bio="Novelist.")
        cls.blog = Blog.objects.create(
            title="A styled post", content="Body.", author=cls.austen, published=True
        )

    def all_pages(self):
        yield reverse("blog:author-list")
        yield reverse("blog:author-detail", args=[self.austen.pk])
        yield reverse("blog:post-list")
        yield reverse("blog:post-create")
        for name in PAGES_NEEDING_A_POST:
            yield reverse(name, args=[self.blog.pk])

    def test_staticfiles_can_find_the_stylesheet(self):
        """If this fails, the file is in the wrong directory."""
        self.assertIsNotNone(finders.find("blog/style.css"))

    def test_every_page_links_the_stylesheet(self):
        for url in self.all_pages():
            with self.subTest(url=url):
                response = self.client.get(url)
                self.assertEqual(response.status_code, 200)
                self.assertContains(
                    response, '<link rel="stylesheet" href="/static/blog/style.css">'
                )

    def test_no_page_leaks_template_syntax(self):
        """`{% load static %}` before the doctype is easy to get wrong."""
        for url in self.all_pages():
            with self.subTest(url=url):
                body = self.client.get(url).content.decode()
                for token in ("{%", "{{", "{#", "#}"):
                    self.assertNotIn(token, body)

    def test_list_marks_published_and_draft_differently(self):
        Blog.objects.create(title="A draft post", content="x", author=self.austen)
        response = self.client.get(reverse("blog:post-list"))
        self.assertContains(response, 'class="badge badge-published"')
        self.assertContains(response, 'class="badge badge-draft"')

    def test_empty_list_uses_the_empty_state(self):
        Blog.objects.all().delete()
        self.assertContains(self.client.get(reverse("blog:post-list")), 'class="empty"')

    def test_checkbox_field_gets_its_own_wrapper(self):
        """Without this the checkbox stretches to 100% width like a text input."""
        response = self.client.get(reverse("blog:post-create"))
        self.assertContains(response, 'class="field field-checkbox"')

    def test_field_errors_render_in_an_errorlist(self):
        response = self.client.post(reverse("blog:post-create"), {
            "title": "Hi", "author": self.austen.pk, "content": "x",
        })
        self.assertContains(response, 'class="errorlist"')

    def test_non_field_errors_render_in_a_boxed_form_errors_list(self):
        response = self.client.post(reverse("blog:post-create"), {
            "title": self.blog.title, "author": self.austen.pk, "content": "x",
        })
        self.assertTrue(response.context["form"].non_field_errors())
        self.assertContains(response, 'class="errorlist form-errors"')

    def test_flash_message_carries_its_tag_as_a_class(self):
        response = self.client.post(reverse("blog:post-create"), {
            "title": "Freshly created", "author": self.austen.pk, "content": "x",
        }, follow=True)
        self.assertContains(response, 'class="messages"')
        self.assertContains(response, 'class="success"')

    def test_delete_page_warns(self):
        response = self.client.get(reverse("blog:post-delete", args=[self.blog.pk]))
        self.assertContains(response, 'class="warning-panel"')
        self.assertContains(response, "btn-danger")


class StylesheetContentTests(TestCase):
    """Every class a template emits must exist in the stylesheet."""

    def test_no_template_class_is_undefined_in_the_css(self):
        import re
        from django.contrib.staticfiles import finders

        css = open(finders.find("blog/style.css")).read()
        defined = set(re.findall(r"\.([A-Za-z][A-Za-z0-9_-]*)", css))

        author = Author.objects.create(name="Jane Austen")
        blog = Blog.objects.create(title="A styled post", content="x", author=author)
        urls = [
            reverse("blog:author-list"),
            reverse("blog:author-detail", args=[author.pk]),
            reverse("blog:post-list"),
            reverse("blog:post-create"),
            reverse("blog:post-detail", args=[blog.pk]),
            reverse("blog:post-update", args=[blog.pk]),
            reverse("blog:post-delete", args=[blog.pk]),
        ]
        used = set()
        for url in urls:
            body = self.client.get(url).content.decode()
            for attr in re.findall(r'class="([^"]+)"', body):
                used.update(attr.split())

        self.assertEqual(sorted(used - defined), [], "classes used but never styled")
