# Generated by Django 4.2.19 on 2025-03-19 10:19

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('myprofile', '0006_myprofile_date_joined'),
    ]

    operations = [
        migrations.AlterField(
            model_name='myprofile',
            name='avatar',
            field=models.ImageField(default='', null=True, upload_to='backend/avatar/'),
        ),
    ]
