"""Final verification of all demo data."""
import mysql.connector
conn = mysql.connector.connect(host='127.0.0.1', port=3306, user='root', password='1234', database='smart_campus')
cur = conn.cursor(dictionary=True)

print("=" * 60)
print("NEXORA DEMO DATA - FINAL VERIFICATION")
print("=" * 60)

# Admin stats
print("\n-- ADMIN DASHBOARD STATS --")
for label, sql in [
    ("Students", "SELECT COUNT(*) as c FROM students"),
    ("Faculty", "SELECT COUNT(*) as c FROM faculty"),
    ("Courses", "SELECT COUNT(DISTINCT course_id) as c FROM courses"),
    ("Active Enrollments", "SELECT COUNT(*) as c FROM enrollments WHERE status='active'"),
    ("Completed Enrollments", "SELECT COUNT(*) as c FROM enrollments WHERE status='completed'"),
    ("Attendance Records", "SELECT COUNT(*) as c FROM attendance"),
    ("Grade Entries", "SELECT COUNT(*) as c FROM grades WHERE marks_obtained > 0"),
    ("Audit Logs", "SELECT COUNT(*) as c FROM audit_log"),
    ("Students with CGPA", "SELECT COUNT(*) as c FROM v_student_cgpa"),
]:
    cur.execute(sql)
    print(f"  {label:25} {cur.fetchone()['c']}")

# Ahmed's teaching load
print("\n-- FACULTY: Tariq Ahmed (f_ahmed) --")
cur.execute("""
    SELECT sm.name AS semester, c.course_code, cs.section_code,
           COUNT(CASE WHEN e.status='active' THEN 1 END) AS active,
           COUNT(CASE WHEN e.status='completed' THEN 1 END) AS completed,
           (SELECT COUNT(*) FROM attendance a2 JOIN enrollments e2 ON a2.enrollment_id=e2.enrollment_id 
            WHERE e2.section_id=cs.section_id) AS att_records
    FROM course_sections cs
    JOIN courses c ON cs.course_id=c.course_id
    JOIN semesters sm ON cs.semester_id=sm.semester_id
    LEFT JOIN enrollments e ON cs.section_id=e.section_id
    WHERE cs.faculty_id=(SELECT faculty_id FROM faculty f JOIN users u ON f.user_id=u.user_id WHERE u.username='f_ahmed')
    GROUP BY sm.name, c.course_code, cs.section_code, cs.section_id, sm.start_date
    ORDER BY sm.start_date, c.course_code
""")
for r in cur.fetchall():
    print(f"  {r['semester']:15} {r['course_code']}-{r['section_code']}  "
          f"active={r['active']:2} completed={r['completed']:2} att={r['att_records']:4}")

# Ali's data
print("\n-- STUDENT: Ali Raza (s_ali01) --")
cur.execute("""
    SELECT sm.name AS semester, c.course_code, e.status, 
           g.marks_obtained, g.letter_grade, g.grade_points,
           (SELECT COUNT(*) FROM attendance a WHERE a.enrollment_id=e.enrollment_id) AS att_count
    FROM enrollments e
    JOIN course_sections cs ON e.section_id=cs.section_id
    JOIN courses c ON cs.course_id=c.course_id
    JOIN semesters sm ON cs.semester_id=sm.semester_id
    LEFT JOIN grades g ON e.enrollment_id=g.enrollment_id
    WHERE e.student_id=(SELECT student_id FROM students s JOIN users u ON s.user_id=u.user_id WHERE u.username='s_ali01')
    ORDER BY sm.start_date, c.course_code
""")
for r in cur.fetchall():
    grade_str = f"{r['marks_obtained']:5.1f} {r['letter_grade'] or '--':2} ({r['grade_points'] or 0:.2f})" if r['marks_obtained'] else "not graded"
    print(f"  {r['semester']:15} {r['course_code']:6} {r['status']:10} {grade_str:20} att={r['att_count']}")

cur.execute("SELECT cgpa FROM v_student_cgpa WHERE student_id=(SELECT student_id FROM students s JOIN users u ON s.user_id=u.user_id WHERE u.username='s_ali01')")
cgpa = cur.fetchone()
print(f"  CGPA: {cgpa['cgpa'] if cgpa else 'N/A'}")

print("\n" + "=" * 60)
print("LOGIN CREDENTIALS (all password: 1234)")
print("=" * 60)
print("  Admin:   admin_ali  / 1234")
print("  Faculty: f_ahmed    / 1234")
print("  Student: s_ali01    / 1234")
print("=" * 60)

cur.close()
conn.close()
