from django.contrib import admin

from .models import AboutMeInfo


class AboutMeInfoAdmin(admin.ModelAdmin):
    def has_add_permission(self, request):
        if AboutMeInfo.objects.exists():
            return False
        return True


admin.site.register(AboutMeInfo, AboutMeInfoAdmin)
