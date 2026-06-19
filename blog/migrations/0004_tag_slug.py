from django.db import migrations, models
from django.utils.text import slugify


def populate_tag_slugs(apps, schema_editor):
    Tag = apps.get_model("blog", "Tag")
    for tag in Tag.objects.all():
        tag.slug = slugify(tag.name) or "tag"
        tag.save(update_fields=["slug"])


class Migration(migrations.Migration):
    dependencies = [
        ("blog", "0003_post_language"),
    ]

    operations = [
        migrations.AddField(
            model_name="tag",
            name="slug",
            field=models.SlugField(blank=True, default="", max_length=50),
        ),
        migrations.RunPython(populate_tag_slugs, migrations.RunPython.noop),
        migrations.AlterField(
            model_name="tag",
            name="slug",
            field=models.SlugField(blank=True, max_length=50, unique=True),
        ),
    ]
