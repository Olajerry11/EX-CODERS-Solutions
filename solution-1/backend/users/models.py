"""
users/models.py

Custom User model extending AbstractUser.
Adds RBAC flags (is_student, is_lecturer) so permissions can be asserted
without querying a separate roles table — ideal for hackathon speed.

Design notes
────────────
• A user CAN be both a student and a lecturer (e.g. postgrad teaching assistant),
  so we use two independent boolean flags rather than a single choice field.
• AUTH_USER_MODEL = 'users.User' is declared in settings.py.
"""

from django.contrib.auth.models import AbstractUser
from django.db import models


class User(AbstractUser):
    """
    Extended user model with role flags for RBAC.

    Inherited fields from AbstractUser (selected):
        username, first_name, last_name, email,
        is_staff, is_active, is_superuser, date_joined, last_login

    Added fields:
        is_student  — True when the account belongs to a student.
        is_lecturer — True when the account belongs to a teaching staff member.
        matric_number — Unique student identifier (nullable for lecturers).
        staff_id      — Unique staff identifier (nullable for students).
        phone         — Optional contact number.
    """

    # ── Role flags (RBAC) ─────────────────────────────────────────────────────
    is_student = models.BooleanField(
        default=False,
        help_text="Designates this user as a student with read-only access to "
                  "timetable, materials, and notices.",
    )
    is_lecturer = models.BooleanField(
        default=False,
        help_text="Designates this user as a lecturer with full CRUD access to "
                  "notices, materials, and attendance sessions.",
    )

    # ── Profile fields ────────────────────────────────────────────────────────
    matric_number = models.CharField(
        max_length=20,
        unique=True,
        blank=True,
        null=True,
        help_text="Student matriculation number. Leave blank for lecturers.",
    )
    staff_id = models.CharField(
        max_length=20,
        unique=True,
        blank=True,
        null=True,
        help_text="Staff/Employee ID. Leave blank for students.",
    )
    phone = models.CharField(
        max_length=20,
        blank=True,
        default="",
        help_text="Optional contact phone number.",
    )

    # ── Meta ──────────────────────────────────────────────────────────────────
    class Meta:
        verbose_name = "User"
        verbose_name_plural = "Users"
        ordering = ["last_name", "first_name"]

    # ── Dunder / helpers ──────────────────────────────────────────────────────
    def __str__(self) -> str:
        role = "Lecturer" if self.is_lecturer else ("Student" if self.is_student else "Staff")
        identifier = self.staff_id or self.matric_number or self.username
        return f"{self.get_full_name() or self.username} [{role} | {identifier}]"

    @property
    def role(self) -> str:
        """Returns a human-readable role string for use in serializers / admin."""
        if self.is_lecturer and self.is_student:
            return "Teaching Assistant"
        if self.is_lecturer:
            return "Lecturer"
        if self.is_student:
            return "Student"
        return "Admin / Staff"
