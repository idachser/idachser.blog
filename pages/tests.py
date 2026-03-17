from unittest.mock import Mock, patch

from django.http import Http404, HttpResponse
from django.test import RequestFactory, TestCase

from .models import AboutMeInfo
from . import views


class AboutPageTests(TestCase):
    def setUp(self):
        self.factory = RequestFactory()

    @patch.object(views.markdown, "Markdown")
    def test_about_page_renders_existing_record_without_asserting_html(self, markdown_class):
        converter = Mock()
        converter.convert.return_value = "converted-body"
        markdown_class.return_value = converter
        AboutMeInfo.objects.create(title="About Me", body="**bio**")

        request = self.factory.get("/about/")
        capture = Mock(return_value=HttpResponse("ok"))

        with patch.object(views, "render", capture):
            response = views.about(request)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(capture.call_args.args[1], "pages/about.html")
        info = capture.call_args.args[2]["info"]
        self.assertEqual(info.title, "About Me")
        self.assertEqual(info.body, "converted-body")
        markdown_class.assert_called_once_with(extensions=["fenced_code"])
        converter.convert.assert_called_once_with("**bio**")

    def test_about_page_returns_404_without_record(self):
        request = self.factory.get("/about/")

        with self.assertRaises(Http404):
            views.about(request)
