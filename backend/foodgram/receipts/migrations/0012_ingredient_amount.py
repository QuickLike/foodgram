# Generated by Django 3.2.3 on 2024-06-23 19:48

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('receipts', '0011_rename_description_receipt_text'),
    ]

    operations = [
        migrations.AddField(
            model_name='ingredient',
            name='amount',
            field=models.PositiveSmallIntegerField(default=0, verbose_name='Количество'),
        ),
    ]
