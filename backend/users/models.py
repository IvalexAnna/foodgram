from django.contrib.auth.models import AbstractUser
from django.db import models

MAX_LENGTH: int = 6
NAME_LENGTH: int = 150


class UserRole(models.TextChoices):
    """Класс для определения ролей пользователей."""

    USER = "user", "Пользователь"
    MODERATOR = "moderator", "Модератор"
    ADMIN = "admin", "Админ"


class FoodgramUser(AbstractUser):
    """Модель для пользователей созданная для приложения foodgram"""

    email = models.EmailField(max_length=NAME_LENGTH,
                              verbose_name="Электронная почта", unique=True)
    username = models.CharField(
        max_length=NAME_LENGTH, verbose_name="Имя пользователя", unique=True, db_index=True
    )
    first_name = models.CharField(max_length=NAME_LENGTH, verbose_name="Имя")
    last_name = models.CharField(
        max_length=NAME_LENGTH, verbose_name="Фамилия")
    avatar = models.ImageField(
        upload_to='avatars/', null=True, blank=True, verbose_name="Аватар")
    USERNAME_FIELD = "email"
    REQUIRED_FIELDS = ["username", "first_name", "last_name"]

    class Meta:
        """Мета-параметры модели"""

        verbose_name = "Пользователь"
        verbose_name_plural = "Пользователи"
        ordering = ("id",)

    def str(self):
        """Строковое представление модели"""

        return self.username


class Follow(models.Model):
    """Модель подписчика."""

    author = models.ForeignKey(
        FoodgramUser,
        related_name="follow",
        on_delete=models.CASCADE,
        verbose_name="Автор рецепта",
    )
    user = models.ForeignKey(
        FoodgramUser,
        on_delete=models.CASCADE,
        related_name="follower",
        verbose_name="Подписчик",
    )

    class Meta:
        """Мета-параметры модели"""

        verbose_name = "Подписка"
        verbose_name_plural = "Подписки"
        constraints = [
            models.UniqueConstraint(
                fields=["user", "author"], name="unique_follow")
        ]

    def str(self):
        """Метод строкового представления модели."""

        return f"{self.user} {self.author}"
