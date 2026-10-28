import os
from datetime import date
from io import BytesIO
from tempfile import TemporaryDirectory
from unittest.mock import Mock, patch

from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.core.files.uploadedfile import SimpleUploadedFile
from django.http import Http404, HttpResponse
from django.test import (
    Client,
    RequestFactory,
    TestCase,
    modify_settings,
    override_settings,
)
from django.urls import reverse
from PIL import Image

from rss.feeds import PostsFeed

from .models import MediaFile, Post, PostVote, Tag
from .templatetags.blog_extras import (
    score_class,
    signed_score,
    plain_score,
)
from . import views


class BlogViewTests(TestCase):
    def setUp(self):
        self.factory = RequestFactory()
        self.tag = Tag.objects.create(name="django")
        self.other_tag = Tag.objects.create(name="python")

    def create_post(
        self,
        title,
        publish_date,
        *,
        published=True,
        tags=None,
        body="body",
        description="desc",
    ):
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

    @patch.object(
        views, "render_md", side_effect=lambda text: f"rendered::{text}"
    )
    def test_posts_list_filters_paginates_and_renders_descriptions(
        self, render_md
    ):
        posts = [
            self.create_post(
                f"Post {index}",
                date(2025, 1, index),
                tags=[self.tag],
                description=f"desc-{index}",
            )
            for index in range(1, 7)
        ]
        self.create_post(
            "Draft Post",
            date(2025, 1, 10),
            published=False,
            description="draft",
        )

        request = self.factory.get("/")
        capture = Mock(return_value=HttpResponse("ok"))

        with patch.object(views, "render", capture):
            response = views.posts_list(request)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(capture.call_args.args[1], "blog/posts.html")
        page = capture.call_args.args[2]["posts"]
        self.assertEqual(page.paginator.count, 6)
        self.assertEqual(len(page.object_list), 5)
        self.assertEqual(
            [post.title for post in page.object_list],
            [post.title for post in reversed(posts[1:])],
        )
        render_md.assert_any_call("desc-2")
        render_md.assert_any_call("desc-6")
        self.assertEqual(render_md.call_count, 5)

    def test_posts_list_renders_pagination_controls_with_multiple_pages(self):
        for index in range(1, 7):
            self.create_post(f"Post {index}", date(2025, 1, index))

        response = self.client.get("/")

        self.assertContains(response, "?page=2")

    def test_posts_list_hides_pagination_controls_with_single_page(self):
        self.create_post("Only Post", date(2025, 1, 1))

        response = self.client.get("/")

        self.assertNotContains(response, "?page=")

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

    @patch.object(
        views, "render_md", side_effect=lambda text: f"rendered::{text}"
    )
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
        self.create_post(
            "Other Tag",
            date(2025, 2, 3),
            tags=[self.other_tag],
            description="other-tag",
        )
        self.create_post(
            "Tagged Draft",
            date(2025, 2, 4),
            published=False,
            tags=[self.tag],
            description="draft",
        )

        request = self.factory.get(f"/tags/{self.tag.slug}")
        capture = Mock(return_value=HttpResponse("ok"))

        with patch.object(views, "render", capture):
            response = views.tagged_posts_list(request, self.tag.slug)

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

    def test_tagged_posts_reachable_by_generated_slug(self):
        tag = Tag.objects.create(name="Data Science")
        self.create_post("Tagged", date(2025, 6, 1), tags=[tag])

        request = self.factory.get(f"/tags/{tag.slug}")
        capture = Mock(return_value=HttpResponse("ok"))

        with patch.object(views, "render", capture):
            response = views.tagged_posts_list(request, tag.slug)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(capture.call_args.kwargs["context"]["tag"], tag)

    def test_tagged_posts_list_returns_404_for_missing_tag(self):
        request = self.factory.get("/tags/missing")

        with self.assertRaises(Http404):
            views.tagged_posts_list(request, "missing")

    def test_tagged_posts_list_returns_404_when_only_unpublished_posts_match(
        self,
    ):
        self.create_post(
            "Tagged Draft", date(2025, 2, 4), published=False, tags=[self.tag]
        )

        request = self.factory.get(f"/tags/{self.tag.slug}")

        with self.assertRaises(Http404):
            views.tagged_posts_list(request, self.tag.slug)

    @patch.object(views, "render_md", return_value="rendered-body")
    def test_post_detail_uses_slug_and_renders_body(self, render_md):
        post = self.create_post(
            "Detail Post", date(2025, 3, 1), body="**content**"
        )

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
        post = self.create_post(
            "Draft Detail", date(2025, 3, 2), published=False
        )

        request = self.factory.get(f"/post/{post.slug}/")

        with self.assertRaises(Http404):
            views.post_detail(request, post.slug)

    def test_tags_list_returns_all_tags(self):
        self.create_post(
            "Published Django 1", date(2025, 4, 1), tags=[self.tag]
        )
        self.create_post(
            "Published Django 2", date(2025, 4, 2), tags=[self.tag]
        )
        self.create_post(
            "Published Python", date(2025, 4, 3), tags=[self.other_tag]
        )
        self.create_post(
            "Draft Django", date(2025, 4, 4), published=False, tags=[self.tag]
        )

        request = self.factory.get("/tags/")
        capture = Mock(return_value=HttpResponse("ok"))

        with patch.object(views, "render", capture):
            response = views.tags_list(request)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(capture.call_args.args[1], "blog/tags.html")
        tags = {
            tag.name: tag.article_count
            for tag in capture.call_args.args[2]["tags"]
        }
        self.assertEqual(tags, {"django": 2, "python": 1})


class BlogModelAndFeedTests(TestCase):
    def create_post(self, title, publish_date, *, published=True):
        return Post.objects.create(
            title=title,
            publish_date=publish_date,
            published=published,
            body="body",
            description="desc",
        )

    def make_uploaded_image(
        self, *, size=(50, 50), color="red", name="image.png"
    ):
        buff = BytesIO()
        image = Image.new("RGB", size, color=color)
        image.save(buff, format="PNG")
        return SimpleUploadedFile(
            name, buff.getvalue(), content_type="image/png"
        )

    def test_post_save_generates_slug_from_title(self):
        post = self.create_post("Hello Django World", date(2025, 4, 1))

        self.assertEqual(post.slug, "hello-django-world")

    def test_tag_save_generates_slug_from_name(self):
        tag = Tag.objects.create(name="Machine Learning")

        self.assertEqual(tag.slug, "machine-learning")

    def test_posts_feed_returns_only_published_posts_in_descending_order(self):
        older = self.create_post("Older", date(2025, 1, 1), published=True)
        newest = self.create_post("Newest", date(2025, 1, 3), published=True)
        self.create_post("Draft", date(2025, 1, 4), published=False)
        middle = self.create_post("Middle", date(2025, 1, 2), published=True)

        items = list(PostsFeed().items())

        self.assertEqual(items, [newest, middle, older])

    def test_posts_feed_renders_markdown_descriptions(self):
        post = Post.objects.create(
            title="Feed Post",
            publish_date=date(2025, 1, 5),
            published=True,
            body="body",
            description="**bold** desc",
        )

        description = PostsFeed().item_description(post)

        self.assertIn("<strong>bold</strong>", description)

    def test_posts_feed_includes_item_author(self):
        self.create_post("Authored", date(2025, 1, 6))

        response = self.client.get("/rss/")

        self.assertContains(response, "Ingvar Dachser")

    def test_media_file_save_rejects_non_image_uploads(self):
        post = self.create_post("With Upload", date(2025, 5, 1))
        upload = SimpleUploadedFile(
            "broken.txt", b"not-an-image", content_type="text/plain"
        )

        with self.assertRaises(ValidationError):
            MediaFile(post=post, file=upload).save()

    def test_media_file_resave_without_new_upload_keeps_single_file(self):
        post = self.create_post("With Media Resave", date(2025, 5, 3))

        with TemporaryDirectory() as media_root:
            with self.settings(MEDIA_ROOT=media_root):
                media = MediaFile(post=post, file=self.make_uploaded_image())
                media.save()
                saved_name = media.file.name

                media.save()

                self.assertEqual(media.file.name, saved_name)
                media_dir = os.path.dirname(media.file.path)
                self.assertEqual(os.listdir(media_dir), ["image.jpg"])

    def test_media_file_replacing_upload_removes_previous_file(self):
        post = self.create_post("With Replaced Media", date(2025, 5, 4))

        with TemporaryDirectory() as media_root:
            with self.settings(MEDIA_ROOT=media_root):
                media = MediaFile(post=post, file=self.make_uploaded_image())
                media.save()
                old_path = media.file.path

                media.file = self.make_uploaded_image(name="other.png")
                media.save()

                self.assertFalse(os.path.exists(old_path))
                self.assertTrue(media.file.name.endswith("other.jpg"))

    def test_post_delete_removes_saved_media_file(self):
        post = self.create_post("With Media", date(2025, 5, 2))

        with TemporaryDirectory() as media_root:
            with self.settings(MEDIA_ROOT=media_root):
                media = MediaFile(post=post, file=self.make_uploaded_image())
                media.save()
                saved_path = media.file.path

                self.assertTrue(saved_path.endswith("image.jpg"))
                with Image.open(saved_path) as saved_image:
                    self.assertEqual(saved_image.format, "JPEG")

                post.delete()

                self.assertFalse(os.path.exists(saved_path))


@modify_settings(INSTALLED_APPS={"append": "django.contrib.admin"})
@override_settings(ROOT_URLCONF="website.urls")
class PostPreviewAdminTests(TestCase):
    def setUp(self):
        self.post = Post.objects.create(
            title="Draft",
            publish_date=date(2025, 5, 1),
            published=False,
            body="**bold draft**",
        )
        self.preview_url = reverse(
            "admin:blog_post_preview", args=[self.post.pk]
        )
        self.admin_user = get_user_model().objects.create_superuser(
            "admin", "admin@example.com", "password"
        )

    def test_preview_renders_unpublished_post_for_staff(self):
        self.client.force_login(self.admin_user)

        response = self.client.get(self.preview_url)

        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "blog/post_detail.html")
        self.assertContains(response, "<strong>bold draft</strong>", html=True)
        self.assertContains(response, "Preview — not published")
        self.assertEqual(response["X-Robots-Tag"], "noindex, nofollow")

    def test_preview_of_published_post_omits_not_published_note(self):
        self.post.published = True
        self.post.save()
        self.client.force_login(self.admin_user)

        response = self.client.get(self.preview_url)

        self.assertContains(response, "Preview")
        self.assertNotContains(response, "not published")

    def test_preview_hides_voting(self):
        self.client.force_login(self.admin_user)

        response = self.client.get(self.preview_url)

        self.assertNotContains(response, 'id="vote"')
        self.assertNotContains(response, "data-score")

    def test_admin_pages_load_site_palette_stylesheet(self):
        response = self.client.get(reverse("admin:login"))

        self.assertContains(response, "css/admin.css")
        self.assertContains(response, "admin/css/base.css")

    def test_admin_header_uses_blog_name(self):
        response = self.client.get(reverse("admin:login"))

        self.assertContains(response, "idachser.blog administration")

    def test_preview_redirects_anonymous_user_to_login(self):
        response = self.client.get(self.preview_url)

        self.assertEqual(response.status_code, 302)
        self.assertIn(reverse("admin:login"), response["Location"])

    def test_preview_redirects_non_staff_user_to_login(self):
        user = get_user_model().objects.create_user("reader", password="pw")
        self.client.force_login(user)

        response = self.client.get(self.preview_url)

        self.assertEqual(response.status_code, 302)
        self.assertIn(reverse("admin:login"), response["Location"])

    def test_preview_forbidden_for_staff_without_view_permission(self):
        user = get_user_model().objects.create_user(
            "staff", password="pw", is_staff=True
        )
        self.client.force_login(user)

        response = self.client.get(self.preview_url)

        self.assertEqual(response.status_code, 403)

    def test_preview_returns_404_for_missing_post(self):
        self.client.force_login(self.admin_user)

        response = self.client.get(
            reverse("admin:blog_post_preview", args=[self.post.pk + 100])
        )

        self.assertEqual(response.status_code, 404)

    def test_change_form_links_to_preview(self):
        self.client.force_login(self.admin_user)

        change = self.client.get(
            reverse("admin:blog_post_change", args=[self.post.pk])
        )
        add = self.client.get(reverse("admin:blog_post_add"))

        self.assertContains(change, self.preview_url)
        self.assertNotContains(add, "/preview/")

    def test_public_detail_still_hides_draft(self):
        response = self.client.get(
            reverse("post_detail", args=[self.post.slug])
        )

        self.assertEqual(response.status_code, 404)


class PostVoteTests(TestCase):
    def setUp(self):
        self.post = Post.objects.create(
            title="Votable",
            publish_date=date(2025, 7, 1),
            published=True,
            body="body",
        )
        self.url = reverse("post_vote", args=[self.post.slug])

    def vote(self, value, *, client=None, ip="10.0.0.1", json=True):
        client = client or self.client
        headers = {"Accept": "application/json"} if json else {}
        return client.post(
            self.url, {"value": value}, REMOTE_ADDR=ip, headers=headers
        )

    def score(self):
        return sum(v.value for v in PostVote.objects.filter(post=self.post))

    def test_get_is_not_allowed(self):
        self.assertEqual(self.client.get(self.url).status_code, 405)

    def test_unpublished_post_returns_404(self):
        draft = Post.objects.create(
            title="Draft", publish_date=date(2025, 7, 2), body="b"
        )
        response = self.client.post(
            reverse("post_vote", args=[draft.slug]), {"value": "1"}
        )
        self.assertEqual(response.status_code, 404)

    def test_invalid_value_returns_400(self):
        for value in ["2", "0", "abc", ""]:
            self.assertEqual(self.vote(value).status_code, 400)
        self.assertFalse(PostVote.objects.exists())

    def test_csrf_is_enforced(self):
        client = Client(enforce_csrf_checks=True)
        self.assertEqual(self.vote("1", client=client).status_code, 403)

    def test_first_vote_sets_cookie_and_returns_score(self):
        response = self.vote("1")

        self.assertEqual(response.json(), {"score": 1, "vote": 1})
        self.assertIn(views.VOTER_COOKIE, response.cookies)
        self.assertTrue(response.cookies[views.VOTER_COOKIE]["httponly"])

    def test_repeating_same_vote_removes_it(self):
        self.vote("1")
        response = self.vote("1")

        self.assertEqual(response.json(), {"score": 0, "vote": None})
        self.assertFalse(PostVote.objects.exists())

    def test_opposite_vote_flips_it(self):
        self.vote("1")
        response = self.vote("-1")

        self.assertEqual(response.json(), {"score": -1, "vote": -1})
        self.assertEqual(PostVote.objects.count(), 1)

    def test_same_ip_with_new_cookie_changes_existing_vote(self):
        self.vote("1", client=Client())
        response = self.vote("-1", client=Client())

        self.assertEqual(response.json()["score"], -1)
        self.assertEqual(PostVote.objects.count(), 1)

    def test_real_ip_header_takes_precedence(self):
        Client().post(
            self.url,
            {"value": "1"},
            REMOTE_ADDR="172.18.0.5",
            HTTP_X_REAL_IP="1.1.1.1",
        )
        Client().post(
            self.url,
            {"value": "1"},
            REMOTE_ADDR="172.18.0.5",
            HTTP_X_REAL_IP="2.2.2.2",
        )

        self.assertEqual(PostVote.objects.count(), 2)

    def test_same_cookie_from_new_ip_changes_existing_vote(self):
        self.vote("1", ip="10.0.0.1")
        self.vote("-1", ip="10.0.0.2")

        self.assertEqual(PostVote.objects.count(), 1)
        self.assertEqual(self.score(), -1)

    def test_different_visitors_votes_add_up(self):
        for index in range(3):
            self.vote("1", client=Client(), ip=f"10.0.0.{index}")
        self.vote("-1", client=Client(), ip="10.0.1.1")

        self.assertEqual(self.score(), 2)

    def test_non_json_vote_redirects_to_vote_block(self):
        response = self.vote("1", json=False)

        self.assertRedirects(
            response,
            reverse("post_detail", args=[self.post.slug]) + "#vote",
            fetch_redirect_response=False,
        )
        self.assertEqual(self.score(), 1)

    def test_post_detail_does_not_set_voter_cookie(self):
        response = self.client.get(
            reverse("post_detail", args=[self.post.slug])
        )

        self.assertNotIn(views.VOTER_COOKIE, response.cookies)

    def test_post_detail_shows_score_and_active_vote(self):
        self.vote("-1")
        self.vote("-1", client=Client(), ip="10.0.0.2")

        response = self.client.get(
            reverse("post_detail", args=[self.post.slug])
        )

        self.assertContains(
            response, 'class="score score--neg" data-score>\u22122<'
        )
        self.assertContains(
            response, 'class="score score--neg" data-score="plain">\u22122<'
        )
        self.assertContains(response, 'value="-1" class="vote-btn is-active"')
        self.assertContains(response, 'value="1" class="vote-btn"')

    def test_posts_list_shows_zero_score(self):
        response = self.client.get("/")

        self.assertContains(
            response, 'class="score score--zero" data-score>+0<'
        )

    def test_tag_page_score_is_not_multiplied_by_tags(self):
        first = Tag.objects.create(name="one")
        second = Tag.objects.create(name="two")
        self.post.tags.set([first, second])
        for index in range(3):
            self.vote("1", client=Client(), ip=f"10.0.0.{index}")

        response = self.client.get(reverse("tagged_posts", args=[first.slug]))

        self.assertContains(response, 'class="score score--pos" data-score>+3<')

    def test_score_filters(self):
        self.assertEqual(signed_score(0), "+0")
        self.assertEqual(signed_score(5), "+5")
        self.assertEqual(signed_score(-2), "\u22122")
        self.assertEqual(plain_score(-2), "\u22122")
        self.assertEqual(plain_score(0), "0")
        self.assertEqual(plain_score(3), "3")
        self.assertEqual(score_class(0), "score--zero")
        self.assertEqual(score_class(3), "score--pos")
        self.assertEqual(score_class(-1), "score--neg")
