import random
import string

from django.contrib.auth import get_user_model
from django.db.utils import IntegrityError
from djoser.serializers import UserCreateSerializer
from rest_framework import serializers

from rest_framework.exceptions import ValidationError
from users.models import UserRole, Follow
from api.fields import Base64ImageField


FoodgramUser = get_user_model()


class CustomUserSerializer(UserCreateSerializer):
    """Сериализатор для модели User."""

    is_subscribed = serializers.SerializerMethodField()
    avatar = Base64ImageField(required=False)

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
            'avatar'
        )

    def get_is_subscribed(self, obj):
        """Метод проверки подписки"""

        user = self.context.get("request").user
        if user.is_anonymous:
            return False
        return Follow.objects.filter(user=user, author=obj.id).exists()


class CustomCreateUserSerializer(UserCreateSerializer):
    """Сериализатор для создания пользователя."""

    class Meta(UserCreateSerializer.Meta):
        """Мета-параметры сериализатора"""

        model = FoodgramUser
        fields = ("email", "id", "username", "first_name", "last_name", "password")


