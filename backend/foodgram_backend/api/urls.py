from django.urls import include, path
from rest_framework.routers import DefaultRouter

from .users.views import UserViewSet
from .views import RecipeViewSet, TagViewSet, IngredientViewSet

router = DefaultRouter()

router.register("users", UserViewSet, basename="User")
router.register("recipes", RecipeViewSet, basename="Recipe")
router.register("tags", TagViewSet, basename="Tag")
router.register("ingredients", IngredientViewSet, basename="Ingredient")


urlpatterns = [
    path("", include(router.urls)),
    path('auth/', include('djoser.urls.authtoken')),
    #path('auth/', include('djoser.urls.jwt')),
]