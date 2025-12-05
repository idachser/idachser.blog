from datetime import datetime as dt

import feedparser
import markdown
from django.shortcuts import get_object_or_404, render

from .models import AboutMeInfo


def about(request):
    md = markdown.Markdown(extensions=["fenced_code"])
    about_info = get_object_or_404(AboutMeInfo)
    about_info.body = md.convert(about_info.body)
    return render(request, "pages/about.html", {"info": about_info})


def news(request):
    it_news = feedparser.parse("https://rss.golem.de/rss.php?feed=ATOM1.0")
    sc_news = feedparser.parse(
        "https://www.spektrum.de/alias/rss/spektrum-de-rss-feed/996406"
    )

    news = []
    for entry in it_news.entries:
        new = {
            "title": entry.title,
            "pub_date": dt.strptime(f"{entry.published}", "%Y-%m-%dT%H:%M:%S%z"),
            "desc": entry.summary,
            "link": entry.link,
            "author": entry.author,
        }
        news.append(new)
    for entry in sc_news.entries:
        news.append(
            {
                "title": entry.title,
                "pub_date": dt.strptime(
                    f"{entry.published}", "%a, %d %b %Y %H:%M:%S %z"
                ),
                "desc": entry.summary,
                "link": entry.link,
                "author": entry.author if hasattr(entry, "author") else "Unknown",
                "categories": [tag["term"] for tag in getattr(entry, "tags", [])[:3]],
            }
        )

    context = {
        "news": news,
    }
    return render(request, "pages/news.html", context=context)
