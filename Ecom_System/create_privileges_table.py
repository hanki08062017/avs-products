import sqlite3

# Connect to the database
conn = sqlite3.connect('db.sqlite3')
cursor = conn.cursor()

# Create the staff_privileges table
cursor.execute('''
CREATE TABLE IF NOT EXISTS staff_privileges (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    staff_id VARCHAR(50) NOT NULL UNIQUE,
    manage_orders BOOLEAN NOT NULL DEFAULT 0,
    manage_products BOOLEAN NOT NULL DEFAULT 0,
    manage_reports BOOLEAN NOT NULL DEFAULT 0,
    manage_payments BOOLEAN NOT NULL DEFAULT 0,
    created_at DATETIME NOT NULL,
    modified_at DATETIME NOT NULL,
    FOREIGN KEY (staff_id) REFERENCES business_staff(staff_id)
)
''')

conn.commit()
conn.close()

print("Table 'staff_privileges' created successfully!")
