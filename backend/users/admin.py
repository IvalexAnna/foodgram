from django.contrib import admin
from django.contrib.auth.admin import UserAdmin

from .models import FoodgramUser


@admin.register(FoodgramUser)
class FoodgramUserAdmin(UserAdmin):
    list_display = (
        "email", "username", "first_name", "last_name")
    list_filter = ("username",)
    search_fields = ("email", "username")
    empty_value_display = "-пусто-"
