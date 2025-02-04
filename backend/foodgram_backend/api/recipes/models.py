from django.contrib.auth import get_user_model
from django.db import models

User = get_user_model()

MAX_TEXT_LENGTH: int = 256
MAX_SLUG_LNGTH: int = 50


class Recipe(models.Model):
    """Модель для представления рецептов."""

    author = models.ForeignKey(User, on_delete=models.CASCADE, verbose_name="Автор публикации", null=True)
    name = models.CharField(max_length=MAX_TEXT_LENGTH, verbose_name="Название рецепта")
    image = models.ImageField(upload_to='recipes/', verbose_name="Картинка", blank=True)
    description = models.TextField(verbose_name="Текстовое описание")
    ingredients = models.ManyToManyField('ingredient', through='RecipeIngredient', verbose_name="Ингредиенты")
    tags = models.ManyToManyField('Tag', verbose_name="Теги", blank=True)
    cooking_time = models.PositiveIntegerField(verbose_name="Время приготовления (в минутах)")

    class Meta:
        ordering = ("name",)
        verbose_name = "Рецепт"
        verbose_name_plural = "Рецепты"

    def __str__(self):
        return self.name


class Tag(models.Model):
    """Модель для представления тегов."""

    name = models.CharField(max_length=MAX_TEXT_LENGTH, verbose_name="Тег", unique=True)
    slug = models.SlugField(
        max_length=MAX_SLUG_LNGTH,
        unique=True,
        db_index=True,
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

    name = models.CharField(max_length=MAX_TEXT_LENGTH, verbose_name="Ингредиент", unique=True)
    slug = models.SlugField(
        max_length=MAX_SLUG_LNGTH,
        unique=True,
        db_index=True,
        verbose_name="Slug ингредиента",
    )
    measure = models.CharField(max_length=50, verbose_name="Единица измерения")

    class Meta:
        ordering = ("name",)
        verbose_name = "Ингредиент"
        verbose_name_plural = "Ингредиенты"

    def __str__(self):
        return self.name


class RecipeIngredient(models.Model):
    """Промежуточная модель для связи рецептов и ингредиентов."""

    recipe = models.ForeignKey(Recipe, on_delete=models.CASCADE)
    ingredient = models.ForeignKey(Ingredient, on_delete=models.CASCADE)
    quantity = models.PositiveIntegerField(verbose_name="Количество")

    class Meta:
        unique_together = ('recipe', 'ingredient')
    
    def __str__(self):
        return f"{self.quantity} {self.ingredient.measure} of {self.ingredient.name} in {self.recipe.name}"
