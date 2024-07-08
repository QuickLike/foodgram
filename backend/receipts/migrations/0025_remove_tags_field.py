# 0025_remove_tags_field.py

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('receipts', '0024_alter_receipt_short_link'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='receipt',
            name='tags',
        ),
    ]
