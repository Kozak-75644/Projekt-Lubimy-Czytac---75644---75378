from flask import Flask, request, jsonify
from flask_cors import CORS
from werkzeug.security import generate_password_hash, check_password_hash
import sqlite3

app = Flask(__name__)
CORS(app)

def get_db_connection():
    conn = sqlite3.connect('books.db')
    conn.row_factory = sqlite3.Row
    conn.execute('PRAGMA foreign_keys = ON')
    return conn

# Inicjalizacja zaktualizowanej bazy danych
def init_db():
    conn = get_db_connection()

    # Nowa tabela autorów
    conn.execute('''
        CREATE TABLE IF NOT EXISTS authors (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT UNIQUE NOT NULL
        )
    ''')

    # Tabela książek zaktualizowana o klucz obcy (author_id zamiast tekstowego author)
    conn.execute('''
        CREATE TABLE IF NOT EXISTS books (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT NOT NULL,
            author_id INTEGER NOT NULL,
            genre TEXT,
            rating INTEGER,
            image TEXT,
            description TEXT,
            FOREIGN KEY (author_id) REFERENCES authors (id)
        )
    ''')

    conn.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT NOT NULL,
            email TEXT UNIQUE NOT NULL,
            password_hash TEXT NOT NULL,
            role TEXT DEFAULT 'user',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')

    conn.execute('''
        CREATE TABLE IF NOT EXISTS comments (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            book_id INTEGER NOT NULL,
            user_id INTEGER NOT NULL,
            content TEXT NOT NULL,
            FOREIGN KEY (book_id) REFERENCES books (id),
            FOREIGN KEY (user_id) REFERENCES users (id)
        )
    ''')

    conn.commit()
    conn.close()

init_db()

# --- ENDPOINTY UŻYTKOWNIKÓW ---

@app.route('/register', methods=['POST'])
def register():
    data = request.get_json()
    username = data.get('username')
    email = data.get('email')
    password = data.get('password')

    if not username or not email or not password:
        return jsonify({'error': 'Brak pełnych danych'}), 400

    hashed_password = generate_password_hash(password)
    
    conn = get_db_connection()
    try:
        conn.execute(
            'INSERT INTO users (username, email, password_hash) VALUES (?, ?, ?)',
            (username, email, hashed_password)
        )
        conn.commit()
    except sqlite3.IntegrityError:
        conn.close()
        return jsonify({'error': 'Email już istnieje'}), 400
    
    conn.close()
    return jsonify({'message': 'Zarejestrowano pomyślnie'}), 201

@app.route('/login', methods=['POST'])
def login():
    data = request.get_json()
    email = data.get('email')
    password = data.get('password')

    conn = get_db_connection()
    user = conn.execute('SELECT * FROM users WHERE email = ?', (email,)).fetchone()
    conn.close()

    if user and check_password_hash(user['password_hash'], password):
        return jsonify({
            'message': 'Zalogowano', 
            'user_id': user['id'], 
            'username': user['username'],
            'role': user['role']
        }), 200
    else:
        return jsonify({'error': 'Nieprawidłowe dane'}), 401

@app.route('/users/<int:user_id>/profile', methods=['GET'])
def get_user_profile(user_id):
    conn = get_db_connection()
    user = conn.execute('SELECT username, created_at, role FROM users WHERE id = ?', (user_id,)).fetchone()
    
    if not user:
        conn.close()
        return jsonify({'error': 'Użytkownik nie znaleziony'}), 404

    comments = conn.execute('''
        SELECT comments.id, comments.content, books.title as book_title
        FROM comments
        JOIN books ON comments.book_id = books.id
        WHERE comments.user_id = ?
    ''', (user_id,)).fetchall()
    conn.close()
    
    profile_data = {
        'username': user['username'],
        'created_at': user['created_at'],
        'role': user['role'],
        'comments_count': len(comments),
        'comments': [dict(c) for c in comments]
    }
    return jsonify(profile_data)

# --- ENDPOINTY AUTORÓW ---

# Pobieranie listy wszystkich autorów
@app.route('/authors', methods=['GET'])
def get_authors():
    conn = get_db_connection()
    authors = conn.execute('SELECT * FROM authors').fetchall()
    conn.close()
    return jsonify([dict(a) for a in authors])

# Pobieranie szczegółów autora wraz z przypisanymi do niego książkami
@app.route('/authors/<int:author_id>', methods=['GET'])
def get_author_details(author_id):
    conn = get_db_connection()
    author = conn.execute('SELECT * FROM authors WHERE id = ?', (author_id,)).fetchone()
    
    if not author:
        conn.close()
        return jsonify({'error': 'Autor nie znaleziony'}), 404
        
    books = conn.execute('SELECT id, title, genre, image FROM books WHERE author_id = ?', (author_id,)).fetchall()
    conn.close()
    
    return jsonify({
        'author_name': author['name'],
        'books': [dict(b) for b in books]
    })


# --- ENDPOINTY KSIĄŻEK ---

@app.route('/books/search', methods=['GET'])
def search_books():
    query = request.args.get('q', '')
    conn = get_db_connection()
    # Połączenie tabel w celu wyszukiwania również po nazwie autora
    books = conn.execute('''
        SELECT books.*, authors.name as author 
        FROM books 
        JOIN authors ON books.author_id = authors.id
        WHERE books.title LIKE ? OR authors.name LIKE ?
    ''', (f'%{query}%', f'%{query}%')).fetchall()
    conn.close()
    
    return jsonify([dict(book) for book in books])

@app.route('/books', methods=['GET'])
def get_books():
    conn = get_db_connection()
    # Pobieranie nazwy autora dzięki relacji (JOIN)
    books = conn.execute('''
        SELECT books.*, authors.name as author 
        FROM books 
        JOIN authors ON books.author_id = authors.id
    ''').fetchall()
    conn.close()
    return jsonify([dict(book) for book in books])

@app.route('/books', methods=['POST'])
def add_book():
    new_book = request.get_json()
    author_name = new_book.get('author')
    
    conn = get_db_connection()
    
    # Automatyczne dodanie autora, jeśli nie istnieje w tabeli 'authors'
    author = conn.execute('SELECT id FROM authors WHERE name = ?', (author_name,)).fetchone()
    if author:
        author_id = author['id']
    else:
        cursor = conn.execute('INSERT INTO authors (name) VALUES (?)', (author_name,))
        author_id = cursor.lastrowid
        
    conn.execute(
        'INSERT INTO books (title, author_id, genre, rating, image, description) VALUES (?, ?, ?, ?, ?, ?)', 
        (
            new_book.get('title'), author_id, new_book.get('genre', ''), 
            new_book.get('rating', 0), new_book.get('image', ''), new_book.get('description', '')
        )
    )
    conn.commit()
    conn.close()
    return jsonify({'message': 'Created'}), 201

@app.route('/books/<int:id>', methods=['PUT'])
def update_book(id):
    data = request.get_json()
    author_name = data.get('author')
    
    conn = get_db_connection()
    
    # Wyszukiwanie lub tworzenie nowego autora przy edycji
    author = conn.execute('SELECT id FROM authors WHERE name = ?', (author_name,)).fetchone()
    if author:
        author_id = author['id']
    else:
        cursor = conn.execute('INSERT INTO authors (name) VALUES (?)', (author_name,))
        author_id = cursor.lastrowid

    conn.execute(
        '''UPDATE books 
           SET title = ?, author_id = ?, genre = ?, rating = ?, image = ?, description = ? 
           WHERE id = ?''', 
        (
            data.get('title'), author_id, data.get('genre', ''), 
            data.get('rating', 0), data.get('image', ''), data.get('description', ''), id
        )
    )
    conn.commit()
    conn.close()
    return jsonify({'message': 'Zaktualizowano książkę'})

@app.route('/books/<int:id>', methods=['DELETE'])
def delete_book(id):
    data = request.get_json(silent=True) or {}
    user_id = data.get('user_id')

    if not user_id:
        return jsonify({'error': 'Brak ID użytkownika'}), 400

    conn = get_db_connection()
    user = conn.execute('SELECT role FROM users WHERE id = ?', (user_id,)).fetchone()
    
    if not user or user['role'] != 'admin':
        conn.close()
        return jsonify({'error': 'Brak uprawnień admina'}), 403

    conn.execute('DELETE FROM books WHERE id = ?', (id,))
    conn.execute('DELETE FROM comments WHERE book_id = ?', (id,))
    conn.commit()
    conn.close()
    return jsonify({'message': 'Usunięto książkę'})


# --- ENDPOINTY KOMENTARZY ---

@app.route('/books/<int:book_id>/comments', methods=['GET'])
def get_comments(book_id):
    conn = get_db_connection()
    comments = conn.execute('''
        SELECT comments.id, comments.content, users.username 
        FROM comments 
        JOIN users ON comments.user_id = users.id 
        WHERE comments.book_id = ?
    ''', (book_id,)).fetchall()
    conn.close()
    return jsonify([dict(c) for c in comments])

@app.route('/books/<int:book_id>/comments', methods=['POST'])
def add_comment(book_id):
    data = request.get_json()
    content = data.get('content')
    user_id = data.get('user_id')

    if not content or not user_id:
        return jsonify({'error': 'Brak danych'}), 400

    conn = get_db_connection()
    conn.execute('INSERT INTO comments (book_id, user_id, content) VALUES (?, ?, ?)', (book_id, user_id, content))
    conn.commit()
    conn.close()
    return jsonify({'message': 'Dodano komentarz'}), 201

if __name__ == '__main__':
    app.run(debug=True)
