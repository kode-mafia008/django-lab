from django.shortcuts import render
from .models import Author

# Create your views here.

def author_list(request):
    authors = Author.objects.all() # ORM (Object Relational Mapping) query to fetch all authors from the database
    print(authors.query)  # print the raw SQL query to the console for debugging purposes
    return render(request, "author_list.html", {"authors": authors})
    