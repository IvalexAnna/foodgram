from django.db.models import Avg
from rest_framework import viewsets, permissions, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.views import APIView
from django.http import HttpResponse
import csv
from django.db.models import Exists, OuterRef, Sum
from .recipes.models import Recipe, Tag, Ingredient
from .serializers import RecipeSerializer, TagSerializer, IngredientSerializer
from django_filters.rest_framework import DjangoFilterBackend
from .mixins import AddRemoveMixin
from django.http import Http404
from .filters import RecipeFilter

from .recipes.models import (
    Recipe,
    Tag,
    Ingredient,
    ShoppingCart,
    Favorite,
    RecipeIngredient,
)
from .serializers import RecipeSerializer, TagSerializer, IngredientSerializer
from .pagination import CustomPagination
from django.shortcuts import get_object_or_404, redirect


class RecipeViewSet(viewsets.ModelViewSet, AddRemoveMixin):
    queryset = Recipe.objects.all()
    serializer_class = RecipeSerializer
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]
    pagination_class = CustomPagination
    filter_backends = [DjangoFilterBackend]
    filterset_class = RecipeFilter
    search_fields = ["tags__slug"]

    def perform_create(self, serializer):
        serializer.save(author=self.request.user)

    def get_queryset(self):
        queryset = super().get_queryset()
        author_id = self.request.query_params.get("author")
        tags = self.request.query_params.getlist("tags")
        user = self.request.user
        if user.is_authenticated:
            queryset = queryset.annotate(
                is_in_shopping_cart=Exists(
                    ShoppingCart.objects.filter(user=user, recipe=OuterRef("pk"))
                )
            )
        if tags:
            queryset = queryset.filter(tags__slug__in=tags)
        if author_id:
            queryset = queryset.filter(author__id=author_id)
        return queryset.order_by("id")

    @action(detail=True, methods=["GET"], url_path="get-link")
    def get_short_link(self, request, pk=None):
        recipe = self.get_object()
        short_link = recipe.get_or_create_short_link()
        short_url = request.build_absolute_uri(f"/s/{short_link}")
        return Response({"short-link": short_url}, status=status.HTTP_200_OK)

    @action(
        detail=True,
        methods=["POST", "DELETE"],
        url_path="shopping_cart",
    )
    def shopping_cart(self, request, pk=None):
        return self.handle_add_remove(request, pk, ShoppingCart)

    @action(
        detail=False,
        methods=["GET"],
        url_path="download_shopping_cart",
    )
    def download_shopping_cart(self, request):
        user = request.user
        response = HttpResponse(content_type="text/plain")

        shopping_cart = ShoppingCart.objects.filter(user=user).values_list(
            "recipe", flat=True
        )

        ingredients_sum = (
            RecipeIngredient.objects.filter(recipe__in=shopping_cart)
            .values("ingredient__name", "ingredient__measurement_unit")
            .annotate(total_amount=Sum("amount"))
            .order_by("ingredient__name")
        )

        response.write("Список покупок:\n\n".encode("utf-8"))
        for index, item in enumerate(ingredients_sum, start=1):
            line = (
                f"{index}. {item['ingredient__name']} "
                f"({item['ingredient__measurement_unit']}) - "
                f"{item['total_amount']}\n"
            )
            response.write(line.encode("utf-8"))
        return response

    @action(
        detail=True,
        methods=["POST", "DELETE"],
        url_path="favorite",
    )
    def favorite(self, request, pk=None):
        return self.handle_add_remove(request, pk, Favorite)




class TagViewSet(viewsets.ModelViewSet):
    """Представление для работы с тегами."""

    queryset = Tag.objects.all()
    serializer_class = TagSerializer
    pagination_class = None


class IngredientViewSet(viewsets.ModelViewSet):
    """Представление для работы с ингридиентами."""

    queryset = Ingredient.objects.all()
    serializer_class = IngredientSerializer
    filter_backends = DjangoFilterBackend,
    pagination_class = None
    search_fields = ["name"]

    def get_queryset(self):
        queryset = super().get_queryset()
        name = self.request.query_params.get("name")
        if name:
            queryset = queryset.filter(name__istartswith=name)
        return queryset


def redirect_short_link(request, pk):
    if Recipe.objects.filter(pk=pk).exists():
        return redirect(f'/recipes/{pk}')
    raise Http404('Рецепт не найден.')
