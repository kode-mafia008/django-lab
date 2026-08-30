from django.shortcuts import render
from .models import Author

def author_list(request):
    authors = Author.objects.all()
    
    return render(request, "blog/author_list.html", {"authors": authors, "raw_sql": raw_sql})