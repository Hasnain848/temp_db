# 🎓 Nexora — Academic Management System

A full-stack **Academic Management System** built with **Flask + MySQL** for managing students, faculty, courses, grades, and attendance. This project demonstrates advanced database concepts including normalization (1NF–BCNF), stored procedures, triggers, views, CHECK constraints, and connection pooling.

---

## 📋 Table of Contents

- [Overview](#-overview)
- [Tech Stack](#-tech-stack)
- [3-Tier Architecture](#-3-tier-architecture)
- [Project Structure](#-project-structure)
- [Database Design](#-database-design)
- [Module Breakdown](#-module-breakdown)
- [Faculty Portal Deep Dive](#-faculty-portal-deep-dive)
- [Route Reference](#-route-reference)
- [Database Objects Reference](#-database-objects-reference)
- [Setup & Installation Guide](#-setup--installation-guide)
- [Security Features](#-security-features)
- [Normalization](#-normalization)
- [How to Improve](#-how-to-improve)
- [DBMS Syllabus Coverage](#-dbms-syllabus-coverage)
- [Team Members](#-team-members)

---

## 🌟 Overview

**Smart Campus Hub** is a role-based academic management platform with three portals:

| Portal | Users | Core Features |
|--------|-------|---------------|
| **Student Portal** | Students | View courses, enroll, check grades/attendance with semester filters, semester-grouped transcript |
| **Faculty Portal** | Professors | Manage courses, mark attendance, enter grades, view analytics |
| **Admin Portal** | Administrators | Manage users, courses, enrollment reports, GPA distribution |

### Key Highlights
- ✅ **Role-Based Access Control** — Students, Faculty, and Admin each see only their relevant data
- ✅ **Database-Level Validation** — CHECK constraints, triggers, and stored procedures enforce data integrity
- ✅ **Audit Logging** — Grade and attendance changes are tracked in an audit_log table
- ✅ **Connection Pooling** — MySQL connection pool (5 connections) for efficient resource usage
- ✅ **Premium UI** — Modern design with dark mode, micro-animations, glassmorphism effects
- ✅ **Responsive Design** — Works on desktop, tablet, and mobile
- ✅ **Normalization** — All tables in BCNF; CGPA computed via view, not stored

---

## 🛠 Tech Stack

| Layer | Technology |
|-------|-----------|
| **Backend** | Python 3.11, Flask 3.x |
| **Database** | MySQL 8.x (InnoDB engine) |
| **Connector** | `mysql-connector-python` (raw SQL, no ORM) |
| **Authentication** | `werkzeug.security` (bcrypt password hashing) |
| **Frontend** | HTML5, Vanilla CSS, Vanilla JavaScript |
| **Font** | Inter (Google Fonts) |
| **Environment** | `python-dotenv` for `.env` configuration |

---

## 🏗 3-Tier Architecture

Smart Campus Hub follows a strict **three-tier architecture**, separating concerns into Presentation, Application, and Data layers.

```
┌─────────────────────────────────────────────────────┐
│           TIER 1 — PRESENTATION LAYER               │
│              Browser (Client Side)                   │
│    HTML5 Templates + CSS Design System + JavaScript  │
│    templates/  |  static/css/  |  static/js/        │
└──────────────────────┬──────────────────────────────┘
                       │ HTTP Requests / Responses
┌──────────────────────▼──────────────────────────────┐
│           TIER 2 — APPLICATION LAYER                │
│              Flask Server (Python)                   │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐          │
│  │ auth_bp  │  │faculty_bp│  │ admin_bp │          │
│  │ (login/  │  │(courses, │  │(manage   │          │
│  │  logout) │  │ grades,  │  │ students,│          │
│  └────┬─────┘  │ attend.) │  │ faculty) │          │
│       │        └────┬─────┘  └────┬─────┘          │
│  ┌────▼─────────────▼─────────────▼─────┐          │
│  │  decorators.py — RBAC Guards         │          │
│  │  @login_required  @role_required     │          │
│  └────────────────┬─────────────────────┘          │
│  ┌────────────────▼─────────────────────┐          │
│  │  db_connector.py — Connection Pool   │          │
│  │  execute_query() / call_procedure()  │          │
│  └────────────────┬─────────────────────┘          │
└───────────────────┼─────────────────────────────────┘
                    │ MySQL Protocol (Pooled)
┌───────────────────▼─────────────────────────────────┐
│           TIER 3 — DATA LAYER                       │
│              MySQL 8.x Database                      │
│  ┌─────────┐ ┌──────────┐ ┌─────────┐ ┌──────────┐ │
│  │10 Tables│ │ 5 Views  │ │9 Triggers│ │3 Stored  │ │
│  │         │ │          │ │         │ │Procedures│ │
│  └─────────┘ └──────────┘ └─────────┘ └──────────┘ │
│  7 CHECK Constraints  |  8 Performance Indexes      │
└─────────────────────────────────────────────────────┘
```

### Tier Details

| Tier | Role | Files | Key Responsibility |
|------|------|-------|-------------------|
| **Presentation** | User Interface | `templates/`, `static/css/`, `static/js/` | Renders HTML pages, handles user interactions, dark mode, animations |
| **Application** | Business Logic | `app.py`, `blueprints/`, `decorators.py`, `db_connector.py` | Route handling, authentication, authorization, input validation, session management |
| **Data** | Persistence & Integrity | `db/schema.sql`, `db/views.sql`, `db/triggers.sql`, `db/stored_procedures.sql` | Data storage, constraints, triggers, views, stored procedures, audit logging |

### Benefits of This Architecture
- **Separation of Concerns** — UI, logic, and data are independent
- **Security** — Database never exposed directly to browser
- **Scalability** — Each tier can scale independently
- **Maintainability** — Team members work on different tiers simultaneously
- **Testability** — Each tier can be tested in isolation

---

## 📁 Project Structure

```
smart_campus/
├── app.py                    # Flask app factory, blueprint registration
├── config.py                 # DB credentials from .env
├── db_connector.py           # MySQL connection pool + query helpers
├── decorators.py             # @login_required, @role_required
├── requirements.txt          # Python dependencies
├── .env                      # Local secrets (DB_HOST, DB_USER, etc.)
│
├── blueprints/
│   ├── __init__.py
│   ├── auth.py               # Login/logout with password hashing
│   ├── student.py            # Student portal routes
│   ├── faculty.py            # Faculty portal routes (13 routes)
│   └── admin.py              # Admin portal routes
│
├── db/
│   ├── schema.sql            # 10 tables with CHECK constraints + indexes
│   ├── stored_procedures.sql # 3 stored procedures
│   ├── views.sql             # 5 SQL views
│   ├── triggers.sql          # 9 triggers (validation + audit + workload)
│   ├── seed_data.sql         # Sample data (50+ students, 14 courses)
│   └── queries/
│       ├── student_queries.sql
│       ├── faculty_queries.sql
│       └── admin_queries.sql
│
├── templates/
│   ├── base.html             # Master layout with sidebar navigation
│   ├── auth/login.html
│   ├── student/              # 6 student templates
│   ├── faculty/              # 8 faculty templates
│   └── admin/                # 6 admin templates
│
└── static/
    ├── css/style.css         # Premium design system (~1000 lines)
    └── js/main.js            # Client-side interaction logic (~300 lines)
```

---

## 🗄 Database Design

### Entity-Relationship Summary

```
users (1) ──── (1) students          [via user_id FK]
users (1) ──── (1) faculty           [via user_id FK]
courses (1) ── (M) course_sections   [catalog → many sections]
faculty (1) ── (M) course_sections   [faculty → many sections]
semesters (1) ─ (M) course_sections  [semester → many sections]
students (M) ─ (M) course_sections   [resolved via enrollments]
enrollments (1) ── (M) attendance
enrollments (1) ── (1) grades
users (1) ──── (M) audit_log         [changed_by FK]
```

### Tables (10 total)

| # | Table | Purpose | Key Constraints |
|---|-------|---------|----------------|
| 1 | `users` | Authentication & roles | `UNIQUE(username)`, `CHECK(LENGTH(username) >= 3)` |
| 2 | `students` | Student profiles | `CHECK(email LIKE '%@%')` — no stored `cgpa` column |
| 3 | `faculty` | Faculty profiles | `CHECK(email LIKE '%@%')` |
| 4 | `courses` | Course catalog only | `CHECK(credit_hours BETWEEN 1 AND 3)` |
| 5 | `semesters` | Academic semester registry | `UNIQUE(name)`, `CHECK(end_date > start_date)` |
| 6 | `course_sections` | Course offerings per semester | `UNIQUE(course_id, semester_id, section_code)` |
| 7 | `enrollments` | Student-Section junction | `UNIQUE(student_id, section_id)` |
| 8 | `attendance` | Daily attendance records | `UNIQUE(enrollment_id, class_date)` |
| 9 | `grades` | Academic grades | `CHECK(marks_obtained BETWEEN 0 AND total_marks)` |
| 10 | `audit_log` | Change tracking | Populated by triggers on grades/attendance |

---

## 📦 Module Breakdown

### 1. Authentication Module (`auth.py`)
- Login with bcrypt password verification
- Session stores `user_id`, `username`, `role`, `entity_id`
- Role-based routing to correct portal after login

### 2. Student Portal (`student.py`)
- Dashboard with enrolled courses and CGPA
- Browse and enroll in available sections (via stored procedure)
- Attendance with semester dropdown filter
- Grades with semester filter; CGPA always cumulative
- Semester-grouped transcript with per-semester GPA

### 3. Faculty Portal (`faculty.py`) — 13 Routes
- Dashboard with 4 stat cards and recent activity
- Course management, roster viewing
- Attendance marking with bulk actions
- Grade entry with live letter-grade preview
- Course analytics with grade distribution

### 4. Admin Portal (`admin.py`)
- System-wide statistics dashboard
- Student/Faculty CRUD management
- Course creation with section and semester assignment
- Reports: enrollment stats, GPA distribution, faculty workload

---

## ⭐ Faculty Portal Deep Dive

| Feature | Route | Description |
|---------|-------|-------------|
| Dashboard | `/faculty/dashboard` | Welcome banner, 4 stat cards, quick actions, recent activity |
| My Courses | `/faculty/my-courses` | Course cards with enrollment progress bars |
| Roster | `/faculty/roster/<id>` | Student list with attendance % and grade badges |
| Mark Attendance | `/faculty/attendance/<id>` | Color-coded radios, bulk actions, live counter |
| Attendance History | `/faculty/attendance/history/<id>` | Date-wise summaries, searchable records |
| Enter Grades | `/faculty/grades/<id>` | Live grade preview, unsaved changes indicator |
| Analytics | `/faculty/analytics/<id>` | Grade distribution chart, top performers, at-risk list |
| Profile | `/faculty/profile` | View/edit email, department, designation |

---

## 🔗 Route Reference

### Auth Routes
| Method | Endpoint | Function |
|--------|----------|----------|
| GET/POST | `/login` | Login page + handler |
| GET | `/logout` | Clear session |

### Student Routes (8)
| Method | Endpoint |
|--------|----------|
| GET | `/student/dashboard` |
| GET | `/student/courses` |
| POST | `/student/enroll/<id>` |
| GET | `/student/attendance` (supports `?semester=`) |
| GET | `/student/grades` (supports `?semester=`) |
| GET | `/student/transcript` |
| GET | `/student/profile` |
| POST | `/student/change-password` |

### Faculty Routes (13)
| Method | Endpoint |
|--------|----------|
| GET | `/faculty/dashboard` |
| GET | `/faculty/my-courses` |
| GET | `/faculty/roster/<id>` |
| GET | `/faculty/attendance/<id>` |
| POST | `/faculty/attendance/submit` |
| GET | `/faculty/attendance/history/<id>` |
| GET | `/faculty/grades/<id>` |
| POST | `/faculty/grades/save` |
| GET | `/faculty/analytics/<id>` |
| GET | `/faculty/profile` |
| POST | `/faculty/profile/update` |
| GET | `/faculty/api/course-students/<id>` |

### Admin Routes (8)
| Method | Endpoint |
|--------|----------|
| GET | `/admin/dashboard` |
| GET | `/admin/students` |
| POST | `/admin/students/add` |
| GET | `/admin/faculty` |
| POST | `/admin/faculty/add` |
| GET | `/admin/courses` |
| POST | `/admin/courses/create` |
| GET | `/admin/reports` |

---

## 🗃 Database Objects Reference

### Views (5)

| View | Purpose |
|------|---------|
| `v_student_transcript` | Full academic record per student |
| `v_attendance_summary` | Attendance % per enrollment per section |
| `v_course_roster` | Students enrolled per section (faculty use) |
| `v_admin_enrollment_report` | Section fill rates (admin reports) |
| `v_student_cgpa` | Computed CGPA from completed enrollments |

### Stored Procedures (3)

| Procedure | Purpose |
|-----------|---------|
| `RegisterStudentInCourse(student_id, section_id)` | Enroll with capacity + duplicate check |
| `CalculateStudentGPA(student_id)` | Compute weighted GPA |
| `UpdateLetterGrade(enrollment_id)` | Derive letter grade from marks |

### Triggers (9)

| Trigger | Purpose |
|---------|---------|
| `trg_grade_before_insert` | Validates marks range on INSERT |
| `trg_grade_before_update` | Validates marks range on UPDATE |
| `trg_grade_audit_update` | Logs grade changes to audit_log |
| `trg_attendance_audit_update` | Logs attendance changes to audit_log |
| `trg_attendance_before_insert` | Blocks future-date attendance |
| `trg_attendance_before_update` | Blocks future-date on edits |
| `trg_faculty_load_insert` | Max 6 sections per semester per faculty |
| `trg_faculty_load_update` | Max 6 sections on reassignment |

---

## 🚀 Setup & Installation Guide

### Prerequisites
- **Python 3.11+** — [Download](https://python.org/downloads)
- **MySQL 8.x** — [Download](https://dev.mysql.com/downloads/installer/)
- **MySQL Workbench** (optional, for visual management)
- **VS Code** (recommended IDE)

### Step 1: Clone & Create Virtual Environment

```bash
git clone <repository-url>
cd smart_campus

# Create virtual environment
python -m venv venv

# Activate virtual environment
venv\Scripts\activate        # Windows
# source venv/bin/activate   # macOS/Linux

# Install dependencies
pip install -r requirements.txt
```

### Step 2: Configure Environment Variables

Create a `.env` file in the project root:

```ini
DB_HOST=127.0.0.1
DB_PORT=3306
DB_USER=root
DB_PASS=your_mysql_password
DB_NAME=smart_campus
SECRET_KEY=your-secret-key-here
```

### Step 3: Set Up MySQL Database

**Option A: Using MySQL Workbench (Recommended)**

1. Open MySQL Workbench → Connect to your local MySQL server
2. Click **File → Open SQL Script** (`Ctrl+Shift+O`)
3. Execute each script in **this exact order** (click the ⚡ lightning bolt icon):
   1. `db/schema.sql` — Creates the database and all 10 tables
   2. `db/stored_procedures.sql` — Creates 3 stored procedures
   3. `db/views.sql` — Creates 5 views
   4. `db/triggers.sql` — Creates 9 triggers
   5. `db/seed_data.sql` — Populates sample data

**Option B: Using MySQL CLI**

```bash
mysql -u root -p < db/schema.sql
mysql -u root -p < db/stored_procedures.sql
mysql -u root -p < db/views.sql
mysql -u root -p < db/triggers.sql
mysql -u root -p < db/seed_data.sql
```

### Step 4: Run the Application

```bash
python app.py
```

Visit **http://127.0.0.1:5000** in your browser.

### Step 5: Test Login Credentials

| Username | Password | Role | Notes |
|----------|----------|------|-------|
| `f_ahmed` | `1234` | Faculty | Has CS101 and CS205 assigned |
| `f_mehmood` | `1234` | Faculty | Has IT220 and IS310 assigned |
| `s_ali01` | `1234` | Student | Enrolled in 3 courses |
| `admin_ali` | `1234` | Admin | Full system access |

### Troubleshooting

| Issue | Solution |
|-------|---------|
| `ModuleNotFoundError` | Run `pip install -r requirements.txt` |
| MySQL connection refused | Ensure MySQL service is running; check `.env` credentials |
| `Unknown database 'smart_campus'` | Run `db/schema.sql` first — it creates the database |
| Port 5000 in use | Change port in `app.py`: `app.run(debug=True, port=5001)` |
| Password hash mismatch | Run `python update_passwords.py` to reset passwords |

---

## 🔒 Security Features

| Feature | Implementation |
|---------|---------------|
| Password Hashing | `werkzeug.security.generate_password_hash` (bcrypt) |
| Session Auth | Flask session with server-side storage |
| Role-Based Access | `@login_required` + `@role_required` decorators |
| Course Ownership | `_owns_course()` prevents cross-faculty access |
| SQL Injection Prevention | Parameterized queries (`%s` placeholders) |
| Input Validation | Server-side + DB-level CHECK constraints |
| Audit Trail | `audit_log` populated by triggers |
| Error Handling | try/except with rollback on all DB operations |

---

## 📐 Normalization

All tables are normalized to **Boyce-Codd Normal Form (BCNF)**.

| Normal Form | How It's Achieved | Example |
|-------------|-------------------|---------|
| **1NF** | All attributes are atomic; no repeating groups | Courses per student stored in separate enrollment rows |
| **2NF** | No partial dependencies | Auth data (`users`) separated from profiles (`students`/`faculty`) |
| **3NF** | No transitive dependencies | CGPA computed via `v_student_cgpa` view, not stored |
| **BCNF** | Every determinant is a candidate key | All FDs have superkey determinants |

---

## 🚀 How to Improve

1. **CSRF Protection** — Add `flask-wtf` for CSRF tokens
2. **Password Reset** — Email-based reset via `flask-mail`
3. **Pagination** — For large student/course lists
4. **File Export** — CSV/PDF export for transcripts
5. **REST API** — `/api/v1/...` for mobile integration
6. **Docker** — Containerize with Docker + docker-compose
7. **Caching** — Redis for frequently accessed dashboards
8. **Real-Time** — Flask-SocketIO for live notifications

---

## 📖 DBMS Syllabus Coverage

| Topic | Where It Appears |
|-------|-----------------|
| Ch.1 — DB characteristics | Project uses structured relational DB vs flat files |
| Ch.2 — Three-schema architecture | External (UI), Conceptual (ERD), Internal (InnoDB) |
| Ch.3 — ER Diagram | 10 entities with 1:1, 1:M, M:N relationships |
| Ch.5 — Relational model, constraints | `schema.sql` — FK, UNIQUE, ENUM, CHECK, NOT NULL |
| Ch.6 — DDL, DML, SQL | `schema.sql` (DDL), `seed_data.sql` (DML), routes (DML) |
| Ch.7 — Complex queries, Views | `views.sql` (5 views), `queries/*.sql` (complex JOINs) |
| Ch.8 — Relational Algebra | Views implement σ, π, ⋈ operations |
| Ch.14 — Normalization (2NF–BCNF) | users/students separation (2NF), CGPA as view (3NF) |
| Ch.20 — Transactions, ACID | Stored procedures with COMMIT/ROLLBACK |
| Ch.21 — Concurrency | Connection pool, InnoDB row-level locking |
| Ch.22 — Recovery | InnoDB redo/undo logs |

---
