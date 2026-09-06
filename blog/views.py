from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied
from django.db.models import Q
from django.shortcuts import get_object_or_404, redirect, render

from .forms import BlogForm
from .models import Author, Blog
from .throttling import rate_limit


def visible_blogs(user):
    """The posts `user` is allowed to see: everything published, plus their own drafts.

    The API enforces the same rule in `BlogViewSet.get_queryset()`. Two clients,
    one rule — but it has to be written twice, because a permission class
    protects a DRF view and nothing else. `@login_required` and
    `permission_classes` do not know about each other.
    """
    posts = Blog.objects.select_related("author", "owner")
    if not user.is_authenticated:
        # `Q(owner=AnonymousUser())` is a TypeError, not an empty result — an
        # anonymous branch is required, not optional.
        return posts.filter(published=True)
    return posts.filter(Q(published=True) | Q(owner=user))


def owned_blog_or_403(request, pk):
    """Fetch a post for editing, or refuse with 403.

    A deliberate difference from the API. `BlogViewSet` scopes its queryset, so
    a post you may not touch comes back as a 404 and leaks nothing. Here the
    answer is an explicit 403, because the caller is a person who followed a
    link and "you cannot edit this" is more useful to them than "no such page".

    Both are defensible. What is not defensible is picking neither — which is
    what this view did until today.
    """
    blog = get_object_or_404(Blog, pk=pk)
    if blog.owner_id is None or blog.owner_id != request.user.id:
        raise PermissionDenied("You can only change posts you created.")
    return blog


def author_list(request):
    authors = Author.objects.order_by("name")
    return render(request, "blog/author_list.html", {"authors": authors})


def author_detail(request, pk):
    author = get_object_or_404(Author, pk=pk)
    return render(request, "blog/author_detail.html", {"author": author})


# ---------------------------------------------------------------------------
# Blog CRUD, rendered as HTML pages by a ModelForm.
#
# Each of these is the same four-step shape:
#   GET  -> build an unbound (or instance-bound) form, render it
#   POST -> bind the form to request.POST, validate, save, redirect
# The redirect after a successful POST is not decoration: it stops a browser
# refresh from re-submitting the form.
# ---------------------------------------------------------------------------


def blog_list(request):
    blogs = visible_blogs(request.user)
    return render(request, "blog/blog_list.html", {"blogs": blogs})


@rate_limit(scope="blog-detail", rate="30/min")
def blog_detail(request, pk):
    """One post, rendered — and the busiest read in the app.

    Rate-limited because it is the obvious scraping target: it is public for
    published posts, it takes a row id in the URL, and walking 1..n through it
    is how somebody copies the whole site. The limit is per account when signed
    in and per address when not; see `blog/throttling.py`.
    """
    # Somebody else's draft is a 404 here, exactly as it is over the API.
    blog = get_object_or_404(visible_blogs(request.user), pk=pk)
    return render(request, "blog/blog_detail.html", {"blog": blog})


@login_required
def blog_create(request):
    if request.method == "POST":
        form = BlogForm(request.POST)
        if form.is_valid():
            # `commit=False` builds the object without writing it, so the
            # server can add the fields the form is not allowed to carry.
            blog = form.save(commit=False)
            blog.owner = request.user
            blog.save()
            messages.success(request, f"Created '{blog.title}'.")
            return redirect("blog:post-detail", pk=blog.pk)
    else:
        form = BlogForm()

    return render(
        request,
        "blog/blog_form.html",
        {"form": form, "heading": "New post", "submit_label": "Create post"},
    )


@login_required
def blog_update(request, pk):
    blog = owned_blog_or_403(request, pk)

    if request.method == "POST":
        # `instance=` is the whole difference between create and update.
        form = BlogForm(request.POST, instance=blog)
        if form.is_valid():
            blog = form.save()
            messages.success(request, f"Saved '{blog.title}'.")
            return redirect("blog:post-detail", pk=blog.pk)
    else:
        form = BlogForm(instance=blog)

    return render(
        request,
        "blog/blog_form.html",
        {
            "form": form,
            "blog": blog,
            "heading": f"Edit '{blog.title}'",
            "submit_label": "Save changes",
        },
    )


@login_required
def blog_delete(request, pk):
    blog = owned_blog_or_403(request, pk)

    # A GET only ever shows the confirmation page. Deleting on GET would let
    # any link — or any crawler — destroy a row.
    if request.method == "POST":
        title = blog.title
        blog.delete()
        messages.success(request, f"Deleted '{title}'.")
        return redirect("blog:post-list")

    return render(request, "blog/blog_confirm_delete.html", {"blog": blog})
