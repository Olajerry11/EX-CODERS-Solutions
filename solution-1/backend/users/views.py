"""
users/views.py

Authentication and user account endpoints.

Endpoints
─────────
  POST /api/auth/register/        — Create a new student or lecturer account
  POST /api/auth/login/           — Obtain JWT access + refresh tokens
  POST /api/auth/token/refresh/   — Rotate access token using refresh token
  POST /api/auth/logout/          — Blacklist refresh token (revoke session)
  GET  /api/users/me/             — Retrieve authenticated user's profile
  PATCH /api/users/me/            — Partial update of profile (phone, names)
"""

from rest_framework import generics, permissions, status
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework_simplejwt.views import TokenObtainPairView

from .serializers import (
    CustomTokenObtainPairSerializer,
    UserProfileUpdateSerializer,
    UserRegistrationSerializer,
    UserSerializer,
)


# ─────────────────────────────────────────────────────────────────────────────
# AUTH — Login (obtain JWT pair)
# ─────────────────────────────────────────────────────────────────────────────

class LoginView(TokenObtainPairView):
    """
    POST /api/auth/login/

    Returns access + refresh tokens, with an embedded 'user' profile block
    and role claims baked into the JWT payload.

    Example request:
        { "username": "john_doe", "password": "s3cr3t!" }

    Example response:
        {
          "access":  "<jwt>",
          "refresh": "<jwt>",
          "user": { "id": 1, "role": "Student", ... }
        }
    """

    serializer_class = CustomTokenObtainPairSerializer


# ─────────────────────────────────────────────────────────────────────────────
# AUTH — Logout (blacklist refresh token)
# ─────────────────────────────────────────────────────────────────────────────

class LogoutView(APIView):
    """
    POST /api/auth/logout/

    Blacklists the provided refresh token, invalidating the session.
    The client should also discard its stored access token.

    Request body:
        { "refresh": "<refresh_token>" }
    """

    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        refresh_token = request.data.get("refresh")
        if not refresh_token:
            return Response(
                {"detail": "Refresh token is required."},
                status=status.HTTP_400_BAD_REQUEST,
            )
        try:
            token = RefreshToken(refresh_token)
            token.blacklist()
            return Response(
                {"detail": "Successfully logged out."},
                status=status.HTTP_205_RESET_CONTENT,
            )
        except Exception:
            return Response(
                {"detail": "Invalid or already-blacklisted token."},
                status=status.HTTP_400_BAD_REQUEST,
            )


# ─────────────────────────────────────────────────────────────────────────────
# REGISTRATION
# ─────────────────────────────────────────────────────────────────────────────

class RegisterView(generics.CreateAPIView):
    """
    POST /api/auth/register/

    Creates a new student or lecturer account. No authentication required.

    Required fields: username, password, password_confirm, first_name,
                     last_name, email, is_student OR is_lecturer,
                     matric_number (if student), staff_id (if lecturer).

    Returns: 201 Created with the serialized user profile (no password).
    """

    permission_classes = [permissions.AllowAny]
    serializer_class = UserRegistrationSerializer

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()
        # Return full profile (not the write serializer's data)
        return Response(
            UserSerializer(user).data,
            status=status.HTTP_201_CREATED,
        )


# ─────────────────────────────────────────────────────────────────────────────
# CURRENT USER PROFILE
# ─────────────────────────────────────────────────────────────────────────────

class MeView(generics.RetrieveUpdateAPIView):
    """
    GET   /api/users/me/ — Return the authenticated user's full profile.
    PATCH /api/users/me/ — Partially update allowed profile fields.

    Non-updatable via this endpoint:
        username, password, is_student, is_lecturer, matric_number, staff_id
    """

    permission_classes = [permissions.IsAuthenticated]
    http_method_names = ["get", "patch", "head", "options"]  # No PUT

    def get_serializer_class(self):
        if self.request.method in ("PATCH",):
            return UserProfileUpdateSerializer
        return UserSerializer

    def get_object(self):
        return self.request.user

    def partial_update(self, request, *args, **kwargs):
        """Override to return the full profile after update."""
        serializer = UserProfileUpdateSerializer(
            request.user,
            data=request.data,
            partial=True,
        )
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(UserSerializer(request.user).data)
