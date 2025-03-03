from django.urls import path

from api.views import RecipeViewSet

urlpatterns = [
    path("s/<slug:url_slug>/", RecipeViewSet, name="url_redirect"),
]
