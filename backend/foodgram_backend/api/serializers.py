from rest_framework import serializers
from .recipes.models import Recipe, Tag, Ingredient


class IngredientSerializer(serializers.ModelSerializer):
    """Сериализатор для модели Ingredient."""

    class Meta:
        model = Ingredient
        fields = ("id", "name", "slug", "measure")
        read_only_fields = ["id"]


class TagSerializer(serializers.ModelSerializer):
    """Сериализатор для модели Recipes."""

    class Meta:
        model = Tag
        fields = ("id", "name", "slug")
        read_only_fields = ["id"]


class RecipeSerializer(serializers.ModelSerializer):
    """Сериализатор для модели Recipes."""
    ingredients = IngredientSerializer(many=True)
    tags = TagSerializer(many=True)
    class Meta:
        model = Recipe
        fields = (
            "id",
            "author",
            "name",
            "image",
            "description",
            "ingredients",
            "tags",
            "cooking_time",
        )
        read_only_fields = ["author", "id"]






