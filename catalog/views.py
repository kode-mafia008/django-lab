from django.db.models import Q
from django.shortcuts import get_object_or_404, render

from .models import Book


def book_list(request):
    books = Book.objects.select_related("author").prefetch_related("genres")
    return render(request, "catalog/book_list.html", {
        "page_title": "All books",
        "books": books,
        "total": books.count(),
    })


def book_detail(request, pk):
    book = get_object_or_404(
        Book.objects.select_related("author").prefetch_related("genres"), pk=pk
    )
    return render(request, "catalog/book_detail.html", {"book": book})


def book_search(request):
    q = request.GET.get("q", "").strip()
    books = Book.objects.select_related("author")
    if q:
        books = books.filter(
            Q(title__icontains=q) | Q(author__name__icontains=q)
        ).distinct()
    return render(request, "catalog/search.html", {"books": books, "q": q})


def about(request):
    return render(request, "catalog/about.html")
