from django.shortcuts import render
from .models import Author

def author_list(request):
    authors = Author.objects.all() 
    print(authors.query)
    return render(request, 'author-list.html', {'authors': authors})