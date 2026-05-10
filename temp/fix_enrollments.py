"""
Enroll students in ALL of f_ahmed's sections (past + current) with
grades, attendance, and proper completed/active status.
Keeps everything consistent for admin/student/faculty views.
"""
import mysql.connector
import random

random.seed(99)

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

# ── IDs ──
ahmed_fac = q("""SELECT f.faculty_id, f.user_id FROM faculty f 
    JOIN users u ON f.user_id=u.user_id WHERE u.username='f_ahmed'""")[0]
ahmed_fid = ahmed_fac['faculty_id']
ahmed_uid = ahmed_fac['user_id']

# ── All of Ahmed's sections ──
ahmed_sections = q("""
    SELECT cs.section_id, c.course_code, c.course_name, sm.name AS sem_name,
           sm.start_date, cs.max_capacity,
           (SELECT COUNT(*) FROM enrollments e WHERE e.section_id=cs.section_id AND e.status='active') AS active_count,
           (SELECT COUNT(*) FROM enrollments e WHERE e.section_id=cs.section_id AND e.status='completed') AS completed_count
    FROM course_sections cs
    JOIN courses c ON cs.course_id=c.course_id
    JOIN semesters sm ON cs.semester_id=sm.semester_id
    WHERE cs.faculty_id=%s
    ORDER BY sm.start_date, c.course_code
""", (ahmed_fid,))

print("== Ahmed's sections BEFORE fix ==")
for s in ahmed_sections:
    print(f"  {s['sem_name']:15} | {s['course_code']:6} | sec_id={s['section_id']:3} | "
          f"active={s['active_count']}, completed={s['completed_count']}, cap={s['max_capacity']}")

# ── Get pool of students to enroll ──
all_students = q("""
    SELECT s.student_id, u.username FROM students s
    JOIN users u ON s.user_id=u.user_id
    WHERE u.is_active=1
    ORDER BY s.student_id
""")
student_ids = [s['student_id'] for s in all_students]
print(f"\n  Total students available: {len(student_ids)}")

# ── Helpers ──
def calc_grade(marks):
    if marks >= 90: return 'A', 4.00
    elif marks >= 85: return 'A-', 3.70
    elif marks >= 80: return 'B+', 3.30
    elif marks >= 75: return 'B', 3.00
    elif marks >= 70: return 'B-', 2.70
    elif marks >= 65: return 'C+', 2.30
    elif marks >= 60: return 'C', 2.00
    else: return 'F', 0.00

def enroll_student(student_id, section_id, status='active'):
    row = q("SELECT enrollment_id FROM enrollments WHERE student_id=%s AND section_id=%s",
            (student_id, section_id))
    if row:
        q("UPDATE enrollments SET status=%s WHERE enrollment_id=%s", (status, row[0]['enrollment_id']))
        return row[0]['enrollment_id']
    return qi("INSERT INTO enrollments (student_id,section_id,status) VALUES (%s,%s,%s)",
              (student_id, section_id, status))

def set_grade(enrollment_id, marks, letter, points):
    row = q("SELECT grade_id FROM grades WHERE enrollment_id=%s", (enrollment_id,))
    if row:
        q("UPDATE grades SET marks_obtained=%s, total_marks=100, letter_grade=%s, grade_points=%s WHERE enrollment_id=%s",
          (marks, letter, points, enrollment_id))
    else:
        qi("INSERT INTO grades (enrollment_id,marks_obtained,total_marks,letter_grade,grade_points) VALUES (%s,%s,100,%s,%s)",
           (enrollment_id, marks, letter, points))

def add_attendance(enrollment_id, dates, marker_uid):
    for dt in dates:
        r = random.random()
        if r < 0.78: status = 'present'
        elif r < 0.92: status = 'late'
        else: status = 'absent'
        try:
            qi("INSERT IGNORE INTO attendance (enrollment_id,class_date,status,marked_by) VALUES (%s,%s,%s,%s)",
               (enrollment_id, dt, status, marker_uid))
        except: pass

# ── Define class dates for each semester ──
spring_2025_mw = ['2025-01-20','2025-01-22','2025-01-27','2025-01-29',
                  '2025-02-03','2025-02-05','2025-02-10','2025-02-12',
                  '2025-02-17','2025-02-19','2025-02-24','2025-02-26',
                  '2025-03-03','2025-03-05','2025-03-10','2025-03-12',
                  '2025-03-17','2025-03-19','2025-03-24','2025-03-26',
                  '2025-03-31','2025-04-02','2025-04-07','2025-04-09',
                  '2025-04-14','2025-04-16']

spring_2025_tt = ['2025-01-21','2025-01-23','2025-01-28','2025-01-30',
                  '2025-02-04','2025-02-06','2025-02-11','2025-02-13',
                  '2025-02-18','2025-02-20','2025-02-25','2025-02-27',
                  '2025-03-04','2025-03-06','2025-03-11','2025-03-13',
                  '2025-03-18','2025-03-20','2025-03-25','2025-03-27',
                  '2025-04-01','2025-04-03','2025-04-08','2025-04-10',
                  '2025-04-15','2025-04-17']

fall_2025_mw = ['2025-08-25','2025-08-27','2025-09-01','2025-09-03',
                '2025-09-08','2025-09-10','2025-09-15','2025-09-17',
                '2025-09-22','2025-09-24','2025-09-29','2025-10-01',
                '2025-10-06','2025-10-08','2025-10-13','2025-10-15',
                '2025-10-20','2025-10-22','2025-10-27','2025-10-29',
                '2025-11-03','2025-11-05','2025-11-10','2025-11-12',
                '2025-11-17','2025-11-19','2025-11-24','2025-11-26']

fall_2025_tt = ['2025-08-26','2025-08-28','2025-09-02','2025-09-04',
                '2025-09-09','2025-09-11','2025-09-16','2025-09-18',
                '2025-09-23','2025-09-25','2025-09-30','2025-10-02',
                '2025-10-07','2025-10-09','2025-10-14','2025-10-16',
                '2025-10-21','2025-10-23','2025-10-28','2025-10-30',
                '2025-11-04','2025-11-06','2025-11-11','2025-11-13',
                '2025-11-18','2025-11-20']

fall_2026_mw = ['2026-09-01','2026-09-03','2026-09-08','2026-09-10',
                '2026-09-15','2026-09-17','2026-09-22','2026-09-24',
                '2026-09-29','2026-10-01','2026-10-06','2026-10-08']

fall_2026_tt = ['2026-09-02','2026-09-04','2026-09-09','2026-09-11',
                '2026-09-16','2026-09-18','2026-09-23','2026-09-25',
                '2026-09-30','2026-10-02','2026-10-07','2026-10-09']

# ── Map sections to their schedule type and semester status ──
# Ahmed teaches: Spring 2025 (MT101), Fall 2025 (CS301, MT201), Fall 2026 (CS301, MT101, CS205)
# Plus whatever other sections exist

section_config = {}
for s in ahmed_sections:
    sid = s['section_id']
    sem = s['sem_name']
    code = s['course_code']
    
    if 'Spring 2025' in sem:
        section_config[sid] = {'status': 'completed', 'dates': spring_2025_tt, 'sem': sem, 'code': code}
    elif 'Fall 2025' in sem:
        if code in ('CS301',):
            section_config[sid] = {'status': 'completed', 'dates': fall_2025_mw, 'sem': sem, 'code': code}
        else:
            section_config[sid] = {'status': 'completed', 'dates': fall_2025_tt, 'sem': sem, 'code': code}
    elif 'Fall 2026' in sem:
        if code in ('MT101',):
            section_config[sid] = {'status': 'active', 'dates': fall_2026_tt, 'sem': sem, 'code': code}
        else:
            section_config[sid] = {'status': 'active', 'dates': fall_2026_mw, 'sem': sem, 'code': code}
    else:
        section_config[sid] = {'status': 'active', 'dates': fall_2026_mw, 'sem': sem, 'code': code}

# ── Enroll students in each of Ahmed's sections ──
print("\n== Enrolling students in Ahmed's sections ==")

# Use different student subsets per section to make it realistic
# Past semesters: ~20-30 students, current: ~15-25
for s in ahmed_sections:
    sid = s['section_id']
    cfg = section_config[sid]
    already_enrolled = s['active_count'] + s['completed_count']
    
    # Target enrollment: 18-28 students
    if 'Spring 2025' in cfg['sem']:
        target = 22
    elif 'Fall 2025' in cfg['sem']:
        target = 25
    else:
        target = 20
    
    need = max(0, target - already_enrolled)
    
    # Get students NOT already in this section
    existing = q("SELECT student_id FROM enrollments WHERE section_id=%s", (sid,))
    existing_ids = {r['student_id'] for r in existing}
    available = [st for st in student_ids if st not in existing_ids]
    
    # Pick random students
    to_enroll = random.sample(available, min(need, len(available)))
    
    enrolled_count = 0
    for st_id in to_enroll:
        eid = enroll_student(st_id, sid, cfg['status'])
        
        if cfg['status'] == 'completed':
            # Completed: assign final grade with realistic distribution
            marks = round(random.gauss(75, 12), 1)
            marks = max(35, min(98, marks))
            letter, points = calc_grade(marks)
            set_grade(eid, marks, letter, points)
        else:
            # Active: partial/midterm marks
            marks = round(random.gauss(40, 8), 1)
            marks = max(10, min(50, marks))
            set_grade(eid, marks, None, None)
        
        # Add attendance
        add_attendance(eid, cfg['dates'], ahmed_uid)
        enrolled_count += 1
    
    total = already_enrolled + enrolled_count
    print(f"  {cfg['sem']:15} | {cfg['code']:6} | added {enrolled_count:2} students | total now: {total}")

conn.commit()

# ── Verify final state ──
print("\n== Ahmed's sections AFTER fix ==")
ahmed_sections_after = q("""
    SELECT cs.section_id, c.course_code, sm.name AS sem_name,
           (SELECT COUNT(*) FROM enrollments e WHERE e.section_id=cs.section_id AND e.status='active') AS active_count,
           (SELECT COUNT(*) FROM enrollments e WHERE e.section_id=cs.section_id AND e.status='completed') AS completed_count,
           (SELECT COUNT(*) FROM attendance a JOIN enrollments e ON a.enrollment_id=e.enrollment_id 
            WHERE e.section_id=cs.section_id) AS att_records
    FROM course_sections cs
    JOIN courses c ON cs.course_id=c.course_id
    JOIN semesters sm ON cs.semester_id=sm.semester_id
    WHERE cs.faculty_id=%s
    ORDER BY sm.start_date, c.course_code
""", (ahmed_fid,))

for s in ahmed_sections_after:
    print(f"  {s['sem_name']:15} | {s['course_code']:6} | "
          f"active={s['active_count']:2}, completed={s['completed_count']:2} | "
          f"attendance={s['att_records']:4}")

# ── Admin consistency check ──
print("\n== Admin-level stats ==")
total_s = q("SELECT COUNT(*) as c FROM students")[0]['c']
total_f = q("SELECT COUNT(*) as c FROM faculty")[0]['c']
total_e_active = q("SELECT COUNT(*) as c FROM enrollments WHERE status='active'")[0]['c']
total_e_completed = q("SELECT COUNT(*) as c FROM enrollments WHERE status='completed'")[0]['c']
total_att = q("SELECT COUNT(*) as c FROM attendance")[0]['c']
total_grades = q("SELECT COUNT(*) as c FROM grades WHERE marks_obtained > 0")[0]['c']
cgpa_students = q("SELECT COUNT(*) as c FROM v_student_cgpa")[0]['c']

print(f"  Students: {total_s}")
print(f"  Faculty: {total_f}")
print(f"  Active enrollments: {total_e_active}")
print(f"  Completed enrollments: {total_e_completed}")
print(f"  Attendance records: {total_att}")
print(f"  Graded entries: {total_grades}")
print(f"  Students with CGPA: {cgpa_students}")

# ── Ali check ──
ali = q("SELECT student_id FROM students s JOIN users u ON s.user_id=u.user_id WHERE u.username='s_ali01'")[0]
ali_cgpa = q("SELECT cgpa FROM v_student_cgpa WHERE student_id=%s", (ali['student_id'],))
ali_active = q("SELECT COUNT(*) as c FROM enrollments WHERE student_id=%s AND status='active'", (ali['student_id'],))[0]['c']
ali_comp = q("SELECT COUNT(*) as c FROM enrollments WHERE student_id=%s AND status='completed'", (ali['student_id'],))[0]['c']
ali_att = q("SELECT COUNT(*) as c FROM attendance a JOIN enrollments e ON a.enrollment_id=e.enrollment_id WHERE e.student_id=%s", (ali['student_id'],))[0]['c']
print(f"\n  Ali (s_ali01): CGPA={ali_cgpa[0]['cgpa'] if ali_cgpa else 'N/A'}, "
      f"active={ali_active}, completed={ali_comp}, attendance={ali_att}")

cur.close()
conn.close()
print("\n== ENROLLMENT FIX COMPLETE ==")
