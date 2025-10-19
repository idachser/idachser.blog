from django.db import models
from django.utils.text import slugify


class Tag(models.Model):
    name = models.CharField(max_length=50, unique=True)

    def __str__(self):
        return str(self.name)


class Post(models.Model):
    title = models.CharField(max_length=200, unique=True)
    description = models.CharField(max_length=500, blank=True)
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
