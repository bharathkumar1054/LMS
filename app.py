from flask import Flask, render_template, request, redirect, session, flash
import sqlite3

app = Flask(__name__)
app.secret_key = 'your_secret_key'

DATABASE = 'database.db'

# Helper to connect to DB
def get_db():
    return sqlite3.connect(DATABASE)

# -------------------------
# 1. Role Selection & Login
# -------------------------

@app.route('/')
def home():
    return render_template('index.html')

@app.route('/login/<role>')
def show_login(role):
    if role not in ['admin', 'librarian', 'member']:
        flash("Invalid role selected", "danger")
        return redirect('/')
    return render_template('login.html', role=role)

@app.route('/login', methods=['POST'])
def login():
    username = request.form['username']
    password = request.form['password']
    role = request.form['role']

    conn = get_db()
    c = conn.cursor()
    c.execute("SELECT * FROM users WHERE username=? AND password=? AND role=?", (username, password, role))
    user = c.fetchone()
    conn.close()

    if user:
        session['user_id'] = user[0]
        session['username'] = user[1]
        session['role'] = user[3]
        flash(f"Welcome, {user[1]}!", "success")

        if role == 'admin':
            return redirect('/admin')
        elif role == 'librarian':
            return redirect('/librarian')
        else:
            return redirect('/member')
    else:
        flash("Invalid credentials or role mismatch", "danger")
        return redirect('/')

# -------------------------
# 2. Dashboards
# -------------------------

@app.route('/admin')
def admin_dashboard():
    if session.get('role') != 'admin':
        flash("Access denied", "danger")
        return redirect('/')

    # Show all books directly in admin dashboard
    conn = get_db()
    c = conn.cursor()
    c.execute("SELECT * FROM books")
    books = c.fetchall()
    conn.close()
    return render_template('admin_book.html', books=books)

@app.route('/librarian')
def librarian_dashboard():
    if session.get('role') != 'librarian':
        flash("Access denied", "danger")
        return redirect('/')
    return render_template('librarian_dashboard.html')

@app.route('/member')
def member_dashboard():
    if session.get('role') != 'member':
        flash("Access denied", "danger")
        return redirect('/')
    return render_template('member_dashboard.html')

# -------------------------
# 3. Admin: Book Management
# -------------------------

# View all books (admin shortcut, same as dashboard)
@app.route('/admin/books')
def admin_books():
    if session.get('role') != 'admin':
        flash("Unauthorized access", "danger")
        return redirect('/')
    
    conn = get_db()
    c = conn.cursor()
    c.execute("SELECT * FROM books")
    books = c.fetchall()
    conn.close()
    return render_template('admin_book.html', books=books)

# Add a new book
@app.route('/admin/books/add', methods=['GET', 'POST'])
def add_book():
    if session.get('role') != 'admin':
        flash("Unauthorized access", "danger")
        return redirect('/')
    
    if request.method == 'POST':
        title = request.form['title']
        author = request.form['author']
        isbn = request.form['isbn']
        category = request.form['category']
        quantity = request.form['quantity']

        conn = get_db()
        c = conn.cursor()
        c.execute("INSERT INTO books (title, author, isbn, category, quantity) VALUES (?, ?, ?, ?, ?)",
                  (title, author, isbn, category, quantity))
        conn.commit()
        conn.close()
        flash("Book added successfully", "success")
        return redirect('/admin/books')
    
    return render_template('add_book.html')

# Edit a book
@app.route('/admin/books/edit/<int:book_id>', methods=['GET', 'POST'])
def edit_book(book_id):
    if session.get('role') != 'admin':
        flash("Unauthorized access", "danger")
        return redirect('/')

    conn = get_db()
    c = conn.cursor()
    
    if request.method == 'POST':
        title = request.form['title']
        author = request.form['author']
        isbn = request.form['isbn']
        category = request.form['category']
        quantity = request.form['quantity']

        c.execute('''
            UPDATE books SET title=?, author=?, isbn=?, category=?, quantity=? WHERE id=?
        ''', (title, author, isbn, category, quantity, book_id))
        conn.commit()
        conn.close()
        flash("Book updated successfully", "success")
        return redirect('/admin/books')

    c.execute("SELECT * FROM books WHERE id=?", (book_id,))
    book = c.fetchone()
    conn.close()
    return render_template('edit_book.html', book=book)

# Delete a book
@app.route('/admin/books/delete/<int:book_id>', methods=['POST'])
def delete_book(book_id):
    if session.get('role') != 'admin':
        flash("Unauthorized access", "danger")
        return redirect('/')

    conn = get_db()
    c = conn.cursor()
    c.execute("DELETE FROM books WHERE id=?", (book_id,))
    conn.commit()
    conn.close()
    flash("Book deleted", "info")
    return redirect('/admin/books')

@app.route('/member/books')
def member_books():
    conn = sqlite3.connect('database.db')
    conn.row_factory = sqlite3.Row
    books = conn.execute('SELECT * FROM books').fetchall()
    conn.close()
    return render_template('member_books.html', books=books)

from datetime import datetime, timedelta

# -------------------------
# 4. Admin/Librarian: Issue Book
# -------------------------

@app.route('/admin/issues/issue', methods=['GET', 'POST'])
def issue_book():
    if session.get('role') not in ['admin', 'librarian']:
        flash("Unauthorized access", "danger")
        return redirect('/')

    conn = get_db()
    c = conn.cursor()

    if request.method == 'POST':
        member_id = request.form['member_id']
        book_id = request.form['book_id']
        issue_date = datetime.today().date()
        due_date = issue_date + timedelta(days=14)

        try:
            # Insert issue
            c.execute('''
                INSERT INTO issues (member_id, book_id, issue_date, due_date)
                VALUES (?, ?, ?, ?)
            ''', (member_id, book_id, issue_date, due_date))

            # Decrease book quantity
            c.execute('UPDATE books SET quantity = quantity - 1 WHERE id = ?', (book_id,))
            conn.commit()
            flash("Book issued successfully", "success")
        except Exception as e:
            flash("Error issuing book: " + str(e), "danger")

        conn.close()
        return redirect('/admin/issues')

    # On GET: fetch available books and members
    c.execute('SELECT id, title FROM books WHERE quantity > 0')
    books = c.fetchall()
    c.execute("SELECT id, username FROM users WHERE role = 'member'")
    members = c.fetchall()
    conn.close()
    return render_template('issue_book.html', books=books, members=members)


@app.route('/admin/issues')
def view_issues():
    if session.get('role') not in ['admin', 'librarian']:
        flash("Unauthorized access", "danger")
        return redirect('/')

    conn = get_db()
    c = conn.cursor()
    c.execute('''
        SELECT issues.id, users.username, books.title,
               issues.issue_date, issues.due_date,
               issues.return_date, issues.fine,
               issues.status
        FROM issues
        JOIN users ON issues.member_id = users.id
        JOIN books ON issues.book_id = books.id
        ORDER BY issues.issue_date DESC
    ''')
    issues = c.fetchall()
    conn.close()
    return render_template('admin_issues.html', issues=issues)




# -------------------------
# Run the app
# -------------------------

if __name__ == '__main__':
    app.run(debug=True)
