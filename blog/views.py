from django.shortcuts import get_list_or_404, get_object_or_404, render

from .models import Post


def posts_list(request):
    posts = get_list_or_404(Post)
    return render(request, "blog/posts.html", {"posts": posts})


def post_detail(request, slug):
    post = get_object_or_404(Post, slug=slug)
    return render(request, "blog/post_detail.html", {"post": post})
