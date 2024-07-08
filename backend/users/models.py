import re

from django.core.exceptions import ValidationError
from django.contrib.auth.models import AbstractUser, BaseUserManager, models

from constants.constants import MAX_USERNAME_LENGTH


class UserManager(BaseUserManager):
    def create_user(
            self,
            email,
            username,
            first_name,
            last_name,
            password=None,
            **extra_fields
    ):
        if not email:
            raise ValueError('The Email field must be set')
        email = self.normalize_email(email)
        user = self.model(
            email=email,
            username=username,
            first_name=first_name,
            last_name=last_name,
            **extra_fields
        )
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(
            self,
            email,
            username,
            first_name,
            last_name,
            password=None,
            **extra_fields
    ):
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)

        return self.create_user(
            email, username, first_name, last_name, password, **extra_fields
        )


class MyUser(AbstractUser):
    username = models.CharField(
        max_length=MAX_USERNAME_LENGTH,
        unique=True,
    )
    email = models.EmailField(
        unique=True,
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

    def clean(self):
        super().clean()
        if self.username == 'me':
            raise ValidationError(
                message='Имя пользователя не может быть "me".'
            )
        if not re.fullmatch(pattern=r'^[w.@+-]+Z', string=str(self.username)):
            raise ValidationError(
                message=(
                    'Имя пользователя должно содержать только '
                    'буквы, цифры, точки, дефисы,'
                    'подчеркивания и знаки плюса.'
                )
            )


class Subscription(models.Model):
    follower = models.ForeignKey(
        MyUser,
        on_delete=models.CASCADE,
        related_name='follower',
    )
    following = models.ForeignKey(
        MyUser,
        on_delete=models.CASCADE,
        related_name='following',
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

        if Subscription.objects.filter(
                follower=self.follower, following=self.following
        ).exists():
            raise ValidationError('Вы уже подписаны на этого пользователя.')

    def __str__(self):
        return f'{self.follower} {self.following}'
