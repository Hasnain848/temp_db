import mysql.connector
conn = mysql.connector.connect(host='127.0.0.1', port=3306, user='root', password='1234', database='smart_campus')
cur = conn.cursor()
cur.execute("SELECT user_id, username, role FROM users WHERE role=%s", ('admin',))
rows = cur.fetchall()
print("Admin accounts:", rows)
cur.close()
conn.close()
