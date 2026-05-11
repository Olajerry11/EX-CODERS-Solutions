"""
core/permissions.py

Custom DRF permission classes for Role-Based Access Control.

Classes
───────
  IsLecturer          — Allows access only to authenticated lecturers.
  IsStudent           — Allows access only to authenticated students.
  IsLecturerOrStudent — Allows any authenticated user (lecturer or student).
  IsOwnerOrLecturer   — Allows the object owner or any lecturer.

Usage in views
──────────────
  permission_classes = [IsAuthenticated, IsLecturer]
  permission_classes = [IsAuthenticated, IsStudent]
"""

from rest_framework.permissions import BasePermission, SAFE_METHODS


class IsLecturer(BasePermission):
    """
    Grants access only to authenticated users with is_lecturer=True.
    Used for: create/update/delete on Notices, Materials, AttendanceSessions.
    """

    message = "Access restricted to lecturers."

    def has_permission(self, request, view) -> bool:
        return bool(
            request.user
            and request.user.is_authenticated
            and request.user.is_lecturer
        )


class IsStudent(BasePermission):
    """
    Grants access only to authenticated users with is_student=True.
    Used for: attendance submission.
    """

    message = "Access restricted to students."

    def has_permission(self, request, view) -> bool:
        return bool(
            request.user
            and request.user.is_authenticated
            and request.user.is_student
        )


class IsLecturerOrReadOnly(BasePermission):
    """
    Lecturers get full access.
    Students (and any authenticated user) get read-only access (safe methods only).

    Used for: Course, TimetableSlot, Material, Notice ViewSets.
    """

    message = "Write access restricted to lecturers. Students may only read."

    def has_permission(self, request, view) -> bool:
        if not (request.user and request.user.is_authenticated):
            return False
        # Safe methods (GET, HEAD, OPTIONS) allowed for all authenticated users
        if request.method in SAFE_METHODS:
            return True
        # Write methods require lecturer flag
        return request.user.is_lecturer


class IsLecturerOrStudentReadOnly(BasePermission):
    """
    Same as IsLecturerOrReadOnly but restricted to only lecturers and students
    (excludes unauthenticated and admin-only accounts with neither flag set).
    """

    message = "Access restricted to lecturers (full) or students (read-only)."

    def has_permission(self, request, view) -> bool:
        if not (request.user and request.user.is_authenticated):
            return False
        if not (request.user.is_lecturer or request.user.is_student):
            return False
        if request.method in SAFE_METHODS:
            return True
        return request.user.is_lecturer
