"""What may be uploaded — an allowlist, and what it does not promise.

`Media.file` is a `FileField`, not an `ImageField`, because `ImageField` needs
Pillow and Pillow is not installed here. So Django is not opening the file to
check that an "image" is an image. This module is what stands in its place, and
it is honest about being weaker than that:

* **The content type is not evidence.** `f.content_type` is copied from what the
  browser sent, and the browser is the caller. Anything can claim `image/png`.
* **The name is not evidence either.** It arrives from the client, so the
  extension is a claim about the bytes, not a fact about them.

What an extension allowlist plus a size cap actually buys is narrower and still
worth having: nothing outside a short, known set of names is ever written to
disk, one request cannot fill the disk, and one post cannot hold an unbounded
number of files. Path traversal is not on this list because Django already
handles it — `FileField.generate_filename` runs the name through
`validate_file_name`, so `../../etc/passwd` never becomes a path.
"""

from pathlib import PurePosixPath

from django.core.exceptions import ValidationError


# Four is what post_form.html tells the user, so four is what the server
# enforces. A limit stated only in the UI is not a limit.
MAX_FILES = 4
MAX_BYTES = 10 * 1024 * 1024

IMAGE_EXTENSIONS = {".jpg", ".jpeg", ".png", ".gif", ".webp"}
VIDEO_EXTENSIONS = {".mp4", ".webm", ".mov"}
ALLOWED_EXTENSIONS = IMAGE_EXTENSIONS | VIDEO_EXTENSIONS


def kind_for(name):
    """Return `Media.kind` for a file name, or None if it is not allowed."""
    suffix = PurePosixPath(name or "").suffix.lower()
    if suffix in VIDEO_EXTENSIONS:
        return "video"
    if suffix in IMAGE_EXTENSIONS:
        return "image"
    return None


def validate_upload(upload):
    """Check one file and return the `kind` it will be stored as.

    Raises `ValidationError` with a message a person can act on — "that file
    type" beats "invalid input", because the user is the one who has to pick a
    different file.
    """
    kind = kind_for(upload.name)
    if kind is None:
        raise ValidationError(
            "%(name)s: only %(allowed)s files can be uploaded.",
            params={
                "name": upload.name,
                "allowed": ", ".join(sorted(e.lstrip(".") for e in ALLOWED_EXTENSIONS)),
            },
        )
    if upload.size > MAX_BYTES:
        raise ValidationError(
            "%(name)s is %(size).1f MB. The limit is %(limit)s MB.",
            params={
                "name": upload.name,
                "size": upload.size / (1024 * 1024),
                "limit": MAX_BYTES // (1024 * 1024),
            },
        )
    return kind


def validate_uploads(uploads, existing=0):
    """Check a whole batch and return [(file, kind), ...].

    Every file is checked, not just the first, so someone who picks four wrong
    files is told about four of them once instead of one of them four times.
    `existing` is how many the post already has, because editing a post with
    three files and adding two is five files.
    """
    uploads = list(uploads)
    if existing + len(uploads) > MAX_FILES:
        raise ValidationError(
            "A post can hold %(max)d files and this one would have %(count)d.",
            params={"max": MAX_FILES, "count": existing + len(uploads)},
        )

    checked, errors = [], []
    for upload in uploads:
        try:
            checked.append((upload, validate_upload(upload)))
        except ValidationError as exc:
            errors.extend(exc.messages)
    if errors:
        raise ValidationError(errors)
    return checked
