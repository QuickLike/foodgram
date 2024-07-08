from django_filters import rest_framework
from receipts.models import Ingredient, Receipt, Tag


class IngredientFilter(rest_framework.FilterSet):
    name = rest_framework.CharFilter(
        field_name='name',
        lookup_expr='startswith'
    )

    class Meta:
        model = Ingredient
        fields = []


class ReceiptFilter(rest_framework.FilterSet):
    author = rest_framework.CharFilter(
        field_name='author__id',
        lookup_expr='exact',
        label='ID автора'
    )
    tags = rest_framework.ModelMultipleChoiceFilter(
        field_name='tags__slug',
        to_field_name='slug',
        queryset=Tag.objects.all(),
        conjoined=False
    )
    is_in_shopping_cart = rest_framework.BooleanFilter(
        method='filter_is_in_shopping_cart',
        label='В корзине',
    )
    is_favorited = rest_framework.BooleanFilter(
        method='filter_is_favorited',
        label='В избранном'
    )

    class Meta:
        model = Receipt
        fields = ['author', 'tags', 'is_in_shopping_cart', 'is_favorited']

    def filter_is_in_shopping_cart(self, recipes, name, value):
        user = self.request.user
        if user.is_authenticated and value:
            return recipes.filter(shoppingcart__user=user)
        return recipes

    def filter_is_favorited(self, recipes, name, value):
        user = self.request.user
        if user.is_authenticated and value:
            return recipes.filter(favourite__user=user)
        return recipes
