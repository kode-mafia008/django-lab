from rest_framework import serializers

from .models import Author, Blog


class AuthorSerializer(serializers.ModelSerializer):

    class Meta:
        model = Author
        fields = [
            'id',
            'name',
            'bio'
        ]
        read_only_fields = ['id']


class BlogSerializer(serializers.ModelSerializer):
    """`Meta.fields` is an allowlist, and that is a security control.

    A serializer that lists its fields explicitly cannot be surprised by a
    field added to the model later. `fields = "__all__"` can, and the field it
    exposes is always the one you least wanted to expose.
    """

    # Output only. The client sees who owns a post; it never gets to say so.
    # If this were writable, "create a post as somebody else" would be one
    # extra key in the JSON body.
    # `default=None` matters: without it, a row whose owner is NULL drops the
    # key from the JSON entirely instead of reporting `"owner": null`, and a
    # response shape that changes per row is a bug waiting to be written.
    owner = serializers.ReadOnlyField(source="owner.username", default=None)

    class Meta:
        model = Blog
        fields = [
            'id',
            'title',
            'content',
            'author',
            'owner',
            'published',
            'created_at',
            'updated_at'
        ]
        # Server-owned values. Anything a client is allowed to set is a field
        # you have to validate; anything it is not allowed to set is a field
        # you have to make read-only *here*, not in the view.
        read_only_fields = ['id', 'owner', 'created_at', 'updated_at']
