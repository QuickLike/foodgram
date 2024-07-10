import re

from django.core.exceptions import ValidationError
from django.core.validators import MinValueValidator
from django.contrib.auth.models import AbstractUser, models
from django.utils.translation import gettext_lazy as _
from shortuuid.django_fields import ShortUUIDField

from .constants import (
    MIN_COOKING_TIME,
    SHORT_LINK_LENGTH,
    MIN_INGREDIENTS_AMOUNT,
    EMAIL_MAX_LENGTH,
    MAX_USERNAME_LENGTH,
    RESERVED_USERNAME
)


def validate_username(username):
    if username == RESERVED_USERNAME:
        raise ValidationError(
            _(f'Имя пользователя не может быть {RESERVED_USERNAME}.')
        )
    invalid_chars = re.findall(r'[^a-zA-Z0-9.@+-]', username)
    if invalid_chars:
        raise ValidationError(
            _('Имя пользователя должно содержать только '
              'буквы, цифры, точки, дефисы, подчеркивания и знаки плюса. '
              'Недопустимые символы: %(invalid_chars)s'),
            params={'invalid_chars': ', '.join(set(invalid_chars))}
        )


class User(AbstractUser):
    username = models.CharField(
        max_length=MAX_USERNAME_LENGTH,
        unique=True,
        validators=[validate_username],
    )
    email = models.EmailField(
        unique=True,
        max_length=EMAIL_MAX_LENGTH,
    )
    first_name = models.CharField(max_length=50)
    last_name = models.CharField(max_length=50)
    avatar = models.ImageField(
        upload_to='users/avatars',
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
        related_name='followers',
    )
    following = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='authors',
    )

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=['follower', 'following'],
                name='unique_follower_following'
            ),
        ]
        verbose_name = 'Подписка'
        verbose_name_plural = 'подписки'

    def clean(self):
        if self.follower == self.following:
            raise ValidationError('Нельзя подписаться на самого себя.')

    def __str__(self):
        return f'{self.follower} {self.following}'


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
        verbose_name = 'Продукт'
        verbose_name_plural = 'продукты'

    def __str__(self):
        return f'{self.name[:20]}, {self.measurement_unit}'


class Receipt(models.Model):
    author = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='recipes',
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
        null=False,
    )
    text = models.TextField(
        verbose_name='Описание',
        null=False,
    )
    ingredients = models.ManyToManyField(
        Ingredient,
        verbose_name='Продукты в рецепте',
        through='IngredientReceipt',
    )
    tags = models.ManyToManyField(
        Tag,
        verbose_name='Теги',
    )
    cooking_time = models.PositiveIntegerField(
        verbose_name='Время приготовления',
        null=False,
        validators=(MinValueValidator(MIN_COOKING_TIME), ),
        default=MIN_COOKING_TIME,
    )
    published_at = models.DateTimeField(
        verbose_name='Опубликовано',
        auto_now_add=True,
    )
    short_link = ShortUUIDField(
        primary_key=False,
        length=SHORT_LINK_LENGTH
    )

    class Meta:
        verbose_name = 'Рецепт'
        verbose_name_plural = 'рецепты'

        ordering = ('-published_at', )

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
        on_delete=models.CASCADE,
        related_name='%(class)ss',
    )
    receipt = models.ForeignKey(
        Receipt,
        on_delete=models.CASCADE,
        related_name='%(class)ss',
    )

    class Meta:
        abstract = True
        constraints = [
            models.UniqueConstraint(
                fields=['user', 'receipt'],
                name='unique_user_%(class)',
            )
        ]

    def __str__(self):
        return f'{self.user} {self.receipt}'


class Favourite(UserRecipeBase):

    class Meta:
        verbose_name = 'Избранное'
        verbose_name_plural = 'избранные'


class ShoppingCart(UserRecipeBase):

    class Meta:
        verbose_name = 'Корзина покупок'
        verbose_name_plural = 'корзины покупок'
