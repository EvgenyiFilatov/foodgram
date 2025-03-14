from django.db import models
from django.utils import timezone
from myprofile.models import MyProfile


class Tags(models.Model):
    """Тегами можно описать к какому типу относится рецепт."""

    name = models.CharField(
        unique=True,
        max_length=32,
        verbose_name='Название',
    )
    slug = models.SlugField(
        unique=True,
        max_length=32,
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
        max_length=128,
        verbose_name='Название',
    )
    measurement_unit = models.CharField(
        max_length=64,
        verbose_name='Единица измерения',
    )

    class Meta:
        verbose_name = 'Ингредиент'
        verbose_name_plural = 'Ингредиенты'

    def __str__(self):
        return self.name


class Recipes(models.Model):
    """Рецепты."""

    author = models.ForeignKey(
        MyProfile, on_delete=models.CASCADE,
        verbose_name='Автор', related_name='recipes',
    )
    name = models.CharField(
        max_length=256,
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
    cooking_time = models.PositiveIntegerField(
        verbose_name='Время приготовления',
    )
    is_favorited = models.BooleanField(default=False)
    is_in_shopping_cart = models.BooleanField(default=False)
    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name='Дата публикации'
    )
    short_link = models.CharField(max_length=10, unique=True, blank=True)

    class Meta:
        verbose_name = 'Рецепт'
        verbose_name_plural = 'Рецепты'
        ordering = ('-created_at',)

    def __str__(self):
        return self.name


class RecipeIngredients(models.Model):
    recipe = models.ForeignKey(
        Recipes, on_delete=models.CASCADE, related_name='ingredient'
    )
    ingredient = models.ForeignKey(Ingredients, on_delete=models.CASCADE)
    amount = models.PositiveIntegerField()

    class Meta:
        verbose_name = 'Ингредиент рецепта'
        verbose_name_plural = 'Ингредиенты рецептов'
