# Generated by Django 3.2.3 on 2024-07-14 11:33

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('receipts', '0006_auto_20240714_1142'),
    ]

    operations = [
        migrations.RemoveIndex(
            model_name='ingredientinreceipt',
            name='receipts_in_ingredi_59b49d_idx',
        ),
        migrations.RemoveIndex(
            model_name='ingredientinreceipt',
            name='receipts_in_receipt_8e95a2_idx',
        ),
        migrations.AlterField(
            model_name='ingredientinreceipt',
            name='ingredient',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='receipts.ingredient', verbose_name='Продукт'),
        ),
        migrations.AlterField(
            model_name='ingredientinreceipt',
            name='receipt',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='receipts.receipt', verbose_name='Рецепт'),
        ),
    ]
