"""
core/urls.py

URL patterns for all domain resources.

Router-generated endpoints
──────────────────────────
  /api/courses/                            GET (list), POST (create)
  /api/courses/<id>/                       GET, PUT, PATCH, DELETE
  /api/timetable/                          GET, POST
  /api/timetable/<id>/                     GET, PUT, PATCH, DELETE
  /api/materials/                          GET, POST (multipart)
  /api/materials/<id>/                     GET, PUT, PATCH, DELETE
  /api/notices/                            GET, POST
  /api/notices/<id>/                       GET, PUT, PATCH, DELETE
  /api/attendance/sessions/               GET, POST
  /api/attendance/sessions/<id>/          GET, PUT, PATCH, DELETE
  /api/attendance/sessions/<id>/records/  GET  (lecturer only)
  /api/attendance/records/                GET (list)
  /api/attendance/records/<id>/           GET (detail)

Custom endpoints
────────────────
  /api/attendance/submit/                 POST (students only)
"""

from django.urls import include, path
from rest_framework.routers import DefaultRouter

from .views import (
    AttendanceRecordViewSet,
    AttendanceSessionViewSet,
    AttendanceSubmitView,
    CourseViewSet,
    MaterialViewSet,
    NoticeViewSet,
    TimetableSlotViewSet,
)

app_name = "core"

# ─────────────────────────────────────────────────────────────────────────────
# DEFAULT ROUTER
# Registers ViewSets and auto-generates all standard CRUD routes + detail URLs.
# ─────────────────────────────────────────────────────────────────────────────
router = DefaultRouter()

router.register(r"courses",   CourseViewSet,   basename="course")
router.register(r"timetable", TimetableSlotViewSet, basename="timetableslot")
router.register(r"materials", MaterialViewSet, basename="material")
router.register(r"notices",   NoticeViewSet,   basename="notice")

# Attendance sub-resources grouped under the same prefix for clarity
router.register(
    r"attendance/sessions",
    AttendanceSessionViewSet,
    basename="attendancesession",
)
router.register(
    r"attendance/records",
    AttendanceRecordViewSet,
    basename="attendancerecord",
)

# ─────────────────────────────────────────────────────────────────────────────
# URL PATTERNS
# ─────────────────────────────────────────────────────────────────────────────
urlpatterns = [
    # All router-generated URLs
    path("", include(router.urls)),

    # Custom attendance submit endpoint (not a ViewSet action — separate view)
    # POST /api/attendance/submit/
    path(
        "attendance/submit/",
        AttendanceSubmitView.as_view(),
        name="attendance-submit",
    ),
]
