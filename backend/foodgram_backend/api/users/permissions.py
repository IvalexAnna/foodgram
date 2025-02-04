from rest_framework import permissions


class IsAnonymous(permissions.BasePermission):
    """
    Разрешение для анонимных пользователей.
    """

    def has_permission(self, request, view):
        return request.user.is_anonymous


class IsAuthenticatedUser(permissions.BasePermission):
    """
    Разрешение для аутентифицированных пользователей.
    """

    def has_permission(self, request, view):
        return request.user.is_authenticated


class IsModerator(permissions.BasePermission):
    """
    Разрешение для модераторов.
    """

    def has_permission(self, request, view):
        return request.user.is_moderator or request.user.is_admin


class IsAdmin(permissions.BasePermission):
    """
    Разрешение для администраторов.
    """

    def has_permission(self, request, view):
        return request.user.is_admin
