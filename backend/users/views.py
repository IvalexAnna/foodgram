import random
import string

from django.conf import settings
from django.core.mail import send_mail
from django.shortcuts import get_object_or_404
from rest_framework import filters, status, viewsets
from rest_framework.exceptions import MethodNotAllowed, PermissionDenied
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.tokens import AccessToken
from users.models import UserRole, FoodgramUser
from djoser.views import UserViewSet
from .permissions import IsAnonymous, IsAuthenticatedUser
from .serializers import CustomUserSerializer
from api.pagination import CustomPagination
from rest_framework.permissions import IsAuthenticated
from rest_framework.decorators import action


class CustomUserViewSet(UserViewSet):
    """ViewSet для управления пользователями."""
    queryset = FoodgramUser.objects.all()
    serializer_class = CustomUserSerializer
    permission_classes = [IsAuthenticatedUser]
    pagination_class = CustomPagination

    def get_object(self):
        """
        Получение объекта пользователя по username или pk.
        """
        if self.kwargs.get("username") == "me":
            return self.request.user
        elif self.request.user.is_admin:
            username = self.kwargs.get("username")
            user = get_object_or_404(FoodgramUser, username=username)
            return user
        else:
            raise PermissionDenied("У вас нет прав доступа к этому ресурсу.")

    def list(self, request, *args, **kwargs):
        if not request.user.is_admin:
            raise PermissionDenied("У вас нет прав доступа к этому ресурсу.")
        return super().list(request, *args, **kwargs)

    def create(self, request, *args, **kwargs):
        self.permission_classes = [IsAnonymous]
        self.check_permissions(request)
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data, status=status.HTTP_201_CREATED)

    @action(
        detail=False,
        methods=["PUT", "PATCH", "DELETE"],
        permission_classes=[IsAuthenticated],
        url_path="me/avatar",
    )
    def avatar(self, request):
        user = request.user

        # Удаление аватара
        if request.method == "DELETE":
            if user.avatar:
                user.avatar.delete(save=True)
                return Response(status=status.HTTP_204_NO_CONTENT)
            return Response({"error": "Аватар не найден"}, status=status.HTTP_404_NOT_FOUND)

        # Проверка наличия данных
        if not request.data.get("avatar"):
            return Response({"error": "Поле 'avatar' обязательно."}, status=status.HTTP_400_BAD_REQUEST)

        # Обновление аватара
        serializer = CustomUserSerializer(user, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()

        # Проверка наличия URL аватара
        if user.avatar:
            return Response({"avatar": user.avatar.url}, status=status.HTTP_200_OK)
        else:
            return Response({"error": "Ошибка при сохранении аватара."}, status=status.HTTP_400_BAD_REQUEST)

    def partial_update(self, request, *args, **kwargs):
        user = self.get_object()

        if not request.user.is_admin and request.user != user:
            self.permission_denied(request)

        serializer = self.get_serializer(user, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()

        return Response(serializer.data)

    def destroy(self, request, *args, **kwargs):
        if kwargs.get("username") == "me":
            raise MethodNotAllowed("DELETE")

        if not request.user.is_admin:
            raise PermissionDenied("У вас нет прав доступа к этому ресурсу.")

        return super().destroy(request, *args, **kwargs)

    def update(self, request, *args, **kwargs):
        raise MethodNotAllowed("PUT-запросы к этому ресурсу не предусмотрены.")
