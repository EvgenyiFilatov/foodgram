# Generated by Django 4.2.19 on 2025-02-21 08:06

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('myprofile', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='myprofile',
            name='is_subscribed',
            field=models.BooleanField(default=False),
        ),
    ]
