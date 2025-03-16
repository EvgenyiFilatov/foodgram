import re

from api.serializers import Base64ImageField
from myprofile.models import MyProfile, Subscription
from recipes.models import Recipes
from recipes.serializers import RecipesForFavoriteAndShoppingSerializer
from rest_framework import serializers


class UserSerializer(serializers.ModelSerializer):
    avatar = Base64ImageField(required=False, allow_null=True)
    is_subscribed = serializers.SerializerMethodField()

    class Meta:
        model = MyProfile
        fields = [
            'id',
            'first_name',
            'last_name',
            'username',
            'email',
            'avatar',
            'is_subscribed'
        ]

    def update(self, instance, validated_data):
        if 'avatar' not in validated_data:
            raise serializers.ValidationError("Аватар не должен быть пустым.")
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
        fields = [
            'first_name',
            'id',
            'last_name',
            'username',
            'email',
            'password',
        ]
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


class UserSerializerWithRecipes(UserSerializer):
    avatar = Base64ImageField(read_only=True)
    recipes = serializers.SerializerMethodField()
    recipes_count = serializers.SerializerMethodField()
    is_subscribed = serializers.SerializerMethodField()

    class Meta:
        model = MyProfile
        fields = [
            'id',
            'first_name',
            'last_name',
            'username',
            'email',
            'avatar',
            'is_subscribed',
            'recipes',
            'recipes_count'
        ]

    def get_recipes_count(self, obj):
        return obj.recipes.count()

    def get_recipes(self, obj):
        request = self.context.get('request')
        limit = request.GET.get('recipes_limit') if request else None
        queryset = Recipes.objects.filter(author=obj.id)
        if limit and limit.isdigit():
            queryset = queryset[:int(limit)]
        return RecipesForFavoriteAndShoppingSerializer(
            queryset, many=True
        ).data

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
        fields = ['subscribe_to']

    def to_representation(self, instance):
        representation = super().to_representation(instance)
        user_data = representation['subscribe_to']
        return user_data
