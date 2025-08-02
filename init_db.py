import sqlite3

conn = sqlite3.connect('database.db')
cursor = conn.cursor()

cursor.execute('''
CREATE TABLE IF NOT EXISTS chefs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    email TEXT UNIQUE NOT NULL,
    password TEXT NOT NULL
)
''')

print("Chef table created.")


cursor.execute('''
CREATE TABLE IF NOT EXISTS dishes (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    chef_id INTEGER,
    name TEXT NOT NULL,
    description TEXT,
    price REAL,
    prep_time TEXT,
    image_filename TEXT,
    available INTEGER DEFAULT 1,
    FOREIGN KEY (chef_id) REFERENCES chefs(id)
)
''')
print("Dishes table created.")

# Recreate it with updated schema
cursor.execute('''
CREATE TABLE IF NOT EXISTS orders (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    customer_name TEXT NOT NULL,
    customer_email TEXT NOT NULL,
    customer_address TEXT NOT NULL,
    customer_phone TEXT NOT NULL,
    dish_id INTEGER,
    quantity INTEGER DEFAULT 1,
    status TEXT DEFAULT 'Placed',
    customer_id INTEGER REFERENCES customers(id),
    timestamp TEXT,
    FOREIGN KEY (dish_id) REFERENCES dishes(id)
)
''')
cursor.execute('''
CREATE TABLE IF NOT EXISTS customers (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    email TEXT UNIQUE NOT NULL,
    password TEXT NOT NULL
)
''')
conn.commit()
conn.close()
print("Recreated orders table with full schema.")




