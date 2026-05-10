import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from db_connector import execute_query

# Reset all user passwords to plaintext 'pass123' for development
execute_query(
    "UPDATE users SET password = %s",
    ('pass123',),
    fetch=False
)
print("All user passwords reset to 'pass123'")
