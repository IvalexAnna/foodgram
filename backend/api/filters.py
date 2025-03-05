import django_filters

from recipes.models import Ingredient, Recipe, Tag, User


class LimitFilter(django_filters.FilterSet):
    """Фильтр для ограничения количества объектов в результате запроса."""

    limit = django_filters.NumberFilter(method="filter_limit")

    class Meta:
        model = User
        fields = ("limit",)

    def filter_limit(self, authors, name, value):
        return authors[:int(value)] if value else authors


class NameFilter(django_filters.FilterSet):
    """Фильтр для поиска ингредиентов по имени."""

    name = django_filters.CharFilter(
        field_name="name",
        lookup_expr="startswith"
    )

    class Meta:
        model = Ingredient
        fields = ("name",)


class RecipeFilter(django_filters.FilterSet):
    tags = django_filters.ModelMultipleChoiceFilter(
        field_name='tags__slug',
        to_field_name='slug',
        queryset=Tag.objects.all(),
    )
    is_favorited = django_filters.NumberFilter(method='filter_is_favorited')
    is_in_shopping_cart = django_filters.NumberFilter(
        method='filter_is_in_shopping_cart'
    )

    class Meta:
        model = Recipe
        fields = ('is_favorited', 'is_in_shopping_cart', 'tags', 'author',)

    def filter_is_favorited(self, queryset, name, value):
        user = getattr(self.request, 'user', None)
        if value == 1 and user and user.is_authenticated:
            return queryset.filter(favorites__user=user)
        return queryset

    def filter_is_in_shopping_cart(self, queryset, name, value):
        user = self.request.user
        print(value)
        if value == 1 and not user.is_anonymous:
            return queryset.filter(shoppingcarts__user=user)
        return queryset