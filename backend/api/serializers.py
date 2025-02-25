from api.fields import Base64ImageField
from django.contrib.auth import get_user_model
from django.db import transaction
from djoser.serializers import UserSerializer as DjoserUserSerializer
from recipes.models import Follow, Ingredient, Recipe, RecipeIngredients, Tag
from rest_framework import serializers

from .constants import (
    ITEMS_NOT_REPEAT,
    MIN_VALUE_AMOUNT,
    MIN_VALUE_COOKING_TIME,
    NOT_EMPTY_FIELD,
    REQUIRED_FIELD,
)

User = get_user_model()


class IngredientSerializer(serializers.ModelSerializer):
    """Сериализатор для модели Ingredient."""

    class Meta:
        model = Ingredient
        fields = "__all__"


class RecipeIngredientCreateSerializer(serializers.Serializer):
    """Сериализатор для создания ингредиентов в рецепте."""

    id = serializers.PrimaryKeyRelatedField(
        queryset=Ingredient.objects.all(), source="ingredient"
    )
    amount = serializers.IntegerField(min_value=MIN_VALUE_AMOUNT)


class TagSerializer(serializers.ModelSerializer):
    """Сериализатор для модели Tag."""

    class Meta:
        model = Tag
        fields = "__all__"


class CustomUserSerializer(DjoserUserSerializer):
    """Сериализатор для модели User."""

    is_subscribed = serializers.SerializerMethodField()

    class Meta(DjoserUserSerializer.Meta):
        fields = (*DjoserUserSerializer.Meta.fields, "avatar", "is_subscribed")

    def get_is_subscribed(self, subscribing):
        request = self.context.get("request")
        return (
            request
            and request.user.is_authenticated
            and Follow.objects.filter(
                user=request.user, subscribing=subscribing
            ).exists()
        )


class UserAvatarSerializer(serializers.ModelSerializer):
    """Сериализатор для обновления аватара пользователя."""

    avatar = Base64ImageField(required=True)

    class Meta:
        model = User
        fields = ("avatar",)


class RecipeIngredientSerializer(serializers.ModelSerializer):
    """Сериализатор для модели RecipeIngredients."""

    id = serializers.IntegerField(source="ingredient.id", read_only=True)
    name = serializers.CharField(source="ingredient.name", read_only=True)
    measurement_unit = serializers.CharField(
        source="ingredient.measurement_unit", read_only=True
    )

    class Meta:
        model = RecipeIngredients
        fields = ["id", "name", "measurement_unit", "amount"]
        read_only_fields = [
            "amount",
        ]


class RecipeSerializer(serializers.ModelSerializer):
    """Сериализатор для модели Recipe."""

    ingredients = RecipeIngredientSerializer(
        many=True, read_only=True, source="recipe_ingredients"
    )
    tags = TagSerializer(many=True, read_only=True)
    author = CustomUserSerializer(read_only=True)
    is_favorited = serializers.SerializerMethodField(read_only=True)
    is_in_shopping_cart = serializers.SerializerMethodField(read_only=True)

    class Meta:
        model = Recipe
        fields = [
            "id",
            "author",
            "name",
            "image",
            "text",
            "ingredients",
            "tags",
            "cooking_time",
            "is_favorited",
            "is_in_shopping_cart",
        ]

    def _get_is_related(self, recipe, related_name):
        request = self.context.get("request")
        return (
            request
            and request.user.is_authenticated
            and (getattr
                 (recipe, related_name).filter(user=request.user).exists())
        )

    def get_is_favorited(self, recipe):
        return self._get_is_related(recipe, "favorites")

    def get_is_in_shopping_cart(self, recipe):
        return self._get_is_related(recipe, "shoppingcarts")


class RecipeCreateSerializer(serializers.ModelSerializer):
    """Сериализатор для создания и обновления рецептов."""

    ingredients = RecipeIngredientCreateSerializer(many=True, required=True)
    image = Base64ImageField(required=False)
    cooking_time = serializers.IntegerField(min_value=MIN_VALUE_COOKING_TIME)

    class Meta:
        model = Recipe
        fields = "name", "text", "cooking_time", "tags", "ingredients", "image"

    def validate(self, data):
        for field in ["image", "ingredients", "tags"]:
            if not data.get(field):
                if field == "image" and self.instance:
                    continue
                raise serializers.ValidationError({field: REQUIRED_FIELD})
        if not data.get("image", True):
            raise serializers.ValidationError({"image": NOT_EMPTY_FIELD})
        return data

    def _validate_unique(self, items):
        duplicates = [item for item in items if items.count(item) > 1]
        if duplicates:
            raise serializers.ValidationError(
                ITEMS_NOT_REPEAT.format(duplicates)
            )

    def validate_ingredients(self, recipe_ingredient_data):
        self._validate_unique(
            [
                ingredient_data["ingredient"]
                for ingredient_data in recipe_ingredient_data
            ]
        )
        return recipe_ingredient_data

    def validate_tags(self, tags):
        self._validate_unique(tags)
        return tags

    @transaction.atomic
    def _set_recipe_ingredients_and_tags(
        self, recipe, recipe_ingredient_data, tag_data
    ):
        recipe.tags.set(tag_data)
        RecipeIngredients.objects.bulk_create(
            RecipeIngredients(
                recipe=recipe,
                ingredient=ingredient_data["ingredient"],
                amount=ingredient_data["amount"],
            )
            for ingredient_data in recipe_ingredient_data
        )
        return recipe

    def create(self, recipe_data):
        recipe_ingredient_data = recipe_data.pop("ingredients")
        tag_data = recipe_data.pop("tags")
        return self._set_recipe_ingredients_and_tags(
            recipe=super().create(recipe_data),
            recipe_ingredient_data=recipe_ingredient_data,
            tag_data=tag_data,
        )

    def update(self, old_recipe, new_recipe_data):
        recipe_ingredient_data = new_recipe_data.pop("ingredients")
        tag_data = new_recipe_data.pop("tags")
        old_recipe.ingredients.clear()
        self._set_recipe_ingredients_and_tags(
            recipe=old_recipe,
            recipe_ingredient_data=recipe_ingredient_data,
            tag_data=tag_data,
        )
        return super().update(old_recipe, new_recipe_data)

    def to_representation(self, recipe):
        return RecipeSerializer(recipe, context=self.context).data


class RecipeListSerializer(serializers.ModelSerializer):
    """Сериализатор для отображения краткой информации о рецепте."""

    class Meta:
        model = Recipe
        fields = "id", "name", "image", "cooking_time"
        read_only_fields = fields


class FollowSerializer(CustomUserSerializer):
    """Сериализатор для модели Follow."""

    recipes = serializers.SerializerMethodField()
    recipes_count = serializers.IntegerField(source="recipes.count")

    class Meta(CustomUserSerializer.Meta):
        fields = (
            *CustomUserSerializer.Meta.fields, "recipes", "recipes_count"
        )
        read_only_fields = fields

    def get_recipes(self, author):
        return RecipeListSerializer(
            author.recipes.all()[
                : int(self.context.get(
                    "request").GET.get("recipes_limit", 10**10)
                )
            ],
            many=True,
            read_only=True,
        ).data
