from django.shortcuts import render
from .models import Author


def author_list(request):
    authors= Author.objects.all()
    return render(request,"author_list.html",{"authors":authors})


# Create your views here.
