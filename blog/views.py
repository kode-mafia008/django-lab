from django.shortcuts import get_object_or_404, render, redirect
from rest_framework import generics
from rest_framework import viewsets

from .serializers import AuthorSerializer, BlogSerializer
from .models import Author, Blog
from rest_framework.permissions import IsAuthenticated
from .forms import BlogForm
from django.contrib import messages


def author_list(request):
    authors = Author.objects.order_by("name")
    return render(request, "blog/author_list.html", {"authors": authors})


def author_detail(request, pk):
    author = get_object_or_404(Author, pk=pk)
    return render(request, "blog/author_detail.html", {"author": author})


class AuthorViewSet(viewsets.ModelViewSet):
    queryset = Author.objects.all()
    serializer_class = AuthorSerializer
    permission_classes = [IsAuthenticated]

class BlogViewSet(viewsets.ModelViewSet):
    queryset = Blog.objects.all()
    serializer_class = BlogSerializer
    permission_classes = [IsAuthenticated]


#form view
def blog_list(request):
    blogs = Blog.objects.order_by("-published")
    return render(request, "blog/blog_list.html", {"blogs": blogs})
def blog_detail(request, pk):
    blog = get_object_or_404(Blog.objects.select_related("author"), pk=pk)
    return render(request, "blog/blog_detail.html", {"blog": blog})

def blog_create(request):
    if request.method == "POST":
        form = BlogForm(request.POST)
        if form.is_valid():
            blog = form.save()
            messages.success(request, "Blog post created successfully.")
            return redirect("blog:blog_detail", pk=blog.pk)
    else:
        form = BlogForm()
    return render(
        request,
        "blog/blog_form.html",
        {"form": form, "heading": "New Post", "button_text": "Create Post"},
    )
def blog_update(request, pk):
    blog = get_object_or_404(Blog, pk=pk)
    if request.method == "POST":
        form = BlogForm(request.POST, instance=blog)
        if form.is_valid():
            form.save()
            messages.success(request, "Blog post updated successfully.")
            return redirect("blog:blog_detail", pk=blog.pk)
    else:
        form = BlogForm(instance=blog)
    return render(
        request,
        "blog/blog_form.html",
        {"form": form, "heading": "Edit Post", "button_text": "Update Post"},
    )