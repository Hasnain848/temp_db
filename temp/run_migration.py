import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from db_connector import execute_query

sql = """
CREATE TABLE IF NOT EXISTS timetable_slots (
    slot_id      INT AUTO_INCREMENT PRIMARY KEY,
    section_id   INT NOT NULL,
    day_of_week  ENUM('Mon','Tue','Wed','Thu','Fri') NOT NULL,
    start_time   TIME NOT NULL,
    end_time     TIME NOT NULL,
    room         VARCHAR(50) DEFAULT '',
    CONSTRAINT fk_tt_section FOREIGN KEY (section_id)
        REFERENCES course_sections(section_id) ON DELETE CASCADE,
    CONSTRAINT uq_tt_slot UNIQUE (section_id, day_of_week, start_time)
)
"""
execute_query(sql, fetch=False)
print("timetable_slots table created successfully!")
