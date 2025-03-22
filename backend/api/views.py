from django.db.models import Sum
from django.shortcuts import get_object_or_404, redirect
from django.urls import reverse
from django_filters import rest_framework as filters
from myprofile.models import MyProfile, Subscription
from rest_framework import permissions, status, viewsets
from rest_framework.decorators import action
from rest_framework.exceptions import ValidationError
from rest_framework.filters import SearchFilter
from rest_framework.response import Response

from api.filters import IngredientsFilter, RecipesFilter
from api.paginators import CustomPageLimitPagination
from api.permissions import IsAuthorOrAdminOrReadOnly
from api.serializers import (
    ChangePasswordSerializer,
    IngredientsSerializer,
    RecipesCreateUpdateSerializer,
    RecipesSerializer,
    ShortRecipesSerializer,
    SubscriptionSerializer,
    TagsSerializer,
    UserCreateSerializer,
    UserSerializer,
)
from api.utils import generate_shopping_list
from recipes.models import Ingredients, Recipes, Tags


class UserViewSet(viewsets.ModelViewSet):
    queryset = MyProfile.objects.all()
    serializer_class = UserSerializer

    def create(self, request):
        serializer = UserCreateSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    @action(
        detail=False,
        methods=('get',),
        url_path='me',
        permission_classes=(permissions.IsAuthenticated,)
    )
    def me(self, request):
        serializer = UserSerializer(request.user)
        return Response(serializer.data)

    @action(
        detail=False,
        methods=('put', 'delete'),
        url_path='me/avatar',
        permission_classes=(permissions.IsAuthenticated,)
    )
    def avatar(self, request):
        user = request.user
        if request.method == 'PUT':
            serializer = UserSerializer(user, data=request.data, partial=True)
            if serializer.is_valid():
                serializer.save()
                avatar_url = user.avatar.url if user.avatar else None
                return Response(
                    {"avatar": request.build_absolute_uri(avatar_url)},
                    status=status.HTTP_200_OK
                )
            return Response(
                serializer.errors,
                status=status.HTTP_400_BAD_REQUEST
            )

        elif request.method == 'DELETE':
            if user.avatar:
                user.avatar.delete(save=False)
                user.avatar = None
                user.save()
            return Response(status=status.HTTP_204_NO_CONTENT)

    @action(
        detail=False,
        methods=('post',),
        url_path='set_password',
        permission_classes=(permissions.IsAuthenticated,)
    )
    def set_password(self, request):
        user = request.user
        serializer = ChangePasswordSerializer(
            data=request.data, context={'request': request}
        )
        if serializer.is_valid():
            new_password = serializer.validated_data['new_password']
            user.set_password(new_password)
            user.save()
            return Response(
                {"detail": "Пароль успешно изменен."},
                status=status.HTTP_204_NO_CONTENT
            )
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    @action(
        detail=False,
        methods=('get',),
        url_path='subscriptions',
        permission_classes=(permissions.IsAuthenticated,)
    )
    def subscriptions(self, request):
        user = request.user
        subscriptions = Subscription.objects.filter(subscriber=user)
        paginator = self.pagination_class()
        paginated_subscriptions = paginator.paginate_queryset(
            subscriptions, request
        )
        serializer = SubscriptionSerializer(
            paginated_subscriptions,
            many=True,
            context={'request': request})
        return paginator.get_paginated_response(serializer.data)

    @action(
        detail=True,
        methods=('post', 'delete'),
        url_path='subscribe',
        permission_classes=(permissions.IsAuthenticated,)
    )
    def subscribe(self, request, pk=None):
        user = request.user
        subscribe_to = get_object_or_404(MyProfile, id=pk)
        if request.method == "POST":
            if user == subscribe_to:
                return Response(
                    {'detail': 'Невозможно подписаться на самого себя.'},
                    status=status.HTTP_400_BAD_REQUEST
                )
            subscription, created = Subscription.objects.get_or_create(
                subscriber=user,
                subscribe_to=subscribe_to
            )
            if not created:
                return Response(
                    {'detail': 'Вы уже подписаны на этого пользователя.'},
                    status=status.HTTP_400_BAD_REQUEST
                )
            return Response(
                SubscriptionSerializer(subscription,
                                       context={'request': request}
                                       ).data, status=status.HTTP_201_CREATED
            )
        elif request.method == "DELETE":
            subscription = Subscription.objects.filter(
                subscriber=user, subscribe_to=subscribe_to).first()
            if not subscription:
                return Response(
                    {'detail': 'Подписка не найдена.'},
                    status=status.HTTP_400_BAD_REQUEST
                )
            subscription.delete()
            return Response(
                {'detail': 'Подписка удалена.'},
                status=status.HTTP_204_NO_CONTENT
            )


class TagsViewSet(viewsets.ReadOnlyModelViewSet):
    """Класс для работы с тегами рецептов."""

    queryset = Tags.objects.all()
    serializer_class = TagsSerializer
    pagination_class = None


class IngredientsViewSet(viewsets.ReadOnlyModelViewSet):
    """Класс для работы с ингредиентами рецептов."""

    queryset = Ingredients.objects.all()
    serializer_class = IngredientsSerializer
    filter_backends = (filters.DjangoFilterBackend, SearchFilter,)
    filterset_class = IngredientsFilter
    pagination_class = None


class RecipesViewSet(viewsets.ModelViewSet):
    """Для рецептов."""

    queryset = Recipes.objects.select_related(
        'author').prefetch_related('ingredients', 'tags')
    filter_backends = (filters.DjangoFilterBackend, SearchFilter)
    filterset_class = RecipesFilter
    serializer_class = RecipesSerializer
    pagination_class = CustomPageLimitPagination

    def get_permissions(self):
        if self.request.method == 'POST' or self.action in (
            'favorite', 'add_to_shopping_cart', 'download_shopping_cart',
        ):
            return (permissions.IsAuthenticated(),)
        elif self.request.method in ['PATCH', 'DELETE']:
            return (IsAuthorOrAdminOrReadOnly(),)
        return super().get_permissions()

    def get_serializer_class(self):
        if self.request.method in ['POST', 'PATCH']:
            return RecipesCreateUpdateSerializer
        return super().get_serializer_class()

    def perform_create(self, serializer):
        recipe = serializer.save(author=self.request.user)
        return recipe

    @action(detail=True, methods=['get'], url_path='get-link')
    def get_short_link(self, request, pk=None):
        """Получить короткую ссылку на рецепт."""
        recipe = get_object_or_404(Recipes, id=pk)
        short_link = request.build_absolute_uri(f'/s/{recipe.short_link}')
        return Response({'short-link': short_link})

    def _add_del_favorite_and_cart(
        self, request, pk, related_name, add_error, delete_error
    ):
        recipe = get_object_or_404(Recipes, id=pk)
        user = request.user
        related_model = getattr(user, related_name)
        if request.method == 'POST':
            if related_model.filter(id=recipe.id).exists():
                raise ValidationError(add_error)
            related_model.add(recipe)
            recipe.save()
            return Response(ShortRecipesSerializer(
                recipe).data, status=status.HTTP_201_CREATED)
        if not related_model.filter(id=recipe.id).exists():
            raise ValidationError(delete_error)

        related_model.remove(recipe)
        recipe.save()
        return Response(status=status.HTTP_204_NO_CONTENT)

    @action(
        detail=True,
        methods=('post', 'delete'),
        url_path='favorite',
    )
    def favorite(self, request, pk=None):
        return self._add_del_favorite_and_cart(
            request,
            pk,
            'favorite_recipes',
            'Рецепт уже добавлен в избранное.',
            'Рецепт не найден в избранном.',
        )

    @action(
        detail=True,
        methods=('post', 'delete'),
        url_path='shopping_cart',
    )
    def add_to_shopping_cart(self, request, pk=None):
        return self._add_del_favorite_and_cart(
            request,
            pk,
            'shopping_cart_recipes',
            'Рецепт уже добавлен в корзину.',
            'Рецепт не найден в корзине.',
        )

    @action(
        detail=False,
        methods=('get',),
        url_path='download_shopping_cart',
    )
    def download_shopping_cart(self, request):
        """Для скачивания списка покупок."""
        user = request.user
        recipes_ingredients = (
            user.shopping_cart_recipes.prefetch_related(
                'recipe_ingredients__ingredient'
            )
            .values(
                'recipe_ingredients__ingredient__name',
                'recipe_ingredients__ingredient__measurement_unit',
            )
            .annotate(total_amount=Sum('recipe_ingredients__amount'))
        )
        ingredients = {
            item['recipe_ingredients__ingredient__name']: {
                'measurement_unit':
                item['recipe_ingredients__ingredient__measurement_unit'],
                'total_amount': item['total_amount']
            }
            for item in recipes_ingredients
        }
        return generate_shopping_list(ingredients)


def redirect_short_link(request, short_link):
    """Перенаправление по короткой ссылке на рецепт."""
    recipe = get_object_or_404(Recipes, short_link=short_link)
    return redirect(f'/recipes/{recipe.id}')
