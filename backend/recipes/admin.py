from django.contrib import admin
from django.utils.safestring import mark_safe
from recipes.models import Ingredients, RecipeIngredients, Recipes, Tags


@admin.register(Tags)
class TagsAdmin(admin.ModelAdmin):
    list_display = ('id', 'name', 'slug')


@admin.register(Ingredients)
class IngredientsAdmin(admin.ModelAdmin):
    list_display = ('id', 'name', 'measurement_unit')
    search_fields = ('name', 'measurement_unit')
    list_filter = ('measurement_unit',)


class RecipeIngredientsInline(admin.TabularInline):
    model = RecipeIngredients
    extra = 1


@admin.register(Recipes)
class RecipesAdmin(admin.ModelAdmin):
    inlines = [RecipeIngredientsInline]
    list_display = (
        'name',
        'author',
        'cooking_time',
        'favorited_count',
        'tags_list',
        'display_image',
        'products_list'
    )
    exclude = ('ingredients',)
    search_fields = ('name', 'author__username',)
    list_filter = ('tags', 'author__username')

    @admin.display(description='Количество добавлений в избранное')
    def favorited_count(self, obj):
        return obj.favorited_by.count()

    @admin.display(description='Теги')
    def tags_list(self, obj):
        return ", ".join([tag.name for tag in obj.tags.all()])

    @mark_safe
    @admin.display(description='Изображение')
    def display_image(self, obj):
        if obj.image:
            return (
                f'<img src="{obj.image.url}"'
                'style="max-width: 150px; height: auto;" />'
            )
        return 'Нет изображения'
    display_image.allow_tags = True

    @admin.display(description='Продукты')
    def products_list(self, obj):
        return ", ".join(
            [f"{ingredient.ingredient} {ingredient.amount}"
             for ingredient in obj.ingredient.all()]
        )
