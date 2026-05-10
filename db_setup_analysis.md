# 🗄️ Nexora — Database Setup: Which SQL Files Do You Need?

## Short Answer

**No, the 5 files listed in the README are NOT enough.** You need **4 additional files** run after them for the app to work fully.

---

## Complete Execution Order (9 files total)

Execute in **MySQL Workbench** in this exact order:

| # | File | Purpose | In README? |
|---|------|---------|:----------:|
| 1 | `db/schema.sql` | Creates database + 10 tables + indexes | ✅ Yes |
| 2 | `db/stored_procedures.sql` | Creates 3 stored procedures | ✅ Yes |
| 3 | `db/views.sql` | Creates 5 views | ✅ Yes |
| 4 | `db/triggers.sql` | Creates 9 triggers | ✅ Yes |
| 5 | `db/seed_data.sql` | Base seed: semesters, 8 faculty, 14 courses, ~50 students | ✅ Yes |
| 6 | `db/timetable_migration.sql` | Creates `timetable_slots` table (TABLE 11) | ❌ **Missing** |
| 7 | `db/seed_sections.sql` | Populates `course_sections` for Spring 2025, Fall 2025, Fall 2026 | ❌ **Missing** |
| 8 | `db/seed_enrollments.sql` | Populates enrollments, grades, timetable data for all semesters | ❌ **Missing** |
| 9 | `db/seed_showcase.sql` | Showcase data for demo student (Ali Raza) & faculty (Adeel Khan) — attendance, grades, history | ❌ **Missing** |

---

## Why the Extra Files Are Needed

### `timetable_migration.sql` — **CRITICAL**
- Creates the `timetable_slots` table
- The app has **timetable routes** in all 3 blueprints (`student.py`, `faculty.py`, `admin.py`) + 3 templates
- **Without this table, clicking "Timetable" in the sidebar will crash the app**

### `seed_sections.sql` — **CRITICAL**
- `seed_data.sql` creates **students, faculty, courses, and semesters** but does **NOT** populate `course_sections`
- Without sections, students can't enroll, faculty can't see courses, dashboards will be empty

### `seed_enrollments.sql` — **Important for demo**
- Populates Spring 2025 (completed with grades) + Fall 2026 (active) enrollments
- Also populates timetable slot data for Fall 2026
- Without this, transcripts/GPAs will be empty and the demo will look broken

### `seed_showcase.sql` — **Nice to have**
- Sets up a polished demo for the `s_ali01` student and `f_khan` faculty
- Gives them multi-semester history, attendance records, and grade data
- Makes the demo login credentials from the README actually show meaningful data

---

## Files You Do NOT Need to Run in Workbench

| File | Why Not |
|------|---------|
| `db/fix_grade_trigger.sql` | Already handled by `triggers.sql` (this was a one-time hotfix, now merged) |
| `db/migration_sections.sql` | **Old/obsolete** — this was for migrating from an older schema that had `courses.section`, `courses.semester`, `courses.faculty_id`. The current `schema.sql` already uses the new `course_sections` table, so this migration is irrelevant |
| `db/rebuild_db.py` | Python alternative that does everything in one script (bypasses Workbench) — use this OR the SQL files, not both |
| `db/run_migration.py` | Python migration script — also obsolete with the current schema |
| `db/queries/*.sql` | Reference queries only — not meant to be executed during setup |

---

## ⚡ Quick Setup Summary

```
MySQL Workbench → File → Open SQL Script → Execute (⚡) each:

1. schema.sql
2. stored_procedures.sql
3. views.sql
4. triggers.sql
5. seed_data.sql
6. timetable_migration.sql     ← ADD THIS
7. seed_sections.sql           ← ADD THIS
8. seed_enrollments.sql        ← ADD THIS
9. seed_showcase.sql           ← ADD THIS (optional but recommended)
```

> [!WARNING]
> If you skip files 6–8, the app will either crash on timetable pages or show empty dashboards with no course/enrollment data.
