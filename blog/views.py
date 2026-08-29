<<<<<<< HEAD
from django.shortcuts import render
from .models import Author


def author_list(request):
    authors= Author.objects.all()
    return render(request,"author_list.html",{"authors":authors})

=======
from django.shortcuts import get_object_or_404, render
>>>>>>> 4541acb24b5a23784c3febde83838a201d9a5815

from .models import Author


def author_list(request):
    authors = Author.objects.order_by("name")
    return render(request, "blog/author_list.html", {"authors": authors})


def author_detail(request, pk):
    author = get_object_or_404(Author, pk=pk)
    return render(request, "blog/author_detail.html", {"author": author})
