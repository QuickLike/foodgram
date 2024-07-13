# Generated by Django 3.2.3 on 2024-07-13 07:11

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('receipts', '0001_initial'),
    ]

    operations = [
        migrations.AlterField(
            model_name='ingredientinreceipt',
            name='receipt',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='ingredients_in_receipts', to='receipts.receipt'),
        ),
    ]