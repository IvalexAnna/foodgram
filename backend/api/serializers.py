import base64

from django.core.files.base import ContentFile
from rest_framework import serializers
from .recipes.models import Recipe, Tag, Ingredient, RecipeIngredient

from users.models import FoodgramUser
from users.serializers import CustomUserSerializer


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
        fields = ["id", "name", "measurement_unit"]


class RecipeIngredientSerializer(serializers.ModelSerializer):
    id = serializers.IntegerField(required=True)
    amount = serializers.IntegerField(min_value=1)

    class Meta:
        model = RecipeIngredient
        fields = ["id", "amount"]

class TagSerializer(serializers.ModelSerializer):
    """Сериализатор для модели Tag."""

    class Meta:
        model = Tag
        fields = ["id", "name", "slug"]
        read_only_fields = ["id"]


class RecipeSerializer(serializers.ModelSerializer):
    ingredients = RecipeIngredientSerializer(many=True, source='ingredient_list')
    tags = serializers.PrimaryKeyRelatedField(queryset=Tag.objects.all(), many=True, required=True)
    author = serializers.SlugRelatedField(slug_field="username", read_only=True)
    image = Base64ImageField(required=False, allow_null=True)
    is_favorited = serializers.SerializerMethodField()
    is_in_shopping_cart = serializers.SerializerMethodField()

    class Meta:
        model = Recipe
        fields = [
            "id", "author", "name", "image", "text", "ingredients", "tags",
            "cooking_time", "is_favorited", "is_in_shopping_cart"
        ]
        read_only_fields = ["author", "id"]

    def create(self, validated_data):
        ingredients_data = validated_data.pop('ingredients')
        tags_data = validated_data.pop('tags')

        recipe = Recipe.objects.create(**validated_data)

        recipe_ingredients = []
        for ingredient_data in ingredients_data:
            ingredient_id = ingredient_data["id"]
            amount = ingredient_data['amount']
            ingredient_instance = Ingredient.objects.get(id=ingredient_id)
            recipe_ingredients.append(RecipeIngredient(recipe=recipe, ingredient=ingredient_instance))

        RecipeIngredient.objects.bulk_create(recipe_ingredients)

        recipe.tags.set(tags_data)
        return recipe

    def update(self, instance, validated_data):
        ingredients_data = validated_data.pop('ingredients', None)
        tags_data = validated_data.pop('tags', None)

        if ingredients_data is not None:
            RecipeIngredient.objects.filter(recipe=instance).delete()
            for ingredient_data in ingredients_data:
                ingredient_id = ingredient_data['ingredient_id']
                amount = ingredient_data['amount']
                ingredient_instance = Ingredient.objects.get(id=ingredient_id)
                RecipeIngredient.objects.create(recipe=instance, ingredient=ingredient_instance, amount=amount)

        if tags_data is not None:
            instance.tags.set(tags_data)

        for attr, value in validated_data.items():
            setattr(instance, attr, value)

        instance.save()
        return instance


class FollowSerializer(CustomUserSerializer):
    """Сериализатор для модели Follow."""

    recipes = serializers.SerializerMethodField(
        read_only=True, method_name="get_recipes"
    )
    recipes_count = serializers.SerializerMethodField(read_only=True)

    class Meta:
        """Мета-параметры сериализатора"""

        model = FoodgramUser
        fields = [
            "email",
            "id",
            "username",
            "first_name",
            "last_name",
            "is_subscribed",
            "recipes",
            "recipes_count",
        ]

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
