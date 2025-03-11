from django.contrib.auth.models import (
    AbstractBaseUser,
    BaseUserManager,
    PermissionsMixin
)
from django.db import models


class MyProfileManager(BaseUserManager):
    def create_user(
            self, email,
            first_name,
            last_name,
            username,
            password=None,
            **extra_fields
    ):
        if not email:
            raise ValueError('Email обязателен к заполнению')
        if not first_name:
            raise ValueError('Имя обязательно к заполнению')
        if not last_name:
            raise ValueError('Фамилия обязательна к заполнению')
        if not username:
            raise ValueError('Никнейм обязателен к заполнению')

        email = self.normalize_email(email)
        user = self.model(
            email=email,
            first_name=first_name,
            last_name=last_name,
            username=username,
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
            email,
            first_name,
            last_name,
            username,
            password,
            **extra_fields
        )


class MyProfile(AbstractBaseUser, PermissionsMixin):
    """Кастомная модель юзера, позволяет выбрать роль каждого пользователя."""
    first_name = models.CharField(
        max_length=150,
        verbose_name="Имя",
        blank=False
    )
    last_name = models.CharField(
        max_length=150,
        verbose_name="Фамилия",
        blank=False
    )
    username = models.CharField(
        max_length=150,
        unique=True,
        verbose_name="Имя пользователя",
        blank=False
    )
    email = models.EmailField(
        max_length=254,
        unique=True,
        verbose_name="Адрес электронной почты",
        blank=False
    )
    avatar = models.ImageField(
        upload_to='backend/avatar/',
        null=True,
        default=None
    )
    is_active = models.BooleanField(default=True)
    is_staff = models.BooleanField(default=False)
    is_subscribed = models.BooleanField(default=False)
    favorite_recipes = models.ManyToManyField(
        'recipes.Recipes',
        related_name='favorited_by',
        blank=True
    )
    shopping_cart_recipes = models.ManyToManyField(
        'recipes.Recipes',
        related_name='in_shopping_cart',
        blank=True
    )

    objects = MyProfileManager()

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['username', 'first_name', 'last_name']

    class Meta:
        verbose_name = 'Пользователь'
        verbose_name_plural = 'Пользователи'

    def __str__(self):
        return self.username


class Subscription(models.Model):
    subscriber = models.ForeignKey(
        MyProfile,
        related_name='subscriptions',
        on_delete=models.CASCADE
    )
    subscribe_to = models.ForeignKey(
        MyProfile,
        related_name='subscribers',
        on_delete=models.CASCADE
    )

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=['subscriber', 'subscribe_to'],
                name='unique_subscription'
            )
        ]
        verbose_name = 'Подписка'
        verbose_name_plural = 'Подписки'

    def save(self, *args, **kwargs):
        if self.subscriber == self.subscribe_to:
            raise ValueError('Невозможно подписаться на самого себя.')
        super().save(*args, **kwargs)

    def __str__(self):
        return (
            f'{self.subscriber.username} подписался на'
            f'{self.subscribe_to.username}'
        )
