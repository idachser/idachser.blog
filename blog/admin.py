from django.contrib import admin
from django.core.exceptions import PermissionDenied
from django.shortcuts import get_object_or_404, render
from django.urls import path

from .models import MediaFile, Post, Tag, with_score
from .views import render_md


class MediaFileInline(admin.TabularInline):
    model = MediaFile
    extra = 1
    fields = ["file"]


class PostAdmin(admin.ModelAdmin):
    inlines = [MediaFileInline]
    list_display = ["title", "publish_date", "published", "score"]

    def get_queryset(self, request):
        return with_score(super().get_queryset(request))

    @admin.display(ordering="score")
    def score(self, obj):
        return obj.score

    def get_urls(self):
        urls = [
            path(
                "<int:object_id>/preview/",
                self.admin_site.admin_view(self.preview_view),
                name="blog_post_preview",
            ),
        ]
        return urls + super().get_urls()

    def preview_view(self, request, object_id):
        post = get_object_or_404(Post, pk=object_id)
        if not self.has_view_permission(request, post):
            raise PermissionDenied
        post.body = render_md(post.body)
        response = render(
            request,
            "blog/post_detail.html",
            {"post": post, "is_preview": True},
        )
        response["X-Robots-Tag"] = "noindex, nofollow"
        return response


admin.site.register(Tag)
admin.site.register(Post, PostAdmin)
