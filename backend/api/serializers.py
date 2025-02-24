
from django.shortcuts import get_object_or_404
from rest_framework import status
from django.db import transaction
from rest_framework import serializers
from .recipes.models import Recipe, Tag, Ingredient, RecipeIngredient, ShoppingCart, Favorite
from rest_framework.exceptions import ValidationError
from users.models import FoodgramUser, Follow
from users.serializers import CustomUserSerializer
from rest_framework.relations import PrimaryKeyRelatedField
from rest_framework.fields import IntegerField, SerializerMethodField
from rest_framework.serializers import ModelSerializer, ReadOnlyField
from .fields import Base64ImageField


class IngredientSerializer(serializers.ModelSerializer):
    """Сериализатор для модели Ingredient."""

    class Meta:
        model = Ingredient
        fields = ["id", "name", "measurement_unit"]


class RecipeIngredientCreateSerializer(serializers.ModelSerializer):
    id = IntegerField(write_only=True)
    amount = IntegerField(required=True)
    name = SerializerMethodField()
    measurement_unit = SerializerMethodField()

    class Meta:
        model = RecipeIngredient
        fields = ['id', 'amount', 'name', 'measurement_unit']

    def get_measurement_unit(self, ingredient):
        measurement_unit = ingredient.ingredient.measurement_unit
        return measurement_unit

    def get_name(self, ingredient):
        name = ingredient.ingredient.name
        return name


class TagSerializer(serializers.ModelSerializer):
    """Сериализатор для модели Tag."""

    class Meta:
        model = Tag
        fields = ["id", "name", "slug"]
        read_only_fields = ["id"]


class RecipeIngredientSerializer(ModelSerializer):
    id = serializers.IntegerField(source="ingredient.id", read_only=True)
    name = serializers.CharField(source="ingredient.name")
    measurement_unit = serializers.CharField(
        source="ingredient.measurement_unit")

    class Meta:
        model = RecipeIngredient
        fields = ["id", "name", "measurement_unit", "amount"]
        read_only_fields = ['amount']


class RecipeSerializer(ModelSerializer):
    ingredients = RecipeIngredientSerializer(
        many=True, read_only=True, source='recipe_ingredients'
    )
    tags = TagSerializer(many=True, read_only=True)
    author = CustomUserSerializer(read_only=True)
    image = Base64ImageField(required=False, allow_null=True)
    is_favorited = SerializerMethodField(read_only=True)
    is_in_shopping_cart = SerializerMethodField(read_only=True)

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

    def get_is_favorited(self, obj):
        request = self.context.get("request")
        if request and request.user.is_authenticated:
            return Favorite.objects.filter(user=request.user,
                                           recipe=obj).exists()
        return False

    def get_is_in_shopping_cart(self, obj):
        request = self.context.get("request")
        if request and request.user.is_authenticated:
            return ShoppingCart.objects.filter(user=request.user,
                                               recipe=obj).exists()
        return False


class RecipeCreateSerializer(ModelSerializer):
    # tags = PrimaryKeyRelatedField(queryset=Tag.objects.all(), many=True)
    # author = CustomUserSerializer(read_only=True)
    ingredients = RecipeIngredientCreateSerializer(many=True)
    image = Base64ImageField(required=False)
    cooking_time = serializers.IntegerField(min_value=1)

    class Meta:
        model = Recipe
        fields = 'name', 'text', 'cooking_time', 'tags', 'ingredients', 'image'

    def validate(self, data):
        for field in ['image', 'ingredients', 'tags']:
            if not data.get(field):
                if field == 'image' and self.instance:
                    continue
                raise serializers.ValidationError('Обязательное поле.')
        if not data.get('image', True):
            raise serializers.ValidationError('Поле не должно быть пустым')
        return data

    def _validate_unique(self, items):
        duplicates = [item for item in items if items.count(item) > 1]
        if duplicates:
            raise serializers.ValidationError(
                'Объекты не должны повторяться: {}'.format(duplicates)
            )

    def validate_ingredients(self, recipe_ingredient_data):
        self._validate_unique([
            ingredient_data['ingredient'] for ingredient_data
            in recipe_ingredient_data
        ])
        return recipe_ingredient_data

    def validate_tags(self, tags):
        self._validate_unique(tags)
        return tags

    @transaction.atomic
    def _set_recipe_ingredients_and_tags(
        self, recipe, recipe_ingredient_data, tag_data
    ):
        recipe.tags.set(tag_data)
        RecipeIngredient.objects.bulk_create(
            RecipeIngredient(
                recipe=recipe,
                ingredient=ingredient_data['ingredient'],
                amount=ingredient_data['amount']
            ) for ingredient_data in recipe_ingredient_data)
        return recipe

    def create(self, recipe_data):
        recipe_ingredient_data = recipe_data.pop('ingredients')
        tag_data = recipe_data.pop('tags')
        return self._set_recipe_ingredients_and_tags(
            recipe=super().create(recipe_data),
            recipe_ingredient_data=recipe_ingredient_data,
            tag_data=tag_data
        )

    def update(self, old_recipe, new_recipe_data):
        recipe_ingredient_data = new_recipe_data.pop('ingredients')
        tag_data = new_recipe_data.pop('tags')
        old_recipe.ingredients.clear()
        self._set_recipe_ingredients_and_tags(
            recipe=old_recipe,
            recipe_ingredient_data=recipe_ingredient_data,
            tag_data=tag_data,
        )
        return super().update(old_recipe, new_recipe_data)

    def to_representation(self, recipe):
        return RecipeSerializer(recipe, context=self.context).data


class RecipeShortSerializer(ModelSerializer):
    image = Base64ImageField()

    class Meta:
        model = Recipe
        fields = [
            'id',
            'name',
            'image',
            'cooking_time'
        ]


class FollowSerializer(CustomUserSerializer):
    """Сериализатор для модели Follow."""

    recipes = serializers.SerializerMethodField(method_name="get_recipes")
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
        read_only_fields = ['email', 'username']

    def validate(self, data):
        author = self.instance
        user = self.context.get('request').user
        if Follow.objects.filter(author=author, user=user).exists():
            raise ValidationError(
                detail='У вас уже есть подписка на этого пользователя!',
                code=status.HTTP_400_BAD_REQUEST
            )
        if user == author:
            raise ValidationError(
                detail='Нельзя подписаться на самого себя!',
                code=status.HTTP_400_BAD_REQUEST
            )
        return data

    def get_recipes(self, obj):
        """Метод для получения рецептов"""

        request = self.context.get("request")
        recipes = obj.recipes.all()
        recipes_limit = request.query_params.get("recipes_limit")

        if recipes_limit:
            recipes = recipes[: int(recipes_limit)]
        serializer = RecipeShortSerializer(recipes, many=True, read_only=True)

        return serializer.data

    @staticmethod
    def get_recipes_count(obj):
        """Метод для получения количества рецептов"""

        return obj.recipes.count()
