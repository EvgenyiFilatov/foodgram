import csv
import hashlib
from collections import defaultdict
from io import BytesIO, TextIOWrapper

from api.paginators import CustomPageLimitPagination
from django.http import HttpResponse
from django.shortcuts import get_object_or_404, redirect
from django_filters import rest_framework as filters
from recipes.filters import IngredientsFilter, RecipesFilter
from recipes.models import Ingredients, Recipes, Tags
from recipes.permissions import IsAuthorOrAdminOrReadOnly
from recipes.serializers import (IngredientsSerializer,
                                 RecipesCreateUpdateSerializer,
                                 RecipesForFavoriteAndShoppingSerializer,
                                 RecipesSerializer, TagsSerializer)
from rest_framework import permissions, status, viewsets
from rest_framework.decorators import action
from rest_framework.filters import SearchFilter
from rest_framework.response import Response


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

    queryset = Recipes.objects.all()
    filter_backends = (filters.DjangoFilterBackend, SearchFilter)
    filterset_class = RecipesFilter
    serializer_class = RecipesSerializer
    pagination_class = CustomPageLimitPagination

    def get_permissions(self):
        if self.request.method == 'POST':
            return [permissions.IsAuthenticated()]
        elif self.request.method in ['PATCH', 'DELETE']:
            if self.request.user.is_staff:
                return True
            return [IsAuthorOrAdminOrReadOnly()]
        return super().get_permissions()

    def create(self, request, *args, **kwargs):
        serializer = RecipesCreateUpdateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        recipe = serializer.save(author=request.user)
        return Response(RecipesSerializer(recipe).data, status=201)

    def update(self, request, pk=None, partial=False):
        recipe = get_object_or_404(Recipes, id=pk)
        self.check_object_permissions(request, recipe)
        serializer = RecipesCreateUpdateSerializer(
            recipe, data=request.data, partial=partial)
        serializer.is_valid(raise_exception=True)
        recipe = serializer.save()
        return Response(RecipesSerializer(recipe).data)

    def destroy(self, request, pk=None):
        recipe = get_object_or_404(Recipes, id=pk)
        self.check_object_permissions(request, recipe)
        recipe.delete()
        return Response(
            {'detail': 'Рецепт удален.'},
            status=status.HTTP_204_NO_CONTENT
        )

    @action(detail=True, methods=['get'], url_path='get-link')
    def get_short_link(self, request, pk=None):
        """Получить короткую ссылку на рецепт."""
        recipe = get_object_or_404(Recipes, id=pk)
        if not recipe.short_link:
            recipe_hash = hashlib.md5(f"{recipe.id}".encode()).hexdigest()[:6]
            recipe.short_link = recipe_hash
            recipe.save()
        short_link = request.build_absolute_uri(f"/s/{recipe.short_link}")
        return Response({"short-link": short_link})

    @action(
        detail=True,
        methods=['post', 'delete'],
        url_path='favorite',
        permission_classes=(permissions.IsAuthenticated,)
    )
    def add_to_favorites(self, request, pk=None):
        recipe = get_object_or_404(Recipes, id=pk)
        if not request.user.is_authenticated:
            return Response(
                {'detail': 'Необходима авторизация.'},
                status=status.HTTP_401_UNAUTHORIZED
            )
        if request.method == 'POST':
            if request.user.favorite_recipes.filter(id=recipe.id).exists():
                return Response(
                    {'detail': 'Рецепт уже добавлен в избранное.'},
                    status=status.HTTP_400_BAD_REQUEST
                )
            request.user.favorite_recipes.add(recipe)
            recipe.save()
            return Response(RecipesForFavoriteAndShoppingSerializer(
                recipe).data, status=status.HTTP_201_CREATED)
        elif request.method == 'DELETE':
            if not request.user.favorite_recipes.filter(id=recipe.id).exists():
                return Response(
                    {'detail': 'Рецепт не найден в избранном.'},
                    status=status.HTTP_400_BAD_REQUEST
                )
            request.user.favorite_recipes.remove(recipe)
            recipe.save()
            return Response(status=status.HTTP_204_NO_CONTENT)

    @action(
        detail=True,
        methods=['post', 'delete'],
        url_path='shopping_cart',
        permission_classes=(permissions.IsAuthenticated,)
    )
    def add_to_shopping_cart(self, request, pk=None):
        recipe = get_object_or_404(Recipes, id=pk)
        if not request.user.is_authenticated:
            return Response(
                {'detail': 'Необходима авторизация.'},
                status=status.HTTP_401_UNAUTHORIZED
            )
        if request.method == 'POST':
            if request.user.shopping_cart_recipes.filter(
                id=recipe.id
            ).exists():
                return Response(
                    {'detail': 'Рецепт уже добавлен в корзину.'},
                    status=status.HTTP_400_BAD_REQUEST
                )
            request.user.shopping_cart_recipes.add(recipe)
            return Response(RecipesForFavoriteAndShoppingSerializer(
                recipe).data, status=status.HTTP_201_CREATED)
        elif request.method == 'DELETE':
            if not request.user.shopping_cart_recipes.filter(
                    id=recipe.id).exists():
                return Response(
                    {'detail': 'Рецепт не найден в корзине.'},
                    status=status.HTTP_400_BAD_REQUEST
                )
            request.user.shopping_cart_recipes.remove(recipe)
            return Response(status=status.HTTP_204_NO_CONTENT)

    def get_object(self, pk):
        try:
            return Recipes.objects.get(pk=pk)
        except Recipes.DoesNotExist:
            return Response(
                {'error': 'Рецепт не найден'},
                status=status.HTTP_404_NOT_FOUND
            )

    def retrieve(self, request, *args, **kwargs):
        recipe = self.get_object(kwargs['pk'])
        if isinstance(recipe, Response):
            return recipe
        serializer = RecipesSerializer(recipe, context={'request': request})
        return Response(serializer.data)

    @action(
        detail=False,
        methods=['get'],
        url_path='download_shopping_cart',
        permission_classes=(permissions.IsAuthenticated,)
    )
    def download_shopping_cart(self, request):
        """Для скачивания списка покупок."""
        user = request.user
        recipes = user.shopping_cart_recipes.all()
        ingredients = defaultdict(
            lambda: {'amount': 0, 'measurement_unit': None})

        for recipe in recipes:
            for recipe_ingredient in recipe.ingredient.all():
                ingredient = recipe_ingredient.ingredient
                ingredients[ingredient]['amount'] += recipe_ingredient.amount
                ingredients[ingredient]['measurement_unit'] = (
                    ingredient.measurement_unit
                )

        print(ingredients)

        output = BytesIO()
        text_output = TextIOWrapper(output, encoding='utf-8-sig', newline='')

        writer = csv.writer(
            text_output, delimiter=',',
            quoting=csv.QUOTE_MINIMAL
        )
        writer.writerow(['Ingredient', 'Amount', 'Measurement Unit'])

        for name, data in ingredients.items():
            writer.writerow([name, data['amount'], data['measurement_unit']])

        text_output.flush()
        output.seek(0)

        response = HttpResponse(output.getvalue(), content_type='text/csv')
        response['Content-Disposition'] = (
            'attachment; filename="shopping_cart.csv"'
        )
        return response


def redirect_short_link(request, short_link):
    """Перенаправление по короткой ссылке на рецепт."""
    recipe = get_object_or_404(Recipes, short_link=short_link)
    return redirect(f'/recipes/{recipe.id}/')
