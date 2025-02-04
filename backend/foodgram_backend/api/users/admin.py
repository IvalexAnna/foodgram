from django.contrib import admin
from django.contrib.auth.admin import UserAdmin

from .models import FoodgramUser


@admin.register(FoodgramUser)
class YamdbUserAdmin(UserAdmin):
    list_display = (
        "email", "username", "is_subscribed", "avatar", "first_name",
        "last_name")
    list_filter = ("username",)
    search_fields = ("email", "username")
    empty_value_display = "-пусто-"
