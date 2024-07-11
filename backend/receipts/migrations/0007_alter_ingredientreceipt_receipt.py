# Generated by Django 3.2.3 on 2024-07-11 16:39

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('receipts', '0006_auto_20240711_1931'),
    ]

    operations = [
        migrations.AlterField(
            model_name='ingredientreceipt',
            name='receipt',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='ingredient_list', to='receipts.receipt'),
        ),
    ]
