import sqlite3

# Connect to SQLite database
conn = sqlite3.connect('database.db')
c = conn.cursor()

# -----------------------------
# Create 'users' table
# -----------------------------
c.execute('''
CREATE TABLE IF NOT EXISTS users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    username TEXT UNIQUE NOT NULL,
    password TEXT NOT NULL,
    role TEXT CHECK(role IN ('admin', 'librarian', 'member')) NOT NULL
)
''')

# -----------------------------
# Create 'books' table
# -----------------------------
c.execute('''
CREATE TABLE IF NOT EXISTS books (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    title TEXT NOT NULL,
    author TEXT NOT NULL,
    isbn TEXT UNIQUE NOT NULL,
    category TEXT,
    quantity INTEGER NOT NULL
)
''')

# -----------------------------
# Create 'issues' table
# -----------------------------
c.execute('''
CREATE TABLE IF NOT EXISTS issues (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    book_id INTEGER NOT NULL,
    member_id INTEGER NOT NULL,
    issue_date TEXT NOT NULL,
    due_date TEXT NOT NULL,
    return_date TEXT,
    fine INTEGER DEFAULT 0,
    FOREIGN KEY (book_id) REFERENCES books(id),
    FOREIGN KEY (member_id) REFERENCES users(id)
)
''')

# -----------------------------
# Insert default users
# -----------------------------
default_users = [
    ('admin', 'admin123', 'admin'),
    ('librarian', 'lib123', 'librarian'),
    ('member', 'mem123', 'member')
]

for username, password, role in default_users:
    try:
        c.execute("INSERT INTO users (username, password, role) VALUES (?, ?, ?)", 
                  (username, password, role))
        print(f"{role.capitalize()} user added.")
    except sqlite3.IntegrityError:
        print(f"{role.capitalize()} already exists.")

# -----------------------------
# Optional: Add sample book(s)
# -----------------------------
try:
    c.execute('''
        INSERT INTO books (title, author, isbn, category, quantity)
        VALUES (?, ?, ?, ?, ?)
    ''', ('The Great Gatsby', 'F. Scott Fitzgerald', '9780743273565', 'Fiction', 5))
    print("Sample book added.")
except sqlite3.IntegrityError:
    print("Sample book already exists or ISBN conflict.")

# Save changes and close connection
conn.commit()
conn.close()
print("Database initialized successfully.")
