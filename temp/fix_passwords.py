import mysql.connector

conn = mysql.connector.connect(host='127.0.0.1', port=3306, user='root', password='1234', database='smart_campus')
cur = conn.cursor(dictionary=True)

# Update all bcrypt-hashed passwords to plaintext '1234'
cur.execute("UPDATE users SET password='1234' WHERE password LIKE '$2b$%'")
conn.commit()
print(f"Updated {cur.rowcount} users to plaintext password '1234'")

# Show all users
cur.execute("SELECT user_id, username, role, password FROM users")
rows = cur.fetchall()
print(f"\n{'ID':<5} {'Username':<15} {'Role':<10} {'Password':<10}")
print("-" * 45)
for r in rows:
    pw_display = r['password'][:10] + '...' if len(r['password']) > 10 else r['password']
    print(f"{r['user_id']:<5} {r['username']:<15} {r['role']:<10} {pw_display}")

cur.close()
conn.close()
