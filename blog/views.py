import markdown
from django.shortcuts import get_list_or_404, get_object_or_404, render

from .models import Post, Tag


def posts_list(request):
    posts = get_list_or_404(Post)
    return render(request, "blog/posts.html", {"posts": posts})


def post_detail(request, slug):
    md = markdown.Markdown(extensions=["fenced_code", "codehilite"])
    post = get_object_or_404(Post, slug=slug)
    post.body = md.convert(post.body)
    context = {"post": post}
    return render(request, "blog/post_detail.html", context)


def tags_list(request):
    tags = Tag.objects.all()
    return render(request, "blog/tags.html", {"tags": tags})
