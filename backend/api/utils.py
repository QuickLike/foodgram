from datetime import datetime

from django.db.models import Sum

from receipts.models import IngredientInReceipt


def generate_shopping_list(user):
    ingredients_in_receipt = (
        IngredientInReceipt.objects.filter(
            receipt__shopping_carts__user=user
        ).values(
            'ingredient__name',
            'ingredient__measurement_unit'
        ).annotate(
            total_amount=Sum('amount')
        )
    )

    recipes_for_ingredients = {}
    for ingredient_info in ingredients_in_receipt:
        ingredient_name = ingredient_info['ingredient__name']
        recipes = IngredientInReceipt.objects.filter(
            receipt__shopping_carts__user=user,
            ingredient__name=ingredient_name
        ).values_list('receipt__name', flat=True).distinct()
        recipes_for_ingredients[ingredient_name] = recipes

    return '\n'.join([
        f'Список покупок для {user.username}. '
        f'Дата составления {datetime.now().strftime("%d.%m.%Y %H:%M")}:',
        "Продукты:",
        *[
            (f"{id_}. {ingredient['ingredient__name'].title()}: "
             f"{ingredient['total_amount']} "
             f"{ingredient['ingredient__measurement_unit']}")
            for id_, ingredient in enumerate(ingredients_in_receipt, start=1)
        ],
        "Рецепты:",
        *[
            f"{', '.join(recipes_for_ingredients[ingredient])}"
            for ingredient in recipes_for_ingredients
        ],
    ])
