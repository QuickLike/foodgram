from collections import defaultdict

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

    recipes_for_ingredients = defaultdict(set)
    for item in IngredientInReceipt.objects.filter(
            receipt__shopping_carts__user=user
    ):
        recipes_for_ingredients[item.ingredient.name].add(item.receipt.name)

    product_lines = [
        (f"{id_ + 1}. {ingredient['ingredient__name']}: "
         f"{ingredient['total_amount']} "
         f"{ingredient['ingredient__measurement_unit']}")
        for id_, ingredient in enumerate(ingredients_in_receipt)
    ]

    recipe_lines = [
        f"{ingredient}: {', '.join(recipes_for_ingredients[ingredient])}"
        for ingredient in recipes_for_ingredients
    ]

    return '\n'.join([
        f"Список покупок для {user.username}:",
        "Продукты:",
        *product_lines,
        "Рецепты:",
        *recipe_lines,
    ])
