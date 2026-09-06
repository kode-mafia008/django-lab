from django.contrib import admin

from .models import (
    Post,
    PostMedia,
    Comment,
    Like,
    SavedPost,
    Share,
)


@admin.register(Post)
class PostAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "author",
        "content_preview",
        "is_archived",
        "created_at",
        "updated_at",
    )

    list_filter = (
        "is_archived",
        "created_at",
        "updated_at",
    )

    search_fields = (
        "content",
        "author__username",
        "author__email",
    )

    readonly_fields = (
        "created_at",
        "updated_at",
    )

    def content_preview(self, obj):
        if not obj.content:
            return "(No text)"
        return obj.content[:60]

    content_preview.short_description = "Content"


@admin.register(PostMedia)
class PostMediaAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "post",
        "media_type",
        "file",
        "created_at",
    )

    list_filter = (
        "media_type",
        "created_at",
    )

    search_fields = (
        "post__content",
        "post__author__username",
    )

    readonly_fields = (
        "created_at",
    )



class ReplyInline(admin.TabularInline):
    model = Comment
    fk_name = "parent"

    extra = 0

    fields = (
        "author",
        "content",
        "created_at",
    )

    readonly_fields = (
        "created_at",
    )

    autocomplete_fields = (
        "author",
    )


@admin.register(Comment)
class CommentAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "post",
        "author",
        "comment_type",
        "parent",
        "content_preview",
        "created_at",
        "updated_at",
    )

    list_filter = (
        "created_at",
        "updated_at",
    )

    search_fields = (
        "content",
        "author__username",
        "author__email",
        "post__content",
    )

    readonly_fields = (
        "created_at",
        "updated_at",
    )

    autocomplete_fields = (
        "post",
        "author",
        "parent",
    )

    inlines = [
        ReplyInline,
    ]

    def content_preview(self, obj):
        if not obj.content:
            return "(No text)"

        return obj.content[:60]

    content_preview.short_description = "Content"

    def comment_type(self, obj):
        if obj.parent_id:
            return "Reply"

        return "Comment"

    comment_type.short_description = "Type"
    
    

@admin.register(Like)
class LikeAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "user",
        "post",
        "created_at",
    )

    list_filter = (
        "created_at",
    )

    search_fields = (
        "user__username",
        "user__email",
        "post__content",
    )

    readonly_fields = (
        "created_at",
    )


@admin.register(SavedPost)
class SavedPostAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "user",
        "post",
        "created_at",
    )

    list_filter = (
        "created_at",
    )

    search_fields = (
        "user__username",
        "user__email",
        "post__content",
    )

    readonly_fields = (
        "created_at",
    )


@admin.register(Share)
class ShareAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "user",
        "post",
        "created_at",
    )

    list_filter = (
        "created_at",
    )

    search_fields = (
        "user__username",
        "user__email",
        "post__content",
    )

    readonly_fields = (
        "created_at",
    )