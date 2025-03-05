from datetime import date
import hashids

from django.db.models import Sum
from django.conf import settings
from django.shortcuts import redirect
from django.http import FileResponse, HttpResponse, HttpResponseNotFound
from django.utils.formats import date_format
from django_filters.rest_framework import DjangoFilterBackend
from djoser.views import UserViewSet
from recipes.models import (
    Favorite, Follow, Ingredient, Recipe, ShoppingCart, Tag
)
from rest_framework import serializers, status
from rest_framework.decorators import action
from rest_framework.permissions import (
    IsAuthenticated, IsAuthenticatedOrReadOnly
)
from rest_framework.response import Response
from rest_framework.viewsets import ModelViewSet, ReadOnlyModelViewSet

from .filters import LimitFilter, NameFilter, RecipeFilter
from .pagination import CustomPagination
from .permissions import IsAuthorOrReadOnly
from .serializers import (
    FollowSerializer,
    IngredientSerializer,
    RecipeCreateSerializer,
    RecipeListSerializer,
    RecipeSerializer,
    TagSerializer,
    UserAvatarSerializer,
)

from .utils import generate_shopping_list
from . import constants


class IngredientViewSet(ReadOnlyModelViewSet):
    """Представление для модели Ingredient."""

    queryset = Ingredient.objects.all()
    serializer_class = IngredientSerializer
    filter_backends = (DjangoFilterBackend,)
    filterset_class = NameFilter
    pagination_class = None


class TagViewSet(ReadOnlyModelViewSet):
    """Представление для модели Tag."""

    queryset = Tag.objects.all()
    serializer_class = TagSerializer
    pagination_class = None


class RecipeViewSet(ModelViewSet):
    """Представление для модели Recipe."""

    queryset = Recipe.objects.all()
    permission_classes = IsAuthenticatedOrReadOnly, IsAuthorOrReadOnly
    filter_backends = (DjangoFilterBackend,)
    filterset_class = RecipeFilter
    http_method_names = (
        "get", "post", "patch", "delete", "head", "options", "trace"
    )
    pagination = CustomPagination

    def get_serializer_class(self):
        if self.action in ["list", "retrieve"]:
            return RecipeSerializer
        return RecipeCreateSerializer

    def perform_create(self, serializer):
        serializer.save(author=self.request.user)

    def _handle_recipe_list_item(self, request, model):
        recipe = self.get_object()
        if request.method == "DELETE":
            try:
                model.objects.get(user=request.user, recipe=recipe).delete()
                return Response(status=status.HTTP_204_NO_CONTENT)
            except model.DoesNotExist:
                return Response(
                    {"error": constants.RECIPE_NOT_IN_FAVORITE},
                    status=status.HTTP_400_BAD_REQUEST,
                )

        _, created = model.objects.get_or_create(
            user=request.user, recipe=recipe
        )
        if not created:
            raise serializers.ValidationError(
                {"error": f"Рецепт '{recipe}' уже добавлен в список любимых"}
            )

        return Response(
            RecipeListSerializer(recipe).data, status=status.HTTP_201_CREATED
        )

    @action(
        ["post", "delete"],
        detail=True,
        url_path="favorite",
        permission_classes=[IsAuthenticated],
    )
    def favorite(self, request, pk):
        return self._handle_recipe_list_item(request, Favorite)

    @action(
        ["post", "delete"],
        detail=True,
        url_path="shopping_cart",
        permission_classes=[IsAuthenticated],
    )
    def shopping_cart(self, request, pk):
        return self._handle_recipe_list_item(request, ShoppingCart)

    @action(
        detail=True,
        methods=['get'],
        url_path='get-link'
    )
    def get_link(self, request, pk=None):
        recipe = self.get_object()
        hashid = hashids.Hashids(salt='random_salt', min_length=8)
        short_id = hashid.encode(recipe.id)
        short_link = f'{settings.BASE_URL}/s/{short_id}'
        return Response({'short-link': short_link})


def redirect_to_recipe(request, short_id):
    hashid = hashids.Hashids(salt='random_salt', min_length=8)
    decoded_id = hashid.decode(short_id)

    if decoded_id:
        recipe_id = decoded_id[0]
        return redirect(f'/recipes/{recipe_id}/')

    return HttpResponseNotFound('Рецепт не найден')


class FoodgramUserViewSet(UserViewSet):
    """Представление для модели User."""

    filter_backends = (DjangoFilterBackend,)
    filterset_class = LimitFilter

    def get_permissions(self):
        if self.action == "me":
            return (IsAuthenticated(),)
        return super().get_permissions()

    @action(["put", "delete"], detail=False, url_path="me/avatar")
    def me_avatar(self, request):
        user = request.user
        if request.method == "DELETE":
            user.avatar.delete()
            return Response(status=status.HTTP_204_NO_CONTENT)
        serializer = UserAvatarSerializer(user, data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data, status=status.HTTP_200_OK)

    @action(
        ["get"],
        detail=False,
        url_path="subscriptions",
        permission_classes=[IsAuthenticated],
    )
    def subscriptions(self, request):
        subscribe_data = FollowSerializer(
            self.filter_queryset(
                self.get_queryset().filter(authors__user=request.user)
            ),
            context={"request": request},
            many=True,
        ).data
        return self.get_paginated_response(
            self.paginate_queryset(subscribe_data)
        )

    @action(
        ["post", "delete"],
        detail=True,
        url_path="subscribe",
        permission_classes=[IsAuthenticated],
    )
    def create_delete_subscribe(self, request, id=None):
        author = self.get_object()
        model = Follow
        if request.method == "DELETE":
            try:
                model.objects.get(
                    user=request.user, subscribing=author
                ).delete()
                return Response(status=status.HTTP_204_NO_CONTENT)
            except model.DoesNotExist:
                return Response(
                    {"error": "Вы не подписаны"},
                    status=status.HTTP_400_BAD_REQUEST
                )

        if request.user == author:
            raise serializers.ValidationError(constants.SELF_SUBSCRIBE_ERROR)
        _, created = Follow.objects.get_or_create(
            user=request.user, subscribing=author
        )
        if not created:
            raise serializers.ValidationError(
                {"subscribe": constants.ALREADY_SUBSCRIBED_ERROR.format(
                    author)}
            )
        return Response(
            FollowSerializer(author, context={"request": request}).data,
            status=status.HTTP_201_CREATED,
        )
    @action(
        ["get"],
        detail=False,
        url_path="download_shopping_cart",
        permission_classes=[IsAuthenticated],
    )
    def download_shopping_cart(self, request):
        recipes = Recipe.objects.filter(shoppingcarts__user=request.user)
        ingredients = (
            Ingredient.objects.filter(recipes__in=recipes)
            .annotate(total_amount=Sum("recipe_ingredients__amount"))
            .order_by("name")
        )
        return FileResponse(
            generate_shopping_list(request.user, recipes, ingredients),
            content_type="text/plain; charset=utf-8",
            as_attachment=True,
            filename=constants.FILENAME.format(
                date_format(date.today(), constants.DATE_FORMAT_SHORT)
            ),
        )