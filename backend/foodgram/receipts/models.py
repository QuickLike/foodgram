from django.contrib.auth import get_user_model
from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models

User = get_user_model()


class Tag(models.Model):
    name = models.CharField(
        max_length=128,
        verbose_name='Название',
        unique=True,
        null=False,
    )
    slug = models.SlugField(
        max_length=128,
        verbose_name='Слаг',
        unique=True,
        null=False,
    )

    class Meta:
        verbose_name = 'Тег'
        verbose_name_plural = 'теги'

    def __str__(self):
        return self.name[:20]


class Ingredient(models.Model):
    name = models.CharField(
        max_length=128,
        verbose_name='Название',
        null=False,
    )
    measurement_unit = models.CharField(
        max_length=16,
        verbose_name='Единица измерения',
        null=False,
    )

    class Meta:
        verbose_name = 'Ингредиент'
        verbose_name_plural = 'ингредиенты'

    def __str__(self):
        return f'{self.name[:20]}, {self.measurement_unit}'


class Receipt(models.Model):
    author = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='receipts',
        verbose_name='Автор',
        null=False,
    )
    name = models.CharField(
        max_length=128,
        verbose_name='Название',
        null=False,
    )
    image = models.ImageField(
        upload_to='receipt/images',
        default=None,
        null=False,
    )
    text = models.TextField(
        max_length=1024,
        verbose_name='Описание',
        null=False,
    )
    ingredients = models.ManyToManyField(
        Ingredient,
        verbose_name='Ингредиенты',
        through='IngredientReceipt',
    )
    tags = models.ManyToManyField(
        Tag,
        verbose_name='Теги',
        through='TagReceipt',
    )
    cooking_time = models.PositiveIntegerField(
        verbose_name='Время приготовления',
        null=False,
    )
    published_at = models.DateTimeField(
        verbose_name='Опубликовано',
        auto_now_add=True,
    )
    is_favorited = models.BooleanField(
        verbose_name='В избранном',
        default=False,
    )
    is_in_shopping_cart = models.BooleanField(
        verbose_name='В корзине',
        default=False,
    )

    class Meta:
        verbose_name = 'Рецепт'
        verbose_name_plural = 'рецепты'
        ordering = ['-published_at']

    def __str__(self):
        return self.name[:20]


class IngredientReceipt(models.Model):
    ingredient = models.ForeignKey(
        Ingredient,
        on_delete=models.CASCADE,
    )
    receipt = models.ForeignKey(
        Receipt,
        on_delete=models.CASCADE,
    )
    amount = models.PositiveSmallIntegerField(
        verbose_name='Количество',
        validators=[MinValueValidator(1), MaxValueValidator(100_000)],
        default=1,
    )

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=['ingredient', 'receipt'],
                name='unique_ingredient_receipt',
            )
        ]

    def __str__(self):
        return f'{self.ingredient} {self.receipt}'


class TagReceipt(models.Model):
    tag = models.ForeignKey(
        Tag,
        on_delete=models.CASCADE,
        )
    receipt = models.ForeignKey(
        Receipt,
        on_delete=models.CASCADE,
    )

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=['tag', 'receipt'],
                name='unique_tag_receipt',
            )
        ]

    def __str__(self):
        return f'{self.tag} {self.receipt}'


class Favourite(models.Model):
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='favourites',
    )
    receipt = models.ForeignKey(
        Receipt,
        on_delete=models.CASCADE,
        related_name='added_to_favourites',
    )

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=['user', 'receipt'],
                name='unique_user_favourites',
            )
        ]
        verbose_name = 'Избранное'
        verbose_name_plural = 'избранные'

    def __str__(self):
        return f'{self.user} {self.receipt}'


class ShoppingCart(models.Model):
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='shopping_cart',
    )
    receipt = models.ForeignKey(
        Receipt,
        on_delete=models.CASCADE,
        related_name='added_to_shopping_to_cart',
    )

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=['user', 'receipt'],
                name='unique_user_shopping_cart',
            )
        ]
        verbose_name = 'Корзина покупок'
        verbose_name_plural = 'корзины покупок'

    def __str__(self):
        return f'{self.user} {self.receipt}'
