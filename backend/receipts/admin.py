from django.contrib import admin

from .models import Ingredient, Receipt, Tag


@admin.register(Ingredient)
class IngredientAdmin(admin.ModelAdmin):
    list_display = (
        'name',
        'measurement_unit',
    )
    list_editable = (
        'measurement_unit',
    )
    search_fields = (
        'name',
    )
    list_filter = (
        'measurement_unit',
    )
    list_display_links = (
        'name',
    )


@admin.register(Tag)
class TagAdmin(admin.ModelAdmin):
    list_display = (
        'slug',
        'name',
    )
    list_editable = (
        'name',
    )
    search_fields = (
        'name',
    )
    list_filter = (
        'name',
    )
    list_display_links = (
        'slug',
    )


class ReceiptIngredientsInline(admin.TabularInline):
    model = Receipt.ingredients.through
    verbose_name_plural = 'ingredients'


@admin.register(Receipt)
class ReceiptAdmin(admin.ModelAdmin):
    inlines = [ReceiptIngredientsInline]
    list_display = (
        'name',
        'author',
    )
    search_fields = (
        'name',
        'tags',
        'ingredients',
        'description',
    )
    list_filter = (
        'tags',
        'cooking_time',
        'published_at',
    )
    list_display_links = (
        'name',
    )
