import markdown
from django.shortcuts import get_list_or_404, get_object_or_404, render

from .models import Post, Tag


def posts_list(request):
    md = markdown.Markdown(extensions=["fenced_code", "codehilite"])
    posts = Post.objects.filter(published=True).order_by("-publish_date")
    for post in posts:
        post.description = md.convert(post.description)
    return render(request, "blog/posts.html", {"posts": posts})


def tagged_posts_list(request, tag_slug):
    md = markdown.Markdown(extensions=["fenced_code", "codehilite"])
    tag = get_object_or_404(Tag, name=tag_slug)
    posts = get_list_or_404(Post, tags=tag, published=True)
    for post in posts:
        post.description = md.convert(post.description)
    context = {"tag": tag, "posts": posts}
    return render(request, "blog/posts.html", context=context)


def post_detail(request, slug):
    md = markdown.Markdown(extensions=["fenced_code", "codehilite"])
    post = get_object_or_404(Post, slug=slug)
    post.body = md.convert(post.body)
    context = {"post": post}
    return render(request, "blog/post_detail.html", context)


def tags_list(request):
    tags = Tag.objects.all()
    return render(request, "blog/tags.html", {"tags": tags})
