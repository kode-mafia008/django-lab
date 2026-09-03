from django import forms
from .models import Blog

class BlogForm(forms.ModelForm):
    class Meta:
        model = Blog
        fields = ['title', 
                  'content',
                  'author', 
                  'published']    
        
        widgets = {
            'title': forms.TextInput(
                attrs={'placeholder': 'A short specific title',"autofocus":True}
                ), 
            'content': forms.Textarea(
                attrs={'rows':5, 'placeholder': 'Write your blog content here...'}
                ),
        }
        labels = {
            'published': 'Publish immediately',
        }
        help_texts = {
            'title': 'Enter a title for your blog post.',
            'content': 'Write the content of your blog post here.',
            'author': 'Select the author of the blog post.',
            'published': 'Check this box to publish the blog post immediately.',
        }
        
    def clean_title(self):
        title = self.cleaned_data.get('title')
        if not title:
            raise forms.ValidationError("Title is required.")
        if len(title) < 5:
            raise forms.ValidationError("Title must be at least 5 characters long.")
        return title
    
    def clean_content(self):
        cleaned=super().clean()
        content = cleaned.get('content')
        title = cleaned.get('title')
        author = cleaned.get('author')
        
        if title and author:
            # Perform any additional validation logic here
            clash=Blog.objects.filter(title=title, author=author).exists()
            if self.instance.pk:
                clash=clash.exclude(pk=self.instance.pk).exists()
            if clash.exist():
                raise forms.ValidationError(
                    f"A blog postwith this(title)already exists for this (author)."
                )        
        return cleaned        
            
        
           
