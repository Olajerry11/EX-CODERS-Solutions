"""
core/views.py

API ViewSets and custom endpoints for the university scheduling system.

RBAC Summary
────────────
  Resource              Lecturers       Students
  ──────────────────    ─────────────   ──────────────────
  Course                Full CRUD       Read-only
  TimetableSlot         Full CRUD       Read-only
  Material              Full CRUD       Read-only
  Notice                Full CRUD       Read-only
  AttendanceSession     Full CRUD       Read (no PIN shown)
  AttendanceRecord      Read-only       Read-only (own records)
  /attendance/submit/   ✗               POST only

Custom Endpoints
────────────────
  POST /api/attendance/submit/
      Accepts: { "course_id": <int>, "pin": "<4-digit>" }
      Guards:  session exists → not expired → no duplicate
      Returns: AttendanceRecord (no PIN)
"""

from rest_framework import generics, mixins, permissions, status, viewsets
from rest_framework.decorators import action
from rest_framework.parsers import FormParser, JSONParser, MultiPartParser
from rest_framework.response import Response
from rest_framework.views import APIView

from .models import (
    AttendanceRecord,
    AttendanceSession,
    Course,
    Material,
    Notice,
    TimetableSlot,
)
from .permissions import IsLecturer, IsLecturerOrReadOnly, IsStudent
from .serializers import (
    AttendanceRecordSerializer,
    AttendanceSessionSerializer,
    AttendanceSessionStudentSerializer,
    AttendanceSubmitSerializer,
    CourseSerializer,
    MaterialSerializer,
    NoticeSerializer,
    TimetableSlotSerializer,
)


# ─────────────────────────────────────────────────────────────────────────────
# COURSE
# ─────────────────────────────────────────────────────────────────────────────

class CourseViewSet(viewsets.ModelViewSet):
    """
    /api/courses/

    Lecturers : GET, POST, PUT, PATCH, DELETE
    Students  : GET only

    Filtering helpers (query params):
      ?lecturer=<id>  — courses taught by a specific lecturer
      ?search=<str>   — filter by course_code or title (case-insensitive)
    """

    serializer_class = CourseSerializer
    permission_classes = [permissions.IsAuthenticated, IsLecturerOrReadOnly]

    def get_queryset(self):
        qs = Course.objects.select_related("lecturer").prefetch_related("students")
        # Optional query-param filters
        lecturer_id = self.request.query_params.get("lecturer")
        search = self.request.query_params.get("search")
        if lecturer_id:
            qs = qs.filter(lecturer_id=lecturer_id)
        if search:
            qs = qs.filter(course_code__icontains=search) | qs.filter(
                title__icontains=search
            )
        return qs

    def perform_create(self, serializer):
        """Auto-assign the logged-in lecturer as the course lecturer if not specified."""
        if self.request.user.is_lecturer and not serializer.validated_data.get("lecturer"):
            serializer.save(lecturer=self.request.user)
        else:
            serializer.save()


# ─────────────────────────────────────────────────────────────────────────────
# TIMETABLE SLOT
# ─────────────────────────────────────────────────────────────────────────────

class TimetableSlotViewSet(viewsets.ModelViewSet):
    """
    /api/timetable/

    Lecturers : full CRUD — clash detection fires automatically via serializer.
    Students  : GET only

    Filtering helpers:
      ?day=<MON|TUE|...>  — filter by day of week
      ?course=<id>        — filter by course
      ?venue=<str>        — filter by venue
    """

    serializer_class = TimetableSlotSerializer
    permission_classes = [permissions.IsAuthenticated, IsLecturerOrReadOnly]

    def get_queryset(self):
        qs = TimetableSlot.objects.select_related("course")
        day = self.request.query_params.get("day")
        course_id = self.request.query_params.get("course")
        venue = self.request.query_params.get("venue")
        if day:
            qs = qs.filter(day_of_week=day.upper())
        if course_id:
            qs = qs.filter(course_id=course_id)
        if venue:
            qs = qs.filter(venue__icontains=venue)
        return qs


# ─────────────────────────────────────────────────────────────────────────────
# MATERIAL
# ─────────────────────────────────────────────────────────────────────────────

class MaterialViewSet(viewsets.ModelViewSet):
    """
    /api/materials/

    Lecturers : full CRUD — accepts multipart/form-data for file upload.
    Students  : GET only

    Filtering helpers:
      ?course=<id>  — filter by course
    """

    serializer_class = MaterialSerializer
    permission_classes = [permissions.IsAuthenticated, IsLecturerOrReadOnly]
    # Support both JSON (metadata update) and multipart (file upload)
    parser_classes = [MultiPartParser, FormParser, JSONParser]

    def get_queryset(self):
        qs = Material.objects.select_related("course", "uploaded_by")
        course_id = self.request.query_params.get("course")
        if course_id:
            qs = qs.filter(course_id=course_id)
        return qs

    def perform_create(self, serializer):
        """Auto-assign the uploading lecturer as uploaded_by."""
        serializer.save(uploaded_by=self.request.user)

    def get_serializer_context(self):
        """Pass request into serializer context for building absolute file URLs."""
        context = super().get_serializer_context()
        context["request"] = self.request
        return context


# ─────────────────────────────────────────────────────────────────────────────
# NOTICE
# ─────────────────────────────────────────────────────────────────────────────

class NoticeViewSet(viewsets.ModelViewSet):
    """
    /api/notices/

    Lecturers : full CRUD
    Students  : GET only (read all notices, scoped or general)

    Filtering helpers:
      ?course=<id>  — course-scoped notices only
      ?general=1    — notices with no course (university-wide)
    """

    serializer_class = NoticeSerializer
    permission_classes = [permissions.IsAuthenticated, IsLecturerOrReadOnly]

    def get_queryset(self):
        qs = Notice.objects.select_related("author", "course")
        course_id = self.request.query_params.get("course")
        general = self.request.query_params.get("general")
        if course_id:
            qs = qs.filter(course_id=course_id)
        if general:
            qs = qs.filter(course__isnull=True)
        return qs

    def perform_create(self, serializer):
        """Auto-assign the logged-in lecturer as the author."""
        serializer.save(author=self.request.user)


# ─────────────────────────────────────────────────────────────────────────────
# ATTENDANCE SESSION
# ─────────────────────────────────────────────────────────────────────────────

class AttendanceSessionViewSet(viewsets.ModelViewSet):
    """
    /api/attendance/sessions/

    Lecturers
    ─────────
    • POST   — creates a new session; PIN is auto-generated and returned.
    • GET    — list/detail with PIN visible.
    • PATCH  — can extend expires_at to keep session open longer.
    • DELETE — close a session early.

    Students
    ────────
    • GET only — list/detail WITHOUT the PIN field (AttendanceSessionStudentSerializer).
    • To submit attendance, students use POST /api/attendance/submit/ instead.

    Custom action:
    • GET /api/attendance/sessions/<id>/records/
        Returns all sign-in records for a session (lecturer only).
    """

    permission_classes = [permissions.IsAuthenticated, IsLecturerOrReadOnly]

    def get_queryset(self):
        qs = AttendanceSession.objects.select_related("course", "lecturer")
        course_id = self.request.query_params.get("course")
        active_only = self.request.query_params.get("active")
        if course_id:
            qs = qs.filter(course_id=course_id)
        if active_only:
            # Filter to sessions whose expires_at is in the future
            from django.utils import timezone
            qs = qs.filter(expires_at__gt=timezone.now())
        return qs

    def get_serializer_class(self):
        """
        Serve different serializers based on the caller's role:
          - Lecturers see the PIN (AttendanceSessionSerializer).
          - Students never see the PIN (AttendanceSessionStudentSerializer).
        """
        if self.request.user.is_student and not self.request.user.is_lecturer:
            return AttendanceSessionStudentSerializer
        return AttendanceSessionSerializer

    def perform_create(self, serializer):
        """Auto-assign the logged-in lecturer."""
        serializer.save(lecturer=self.request.user)

    @action(
        detail=True,
        methods=["get"],
        permission_classes=[permissions.IsAuthenticated, IsLecturer],
        url_path="records",
    )
    def records(self, request, pk=None):
        """
        GET /api/attendance/sessions/<id>/records/

        Returns the list of sign-in records for this session.
        Only accessible to lecturers.
        """
        session = self.get_object()
        records_qs = session.records.select_related("student", "session__course")
        serializer = AttendanceRecordSerializer(records_qs, many=True)
        return Response(serializer.data)


# ─────────────────────────────────────────────────────────────────────────────
# ATTENDANCE RECORD
# ─────────────────────────────────────────────────────────────────────────────

class AttendanceRecordViewSet(
    mixins.RetrieveModelMixin,
    mixins.ListModelMixin,
    viewsets.GenericViewSet,
):
    """
    /api/attendance/records/    — Read-only for all authenticated users.

    Students see only their own records.
    Lecturers see all records (filterable by session or course).

    Filtering helpers:
      ?session=<id>  — records for a specific session
      ?student=<id>  — records for a specific student (lecturer only)
      ?course=<id>   — all records across sessions for a course
    """

    serializer_class = AttendanceRecordSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        user = self.request.user
        qs = AttendanceRecord.objects.select_related(
            "student", "session", "session__course"
        )

        # Students can only view their own attendance history
        if user.is_student and not user.is_lecturer:
            qs = qs.filter(student=user)

        # Optional filters
        session_id = self.request.query_params.get("session")
        student_id = self.request.query_params.get("student")
        course_id = self.request.query_params.get("course")

        if session_id:
            qs = qs.filter(session_id=session_id)
        if student_id and user.is_lecturer:
            qs = qs.filter(student_id=student_id)
        if course_id:
            qs = qs.filter(session__course_id=course_id)

        return qs


# ─────────────────────────────────────────────────────────────────────────────
# ATTENDANCE SUBMIT — Custom endpoint
# ─────────────────────────────────────────────────────────────────────────────

class AttendanceSubmitView(APIView):
    """
    POST /api/attendance/submit/

    Allows a student to sign in to an active attendance session using the
    4-digit PIN announced verbally by their lecturer.

    Authentication : JWT Bearer token (student must be logged in)
    Permission     : IsStudent only

    Request body:
        {
            "course_id": 3,
            "pin": "7842"
        }

    Success response (201 Created):
        {
            "detail": "Attendance recorded successfully.",
            "record": {
                "id": 12,
                "session_id": 5,
                "course_code": "CSC401",
                "course_title": "Operating Systems",
                "student": 7,
                "student_detail": { ... },
                "timestamp": "2026-05-11T22:40:00Z"
            }
        }

    Error responses:
        400 — Invalid PIN / wrong course
        400 — Session expired
        400 — Already signed in
        403 — Non-student caller
    """

    permission_classes = [permissions.IsAuthenticated, IsStudent]

    def post(self, request):
        serializer = AttendanceSubmitSerializer(
            data=request.data,
            context={"request": request},
        )

        if not serializer.is_valid():
            return Response(
                serializer.errors,
                status=status.HTTP_400_BAD_REQUEST,
            )

        # save() runs the validated logic and creates the AttendanceRecord
        record = serializer.save()

        return Response(
            {
                "detail": "Attendance recorded successfully.",
                "record": AttendanceRecordSerializer(
                    record, context={"request": request}
                ).data,
            },
            status=status.HTTP_201_CREATED,
        )
