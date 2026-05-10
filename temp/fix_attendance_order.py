"""Fix: Add attendance for completed semesters + fix view to include start_date for ordering."""
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

# ── Get Ali's IDs ──
ali = q("SELECT s.student_id, s.user_id FROM students s JOIN users u ON s.user_id=u.user_id WHERE u.username='s_ali01'")[0]
ali_sid = ali['student_id']

ahmed = q("SELECT f.faculty_id, f.user_id FROM faculty f JOIN users u ON f.user_id=u.user_id WHERE u.username='f_ahmed'")[0]
ahmed_uid = ahmed['user_id']

farooq = q("SELECT f.faculty_id, f.user_id FROM faculty f JOIN users u ON f.user_id=u.user_id WHERE u.username='f_farooq'")
farooq_uid = farooq[0]['user_id'] if farooq else ahmed_uid

print("== Adding attendance for completed semesters ==")

# ── Get Ali's enrollment IDs for completed courses ──
completed = q("""
    SELECT e.enrollment_id, e.section_id, c.course_code, sm.name AS sem_name, cs.faculty_id
    FROM enrollments e
    JOIN course_sections cs ON e.section_id = cs.section_id
    JOIN courses c ON cs.course_id = c.course_id
    JOIN semesters sm ON cs.semester_id = sm.semester_id
    WHERE e.student_id = %s AND e.status = 'completed'
    ORDER BY sm.start_date, c.course_code
""", (ali_sid,))

for row in completed:
    print(f"  {row['sem_name']} - {row['course_code']} (enrollment {row['enrollment_id']})")

# ── Spring 2025 attendance (Jan-May 2025) ──
# MT101 Spring 2025 (Tue/Thu)
mt101_sp25 = [r for r in completed if r['course_code']=='MT101' and 'Spring 2025' in r['sem_name']]
if mt101_sp25:
    eid = mt101_sp25[0]['enrollment_id']
    fuid = ahmed_uid
    att_data = [
        (eid,'2025-01-21','present',fuid),(eid,'2025-01-23','present',fuid),
        (eid,'2025-01-28','present',fuid),(eid,'2025-01-30','late',fuid),
        (eid,'2025-02-04','present',fuid),(eid,'2025-02-06','present',fuid),
        (eid,'2025-02-11','present',fuid),(eid,'2025-02-13','absent',fuid),
        (eid,'2025-02-18','present',fuid),(eid,'2025-02-20','present',fuid),
        (eid,'2025-02-25','present',fuid),(eid,'2025-02-27','present',fuid),
        (eid,'2025-03-04','present',fuid),(eid,'2025-03-06','late',fuid),
        (eid,'2025-03-11','present',fuid),(eid,'2025-03-13','present',fuid),
        (eid,'2025-03-18','present',fuid),(eid,'2025-03-20','present',fuid),
        (eid,'2025-03-25','absent',fuid), (eid,'2025-03-27','present',fuid),
        (eid,'2025-04-01','present',fuid),(eid,'2025-04-03','present',fuid),
        (eid,'2025-04-08','present',fuid),(eid,'2025-04-10','present',fuid),
        (eid,'2025-04-15','present',fuid),(eid,'2025-04-17','late',fuid),
        (eid,'2025-04-22','present',fuid),(eid,'2025-04-24','present',fuid),
    ]
    for a in att_data:
        try: qi("INSERT IGNORE INTO attendance (enrollment_id,class_date,status,marked_by) VALUES (%s,%s,%s,%s)", a)
        except: pass
    print(f"    MT101 Spring 2025: {len(att_data)} attendance records")

# CS101 Spring 2025 (Mon/Wed)
cs101_sp25 = [r for r in completed if r['course_code']=='CS101' and 'Spring 2025' in r['sem_name']]
if cs101_sp25:
    eid = cs101_sp25[0]['enrollment_id']
    fuid = farooq_uid
    att_data = [
        (eid,'2025-01-20','present',fuid),(eid,'2025-01-22','present',fuid),
        (eid,'2025-01-27','present',fuid),(eid,'2025-01-29','present',fuid),
        (eid,'2025-02-03','late',fuid),   (eid,'2025-02-05','present',fuid),
        (eid,'2025-02-10','present',fuid),(eid,'2025-02-12','present',fuid),
        (eid,'2025-02-17','present',fuid),(eid,'2025-02-19','absent',fuid),
        (eid,'2025-02-24','present',fuid),(eid,'2025-02-26','present',fuid),
        (eid,'2025-03-03','present',fuid),(eid,'2025-03-05','present',fuid),
        (eid,'2025-03-10','present',fuid),(eid,'2025-03-12','present',fuid),
        (eid,'2025-03-17','late',fuid),   (eid,'2025-03-19','present',fuid),
        (eid,'2025-03-24','present',fuid),(eid,'2025-03-26','present',fuid),
        (eid,'2025-03-31','present',fuid),(eid,'2025-04-02','present',fuid),
        (eid,'2025-04-07','present',fuid),(eid,'2025-04-09','present',fuid),
        (eid,'2025-04-14','present',fuid),(eid,'2025-04-16','present',fuid),
    ]
    for a in att_data:
        try: qi("INSERT IGNORE INTO attendance (enrollment_id,class_date,status,marked_by) VALUES (%s,%s,%s,%s)", a)
        except: pass
    print(f"    CS101 Spring 2025: {len(att_data)} attendance records")

# ── Fall 2025 attendance (Aug-Dec 2025) ──
# CS301 Fall 2025 (Mon/Wed) - Ahmed
cs301_f25 = [r for r in completed if r['course_code']=='CS301' and 'Fall 2025' in r['sem_name']]
if cs301_f25:
    eid = cs301_f25[0]['enrollment_id']
    fuid = ahmed_uid
    att_data = [
        (eid,'2025-08-25','present',fuid),(eid,'2025-08-27','present',fuid),
        (eid,'2025-09-01','present',fuid),(eid,'2025-09-03','present',fuid),
        (eid,'2025-09-08','present',fuid),(eid,'2025-09-10','late',fuid),
        (eid,'2025-09-15','present',fuid),(eid,'2025-09-17','present',fuid),
        (eid,'2025-09-22','present',fuid),(eid,'2025-09-24','absent',fuid),
        (eid,'2025-09-29','present',fuid),(eid,'2025-10-01','present',fuid),
        (eid,'2025-10-06','present',fuid),(eid,'2025-10-08','present',fuid),
        (eid,'2025-10-13','present',fuid),(eid,'2025-10-15','present',fuid),
        (eid,'2025-10-20','late',fuid),   (eid,'2025-10-22','present',fuid),
        (eid,'2025-10-27','present',fuid),(eid,'2025-10-29','present',fuid),
        (eid,'2025-11-03','present',fuid),(eid,'2025-11-05','present',fuid),
        (eid,'2025-11-10','present',fuid),(eid,'2025-11-12','present',fuid),
        (eid,'2025-11-17','absent',fuid), (eid,'2025-11-19','present',fuid),
        (eid,'2025-11-24','present',fuid),(eid,'2025-11-26','present',fuid),
    ]
    for a in att_data:
        try: qi("INSERT IGNORE INTO attendance (enrollment_id,class_date,status,marked_by) VALUES (%s,%s,%s,%s)", a)
        except: pass
    print(f"    CS301 Fall 2025: {len(att_data)} attendance records")

# MT201 Fall 2025 (Tue/Thu) - Ahmed
mt201_f25 = [r for r in completed if r['course_code']=='MT201' and 'Fall 2025' in r['sem_name']]
if mt201_f25:
    eid = mt201_f25[0]['enrollment_id']
    fuid = ahmed_uid
    att_data = [
        (eid,'2025-08-26','present',fuid),(eid,'2025-08-28','present',fuid),
        (eid,'2025-09-02','present',fuid),(eid,'2025-09-04','late',fuid),
        (eid,'2025-09-09','present',fuid),(eid,'2025-09-11','present',fuid),
        (eid,'2025-09-16','present',fuid),(eid,'2025-09-18','present',fuid),
        (eid,'2025-09-23','absent',fuid), (eid,'2025-09-25','present',fuid),
        (eid,'2025-09-30','present',fuid),(eid,'2025-10-02','present',fuid),
        (eid,'2025-10-07','present',fuid),(eid,'2025-10-09','present',fuid),
        (eid,'2025-10-14','present',fuid),(eid,'2025-10-16','late',fuid),
        (eid,'2025-10-21','present',fuid),(eid,'2025-10-23','present',fuid),
        (eid,'2025-10-28','present',fuid),(eid,'2025-10-30','present',fuid),
        (eid,'2025-11-04','present',fuid),(eid,'2025-11-06','present',fuid),
        (eid,'2025-11-11','absent',fuid), (eid,'2025-11-13','present',fuid),
        (eid,'2025-11-18','present',fuid),(eid,'2025-11-20','present',fuid),
    ]
    for a in att_data:
        try: qi("INSERT IGNORE INTO attendance (enrollment_id,class_date,status,marked_by) VALUES (%s,%s,%s,%s)", a)
        except: pass
    print(f"    MT201 Fall 2025: {len(att_data)} attendance records")

# CS205 Fall 2025 (Mon/Wed) - Farooq
cs205_f25 = [r for r in completed if r['course_code']=='CS205' and 'Fall 2025' in r['sem_name']]
if cs205_f25:
    eid = cs205_f25[0]['enrollment_id']
    fuid = farooq_uid
    att_data = [
        (eid,'2025-08-25','present',fuid),(eid,'2025-08-27','present',fuid),
        (eid,'2025-09-01','present',fuid),(eid,'2025-09-03','present',fuid),
        (eid,'2025-09-08','late',fuid),   (eid,'2025-09-10','present',fuid),
        (eid,'2025-09-15','present',fuid),(eid,'2025-09-17','present',fuid),
        (eid,'2025-09-22','present',fuid),(eid,'2025-09-24','present',fuid),
        (eid,'2025-09-29','absent',fuid), (eid,'2025-10-01','present',fuid),
        (eid,'2025-10-06','present',fuid),(eid,'2025-10-08','present',fuid),
        (eid,'2025-10-13','present',fuid),(eid,'2025-10-15','present',fuid),
        (eid,'2025-10-20','present',fuid),(eid,'2025-10-22','present',fuid),
        (eid,'2025-10-27','late',fuid),   (eid,'2025-10-29','present',fuid),
        (eid,'2025-11-03','present',fuid),(eid,'2025-11-05','present',fuid),
        (eid,'2025-11-10','present',fuid),(eid,'2025-11-12','present',fuid),
    ]
    for a in att_data:
        try: qi("INSERT IGNORE INTO attendance (enrollment_id,class_date,status,marked_by) VALUES (%s,%s,%s,%s)", a)
        except: pass
    print(f"    CS205 Fall 2025: {len(att_data)} attendance records")

# CS101 Fall 2025 (Tue/Thu) - Farooq
cs101_f25 = [r for r in completed if r['course_code']=='CS101' and 'Fall 2025' in r['sem_name']]
if cs101_f25:
    eid = cs101_f25[0]['enrollment_id']
    fuid = farooq_uid
    att_data = [
        (eid,'2025-08-26','present',fuid),(eid,'2025-08-28','present',fuid),
        (eid,'2025-09-02','present',fuid),(eid,'2025-09-04','present',fuid),
        (eid,'2025-09-09','present',fuid),(eid,'2025-09-11','present',fuid),
        (eid,'2025-09-16','late',fuid),   (eid,'2025-09-18','present',fuid),
        (eid,'2025-09-23','present',fuid),(eid,'2025-09-25','absent',fuid),
        (eid,'2025-09-30','present',fuid),(eid,'2025-10-02','present',fuid),
        (eid,'2025-10-07','present',fuid),(eid,'2025-10-09','present',fuid),
        (eid,'2025-10-14','present',fuid),(eid,'2025-10-16','present',fuid),
        (eid,'2025-10-21','present',fuid),(eid,'2025-10-23','present',fuid),
        (eid,'2025-10-28','late',fuid),   (eid,'2025-10-30','present',fuid),
        (eid,'2025-11-04','present',fuid),(eid,'2025-11-06','present',fuid),
        (eid,'2025-11-11','present',fuid),(eid,'2025-11-13','present',fuid),
    ]
    for a in att_data:
        try: qi("INSERT IGNORE INTO attendance (enrollment_id,class_date,status,marked_by) VALUES (%s,%s,%s,%s)", a)
        except: pass
    print(f"    CS101 Fall 2025: {len(att_data)} attendance records")

conn.commit()

# ── Fix views: add start_date for chronological ordering ──
print("\n== Updating views to include semester start_date ==")

cur.execute("""CREATE OR REPLACE VIEW v_student_transcript AS
    SELECT s.student_id, CONCAT(s.first_name,' ',s.last_name) AS student_name,
           c.course_code, c.course_name, c.credit_hours, cs.section_code,
           sm.name AS semester_name, sm.start_date AS semester_start,
           g.marks_obtained, g.total_marks,
           g.letter_grade, g.grade_points, e.status AS enrollment_status, e.enrolled_at
    FROM students s JOIN enrollments e ON s.student_id=e.student_id
    JOIN course_sections cs ON e.section_id=cs.section_id
    JOIN courses c ON cs.course_id=c.course_id
    JOIN semesters sm ON cs.semester_id=sm.semester_id
    LEFT JOIN grades g ON e.enrollment_id=g.enrollment_id""")

cur.execute("""CREATE OR REPLACE VIEW v_attendance_summary AS
    SELECT e.enrollment_id, e.student_id, e.section_id, c.course_name,
           cs.section_code, sm.name AS semester_name, sm.start_date AS semester_start,
           COUNT(a.attendance_id) AS total_classes,
           SUM(CASE WHEN a.status='present' THEN 1 ELSE 0 END) AS classes_attended,
           ROUND(SUM(CASE WHEN a.status='present' THEN 1 ELSE 0 END)
                 /NULLIF(COUNT(a.attendance_id),0)*100,2) AS attendance_percentage
    FROM enrollments e JOIN course_sections cs ON e.section_id=cs.section_id
    JOIN courses c ON cs.course_id=c.course_id
    JOIN semesters sm ON cs.semester_id=sm.semester_id
    LEFT JOIN attendance a ON e.enrollment_id=a.enrollment_id
    GROUP BY e.enrollment_id, e.student_id, e.section_id, c.course_name, 
             cs.section_code, sm.name, sm.start_date""")

conn.commit()
print("  Views updated with semester_start column")

# ── Verify ──
att_count = q("SELECT COUNT(*) as c FROM attendance a JOIN enrollments e ON a.enrollment_id=e.enrollment_id WHERE e.student_id=%s", (ali_sid,))
print(f"\n  Ali's total attendance records: {att_count[0]['c']}")

transcript = q("SELECT semester_name, course_code, enrollment_status FROM v_student_transcript WHERE student_id=%s ORDER BY semester_start, course_code", (ali_sid,))
print("  Transcript order (chronological):")
for r in transcript:
    print(f"    {r['semester_name']} | {r['course_code']} | {r['enrollment_status']}")

cur.close()
conn.close()
print("\n== FIX COMPLETE ==")
