from django.shortcuts import render
from .models import Author


# Create your views here.
def author_list(request):
    authors = Author.objects.all() #ORM(OBJECT OPERATIONAL MAPPING)
    return render(request, "author_list.html", {"authors": authors})