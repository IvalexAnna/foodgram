from rest_framework.pagination import PageNumberPagination

from django.conf import settings

PAGE_SIZE = settings.REST_FRAMEWORK["PAGE_SIZE"]


class CustomPagination(PageNumberPagination):
    """Кастомная пагинация."""

    page_size = PAGE_SIZE
    page_size_query_param = "limit"
    max_page_size = PAGE_SIZE
