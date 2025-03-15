from django.contrib import admin
from recipes.models import Ingredients, RecipeIngredients, Recipes, Tags


@admin.register(Tags)
class Tags(admin.ModelAdmin):
    list_display = ('id', 'name', 'slug')


@admin.register(Ingredients)
class Ingredients(admin.ModelAdmin):
    list_display = ('id', 'name', 'measurement_unit')
    search_fields = ('name',)


class RecipeIngredientsInline(admin.TabularInline):
    model = RecipeIngredients
    extra = 1


@admin.register(Recipes)
class Recipes(admin.ModelAdmin):
    inlines = [RecipeIngredientsInline]
    list_display = (
        'name',
        'author',
        'cooking_time',
        'is_favorited',
        'is_in_shopping_cart',
        'favorited_count',
    )
    exclude = ('ingredients',)
    search_fields = ('name', 'author',)
    list_filter = ('tags',)
