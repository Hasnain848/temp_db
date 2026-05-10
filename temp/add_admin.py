import mysql.connector

conn = mysql.connector.connect(host='127.0.0.1', port=3306, user='root', password='1234', database='smart_campus')
cur = conn.cursor(dictionary=True)

# Check if admin exists
cur.execute("SELECT * FROM users WHERE role='admin'")
admins = cur.fetchall()

if not admins:
    cur.execute("INSERT INTO users (username, password, role, is_active) VALUES ('admin_ali', '1234', 'admin', 1)")
    conn.commit()
    print("✅ Admin account created: admin_ali / 1234")
else:
    print(f"Admin(s) already exist: {[a['username'] for a in admins]}")

cur.close()
conn.close()
