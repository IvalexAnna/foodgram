from django.urls import path

from api.views import RecipeViewSet

urlpatterns = [

    path("s/<int:pk>/",RecipeViewSet.as_view(
        {"get": "redirect_recipe"}), name="short-link"),
]
