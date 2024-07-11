from collections import defaultdict
from receipts.models import IngredientReceipt


def generate_shopping_list(user):

    ings = (
        IngredientReceipt.objects.filter(
            receipt__shoppingcarts__user=user
        ).select_related('ingredient', 'receipt')
    )

    shopping_list = defaultdict(float)
    recipes = defaultdict(set)

    for ing in ings:
        shopping_list[ing.ingredient.name] += ing.amount
        recipes[ing.ingredient.name].add(ing.receipt.name)

    lines = [f"Список покупок для {user.username}:"]
    for idx, (ingredient, amount) in enumerate(shopping_list.items(), 1):
        recipe_list = ", ".join(recipes[ingredient])
        lines.append(
            f"{idx}. {ingredient}: {amount} "
            f"{ings[0].ingredient.measurement_unit} (для рецептов: {recipe_list})"
        )

    return "\n".join(lines)