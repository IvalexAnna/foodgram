from django.contrib.auth import get_user_model
from django.db import models
from django.utils.text import slugify
from django.db.models.signals import pre_save
from django.dispatch import receiver
from users.models import FoodgramUser
from django.db.models import UniqueConstraint
from django.core.validators import MinValueValidator

User = get_user_model()

MAX_TEXT_LENGTH: int = 256
MAX_SLUG_LNGTH: int = 50


class Recipe(models.Model):
    """Модель для представления рецептов."""

    author = models.ForeignKey(
        FoodgramUser,
        related_name='recipes',
        on_delete=models.CASCADE,
        verbose_name="Автор публикации"
    )
    name = models.CharField(max_length=MAX_TEXT_LENGTH,
                            verbose_name="Название рецепта", db_index=True)
    image = models.ImageField(upload_to="recipes/",
                              verbose_name="Картинка", blank=True)
    text = models.TextField(verbose_name="Текстовое описание")
    ingredients = models.ManyToManyField(
        "Ingredient",
        related_name='recipes',
        verbose_name="Ингредиенты",
        through='RecipeIngredient',
    )
    tags = models.ManyToManyField(
        "Tag", verbose_name='Теги')
    cooking_time = models.PositiveIntegerField(
        verbose_name="Время приготовления (в минутах)"
    )
    
    class Meta:
        verbose_name = "Рецепт"
        verbose_name_plural = "Рецепты"
        default_related_name = 'recipes'
        ordering = ('name',)

    def __str__(self):
        return self.name


class Tag(models.Model):
    """Модель для представления тегов."""

    name = models.CharField(max_length=MAX_TEXT_LENGTH,
                            verbose_name="Тег", unique=True)
    slug = models.SlugField(
        max_length=MAX_SLUG_LNGTH,
        unique=True,
        verbose_name="Slug тега",
    )

    class Meta:
        ordering = ("name",)
        verbose_name = "Тег"
        verbose_name_plural = "Теги"

    def __str__(self):
        return self.name


class Ingredient(models.Model):
    """Модель для представления ингредиентов."""

    name = models.CharField(max_length=MAX_TEXT_LENGTH,
                            verbose_name="Название ингредиента")
    measurement_unit = models.CharField(
        max_length=MAX_SLUG_LNGTH, verbose_name="Единица измерения")

    class Meta:
        ordering = ("name",)
        verbose_name = "Ингредиент"
        verbose_name_plural = "Ингредиенты"
        constraints = [
            models.UniqueConstraint(
                fields=['name', 'measurement_unit'],
                name='unique_ingredient'
            )
        ]
    def __str__(self):
        return f"{self.name} ({self.measurement_unit})"


class RecipeIngredient(models.Model):
    """Промежуточная модель для связи рецептов и ингредиентов."""

    recipe = models.ForeignKey(Recipe, on_delete=models.CASCADE, verbose_name='Рецепт',)
    ingredient = models.ForeignKey(
        Ingredient,
        on_delete=models.CASCADE,
        related_name='ingredient_list',
        verbose_name='Ингредиенты в рецепте',
    )
    amount = models.PositiveIntegerField(
        default=1,
        validators=[
            MinValueValidator(1, 'Минимальное значение - 1')
        ],
        verbose_name='Количество ингредиента'
    )

    class Meta:
        default_related_name = 'ingridients_recipe'
        verbose_name = 'Ингредиент в рецепте'
        verbose_name_plural = 'Ингредиенты в рецепте'

    def __str__(self):
        return f'{self.ingredient} – {self.amount}'



class Favorite(models.Model):
    """Модель избранного."""
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='favorites',
        verbose_name='Пользователь',
    )
    recipe = models.ForeignKey(
        Recipe,
        on_delete=models.CASCADE,
        related_name='favorites',
        verbose_name='Рецепт',
    )

    class Meta:
        ordering = ('user',)
        verbose_name = 'Избранный рецепт'
        verbose_name_plural = 'Избранное'
        constraints = [
            UniqueConstraint(
                fields=('user', 'recipe'),
                name='unique_favourites',
            )
        ]

    def __str__(self):
        return f'{self.user} добавил "{self.recipe}" в Избранное'


class ShoppingCart(models.Model):
    """Модель корзины"""
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='shopping_cart',
        verbose_name='Пользователь',
    )
    recipe = models.ForeignKey(
        Recipe,
        on_delete=models.CASCADE,
        related_name='shopping_cart',
        verbose_name='Рецепт',
    )

    class Meta:
        verbose_name = 'Корзина покупок'
        verbose_name_plural = 'Корзина покупок'
        constraints = [
            UniqueConstraint(
                fields=('user', 'recipe'),
                name='unique_shopping_cart'
            )
        ]

    def __str__(self):
        return f'{self.user} добавил "{self.recipe}" в свою корзину'
