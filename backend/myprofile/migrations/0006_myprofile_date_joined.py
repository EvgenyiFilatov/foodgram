# Generated by Django 4.2.19 on 2025-03-19 09:58

import django.utils.timezone
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('myprofile', '0005_myprofile_favorite_recipes_and_more'),
    ]

    operations = [
        migrations.AddField(
            model_name='myprofile',
            name='date_joined',
            field=models.DateTimeField(default=django.utils.timezone.now),
        ),
    ]
