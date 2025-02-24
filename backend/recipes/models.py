from django.contrib.auth import get_user_model
from django.db import models
from django.utils.text import slugify
from django.db.models.signals import pre_save
from django.dispatch import receiver
from django.db.models import UniqueConstraint
from django.core.validators import MinValueValidator

from django.contrib.auth.models import AbstractUser
from django.db import models
from django.contrib.auth import models as auth_models, validators
from django.core.exceptions import ValidationError
from django.core.validators import MinValueValidator


MAX_LENGTH: int = 6
NAME_LENGTH: int = 150
SELF_SUBSCRIBE_ERROR: str = 'Нельзя подписаться на самого себя.'
MAX_TEXT_LENGTH: int = 256
MAX_SLUG_LNGTH: int = 50
MIN_VALUE_COOKING_TIME: int = 1
MIN_VALUE_AMOUNT: int = 1


class UserRole(models.TextChoices):
    """Класс для определения ролей пользователей."""

    USER = "user", "Пользователь"
    MODERATOR = "moderator", "Модератор"
    ADMIN = "admin", "Админ"


class FoodgramUser(AbstractUser):
    """Модель для пользователей созданная для приложения foodgram"""

    email = models.EmailField(max_length=NAME_LENGTH,
                              verbose_name="Электронная почта", unique=True, blank=False, null=False)
    username = models.CharField(
        max_length=NAME_LENGTH, unique=True,
        validators=(validators.UnicodeUsernameValidator(),),
        verbose_name='Логин'
    )
    first_name = models.CharField(max_length=NAME_LENGTH, verbose_name="Имя")
    last_name = models.CharField(
        max_length=NAME_LENGTH, verbose_name="Фамилия")
    avatar = models.ImageField(
        upload_to='avatars/', verbose_name='Аватар',
        null=True, default=''
    )
    USERNAME_FIELD = "email"
    REQUIRED_FIELDS = ["username", "first_name", "last_name"]

    def str(self):
        """Строковое представление модели"""

        return self.username

    class Meta:
        """Мета-параметры модели"""

        verbose_name = "Пользователь"
        verbose_name_plural = "Пользователи"
        ordering = 'username', 'email'


class Follow(models.Model):
    """Модель подписчика."""

    user = models.ForeignKey(
        FoodgramUser, on_delete=models.CASCADE,
        verbose_name='Пользователь',
        related_name='subscribers'
    )
    subscribing = models.ForeignKey(
        FoodgramUser, on_delete=models.CASCADE,
        verbose_name='Автор',
        related_name='authors'
    )

    class Meta:
        verbose_name = 'Подписка'
        verbose_name_plural = 'Подписки'
        constraints = [models.UniqueConstraint(
            fields=['user', 'subscribing'], name='unique_subscription'
        )]

    def __str__(self):
        return (f'{self.user.username[:21]} подписан на '
                f'{self.subscribing.username[:21]}')

    def clean(self):
        if self.user == self.subscribing:
            raise ValidationError(SELF_SUBSCRIBE_ERROR)


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


class Recipe(models.Model):
    """Модель для представления рецептов."""

    author = models.ForeignKey(FoodgramUser, on_delete=models.CASCADE,
                               verbose_name='Автор')
    name = models.CharField(max_length=256, verbose_name='Название')
    image = models.ImageField(upload_to='recipes/recipes', verbose_name='Фото')
    text = models.TextField('Описание')
    cooking_time = models.PositiveIntegerField(
        validators=[MinValueValidator(MIN_VALUE_COOKING_TIME)],
        verbose_name='Время (мин)',
    )
    pub_date = models.DateTimeField(auto_now_add=True,
                                    verbose_name='Дата публикации')
    ingredients = models.ManyToManyField(
        Ingredient,
        verbose_name='Список продуктов',
        through='RecipeIngredients',
    )
    tags = models.ManyToManyField(Tag, verbose_name='Список тэгов')

    class Meta:
        verbose_name = 'Рецепт'
        verbose_name_plural = 'Рецепты'
        default_related_name = 'recipes'
        ordering = ('-pub_date',)

    def __str__(self):
        return f'{self.author} - {self.name[:21]}'


class RecipeIngredients(models.Model):
    recipe = models.ForeignKey(
        Recipe, on_delete=models.CASCADE,
        verbose_name='Рецепт',
    )
    ingredient = models.ForeignKey(
        Ingredient, on_delete=models.CASCADE, verbose_name='Продукт'
    )
    amount = models.PositiveIntegerField(
        validators=[MinValueValidator(MIN_VALUE_AMOUNT)],
        verbose_name='Мера'
    )

    def __str__(self):
        return (f'{self.ingredient.name[:21]} - {self.amount} '
                f'{self.ingredient.measurement_unit[:21]}')

    class Meta:
        verbose_name = 'Количество продукта'
        verbose_name_plural = 'Количество продуктов'
        default_related_name = 'recipe_ingredients'


class UserRecipeBaseModel(models.Model):
    user = models.ForeignKey(
        FoodgramUser, on_delete=models.CASCADE,
        verbose_name='Пользователь',
    )
    recipe = models.ForeignKey(
        Recipe, on_delete=models.CASCADE,
        verbose_name='Рецепт',
    )

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=['user', 'recipe'],
                name='%(class)s_unique_user_recipe'
            )
        ]
        abstract = True
        default_related_name = '%(class)ss'

    def __str__(self):
        return f'У {self.user.username[:21]} в списке {self.recipe}'


class Favorite(UserRecipeBaseModel):
    class Meta(UserRecipeBaseModel.Meta):
        verbose_name = 'Избранное'
        verbose_name_plural = 'Избранное'


class ShoppingCart(UserRecipeBaseModel):
    class Meta(UserRecipeBaseModel.Meta):
        verbose_name = 'Списки покупок'
        verbose_name_plural = 'Список покупок'
