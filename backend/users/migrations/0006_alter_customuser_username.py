# Generated by Django 3.2.3 on 2024-07-01 08:43

import django.contrib.auth.validators
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('users', '0005_alter_customuser_managers'),
    ]

    operations = [
        migrations.AlterField(
            model_name='customuser',
            name='username',
            field=models.CharField(max_length=50, unique=True, validators=[django.contrib.auth.validators.ASCIIUsernameValidator()]),
        ),
    ]