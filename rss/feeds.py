from django.contrib.syndication.views import Feed
from django.urls import reverse

from blog.models import Post


class PostsFeed(Feed):
    title = "idachser.blog"
    link = "/rss/"
    description = "Latest posts from idachser.blog"

    def items(self):
        return Post.objects.filter(published=True).order_by("-publish_date")[:10]

    def item_title(self, item):
        return item.title

    def item_author(self):
        return "Ingvar Dachser"

    def item_description(self, item):
        return item.description

    def item_copyright(self):
        return "idachser.blog"

    def item_link(self, item):
        return reverse("post_detail", args=[item.slug])
