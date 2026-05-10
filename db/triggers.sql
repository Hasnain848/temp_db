USE smart_campus;
DELIMITER $$

-- ============================================================
-- TRIGGER 1: Validate grades before INSERT
-- Ensures marks_obtained does not exceed total_marks
-- ============================================================
CREATE TRIGGER trg_grade_before_insert
BEFORE INSERT ON grades
FOR EACH ROW
BEGIN
    IF NEW.marks_obtained IS NOT NULL AND NEW.total_marks IS NOT NULL THEN
        IF NEW.marks_obtained < 0 OR NEW.marks_obtained > NEW.total_marks THEN
            SIGNAL SQLSTATE '45000'
            SET MESSAGE_TEXT = 'marks_obtained must be between 0 and total_marks';
        END IF;
    END IF;
END$$

-- ============================================================
-- TRIGGER 2: Validate grades before UPDATE
-- Ensures marks_obtained does not exceed total_marks
-- ============================================================
CREATE TRIGGER trg_grade_before_update
BEFORE UPDATE ON grades
FOR EACH ROW
BEGIN
    IF NEW.marks_obtained IS NOT NULL AND NEW.total_marks IS NOT NULL THEN
        IF NEW.marks_obtained < 0 OR NEW.marks_obtained > NEW.total_marks THEN
            SIGNAL SQLSTATE '45000'
            SET MESSAGE_TEXT = 'marks_obtained must be between 0 and total_marks';
        END IF;
    END IF;
END$$

-- ============================================================
-- TRIGGER 3: Auto-call UpdateLetterGrade when marks are updated
-- ** DISABLED ** — Causes MySQL error 1442: "Can't update table
-- 'grades' in stored function/trigger because it is already used
-- by statement which invoked this stored function/trigger."
-- Letter grade + grade_points are now computed in Python
-- (_compute_letter_grade) and set directly in the UPDATE/INSERT.
-- ============================================================
-- CREATE TRIGGER trg_grade_after_update
-- AFTER UPDATE ON grades
-- FOR EACH ROW
-- BEGIN
--     IF NEW.marks_obtained <> OLD.marks_obtained THEN
--         CALL UpdateLetterGrade(NEW.enrollment_id);
--     END IF;
-- END$$

-- ============================================================
-- TRIGGER 4: Audit log for grade changes
-- Tracks all modifications to student grades
-- ============================================================
CREATE TRIGGER trg_grade_audit_update
AFTER UPDATE ON grades
FOR EACH ROW
BEGIN
    INSERT INTO audit_log (table_name, record_id, action, old_value, new_value, changed_by)
    VALUES (
        'grades',
        NEW.grade_id,
        'UPDATE',
        CONCAT('marks=', OLD.marks_obtained, ', grade=', IFNULL(OLD.letter_grade, 'NULL')),
        CONCAT('marks=', NEW.marks_obtained, ', grade=', IFNULL(NEW.letter_grade, 'NULL')),
        NULL
    );
END$$

-- ============================================================
-- TRIGGER 5: Audit log for attendance changes
-- Tracks all modifications to attendance records
-- ============================================================
CREATE TRIGGER trg_attendance_audit_update
AFTER UPDATE ON attendance
FOR EACH ROW
BEGIN
    INSERT INTO audit_log (table_name, record_id, action, old_value, new_value, changed_by)
    VALUES (
        'attendance',
        NEW.attendance_id,
        'UPDATE',
        CONCAT('status=', OLD.status),
        CONCAT('status=', NEW.status),
        NEW.marked_by
    );
END$$

-- ============================================================
-- TRIGGER 6: Prevent future attendance dates on INSERT
-- Uses SIGNAL (non-deterministic CHECK not permitted in MySQL 8)
-- ============================================================
CREATE TRIGGER trg_attendance_before_insert
BEFORE INSERT ON attendance
FOR EACH ROW
BEGIN
    IF NEW.class_date > CURDATE() THEN
        SIGNAL SQLSTATE '45000'
        SET MESSAGE_TEXT = 'Cannot mark attendance for a future date';
    END IF;
END$$

-- ============================================================
-- TRIGGER 7: Prevent future attendance dates on UPDATE
-- Guards against backdating/forward-dating via UPDATE path
-- ============================================================
CREATE TRIGGER trg_attendance_before_update
BEFORE UPDATE ON attendance
FOR EACH ROW
BEGIN
    IF NEW.class_date > CURDATE() THEN
        SIGNAL SQLSTATE '45000'
        SET MESSAGE_TEXT = 'Cannot mark attendance for a future date';
    END IF;
END$$

-- ============================================================
-- TRIGGER 8: Prevent assigning a faculty member more than 6 courses
-- The limit must be updated here if config.py:MAX_COURSES_PER_FACULTY is changed.
-- ============================================================
CREATE TRIGGER trg_faculty_load_insert
BEFORE INSERT ON course_sections
FOR EACH ROW
BEGIN
    DECLARE v_count INT;
    IF NEW.faculty_id IS NOT NULL THEN
        SELECT COUNT(*) INTO v_count
        FROM course_sections
        WHERE faculty_id = NEW.faculty_id
          AND semester_id = NEW.semester_id;
        
        IF v_count >= 6 THEN
            SIGNAL SQLSTATE '45000'
            SET MESSAGE_TEXT = 'Faculty cannot be assigned more than 6 sections per semester.';
        END IF;
    END IF;
END$$

CREATE TRIGGER trg_faculty_load_update
BEFORE UPDATE ON course_sections
FOR EACH ROW
BEGIN
    DECLARE v_count INT;
    IF NEW.faculty_id IS NOT NULL AND NEW.faculty_id != OLD.faculty_id THEN
        SELECT COUNT(*) INTO v_count
        FROM course_sections
        WHERE faculty_id = NEW.faculty_id
          AND semester_id = NEW.semester_id;
        
        IF v_count >= 6 THEN
            SIGNAL SQLSTATE '45000'
            SET MESSAGE_TEXT = 'Faculty cannot be assigned more than 6 sections per semester.';
        END IF;
    END IF;
END$$

-- ============================================================
-- TRIGGER 10: Enforce section capacity at the DB layer
-- Rationale: RegisterStudentInCourse checks capacity in application
-- logic, but that check is NOT atomic — two concurrent calls can
-- both pass the SELECT COUNT(*) check before either INSERT commits.
-- This BEFORE INSERT trigger is the last line of defence: it runs
-- inside the same transaction as the INSERT, so the row count it
-- reads is always consistent with the about-to-be-committed state.
-- Covers: Ch.21 Concurrency control — trigger-enforced serialization.
-- ============================================================
CREATE TRIGGER trg_enrollment_capacity_guard
BEFORE INSERT ON enrollments
FOR EACH ROW
BEGIN
    DECLARE v_capacity     SMALLINT DEFAULT 0;
    DECLARE v_enrolled_cnt INT      DEFAULT 0;

    -- Only enforce for active enrollments; drops/completions don't fill seats
    IF NEW.status = 'active' THEN
        SELECT max_capacity INTO v_capacity
        FROM course_sections
        WHERE section_id = NEW.section_id;

        SELECT COUNT(*) INTO v_enrolled_cnt
        FROM enrollments
        WHERE section_id = NEW.section_id
          AND status = 'active';

        IF v_enrolled_cnt >= v_capacity THEN
            SIGNAL SQLSTATE '45000'
            SET MESSAGE_TEXT = 'Section capacity exceeded. Enrollment blocked by DB trigger.';
        END IF;
    END IF;
END$$

-- ============================================================
-- TRIGGER 11: Block enrollment into an inactive semester
-- Rationale: A section can exist in a past or future semester.
-- Allowing enrollments into closed/inactive semesters would corrupt
-- academic records. This trigger enforces semester state at the DB
-- layer regardless of which code path inserts the enrollment.
-- Covers: Ch.5 Integrity constraints — cross-table referential guard.
-- ============================================================
CREATE TRIGGER trg_enrollment_active_semester_check
BEFORE INSERT ON enrollments
FOR EACH ROW
BEGIN
    DECLARE v_is_active BOOLEAN DEFAULT FALSE;

    SELECT sm.is_active INTO v_is_active
    FROM course_sections cs
    JOIN semesters sm ON cs.semester_id = sm.semester_id
    WHERE cs.section_id = NEW.section_id;

    IF v_is_active = FALSE THEN
        SIGNAL SQLSTATE '45000'
        SET MESSAGE_TEXT = 'Cannot enroll: the target semester is not currently active.';
    END IF;
END$$

-- ============================================================
-- TRIGGER 12: Audit grade INSERT events
-- Rationale: trg_grade_audit_update already covers UPDATE, but the
-- initial grade row is created by INSERT (empty placeholder in
-- RegisterStudentInCourse). Auditing the INSERT closes the gap,
-- giving a complete, tamper-evident grade lifecycle in audit_log.
-- Covers: Ch.20 Transaction processing — full audit trail.
-- ============================================================
CREATE TRIGGER trg_grade_after_insert_audit
AFTER INSERT ON grades
FOR EACH ROW
BEGIN
    INSERT INTO audit_log (table_name, record_id, action, old_value, new_value, changed_by)
    VALUES (
        'grades',
        NEW.grade_id,
        'INSERT',
        NULL,
        CONCAT('enrollment_id=', NEW.enrollment_id,
               ', marks=', IFNULL(NEW.marks_obtained, 'NULL'),
               ', grade=', IFNULL(NEW.letter_grade, 'NULL')),
        NULL   -- changed_by not available at INSERT time; set by application layer
    );
END$$

-- ============================================================
-- TRIGGER 13: Audit enrollment status changes
-- Rationale: enrollment.status transitions (active → dropped,
-- active → completed) are irreversible academic events. Logging
-- them gives advisors and admins a full history of every drop/
-- completion without needing application-layer bookkeeping.
-- Covers: Ch.20 Audit logging, Ch.7 Data integrity.
-- ============================================================
CREATE TRIGGER trg_enrollment_after_update_audit
AFTER UPDATE ON enrollments
FOR EACH ROW
BEGIN
    -- Only log when status actually changes — avoids noise from no-op updates
    IF OLD.status <> NEW.status THEN
        INSERT INTO audit_log (table_name, record_id, action, old_value, new_value, changed_by)
        VALUES (
            'enrollments',
            NEW.enrollment_id,
            'UPDATE',
            CONCAT('status=', OLD.status,
                   ', student_id=', OLD.student_id,
                   ', section_id=', OLD.section_id),
            CONCAT('status=', NEW.status,
                   ', student_id=', NEW.student_id,
                   ', section_id=', NEW.section_id),
            NULL
        );
    END IF;
END$$

-- ============================================================
-- TRIGGER 14: Guard against hard-deleting a graded enrollment
-- Rationale: An enrollment row with a non-null, non-zero grade
-- represents a permanent academic record. Hard deletion (as opposed
-- to a status change to 'dropped') would silently destroy that
-- record and break CGPA calculations. This trigger raises an error
-- to force callers through the proper DropEnrollment procedure.
-- Covers: Ch.5 Integrity constraints — business-rule enforcement.
-- ============================================================
CREATE TRIGGER trg_enrollment_before_delete_guard
BEFORE DELETE ON enrollments
FOR EACH ROW
BEGIN
    DECLARE v_has_grade TINYINT DEFAULT 0;

    SELECT COUNT(*) INTO v_has_grade
    FROM grades
    WHERE enrollment_id = OLD.enrollment_id
      AND (marks_obtained IS NOT NULL AND marks_obtained > 0);

    IF v_has_grade > 0 THEN
        SIGNAL SQLSTATE '45000'
        SET MESSAGE_TEXT = 'Cannot hard-delete an enrollment that already has grade data. Use DropEnrollment procedure instead.';
    END IF;
END$$

-- ============================================================
-- TRIGGER 15: Prevent enrollment in multiple sections of the same
--             course within the same semester
--
-- Rationale: The schema allows many sections per course per semester
-- (course_sections). A student should attend exactly one section of
-- a given course in a given term. Without this guard a student could
-- bypass the application layer (e.g. via a direct INSERT or a future
-- admin tool) and end up enrolled in two sections of CS-101 in the
-- same semester, corrupting transcript and CGPA data.
--
-- How it works: Given the section the student is trying to join,
-- look up that section's (course_id, semester_id). Then count how
-- many *active* enrollments the student already has in *any* section
-- of that same course+semester pair. If the count is >= 1, block.
--
-- Covers: Ch.5 Business-rule integrity constraints,
--         Ch.6 Cross-table referential validation.
-- ============================================================
CREATE TRIGGER trg_enrollment_no_duplicate_course_in_semester
BEFORE INSERT ON enrollments
FOR EACH ROW
BEGIN
    DECLARE v_course_id        INT DEFAULT NULL;
    DECLARE v_semester_id      INT DEFAULT NULL;
    DECLARE v_existing_sections INT DEFAULT 0;

    -- Only apply to active enrollments (drops/completions are historical)
    IF NEW.status = 'active' THEN
        -- Resolve the course and semester that the target section belongs to
        SELECT cs.course_id, cs.semester_id
        INTO   v_course_id, v_semester_id
        FROM   course_sections cs
        WHERE  cs.section_id = NEW.section_id;

        -- Count active enrollments for this student in any section of
        -- the same course during the same semester
        SELECT COUNT(*) INTO v_existing_sections
        FROM   enrollments   e
        JOIN   course_sections cs ON e.section_id = cs.section_id
        WHERE  e.student_id  = NEW.student_id
          AND  e.status       = 'active'
          AND  cs.course_id   = v_course_id
          AND  cs.semester_id = v_semester_id;

        IF v_existing_sections >= 1 THEN
            SIGNAL SQLSTATE '45000'
            SET MESSAGE_TEXT = 'Enrollment rejected: student is already enrolled in another section of this course in the same semester.';
        END IF;
    END IF;
END$$

-- ============================================================
-- TRIGGER 16: Cap a student at 6 active enrollments per semester
--
-- Rationale: Academic policy limits each student to 6 courses per
-- term. Without a DB-level guard, a student could accumulate more
-- than 6 active enrollments across multiple sections/courses if:
--   (a) the application check is absent or bypassed, or
--   (b) an admin inserts rows directly via SQL.
--
-- How it works: Resolve the semester of the target section, then
-- count all active enrollments the student has in any section whose
-- semester matches. Block if the count is already >= 6.
--
-- Note: only active enrollments count — dropped or completed rows
-- do not consume a "course slot" for the current term.
--
-- Covers: Ch.5 Business-rule integrity constraints,
--         Ch.21 Consistency enforcement across concurrent sessions.
-- ============================================================
CREATE TRIGGER trg_enrollment_max_courses_per_semester
BEFORE INSERT ON enrollments
FOR EACH ROW
BEGIN
    DECLARE v_semester_id    INT DEFAULT NULL;
    DECLARE v_active_courses INT DEFAULT 0;

    IF NEW.status = 'active' THEN
        -- Find the semester that contains the target section
        SELECT semester_id INTO v_semester_id
        FROM   course_sections
        WHERE  section_id = NEW.section_id;

        -- Count distinct active course enrollments for this student
        -- in the same semester (join through course_sections to get semester)
        SELECT COUNT(*) INTO v_active_courses
        FROM   enrollments   e
        JOIN   course_sections cs ON e.section_id = cs.section_id
        WHERE  e.student_id  = NEW.student_id
          AND  e.status       = 'active'
          AND  cs.semester_id = v_semester_id;

        IF v_active_courses >= 6 THEN
            SIGNAL SQLSTATE '45000'
            SET MESSAGE_TEXT = 'Enrollment rejected: student has reached the maximum of 6 active courses per semester.';
        END IF;
    END IF;
END$$

DELIMITER ;