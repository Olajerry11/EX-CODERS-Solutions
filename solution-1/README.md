# 🎓 EX-Coders University Scheduling & Attendance API

A production-ready, **decoupled REST API** built for a university hackathon that solves three critical student pain points:

| Pain Point | Solution |
|---|---|
| **Scheduling clashes** | TimetableSlot model with server-enforced venue/time overlap detection |
| **Material distribution** | Secure, lecturer-only file uploads accessible to all enrolled students |
| **Attendance fraud** | Time-bounded PIN sessions (5-min expiry) with duplicate-sign-in prevention |

---

## 🏗️ Tech Stack

| Layer | Technology | Version |
|---|---|---|
| Framework | Django + Django REST Framework | 4.2 / 3.17 |
| Authentication | SimpleJWT (RS256-ready, HS256 default) | 5.5 |
| Token Blacklist | `rest_framework_simplejwt.token_blacklist` | — |
| Database | SQLite | zero-config |
| CORS | `django-cors-headers` | 4.9 |
| File handling | Pillow | 12.x |
| Config | `python-decouple` (.env) | 3.8 |
| Python | CPython | 3.12+ |

---

## 📐 Schema Overview

```
┌─────────────────┐       ┌──────────────────────┐
│      User       │       │        Course         │
│─────────────────│       │──────────────────────│
│ id              │1     *│ id                   │
│ username        │───────│ course_code (unique) │
│ is_student (FK) │       │ title                │
│ is_lecturer     │       │ description          │
│ matric_number   │       │ lecturer ─────────────┼──► User(is_lecturer)
│ staff_id        │       │ students (M2M) ───────┼──► User(is_student)
└─────────────────┘       └──────────────────────┘
                                    │
           ┌────────────────────────┼──────────────────────────────┐
           │                        │                              │
           ▼                        ▼                              ▼
┌──────────────────┐   ┌────────────────────┐   ┌────────────────────────┐
│  TimetableSlot   │   │      Material      │   │        Notice          │
│──────────────────│   │────────────────────│   │────────────────────────│
│ course (FK)      │   │ course (FK)        │   │ author (FK→Lecturer)   │
│ venue            │   │ title              │   │ course (FK, nullable)  │
│ day_of_week      │   │ file               │   │ title                  │
│ start_time       │   │ uploaded_by (FK)   │   │ message                │
│ end_time         │   │ upload_date        │   │ timestamp              │
│                  │   └────────────────────┘   └────────────────────────┘
│ ⚡ CLASH GUARD:  │
│ clean()+save()   │   ┌─────────────────────────┐
│ raises           │   │    AttendanceSession     │
│ ValidationError  │   │─────────────────────────│
│ on overlap       │   │ course (FK)              │
└──────────────────┘   │ lecturer (FK)            │
                       │ pin  (4-digit, auto-gen) │
                       │ created_at               │
                       │ expires_at (now + 5 min) │
                       └─────────────────────────┘
                                    │ 1
                                    │
                                    │ *
                       ┌─────────────────────────┐
                       │    AttendanceRecord      │
                       │─────────────────────────│
                       │ session (FK)             │
                       │ student (FK)             │
                       │ timestamp (auto)         │
                       │                          │
                       │ ⚡ UNIQUE(session,student)│
                       └─────────────────────────┘
```

### RBAC Quick Reference

| Flag | Role | Capabilities |
|---|---|---|
| `is_lecturer = True` | Lecturer | Full CRUD on Courses, Timetable, Materials, Notices, Attendance Sessions |
| `is_student = True` | Student | Read-only on all resources; POST to `/api/attendance/submit/` |
| Both `True` | Teaching Assistant | Combined capabilities |

---

## ⚙️ Setup Guide

### Prerequisites

- Python 3.12 or higher
- `pip` (comes with Python)
- Git (optional, for cloning)

---

### 1. Clone / Navigate to project

```bash
cd solution-1
```

---

### 2. Create and activate virtual environment

```bash
# Create
python -m venv venv

# Activate (Windows PowerShell)
.\venv\Scripts\Activate.ps1

# Activate (Windows CMD)
venv\Scripts\activate.bat

# Activate (macOS / Linux)
source venv/bin/activate
```

---

### 3. Install dependencies

```bash
pip install -r requirements.txt
```

---

### 4. Configure environment variables

```bash
# Copy the template
cp backend/.env.example backend/.env
```

Edit `backend/.env`:

```dotenv
# Generate a new key with:
# python -c "from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())"
SECRET_KEY=your-generated-secret-key-here

DEBUG=True
ALLOWED_HOSTS=127.0.0.1,localhost
CORS_ALLOWED_ORIGINS=http://localhost:3000,http://127.0.0.1:3000
```

> ⚠️ **Never commit `.env` to version control.** It is already in `.gitignore`.

---

### 5. Run database migrations

```bash
python backend/manage.py migrate
```

Expected output:
```
Operations to perform:
  Apply all migrations: admin, auth, contenttypes, core, sessions, token_blacklist, users
Running migrations:
  Applying users.0001_initial... OK
  Applying core.0001_initial... OK
  ...
```

---

### 6. Create a superuser (admin panel access)

```bash
python backend/manage.py createsuperuser
```

Follow the prompts. Then log in at `http://127.0.0.1:8000/admin/`.

> **Tip for hackathon demo:** After creating the superuser, open the admin panel
> and create a Lecturer user and a Student user with the correct role flags set,
> then use their credentials with the JWT login endpoint.

---

### 7. Start the development server

```bash
python backend/manage.py runserver
```

Server will be available at: **`http://127.0.0.1:8000/`**

The DRF Browsable API root is at: **`http://127.0.0.1:8000/api/`**

---

## 🗺️ API Endpoint Map

### Authentication

| Method | Endpoint | Permission | Description |
|---|---|---|---|
| `POST` | `/api/auth/register/` | Public | Create student or lecturer account |
| `POST` | `/api/auth/login/` | Public | Obtain JWT access + refresh tokens |
| `POST` | `/api/auth/token/refresh/` | Public | Rotate expired access token |
| `POST` | `/api/auth/logout/` | Authenticated | Blacklist refresh token |
| `GET` | `/api/users/me/` | Authenticated | View own profile |
| `PATCH` | `/api/users/me/` | Authenticated | Update profile fields |

### Courses

| Method | Endpoint | Permission | Description |
|---|---|---|---|
| `GET` | `/api/courses/` | Any Auth | List all courses |
| `POST` | `/api/courses/` | Lecturer | Create a new course |
| `GET` | `/api/courses/<id>/` | Any Auth | Course detail |
| `PUT/PATCH` | `/api/courses/<id>/` | Lecturer | Update course |
| `DELETE` | `/api/courses/<id>/` | Lecturer | Delete course |

**Query params:** `?lecturer=<id>` · `?search=<str>`

### Timetable

| Method | Endpoint | Permission | Description |
|---|---|---|---|
| `GET` | `/api/timetable/` | Any Auth | Full timetable |
| `POST` | `/api/timetable/` | Lecturer | Add slot (clash guard active) |
| `GET/PUT/PATCH/DELETE` | `/api/timetable/<id>/` | Lecturer | Manage slot |

**Query params:** `?day=MON` · `?course=<id>` · `?venue=<str>`

### Materials

| Method | Endpoint | Permission | Description |
|---|---|---|---|
| `GET` | `/api/materials/` | Any Auth | List materials |
| `POST` | `/api/materials/` | Lecturer | Upload file (`multipart/form-data`) |
| `GET/PUT/PATCH/DELETE` | `/api/materials/<id>/` | Lecturer | Manage material |

**Query params:** `?course=<id>`

### Notices

| Method | Endpoint | Permission | Description |
|---|---|---|---|
| `GET` | `/api/notices/` | Any Auth | List notices |
| `POST` | `/api/notices/` | Lecturer | Broadcast notice |
| `GET/PUT/PATCH/DELETE` | `/api/notices/<id>/` | Lecturer | Manage notice |

**Query params:** `?course=<id>` · `?general=1` (university-wide only)

### Attendance

| Method | Endpoint | Permission | Description |
|---|---|---|---|
| `GET` | `/api/attendance/sessions/` | Any Auth | List sessions (PIN visible to Lecturers only) |
| `POST` | `/api/attendance/sessions/` | Lecturer | Open a new session (PIN auto-generated) |
| `GET/PATCH/DELETE` | `/api/attendance/sessions/<id>/` | Lecturer | Manage session |
| `GET` | `/api/attendance/sessions/<id>/records/` | Lecturer | View all sign-ins for a session |
| `GET` | `/api/attendance/records/` | Any Auth | Own records (Student) / All records (Lecturer) |
| **`POST`** | **`/api/attendance/submit/`** | **Student** | **Submit PIN to mark attendance** |

---

## 🔐 Attendance PIN — Example Payload

### Step 1 — Lecturer opens a session

**Request:**
```http
POST /api/attendance/sessions/
Authorization: Bearer <lecturer_access_token>
Content-Type: application/json

{
    "course": 3
}
```

**Response `201 Created`:**
```json
{
    "id": 7,
    "course": 3,
    "course_code": "CSC401",
    "lecturer": 2,
    "pin": "4829",
    "created_at": "2026-05-11T22:40:00Z",
    "expires_at": "2026-05-11T22:45:00Z",
    "is_active": true,
    "record_count": 0
}
```
> The lecturer shares the PIN `"4829"` verbally (or on a projector).
> Students have **5 minutes** before the session expires.

---

### Step 2 — Student submits attendance

**Request:**
```http
POST /api/attendance/submit/
Authorization: Bearer <student_access_token>
Content-Type: application/json

{
    "course_id": 3,
    "pin": "4829"
}
```

**Response `201 Created`:**
```json
{
    "detail": "Attendance recorded successfully.",
    "record": {
        "id": 15,
        "session_id": 7,
        "course_code": "CSC401",
        "course_title": "Operating Systems",
        "student": 9,
        "student_detail": {
            "id": 9,
            "username": "joy_eze",
            "full_name": "Joy Eze",
            "role": "Student",
            "matric_number": "21/0432/ENG",
            "is_student": true,
            "is_lecturer": false
        },
        "timestamp": "2026-05-11T22:41:33Z"
    }
}
```

> **Notice:** The PIN `"4829"` is never echoed back in the response.

---

### Error Responses

| Scenario | Status | Body |
|---|---|---|
| Wrong PIN / course mismatch | `400` | `{"pin": "Invalid PIN or course. Please check and try again."}` |
| Session expired | `400` | `{"pin": "This attendance session has expired. Contact your lecturer."}` |
| Already signed in | `400` | `{"non_field_errors": ["You have already signed in to this session."]}` |
| Non-student caller | `403` | `{"detail": "Access restricted to students."}` |
| Missing token | `401` | `{"detail": "Authentication credentials were not provided."}` |

---

### Registration Example

```http
POST /api/auth/register/
Content-Type: application/json

{
    "username": "joy_eze",
    "email": "joy@university.edu",
    "first_name": "Joy",
    "last_name": "Eze",
    "password": "SecurePass#2026",
    "password_confirm": "SecurePass#2026",
    "is_student": true,
    "is_lecturer": false,
    "matric_number": "21/0432/ENG",
    "staff_id": null,
    "phone": "+2348012345678"
}
```

**Response `201 Created`:**
```json
{
    "id": 9,
    "username": "joy_eze",
    "email": "joy@university.edu",
    "full_name": "Joy Eze",
    "role": "Student",
    "is_student": true,
    "is_lecturer": false,
    "matric_number": "21/0432/ENG",
    "staff_id": null,
    "phone": "+2348012345678",
    "date_joined": "2026-05-11T22:30:00Z"
}
```

---

## 🗂️ Project Structure

```
solution-1/
├── .gitignore
├── requirements.txt
├── README.md
└── backend/
    ├── manage.py
    ├── .env.example              ← Safe template; copy to .env
    ├── db.sqlite3                ← Created after first migrate (gitignored)
    ├── media/                    ← Uploaded files (gitignored)
    │
    ├── backend/                  ← Django project package
    │   ├── settings.py           ← JWT, DRF, CORS, SQLite config
    │   ├── urls.py               ← Root URL tree
    │   └── wsgi.py
    │
    ├── users/                    ← Authentication & RBAC app
    │   ├── models.py             ← Custom User (is_student, is_lecturer)
    │   ├── serializers.py        ← JWT + registration + profile serializers
    │   ├── views.py              ← Login, logout, register, /me/ views
    │   ├── urls.py               ← Auth URL patterns
    │   └── admin.py              ← Extended UserAdmin
    │
    └── core/                     ← Domain models app
        ├── models.py             ← Course, TimetableSlot (clash guard),
        │                           Material, Notice, AttendanceSession,
        │                           AttendanceRecord
        ├── serializers.py        ← All domain serializers + PIN security
        ├── views.py              ← ModelViewSets + AttendanceSubmitView
        ├── urls.py               ← DefaultRouter + submit endpoint
        ├── permissions.py        ← IsLecturer, IsStudent, IsLecturerOrReadOnly
        └── admin.py              ← Fully-editable admin for all models
```

---

## 🔒 Security Notes

1. **JWT tokens** — Access tokens expire in 1 hour; refresh tokens in 7 days with automatic rotation and blacklisting on logout.
2. **PIN security** — The attendance PIN is `write_only` in all student-facing serializers; it is never returned in responses after submission.
3. **Double-booking** — `TimetableSlot.clean()` enforces venue overlap detection at the ORM level, not just the API.
4. **Duplicate attendance** — Enforced by a DB-level `UNIQUE(session, student)` constraint on `AttendanceRecord`.
5. **Server-set timestamps** — `AttendanceRecord.timestamp` uses `auto_now_add=True`; clients cannot spoof their sign-in time.
6. **Role assignment** — `is_lecturer` and `is_student` flags are set at registration and are not user-modifiable via the `/api/users/me/` PATCH endpoint.

---

## 🚀 Hackathon Demo Checklist

```bash
# 1. Start server
python backend/manage.py runserver

# 2. Open admin panel → create a Lecturer and a Student
open http://127.0.0.1:8000/admin/

# 3. Register via API (or use admin-created users)
# 4. Login → copy access token
# 5. Create a Course (Lecturer token)
# 6. Add a TimetableSlot — try overlapping times to see clash error
# 7. Upload a Material (multipart)
# 8. Open an AttendanceSession → note the PIN
# 9. Submit attendance as Student within 5 minutes
# 10. View the sign-in list at /api/attendance/sessions/<id>/records/
```

---

*Built for the EX-Coders University Hackathon — Django REST Framework · SimpleJWT · SQLite*
