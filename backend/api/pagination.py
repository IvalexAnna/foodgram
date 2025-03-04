from rest_framework.pagination import LimitOffsetPagination


class CustomPagination(LimitOffsetPagination):
    """Кастомная пагинация."""

    default_limit = 6
    max_limit = 100
