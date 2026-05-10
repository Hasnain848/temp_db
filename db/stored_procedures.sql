USE smart_campus;
DELIMITER $$

-- ============================================================
-- PROCEDURE 1: RegisterStudentInCourse  [UPGRADED — v2]
-- Covers: Ch.5 constraint violations, Ch.6 DML,
--         Ch.21 Concurrency control (serialization)
--
-- v2 changes vs original:
--   1. Wrapped in an explicit START TRANSACTION … COMMIT / ROLLBACK
--      so all checks + both INSERTs are atomic.
--   2. Uses SELECT … FOR UPDATE on course_sections to acquire a
--      row-level exclusive lock before reading max_capacity.
--      Any concurrent call for the same section will block here
--      until this transaction commits, preventing the "double-
--      enrollment after capacity check" race condition.
--   3. DECLARE CONTINUE HANDLER catches any unexpected SQL error,
--      rolls back, and surfaces a clean error message to the caller.
-- ============================================================
CREATE PROCEDURE RegisterStudentInCourse(
    IN  p_student_id INT,
    IN  p_section_id INT,
    OUT p_message    VARCHAR(255),
    OUT p_success    TINYINT
)
BEGIN
    -- Error handler: catches any unexpected SQL exception, rolls back,
    -- and records a safe failure response.
    DECLARE v_count              INT     DEFAULT 0;
    DECLARE v_enrolled_cnt       INT     DEFAULT 0;
    DECLARE v_capacity           INT     DEFAULT 0;
    DECLARE v_enrollment_id      INT     DEFAULT 0;
    DECLARE v_course_id          INT     DEFAULT NULL;
    DECLARE v_semester_id        INT     DEFAULT NULL;
    DECLARE v_same_course_cnt    INT     DEFAULT 0;   -- Rule 1
    DECLARE v_active_course_cnt  INT     DEFAULT 0;   -- Rule 2

    DECLARE EXIT HANDLER FOR SQLEXCEPTION
    BEGIN
        ROLLBACK;
        SET p_message = 'Unexpected database error during enrollment. Transaction rolled back.';
        SET p_success = 0;
    END;

    START TRANSACTION;

    -- Step 1: Acquire an exclusive row lock on the section row.
    -- Rationale: prevents two concurrent transactions from both
    -- reading the same enrolled count and both deciding "there is
    -- space" before either INSERT has committed.
    -- Ch.21: SELECT … FOR UPDATE — pessimistic concurrency control.
    SELECT max_capacity, course_id, semester_id
    INTO   v_capacity, v_course_id, v_semester_id
    FROM   course_sections
    WHERE  section_id = p_section_id
    FOR UPDATE;                        -- <-- serialization point

    -- Step 2: Re-read the live enrolled count (under the lock)
    SELECT COUNT(*) INTO v_enrolled_cnt
    FROM enrollments
    WHERE section_id = p_section_id
      AND status = 'active';

    -- Step 3: Check for duplicate active enrollment (same section)
    SELECT COUNT(*) INTO v_count
    FROM enrollments
    WHERE student_id = p_student_id
      AND section_id = p_section_id
      AND status = 'active';

    -- ── RULE 1 ─────────────────────────────────────────────────────────────
    -- Step 4: Check for enrollment in ANOTHER section of the SAME COURSE
    --         in the SAME SEMESTER.
    -- Without this check a student could join CS-101-A and CS-101-B in the
    -- same term, creating duplicate transcript entries and inflating CGPA.
    SELECT COUNT(*) INTO v_same_course_cnt
    FROM   enrollments   e
    JOIN   course_sections cs ON e.section_id = cs.section_id
    WHERE  e.student_id  = p_student_id
      AND  e.status       = 'active'
      AND  cs.course_id   = v_course_id
      AND  cs.semester_id = v_semester_id;
    -- ────────────────────────────────────────────────────────────────────────

    -- ── RULE 2 ─────────────────────────────────────────────────────────────
    -- Step 5: Enforce maximum of 6 active courses per semester.
    -- Count ALL active enrollments the student has in the same semester
    -- (across all courses). If already at 6, block the new one.
    SELECT COUNT(*) INTO v_active_course_cnt
    FROM   enrollments   e
    JOIN   course_sections cs ON e.section_id = cs.section_id
    WHERE  e.student_id  = p_student_id
      AND  e.status       = 'active'
      AND  cs.semester_id = v_semester_id;
    -- ────────────────────────────────────────────────────────────────────────

    IF v_count > 0 THEN
        ROLLBACK;
        SET p_message = 'Student is already enrolled in this section.';
        SET p_success = 0;

    ELSEIF v_same_course_cnt >= 1 THEN
        -- Rule 1 violation: another section of this course already active
        ROLLBACK;
        SET p_message = 'Enrollment rejected: already enrolled in another section of this course this semester.';
        SET p_success = 0;

    ELSEIF v_active_course_cnt >= 6 THEN
        -- Rule 2 violation: already at the 6-course cap for this semester
        ROLLBACK;
        SET p_message = 'Enrollment rejected: maximum of 6 active courses per semester already reached.';
        SET p_success = 0;

    ELSEIF v_enrolled_cnt >= v_capacity THEN
        ROLLBACK;
        SET p_message = 'Section is full. Enrollment not allowed.';
        SET p_success = 0;

    ELSE
        -- Step 6: Insert enrollment row
        INSERT INTO enrollments (student_id, section_id, status)
        VALUES (p_student_id, p_section_id, 'active');

        SET v_enrollment_id = LAST_INSERT_ID();

        -- Step 7: Create the companion grade placeholder atomically
        -- (both rows succeed or neither does — enforced by the transaction)
        INSERT INTO grades (enrollment_id)
        VALUES (v_enrollment_id);

        COMMIT;
        SET p_message = 'Enrollment successful.';
        SET p_success = 1;
    END IF;
END$$

-- ============================================================
-- PROCEDURE 2: CalculateStudentGPA  (unchanged)
-- Covers: Ch.6 aggregate functions, computed fields
-- Grade scale: A=4.0, A-=3.7, B+=3.3, B=3.0, B-=2.7, C+=2.3, C=2.0, F=0.0
-- Note: cgpa is no longer stored; use v_student_cgpa view for display.
--       This procedure returns the computed value via OUT param only.
-- ============================================================
CREATE PROCEDURE CalculateStudentGPA(
    IN  p_student_id INT,
    OUT p_gpa        DECIMAL(3,2)
)
BEGIN
    DECLARE v_total_points  DECIMAL(10,2) DEFAULT 0;
    DECLARE v_total_credits INT DEFAULT 0;

    SELECT
        SUM(g.grade_points * c.credit_hours),
        SUM(c.credit_hours)
    INTO v_total_points, v_total_credits
    FROM enrollments     e
    JOIN grades          g  ON e.enrollment_id = g.enrollment_id
    JOIN course_sections cs ON e.section_id   = cs.section_id
    JOIN courses         c  ON cs.course_id   = c.course_id
    WHERE e.student_id = p_student_id
      AND e.status = 'completed'
      AND g.grade_points IS NOT NULL;

    IF v_total_credits = 0 OR v_total_credits IS NULL THEN
        SET p_gpa = 0.00;
    ELSE
        SET p_gpa = ROUND(v_total_points / v_total_credits, 2);
    END IF;

    -- cgpa is no longer a stored column; result is returned via p_gpa only.
    -- Callers should read v_student_cgpa view for display purposes.
END$$

-- ============================================================
-- PROCEDURE 3: UpdateLetterGrade  (unchanged)
-- Called after marks are entered; sets letter grade + points
-- ============================================================
CREATE PROCEDURE UpdateLetterGrade(IN p_enrollment_id INT)
BEGIN
    DECLARE v_percentage DECIMAL(5,2);
    DECLARE v_letter     CHAR(2);
    DECLARE v_points     DECIMAL(3,2);

    SELECT (marks_obtained / total_marks * 100) INTO v_percentage
    FROM grades WHERE enrollment_id = p_enrollment_id;

    IF    v_percentage >= 90 THEN SET v_letter='A',  v_points=4.00;
    ELSEIF v_percentage >= 85 THEN SET v_letter='A-', v_points=3.70;
    ELSEIF v_percentage >= 80 THEN SET v_letter='B+', v_points=3.30;
    ELSEIF v_percentage >= 75 THEN SET v_letter='B',  v_points=3.00;
    ELSEIF v_percentage >= 70 THEN SET v_letter='B-', v_points=2.70;
    ELSEIF v_percentage >= 65 THEN SET v_letter='C+', v_points=2.30;
    ELSEIF v_percentage >= 60 THEN SET v_letter='C',  v_points=2.00;
    ELSE                           SET v_letter='F',  v_points=0.00;
    END IF;

    UPDATE grades
    SET letter_grade = v_letter, grade_points = v_points
    WHERE enrollment_id = p_enrollment_id;
END$$

-- ============================================================
-- PROCEDURE 4: DropEnrollment
-- Atomically marks an enrollment as 'dropped', clears any
-- uncommitted (zero) grade data, and writes an audit entry —
-- all within a single transaction with full rollback on error.
--
-- Design rationale:
--   • Status change (active → dropped) is irreversible and must be
--     consistent: if the audit INSERT fails for any reason the
--     enrollment must NOT silently remain in a half-updated state.
--   • Grade rows with marks_obtained = 0 (placeholder only, never
--     finalised) are reset to NULL to reflect no academic outcome,
--     keeping CGPA calculations clean.
--   • Graded enrollments (marks_obtained > 0) are NOT cleared —
--     the grade record is retained for transcript history; only the
--     enrollment status changes to 'dropped'.
--   • trg_enrollment_before_delete_guard prevents hard-delete of
--     graded rows, so this procedure is the correct drop path.
-- Covers: Ch.20 Explicit transactions, Ch.21 Atomicity.
-- ============================================================
CREATE PROCEDURE DropEnrollment(
    IN  p_enrollment_id  INT,
    IN  p_changed_by     INT,        -- user_id of the actor (admin/student)
    OUT p_message        VARCHAR(255),
    OUT p_success        TINYINT
)
BEGIN
    DECLARE v_current_status VARCHAR(20) DEFAULT NULL;
    DECLARE v_marks          DECIMAL(5,2) DEFAULT 0;

    DECLARE EXIT HANDLER FOR SQLEXCEPTION
    BEGIN
        ROLLBACK;
        SET p_message = 'Unexpected error during drop. Transaction rolled back.';
        SET p_success = 0;
    END;

    START TRANSACTION;

    -- Step 1: Lock the enrollment row exclusively to prevent concurrent drops
    SELECT status INTO v_current_status
    FROM enrollments
    WHERE enrollment_id = p_enrollment_id
    FOR UPDATE;                             -- serialization point

    IF v_current_status IS NULL THEN
        ROLLBACK;
        SET p_message = 'Enrollment not found.';
        SET p_success = 0;

    ELSEIF v_current_status <> 'active' THEN
        ROLLBACK;
        SET p_message = CONCAT('Cannot drop: enrollment is already "', v_current_status, '".');
        SET p_success = 0;

    ELSE
        -- Step 2: Flip status to dropped
        UPDATE enrollments
        SET status = 'dropped'
        WHERE enrollment_id = p_enrollment_id;

        -- Step 3: Clear placeholder grade only if no marks were entered
        SELECT IFNULL(marks_obtained, 0) INTO v_marks
        FROM grades
        WHERE enrollment_id = p_enrollment_id;

        IF v_marks = 0 THEN
            UPDATE grades
            SET marks_obtained = NULL,
                letter_grade   = NULL,
                grade_points   = NULL
            WHERE enrollment_id = p_enrollment_id;
        END IF;

        -- Step 4: Write an audit entry for the drop event
        INSERT INTO audit_log (table_name, record_id, action, old_value, new_value, changed_by)
        VALUES (
            'enrollments',
            p_enrollment_id,
            'UPDATE',
            'status=active',
            'status=dropped',
            p_changed_by
        );

        COMMIT;
        SET p_message = 'Enrollment dropped successfully.';
        SET p_success = 1;
    END IF;
END$$

-- ============================================================
-- PROCEDURE 5: BulkCompleteEnrollments
-- Transactionally flips all 'active' enrollments in a given
-- section to 'completed' — typically called at semester close.
--
-- Design rationale:
--   • Completing dozens of enrollments one-by-one risks partial
--     updates if the connection drops mid-way. Wrapping every
--     UPDATE in a single transaction guarantees all-or-nothing
--     semantics (Ch.20 Atomicity).
--   • SELECT … FOR UPDATE on course_sections locks the section row
--     first, preventing concurrent RegisterStudentInCourse calls
--     from adding new active enrollments while completion runs
--     (Ch.21 Serializability — prevents phantom reads).
--   • An audit entry is written per completed student so the log
--     reflects exactly when and by whom each record was closed.
--   • p_success returns the count of rows updated so callers can
--     confirm how many students were completed.
-- Covers: Ch.20 Multi-row transaction, Ch.21 Isolation/phantoms.
-- ============================================================
CREATE PROCEDURE BulkCompleteEnrollments(
    IN  p_section_id  INT,
    IN  p_changed_by  INT,         -- user_id of admin performing the action
    OUT p_completed   INT,         -- number of enrollments flipped
    OUT p_message     VARCHAR(255)
)
BEGIN
    DECLARE v_enrollment_id INT;
    DECLARE v_done          TINYINT DEFAULT 0;

    -- Cursor over all active enrollments in the section
    DECLARE cur_active CURSOR FOR
        SELECT enrollment_id
        FROM enrollments
        WHERE section_id = p_section_id
          AND status = 'active';

    DECLARE CONTINUE HANDLER FOR NOT FOUND SET v_done = 1;

    DECLARE EXIT HANDLER FOR SQLEXCEPTION
    BEGIN
        ROLLBACK;
        SET p_message = 'Unexpected error during bulk completion. All changes rolled back.';
        SET p_completed = 0;
    END;

    SET p_completed = 0;

    START TRANSACTION;

    -- Lock the section row so no new active enrollments can be inserted concurrently
    -- while the bulk-complete loop is running (prevents phantom-row problem).
    -- Ch.21: FOR UPDATE — coarse serialization on the parent section.
    SELECT section_id FROM course_sections
    WHERE section_id = p_section_id
    FOR UPDATE;

    OPEN cur_active;

    complete_loop: LOOP
        FETCH cur_active INTO v_enrollment_id;

        IF v_done = 1 THEN
            LEAVE complete_loop;
        END IF;

        -- Flip one enrollment to completed
        UPDATE enrollments
        SET status = 'completed'
        WHERE enrollment_id = v_enrollment_id;

        -- Write a per-row audit record so reviewers can see every completion
        INSERT INTO audit_log (table_name, record_id, action, old_value, new_value, changed_by)
        VALUES (
            'enrollments',
            v_enrollment_id,
            'UPDATE',
            'status=active',
            'status=completed',
            p_changed_by
        );

        SET p_completed = p_completed + 1;
    END LOOP;

    CLOSE cur_active;

    COMMIT;
    SET p_message = CONCAT(p_completed, ' enrollment(s) marked as completed.');
END$$

DELIMITER ;