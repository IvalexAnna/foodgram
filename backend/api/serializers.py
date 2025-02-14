import base64

from django.core.files.base import ContentFile
from rest_framework import serializers
from .recipes.models import Recipe, Tag, Ingredient, RecipeIngredient

from users.models import FoodgramUser
from users.serializers import CustomUserSerializer
from django.core.exceptions import ObjectDoesNotExist


class Base64ImageField(serializers.ImageField):
    """Кастомное поле для кодирования изображения в base64."""

    def to_internal_value(self, data):
        """Метод преобразования картинки"""

        if isinstance(data, str) and data.startswith("data:image"):
            format, imgstr = data.split(";base64,")
            ext = format.split("/")[-1]
            data = ContentFile(base64.b64decode(imgstr), name="photo." + ext)

        return super().to_internal_value(data)


class IngredientSerializer(serializers.ModelSerializer):
    """Сериализатор для модели Ingredient."""

    class Meta:
        model = Ingredient
        fields = ("id", "name", "measurement_unit")
        read_only_fields = ["id"]


class RecipeIngredientSerializer(serializers.Serializer):
    id = serializers.IntegerField(min_value=1, required=False, allow_null=True)
    amount = serializers.IntegerField(min_value=1, required=True)

    def validate_id(self, value):
        if value is not None:
            try:
                Ingredient.objects.get(pk=value)
            except ObjectDoesNotExist:
                raise serializers.ValidationError(
                    "Ingredient with this ID does not exist."
                )
        return value


class TagSerializer(serializers.ModelSerializer):
    """Сериализатор для модели Recipes."""

    class Meta:
        model = Tag
        fields = ("id", "name", "slug")
        read_only_fields = ["id"]


class RecipeSerializer(serializers.ModelSerializer):
    """Сериализатор для модели Recipes."""

    ingredients = RecipeIngredientSerializer(many=True, required=True)
    tags = TagSerializer(many=True, read_only=True)
    author = CustomUserSerializer(read_only=True)
    is_favorited = serializers.SerializerMethodField()
    is_in_shopping_cart = serializers.SerializerMethodField()

    class Meta:
        model = Recipe
        fields = (
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
        )
        read_only_fields = ["author", "id", "is_favorited", "is_in_shopping_cart"]

    def get_is_favorited(self, obj):
        """Проверяет, добавлен ли рецепт в избранное текущим пользователем."""
        request = self.context.get("request")
        if request and request.user.is_authenticated:
            return request.user.favorites.filter(recipe=obj).exists()
        return False

    def get_is_in_shopping_cart(self, obj):
        """Проверяет, добавлен ли рецепт в список покупок текущим пользователем."""
        request = self.context.get("request")
        if request and request.user.is_authenticated:
            return request.user.shopping_cart.filter(recipe=obj).exists()
        return False

    
    def update(self, instance, validated_data):
        """Обновляет существующий рецепт."""
        ingredients_data = validated_data.pop("ingredients")
        instance.name = validated_data.get("name", instance.name)
        instance.image = validated_data.get("image", instance.image)
        instance.text = validated_data.get("text", instance.text)
        instance.cooking_time = validated_data.get(
            "cooking_time", instance.cooking_time
        )

        instance.ingredients.clear()  # Очищаем текущие ингредиенты

        for ingredient_data in ingredients_data:
            ingredient_id = ingredient_data.pop("id")  # Получаем id ингредиента
            ingredient = Ingredient.objects.get(
                pk=ingredient_id
            )  # Получаем объект ингредиента
            RecipeIngredient.objects.create(
                recipe=instance, ingredient=ingredient, **ingredient_data
            )

        tags_data = validated_data.pop("tags", [])
        instance.tags.set(tags_data)

        instance.save()
        return instance

    def validate(self, data):
        """Метод валидации ингредиентов"""

        ingredients = self.initial_data.get("ingredients")
        lst_ingredient = []

        for ingredient in ingredients:
            if ingredient["id"] in lst_ingredient:
                raise serializers.ValidationError(
                    "Ингредиенты должны быть уникальными!"
                )
            lst_ingredient.append(ingredient["id"])

        return data


class AdditionalForRecipeSerializer(serializers.ModelSerializer):
    """Дополнительный сериализатор для рецептов"""

    image = Base64ImageField()

    class Meta:
        """Мета-параметры сериализатора"""

        model = Recipe
        fields = ("id", "name", "image", "cooking_time")


class FollowSerializer(CustomUserSerializer):
    """Сериализатор для модели Follow."""

    recipes = serializers.SerializerMethodField(
        read_only=True, method_name="get_recipes"
    )
    recipes_count = serializers.SerializerMethodField(read_only=True)

    class Meta:
        """Мета-параметры сериализатора"""

        model = FoodgramUser
        fields = (
            "email",
            "id",
            "username",
            "first_name",
            "last_name",
            "is_subscribed",
            "recipes",
            "recipes_count",
        )

    def get_recipes(self, obj):
        """Метод для получения рецептов"""

        request = self.context.get("request")
        recipes = obj.recipes.all()
        recipes_limit = request.query_params.get("recipes_limit")
        if recipes_limit:
            recipes = recipes[: int(recipes_limit)]
        return AdditionalForRecipeSerializer(recipes, many=True).data

    @staticmethod
    def get_recipes_count(obj):
        """Метод для получения количества рецептов"""

        return obj.recipes.count()
