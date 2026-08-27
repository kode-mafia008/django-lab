"""Load a small, realistic dataset so every page has something to show.

Run with:  python manage.py shell < seed.py
Safe to re-run: it clears the catalog tables first.
"""
from datetime import date
from decimal import Decimal

from blog.models import Author, AuthorProfile, Book, Genre

Book.objects.all().delete()
Genre.objects.all().delete()
AuthorProfile.objects.all().delete()
Author.objects.all().delete()

herbert = Author.objects.create(name="Frank Herbert", bio="American science-fiction writer.")
austen = Author.objects.create(name="Jane Austen")
mccarthy = Author.objects.create(name="Cormac McCarthy")
mitchell = Author.objects.create(name="David Mitchell")

AuthorProfile.objects.create(author=herbert, country="United States", website="https://dunenovels.com")
AuthorProfile.objects.create(author=austen, country="United Kingdom")

scifi = Genre.objects.create(name="sci-fi")
classic = Genre.objects.create(name="classic")
dystopia = Genre.objects.create(name="dystopia")
literary = Genre.objects.create(name="literary")

rows = [
    ("Dune",          1965, "9.99",  herbert,  [scifi, classic],    date(1965, 8, 1)),
    ("Dune Messiah",  1969, "8.50",  herbert,  [scifi],             date(1969, 7, 1)),
    ("Children of Dune", 1976, "8.50", herbert, [scifi],            None),
    ("Emma",          1815, "5.50",  austen,   [classic],           None),
    ("Pride and Prejudice", 1813, "5.50", austen, [classic],        None),
    ("The Road",      2006, "12.00", mccarthy, [dystopia, literary], date(2006, 9, 26)),
    ("Blood Meridian", 1985, "11.00", mccarthy, [literary],         None),
    ("Cloud Atlas",   2004, "13.25", mitchell, [literary, scifi],   None),
    ("number9dream",  2001, "10.00", mitchell, [literary],          None),
    ("Ghostwritten",  1999, "10.00", mitchell, [literary],          None),
]

for title, year, price, author, genres, published in rows:
    book = Book.objects.create(
        title=title, year=year, price=Decimal(price),
        author=author, published=published,
    )
    book.genres.set(genres)

print(f"Seeded {Author.objects.count()} authors, "
      f"{Genre.objects.count()} genres, "
      f"{Book.objects.count()} books.")
