import sqlite3

conn = sqlite3.connect("abhishek_management.db")
cursor = conn.cursor()

# 1. Check existing tables
cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
tables = cursor.fetchall()
print("Tables in DB:", tables)

# 2. Create `sacred_dates` table if it doesn't exist
cursor.execute("""
    CREATE TABLE IF NOT EXISTS sacred_dates (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        date TEXT NOT NULL,
        occasion TEXT NOT NULL
    )
""")

# 3. Insert sample data if table is empty
cursor.execute("SELECT COUNT(*) FROM sacred_dates")
if cursor.fetchone()[0] == 0:
    sample_data = [
        ("2025-08-19", "Pournima"),
        ("2025-08-21", "Pradosh"),
        ("2025-08-28", "Guruvar"),
        ("2025-09-02", "Ganesh Chaturthi")
    ]
    cursor.executemany("INSERT INTO sacred_dates (date, occasion) VALUES (?, ?)", sample_data)
    print("Inserted sample sacred dates.")
else:
    print("sacred_dates table already has data.")

conn.commit()
conn.close()
