import random
import string

from django.contrib.auth import get_user_model
from django.db.utils import IntegrityError
from rest_framework import serializers
from rest_framework.exceptions import ValidationError
from api.users.models import UserRole

FoodgramUser = get_user_model()


class FoodgramUserSerializer(serializers.ModelSerializer):
    class Meta:
        model = FoodgramUser
        fields = [
            "email", "username", "is_subscribed", "avatar", "first_name", "last_name"
        ]

    def create(self, validated_data):
        role = validated_data.get("role", UserRole.USER)
        user = FoodgramUser(
            email=validated_data["email"],
            username=validated_data["username"],
            role=role,
            last_name=validated_data.get("last_name", ""),
            is_subscribed=validated_data.pop("is_subscribed", False),
            first_name=validated_data.get("first_name", ""),
            avatar=validated_data.get("avatar", ""),
        )
        user.set_password(validated_data.get("password"))
        user.save()

        confirmation_code = "".join(
            random.choices(string.ascii_letters + string.digits, k=6)
        )

        user.confirmation_code = confirmation_code
        user.save()

        print(f"Код подтверждения для {user.email}: {confirmation_code}")

        return user

    def validate_email(self, value):
        if FoodgramUser.objects.filter(email=value).exists():
            raise serializers.ValidationError(
                "Пользователь с таким email уже существует."
            )
        return value

    def validate_username(self, value):
        if FoodgramUser.objects.filter(username=value).exists():
            raise serializers.ValidationError(
                "Пользователь с таким username уже существует."
            )
        return value

    def update_avatar(self, instance, new_avatar):
        """Обновляет аватар пользователя."""
        if instance.avatar:
            instance.avatar.delete()
        instance.avatar = new_avatar
        instance.save()
        return instance

    def delete_avatar(self, instance):
        """Удаляет аватар пользователя."""
        if instance.avatar:
            instance.avatar.delete()
            instance.avatar = None
            instance.save()
        return instance

    def update(self, instance, validated_data):
        new_avatar = validated_data.get('avatar', None)

        if new_avatar is None:
            return self.delete_avatar(instance)

        return self.update_avatar(instance, new_avatar)


class SignUpSerializer(serializers.ModelSerializer):
    username = serializers.RegexField(
        required=True,
        max_length=150,
        regex=r"^[\w.@+-]+",
    )
    email = serializers.EmailField(required=True, max_length=150)

    class Meta:
        model = FoodgramUser
        fields = ("username", "email")

    def create(self, validated_data):
        try:
            user = FoodgramUser.objects.get_or_create(**validated_data)[0]
        except IntegrityError:
            raise ValidationError(
                "Отсутствует обязательное поле или оно некоректно",
            )
        return user


class TokenSerializer(serializers.Serializer):
    username = serializers.CharField()
    confirmation_code = serializers.CharField()
