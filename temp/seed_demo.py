"""
Seed comprehensive demo data for 3 showcase accounts:
  - Admin:   admin_ali / 1234
  - Faculty: f_ahmed   / 1234  (Tariq Ahmed, Mathematics + CS)
  - Student: s_ali01   / 1234  (Ali Raza, BS Computer Science 2022)

Covers ALL app features:
  - Dashboard stats, enrolled courses, CGPA
  - Attendance (multi-semester, present/absent/late mix)
  - Grades with letter grades and grade points (completed + active semesters)
  - Transcript (multi-semester history)
  - Timetable slots
  - Audit log entries
  - Faculty: roster, mark attendance, enter grades, analytics (grade dist, top/at-risk)
  - Admin: reports, semester stats, enrollment report, GPA distribution
"""
import mysql.connector

conn = mysql.connector.connect(
    host='127.0.0.1', port=3306, user='root', password='1234',
    database='smart_campus'
)
cur = conn.cursor(dictionary=True)

def q(sql, params=None):
    cur.execute(sql, params or ())
    if sql.strip().upper().startswith(('SELECT','SHOW')):
        return cur.fetchall()
    return None

def qi(sql, params=None):
    cur.execute(sql, params or ())
    return cur.lastrowid

print("== Starting Demo Data Seed ==")

# ── Ensure timetable_slots table exists ──
q("""CREATE TABLE IF NOT EXISTS timetable_slots (
    slot_id INT AUTO_INCREMENT PRIMARY KEY,
    section_id INT NOT NULL,
    day_of_week ENUM('Mon','Tue','Wed','Thu','Fri') NOT NULL,
    start_time TIME NOT NULL,
    end_time TIME NOT NULL,
    room VARCHAR(50) DEFAULT '',
    CONSTRAINT fk_tt_section FOREIGN KEY (section_id)
        REFERENCES course_sections(section_id) ON DELETE CASCADE,
    CONSTRAINT uq_tt_slot UNIQUE (section_id, day_of_week, start_time)
)""")
conn.commit()

# ── Get key IDs ──
ali_user = q("SELECT user_id FROM users WHERE username='s_ali01'")
if not ali_user:
    print("ERROR: s_ali01 not found"); exit()
ali_uid = ali_user[0]['user_id']

ali_student = q("SELECT student_id FROM students WHERE user_id=%s", (ali_uid,))
if not ali_student:
    print("ERROR: student record for s_ali01 not found"); exit()
ali_sid = ali_student[0]['student_id']

ahmed_user = q("SELECT user_id FROM users WHERE username='f_ahmed'")
if not ahmed_user:
    print("ERROR: f_ahmed not found"); exit()
ahmed_uid = ahmed_user[0]['user_id']

ahmed_fac = q("SELECT faculty_id FROM faculty WHERE user_id=%s", (ahmed_uid,))
if not ahmed_fac:
    print("ERROR: faculty record for f_ahmed not found"); exit()
ahmed_fid = ahmed_fac[0]['faculty_id']

admin_user = q("SELECT user_id FROM users WHERE username='admin_ali'")
if not admin_user:
    print("ERROR: admin_ali not found"); exit()

print(f"  Ali (student_id={ali_sid}), Tariq Ahmed (faculty_id={ahmed_fid}), admin_ali OK")

# ── Ensure we have semesters ──
semesters = q("SELECT semester_id, name FROM semesters ORDER BY start_date")
sem_map = {s['name']: s['semester_id'] for s in semesters}

# Add missing semesters
for name, sd, ed, active in [
    ('Spring 2025', '2025-01-15', '2025-05-31', 0),
    ('Summer 2025', '2025-06-01', '2025-08-15', 0),
    ('Fall 2025',   '2025-08-20', '2025-12-20', 0),
    ('Fall 2026',   '2026-08-01', '2026-12-31', 1),
]:
    if name not in sem_map:
        sid = qi("INSERT INTO semesters (name,start_date,end_date,is_active) VALUES (%s,%s,%s,%s)",
                 (name, sd, ed, active))
        sem_map[name] = sid
conn.commit()

# ── Ensure courses exist ──
course_map = {}
for code, name, ch in [
    ('CS101','Introduction to Programming',3),
    ('CS205','Database Systems',3),
    ('CS301','Data Structures and Algorithms',3),
    ('CS310','Operating Systems',3),
    ('MT101','Calculus I',3),
    ('MT201','Linear Algebra',3),
    ('SE240','Software Design and Architecture',3),
    ('IT305','Network Security',3),
]:
    row = q("SELECT course_id FROM courses WHERE course_code=%s", (code,))
    if row:
        course_map[code] = row[0]['course_id']
    else:
        cid = qi("INSERT INTO courses (course_code,course_name,credit_hours) VALUES (%s,%s,%s)",
                 (code, name, ch))
        course_map[code] = cid
conn.commit()

# ── Helper: ensure section exists ──
def ensure_section(course_code, semester_name, section_code, faculty_id, capacity=40):
    cid = course_map[course_code]
    smid = sem_map[semester_name]
    row = q("SELECT section_id FROM course_sections WHERE course_id=%s AND semester_id=%s AND section_code=%s",
            (cid, smid, section_code))
    if row:
        # Assign faculty if not set
        q("UPDATE course_sections SET faculty_id=%s WHERE section_id=%s AND faculty_id IS NULL",
          (faculty_id, row[0]['section_id']))
        return row[0]['section_id']
    return qi("INSERT INTO course_sections (course_id,semester_id,faculty_id,section_code,max_capacity) VALUES (%s,%s,%s,%s,%s)",
              (cid, smid, faculty_id, section_code, capacity))

# ── Create sections taught by Tariq Ahmed (f_ahmed) ──
# Fall 2025 (completed semester) - Ahmed teaches CS301-A, MT201-A
sec_cs301_f25 = ensure_section('CS301', 'Fall 2025', 'A', ahmed_fid, 45)
sec_mt201_f25 = ensure_section('MT201', 'Fall 2025', 'A', ahmed_fid, 40)
# Also some other faculty sections for Ali's transcript
farooq_fac = q("SELECT faculty_id FROM faculty WHERE user_id=(SELECT user_id FROM users WHERE username='f_farooq')")
farooq_fid = farooq_fac[0]['faculty_id'] if farooq_fac else ahmed_fid
sec_cs205_f25 = ensure_section('CS205', 'Fall 2025', 'A', farooq_fid, 45)
sec_cs101_f25 = ensure_section('CS101', 'Fall 2025', 'A', farooq_fid, 50)

# Spring 2025 (completed semester)
sec_mt101_sp25 = ensure_section('MT101', 'Spring 2025', 'A', ahmed_fid, 40)
sec_cs101_sp25 = ensure_section('CS101', 'Spring 2025', 'A', farooq_fid, 50)

# Fall 2026 (current active semester) - Ahmed teaches CS301-A, MT101-A, CS205-A
sec_cs301_f26 = ensure_section('CS301', 'Fall 2026', 'A', ahmed_fid, 45)
sec_mt101_f26 = ensure_section('MT101', 'Fall 2026', 'A', ahmed_fid, 40)
sec_cs205_f26 = ensure_section('CS205', 'Fall 2026', 'A', ahmed_fid, 45)
sec_se240_f26 = ensure_section('SE240', 'Fall 2026', 'A', farooq_fid, 40)
sec_it305_f26 = ensure_section('IT305', 'Fall 2026', 'A', farooq_fid, 35)
conn.commit()

print("  Sections created/verified")

# ── Helper: enroll student ──
def enroll(student_id, section_id, status='active'):
    row = q("SELECT enrollment_id FROM enrollments WHERE student_id=%s AND section_id=%s",
            (student_id, section_id))
    if row:
        q("UPDATE enrollments SET status=%s WHERE enrollment_id=%s", (status, row[0]['enrollment_id']))
        return row[0]['enrollment_id']
    return qi("INSERT INTO enrollments (student_id,section_id,status) VALUES (%s,%s,%s)",
              (student_id, section_id, status))

# ── Ali's completed courses (Spring 2025) ──
e_mt101_sp25 = enroll(ali_sid, sec_mt101_sp25, 'completed')
e_cs101_sp25 = enroll(ali_sid, sec_cs101_sp25, 'completed')

# ── Ali's completed courses (Fall 2025) ──
e_cs301_f25 = enroll(ali_sid, sec_cs301_f25, 'completed')
e_mt201_f25 = enroll(ali_sid, sec_mt201_f25, 'completed')
e_cs205_f25 = enroll(ali_sid, sec_cs205_f25, 'completed')
e_cs101_f25 = enroll(ali_sid, sec_cs101_f25, 'completed')

# ── Ali's active courses (Fall 2026 - current) ──
e_cs301_f26 = enroll(ali_sid, sec_cs301_f26, 'active')
e_mt101_f26 = enroll(ali_sid, sec_mt101_f26, 'active')
e_cs205_f26 = enroll(ali_sid, sec_cs205_f26, 'active')
e_se240_f26 = enroll(ali_sid, sec_se240_f26, 'active')
conn.commit()

print("  Ali enrolled in courses across 3 semesters")

# ── Set grades for completed courses ──
def set_grade(enrollment_id, marks, letter, points):
    row = q("SELECT grade_id FROM grades WHERE enrollment_id=%s", (enrollment_id,))
    if row:
        q("UPDATE grades SET marks_obtained=%s, total_marks=100, letter_grade=%s, grade_points=%s WHERE enrollment_id=%s",
          (marks, letter, points, enrollment_id))
    else:
        qi("INSERT INTO grades (enrollment_id,marks_obtained,total_marks,letter_grade,grade_points) VALUES (%s,%s,100,%s,%s)",
           (enrollment_id, marks, letter, points))

# Spring 2025 completed grades
set_grade(e_mt101_sp25, 88.0, 'A-', 3.70)
set_grade(e_cs101_sp25, 92.0, 'A',  4.00)

# Fall 2025 completed grades
set_grade(e_cs301_f25, 91.0, 'A',  4.00)
set_grade(e_mt201_f25, 82.0, 'B+', 3.30)
set_grade(e_cs205_f25, 85.5, 'A-', 3.70)
set_grade(e_cs101_f25, 78.0, 'B',  3.00)

# Fall 2026 active - partial grades (midterm marks so far)
set_grade(e_cs301_f26, 45.0, None, None)  # midterm only
set_grade(e_mt101_f26, 38.0, None, None)
set_grade(e_cs205_f26, 42.0, None, None)
set_grade(e_se240_f26, 0, None, None)  # not graded yet
conn.commit()

print("  Grades set for Ali (6 completed + 4 active)")

# ── Enroll other students in Ahmed's Fall 2026 sections for rich faculty data ──
other_students = q("""SELECT s.student_id FROM students s 
    JOIN users u ON s.user_id=u.user_id 
    WHERE u.username IN ('s_zara02','s_ahmed03','s_sana04','s_bilal05','s_nadia06',
                         's_omar07','s_hira08','s_faisal09','s_amina10','s_imran11',
                         's_rabia12','s_kamran13','s_saima14','s_asad15')""")

import random
random.seed(42)

for i, st in enumerate(other_students):
    sid = st['student_id']
    # Enroll in CS301-A (Ahmed's section)
    eid = enroll(sid, sec_cs301_f26, 'active')
    marks = round(random.uniform(45, 96), 1)
    if marks >= 90: lg, gp = 'A', 4.00
    elif marks >= 85: lg, gp = 'A-', 3.70
    elif marks >= 80: lg, gp = 'B+', 3.30
    elif marks >= 75: lg, gp = 'B', 3.00
    elif marks >= 70: lg, gp = 'B-', 2.70
    elif marks >= 65: lg, gp = 'C+', 2.30
    elif marks >= 60: lg, gp = 'C', 2.00
    else: lg, gp = 'F', 0.00
    set_grade(eid, marks, lg, gp)
    
    # Enroll half in MT101-A too
    if i % 2 == 0:
        eid2 = enroll(sid, sec_mt101_f26, 'active')
        m2 = round(random.uniform(50, 95), 1)
        if m2 >= 90: lg2, gp2 = 'A', 4.00
        elif m2 >= 85: lg2, gp2 = 'A-', 3.70
        elif m2 >= 80: lg2, gp2 = 'B+', 3.30
        elif m2 >= 75: lg2, gp2 = 'B', 3.00
        elif m2 >= 70: lg2, gp2 = 'B-', 2.70
        elif m2 >= 65: lg2, gp2 = 'C+', 2.30
        elif m2 >= 60: lg2, gp2 = 'C', 2.00
        else: lg2, gp2 = 'F', 0.00
        set_grade(eid2, m2, lg2, gp2)

conn.commit()
print(f"  Enrolled {len(other_students)} other students in Ahmed's sections with grades")

# ── Attendance data for Ali in Fall 2026 ──
ali_att_data = [
    # CS301 (Mon/Wed) - Ahmed's class
    (e_cs301_f26, '2026-09-01', 'present'), (e_cs301_f26, '2026-09-03', 'present'),
    (e_cs301_f26, '2026-09-08', 'present'), (e_cs301_f26, '2026-09-10', 'late'),
    (e_cs301_f26, '2026-09-15', 'present'), (e_cs301_f26, '2026-09-17', 'present'),
    (e_cs301_f26, '2026-09-22', 'absent'),  (e_cs301_f26, '2026-09-24', 'present'),
    (e_cs301_f26, '2026-09-29', 'present'), (e_cs301_f26, '2026-10-01', 'present'),
    (e_cs301_f26, '2026-10-06', 'present'), (e_cs301_f26, '2026-10-08', 'late'),
    # MT101 (Tue/Thu) - Ahmed's class
    (e_mt101_f26, '2026-09-02', 'present'), (e_mt101_f26, '2026-09-04', 'present'),
    (e_mt101_f26, '2026-09-09', 'present'), (e_mt101_f26, '2026-09-11', 'present'),
    (e_mt101_f26, '2026-09-16', 'absent'),  (e_mt101_f26, '2026-09-18', 'present'),
    (e_mt101_f26, '2026-09-23', 'present'), (e_mt101_f26, '2026-09-25', 'present'),
    (e_mt101_f26, '2026-09-30', 'present'), (e_mt101_f26, '2026-10-02', 'present'),
    # CS205 (Mon/Wed) - Ahmed's class
    (e_cs205_f26, '2026-09-01', 'present'), (e_cs205_f26, '2026-09-03', 'present'),
    (e_cs205_f26, '2026-09-08', 'late'),    (e_cs205_f26, '2026-09-10', 'present'),
    (e_cs205_f26, '2026-09-15', 'present'), (e_cs205_f26, '2026-09-17', 'present'),
    (e_cs205_f26, '2026-09-22', 'present'), (e_cs205_f26, '2026-09-24', 'present'),
    # SE240 (Fri) - Farooq's class
    (e_se240_f26, '2026-09-04', 'present'), (e_se240_f26, '2026-09-11', 'present'),
    (e_se240_f26, '2026-09-18', 'absent'),  (e_se240_f26, '2026-09-25', 'present'),
    (e_se240_f26, '2026-10-02', 'present'),
]

for eid, dt, status in ali_att_data:
    try:
        qi("INSERT IGNORE INTO attendance (enrollment_id,class_date,status,marked_by) VALUES (%s,%s,%s,%s)",
           (eid, dt, status, ahmed_uid))
    except: pass
conn.commit()
print("  Ali's attendance added (33 records across 4 courses)")

# ── Attendance for OTHER students in Ahmed's CS301 Fall 2026 ──
att_dates_cs301 = ['2026-09-01','2026-09-03','2026-09-08','2026-09-10',
                   '2026-09-15','2026-09-17','2026-09-22','2026-09-24',
                   '2026-09-29','2026-10-01','2026-10-06','2026-10-08']

for st in other_students:
    sid = st['student_id']
    erow = q("SELECT enrollment_id FROM enrollments WHERE student_id=%s AND section_id=%s AND status='active'",
             (sid, sec_cs301_f26))
    if not erow: continue
    eid = erow[0]['enrollment_id']
    for dt in att_dates_cs301:
        r = random.random()
        if r < 0.75: s = 'present'
        elif r < 0.90: s = 'late'
        else: s = 'absent'
        try:
            qi("INSERT IGNORE INTO attendance (enrollment_id,class_date,status,marked_by) VALUES (%s,%s,%s,%s)",
               (eid, dt, s, ahmed_uid))
        except: pass
conn.commit()
print("  Attendance for other students in CS301-A added")

# ── Timetable slots for Fall 2026 ──
timetable_data = [
    # Ahmed's CS301-A: Mon/Wed 09:00-10:30, Room A-101
    (sec_cs301_f26, 'Mon', '09:00:00', '10:30:00', 'A-101'),
    (sec_cs301_f26, 'Wed', '09:00:00', '10:30:00', 'A-101'),
    # Ahmed's MT101-A: Tue/Thu 09:00-10:30, Room B-201
    (sec_mt101_f26, 'Tue', '09:00:00', '10:30:00', 'B-201'),
    (sec_mt101_f26, 'Thu', '09:00:00', '10:30:00', 'B-201'),
    # Ahmed's CS205-A: Mon/Wed 11:00-12:30, Room C-301
    (sec_cs205_f26, 'Mon', '11:00:00', '12:30:00', 'C-301'),
    (sec_cs205_f26, 'Wed', '11:00:00', '12:30:00', 'C-301'),
    # Farooq's SE240-A: Fri 09:00-12:00 (lab), Room Lab-1
    (sec_se240_f26, 'Fri', '09:00:00', '12:00:00', 'Lab-1'),
    # Farooq's IT305-A: Tue/Thu 14:00-15:30, Room D-102
    (sec_it305_f26, 'Tue', '14:00:00', '15:30:00', 'D-102'),
    (sec_it305_f26, 'Thu', '14:00:00', '15:30:00', 'D-102'),
]

for sec, day, st, et, room in timetable_data:
    try:
        qi("INSERT IGNORE INTO timetable_slots (section_id,day_of_week,start_time,end_time,room) VALUES (%s,%s,%s,%s,%s)",
           (sec, day, st, et, room))
    except: pass
conn.commit()
print("  Timetable slots added for Fall 2026")

# ── Audit log entries (shows system activity for admin) ──
audit_entries = [
    ('grades', 1, 'UPDATE', 'marks=0, grade=NULL', 'marks=91.0, grade=A', ahmed_uid),
    ('grades', 2, 'UPDATE', 'marks=0, grade=NULL', 'marks=82.0, grade=B+', ahmed_uid),
    ('attendance', 1, 'UPDATE', 'status=absent', 'status=present', ahmed_uid),
    ('grades', 3, 'UPDATE', 'marks=80, grade=B+', 'marks=85.5, grade=A-', ahmed_uid),
    ('attendance', 5, 'INSERT', None, 'status=present', ahmed_uid),
]

for tbl, rid, action, old, new, by in audit_entries:
    try:
        qi("INSERT INTO audit_log (table_name,record_id,action,old_value,new_value,changed_by) VALUES (%s,%s,%s,%s,%s,%s)",
           (tbl, rid, action, old, new, by))
    except: pass
conn.commit()
print("  Audit log entries added")

# ── Verify final state ──
cgpa = q("SELECT cgpa FROM v_student_cgpa WHERE student_id=%s", (ali_sid,))
print(f"\n  Ali's CGPA: {cgpa[0]['cgpa'] if cgpa else 'N/A'}")

ali_courses = q("SELECT COUNT(*) as c FROM enrollments WHERE student_id=%s AND status='active'", (ali_sid,))
print(f"  Ali's active courses: {ali_courses[0]['c']}")

ali_completed = q("SELECT COUNT(*) as c FROM enrollments WHERE student_id=%s AND status='completed'", (ali_sid,))
print(f"  Ali's completed courses: {ali_completed[0]['c']}")

ahmed_sections = q("SELECT COUNT(*) as c FROM course_sections WHERE faculty_id=%s", (ahmed_fid,))
print(f"  Ahmed's total sections: {ahmed_sections[0]['c']}")

ahmed_students = q("""SELECT COUNT(DISTINCT e.student_id) as c FROM enrollments e 
    JOIN course_sections cs ON e.section_id=cs.section_id 
    WHERE cs.faculty_id=%s AND e.status='active'""", (ahmed_fid,))
print(f"  Ahmed's active students: {ahmed_students[0]['c']}")

total_students = q("SELECT COUNT(*) as c FROM students")
total_faculty = q("SELECT COUNT(*) as c FROM faculty")
total_semesters = q("SELECT COUNT(*) as c FROM semesters")
print(f"\n  Total students: {total_students[0]['c']}")
print(f"  Total faculty: {total_faculty[0]['c']}")
print(f"  Total semesters: {total_semesters[0]['c']}")

cur.close()
conn.close()
print("\n== DEMO DATA SEED COMPLETE ==")
