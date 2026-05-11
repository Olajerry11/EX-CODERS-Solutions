"""Phase 4 verification: URL resolution and router registry."""
import os
import django

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "backend.settings")
django.setup()

from django.urls import reverse

# ── Named URL check ───────────────────────────────────────────────────────────
checks = [
    ("users:register",          "/api/auth/register/"),
    ("users:login",             "/api/auth/login/"),
    ("users:logout",            "/api/auth/logout/"),
    ("users:token-refresh",     "/api/auth/token/refresh/"),
    ("users:me",                "/api/users/me/"),
    ("core:attendance-submit",  "/api/attendance/submit/"),
]

print("Named URL resolution:")
all_ok = True
for name, expected in checks:
    try:
        resolved = reverse(name)
        ok = resolved == expected
        print(f"  [{'PASS' if ok else 'FAIL'}] {name:40s} => {resolved}")
        if not ok:
            print(f"         expected: {expected}")
            all_ok = False
    except Exception as e:
        print(f"  [FAIL] {name:40s} => ERROR: {e}")
        all_ok = False

# ── Router registry ────────────────────────────────────────────────────────────
from core.urls import router as core_router

print("\nDRF DefaultRouter registry (core):")
for prefix, viewset, basename in core_router.registry:
    print(f"  /api/{prefix}/  [{viewset.__name__}]  basename={basename!r}")

# ── Admin registration ─────────────────────────────────────────────────────────
from django.contrib import admin

print("\nAdmin-registered models:")
for model, model_admin in admin.site._registry.items():
    app = model._meta.app_label
    if app in ("users", "core"):
        print(f"  {app}.{model.__name__:30s}  [{type(model_admin).__name__}]")

print(f"\nAll URL checks passed: {all_ok}")
