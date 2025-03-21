import re

from myprofile.models import MyProfile, Subscription
from rest_framework import serializers

from api.fields import Base64ImageField
from recipes.constants import MIN_INGREDIENTS_AMOUNT
from recipes.models import Ingredients, RecipeIngredients, Recipes, Tags


class UserSerializer(serializers.ModelSerializer):
    avatar = Base64ImageField(required=False, allow_null=True)
    is_subscribed = serializers.SerializerMethodField()

    class Meta:
        model = MyProfile
        fields = (
            'id',
            'first_name',
            'last_name',
            'username',
            'email',
            'avatar',
            'is_subscribed'
        )

    def update(self, instance, validated_data):
        if 'avatar' not in validated_data:
            raise serializers.ValidationError("Аватар не должен быть пустым")
        instance.avatar = validated_data.get('avatar', instance.avatar)
        instance.save()
        return instance

    def get_is_subscribed(self, obj):
        request = self.context.get('request')
        if request is not None and request.user.is_authenticated:
            return Subscription.objects.filter(
                subscriber=request.user,
                subscribe_to=obj
            ).exists()
        return False


class UserCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = MyProfile
        fields = (
            'first_name',
            'id',
            'last_name',
            'username',
            'email',
            'password',
        )
        extra_kwargs = {'password': {'write_only': True}}

    def validate_username(self, value):
        pattern = r'^[\w.@+-]+\Z'
        if not re.match(pattern, value):
            raise serializers.ValidationError("Некорректное имя пользователя.")
        return value

    def create(self, validated_data):
        user = MyProfile.objects.create_user(**validated_data)
        return user


class ChangePasswordSerializer(serializers.Serializer):
    current_password = serializers.CharField(required=True)
    new_password = serializers.CharField(required=True)

    def validate(self, data):
        user = self.context['request'].user
        current_password = data['current_password']
        if not user.check_password(current_password):
            raise serializers.ValidationError(
                {"current_password": "Неверный текущий пароль."}
            )
        return data


class ShortRecipesSerializer(serializers.ModelSerializer):
    """Сериализатор отображения рецептов у подписчиков."""
    image = Base64ImageField(required=False, allow_null=True)

    class Meta:
        model = Recipes
        fields = (
            'id',
            'image',
            'name',
            'cooking_time'
        )


class UserSerializerWithRecipes(UserSerializer):
    avatar = Base64ImageField(read_only=True)
    recipes = serializers.SerializerMethodField()
    recipes_count = serializers.SerializerMethodField()
    is_subscribed = serializers.SerializerMethodField()

    class Meta:
        model = MyProfile
        fields = (
            'id',
            'first_name',
            'last_name',
            'username',
            'email',
            'avatar',
            'is_subscribed',
            'recipes',
            'recipes_count'
        )

    def get_recipes_count(self, obj):
        return obj.recipes.count()

    def get_recipes(self, obj):
        request = self.context.get('request')
        limit = request.GET.get('recipes_limit') if request else None
        queryset = Recipes.objects.filter(author=obj.id)
        if limit and limit.isdigit():
            queryset = queryset[:int(limit)]
        return ShortRecipesSerializer(queryset, many=True).data

    def get_is_subscribed(self, obj):
        request = self.context.get('request')
        if request is not None and request.user.is_authenticated:
            return Subscription.objects.filter(
                subscriber=request.user,
                subscribe_to=obj
            ).exists()
        return False


class SubscriptionSerializer(serializers.ModelSerializer):
    subscribe_to = UserSerializerWithRecipes(read_only=True)

    class Meta:
        model = Subscription
        fields = ('subscribe_to',)

    def to_representation(self, instance):
        representation = super().to_representation(instance)
        user_data = representation['subscribe_to']
        return user_data


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
    id = serializers.ReadOnlyField(source='ingredient.id',)
    name = serializers.ReadOnlyField(source='ingredient.name',)
    measurement_unit = serializers.ReadOnlyField(
        source='ingredient.measurement_unit',
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

    def validate_tags(self, tags):
        """Проверка на наличие пустых и повторяющихся полей."""
        # tags = attrs.get('tags')
        if not tags:
            raise serializers.ValidationError(
                "Поле 'tags' не может быть пустым.")
        if len(tags) != len(set(tags)):
            raise serializers.ValidationError("Теги не должны повторяться.")
        return tags

    def validate_ingredients(self, ingredients):

        # ingredients = attrs.get('ingredients')
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

        return ingredients

    def create(self, validated_data):
        ingredients_data = validated_data.pop('ingredients')
        tags_data = validated_data.pop('tags')
        recipe = Recipes.objects.create(**validated_data)
        recipe.tags.set(tags_data)
        self._create_ingredients(recipe, ingredients_data)

        return recipe

    def update(self, instance, validated_data):
        missing_fields = [
            field
            for field in ('tags', 'ingredients')
            if field not in validated_data
        ]
        if missing_fields:
            raise serializers.ValidationError(
                {field: 'Обязательное поле.' for field in missing_fields}
            )
        ingredients_data = validated_data.pop('ingredients', None)
        tags_data = validated_data.pop('tags', None)

        for attr, value in validated_data.items():
            setattr(instance, attr, value)

        if tags_data is not None:
            instance.tags.set(tags_data)

        RecipeIngredients.objects.filter(recipe=instance).delete()
        if ingredients_data is not None:
            self._create_ingredients(instance, ingredients_data)

        instance.save()
        return instance

    def _create_ingredients(self, recipe, ingredients_data):
        ingredients = [
            RecipeIngredients(
                recipe=recipe,
                ingredient=item['id'],
                amount=item['amount']
            ) for item in ingredients_data
        ]
        RecipeIngredients.objects.bulk_create(ingredients)

    def to_representation(self, instance):
        return RecipesSerializer(instance, context=self.context).data


class RecipesSerializer(serializers.ModelSerializer):
    """Сериализатор для работы с рецептами."""
    image = Base64ImageField(required=False, allow_null=True)
    author = UserSerializer(read_only=True)
    tags = TagsSerializer(many=True)
    ingredients = RecipeIngredientSerializer(
        source='recipe_ingredients',
        many=True, read_only=True)
    is_favorited = serializers.SerializerMethodField()
    is_in_shopping_cart = serializers.SerializerMethodField()

    class Meta:
        model = Recipes
        fields = (
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
        )

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
