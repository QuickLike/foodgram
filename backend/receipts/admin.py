from datetime import timedelta

from django.contrib import admin
from django.contrib.auth import get_user_model
from django.contrib.auth.admin import UserAdmin
from django.contrib.auth.models import Group
from django.utils import timezone
from django.utils.safestring import mark_safe
from django.utils.translation import gettext_lazy as _

from .models import Ingredient, Receipt, Tag, IngredientReceipt
from .constants import (
    SHORT_COOKING_TIME,
    MEDIUM_COOKING_TIME,
    SHORT_COOKING_TIME_TEXT,
    MEDIUM_COOKING_TIME_TEXT,
    LONG_COOKING_TIME_TEXT
)

User = get_user_model()

admin.site.unregister(Group)


@admin.register(Ingredient)
class IngredientAdmin(admin.ModelAdmin):
    list_display = (
        'name',
        'measurement_unit',
        'recipes_count'
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

    @admin.display(description='Рецепты')
    def recipes_count(self, ingredient):
        return ingredient.recipes.count()


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

    @admin.display(description='Рецепты')
    def recipes_count(self, tag):
        return tag.recipes.count()


class ReceiptIngredientsInline(admin.TabularInline):
    model = IngredientReceipt
    verbose_name_plural = 'ingredients'


class CookingTimeFilter(admin.SimpleListFilter):
    title = 'Время приготовления'
    parameter_name = 'cooking_time'

    def lookups(self, request, model_admin):
        short_count = Receipt.objects.filter(
            cooking_time__lte=SHORT_COOKING_TIME
        ).count()
        medium_count = Receipt.objects.filter(
            cooking_time__gt=SHORT_COOKING_TIME,
            cooking_time__lte=MEDIUM_COOKING_TIME
        ).count()
        long_count = Receipt.objects.filter(
            cooking_time__gt=MEDIUM_COOKING_TIME
        ).count()

        return (
            (
                'short',
                SHORT_COOKING_TIME_TEXT.format(
                    short_count=short_count,
                    short_time=SHORT_COOKING_TIME_TEXT
                ),
            ),
            (
                'medium',
                MEDIUM_COOKING_TIME_TEXT.format(
                    short_time=SHORT_COOKING_TIME,
                    medium_time=MEDIUM_COOKING_TIME,
                    medium_count=medium_count,
                )
            ),
            (
                'long',
                LONG_COOKING_TIME_TEXT.format(
                    medium_time=MEDIUM_COOKING_TIME,
                    long_count=long_count,
                )
            ),
        )

    def queryset(self, request, queryset):
        value = self.value()
        if value == 'short':
            return queryset.filter(
                cooking_time__lte=SHORT_COOKING_TIME
            )
        if value == 'medium':
            return queryset.filter(
                cooking_time__gt=SHORT_COOKING_TIME,
                cooking_time__lte=MEDIUM_COOKING_TIME
            )
        if value == 'long':
            return queryset.filter(
                cooking_time__gt=MEDIUM_COOKING_TIME
            )
        return queryset


class PublishedDateFilter(admin.SimpleListFilter):
    title = 'Дата публикации'
    parameter_name = 'published_at'

    def lookups(self, request, model_admin):
        return (
            ('today', 'За сегодня'),
            ('this_week', 'За эту неделю'),
            ('this_month', 'За этот месяц'),
            ('older', 'Старые'),
        )

    def queryset(self, request, queryset):
        if self.value() == 'today':
            return queryset.filter(published_at__date=timezone.now().date())
        elif self.value() == 'this_week':
            start_of_week = timezone.now().date() - timedelta(
                days=timezone.now().weekday()
            )
            return queryset.filter(published_at__date__gte=start_of_week)
        elif self.value() == 'this_month':
            start_of_month = timezone.now().date().replace(day=1)
            return queryset.filter(published_at__date__gte=start_of_month)
        elif self.value() == 'older':
            return queryset.exclude(
                published_at__date=timezone.now().date(),
            ).exclude(
                published_at__date__gte=timezone.now().date() - timedelta(
                    days=7
                ),
            ).exclude(
                published_at__date__gte=timezone.now().date().replace(
                    day=1
                ),
            )
        return queryset


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
        PublishedDateFilter,
    )
    list_display_links = (
        'name',
    )

    @admin.display(description='Время приготовления в минутах')
    def cooking_time_display(self, receipt):
        return receipt.cooking_time

    @admin.display(description='Теги')
    def tags_display(self, receipt):
        return "\n".join([tag.name for tag in receipt.tags.all()])

    @admin.display(description='Продукты')
    def ingredients_display(self, receipt):
        ingredients_list = [
            f'{ingredient.name}, {ingredient.measurement_unit}, {ir.amount}'
            for ir in receipt.ingredient_list.all()
            for ingredient in receipt.ingredients.filter(id=ir.ingredient_id)
        ]
        return mark_safe('<br>'.join(ingredients_list))

    @admin.display(description='Картинка')
    def image_display(self, receipt):
        return mark_safe(
            f'<img src="{receipt.image.url}" width="50" height="50" />'
        )


class BooleanFilter(admin.SimpleListFilter):
    def lookups(self, request, model_admin):
        return (
            ('yes', 'Да'),
            ('no', 'Нет'),
        )

    def queryset(self, request, queryset):
        field_name = self.get_field_name()
        if self.value() == 'yes':
            return queryset.filter(
                **{field_name + '__isnull': False}
            ).distinct()
        elif self.value() == 'no':
            return queryset.filter(
                **{field_name + '__isnull': True}
            ).distinct()

    def get_field_name(self):
        raise NotImplementedError("Subclasses should implement this method.")


class HasSubscriptionsFilter(BooleanFilter):
    title = 'Есть подписки'
    parameter_name = 'has_subscriptions'

    def get_field_name(self):
        return 'follower'


class HasSubscribersFilter(BooleanFilter):
    title = 'Есть подписчики'
    parameter_name = 'has_subscribers'

    def get_field_name(self):
        return 'following'


class HasRecipesFilter(BooleanFilter):
    title = 'Есть рецепты'
    parameter_name = 'has_recipes'

    def get_field_name(self):
        return 'recipes'


@admin.register(User)
class UserAdmin(UserAdmin):
    fieldsets = UserAdmin.fieldsets + (
        (_('Extra Fields'), {'fields': ('avatar',)}),
    )

    list_display = (
        'username', 'email', 'first_name', 'last_name', 'is_staff',
        'subscription_count', 'subscriber_count', 'recipe_count'
    )
    list_filter = (
        'is_staff', 'is_superuser', 'is_active',
        HasSubscriptionsFilter, HasSubscribersFilter, HasRecipesFilter
    )

    @admin.display(description='Подписки')
    def subscription_count(self, user):
        return user.followers.count()

    @admin.display(description='Подписчики')
    def subscriber_count(self, user):
        return user.authors.count()

    @admin.display(description='Рецепты')
    def recipe_count(self, user):
        return user.recipes.count()
