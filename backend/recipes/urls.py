from django.urls import path

from . import views

urlpatterns = [
    path("s/<slug:url_slug>/", views.url_redirect, name="url_redirect"),
]
