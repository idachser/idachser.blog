import hashlib
import hmac
import uuid

import markdown
from django.conf import settings
from django.db.models import Count, Q
from django.core.paginator import Paginator
from django.http import HttpResponseBadRequest, JsonResponse
from django.shortcuts import (
    get_list_or_404,
    get_object_or_404,
    redirect,
    render,
)
from django.urls import reverse
from django.views.decorators.http import require_POST

from .models import Post, PostVote, Tag, with_score

VOTER_COOKIE = "voter_id"
VOTER_COOKIE_SALT = "blog.vote"
VOTER_COOKIE_MAX_AGE = 365 * 24 * 60 * 60


def render_md(text):
    config = {"mdx_math": {"enable_dollar_delimiter": True}}
    return markdown.markdown(
        text,
        extensions=["fenced_code", "codehilite", "extra", "mdx_math"],
        extension_configs=config,
    )


def posts_list(request):
    posts = with_score(Post.objects.filter(published=True)).order_by(
        "-publish_date"
    )
    paginator = Paginator(posts, 5)

    page_number = request.GET.get("page")
    page_obj = paginator.get_page(page_number)

    for post in page_obj:
        post.description = render_md(post.description)

    return render(request, "blog/posts.html", {"posts": page_obj})


def tagged_posts_list(request, tag_slug):
    tag = get_object_or_404(Tag, slug=tag_slug)
    posts = get_list_or_404(with_score(Post.objects), tags=tag, published=True)
    paginator = Paginator(posts, 5)

    page_number = request.GET.get("page")
    page_obj = paginator.get_page(page_number)

    for post in page_obj:
        post.description = render_md(post.description)

    context = {"tag": tag, "posts": page_obj}

    return render(request, "blog/posts.html", context=context)


def post_detail(request, slug):
    post = get_object_or_404(
        with_score(Post.objects), slug=slug, published=True
    )
    post.body = render_md(post.body)
    voter_id = _voter_id(request)
    user_vote = (
        post.votes.filter(voter_id=voter_id)
        .values_list("value", flat=True)
        .first()
        if voter_id
        else None
    )
    context = {"post": post, "user_vote": user_vote}

    return render(request, "blog/post_detail.html", context)


def tags_list(request):
    tags = Tag.objects.annotate(
        article_count=Count("post", filter=Q(post__published=True))
    )
    return render(request, "blog/tags.html", {"tags": tags})


def _voter_id(request):
    return request.get_signed_cookie(
        VOTER_COOKIE, default=None, salt=VOTER_COOKIE_SALT
    )


def _client_ip_hash(request):
    # X-Real-IP is set by nginx, and gunicorn is not reachable directly.
    ip = request.META.get("HTTP_X_REAL_IP") or request.META.get(
        "REMOTE_ADDR", ""
    )
    return hmac.new(
        settings.SECRET_KEY.encode(), ip.encode(), hashlib.sha256
    ).hexdigest()


@require_POST
def vote(request, slug):
    post = get_object_or_404(Post, slug=slug, published=True)
    try:
        value = int(request.POST.get("value", ""))
    except ValueError:
        value = None
    if value not in (PostVote.UP, PostVote.DOWN):
        return HttpResponseBadRequest("Invalid vote.")

    voter_id = _voter_id(request) or str(uuid.uuid4())
    user_vote = PostVote.toggle(post, voter_id, _client_ip_hash(request), value)

    if "application/json" in request.headers.get("Accept", ""):
        score = with_score(Post.objects).get(pk=post.pk).score
        response = JsonResponse({"score": score, "vote": user_vote})
    else:
        response = redirect(reverse("post_detail", args=[post.slug]) + "#vote")
    response.set_signed_cookie(
        VOTER_COOKIE,
        voter_id,
        salt=VOTER_COOKIE_SALT,
        max_age=VOTER_COOKIE_MAX_AGE,
        httponly=True,
        samesite="Lax",
        secure=request.is_secure(),
    )
    return response
