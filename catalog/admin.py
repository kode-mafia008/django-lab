from django.contrib import admin

from .models import Author, AuthorProfile, Book, Genre


@admin.register(Author)
class AuthorAdmin(admin.ModelAdmin):
    list_display = ("name",)
    search_fields = ("name",)


@admin.register(Book)
class BookAdmin(admin.ModelAdmin):
    list_display = ("title", "author", "year", "price", "added_on")
    list_filter = ("year", "genres")
    search_fields = ("title", "author__name")
    filter_horizontal = ("genres",)
    ordering = ("-year",)
    list_per_page = 25


admin.site.register(Genre)
admin.site.register(AuthorProfile)
