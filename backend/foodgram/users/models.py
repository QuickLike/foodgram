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
