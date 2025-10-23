from django.shortcuts import get_object_or_404, render

from .models import AboutMeInfo


def about(request):
    about_info = get_object_or_404(AboutMeInfo)
    return render(request, "pages/about.html", {"info": about_info})
