import django_filters

from receipts.models import Ingredient, Receipt, Tag


class IngredientFilter(django_filters.FilterSet):
    name = django_filters.CharFilter(
        field_name='name',
        lookup_expr='startswith'
    )

    class Meta:
        model = Ingredient
        fields = []


class ReceiptFilter(django_filters.FilterSet):
    author = django_filters.CharFilter(
        field_name='author__id',
        lookup_expr='exact',
        label='ID автора'
    )
    tags = django_filters.ModelMultipleChoiceFilter(
        field_name='tags__slug',
        to_field_name='slug',
        queryset=Tag.objects.all(),
        conjoined=False
    )

    class Meta:
        model = Receipt
        fields = ['is_in_shopping_cart', 'is_favorited']
