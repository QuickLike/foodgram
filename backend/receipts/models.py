from django.core.exceptions import ValidationError
from django.core.validators import MinValueValidator, RegexValidator
from django.contrib.auth.models import AbstractUser, models

from .constants import (
    MIN_COOKING_TIME,
    MIN_INGREDIENTS_AMOUNT,
    EMAIL_MAX_LENGTH,
    MAX_USERNAME_LENGTH,
)


class User(AbstractUser):
    username = models.CharField(
        max_length=MAX_USERNAME_LENGTH,
        unique=True,
        validators=(RegexValidator(r'^[\w.@+-]+\Z'),),
    )
    email = models.EmailField(
        unique=True,
        max_length=EMAIL_MAX_LENGTH,
    )
    first_name = models.CharField(max_length=50)
    last_name = models.CharField(max_length=50)
    avatar = models.ImageField(
        upload_to='users',
        blank=True,
    )

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['username', 'first_name', 'last_name']

    class Meta:
        verbose_name = 'Пользователь'
        verbose_name_plural = 'Пользователи'
        ordering = ('username',)


class Subscription(models.Model):
    follower = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        verbose_name='Пользователь',
        related_name='followers',
    )
    author = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        verbose_name='Подписчик',
        related_name='authors',
    )

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=['follower', 'author'],
                name='unique_follower_author'
            ),
        ]
        default_related_name = 'subscriptions'
        verbose_name = 'Подписка'
        verbose_name_plural = 'подписки'

    def clean(self):
        if self.follower == self.author:
            raise ValidationError('Нельзя подписаться на самого себя.')

    def __str__(self):
        return f'{self.follower} {self.author}'


class Tag(models.Model):
    name = models.CharField(
        max_length=128,
        verbose_name='Название',
        unique=True,
    )
    slug = models.SlugField(
        max_length=128,
        verbose_name='Ярлык',
        unique=True,
    )

    class Meta:
        default_related_name = 'tags'
        verbose_name = 'Тег'
        verbose_name_plural = 'теги'

    def __str__(self):
        return self.name[:20]


class Ingredient(models.Model):
    name = models.CharField(
        max_length=128,
        verbose_name='Название',
    )
    measurement_unit = models.CharField(
        max_length=16,
        verbose_name='Единица измерения',
    )

    class Meta:
        default_related_name = 'ingredients'
        verbose_name = 'Продукт'
        verbose_name_plural = 'продукты'

    def __str__(self):
        return f'{self.name[:20]}, {self.measurement_unit}'


class Receipt(models.Model):
    author = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        verbose_name='Автор',
    )
    name = models.CharField(
        max_length=128,
        verbose_name='Название',
    )
    image = models.ImageField(
        upload_to='receipts',
    )
    text = models.TextField(
        verbose_name='Описание',
    )
    ingredients = models.ManyToManyField(
        Ingredient,
        verbose_name='Продукты в рецепте',
        through='IngredientInReceipt',
    )
    tags = models.ManyToManyField(
        Tag,
        verbose_name='Теги',
    )
    cooking_time = models.PositiveIntegerField(
        verbose_name='Время приготовления',
        validators=(MinValueValidator(MIN_COOKING_TIME), ),
    )
    published_at = models.DateTimeField(
        verbose_name='Опубликовано',
        auto_now_add=True,
    )

    class Meta:
        default_related_name = 'recipes'
        verbose_name = 'Рецепт'
        verbose_name_plural = 'рецепты'
        ordering = ('-published_at', )

    def __str__(self):
        return self.name[:20]


class IngredientInReceipt(models.Model):
    ingredient = models.ForeignKey(
        Ingredient,
        on_delete=models.CASCADE,
    )
    receipt = models.ForeignKey(
        Receipt,
        related_name='ingredients_in_receipt',
        on_delete=models.CASCADE,
    )
    amount = models.PositiveSmallIntegerField(
        verbose_name='Мера',
        validators=(MinValueValidator(MIN_INGREDIENTS_AMOUNT), ),
        default=MIN_INGREDIENTS_AMOUNT,
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


class UserRecipeBase(models.Model):
    user = models.ForeignKey(
        User,
        verbose_name='Пользователь',
        on_delete=models.CASCADE,
    )
    receipt = models.ForeignKey(
        Receipt,
        verbose_name='Рецепт',
        on_delete=models.CASCADE,
    )

    class Meta:
        abstract = True
        constraints = [
            models.UniqueConstraint(
                fields=['user', 'receipt'],
                name='unique_user_receipt_%(class)s',
            )
        ]

    def __str__(self):
        return f'{self.user} {self.receipt}'


class Favourite(UserRecipeBase):

    class Meta(UserRecipeBase.Meta):
        default_related_name = 'favourites'
        verbose_name = 'Избранное'
        verbose_name_plural = 'избранные'


class ShoppingCart(UserRecipeBase):

    class Meta(UserRecipeBase.Meta):
        default_related_name = 'shopping_carts'
        verbose_name = 'Корзина покупок'
        verbose_name_plural = 'корзины покупок'
