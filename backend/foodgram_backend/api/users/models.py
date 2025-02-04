from django.contrib.auth.models import AbstractUser
from django.db import models

MAX_LENGTH: int = 6


class UserRole(models.TextChoices):
    """Класс для определения ролей пользователей."""
    USER = "user", "Пользователь"
    MODERATOR = "moderator", "Модератор"
    ADMIN = "admin", "Админ"


class FoodgramUser(AbstractUser):
    """Модель пользователя."""
    email = models.EmailField(unique=True, verbose_name="email")

    role = models.CharField(
        max_length=max(len(role) for role in UserRole),
        default=UserRole.USER,
        choices=UserRole.choices,
        verbose_name="Роль",
    )

    confirmation_code = models.CharField(
        max_length=MAX_LENGTH,
        blank=True,
        null=True
    )
    avatar = models.ImageField(upload_to="users/", null=True, blank=True)
    is_subscribed = models.BooleanField(default=False, verbose_name="Подписан")
    
    class Meta(AbstractUser.Meta):
        verbose_name = "Пользователь"
        verbose_name_plural = "Пользователи"
        ordering = ["username"]

    @property
    def is_moderator(self):
        """Проверка, является ли пользователь модератором."""
        return self.role == UserRole.MODERATOR

    @property
    def is_admin(self):
        """Проверяет, является ли пользователь администратором."""
        return self.role == UserRole.ADMIN or self.is_superuser
