from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from django.contrib.contenttypes.models import ContentType
from django.urls import reverse
from django.utils.safestring import mark_safe
from django.db.models import Count

from api.recipes.models import Favorite, Recipe, Ingredient, Tag
from .models import FoodgramUser, Follow


@admin.register(FoodgramUser)
class FoodgramUserAdmin(UserAdmin):
    list_display = ("email", "username", "is_active",
                    "is_staff", "is_superuser")
    search_fields = ("email", "username")
    fieldsets = (
        (None, {"fields": ("username", "email", "password")}),
        ("Личная информация", {
         "fields": ("first_name", "last_name", "avatar")}),
        (
            "Подписки и рецепты",
            {"fields": ("get_subscriptions", "get_recipes",
                        "get_favorited_recipes")},
        ),
        ("Разрешения", {"fields": ("is_active", "is_staff", "is_superuser")}),
        ("Даты", {"fields": ("last_login", "date_joined")}),
    )
    add_fieldsets = (
        (None,
         {
             "classes": ("wide",),
             "fields": (
                 "username",
                 "email",
                 "password1",
                 "password2",
                 "is_staff",
                 "is_active",
             ),
         },
         ),
    )
    ordering = ("username",)
    readonly_fields = ("get_subscriptions", "get_recipes",
                       "get_favorited_recipes")

    def get_subscriptions(self, obj):
        custom_user_ct = ContentType.objects.get_for_model(FoodgramUser)
        app_label = custom_user_ct.app_label
        model_name = custom_user_ct.model

        subscriptions = Follow.objects.filter(user=obj)
        if subscriptions.exists():
            return mark_safe(
                "<br>".join([
                    f'''<a href="{reverse(f"admin:{app_label}_{model_name}_change",
                            args=[sub.author.id])}">{sub.author.username}</a>'''
                    for sub in subscriptions
                ])
            )
        return "Нет подписок"

    def get_recipes(self, obj):
        recipe_ct = ContentType.objects.get_for_model(Recipe)
        app_label = recipe_ct.app_label
        model_name = recipe_ct.model

        recipes = Recipe.objects.filter(author=obj)
        if recipes.exists():
            return mark_safe(
                "<br>".join([
                    f'''<a href="{reverse(f"admin:{app_label}_{model_name}_change",
                            args=[recipe.id])}">{recipe.name}</a>'''
                    for recipe in recipes
                ])
            )
        return "Нет рецептов"

    def get_favorited_recipes(self, obj):
        recipe_ct = ContentType.objects.get_for_model(Favorite)
        app_label = recipe_ct.app_label
        model_name = recipe_ct.model

        favorited_recipes = Favorite.objects.filter(user=obj)
        if favorited_recipes.exists():
            return mark_safe(
                "<br>".join([
                    f'''<a href="{reverse(f"admin:{app_label}_{model_name}_change",
                            args=[favorited_recipe.id])}">{favorited_recipe.recipe.name}</a>'''
                    for favorited_recipe in favorited_recipes
                ])
            )
        return "Нет избранных рецептов"

    get_subscriptions.short_description = "Подписки"
    get_recipes.short_description = "Рецепты"
    get_favorited_recipes.short_description = "Избранные рецепты"


@admin.register(Follow)
class FolowAdmin(admin.ModelAdmin):
    list_display = ("user", "author")


@admin.register(Recipe)
class RecipeAdmin(admin.ModelAdmin):
    list_display = ("name", "author", "favorites_count")
    search_fields = ("name", "author__username")
    list_filter = ("tags",)

    def get_queryset(self, request):
        queryset = super().get_queryset(request)
        queryset = queryset.annotate(favorites_count=Count('favorites'))
        return queryset

    def favorites_count(self, obj):
        return obj.favorites_count
    favorites_count.short_description = "Добавлено в избранное"


@admin.register(Ingredient)
class IngredientAdmin(admin.ModelAdmin):
    list_display = ("name", "measurement_unit")
    search_fields = ("name",)


@admin.register(Tag)
class TagAdmin(admin.ModelAdmin):
    list_display = ("name", "slug")
    search_fields = ("name",)

    def has_change_permission(self, request, obj=None):
        return request.user.is_superuser

    def has_delete_permission(self, request, obj=None):
        return request.user.is_superuser

    def has_add_permission(self, request):
        return request.user.is_superuser
