from flask import Flask, render_template, request, redirect, url_for, flash,session
import sqlite3
import os
from datetime import datetime, timedelta

app = Flask(__name__)
app.secret_key = 'secret'

DATABASE = 'lms.db'

def init_db():
    conn = sqlite3.connect(DATABASE)
    cur = conn.cursor()

   
    cur.execute('''CREATE TABLE IF NOT EXISTS books (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        title TEXT,
        author TEXT,
        category TEXT,
        status TEXT DEFAULT 'Available'
    )''')

   
    cur.execute('''CREATE TABLE IF NOT EXISTS members (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT,
        email TEXT
    )''')

    
    cur.execute('''CREATE TABLE IF NOT EXISTS transactions (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        book_id INTEGER,
        member_id INTEGER,
        issue_date TEXT,
        return_date TEXT,
        fine INTEGER DEFAULT 0
    )''')
#     cur.execute('''CREATE TABLE IF NOT EXISTS requests (
#     id INTEGER PRIMARY KEY AUTOINCREMENT,
#     name TEXT,
#     book TEXT,
#     request_date TEXT
# )''')


    conn.commit()
    conn.close()

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/login', methods=['GET','POST'])
def login():
    if request.method == 'POST':
       
        user = request.form['username']
        pwd = request.form['password']
        if user == 'admin' and pwd == 'admin':
            return redirect(url_for('dashboard'))
        else:
            flash('Invalid Credentials')
            return redirect(url_for('login'))
    return render_template('login.html')

@app.route('/dashboard')
def dashboard():
    return render_template('dashboard.html')

@app.route('/add_book', methods=['GET','POST'])
def add_book():
    if request.method == 'POST':
        title = request.form['title']
        author = request.form['author']
        category = request.form['category']
        conn = sqlite3.connect(DATABASE)
        cur = conn.cursor()
        cur.execute("INSERT INTO books(title,author,category) VALUES (?,?,?)", (title, author, category))
        conn.commit()
        conn.close()
        flash('Book Added Successfully!')
        return redirect(url_for('manage_books'))
    return render_template('add_book.html')

@app.route('/manage_books')
def manage_books():
    conn = sqlite3.connect(DATABASE)
    cur = conn.cursor()
    cur.execute("SELECT * FROM books")
    books = cur.fetchall()
    conn.close()
    return render_template('manage_books.html', books=books)

@app.route('/add_member', methods=['GET','POST'])
def add_member():
    if request.method == 'POST':
        name = request.form['name']
        email = request.form['email']
        conn = sqlite3.connect(DATABASE)
        cur = conn.cursor()
        cur.execute("INSERT INTO members(name,email) VALUES (?,?)", (name,email))
        conn.commit()
        conn.close()
        flash('Member Added Successfully!')
        return redirect(url_for('dashboard'))
    return render_template('add_member.html')

@app.route('/issue_book', methods=['GET','POST'])
def issue_book():
    conn = sqlite3.connect(DATABASE)
    cur = conn.cursor()
    cur.execute("SELECT * FROM books WHERE status='Available'")
    books = cur.fetchall()
    cur.execute("SELECT * FROM members")
    members = cur.fetchall()
    if request.method == 'POST':
        book_id = request.form['book_id']
        member_id = request.form['member_id']
        issue_date = datetime.now().strftime('%Y-%m-%d')
        cur.execute("INSERT INTO transactions(book_id,member_id,issue_date) VALUES (?,?,?)", (book_id, member_id, issue_date))
        cur.execute("UPDATE books SET status='Issued' WHERE id=?", (book_id,))
        conn.commit()
        conn.close()
        flash('Book Issued Successfully!')
        return redirect(url_for('dashboard'))
    conn.close()
    return render_template('issue_book.html', books=books, members=members)

@app.route('/return_book', methods=['GET','POST'])
def return_book():
    conn = sqlite3.connect(DATABASE)
    cur = conn.cursor()
    cur.execute("SELECT t.id, b.title, m.name, t.issue_date FROM transactions t JOIN books b ON t.book_id = b.id JOIN members m ON t.member_id = m.id WHERE t.return_date IS NULL")
    issued = cur.fetchall()
    if request.method == 'POST':
        transaction_id = request.form['transaction_id']
        return_date = datetime.now()
        cur.execute("SELECT issue_date, book_id FROM transactions WHERE id=?", (transaction_id,))
        row = cur.fetchone()
        issue_date = datetime.strptime(row[0], '%Y-%m-%d')
        days_late = (return_date - issue_date).days - 7
        fine = max(0, days_late * 5)
        cur.execute("UPDATE transactions SET return_date=?, fine=? WHERE id=?", (return_date.strftime('%Y-%m-%d'), fine, transaction_id))
        cur.execute("UPDATE books SET status='Available' WHERE id=?", (row[1],))
        conn.commit()
        conn.close()
        flash(f'Book Returned. Fine: ₹{fine}')
        return redirect(url_for('dashboard'))
    conn.close()
    return render_template('return_book.html', issued=issued)

@app.route('/reports')
def reports():
    conn = sqlite3.connect(DATABASE)
    cur = conn.cursor()
    cur.execute("SELECT t.id, b.title, m.name, t.issue_date, t.return_date, t.fine FROM transactions t JOIN books b ON t.book_id = b.id JOIN members m ON t.member_id = m.id")
    reports = cur.fetchall()
    conn.close()
    return render_template('reports.html', reports=reports)

@app.route('/request_book', methods=['GET','POST'])
def request_book():
    if request.method == 'POST':
        name = request.form['name']
        book = request.form['book']
        flash(f'Request submitted for "{book}" by {name}.')
        return redirect(url_for('index'))
    return render_template('request_book.html')
@app.route('/view_requests')
def view_requests():
    if 'user' not in session:
        flash('Please login first.')
        return redirect(url_for('login'))

    conn = sqlite3.connect(DATABASE)
    cur = conn.cursor()
    cur.execute("SELECT * FROM requests ORDER BY request_date DESC")
    requests_list = cur.fetchall()
    conn.close()

    return render_template('view_requests.html', requests=requests_list)



if __name__ == '__main__':
    if not os.path.exists(DATABASE):
        init_db()
    app.run(debug=True)
