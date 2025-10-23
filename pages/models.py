from django.db import models


class AboutMeInfo(models.Model):
    title = models.CharField(max_length=200, default="About Me")
    body = models.TextField()
    author = models.CharField(max_length=50, default="idachser")

    def __str__(self):
        return str(self.title)
