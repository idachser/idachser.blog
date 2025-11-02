from django.contrib import admin

from .models import MediaFile, Post, Tag


class MediaFileInline(admin.TabularInline):
    model = MediaFile
    extra = 1
    fields = ["file"]


class PostAdmin(admin.ModelAdmin):
    inlines = [MediaFileInline]


admin.site.register(Tag)
admin.site.register(Post, PostAdmin)
