from django.core.exceptions import ValidationError
from django.contrib.auth.models import AbstractUser, BaseUserManager, models
from django.contrib.auth.validators import ASCIIUsernameValidator


class CustomUserManager(BaseUserManager):
    def create_user(self, email, username, first_name, last_name, password=None, **extra_fields):
        if not email:
            raise ValueError('The Email field must be set')
        email = self.normalize_email(email)
        user = self.model(email=email, username=username, first_name=first_name, last_name=last_name, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, email, username, first_name, last_name, password=None, **extra_fields):
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)

        return self.create_user(email, username, first_name, last_name, password, **extra_fields)


class CustomUser(AbstractUser):
    username_validator = ASCIIUsernameValidator()
    username = models.CharField(
        max_length=50,
        unique=True,
        null=False,
        validators=[username_validator],
    )
    email = models.EmailField(
        unique=True,
        null=False
    )
    first_name = models.CharField(max_length=50)
    last_name = models.CharField(max_length=50)
    is_subscribed = models.BooleanField(default=False)
    avatar = models.ImageField(
        upload_to='users/avatars',
        blank=True,
    )

    objects = CustomUserManager()

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['username', 'first_name', 'last_name']


class Subscription(models.Model):
    user = models.ForeignKey(
        CustomUser,
        on_delete=models.CASCADE,
        related_name='subscriptions',
    )
    subscribe_on = models.ForeignKey(
        CustomUser,
        on_delete=models.CASCADE,
        related_name='subscribers',
    )

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=['user', 'subscribe_on'],
                name='unique_user_subscribe_on'
            ),
        ]
        verbose_name = 'Подписка'
        verbose_name_plural = 'подписки'

    def clean(self):
        if self.user == self.subscribe_on:
            raise ValidationError('Нельзя подписаться на самого себя.')

        if Subscription.objects.filter(user=self.user, subscribe_on=self.subscribe_on).exists():
            raise ValidationError('Вы уже подписаны на этого пользователя.')

    def __str__(self):
        return f'{self.user} {self.subscribe_on}'

    def save(self, *args, **kwargs):
        self.clean()
        super().save(*args, **kwargs)
