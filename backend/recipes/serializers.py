from myprofile.serializers import Base64ImageField, UserSerializer
from rest_framework import serializers

from recipes.constants import MIN_COOKING_TIME, MIN_INGREDIENTS_AMOUNT
from recipes.models import Ingredients, RecipeIngredients, Recipes, Tags


class TagsSerializer(serializers.ModelSerializer):
    """Сериализатор для работы с тегами рецептов."""
    class Meta:
        model = Tags
        fields = ('id', 'name', 'slug')


class IngredientsSerializer(serializers.ModelSerializer):
    """Сериализатор для работы с ингридиентами рецептов."""

    class Meta:
        model = Ingredients
        fields = ('id', 'name', 'measurement_unit')


class RecipeIngredientSerializerForCreate(serializers.ModelSerializer):
    """Для добавления ингридиентов в рецепт."""
    id = serializers.PrimaryKeyRelatedField(queryset=Ingredients.objects.all())

    class Meta:
        model = RecipeIngredients
        fields = ('id', 'amount')


class RecipeIngredientSerializer(serializers.ModelSerializer):
    """Для отображения ингридиентов в рецепте."""
    id = serializers.ReadOnlyField(source='ingredients.id',)
    name = serializers.ReadOnlyField(source='ingredients.name',)
    measurement_unit = serializers.ReadOnlyField(
        source='ingredients.measurement_unit',
    )

    class Meta:
        model = RecipeIngredients
        fields = ('id', 'name', 'measurement_unit', 'amount',)


class RecipesCreateUpdateSerializer(serializers.ModelSerializer):
    """Сериализатор для создания и обновления рецептов."""
    image = Base64ImageField()
    tags = serializers.PrimaryKeyRelatedField(
        queryset=Tags.objects.all(), many=True
    )
    ingredients = RecipeIngredientSerializerForCreate(many=True)

    class Meta:
        model = Recipes
        fields = (
            'id',
            'tags',
            'ingredients',
            'name',
            'image',
            'text',
            'cooking_time'
        )

    def validate_cooking_time(self, value):
        """Проверка, что время готовки не менее требуемого."""
        if value < MIN_COOKING_TIME:
            raise serializers.ValidationError(
                f"Время готовки должно быть не менее {MIN_COOKING_TIME}.")
        return value

    def validate(self, attrs):
        """Проверка на наличие пустых и повторяющихся полей."""
        tags = attrs.get('tags')
        if not tags:
            raise serializers.ValidationError(
                "Поле 'tags' не может быть пустым.")
        if len(tags) != len(set(tags)):
            raise serializers.ValidationError("Теги не должны повторяться.")

        ingredients = attrs.get('ingredients')
        if not ingredients:
            raise serializers.ValidationError(
                "Должен быть хотя бы один ингредиент.")
        ingredient_ids = [item['id'] for item in ingredients]
        ingredient_amount = [item['amount'] for item in ingredients]
        for item in ingredient_amount:
            if item < MIN_INGREDIENTS_AMOUNT:
                raise serializers.ValidationError(
                    "Количество ингредиента не может быть меньше "
                    f"{MIN_INGREDIENTS_AMOUNT}."
                )

        if len(ingredient_ids) != len(set(ingredient_ids)):
            raise serializers.ValidationError(
                "Ингредиенты не должны повторяться.")

        return attrs

    def create(self, validated_data):
        ingredients_data = validated_data.pop('ingredients')
        tags_data = validated_data.pop('tags')
        recipe = Recipes.objects.create(**validated_data)
        recipe.tags.set(tags_data)

        for ingredient_data in ingredients_data:
            ingredient = ingredient_data['id']
            RecipeIngredients.objects.create(
                recipe=recipe, ingredient=ingredient,
                amount=ingredient_data['amount']
            )

        return recipe

    def update(self, instance, validated_data):
        ingredients_data = validated_data.pop('ingredients', None)
        tags_data = validated_data.pop('tags', None)

        for attr, value in validated_data.items():
            setattr(instance, attr, value)

        if tags_data is not None:
            instance.tags.set(tags_data)

        RecipeIngredients.objects.filter(recipe=instance).all().delete()
        if ingredients_data is not None:
            instance.ingredients.all().delete()
            for item in ingredients_data:
                RecipeIngredients.objects.create(
                    recipe=instance,
                    ingredient=item['id'],
                    amount=item['amount']
                )

        instance.save()
        return instance

    def to_representation(self, instance):
        representation = super().to_representation(instance)
        ingredients = []
        for recipe_ingredient in instance.ingredient.all():
            ingredients.append({
                'id': recipe_ingredient.ingredient.id,
                'name': recipe_ingredient.ingredient.name,
                'amount': recipe_ingredient.amount,
                'measurement_unit':
                recipe_ingredient.ingredient.measurement_unit,
            })
        representation['ingredients'] = ingredients
        return representation


class RecipesForFavoriteAndShoppingSerializer(serializers.ModelSerializer):
    """Сериализатор для работы с рецептами."""
    image = Base64ImageField(required=False, allow_null=True)

    class Meta:
        model = Recipes
        fields = [
            'id',
            'name',
            'image',
            'cooking_time'
        ]


class RecipesSerializer(serializers.ModelSerializer):
    """Сериализатор для работы с рецептами."""
    image = Base64ImageField(required=False, allow_null=True)
    author = UserSerializer(read_only=True)
    tags = TagsSerializer(many=True)
    ingredients = RecipeIngredientSerializer(many=True, read_only=True)
    is_favorited = serializers.SerializerMethodField()
    is_in_shopping_cart = serializers.SerializerMethodField()

    class Meta:
        model = Recipes
        fields = [
            'id',
            'tags',
            'author',
            'ingredients',
            'is_favorited',
            'is_in_shopping_cart',
            'name',
            'image',
            'text',
            'cooking_time'
        ]

    def get_is_favorited(self, obj):
        request = self.context.get('request')
        if request and request.user.is_authenticated:
            return request.user.favorite_recipes.filter(id=obj.id).exists()

        return False

    def get_is_in_shopping_cart(self, obj):
        request = self.context.get('request')
        if request and request.user.is_authenticated:
            return request.user.shopping_cart_recipes.filter(
                id=obj.id
            ).exists()

        return False

    def to_representation(self, instance):
        representation = super().to_representation(instance)
        ingredients = []
        for recipe_ingredient in instance.ingredient.all():
            ingredients.append({
                'id': recipe_ingredient.ingredient.id,
                'name': recipe_ingredient.ingredient.name,
                'amount': recipe_ingredient.amount,
                'measurement_unit':
                recipe_ingredient.ingredient.measurement_unit,
            })
        representation['ingredients'] = ingredients
        return representation
