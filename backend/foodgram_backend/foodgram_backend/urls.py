from django.contrib import admin
from django.urls import path, include
from rest_framework.authtoken import views
from api.users.views import SignupView

urlpatterns = [
    path('admin/', admin.site.urls),
    path('api-token-auth/', views.obtain_auth_token),
    path('api/', include("api.urls")),
    path('auth/', include('djoser.urls')),
    path('auth/', include('djoser.urls.jwt')),
    path("signup/", SignupView.as_view(), name="signup"),
]
