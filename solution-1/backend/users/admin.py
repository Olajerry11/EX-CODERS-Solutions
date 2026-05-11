"""
users/admin.py

Admin configuration for the custom User model.
Extends UserAdmin so all built-in fields (password hash, permissions,
groups) remain manageable alongside our custom fields.
"""

from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin

from .models import User


@admin.register(User)
class UserAdmin(BaseUserAdmin):
    """
    Custom User admin.

    Extends the built-in UserAdmin with our RBAC fields displayed
    in the change form and list view for easy demo management.
    """

    # ── List view ─────────────────────────────────────────────────────────────
    list_display = [
        "username",
        "get_full_name",
        "email",
        "role",
        "is_student",
        "is_lecturer",
        "matric_number",
        "staff_id",
        "is_active",
        "date_joined",
    ]
    list_filter = ["is_student", "is_lecturer", "is_staff", "is_active"]
    search_fields = [
        "username",
        "first_name",
        "last_name",
        "email",
        "matric_number",
        "staff_id",
    ]
    ordering = ["last_name", "first_name"]

    # ── Detail / change form ──────────────────────────────────────────────────
    # Append our custom fieldsets to the built-in ones
    fieldsets = BaseUserAdmin.fieldsets + (
        (
            "Role & Identity",
            {
                "fields": (
                    "is_student",
                    "is_lecturer",
                    "matric_number",
                    "staff_id",
                    "phone",
                ),
                "description": (
                    "Set is_student or is_lecturer to assign RBAC roles. "
                    "matric_number is required for students; staff_id for lecturers."
                ),
            },
        ),
    )

    # Fields shown when creating a new user from the admin
    add_fieldsets = BaseUserAdmin.add_fieldsets + (
        (
            "Role & Identity",
            {
                "classes": ("wide",),
                "fields": (
                    "first_name",
                    "last_name",
                    "email",
                    "is_student",
                    "is_lecturer",
                    "matric_number",
                    "staff_id",
                    "phone",
                ),
            },
        ),
    )
