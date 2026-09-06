from django import forms

from .models import Blog


class BlogForm(forms.ModelForm):
    """A ModelForm over `Blog`.

    `Meta.fields` is an allowlist, not a convenience: anything not named here
    cannot be set from the browser, however the POST body is crafted. That is
    why `created_at` and `updated_at` are absent rather than disabled.
    """

    class Meta:
        model = Blog
        fields = ["title", "author", "content", "published"]
        widgets = {
            "title": forms.TextInput(
                attrs={"placeholder": "A short, specific title", "autofocus": True}
            ),
            "content": forms.Textarea(
                attrs={"rows": 10, "placeholder": "Write the post here."}
            ),
        }
        labels = {
            "published": "Publish immediately",
        }
        help_texts = {
            "author": "Pick one of the authors already in the database.",
            "published": "Leave this unticked to keep the post as a draft.",
        }

    def clean_title(self):
        """Field-level validation. Runs only if `title` itself was valid."""
        title = self.cleaned_data["title"].strip()
        if len(title) < 5:
            raise forms.ValidationError("Give it at least five characters.")
        return title

    def clean(self):
        """Cross-field validation. Runs after every `clean_<field>`."""
        cleaned = super().clean()
        title = cleaned.get("title")
        author = cleaned.get("author")

        # Both may be missing — if a field failed above, it is not in
        # cleaned_data at all, so never assume the keys exist.
        if title and author:
            clash = Blog.objects.filter(title=title, author=author)
            if self.instance.pk:
                # Editing: a post is allowed to keep its own title.
                clash = clash.exclude(pk=self.instance.pk)
            if clash.exists():
                raise forms.ValidationError(
                    f"{author} already has a post called '{title}'."
                )
        return cleaned
