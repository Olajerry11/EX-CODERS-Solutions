"""
core/serializers.py

Serializers for all domain models.

Security design for Attendance PIN
────────────────────────────────────
The PIN lifecycle is carefully controlled:

  1. AttendanceSessionSerializer
     • 'pin' is READ by lecturers ONLY (returned on create so they can
       announce it verbally).  The view restricts this serializer to
       lecturers.
     • Students NEVER call a list/detail endpoint that returns a session's
       PIN — the view returns AttendanceSessionStudentSerializer instead,
       which omits the field entirely.

  2. AttendanceSubmitSerializer  (used by /api/attendance/submit/)
     • 'pin' is write_only — it is accepted from the student, validated
       server-side, and NEVER echoed back in the response.
     • Validation chain:
         a. Does a session with this PIN exist for the given course?
         b. Is the session still active (expires_at > now)?
         c. Has the student already signed in to this session?

  3. AttendanceRecordSerializer
     • Returned after a successful submission — contains NO PIN.
"""

from django.utils import timezone
from rest_framework import serializers

from users.serializers import UserSerializer
from .models import (
    AttendanceRecord,
    AttendanceSession,
    Course,
    Material,
    Notice,
    TimetableSlot,
)


# ─────────────────────────────────────────────────────────────────────────────
# COURSE
# ─────────────────────────────────────────────────────────────────────────────

class CourseSerializer(serializers.ModelSerializer):
    """Full course representation. lecturer nested (read); students count."""

    lecturer_detail = UserSerializer(source="lecturer", read_only=True)
    student_count = serializers.IntegerField(
        source="students.count", read_only=True
    )

    class Meta:
        model = Course
        fields = [
            "id",
            "course_code",
            "title",
            "description",
            "lecturer",          # write: FK id
            "lecturer_detail",   # read:  nested object
            "student_count",
            "created_at",
        ]
        read_only_fields = ["id", "created_at", "lecturer_detail", "student_count"]


# ─────────────────────────────────────────────────────────────────────────────
# TIMETABLE SLOT
# ─────────────────────────────────────────────────────────────────────────────

class TimetableSlotSerializer(serializers.ModelSerializer):
    """
    Serializer for TimetableSlot.

    Clash detection
    ───────────────
    The model's clean() / save() already enforces the double-booking rule.
    DRF's ModelSerializer calls full_clean() during validate(), so any
    ValidationError raised in clean() is automatically surfaced as a 400
    response with the correct field key ('venue').
    """

    course_code = serializers.CharField(source="course.course_code", read_only=True)
    course_title = serializers.CharField(source="course.title", read_only=True)
    day_display = serializers.CharField(
        source="get_day_of_week_display", read_only=True
    )

    class Meta:
        model = TimetableSlot
        fields = [
            "id",
            "course",          # write: FK id
            "course_code",     # read:  from course
            "course_title",    # read:  from course
            "venue",
            "day_of_week",
            "day_display",
            "start_time",
            "end_time",
        ]
        read_only_fields = ["id", "course_code", "course_title", "day_display"]

    def validate(self, attrs: dict) -> dict:
        """
        Trigger model-level clean() so the clash guard fires through DRF.
        We build a temporary (unsaved) instance and call full_clean() on it,
        which will raise a DRF-friendly ValidationError on conflict.
        """
        # Build a partial instance for validation (don't save yet)
        instance = TimetableSlot(**attrs)
        if self.instance:
            # On update, preserve the PK so exclude-self works in clean()
            instance.pk = self.instance.pk

        try:
            instance.clean()
        except Exception as e:
            # Re-raise as DRF ValidationError (preserves field keys)
            raise serializers.ValidationError(e.message_dict if hasattr(e, "message_dict") else str(e))

        return attrs


# ─────────────────────────────────────────────────────────────────────────────
# MATERIAL
# ─────────────────────────────────────────────────────────────────────────────

class MaterialSerializer(serializers.ModelSerializer):
    """
    Serializer for course materials.
    Supports multipart/form-data upload via DRF's MultiPartParser.
    uploaded_by is set automatically in the view from request.user.
    """

    course_code = serializers.CharField(source="course.course_code", read_only=True)
    uploaded_by_name = serializers.SerializerMethodField()
    file_url = serializers.SerializerMethodField()

    class Meta:
        model = Material
        fields = [
            "id",
            "course",           # write: FK id
            "course_code",      # read
            "title",
            "file",             # write: uploaded file
            "file_url",         # read: absolute URL
            "uploaded_by",      # write: FK id (auto-set in view)
            "uploaded_by_name", # read: human name
            "upload_date",
        ]
        read_only_fields = [
            "id",
            "course_code",
            "file_url",
            "uploaded_by_name",
            "upload_date",
        ]
        extra_kwargs = {
            # uploaded_by is injected by the view; not required from the client
            "uploaded_by": {"required": False, "allow_null": True},
        }

    def get_uploaded_by_name(self, obj: Material) -> str:
        if obj.uploaded_by:
            return obj.uploaded_by.get_full_name() or obj.uploaded_by.username
        return "Unknown"

    def get_file_url(self, obj: Material) -> str | None:
        request = self.context.get("request")
        if obj.file and request:
            return request.build_absolute_uri(obj.file.url)
        return None


# ─────────────────────────────────────────────────────────────────────────────
# NOTICE
# ─────────────────────────────────────────────────────────────────────────────

class NoticeSerializer(serializers.ModelSerializer):
    """
    Serializer for lecturer notices.
    author is auto-set in the view; returned as a nested object on read.
    """

    author_name = serializers.SerializerMethodField()
    course_code = serializers.CharField(
        source="course.course_code", read_only=True, default=None
    )

    class Meta:
        model = Notice
        fields = [
            "id",
            "author",       # write: FK id (auto-set in view)
            "author_name",  # read
            "course",       # write: FK id (optional)
            "course_code",  # read
            "title",
            "message",
            "timestamp",
        ]
        read_only_fields = ["id", "author_name", "course_code", "timestamp"]
        extra_kwargs = {
            "author": {"required": False},
            "course": {"required": False, "allow_null": True},
        }

    def get_author_name(self, obj: Notice) -> str:
        return obj.author.get_full_name() or obj.author.username


# ─────────────────────────────────────────────────────────────────────────────
# ATTENDANCE SESSION — Lecturer view (PIN visible)
# ─────────────────────────────────────────────────────────────────────────────

class AttendanceSessionSerializer(serializers.ModelSerializer):
    """
    Full session representation for LECTURERS.

    PIN is readable here so the lecturer can copy/announce it after creation.
    This serializer must NEVER be used in student-facing list/detail endpoints.

    lecturer is auto-set from request.user in the view.
    """

    course_code = serializers.CharField(source="course.course_code", read_only=True)
    is_active = serializers.BooleanField(read_only=True)
    record_count = serializers.IntegerField(
        source="records.count", read_only=True
    )

    class Meta:
        model = AttendanceSession
        fields = [
            "id",
            "course",        # write: FK id
            "course_code",   # read
            "lecturer",      # write: FK id (auto-set in view)
            "pin",           # READ: visible to the creating lecturer only
            "created_at",
            "expires_at",
            "is_active",
            "record_count",
        ]
        read_only_fields = [
            "id",
            "pin",           # Auto-generated; lecturer cannot override it
            "created_at",
            "is_active",
            "record_count",
            "course_code",
        ]
        extra_kwargs = {
            "lecturer": {"required": False},
            # expires_at is optional — defaults to now+5min in the model
            "expires_at": {"required": False},
        }


# ─────────────────────────────────────────────────────────────────────────────
# ATTENDANCE SESSION — Student view (PIN hidden)
# ─────────────────────────────────────────────────────────────────────────────

class AttendanceSessionStudentSerializer(serializers.ModelSerializer):
    """
    Restricted session view for STUDENTS.

    The PIN field is completely absent — students can only submit attendance
    via /api/attendance/submit/ by providing the PIN out-of-band (verbally).
    """

    course_code = serializers.CharField(source="course.course_code", read_only=True)
    course_title = serializers.CharField(source="course.title", read_only=True)
    is_active = serializers.BooleanField(read_only=True)

    class Meta:
        model = AttendanceSession
        fields = [
            "id",
            "course_code",
            "course_title",
            "created_at",
            "expires_at",
            "is_active",
            # 'pin' is intentionally excluded
        ]
        read_only_fields = fields


# ─────────────────────────────────────────────────────────────────────────────
# ATTENDANCE SUBMIT — Custom endpoint serializer
# ─────────────────────────────────────────────────────────────────────────────

class AttendanceSubmitSerializer(serializers.Serializer):
    """
    Input serializer for POST /api/attendance/submit/

    Security validation chain (in order):
      1. A session with this PIN exists for the given course.
      2. The session has not expired (expires_at > now).
      3. The authenticated student has not already signed in.

    On success: creates an AttendanceRecord and returns it.
    The PIN is NEVER echoed back in the response.

    Fields
    ──────
    course_id — The Course PK the student believes they are attending.
    pin       — The 4-digit PIN announced by the lecturer (write-only).
    """

    course_id = serializers.IntegerField(
        help_text="Primary key of the Course the student is attending."
    )
    pin = serializers.CharField(
        max_length=4,
        min_length=4,
        write_only=True,          # PIN is NEVER returned in the response
        style={"input_type": "password"},
        help_text="4-digit PIN announced by the lecturer. Write-only.",
    )

    # Internal: populated during validate() for use in the view/save()
    _session = None

    def validate(self, attrs: dict) -> dict:
        """
        Full business-logic validation for attendance submission.
        Runs after individual field validators pass.
        """
        course_id = attrs["course_id"]
        pin       = attrs["pin"]
        student   = self.context["request"].user

        # ── Guard 0: caller must be a student ─────────────────────────────────
        if not student.is_student:
            raise serializers.ValidationError(
                "Only students can submit attendance."
            )

        # ── Guard 1: find the session ─────────────────────────────────────────
        try:
            session = AttendanceSession.objects.select_related("course").get(
                course_id=course_id,
                pin=pin,
            )
        except AttendanceSession.DoesNotExist:
            # Deliberately vague — do not confirm whether course or PIN is wrong
            raise serializers.ValidationError(
                {"pin": "Invalid PIN or course. Please check and try again."}
            )

        # ── Guard 2: session must still be active ─────────────────────────────
        if not session.is_active:
            raise serializers.ValidationError(
                {"pin": "This attendance session has expired. Contact your lecturer."}
            )

        # ── Guard 3: no duplicate sign-ins ────────────────────────────────────
        already_signed = AttendanceRecord.objects.filter(
            session=session,
            student=student,
        ).exists()

        if already_signed:
            raise serializers.ValidationError(
                "You have already signed in to this session."
            )

        # Cache the session for use in save()
        self._session = session
        return attrs

    def save(self, **kwargs) -> AttendanceRecord:
        """Create and return the AttendanceRecord on successful validation."""
        student = self.context["request"].user
        record = AttendanceRecord.objects.create(
            session=self._session,
            student=student,
        )
        return record


# ─────────────────────────────────────────────────────────────────────────────
# ATTENDANCE RECORD — Read
# ─────────────────────────────────────────────────────────────────────────────

class AttendanceRecordSerializer(serializers.ModelSerializer):
    """
    Read-only view of a signed-in attendance record.
    Returned to the student after a successful /api/attendance/submit/ call,
    and to lecturers viewing their session's sign-in list.
    Contains NO PIN information.
    """

    student_detail = UserSerializer(source="student", read_only=True)
    course_code = serializers.CharField(
        source="session.course.course_code", read_only=True
    )
    course_title = serializers.CharField(
        source="session.course.title", read_only=True
    )
    session_id = serializers.IntegerField(source="session.id", read_only=True)

    class Meta:
        model = AttendanceRecord
        fields = [
            "id",
            "session_id",
            "course_code",
            "course_title",
            "student",          # FK id
            "student_detail",   # nested object
            "timestamp",
        ]
        read_only_fields = fields
