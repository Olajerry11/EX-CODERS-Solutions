"""
backend/backend/urls.py

Root URL configuration.

URL structure
─────────────
  /admin/                     — Django admin panel
  /api/auth/register/         — POST: create new user
  /api/auth/login/            — POST: obtain JWT tokens
  /api/auth/token/refresh/    — POST: rotate access token
  /api/auth/logout/           — POST: blacklist refresh token
  /api/users/me/              — GET / PATCH: current user profile
  /api/courses/               — Course CRUD
  /api/timetable/             — Timetable CRUD
  /api/materials/             — Materials CRUD
  /api/notices/               — Notice CRUD
  /api/attendance/sessions/   — Attendance session CRUD
  /api/attendance/records/    — Attendance records (read-only)
  /api/attendance/submit/     — POST: student attendance submission
"""

from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    # ── Django admin ──────────────────────────────────────────────────────────
    path("admin/", admin.site.urls),

    # ── API — Users & Auth (users app) ───────────────────────────────────────
    # Mounts: /api/auth/*, /api/users/*
    path("api/", include("users.urls", namespace="users")),

    # ── API — Domain resources (core app) ────────────────────────────────────
    # Mounts: /api/courses/, /api/timetable/, /api/materials/, /api/notices/,
    #         /api/attendance/sessions/, /api/attendance/records/,
    #         /api/attendance/submit/
    path("api/", include("core.urls", namespace="core")),
]

# ── Serve uploaded media files during development ─────────────────────────────
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

