import os
import shutil
from io import BytesIO

from django.conf import settings
from django.core.exceptions import ValidationError
from django.core.files.base import ContentFile
from django.db import IntegrityError, models, transaction
from django.db.models import OuterRef, Subquery, Sum, Value
from django.db.models.functions import Coalesce
from django.db.models.signals import post_delete
from django.dispatch import receiver
from django.utils.text import slugify
from PIL import Image

MAX_UPLOAD_PIXELS = 20_000_000


class Tag(models.Model):
    name = models.CharField(max_length=50, unique=True)
    slug = models.SlugField(max_length=50, unique=True, blank=True)

    def __str__(self):
        return str(self.name)

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name) or "tag"
        super().save(*args, **kwargs)


class Post(models.Model):
    LANGUAGE_CHOICES = {
        "en": "english",
        "de": "deutsch",
        "ru": "russian",
    }
    title = models.CharField(max_length=200, unique=True)
    language = models.CharField(
        max_length=2, choices=LANGUAGE_CHOICES, default="de"
    )
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


def with_score(queryset):
    # A subquery instead of Sum("votes__value") keeps the total correct when
    # the queryset is also joined through tags.
    votes_total = (
        PostVote.objects.filter(post=OuterRef("pk"))
        .order_by()
        .values("post")
        .annotate(total=Sum("value"))
        .values("total")
    )
    return queryset.annotate(
        score=Coalesce(
            Subquery(votes_total, output_field=models.IntegerField()),
            Value(0),
        )
    )


class PostVote(models.Model):
    UP = 1
    DOWN = -1

    post = models.ForeignKey(
        Post, related_name="votes", on_delete=models.CASCADE
    )
    voter_id = models.CharField(max_length=36)
    ip_hash = models.CharField(max_length=64)
    value = models.SmallIntegerField()
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["post", "voter_id"], name="unique_vote_per_voter"
            ),
            models.UniqueConstraint(
                fields=["post", "ip_hash"], name="unique_vote_per_ip"
            ),
            models.CheckConstraint(
                condition=models.Q(value__in=[1, -1]),
                name="vote_value_is_up_or_down",
            ),
        ]

    @classmethod
    def toggle(cls, post, voter_id, ip_hash, value):
        try:
            return cls._toggle(post, voter_id, ip_hash, value)
        except IntegrityError:
            return cls._toggle(post, voter_id, ip_hash, value)

    @classmethod
    def _toggle(cls, post, voter_id, ip_hash, value):
        with transaction.atomic():
            votes = cls.objects.select_for_update().filter(post=post)
            vote = (
                votes.filter(voter_id=voter_id).first()
                or votes.filter(ip_hash=ip_hash).first()
            )
            if vote is None:
                cls.objects.create(
                    post=post, voter_id=voter_id, ip_hash=ip_hash, value=value
                )
                return value
            if vote.value == value:
                vote.delete()
                return None
            vote.value = value
            vote.save(update_fields=["value"])
            return value


def media_file_path(instance, filename) -> str:
    return f"post_{instance.post.id}/media/{filename}"


class MediaFile(models.Model):
    post = models.ForeignKey(
        Post, related_name="post_media", on_delete=models.CASCADE
    )
    file = models.FileField(upload_to=media_file_path, blank=True)

    def save(self, *args, **kwargs):
        if not self.file:
            return super().save(*args, **kwargs)

        previous_name = None
        if self.pk:
            previous_name = (
                MediaFile.objects.filter(pk=self.pk)
                .values_list("file", flat=True)
                .first()
            )
            if previous_name == self.file.name:
                return super().save(*args, **kwargs)

        try:
            self.file.seek(0)
            with Image.open(self.file) as uploaded_image:
                uploaded_image.verify()

            self.file.seek(0)
            with Image.open(self.file) as uploaded_image:
                if (
                    uploaded_image.width * uploaded_image.height
                    > MAX_UPLOAD_PIXELS
                ):
                    raise ValidationError("Image is too large.")
                uploaded_image.load()
                img = uploaded_image.copy()
        except (Image.DecompressionBombError, OSError) as exc:
            raise ValidationError(
                "Upload must be a valid, safe image."
            ) from exc

        if img.mode != "RGB":
            img = img.convert("RGB")

        max_size = (1920, 1080)
        img.thumbnail(max_size, Image.Resampling.LANCZOS)

        buff = BytesIO()
        img.save(buff, format="JPEG", optimize=True, quality=75)
        base, _ = os.path.splitext(self.file.name)
        self.file.save(f"{base}.jpg", ContentFile(buff.getvalue()), save=False)
        buff.close()
        super().save(*args, **kwargs)
        if previous_name and previous_name != self.file.name:
            self.file.storage.delete(previous_name)


@receiver(post_delete, sender=MediaFile)
def delete_media_file_on_disk(sender, instance, **kwargs):
    if not instance.file:
        return
    try:
        os.remove(instance.file.path)
    except FileNotFoundError:
        pass


@receiver(post_delete, sender=Post)
def cleanup_post_directory(sender, instance, **kwargs):
    post_dir = os.path.join(settings.MEDIA_ROOT, f"post_{instance.pk}")
    shutil.rmtree(post_dir, ignore_errors=True)
