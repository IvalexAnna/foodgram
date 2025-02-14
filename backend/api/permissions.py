from rest_framework import permissions


class IsAdminOrReadOnly(permissions.BasePermission):
    """
    Разрешение, которое позволяет только администраторам выполнять
    любые действия, в то время как остальные пользователи могут
    только просматривать данные.

    """
    def has_permission(self, request, view):
        return request.method in permissions.SAFE_METHODS or (
            request.user.is_authenticated and (request.user.is_admin)
        )


class IsAuthorOrReadOnly(permissions.BasePermission):
    """
    Разрешение, которое позволяет автору объекта выполнять любые действия,
    в то время как другие пользователи могут только просматривать объект.

    """
    def has_object_permission(self, request, view, obj):
        if request.method in permissions.SAFE_METHODS:
            return True
        return obj.author == request.user


class HasAccess(permissions.BasePermission):
    """
    Разрешение, которое позволяет анонимным пользователям только
    безопасные методы (GET, HEAD, OPTIONS), а аутентифицированным
    пользователям выполнять любые действия с объектами.

    """
    def has_permission(self, request, view):
        return (
            request.method in permissions.SAFE_METHODS
            or request.user.is_authenticated
        )

    def has_object_permission(self, request, view, obj):
        if request.method in permissions.SAFE_METHODS:
            return True
        return (
            obj.author == request.user
            or request.user.is_moderator
            or request.user.is_admin
        )
