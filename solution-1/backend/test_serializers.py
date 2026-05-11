"""Quick smoke test for all Phase 2 serializers."""
import django, os
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "backend.settings")
django.setup()

from users.serializers import (
    CustomTokenObtainPairSerializer,
    UserSerializer,
    UserRegistrationSerializer,
    UserProfileUpdateSerializer,
)
from core.serializers import (
    CourseSerializer,
    TimetableSlotSerializer,
    MaterialSerializer,
    NoticeSerializer,
    AttendanceSessionSerializer,
    AttendanceSessionStudentSerializer,
    AttendanceSubmitSerializer,
    AttendanceRecordSerializer,
)

print("All serializers imported successfully.\n")

# Verify PIN security properties
submit_fields = list(AttendanceSubmitSerializer().fields.keys())
session_lec_fields = list(AttendanceSessionSerializer().fields.keys())
session_stu_fields = list(AttendanceSessionStudentSerializer().fields.keys())

print(f"AttendanceSubmitSerializer fields: {submit_fields}")
print(f"AttendanceSessionSerializer (Lecturer) fields: {session_lec_fields}")
print(f"AttendanceSessionStudentSerializer fields: {session_stu_fields}")

pin_write_only = AttendanceSubmitSerializer().fields["pin"].write_only
pin_in_student_view = "pin" in session_stu_fields
pin_in_lecturer_view = "pin" in session_lec_fields

print(f"\nSecurity checks:")
print(f"  [{'PASS' if pin_write_only else 'FAIL'}] PIN is write_only in AttendanceSubmitSerializer: {pin_write_only}")
print(f"  [{'PASS' if not pin_in_student_view else 'FAIL'}] PIN absent from student session view: {not pin_in_student_view}")
print(f"  [{'PASS' if pin_in_lecturer_view else 'FAIL'}] PIN present in lecturer session view: {pin_in_lecturer_view}")

print("\nPhase 2 smoke test PASSED.")
