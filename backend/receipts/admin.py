from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from django.utils.safestring import mark_safe
from django.utils.translation import gettext_lazy as _

from .models import Ingredient, Receipt, Tag, IngredientReceipt

from users.models import MyUser


try:
    admin.site.unregister(MyUser)
except admin.sites.NotRegistered:
    pass


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
        'tags__name',
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
        'recipes_count',
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

    def recipes_count(self, user):
        return user.reciepes.count()

    recipes_count.short_description = 'Число рецептов'


class ReceiptIngredientsInline(admin.TabularInline):
    model = IngredientReceipt
    verbose_name_plural = 'ingredients'


class CookingTimeFilter(admin.SimpleListFilter):
    title = 'Время приготовления'
    parameter_name = 'cooking_time'

    def lookups(self, request, model_admin):
        return (
            ('short', 'Быстрые (<= 15 мин)'),
            ('medium', 'Средние (15 - 60 мин)'),
            ('long', 'Долгие (> 60 мин)'),
        )

    def queryset(self, request, recipes):
        if self.value() == 'short':
            return recipes.filter(cooking_time__lte=15)
        if self.value() == 'medium':
            return recipes.filter(cooking_time__gt=15, cooking_time__lte=60)
        if self.value() == 'long':
            return recipes.filter(cooking_time__gt=60)
        return recipes


@admin.register(Receipt)
class ReceiptAdmin(admin.ModelAdmin):
    inlines = [ReceiptIngredientsInline]
    list_display = (
        'name',
        'author',
        'cooking_time_display',
        'tags_display',
        'ingredients_display',
        'image_display',
    )
    search_fields = (
        'name',
        'tags__name',
        'ingredients__name',
        'description',
    )
    list_filter = (
        'tags',
        CookingTimeFilter,
        'published_at',
    )
    list_display_links = (
        'name',
    )

    def cooking_time_display(self, receipt):
        return f'{receipt.cooking_time} мин'

    cooking_time_display.short_description = 'Время приготовления'

    def tags_display(self, receipt):
        return ", ".join([tag.name for tag in receipt.tags.all()])

    tags_display.short_description = 'Теги'

    def ingredients_display(self, receipt):
        ingredients = receipt.ingredients.all()
        return mark_safe(
            '<br>'.join(
                [
                    f'{ingredient.name},'
                    f'{ingredient.measurement_unit},'
                    f'{ir.amount}' for ingredient, ir in zip(
                        ingredients,
                        receipt.ingredientreceipt_set.all()
                    )
                ]
            )
        )

    ingredients_display.short_description = 'Продукты (имя, ед.изм., мера)'

    def image_display(self, receipt):
        if receipt.image:
            return mark_safe(
                f'<img src="{receipt.image.url}" width="50" height="50" />'
            )
        return 'Нет изображения'

    image_display.short_description = 'Картинка'


class HasSubscriptionsFilter(admin.SimpleListFilter):
    title = 'Есть подписки'
    parameter_name = 'has_subscriptions'

    def lookups(self, request, model_admin):
        return (
            ('yes', 'Да'),
            ('no', 'Нет'),
        )

    def queryset(self, request, subscriptions):
        if self.value() == 'yes':
            return subscriptions.filter(follower__isnull=False).distinct()
        elif self.value() == 'no':
            return subscriptions.filter(follower__isnull=True).distinct()


class HasSubscribersFilter(admin.SimpleListFilter):
    title = 'Есть подписчики'
    parameter_name = 'has_subscribers'

    def lookups(self, request, model_admin):
        return (
            ('yes', 'Да'),
            ('no', 'Нет'),
        )

    def queryset(self, request, subscribers):
        if self.value() == 'yes':
            return subscribers.filter(following__isnull=False).distinct()
        elif self.value() == 'no':
            return subscribers.filter(following__isnull=True).distinct()


class HasRecipesFilter(admin.SimpleListFilter):
    title = 'Есть рецепты'
    parameter_name = 'has_recipes'

    def lookups(self, request, model_admin):
        return (
            ('yes', 'Да'),
            ('no', 'Нет'),
        )

    def queryset(self, request, recipes):
        if self.value() == 'yes':
            return recipes.filter(recipes__isnull=False).distinct()
        elif self.value() == 'no':
            return recipes.filter(recipes__isnull=True).distinct()


@admin.register(MyUser)
class UserAdmin(UserAdmin):
    fieldsets = UserAdmin.fieldsets + (
        (_('Extra Fields'), {'fields': ('avatar',)}),
    )

    list_display = (
        'username', 'email', 'first_name', 'last_name', 'is_staff',
        'subscription_count', 'subscriber_count', 'recipe_count'
    )
    list_filter = (
        'is_staff', 'is_superuser', 'is_active', 'groups',
        HasSubscriptionsFilter, HasSubscribersFilter, HasRecipesFilter
    )

    def subscription_count(self, user):
        return user.follower.count()
    subscription_count.short_description = 'Число подписок'

    def subscriber_count(self, user):
        return user.following.count()
    subscriber_count.short_description = 'Число подписчиков'

    def recipe_count(self, user):
        return user.recipes.count()
    recipe_count.short_description = 'Число рецептов'
