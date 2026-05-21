from flask import Flask, request, jsonify
from flask_cors import CORS
from werkzeug.security import generate_password_hash, check_password_hash
import sqlite3

app = Flask(__name__)
CORS(app)

# Funkcja nawiązująca połączenie z bazą danych SQLite
def get_db_connection():
    conn = sqlite3.connect('books.db')
    conn.row_factory = sqlite3.Row
    return conn

# Funkcja inicjalizująca tabele w bazie danych
def init_db():
    conn = get_db_connection()

    # Tabela książek (dodano kolumnę 'description')
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

    # Tabela użytkowników (rejestracja i logowanie)
    conn.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            email TEXT UNIQUE NOT NULL,
            password_hash TEXT NOT NULL
        )
    ''')

    # Tabela komentarzy (powiązana z konkretną książką)
    conn.execute('''
        CREATE TABLE IF NOT EXISTS comments (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            book_id INTEGER NOT NULL,
            content TEXT NOT NULL,
            FOREIGN KEY (book_id) REFERENCES books (id)
        )
    ''')

    conn.commit()
    conn.close()

init_db()

# --- ENDPOINTY UŻYTKOWNIKÓW ---

# Endpoint rejestracji nowego użytkownika
@app.route('/register', methods=['POST'])
def register():
    data = request.get_json()
    email = data.get('email')
    password = data.get('password')

    if not email or not password:
        return jsonify({'error': 'Brak danych'}), 400

    hashed_password = generate_password_hash(password)

    conn = get_db_connection()
    try:
        conn.execute('INSERT INTO users (email, password_hash) VALUES (?, ?)', (email, hashed_password))
        conn.commit()
    except sqlite3.IntegrityError:
        conn.close()
        return jsonify({'error': 'Email już istnieje'}), 400
    
    conn.close()
    return jsonify({'message': 'Zarejestrowano pomyślnie'}), 201

# Endpoint logowania
@app.route('/login', methods=['POST'])
def login():
    data = request.get_json()
    email = data.get('email')
    password = data.get('password')

    conn = get_db_connection()
    user = conn.execute('SELECT * FROM users WHERE email = ?', (email,)).fetchone()
    conn.close()

    if user and check_password_hash(user['password_hash'], password):
        return jsonify({'message': 'Zalogowano', 'user_id': user['id']}), 200
    else:
        return jsonify({'error': 'Nieprawidłowe dane'}), 401


# --- ENDPOINTY KSIĄŻEK ---

# Pobieranie listy książek
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

# Dodawanie nowej książki 
@app.route('/books', methods=['POST'])
def add_book():
    new_book = request.get_json()
    title = new_book.get('title')
    author = new_book.get('author')
    genre = new_book.get('genre', '')
    rating = new_book.get('rating', 0)
    image = new_book.get('image', '')
    description = new_book.get('description', '')

    conn = get_db_connection()
    conn.execute(
        'INSERT INTO books (title, author, genre, rating, image, description) VALUES (?, ?, ?, ?, ?, ?)', 
        (title, author, genre, rating, image, description)
    )
    conn.commit()
    conn.close()
    return jsonify({'message': 'Created'}), 201

# Usuwanie książki wraz z jej komentarzami
@app.route('/books/<int:id>', methods=['DELETE'])
def delete_book(id):
    conn = get_db_connection()
    conn.execute('DELETE FROM books WHERE id = ?', (id,))
    conn.execute('DELETE FROM comments WHERE book_id = ?', (id,))
    conn.commit()
    conn.close()
    return jsonify({'message': 'Deleted'})


# --- ENDPOINTY KOMENTARZY ---

# Pobieranie komentarzy dla danej książki
@app.route('/books/<int:book_id>/comments', methods=['GET'])
def get_comments(book_id):
    conn = get_db_connection()
    comments = conn.execute('SELECT * FROM comments WHERE book_id = ?', (book_id,)).fetchall()
    conn.close()
    
    comments_list = [{'id': c['id'], 'content': c['content']} for c in comments]
    return jsonify(comments_list)

# Dodawanie komentarza do konkretnej książki
@app.route('/books/<int:book_id>/comments', methods=['POST'])
def add_comment(book_id):
    data = request.get_json()
    content = data.get('content')

    if not content:
        return jsonify({'error': 'Brak treści komentarza'}), 400

    conn = get_db_connection()
    conn.execute('INSERT INTO comments (book_id, content) VALUES (?, ?)', (book_id, content))
    conn.commit()
    conn.close()
    return jsonify({'message': 'Dodano komentarz'}), 201

if __name__ == '__main__':
    app.run(debug=True)
