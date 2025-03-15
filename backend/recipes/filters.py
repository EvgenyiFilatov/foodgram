from django_filters import rest_framework as filters
from myprofile.models import MyProfile
from recipes.models import Ingredients, Recipes, Tags


class IngredientsFilter(filters.FilterSet):

    name = filters.CharFilter(lookup_expr='istartswith')

    class Meta:
        model = Ingredients
        fields = ('name',)


class RecipesFilter(filters.FilterSet):
    author = filters.ModelChoiceFilter(queryset=MyProfile.objects.all())
    tags = filters.ModelMultipleChoiceFilter(
        queryset=Tags.objects.all(),
        field_name='tags__slug',
        to_field_name='slug',
        lookup_expr='exact'
    )
    is_favorited = filters.BooleanFilter(method='filter_is_favorited',)
    is_in_shopping_cart = filters.BooleanFilter(
        method='filter_is_in_shopping_list',
    )

    class Meta:
        model = Recipes
        fields = ['is_favorited', 'author', 'is_in_shopping_cart', 'tags']

    def filter_is_favorited(self, queryset, name, value):
        if value is None:
            return queryset

        if self.request.user.is_authenticated:
            if value:
                return queryset.filter(favorited_by=self.request.user)
            return queryset.exclude(favorited_by=self.request.user)

        return queryset

    def filter_is_in_shopping_list(self, queryset, name, value):
        if value is None:
            return queryset

        if self.request.user.is_authenticated:
            if value:
                return queryset.filter(in_shopping_cart=self.request.user)
            return queryset.exclude(in_shopping_cart=self.request.user)

        return queryset
