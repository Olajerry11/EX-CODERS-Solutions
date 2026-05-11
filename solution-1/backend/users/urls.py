"""
users/urls.py

URL patterns for authentication and user profile endpoints.

Prefix: /api/auth/  and  /api/users/
(mounted in backend/urls.py)
"""

from django.urls import path
from rest_framework_simplejwt.views import TokenRefreshView

from .views import LoginView, LogoutView, MeView, RegisterView

app_name = "users"

urlpatterns = [
    # ── Auth ──────────────────────────────────────────────────────────────────
    # POST — obtain JWT pair; returns access + refresh + user profile
    path("auth/register/", RegisterView.as_view(), name="register"),
    path("auth/login/",    LoginView.as_view(),    name="login"),

    # POST — rotate access token using refresh token (SimpleJWT built-in)
    path("auth/token/refresh/", TokenRefreshView.as_view(), name="token-refresh"),

    # POST — blacklist refresh token (logout)
    path("auth/logout/", LogoutView.as_view(), name="logout"),

    # ── Current user profile ───────────────────────────────────────────────────
    # GET  — retrieve own profile
    # PATCH — update phone / names
    path("users/me/", MeView.as_view(), name="me"),
]
