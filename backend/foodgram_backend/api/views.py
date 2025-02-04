from django.db.models import Avg

from django_filters.rest_framework import DjangoFilterBackend

from rest_framework import filters, mixins, viewsets
from rest_framework.generics import get_object_or_404

from .recipes.models import Recipe, Tag, Ingredient
from .permissions import IsAuthorOrReadOnly
from .serializers import RecipeSerializer, TagSerializer, IngredientSerializer


class CreateListDestroyViewSet(
    mixins.CreateModelMixin,
    mixins.ListModelMixin,
    mixins.DestroyModelMixin,
    viewsets.GenericViewSet,
):
    """
    Базовый класс для представлений, поддерживающий создание,
    получение списка и удаление объектов.

    """

    pass


class RecipeViewSet(CreateListDestroyViewSet):
    """Представление для работы с категориями."""

    queryset = Recipe.objects.all()
    serializer_class = RecipeSerializer
    permission_classes = (IsAuthorOrReadOnly,)
    # filter_backends = (filters.SearchFilter,) фильтр по ингридиентам
    search_fields = ("name",)
    lookup_field = "slug"  # определить слаг

    def perform_create(self, serializer):
        serializer.save(author=self.request.user)


class TagViewSet(viewsets.ModelViewSet):
    """Представление для работы с тегами."""

    queryset = Tag.objects.all()
    serializer_class = TagSerializer
    pagination_class = None


class IngredientViewSet(viewsets.ModelViewSet):
    """Представление для работы с ингридиентами."""

    queryset = Ingredient.objects.all()
    serializer_class = IngredientSerializer
    permission_classes = (IsAuthorOrReadOnly,)  # хз
