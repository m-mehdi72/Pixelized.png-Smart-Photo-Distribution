# Generated by Django 4.1.9 on 2024-05-28 10:30

import core.models
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0003_attendees_alter_photographer_options_and_more'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='image',
            name='image_path',
        ),
        migrations.AddField(
            model_name='image',
            name='image',
            field=models.ImageField(default=1, upload_to=core.models.event_image_path),
            preserve_default=False,
        ),
    ]