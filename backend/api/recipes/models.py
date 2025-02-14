from django.contrib.auth import get_user_model
from django.db import models
from django.utils.text import slugify
from django.db.models.signals import pre_save
from django.dispatch import receiver
from users.models import FoodgramUser

User = get_user_model()

MAX_TEXT_LENGTH: int = 256
MAX_SLUG_LNGTH: int = 50


class Recipe(models.Model):
    """Модель для представления рецептов."""

    author = models.ForeignKey(
        FoodgramUser,
        on_delete=models.CASCADE,
        verbose_name="Автор публикации",
        null=True,
    )
    name = models.CharField(max_length=MAX_TEXT_LENGTH, verbose_name="Название рецепта")
    image = models.ImageField(upload_to="recipes/", verbose_name="Картинка", blank=True)
    text = models.TextField(verbose_name="Текстовое описание")
    ingredients = models.ManyToManyField(
        "Ingredient", through="RecipeIngredient", verbose_name="Ингредиенты"
    )
    tags = models.ManyToManyField("Tag", verbose_name="Теги", blank=True)
    cooking_time = models.PositiveIntegerField(
        verbose_name="Время приготовления (в минутах)"
    )

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


@receiver(pre_save, sender=Tag)
def tag_pre_save(sender, instance, *args, **kwargs):
    """Автоматически генерирует slug для тега перед сохранением."""
    if not instance.slug:
        instance.slug = slugify(instance.name)


class Ingredient(models.Model):
    """Модель для представления ингредиентов."""
    name = models.CharField(max_length=255, verbose_name="Название ингредиента")
    measurement_unit = models.CharField(max_length=50, verbose_name="Единица измерения")
    amount = models.PositiveIntegerField(default=0, verbose_name="Количество")

    class Meta:
        ordering = ("name",)
        verbose_name = "Ингредиент"
        verbose_name_plural = "Ингредиенты"

    def __str__(self):
        return f"{self.name} ({self.measurement_unit})"


class RecipeIngredient(models.Model):
    """Промежуточная модель для связи рецептов и ингредиентов."""

    recipe = models.ForeignKey(Recipe, on_delete=models.CASCADE)
    ingredient = models.ForeignKey(Ingredient, on_delete=models.CASCADE)
    amount = models.PositiveIntegerField(verbose_name="Количество")

    class Meta:
        unique_together = ("recipe", "ingredient")
        verbose_name = "Ингредиент в рецепте"
        verbose_name_plural = "Ингредиенты в рецептах"

    def __str__(self):
        return f"{self.amount} {self.ingredient.measurement_unit} of {self.ingredient.name} in {self.recipe.name}"


class UserFavorite(models.Model):
    """Промежуточная модель для избранных рецептов пользователя."""

    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="favorites")
    recipe = models.ForeignKey(
        Recipe, on_delete=models.CASCADE, related_name="favorites"
    )

    class Meta:
        unique_together = ("user", "recipe")
        verbose_name = "Избранный рецепт"
        verbose_name_plural = "Избранные рецепты"

    def __str__(self):
        return f"{self.user.username} - {self.recipe.name}"


class ShoppingCart(models.Model):
    """Промежуточная модель для списка покупок пользователя."""

    user = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name="shopping_cart"
    )
    recipe = models.ForeignKey(
        Recipe, on_delete=models.CASCADE, related_name="shopping_cart"
    )

    class Meta:
        unique_together = ("user", "recipe")
        verbose_name = "Рецепт в списке покупок"
        verbose_name_plural = "Рецепты в списке покупок"

    def __str__(self):
        return f"{self.user.username} - {self.recipe.name}"
