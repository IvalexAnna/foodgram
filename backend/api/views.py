from django.db.models import Avg
from rest_framework import viewsets, permissions, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.views import APIView
from django.http import HttpResponse
import csv

from .recipes.models import Recipe, Tag, Ingredient
from .serializers import RecipeSerializer, TagSerializer, IngredientSerializer
#from django_filters.rest_framework import DjangoFilterBackend

#from rest_framework import filters, mixins
#from rest_framework.generics import get_object_or_404

from .recipes.models import Recipe, Tag, Ingredient
from .serializers import RecipeSerializer, TagSerializer, IngredientSerializer
from .pagination import CustomPagination
#from .filters import RecipeFilter

    #filter_backends = RecipeFilter
    # search_fields = ("name",)
    # filterset_fields = ["tags", "author"]



class RecipeViewSet(viewsets.ModelViewSet):
    queryset = Recipe.objects.all()
    serializer_class = RecipeSerializer
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]
    pagination_class = CustomPagination

    def perform_create(self, serializer):
        serializer.save(author=self.request.user)

    def get_queryset(self):
        queryset = super().get_queryset()
        is_favorited = self.request.query_params.get('is_favorited')
        author_id = self.request.query_params.get('author')
        tags = self.request.query_params.getlist('tags')

        if is_favorited is not None:
            queryset = queryset.filter(is_favorited=self.request.user)
        if author_id is not None:
            queryset = queryset.filter(author__id=author_id)
        if tags:
            queryset = queryset.filter(tags__slug__in=tags)

        return queryset

    @action(detail=True, methods=['post', 'delete'], permission_classes=[permissions.IsAuthenticated])
    def favorite(self, request, pk=None):
        recipe = self.get_object()
        user = request.user

        if request.method == 'POST':
            recipe.is_favorited.add(user)
            return Response({'status': 'added to favorites'}, status=status.HTTP_201_CREATED)
        elif request.method == 'DELETE':
            recipe.is_favorited.remove(user)
            return Response({'status': 'removed from favorites'}, status=status.HTTP_204_NO_CONTENT)

    @action(detail=True, methods=['post', 'delete'], permission_classes=[permissions.IsAuthenticated])
    def shopping_cart(self, request, pk=None):
        recipe = self.get_object()
        user = request.user

        if request.method == 'POST':
            recipe.shopping_cart.add(user)
            return Response({'status': 'added to shopping cart'}, status=status.HTTP_201_CREATED)
        elif request.method == 'DELETE':
            recipe.shopping_cart.remove(user)
            return Response({'status': 'removed from shopping cart'}, status=status.HTTP_204_NO_CONTENT)

    @action(detail=False, methods=['get'], permission_classes=[permissions.IsAuthenticated])
    def download_shopping_cart(self, request):
        user = request.user
        recipes = user.shopping_cart_recipes.all()

        response = HttpResponse(content_type='text/csv')
        response['Content-Disposition'] = 'attachment; filename="shopping_cart.csv"'

        writer = csv.writer(response)
        writer.writerow(['Ingredient', 'Amount', 'Measurement Unit'])

        ingredients = {}
        for recipe in recipes:
            for item in recipe.ingredientsinrecipe_set.all():
                ingredient_name = item.ingredient.name
                if ingredient_name in ingredients:
                    ingredients[ingredient_name]['amount'] += item.amount
                else:
                    ingredients[ingredient_name] = {
                        'amount': item.amount,
                        'measurement_unit': item.ingredient.measurement_unit,
                    }

        for ingredient, data in ingredients.items():
            writer.writerow([ingredient, data['amount'], data['measurement_unit']])

        return response

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
    pagination_class = None
    #filter_backends = (DjangoFilterBackend,)
    #filterset_class = IngredientFilter