# Generated by Django 3.2.3 on 2024-07-06 10:26

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('receipts', '0022_auto_20240706_1259'),
    ]

    operations = [
        migrations.AlterField(
            model_name='shoppingcart',
            name='receipt',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='added_to_shopping_cart', to='receipts.receipt'),
        ),
    ]
