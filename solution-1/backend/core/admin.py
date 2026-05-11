"""
core/admin.py

Admin configuration for all core domain models.
Every model is fully editable for hackathon demo purposes —
rich list displays, inline editing, and search/filter support.
"""

from django.contrib import admin
from django.utils import timezone
from django.utils.html import format_html

from .models import (
    AttendanceRecord,
    AttendanceSession,
    Course,
    Material,
    Notice,
    TimetableSlot,
)


# ─────────────────────────────────────────────────────────────────────────────
# INLINES
# ─────────────────────────────────────────────────────────────────────────────

class TimetableSlotInline(admin.TabularInline):
    """Show timetable slots directly on the Course change page."""
    model = TimetableSlot
    extra = 1
    fields = ["venue", "day_of_week", "start_time", "end_time"]


class MaterialInline(admin.TabularInline):
    """Show materials directly on the Course change page."""
    model = Material
    extra = 1
    fields = ["title", "file", "uploaded_by", "upload_date"]
    readonly_fields = ["upload_date"]


class AttendanceRecordInline(admin.TabularInline):
    """Show sign-in records directly on the AttendanceSession change page."""
    model = AttendanceRecord
    extra = 0
    readonly_fields = ["student", "timestamp"]
    can_delete = False

    def has_add_permission(self, request, obj=None):
        return False  # Records are only created via the API


# ─────────────────────────────────────────────────────────────────────────────
# COURSE
# ─────────────────────────────────────────────────────────────────────────────

@admin.register(Course)
class CourseAdmin(admin.ModelAdmin):
    list_display  = ["course_code", "title", "lecturer", "student_count", "created_at"]
    list_filter   = ["lecturer"]
    search_fields = ["course_code", "title", "lecturer__username", "lecturer__last_name"]
    ordering      = ["course_code"]
    filter_horizontal = ["students"]   # Nice double-list widget for M2M
    readonly_fields   = ["created_at"]
    inlines = [TimetableSlotInline, MaterialInline]

    @admin.display(description="Students enrolled")
    def student_count(self, obj):
        return obj.students.count()


# ─────────────────────────────────────────────────────────────────────────────
# TIMETABLE SLOT
# ─────────────────────────────────────────────────────────────────────────────

@admin.register(TimetableSlot)
class TimetableSlotAdmin(admin.ModelAdmin):
    list_display  = [
        "course", "day_of_week", "start_time", "end_time", "venue"
    ]
    list_filter   = ["day_of_week", "course"]
    search_fields = ["course__course_code", "venue"]
    ordering      = ["day_of_week", "start_time"]

    # Surface model-level clean() errors in the admin form
    def save_model(self, request, obj, form, change):
        obj.full_clean()
        super().save_model(request, obj, form, change)


# ─────────────────────────────────────────────────────────────────────────────
# MATERIAL
# ─────────────────────────────────────────────────────────────────────────────

@admin.register(Material)
class MaterialAdmin(admin.ModelAdmin):
    list_display  = ["title", "course", "uploaded_by", "upload_date", "file_link"]
    list_filter   = ["course", "uploaded_by"]
    search_fields = ["title", "course__course_code", "uploaded_by__username"]
    readonly_fields = ["upload_date", "file_link"]
    ordering = ["-upload_date"]

    @admin.display(description="Download")
    def file_link(self, obj):
        if obj.file:
            return format_html('<a href="{}" target="_blank">📄 Download</a>', obj.file.url)
        return "—"


# ─────────────────────────────────────────────────────────────────────────────
# NOTICE
# ─────────────────────────────────────────────────────────────────────────────

@admin.register(Notice)
class NoticeAdmin(admin.ModelAdmin):
    list_display  = ["title", "author", "course", "timestamp", "message_preview"]
    list_filter   = ["author", "course"]
    search_fields = ["title", "message", "author__username", "course__course_code"]
    readonly_fields = ["timestamp"]
    ordering = ["-timestamp"]

    @admin.display(description="Preview")
    def message_preview(self, obj):
        return obj.message[:80] + ("…" if len(obj.message) > 80 else "")


# ─────────────────────────────────────────────────────────────────────────────
# ATTENDANCE SESSION
# ─────────────────────────────────────────────────────────────────────────────

@admin.register(AttendanceSession)
class AttendanceSessionAdmin(admin.ModelAdmin):
    list_display  = [
        "course", "lecturer", "pin", "created_at", "expires_at",
        "session_status", "record_count",
    ]
    list_filter   = ["course", "lecturer"]
    search_fields = ["course__course_code", "lecturer__username", "pin"]
    readonly_fields = ["pin", "created_at", "session_status", "record_count"]
    ordering = ["-created_at"]
    inlines = [AttendanceRecordInline]

    @admin.display(description="Status", boolean=False)
    def session_status(self, obj):
        if obj.is_active:
            return format_html('<span style="color:green;font-weight:bold;">● ACTIVE</span>')
        return format_html('<span style="color:red;">○ EXPIRED</span>')

    @admin.display(description="Sign-ins")
    def record_count(self, obj):
        return obj.records.count()

    def has_add_permission(self, request):
        """
        Prevent manual PIN creation from the admin — sessions should be
        created via the API so the PIN is auto-generated and time-bounded.
        Comment this out if you need to seed demo data manually.
        """
        return True  # Allowed for hackathon demo seeding


# ─────────────────────────────────────────────────────────────────────────────
# ATTENDANCE RECORD
# ─────────────────────────────────────────────────────────────────────────────

@admin.register(AttendanceRecord)
class AttendanceRecordAdmin(admin.ModelAdmin):
    list_display  = ["student", "session", "course_code", "timestamp"]
    list_filter   = ["session__course", "session"]
    search_fields = [
        "student__username",
        "student__matric_number",
        "session__course__course_code",
    ]
    readonly_fields = ["student", "session", "timestamp"]
    ordering = ["-timestamp"]

    @admin.display(description="Course")
    def course_code(self, obj):
        return obj.session.course.course_code

    def has_add_permission(self, request):
        """Records are created only through the attendance submit API."""
        return False

    def has_change_permission(self, request, obj=None):
        """Records are immutable audit logs."""
        return False
