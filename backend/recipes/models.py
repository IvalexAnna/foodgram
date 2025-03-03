import random
import string
from django.contrib.auth import get_user_model, validators
from django.contrib.auth.models import AbstractUser
from django.core.exceptions import ValidationError
from django.core.validators import MinValueValidator
from django.db import models

from api import constants


class FoodgramUser(AbstractUser):
    """Модель для пользователей созданная для приложения foodgram"""

    email = models.EmailField(
        max_length=constants.NAME_LENGTH,
        verbose_name="Электронная почта",
        unique=True,
        null=False,
    )
    username = models.CharField(
        max_length=constants.NAME_LENGTH,
        unique=True,
        validators=(validators.UnicodeUsernameValidator(),),
        verbose_name="Логин",
    )
    first_name = models.CharField(
        max_length=constants.NAME_LENGTH,
        verbose_name="Имя"
    )
    last_name = models.CharField(
        max_length=constants.NAME_LENGTH, verbose_name="Фамилия"
    )
    avatar = models.ImageField(
        upload_to="avatars/", verbose_name="Аватар", null=True, default=""
    )
    USERNAME_FIELD = "email"
    REQUIRED_FIELDS = ["username", "first_name", "last_name"]

    class Meta:
        """Мета-параметры модели"""

        verbose_name = "Пользователь"
        verbose_name_plural = "Пользователи"
        ordering = "username", "email"

    def __str__(self):
        """Строковое представление модели"""

        return self.username


User = get_user_model()

class UrlData(models.Model):
    """Модель короткой ссылки."""

    original_url = models.CharField(max_length=constants.MAX_TEXT_LENGTH)
    url_slug = models.CharField(max_length=constants.LETTER_COUNT)

    def save(self, *args, **kwargs):
        if not self.url_slug:
            self.url_slug = self._generate_slug()
        super(UrlData, self).save(*args, **kwargs)

    def _generate_slug(self):
        characters = string.ascii_letters + string.digits
        while True:
            url_slug = ''.join(random.choices(
                characters, k=constants.LETTER_COUNT))
            if not UrlData.objects.filter(url_slug=url_slug).exists():
                break
        return url_slug

    def __str__(self):
        return f"Короткая ссылка для: {self.original_url} -> {self.url_slug}"


class Follow(models.Model):
    """Модель подписчика."""

    user = models.ForeignKey(
        FoodgramUser,
        on_delete=models.CASCADE,
        verbose_name="Пользователь",
        related_name="subscribers",
    )
    subscribing = models.ForeignKey(
        FoodgramUser,
        on_delete=models.CASCADE,
        verbose_name="Автор",
        related_name="authors",
    )

    class Meta:
        verbose_name = "Подписка"
        verbose_name_plural = "Подписки"
        constraints = [
            models.UniqueConstraint(
                fields=["user", "subscribing"], name="unique_subscription"
            )
        ]

    def __str__(self):
        return (
            f"{self.user.username[:constants.LETTER_COUNT]} подписан на "
            f"{self.subscribing.username[:constants.LETTER_COUNT]}"
        )

    def clean(self):
        if self.user == self.subscribing:
            raise ValidationError(constants.SELF_SUBSCRIBE_ERROR)


class Ingredient(models.Model):
    """Модель ингредиентов."""

    name = models.CharField(
        max_length=constants.MAX_TEXT_LENGTH,
        verbose_name="Название ингредиента"
    )
    measurement_unit = models.CharField(
        max_length=constants.MAX_SLUG_LNGTH, verbose_name="Единица измерения"
    )

    class Meta:
        ordering = ("name",)
        verbose_name = "Ингредиент"
        verbose_name_plural = "Ингредиенты"
        constraints = [
            models.UniqueConstraint(
                fields=["name", "measurement_unit"], name="unique_ingredient"
            )
        ]

    def __str__(self):
        return f"{self.name} ({self.measurement_unit})"


class Tag(models.Model):
    """Модель тегов."""

    name = models.CharField(
        max_length=constants.MAX_TEXT_LENGTH, verbose_name="Тег", unique=True
    )
    slug = models.SlugField(
        max_length=constants.MAX_SLUG_LNGTH,
        unique=True,
        verbose_name="Slug тега",
    )

    class Meta:
        ordering = ("name",)
        verbose_name = "Тег"
        verbose_name_plural = "Теги"

    def __str__(self):
        return self.name


class Recipe(models.Model):
    """Модель рецептов."""

    author = models.ForeignKey(
        FoodgramUser, on_delete=models.CASCADE, verbose_name="Автор"
    )
    name = models.CharField(max_length=constants.NAME_LENGTH,
                            verbose_name="Название")
    image = models.ImageField(upload_to="recipes/recipes", verbose_name="Фото")
    text = models.TextField("Описание")
    cooking_time = models.PositiveIntegerField(
        validators=[MinValueValidator(constants.MIN_VALUE_COOKING_TIME)],
        verbose_name="Время (мин)",
    )
    pub_date = models.DateTimeField(auto_now_add=True,
                                    verbose_name="Дата публикации")
    ingredients = models.ManyToManyField(
        Ingredient, verbose_name="Список продуктов",
        through="RecipeIngredients"
    )
    tags = models.ManyToManyField(Tag, verbose_name="Список тэгов")

    class Meta:
        verbose_name = "Рецепт"
        verbose_name_plural = "Рецепты"
        default_related_name = "recipes"
        ordering = ("-pub_date",)

    def __str__(self):
        return f"{self.author} - {self.name[:constants.LETTER_COUNT]}"


class RecipeIngredients(models.Model):
    """Модель для информации о количестве ингредиентов в рецепте."""

    recipe = models.ForeignKey(
        Recipe,
        on_delete=models.CASCADE,
        verbose_name="Рецепт",
    )
    ingredient = models.ForeignKey(
        Ingredient, on_delete=models.CASCADE, verbose_name="Продукт"
    )
    amount = models.PositiveIntegerField(
        validators=[MinValueValidator(constants.MIN_VALUE_AMOUNT)],
        verbose_name="Мера"
    )

    def __str__(self):
        return (
            f"{self.ingredient.name[:constants.LETTER_COUNT]} - {self.amount} "
            f"{self.ingredient.measurement_unit[:constants.LETTER_COUNT]}"
        )

    class Meta:
        verbose_name = "Количество продукта"
        verbose_name_plural = "Количество продуктов"
        default_related_name = "recipe_ingredients"


class UserRecipeBaseModel(models.Model):
    """Модель для связей между пользователями и рецептами."""

    user = models.ForeignKey(
        FoodgramUser,
        on_delete=models.CASCADE,
        verbose_name="Пользователь",
    )
    recipe = models.ForeignKey(
        Recipe,
        on_delete=models.CASCADE,
        verbose_name="Рецепт",
    )

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["user", "recipe"], name="%(class)s_unique_user_recipe"
            )
        ]
        abstract = True
        default_related_name = "%(class)ss"

    def __str__(self):
        return f"У {self.user.username[:constants.LETTER_COUNT]} в списке {self.recipe}"


class Favorite(UserRecipeBaseModel):
    """Модель избранного"""

    class Meta(UserRecipeBaseModel.Meta):
        verbose_name = "Избранное"
        verbose_name_plural = "Избранное"


class ShoppingCart(UserRecipeBaseModel):
    """Модель списка покупок"""

    class Meta(UserRecipeBaseModel.Meta):
        verbose_name = "Списки покупок"
        verbose_name_plural = "Список покупок"
