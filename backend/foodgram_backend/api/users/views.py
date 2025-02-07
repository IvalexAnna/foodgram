import random
import string

from django.conf import settings
from django.core.mail import send_mail
from django.shortcuts import get_object_or_404
from rest_framework import filters, status, viewsets
from rest_framework.exceptions import MethodNotAllowed, PermissionDenied
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.tokens import AccessToken, RefreshToken
from api.users.models import UserRole, FoodgramUser
from rest_framework.authtoken.views import ObtainAuthToken
from rest_framework.authtoken.models import Token
from rest_framework.permissions import AllowAny
from django.contrib.auth import authenticate
from .authentication import EmailBackend

from .permissions import IsAnonymous, IsAuthenticatedUser
from .serializers import TokenSerializer, FoodgramUserSerializer, SignUpSerializer


class UserViewSet(viewsets.ModelViewSet):
    """ViewSet для управления пользователями."""

    queryset = FoodgramUser.objects.all()
    serializer_class = FoodgramUserSerializer
    permission_classes = [IsAnonymous]
    filter_backends = (filters.SearchFilter,)
    search_fields = ("username",)
    lookup_field = "username"

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

    def partial_update(self, request, *args, **kwargs):
        user = self.get_object()
        if not request.user.is_admin:
            if request.user != user:
                self.permission_denied(request)

        data = request.data.copy()

        if "role" in data:
            role = data["role"]
            valid_roles = [UserRole.ADMIN, UserRole.MODERATOR, UserRole.USER]
            if role not in valid_roles:
                return Response(
                    {"error": "Неверная роль."}, status=status.HTTP_400_BAD_REQUEST
                )

            data.pop("role", None)

        serializer = self.get_serializer(user, data=data, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()

        return Response(serializer.data)

    def destroy(self, request, *args, **kwargs):
        if kwargs.get("username") == "me":
            raise MethodNotAllowed("DELETE")

        if not request.user.is_admin:
            raise PermissionDenied("У вас нет прав доступа к этому ресурсу.")

        return super().destroy(request, *args, **kwargs)

    def get_object(self):
        if self.kwargs.get("username") == "me":
            return self.request.user
        elif self.request.user.is_admin:
            username = self.kwargs.get("username")
            user = get_object_or_404(FoodgramUser, username=username)
            return user
        else:
            raise PermissionDenied("У вас нет прав доступа к этому ресурсу.")

    def update(self, request, *args, **kwargs):
        raise MethodNotAllowed("PUT-запросы к этому ресурсу не предусмотрены.")


class TokenObtainView(APIView):
    """View для получения токена доступа."""

    permission_classes = [AllowAny]

    def post(self, request):
        serializer = TokenSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        backend_instance = EmailBackend()
        user = backend_instance.authenticate(
            request=request,
            **serializer.validated_data)

        if user is None:
            return Response(
                {"detail": "Неверный email или пароль."},
                status=status.HTTP_401_UNAUTHORIZED,
            )

        refresh = RefreshToken.for_user(user)
        return Response(
            {"refresh": str(refresh), "access": str(refresh.access_token)},
            status=status.HTTP_200_OK,
        )


class SignupView(APIView):
    """View для регистрации нового пользователя."""

    permission_classes = [AllowAny]

    def post(self, request):
        serializer = SignUpSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()

        confirmation_code = "".join(
            random.choices(string.ascii_letters + string.digits, k=6)
        )
        user.confirmation_code = confirmation_code
        user.save()

        self.send_confirmation_email(user.email, confirmation_code)

        return Response(
            {"username": user.username, "email": user.email}, status=status.HTTP_200_OK
        )

    def send_confirmation_email(self, email, confirmation_code):
        send_mail(
            "Код подтверждения",
            f"Ваш код подтверждения: {confirmation_code}",
            settings.DEFAULT_FROM_EMAIL,
            [email],
            fail_silently=False,
        )
