from django.urls import include, path
from rest_framework.routers import DefaultRouter

from .views import RecipeViewSet, TagViewSet, IngredientViewSet, redirect_short_link

app_name = 'api'

router = DefaultRouter()

router.register('recipes', RecipeViewSet, basename='recipes')
router.register('tags', TagViewSet, basename='tags')
router.register('ingredients', IngredientViewSet, basename='ingredients')


urlpatterns = [
    path('', include(router.urls)),
    path('s/<int:pk>/', redirect_short_link, name='short-link')
]