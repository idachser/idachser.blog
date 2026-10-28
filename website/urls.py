from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import include, path

from pages.views import about
from rss.feeds import PostsFeed

admin.site.site_header = "idachser.blog administration"
admin.site.site_title = "idachser.blog admin"

urlpatterns = [
    path("about/", about, name="about"),
    path("rss/", PostsFeed(), name="posts_feed"),
    path("", include("blog.urls")),
    path(settings.ADMIN_URL, admin.site.urls),
] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
