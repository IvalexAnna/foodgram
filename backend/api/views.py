from django.db.models import Avg

from django_filters.rest_framework import DjangoFilterBackend

from rest_framework import filters, mixins, viewsets
from rest_framework.generics import get_object_or_404

from .recipes.models import Recipe, Tag, Ingredient
from .permissions import IsAuthorOrReadOnly
from rest_framework import permissions
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
    permission_classes = [IsAuthorOrReadOnly]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter]
    search_fields = ("name",)
    filterset_fields = ["tags", "author"]

    def get_serializer_class(self):
        """Метод для вызова определенного сериализатора. """

        if self.action in ('list', 'retrieve'):
            return RecipeSerializer
        elif self.action in ('create', 'partial_update'):
            return CreateRecipeSerializer
        
    def perform_create(self, serializer):
        """Автоматически устанавливаем автора рецепта."""
        serializer.save(author=self.request.user)


class TagViewSet(viewsets.ModelViewSet):
    """Представление для работы с тегами."""

    queryset = Tag.objects.all()
    serializer_class = TagSerializer
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]
    pagination_class = None


class IngredientViewSet(viewsets.ModelViewSet):
    """Представление для работы с ингридиентами."""

    queryset = Ingredient.objects.all()
    serializer_class = IngredientSerializer
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]
