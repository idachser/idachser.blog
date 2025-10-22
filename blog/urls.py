from django.urls import path

from . import views

urlpatterns = [
    path("", views.posts_list, name="posts"),
    path("<str:slug>/", views.post_detail, name="post_detail"),
]
