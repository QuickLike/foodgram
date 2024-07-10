# Generated by Django 3.2.3 on 2024-07-10 11:04

from django.db import migrations
import shortuuid.django_fields


class Migration(migrations.Migration):

    dependencies = [
        ('receipts', '0003_auto_20240710_1402'),
    ]

    operations = [
        migrations.AlterField(
            model_name='receipt',
            name='short_link',
            field=shortuuid.django_fields.ShortUUIDField(alphabet=None, length=6, max_length=6, prefix=''),
        ),
    ]
