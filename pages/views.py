import markdown
from django.shortcuts import get_object_or_404, render

from .models import AboutMeInfo


def about(request):
    md = markdown.Markdown(extensions=["fenced_code"])
    about_info = get_object_or_404(AboutMeInfo)
    about_info.body = md.convert(about_info.body)
    return render(request, "pages/about.html", {"info": about_info})
