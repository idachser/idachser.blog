import os
from io import BytesIO

from django.conf import settings
from django.core.exceptions import ValidationError
from django.core.files.base import ContentFile
from django.db import models
from django.utils.text import slugify
from PIL import Image

MAX_UPLOAD_PIXELS = 20_000_000


class Tag(models.Model):
    name = models.CharField(max_length=50, unique=True)

    def __str__(self):
        return str(self.name)


class Post(models.Model):
    LANGUAGE_CHOICES = {
        "en": "english",
        "de": "deutsch",
        "ru": "russian",
    }
    title = models.CharField(max_length=200, unique=True)
    language = models.CharField(max_length=2, choices=LANGUAGE_CHOICES, default="de")
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

    def delete(self, using=None, keep_parents=False):
        for media in self.post_media.all():
            media.delete()

        post_media_dir = os.path.join(settings.MEDIA_ROOT, f"post_{self.id}", "media")
        if os.path.exists(post_media_dir):
            os.removedirs(post_media_dir)

        return super().delete(using, keep_parents)


def media_file_path(instance, filename) -> str:
    return f"post_{instance.post.id}/media/{filename}"


class MediaFile(models.Model):
    post = models.ForeignKey(Post, related_name="post_media", on_delete=models.CASCADE)
    file = models.FileField(upload_to=media_file_path, blank=True)

    def save(self, *args, **kwargs):
        """compress file and save"""

        if not self.file:
            return super().save(*args, **kwargs)

        try:
            self.file.seek(0)
            with Image.open(self.file) as uploaded_image:
                uploaded_image.verify()

            self.file.seek(0)
            with Image.open(self.file) as uploaded_image:
                uploaded_image.load()
                img = uploaded_image.copy()
        except (Image.DecompressionBombError, OSError) as exc:
            raise ValidationError("Upload must be a valid, safe image.") from exc

        if img.width * img.height > MAX_UPLOAD_PIXELS:
            raise ValidationError("Image is too large.")

        if img.mode != "RGB":
            img = img.convert("RGB")

        max_size = (1920, 1080)
        img.thumbnail(max_size, Image.Resampling.LANCZOS)

        buff = BytesIO()
        img.save(buff, format="JPEG", optimize=True, quality=75)
        self.file.save(self.file.name, ContentFile(buff.getvalue()), save=False)
        buff.close()
        super().save(*args, **kwargs)

    def delete(self, using=None, keep_parents=False):
        if self.file and os.path.isfile(self.file.path):
            os.remove(self.file.path)
        return super().delete(using, keep_parents)
