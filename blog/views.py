import markdown
from django.core.paginator import Paginator
from django.shortcuts import get_list_or_404, get_object_or_404, render

from .models import Post, Tag


def render_md(text):
    config = {"mdx_math": {"enable_dollar_delimiter": True}}
    return markdown.markdown(
        text,
        extensions=["fenced_code", "codehilite", "extra", "mdx_math"],
        extension_configs=config,
    )


def posts_list(request):
    posts = Post.objects.filter(published=True).order_by("-publish_date")
    paginator = Paginator(posts, 5)

    page_number = request.GET.get("page")
    page_obj = paginator.get_page(page_number)

    for post in posts:
        post.description = render_md(post.description)

    return render(request, "blog/posts.html", {"posts": page_obj})


def tagged_posts_list(request, tag_slug):
    tag = get_object_or_404(Tag, name=tag_slug)
    posts = get_list_or_404(Post, tags=tag, published=True)
    paginator = Paginator(posts, 5)

    page_number = request.GET.get("page")
    page_obj = paginator.get_page(page_number)

    for post in posts:
        post.description = render_md(post.description)

    context = {"tag": tag, "posts": page_obj}

    return render(request, "blog/posts.html", context=context)


def post_detail(request, slug):
    post = get_object_or_404(Post, slug=slug)
    post.body = render_md(post.body)
    context = {"post": post}

    return render(request, "blog/post_detail.html", context)


def tags_list(request):
    tags = Tag.objects.all()
    return render(request, "blog/tags.html", {"tags": tags})
