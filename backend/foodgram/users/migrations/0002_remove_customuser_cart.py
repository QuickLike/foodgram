# Generated by Django 3.2.3 on 2024-06-20 17:20

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('users', '0001_initial'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='customuser',
            name='cart',
        ),
    ]
