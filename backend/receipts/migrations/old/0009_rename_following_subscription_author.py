# Generated by Django 3.2.3 on 2024-07-11 19:18

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('receipts', '0008_alter_user_username'),
    ]

    operations = [
        migrations.RenameField(
            model_name='subscription',
            old_name='following',
            new_name='author',
        ),
    ]
