import sqlite3

conn = sqlite3.connect('database.db')
cursor = conn.cursor()
cursor.execute("SELECT id, name, email, password FROM customers")
rows = cursor.fetchall()

for row in rows:
    print(row)
conn.close()
