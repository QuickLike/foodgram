import ast
from datetime import timedelta, date

from django.contrib import admin
from django.contrib.auth import get_user_model
from django.contrib.auth.admin import UserAdmin
from django.contrib.auth.models import Group
from django.db.models import Count
from django.utils import timezone
from django.utils.safestring import mark_safe
from django.utils.translation import gettext_lazy as _

from .models import (
    Ingredient,
    Receipt,
    Tag,
    IngredientInReceipt,
    Favourite,
    ShoppingCart,
    Subscription
)
from .constants import (
    SHORT_COOKING_TIME,
    MEDIUM_COOKING_TIME,
    SHORT_COOKING_TIME_TEXT,
    MEDIUM_COOKING_TIME_TEXT,
    LONG_COOKING_TIME_TEXT,
    TODAY_TEXT,
    THIS_MONTH_TEXT,
    THIS_WEEK_TEXT,
    OLDER_TEXT
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
    )
    list_filter = (
        'measurement_unit',
        # 'in_receipt',
    )
    list_display_links = (
        'name',
    )

    @admin.display(description='Рецепты')
    def recipes_count(self, ingredient):
        return ingredient.recipes.count()

    # @admin.display(description='Есть в рецепте')
    # def in_receipt(self, ingredient):
    #     return ingredient.recipes.count()


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
    list_display_links = (
        'slug',
    )

    @admin.display(description='Рецепты')
    def recipes_count(self, tag):
        return tag.recipes.all().count()


class ReceiptIngredientsInline(admin.TabularInline):
    model = IngredientInReceipt
    verbose_name_plural = 'ingredients'


class CookingTimeFilter(admin.SimpleListFilter):
    title = 'Время приготовления'
    parameter_name = 'cooking_time'

    def lookups(self, request, model_admin):
        short_range = (0, SHORT_COOKING_TIME)
        medium_range = (SHORT_COOKING_TIME + 1, MEDIUM_COOKING_TIME)
        long_range = (MEDIUM_COOKING_TIME + 1, 10**10)

        short_count = Receipt.objects.filter(
            cooking_time__range=short_range
        ).count()
        medium_count = Receipt.objects.filter(
            cooking_time__range=medium_range
        ).count()
        long_count = Receipt.objects.filter(
            cooking_time__range=long_range
        ).count()

        return [
            (
                short_range,
                SHORT_COOKING_TIME_TEXT.format(
                    short_time=SHORT_COOKING_TIME,
                    short_count=short_count
                )
            ),
            (
                medium_range,
                MEDIUM_COOKING_TIME_TEXT.format(
                    short_time=SHORT_COOKING_TIME,
                    medium_time=MEDIUM_COOKING_TIME,
                    medium_count=medium_count
                )
            ),
            (
                long_range,
                LONG_COOKING_TIME_TEXT.format(
                    medium_time=MEDIUM_COOKING_TIME,
                    long_count=long_count
                )
            ),
        ]

    def queryset(self, request, queryset):
        if not self.value():
            return queryset
        if ast.literal_eval(self.value())[1] == 10**10:
            return queryset.filter(cooking_time__gt=ast.literal_eval(self.value())[0])


class PublishedDateFilter(admin.SimpleListFilter):
    title = 'Дата публикации'
    parameter_name = 'published_at'

    def get_filter_params(self):
        today = timezone.now().date()
        start_of_week = today - timedelta(days=today.weekday())
        start_of_month = today.replace(day=1)
        very_old_date = date(1970, 1, 1)

        today_count = Receipt.objects.filter(
            published_at__date=today
        ).count()
        this_week_count = Receipt.objects.filter(
            published_at__date__gte=start_of_week
        ).count()
        this_month_count = Receipt.objects.filter(
            published_at__date__gte=start_of_month
        ).count()
        older_count = Receipt.objects.filter(
            published_at__date__lt=start_of_month
        ).count()

        return [
            ('today', (today, today), today_count),
            ('this_week', (start_of_week, today), this_week_count),
            ('this_month', (start_of_month, today), this_month_count),
            ('older', (very_old_date, start_of_month - timedelta(days=1)),
             older_count
             ),
        ]

    def lookups(self, request, model_admin):
        filter_params = self.get_filter_params()
        return (
            (
                'today',
                'Сегодня ({count})'.format(count=filter_params[0][2])
            ),
            (
                'this_week',
                'На этой неделе ({count})'.format(count=filter_params[1][2])
            ),
            (
                'this_month',
                'В этом месяце ({count})'.format(count=filter_params[2][2])
            ),
            (
                'older',
                'Ранее ({count})'.format(count=filter_params[3][2])
            ),
        )

    def queryset(self, request, queryset):
        value = self.value()
        filter_params = self.get_filter_params()

        for filter_name, (param1, param2), count in filter_params:
            if value == filter_name:
                return queryset.filter(
                    published_at__date__range=(param1, param2)
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

    @admin.display(description='Время (мин)')
    def cooking_time_display(self, receipt):
        return receipt.cooking_time

    @admin.display(description='Теги')
    @mark_safe
    def tags_display(self, receipt):
        return '<br>'.join(map(str, receipt.tags.all()))

    @admin.display(description='Продукты')
    @mark_safe
    def ingredients_display(self, receipt):
        return '<br>'.join(
            [
                f'{ingredient_in_receipt.ingredient.name}, '
                f'{ingredient_in_receipt.ingredient.measurement_unit}, '
                f'{ingredient_in_receipt.amount}'
                for ingredient_in_receipt in
                receipt.ingredients_in_receipts.all()
            ]
        )

    @admin.display(description='Картинка')
    @mark_safe
    def image_display(self, receipt):
        return f'<img src="{receipt.image.url}" width="50" height="50" />'


class BooleanFilter(admin.SimpleListFilter):
    def lookups(self, request, model_admin):
        return (
            ('yes', 'Да'),
            ('no', 'Нет'),
        )

    def queryset(self, request, queryset):
        field_name = self.get_field_name()
        value = self.value()
        if value in ('yes', 'no'):
            return queryset.filter(
                **{f"{field_name}__isnull": value == 'no'}
            ).distinct()
        return queryset

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


class UserRecipeBaseAdmin(admin.ModelAdmin):
    list_display = (
        'user',
        'receipt',
    )
    list_editable = (
        'receipt',
    )
    search_fields = (
        'receipt__name',
        'user__username',
    )
    list_filter = (
        'receipt__name',
    )
    list_display_links = (
        'user',
    )


@admin.register(Favourite)
class FavouriteAdmin(UserRecipeBaseAdmin):
    pass


@admin.register(ShoppingCart)
class ShoppingCartAdmin(UserRecipeBaseAdmin):
    pass


@admin.register(Subscription)
class SubscriptionAdmin(admin.ModelAdmin):
    list_display = (
        'follower',
        'author',
    )
    list_editable = (
        'author',
    )
    search_fields = (
        'follower__username',
        'author__username',
    )
    list_filter = (
        'follower__username',
    )
    list_display_links = (
        'follower',
    )


@admin.register(IngredientInReceipt)
class IngredientInReceiptAdmin(admin.ModelAdmin):
    list_display = (
        'ingredient',
        'receipt',
        'amount',
    )
    list_editable = (
        'ingredient',
        'amount',
    )
    search_fields = (
        'ingredient__name',
        'receipt__name',
    )
    list_filter = (
        'receipt__name',
    )
    list_display_links = (
        'receipt',
    )
