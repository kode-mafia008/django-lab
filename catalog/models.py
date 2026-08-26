from django.db import models


class Author(models.Model):
    name = models.CharField(max_length=120)
    bio = models.TextField(blank=True)

    class Meta:
        db_table = "authors"
        ordering = ["name"]

    def __str__(self):
        return self.name


class AuthorProfile(models.Model):
    author = models.OneToOneField(
        Author, on_delete=models.CASCADE, related_name="profile"
    )
    website = models.URLField(blank=True)
    country = models.CharField(max_length=60, blank=True)

    def __str__(self):
        return f"Profile of {self.author.name}"


class Genre(models.Model):
    name = models.CharField(max_length=60, unique=True)

    class Meta:
        ordering = ["name"]

    def __str__(self):
        return self.name


class Book(models.Model):
    title = models.CharField(max_length=200)
    year = models.IntegerField()
    price = models.DecimalField(max_digits=8, decimal_places=2)
    isbn = models.CharField(max_length=13, blank=True)
    published = models.DateField(null=True, blank=True)
    added_on = models.DateTimeField(auto_now_add=True)

    author = models.ForeignKey(
        Author,
        on_delete=models.CASCADE,
        related_name="books",
        null=True,
        blank=True,
    )
    genres = models.ManyToManyField(Genre, related_name="books", blank=True)

    class Meta:
        ordering = ["-year", "title"]

    def __str__(self):
        return f"{self.title} ({self.year})"
