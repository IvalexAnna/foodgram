from django.urls import include, path
from rest_framework.routers import DefaultRouter

from .views import (
    FoodgramUserViewSet, IngredientViewSet, RecipeViewSet, TagViewSet
)

app_name = "api"

router = DefaultRouter()

router.register("ingredients", IngredientViewSet, basename="ingredient")
router.register("tags", TagViewSet, basename="tag")
router.register("recipes", RecipeViewSet, basename="recipes")
router.register("users", FoodgramUserViewSet, basename="user")


urlpatterns = [
    path("auth/", include("djoser.urls.authtoken")),
    path("", include(router.urls)),
    ]
