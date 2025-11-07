from io import BytesIO

from django.core.files.base import ContentFile
from django.db import models
from django.utils.text import slugify
from PIL import Image


class Tag(models.Model):
    name = models.CharField(max_length=50, unique=True)

    def __str__(self):
        return str(self.name)


class Post(models.Model):
    title = models.CharField(max_length=200, unique=True)
    description = models.TextField(max_length=500, blank=True)
    slug = models.SlugField(max_length=200, unique=True, blank=True)
    publish_date = models.DateField()
    published = models.BooleanField(default=False)
    author = models.CharField(max_length=50, default="idachser")
    body = models.TextField()
    tags = models.ManyToManyField(Tag, blank=True)

    class Meta:
        ordering = ["-publish_date"]

    def __str__(self):
        return str(self.title)

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.title)

        super().save(*args, **kwargs)


def media_file_path(instance, filename) -> str:
    return f"post_{instance.post.id}/media/{filename}"


class MediaFile(models.Model):
    post = models.ForeignKey(Post, related_name="post_media", on_delete=models.CASCADE)
    file = models.FileField(upload_to=media_file_path, blank=True)

    def save(self, *args, **kwargs):
        """compress file and save"""

        img = Image.open(self.file)
        if img.mode != "RGB":
            img = img.convert("RGB")

        max_size = (1920, 1080)
        img.thumbnail(max_size, Image.Resampling.LANCZOS)

        buff = BytesIO()
        img.save(buff, format="JPEG", optimize=True, quality=75)
        self.file.save(self.file.name, ContentFile(buff.getvalue()), save=False)
        buff.close()
        super().save(*args, **kwargs)
