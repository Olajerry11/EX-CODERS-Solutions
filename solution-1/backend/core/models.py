"""
core/models.py

Domain models for the university scheduling & attendance system.

Models
──────
  Course            — Academic course register
  TimetableSlot     — Scheduled class with double-booking guard
  Material          — Uploaded course material (files)
  Notice            — Lecturer broadcast to all students
  AttendanceSession — PIN-gated sign-in window created by a lecturer
  AttendanceRecord  — Single student check-in tied to a session

Business Logic
──────────────
  TimetableSlot.clean()  — Raises ValidationError on venue/time overlap.
  TimetableSlot.save()   — Calls full_clean() so the guard always fires,
                           even outside DRF (admin, shell, fixtures).
  AttendanceSession      — expires_at defaults to 5 minutes from creation;
                           the PIN is a 4-digit zero-padded string.
"""

import random
import string
from datetime import timedelta

from django.conf import settings
from django.core.exceptions import ValidationError
from django.core.validators import RegexValidator
from django.db import models
from django.utils import timezone


# ─────────────────────────────────────────────────────────────────────────────
# HELPERS
# ─────────────────────────────────────────────────────────────────────────────

def _four_digit_pin() -> str:
    """Generate a cryptographically adequate 4-digit numeric PIN."""
    return "".join(random.choices(string.digits, k=4))


def _session_expiry() -> object:
    """Return a timezone-aware datetime 5 minutes from now."""
    return timezone.now() + timedelta(minutes=5)


# ─────────────────────────────────────────────────────────────────────────────
# COURSE
# ─────────────────────────────────────────────────────────────────────────────

class Course(models.Model):
    """
    Represents an academic course unit.

    Fields
    ──────
    course_code — Unique identifier, e.g. "CSC401".
    title       — Full course name, e.g. "Operating Systems".
    description — Optional syllabus summary.
    lecturer    — The primary lecturer responsible for the course.
    students    — Enrolled students (many-to-many; optional for demo).
    """

    course_code = models.CharField(
        max_length=20,
        unique=True,
        help_text='Unique course code, e.g. "CSC401".',
    )
    title = models.CharField(max_length=200)
    description = models.TextField(blank=True, default="")
    lecturer = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="courses_taught",
        limit_choices_to={"is_lecturer": True},
    )
    students = models.ManyToManyField(
        settings.AUTH_USER_MODEL,
        blank=True,
        related_name="courses_enrolled",
        limit_choices_to={"is_student": True},
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["course_code"]
        verbose_name = "Course"
        verbose_name_plural = "Courses"

    def __str__(self) -> str:
        return f"{self.course_code} — {self.title}"


# ─────────────────────────────────────────────────────────────────────────────
# TIMETABLE SLOT
# ─────────────────────────────────────────────────────────────────────────────

class TimetableSlot(models.Model):
    """
    A single scheduled class session for a course.

    Clash-detection logic
    ─────────────────────
    clean() queries for any *other* TimetableSlot on the same day at the
    same venue whose time window overlaps with the one being saved.

    Two intervals [A_start, A_end) and [B_start, B_end) overlap iff:
        A_start < B_end  AND  A_end > B_start

    This is enforced in both clean() (for DRF / form validation) and
    save() (as a last-resort guard for raw ORM writes).
    """

    DAY_CHOICES = [
        ("MON", "Monday"),
        ("TUE", "Tuesday"),
        ("WED", "Wednesday"),
        ("THU", "Thursday"),
        ("FRI", "Friday"),
        ("SAT", "Saturday"),
        ("SUN", "Sunday"),
    ]

    course = models.ForeignKey(
        Course,
        on_delete=models.CASCADE,
        related_name="timetable_slots",
    )
    venue = models.CharField(
        max_length=100,
        help_text='Room or hall identifier, e.g. "LT-3" or "Science Block A".',
    )
    day_of_week = models.CharField(max_length=3, choices=DAY_CHOICES)
    start_time = models.TimeField()
    end_time = models.TimeField()

    class Meta:
        ordering = ["day_of_week", "start_time"]
        verbose_name = "Timetable Slot"
        verbose_name_plural = "Timetable Slots"

    # ── Validation ────────────────────────────────────────────────────────────

    def clean(self) -> None:
        """
        Prevent double-booking: raise ValidationError if this slot's
        venue is already occupied by another slot on the same day that
        overlaps in time.
        """
        # Ensure end is after start before we attempt the overlap query.
        if self.start_time and self.end_time and self.end_time <= self.start_time:
            raise ValidationError(
                {"end_time": "End time must be after start time."}
            )

        # Find overlapping slots at the same venue on the same day,
        # excluding this slot itself (when updating an existing record).
        overlapping = TimetableSlot.objects.filter(
            venue__iexact=self.venue,
            day_of_week=self.day_of_week,
            # Overlap condition: existing.start_time < self.end_time
            #                AND existing.end_time   > self.start_time
            start_time__lt=self.end_time,
            end_time__gt=self.start_time,
        )

        if self.pk:
            # Exclude the current instance during an update
            overlapping = overlapping.exclude(pk=self.pk)

        if overlapping.exists():
            conflict = overlapping.first()
            raise ValidationError(
                {
                    "venue": (
                        f'Venue "{self.venue}" is already booked on '
                        f"{self.get_day_of_week_display()} from "
                        f"{conflict.start_time.strftime('%H:%M')} to "
                        f"{conflict.end_time.strftime('%H:%M')} "
                        f"by {conflict.course}. "
                        f"Please choose a different venue or time."
                    )
                }
            )

    def save(self, *args, **kwargs) -> None:
        """
        Always run full_clean() before persisting, so the clash guard
        fires for raw ORM writes (shell, management commands, fixtures).
        """
        self.full_clean()
        super().save(*args, **kwargs)

    def __str__(self) -> str:
        return (
            f"{self.course.course_code} | {self.get_day_of_week_display()} "
            f"{self.start_time.strftime('%H:%M')}–{self.end_time.strftime('%H:%M')} "
            f"@ {self.venue}"
        )


# ─────────────────────────────────────────────────────────────────────────────
# MATERIAL
# ─────────────────────────────────────────────────────────────────────────────

def _material_upload_path(instance: "Material", filename: str) -> str:
    """Store uploads under media/materials/<course_code>/<filename>."""
    return f"materials/{instance.course.course_code}/{filename}"


class Material(models.Model):
    """
    A file (PDF, slide deck, etc.) uploaded by a lecturer for a course.
    """

    course = models.ForeignKey(
        Course,
        on_delete=models.CASCADE,
        related_name="materials",
    )
    uploaded_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        related_name="uploaded_materials",
        limit_choices_to={"is_lecturer": True},
    )
    title = models.CharField(max_length=200)
    file = models.FileField(upload_to=_material_upload_path)
    upload_date = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-upload_date"]
        verbose_name = "Course Material"
        verbose_name_plural = "Course Materials"

    def __str__(self) -> str:
        return f"{self.title} ({self.course.course_code})"


# ─────────────────────────────────────────────────────────────────────────────
# NOTICE
# ─────────────────────────────────────────────────────────────────────────────

class Notice(models.Model):
    """
    Broadcast notice from a lecturer to all students.
    Optionally scoped to a specific course; NULL means university-wide.
    """

    author = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="notices",
        limit_choices_to={"is_lecturer": True},
    )
    course = models.ForeignKey(
        Course,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="notices",
        help_text="Scope to a specific course, or leave blank for a general notice.",
    )
    title = models.CharField(max_length=200, default="")
    message = models.TextField()
    timestamp = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-timestamp"]
        verbose_name = "Notice"
        verbose_name_plural = "Notices"

    def __str__(self) -> str:
        scope = self.course.course_code if self.course else "General"
        return f"[{scope}] {self.title or self.message[:50]}"


# ─────────────────────────────────────────────────────────────────────────────
# ATTENDANCE SESSION
# ─────────────────────────────────────────────────────────────────────────────

_pin_validator = RegexValidator(
    regex=r"^\d{4}$",
    message="PIN must be exactly 4 digits.",
)


class AttendanceSession(models.Model):
    """
    A time-bounded sign-in window opened by a lecturer.

    Security design
    ───────────────
    • The PIN is auto-generated on creation (4 numeric digits).
    • expires_at defaults to 5 minutes from creation.
    • The submit endpoint checks expires_at > now() before accepting a sign-in.
    • Lecturers can manually close a session by setting expires_at to a past time.
    """

    course = models.ForeignKey(
        Course,
        on_delete=models.CASCADE,
        related_name="attendance_sessions",
    )
    lecturer = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="attendance_sessions_created",
        limit_choices_to={"is_lecturer": True},
    )
    pin = models.CharField(
        max_length=4,
        default=_four_digit_pin,
        validators=[_pin_validator],
        help_text="Auto-generated 4-digit attendance PIN. Shared verbally with students.",
    )
    created_at = models.DateTimeField(auto_now_add=True)
    expires_at = models.DateTimeField(
        default=_session_expiry,
        help_text="Session automatically expires 5 minutes after creation.",
    )

    class Meta:
        ordering = ["-created_at"]
        verbose_name = "Attendance Session"
        verbose_name_plural = "Attendance Sessions"

    @property
    def is_active(self) -> bool:
        """Returns True if the session window has not yet expired."""
        return timezone.now() < self.expires_at

    def __str__(self) -> str:
        status = "ACTIVE" if self.is_active else "EXPIRED"
        return (
            f"{self.course.course_code} | PIN: {self.pin} "
            f"[{status}] — expires {self.expires_at.strftime('%H:%M:%S')}"
        )


# ─────────────────────────────────────────────────────────────────────────────
# ATTENDANCE RECORD
# ─────────────────────────────────────────────────────────────────────────────

class AttendanceRecord(models.Model):
    """
    Records a single student's successful sign-in to an AttendanceSession.

    Constraints
    ───────────
    • unique_together (session, student) prevents duplicate sign-ins.
    • timestamp is server-set (auto_now_add) — cannot be spoofed by the client.
    """

    session = models.ForeignKey(
        AttendanceSession,
        on_delete=models.CASCADE,
        related_name="records",
    )
    student = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="attendance_records",
        limit_choices_to={"is_student": True},
    )
    timestamp = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-timestamp"]
        verbose_name = "Attendance Record"
        verbose_name_plural = "Attendance Records"
        # Core uniqueness constraint: one sign-in per student per session
        unique_together = [("session", "student")]

    def __str__(self) -> str:
        return (
            f"{self.student.get_full_name() or self.student.username} → "
            f"{self.session.course.course_code} "
            f"[{self.timestamp.strftime('%Y-%m-%d %H:%M')}]"
        )
