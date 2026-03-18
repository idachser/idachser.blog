import os
from datetime import date
from io import BytesIO
from tempfile import TemporaryDirectory
from unittest.mock import Mock, patch

from django.core.exceptions import ValidationError
from django.core.files.uploadedfile import SimpleUploadedFile
from django.http import Http404, HttpResponse
from django.test import RequestFactory, TestCase
from PIL import Image

from rss.feeds import PostsFeed

from .models import MediaFile, Post, Tag
from . import views


class BlogViewTests(TestCase):
    def setUp(self):
        self.factory = RequestFactory()
        self.tag = Tag.objects.create(name="django")
        self.other_tag = Tag.objects.create(name="python")

    def create_post(self, title, publish_date, *, published=True, tags=None, body="body", description="desc"):
        post = Post.objects.create(
            title=title,
            publish_date=publish_date,
            published=published,
            body=body,
            description=description,
        )
        if tags:
            post.tags.set(tags)
        return post

    @patch.object(views, "render_md", side_effect=lambda text: f"rendered::{text}")
    def test_posts_list_filters_paginates_and_renders_descriptions(self, render_md):
        posts = [
            self.create_post(f"Post {index}", date(2025, 1, index), tags=[self.tag], description=f"desc-{index}")
            for index in range(1, 7)
        ]
        self.create_post("Draft Post", date(2025, 1, 10), published=False, description="draft")

        request = self.factory.get("/")
        capture = Mock(return_value=HttpResponse("ok"))

        with patch.object(views, "render", capture):
            response = views.posts_list(request)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(capture.call_args.args[1], "blog/posts.html")
        page = capture.call_args.args[2]["posts"]
        self.assertEqual(page.paginator.count, 6)
        self.assertEqual(len(page.object_list), 5)
        self.assertEqual([post.title for post in page.object_list], [post.title for post in reversed(posts[1:])])
        render_md.assert_any_call("desc-1")
        render_md.assert_any_call("desc-6")
        self.assertEqual(render_md.call_count, 6)

    def test_posts_list_second_page_returns_remaining_post(self):
        for index in range(1, 7):
            self.create_post(f"Post {index}", date(2025, 1, index))

        request = self.factory.get("/", {"page": 2})
        capture = Mock(return_value=HttpResponse("ok"))

        with patch.object(views, "render", capture):
            response = views.posts_list(request)

        self.assertEqual(response.status_code, 200)
        page = capture.call_args.args[2]["posts"]
        self.assertEqual(page.number, 2)
        self.assertFalse(page.has_next())
        self.assertEqual([post.title for post in page.object_list], ["Post 1"])

    @patch.object(views, "render_md", side_effect=lambda text: f"rendered::{text}")
    def test_tagged_posts_list_filters_by_tag_and_publication(self, render_md):
        tagged_new = self.create_post(
            "Tagged New",
            date(2025, 2, 2),
            tags=[self.tag],
            description="new-tagged",
        )
        tagged_old = self.create_post(
            "Tagged Old",
            date(2025, 2, 1),
            tags=[self.tag],
            description="old-tagged",
        )
        self.create_post("Other Tag", date(2025, 2, 3), tags=[self.other_tag], description="other-tag")
        self.create_post("Tagged Draft", date(2025, 2, 4), published=False, tags=[self.tag], description="draft")

        request = self.factory.get(f"/tags/{self.tag.name}")
        capture = Mock(return_value=HttpResponse("ok"))

        with patch.object(views, "render", capture):
            response = views.tagged_posts_list(request, self.tag.name)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(capture.call_args.args[1], "blog/posts.html")
        context = capture.call_args.kwargs["context"]
        self.assertEqual(context["tag"], self.tag)
        self.assertEqual(
            [post.title for post in context["posts"].object_list],
            [tagged_new.title, tagged_old.title],
        )
        render_md.assert_any_call("new-tagged")
        render_md.assert_any_call("old-tagged")
        self.assertEqual(render_md.call_count, 2)

    def test_tagged_posts_list_returns_404_for_missing_tag(self):
        request = self.factory.get("/tags/missing")

        with self.assertRaises(Http404):
            views.tagged_posts_list(request, "missing")

    def test_tagged_posts_list_returns_404_when_only_unpublished_posts_match(self):
        self.create_post("Tagged Draft", date(2025, 2, 4), published=False, tags=[self.tag])

        request = self.factory.get(f"/tags/{self.tag.name}")

        with self.assertRaises(Http404):
            views.tagged_posts_list(request, self.tag.name)

    @patch.object(views, "render_md", return_value="rendered-body")
    def test_post_detail_uses_slug_and_renders_body(self, render_md):
        post = self.create_post("Detail Post", date(2025, 3, 1), body="**content**")

        request = self.factory.get(f"/post/{post.slug}/")
        capture = Mock(return_value=HttpResponse("ok"))

        with patch.object(views, "render", capture):
            response = views.post_detail(request, post.slug)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(capture.call_args.args[1], "blog/post_detail.html")
        post_in_context = capture.call_args.args[2]["post"]
        self.assertEqual(post_in_context.title, "Detail Post")
        self.assertEqual(post_in_context.body, "rendered-body")
        render_md.assert_called_once_with("**content**")

    def test_post_detail_returns_404_for_unpublished_post(self):
        post = self.create_post("Draft Detail", date(2025, 3, 2), published=False)

        request = self.factory.get(f"/post/{post.slug}/")

        with self.assertRaises(Http404):
            views.post_detail(request, post.slug)

    def test_tags_list_returns_all_tags(self):
        request = self.factory.get("/tags/")
        capture = Mock(return_value=HttpResponse("ok"))

        with patch.object(views, "render", capture):
            response = views.tags_list(request)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(capture.call_args.args[1], "blog/tags.html")
        self.assertCountEqual([tag.name for tag in capture.call_args.args[2]["tags"]], ["django", "python"])


class BlogModelAndFeedTests(TestCase):
    def create_post(self, title, publish_date, *, published=True):
        return Post.objects.create(
            title=title,
            publish_date=publish_date,
            published=published,
            body="body",
            description="desc",
        )

    def make_uploaded_image(self, *, size=(50, 50), color="red", name="image.png"):
        buff = BytesIO()
        image = Image.new("RGB", size, color=color)
        image.save(buff, format="PNG")
        return SimpleUploadedFile(name, buff.getvalue(), content_type="image/png")

    def test_post_save_generates_slug_from_title(self):
        post = self.create_post("Hello Django World", date(2025, 4, 1))

        self.assertEqual(post.slug, "hello-django-world")

    def test_posts_feed_returns_only_published_posts_in_descending_order(self):
        older = self.create_post("Older", date(2025, 1, 1), published=True)
        newest = self.create_post("Newest", date(2025, 1, 3), published=True)
        self.create_post("Draft", date(2025, 1, 4), published=False)
        middle = self.create_post("Middle", date(2025, 1, 2), published=True)

        items = list(PostsFeed().items())

        self.assertEqual(items, [newest, middle, older])

    def test_media_file_save_rejects_non_image_uploads(self):
        post = self.create_post("With Upload", date(2025, 5, 1))
        upload = SimpleUploadedFile("broken.txt", b"not-an-image", content_type="text/plain")

        with self.assertRaises(ValidationError):
            MediaFile(post=post, file=upload).save()

    def test_post_delete_removes_saved_media_file(self):
        post = self.create_post("With Media", date(2025, 5, 2))

        with TemporaryDirectory() as media_root:
            with self.settings(MEDIA_ROOT=media_root):
                media = MediaFile(post=post, file=self.make_uploaded_image())
                media.save()
                saved_path = media.file.path

                self.assertTrue(saved_path.endswith("image.png"))
                with Image.open(saved_path) as saved_image:
                    self.assertEqual(saved_image.format, "JPEG")

                post.delete()

                self.assertFalse(os.path.exists(saved_path))
