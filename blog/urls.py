from django.urls import path

from . import views

urlpatterns = [
    path("", views.posts_list, name="posts"),
    path("tags/", views.tags_list, name="tags"),
    path("tags/<slug:tag_slug>", views.tagged_posts_list, name="tagged_posts"),
    path("<str:slug>/", views.post_detail, name="post_detail"),
]
