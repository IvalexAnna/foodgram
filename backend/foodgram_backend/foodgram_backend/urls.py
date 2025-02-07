from django.contrib import admin
from django.urls import path, include
from rest_framework.authtoken import views
from api.users.views import SignupView, TokenObtainView

urlpatterns = [
    path('admin/', admin.site.urls),
    #path('api/auth/token/login/', TokenObtainView.as_view(), name='token_obtain'),
    path('api/', include("api.urls")),
    path("signup/", SignupView.as_view(), name="signup"),

]
