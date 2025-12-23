"""
URL configuration for Asset Control Panel project.
"""

from django.contrib import admin
from django.contrib.auth import views as auth_views
from django.urls import include, path

urlpatterns = [
    # Admin interface
    path("admin/", admin.site.urls),
    # Authentication
    path(
        "login/", auth_views.LoginView.as_view(template_name="login.html"), name="login"
    ),
    path("logout/", auth_views.LogoutView.as_view(), name="logout"),
    # Assets app
    path("", include("assets.urls")),
]
