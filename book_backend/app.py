from flask import Flask, request, jsonify
from flask_cors import CORS
from werkzeug.security import generate_password_hash, check_password_hash
import sqlite3

app = Flask(__name__)
CORS(app)

# Funkcja nawiązująca połączenie z bazą danych
def get_db_connection():
    conn = sqlite3.connect('books.db')
    conn.row_factory = sqlite3.Row
    return conn

# Inicjalizacja bazy danych z nowymi relacjami i kolumnami
def init_db():
    conn = get_db_connection()

    conn.execute('''
        CREATE TABLE IF NOT EXISTS books (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT NOT NULL,
            author TEXT NOT NULL,
            genre TEXT,
            rating INTEGER,
            image TEXT,
            description TEXT
        )
    ''')

    # Zaktualizowana tabela użytkowników (dodano username i created_at)
    conn.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT NOT NULL,
            email TEXT UNIQUE NOT NULL,
            password_hash TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')

    # Zaktualizowana tabela komentarzy (dodano user_id jako klucz obcy)
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
        # Zwracamy id oraz username, aby frontend mógł je zapisać w sesji/local storage
        return jsonify({'message': 'Zalogowano', 'user_id': user['id'], 'username': user['username']}), 200
    else:
        return jsonify({'error': 'Nieprawidłowe dane'}), 401

# Nowy endpoint dla profilu użytkownika
@app.route('/users/<int:user_id>/profile', methods=['GET'])
def get_user_profile(user_id):
    conn = get_db_connection()
    
    user = conn.execute('SELECT username, created_at FROM users WHERE id = ?', (user_id,)).fetchone()
    if not user:
        conn.close()
        return jsonify({'error': 'Użytkownik nie znaleziony'}), 404

    # Pobieranie komentarzy użytkownika z dołączeniem tytułu książki
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
        'comments_count': len(comments),
        'comments': [{'id': c['id'], 'content': c['content'], 'book_title': c['book_title']} for c in comments]
    }
    return jsonify(profile_data)


# --- ENDPOINTY KSIĄŻEK ---

@app.route('/books', methods=['GET'])
def get_books():
    conn = get_db_connection()
    books = conn.execute('SELECT * FROM books').fetchall()
    conn.close()
    
    books_list = [
        {
            'id': book['id'], 
            'title': book['title'], 
            'author': book['author'], 
            'genre': book['genre'], 
            'rating': book['rating'],
            'image': book['image'],
            'description': book['description']
        } for book in books
    ]
    return jsonify(books_list)

@app.route('/books', methods=['POST'])
def add_book():
    new_book = request.get_json()
    conn = get_db_connection()
    conn.execute(
        'INSERT INTO books (title, author, genre, rating, image, description) VALUES (?, ?, ?, ?, ?, ?)', 
        (
            new_book.get('title'), 
            new_book.get('author'), 
            new_book.get('genre', ''), 
            new_book.get('rating', 0), 
            new_book.get('image', ''), 
            new_book.get('description', '')
        )
    )
    conn.commit()
    conn.close()
    return jsonify({'message': 'Created'}), 201

@app.route('/books/<int:id>', methods=['DELETE'])
def delete_book(id):
    conn = get_db_connection()
    conn.execute('DELETE FROM books WHERE id = ?', (id,))
    # Usunięcie również powiązanych komentarzy
    conn.execute('DELETE FROM comments WHERE book_id = ?', (id,))
    conn.commit()
    conn.close()
    return jsonify({'message': 'Deleted'})


# --- ENDPOINTY KOMENTARZY ---

@app.route('/books/<int:book_id>/comments', methods=['GET'])
def get_comments(book_id):
    conn = get_db_connection()
    # Pobieranie komentarzy z dołączeniem nazwy użytkownika
    comments = conn.execute('''
        SELECT comments.id, comments.content, users.username 
        FROM comments 
        JOIN users ON comments.user_id = users.id 
        WHERE comments.book_id = ?
    ''', (book_id,)).fetchall()
    conn.close()
    
    comments_list = [{'id': c['id'], 'content': c['content'], 'username': c['username']} for c in comments]
    return jsonify(comments_list)

@app.route('/books/<int:book_id>/comments', methods=['POST'])
def add_comment(book_id):
    data = request.get_json()
    content = data.get('content')
    user_id = data.get('user_id')

    if not content or not user_id:
        return jsonify({'error': 'Brak treści lub ID użytkownika'}), 400

    conn = get_db_connection()
    conn.execute('INSERT INTO comments (book_id, user_id, content) VALUES (?, ?, ?)', (book_id, user_id, content))
    conn.commit()
    conn.close()
    return jsonify({'message': 'Dodano komentarz'}), 201

if __name__ == '__main__':
    app.run(debug=True)
