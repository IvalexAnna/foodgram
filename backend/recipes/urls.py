from django.urls import path

from api.views import url_redirect

urlpatterns = [
    path("s/<slug:url_slug>/", url_redirect, name="url_redirect"),
]
