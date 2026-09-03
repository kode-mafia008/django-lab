from django import forms
from .models import Blog

class BlogForm(forms.ModelForm):

    class Meta:
        model = Blog
        # No trailing comma after any of these four. A trailing comma makes the
        # value a tuple containing the dict/list, and Django then either raises
        # or silently ignores it.
        fields = ['title', 'content', 'author', 'published']
        widgets = {
            "title": forms.TextInput(
                attrs={'placeholder': 'A short, specific title', "autofocus": True}
            ),
            "content": forms.Textarea(
                attrs={'rows': 10, 'placeholder': 'Write your blog post here...'}
            ),
        }
        labels = {
            "published": "Publish immediately",
        }
        help_texts = {
            "title": "The title of your blog post.",
            "content": "The main content of your blog post.",
            "author": "Select the author of the blog post.",
            "published": "Check this box to publish the blog post immediately.",
        }

    def clean_title(self):
        """Field-level validation. Must return the field's own value."""
        title = self.cleaned_data.get('title')
        if not title:
            raise forms.ValidationError("Title is required.")
        if len(title) < 5:
            raise forms.ValidationError("Title must be at least 5 characters long.")
        return title

    def clean(self):
        """Cross-field validation.

        This has to be `clean()`, not `clean_content()`. Django runs each
        `clean_<field>` in field order, so inside `clean_content` the `author`
        field has not been cleaned yet and `cleaned_data['author']` is missing —
        the check below would never run. `clean()` runs after every field.
        """
        cleaned = super().clean()
        title = cleaned.get('title')
        author = cleaned.get('author')

        # A field that failed validation is absent from cleaned_data, so never
        # assume the keys exist.
        if title and author:
            # Keep this a queryset. Calling .exists() here would make `clash` a
            # bool, and bools have no .exclude() or .exists().
            clash = Blog.objects.filter(title=title, author=author)
            if self.instance.pk:
                # Editing: a post is allowed to keep its own title.
                clash = clash.exclude(pk=self.instance.pk)
            if clash.exists():
                raise forms.ValidationError(
                    f"A blog post called '{title}' already exists for {author}."
                )
        return cleaned
