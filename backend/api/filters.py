
from django_filters import rest_framework as filters

from recipes.models import Ingredient, Recipe, Tag, User


class RecipeFilter(filters.FilterSet):
    """
    Определяет параметры фильтрации для рецептов.
    """

    tags = filters.ModelMultipleChoiceFilter(
        field_name='tags__slug',
        to_field_name='slug',
        queryset=Tag.objects.all(),
        conjoined=False
    )
    is_favorited = filters.BooleanFilter(
        method='filter_is_favorited'
    )
    is_in_shopping_cart = filters.BooleanFilter(
        method='filter_is_in_shopping_cart'
    )

    class Meta:
        model = Recipe
        fields = ['author', 'tags', 'is_favorited', 'is_in_shopping_cart']

    def filter_is_favorited(self, queryset, name, value):
        user = self.request.user
        if value:
            if user.is_anonymous:
                return queryset.none()
            return queryset.filter(favorited_by__user=user)
        return queryset

    def filter_is_in_shopping_cart(self, queryset, name, value):
        user = self.request.user
        if value:
            if user.is_anonymous:
                return queryset.none()
            return queryset.filter(in_shopping_cart__user=user)
        return queryset


class LimitFilter(filters.FilterSet):
    """Фильтр для ограничения количества объектов в результате запроса."""

    limit = filters.NumberFilter(method="filter_limit")

    class Meta:
        model = User
        fields = ("limit",)

    def filter_limit(self, authors, name, value):
        return authors[:int(value)] if value else authors


class NameFilter(filters.FilterSet):
    """Фильтр для поиска ингредиентов по имени."""

    name = filters.CharFilter(
        field_name="name",
        lookup_expr="startswith"
    )

    class Meta:
        model = Ingredient
        fields = ("name",)
