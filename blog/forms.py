from django import forms
from .models import Blog
class BlogForm(forms.ModelForm):
    class Meta:
        model = Blog
        fields = ['title', 'content', 'author', 'published']
        widgets = {
            "title": forms.TextInput(
                attrs={"placeholder": "a short, specific title", "autofocus": "true"}
            ),
            "content": forms.Textarea(
                attrs={"rows": 5, "cols": 50, "placeholder": "write your content here"}
            ),
        }
        labels = {
            "published": "Publish immediately",
        }
        help_texts = {
            "title": "Enter a title for your blog post",
            "content": "Write your blog post content here",
            "author": "Enter the author's name",
            "published": "Check this box to publish the blog post immediately",
        }

    def clean_title(self):
        title = self.cleaned_data.get('title')
        if not title:
            raise forms.ValidationError("Title is required.")
        if len(title) < 5:
            raise forms.ValidationError("Title must be at least 5 characters long.")
        return title

    def clean_content(self):
        content = self.cleaned_data.get('content')
        title = self.cleaned_data.get('title')
        author = self.cleaned_data.get('author')
        if title and author:
            clash = Blog.objects.filter(title=title, author=author)
            if self.instance.pk:
                clash = clash.exclude(pk=self.instance.pk)
            if clash.exists():
                raise forms.ValidationError(
                    f"A blog post with the title '{title}' already exists for this author."
                )
        return content