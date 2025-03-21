import random
import string

from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models
from myprofile.models import MyProfile

from recipes.constants import (
    MAX_AMOUNT,
    MAX_COOKING_TIME,
    MAX_LENGTH_MEAS_UNIT,
    MAX_LENGTH_NAME_INGR,
    MAX_LENGTH_NAME_RESIPES,
    MAX_LENGTH_NAME_TAGS,
    MAX_LENGTH_SHORT_LINK,
    MAX_LENGTH_SLUG_TAGS,
    MIN_AMOUNT,
    MIN_COOKING_TIME,
)


class Tags(models.Model):
    """Тегами можно описать к какому типу относится рецепт."""

    name = models.CharField(
        unique=True,
        max_length=MAX_LENGTH_NAME_TAGS,
        verbose_name='Название',
    )
    slug = models.SlugField(
        unique=True,
        max_length=MAX_LENGTH_SLUG_TAGS,
        verbose_name='Уникальный идентификатор',
    )

    class Meta:
        verbose_name = 'Тег'
        verbose_name_plural = 'Теги'

    def __str__(self):
        return self.name


class Ingredients(models.Model):
    """Ингредиенты для приготовления рецепта."""

    name = models.CharField(
        max_length=MAX_LENGTH_NAME_INGR,
        verbose_name='Название',
    )
    measurement_unit = models.CharField(
        max_length=MAX_LENGTH_MEAS_UNIT,
        verbose_name='Единица измерения',
    )

    class Meta:
        verbose_name = 'Ингредиент'
        verbose_name_plural = 'Ингредиенты'
        unique_together = ('name', 'measurement_unit')

    def __str__(self):
        return f'{self.name} ({self.measurement_unit})'


class Recipes(models.Model):
    """Рецепты."""

    author = models.ForeignKey(
        MyProfile, on_delete=models.CASCADE,
        verbose_name='Автор', related_name='recipes',
    )
    name = models.CharField(
        max_length=MAX_LENGTH_NAME_RESIPES,
        verbose_name='Название рецепта',
    )
    image = models.ImageField(
        upload_to='backend/image/'
    )
    text = models.TextField(verbose_name='Текст')
    tags = models.ManyToManyField(
        Tags,
        related_name='recipes',
        verbose_name='Теги',
    )
    ingredients = models.ManyToManyField(
        Ingredients,
        related_name='recipes',
        verbose_name='Ингредиенты',
    )
    cooking_time = models.PositiveSmallIntegerField(
        verbose_name='Время приготовления, мин',
        validators=[
            MinValueValidator(MIN_COOKING_TIME),
            MaxValueValidator(MAX_COOKING_TIME)
        ]
    )
    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name='Дата публикации'
    )
    short_link = models.CharField(
        max_length=MAX_LENGTH_SHORT_LINK,
        unique=True,
        blank=True,
        null=True
    )

    class Meta:
        verbose_name = 'Рецепт'
        verbose_name_plural = 'Рецепты'
        ordering = ('-created_at',)

    def generate_short_link(self):
        """Генерация уникальной короткой ссылки."""
        while True:
            recipe_hash = ''.join(
                random.choices(string.ascii_letters + string.digits, k=6)
            )
            if not Recipes.objects.filter(short_link=recipe_hash).exists():
                return recipe_hash

    def save(self, *args, **kwargs):
        if not self.short_link:
            self.short_link = self.generate_short_link()
        super().save(*args, **kwargs)

    def __str__(self):
        return self.name

    @property
    def favorited_count(self):
        return self.favorited_by.count()


class RecipeIngredients(models.Model):
    recipe = models.ForeignKey(
        Recipes,
        on_delete=models.CASCADE,
        verbose_name='Рецепт',
        related_name='recipe_ingredients'
    )
    ingredient = models.ForeignKey(
        Ingredients,
        on_delete=models.CASCADE,
        verbose_name='Ингредиент',
        related_name='recipe_ingredients'
    )
    amount = models.PositiveSmallIntegerField(
        validators=[
            MinValueValidator(MIN_AMOUNT),
            MaxValueValidator(MAX_AMOUNT)
        ]
    )

    class Meta:
        verbose_name = 'Ингредиент рецепта'
        verbose_name_plural = 'Ингредиенты рецептов'
        unique_together = ('ingredient', 'recipe')
