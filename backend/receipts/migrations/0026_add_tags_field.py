# 0026_add_tags_field.py

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('receipts', '0025_remove_tags_field'),
    ]

    operations = [
        migrations.AddField(
            model_name='receipt',
            name='tags',
            field=models.ManyToManyField(to='receipts.Tag', verbose_name='Теги'),
        ),
    ]
