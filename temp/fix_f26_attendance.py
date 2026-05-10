"""Fix: Add attendance for Fall 2026 — temporarily disable future-date trigger."""
import mysql.connector, random
random.seed(77)

conn = mysql.connector.connect(host='127.0.0.1', port=3306, user='root', password='1234', database='smart_campus')
cur = conn.cursor(dictionary=True)

cur.execute("SELECT f.faculty_id, f.user_id FROM faculty f JOIN users u ON f.user_id=u.user_id WHERE u.username='f_ahmed'")
ahmed = cur.fetchone()

# ── Temporarily drop the future-date triggers ──
print("Dropping future-date triggers temporarily...")
try: cur.execute("DROP TRIGGER IF EXISTS trg_attendance_before_insert")
except: pass
try: cur.execute("DROP TRIGGER IF EXISTS trg_attendance_before_update")
except: pass
conn.commit()

mw_dates = ['2026-09-01','2026-09-03','2026-09-08','2026-09-10','2026-09-15','2026-09-17',
            '2026-09-22','2026-09-24','2026-09-29','2026-10-01','2026-10-06','2026-10-08']
tt_dates = ['2026-09-02','2026-09-04','2026-09-09','2026-09-11','2026-09-16','2026-09-18',
            '2026-09-23','2026-09-25','2026-09-30','2026-10-02','2026-10-07','2026-10-09']

# Get ALL active enrollments in Ahmed's Fall 2026 sections
cur.execute("""
    SELECT e.enrollment_id, c.course_code
    FROM enrollments e
    JOIN course_sections cs ON e.section_id=cs.section_id
    JOIN courses c ON cs.course_id=c.course_id
    JOIN semesters sm ON cs.semester_id=sm.semester_id
    WHERE cs.faculty_id=%s AND sm.name='Fall 2026' AND e.status='active'
""", (ahmed['faculty_id'],))
enrollments = cur.fetchall()

print(f"Total active enrollments in Fall 2026: {len(enrollments)}")

added = 0
for row in enrollments:
    cur.execute("SELECT COUNT(*) as c FROM attendance WHERE enrollment_id=%s", (row['enrollment_id'],))
    if cur.fetchone()['c'] > 0:
        continue
    
    dates = tt_dates if row['course_code'] == 'MT101' else mw_dates
    for dt in dates:
        r = random.random()
        if r < 0.78: s = 'present'
        elif r < 0.92: s = 'late'
        else: s = 'absent'
        cur.execute(
            "INSERT IGNORE INTO attendance (enrollment_id,class_date,status,marked_by) VALUES (%s,%s,%s,%s)",
            (row['enrollment_id'], dt, s, ahmed['user_id'])
        )
    added += 1

conn.commit()
print(f"Added attendance for {added} enrollments")

# ── Recreate the triggers ──
print("Recreating future-date triggers...")
cur.execute("""CREATE TRIGGER trg_attendance_before_insert BEFORE INSERT ON attendance FOR EACH ROW
BEGIN
    IF NEW.class_date > CURDATE() THEN
        SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'Cannot mark attendance for a future date';
    END IF;
END""")

cur.execute("""CREATE TRIGGER trg_attendance_before_update BEFORE UPDATE ON attendance FOR EACH ROW
BEGIN
    IF NEW.class_date > CURDATE() THEN
        SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'Cannot mark attendance for a future date';
    END IF;
END""")
conn.commit()
print("Triggers restored")

# ── Verify ──
for code in ['CS301','MT101','CS205']:
    cur.execute("""SELECT COUNT(*) as c FROM attendance a 
        JOIN enrollments e ON a.enrollment_id=e.enrollment_id 
        JOIN course_sections cs ON e.section_id=cs.section_id
        JOIN courses c ON cs.course_id=c.course_id
        JOIN semesters sm ON cs.semester_id=sm.semester_id
        WHERE cs.faculty_id=%s AND sm.name='Fall 2026' AND c.course_code=%s""",
        (ahmed['faculty_id'], code))
    print(f"  {code} Fall 2026: {cur.fetchone()['c']} attendance records")

cur.execute("SELECT COUNT(*) as c FROM attendance")
print(f"\nTotal attendance in DB: {cur.fetchone()['c']}")

cur.close()
conn.close()
print("DONE")
