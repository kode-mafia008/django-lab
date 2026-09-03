from django.shortcuts import get_object_or_404, render,redirect
from rest_framework import viewsets
from .serializers import AuthorSerializer, BlogSerializer
from .models import Author, Blog
from rest_framework.permissions import IsAuthenticated
from drf_spectacular.utils import extend_schema

from django.contrib import messages
from .forms import Blogform




def author_list(request):
    authors = Author.objects.order_by("name")
    return render(request, "blog/author_list.html", {"authors": authors})


def author_detail(request, pk):
    author = get_object_or_404(Author, pk=pk)
    return render(request, "blog/author_detail.html", {"author": author})

@extend_schema(tags=["Authors"])
class AuthorViewSet(viewsets.ModelViewSet):
    queryset = Author.objects.all()
    serializer_class = AuthorSerializer
    permission_classes = [IsAuthenticated]

@extend_schema(tags=["Blogs"])
class BlogViewSet(viewsets.ModelViewSet):
    queryset = Blog.objects.all()
    serializer_class = BlogSerializer
    permission_classes = [IsAuthenticated]

#form views
def blog_list(request):
    blogs = Blog.objects.select_related("author")
    return render(request,"blog/blog_list.html",{"blogs":blogs})

def blog_detail(request,pk):
    blog =get_object_or_404(Blog.objects.select_related("author"),pk=pk)
    return render(request,"blog/blog_detail.html",{"blog":blog})

def blog_create(request):
    if request.method == "POST":
        form = Blogform(request.POST)
        if form.is_valid():
            blog = form.save()
            messages.sucess(request,f"created '{blog.title}'.")
            return redirect("blog:post-details",pk=blog.pk)
    else:
         form = Blogform()

         return render(
             request,
             "blog/blog_form.html",
            {"form":form,"heading":"New post","submit_label":"create poat"}, 
         )

def blog_update(request,pk):
    blog = get_object_or_404(Blog,pk=pk)

    if request.method == "POST":

        form = Blogform(request.POST, instance=blog)
        if form.is_valid():
            blog = form.save()
            messages.success(request, f"Saved '{blog.title}'.")
            return redirect("blog:post-detail", pk=blog.pk)
    else:
        form = Blogform(instance=blog)
    
    return render(
        request,
        "blog/blog_form.html",
        {
            "form": form,
            "blog": blog,
            "heading":f"Edit '{blog.title}'",
            "submit_label":"Save Changes",
        },
    )

def blog_delete(request,pk):
    blog = get_object_or_404(Blog, pk=pk)

    if request.method == "POST":
        title = blog.title
        blog.delete()
        messages.success(request, f"Deleted '{title}'.")
        return redirect("blog:post_list")
    return render(request, "blog/blog_confirm_delete.html", {"blog": blog})
