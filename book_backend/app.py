from flask import Flask, request, jsonify
from flask_cors import CORS
import sqlite3

app = Flask(__name__)
CORS(app)

# Funkcja nawiązująca połączenie z bazą danych SQLite
def get_db_connection():
    conn = sqlite3.connect('books.db')
    conn.row_factory = sqlite3.Row
    return conn

# Funkcja inicjalizująca tabelę w bazie danych (zawiera nową kolumnę 'image')
def init_db():
    conn = get_db_connection()
    conn.execute('''
        CREATE TABLE IF NOT EXISTS books (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT NOT NULL,
            author TEXT NOT NULL,
            genre TEXT,
            rating INTEGER,
            image TEXT
        )
    ''')
    conn.commit()
    conn.close()

init_db()

# Endpoint pobierający listę wszystkich książek (metoda GET)
@app.route('/books', methods=['GET'])
def get_books():
    conn = get_db_connection()
    books = conn.execute('SELECT * FROM books').fetchall()
    conn.close()
    
    # Mapowanie rekordów z bazy danych na listę słowników
    books_list = [
        {
            'id': book['id'], 
            'title': book['title'], 
            'author': book['author'], 
            'genre': book['genre'], 
            'rating': book['rating'],
            'image': book['image']
        } for book in books
    ]
    return jsonify(books_list)

# Endpoint dodający nową książkę do bazy danych (metoda POST)
@app.route('/books', methods=['POST'])
def add_book():
    new_book = request.get_json()
    title = new_book.get('title')
    author = new_book.get('author')
    genre = new_book.get('genre', '')
    rating = new_book.get('rating', 0)
    image = new_book.get('image', '')

    conn = get_db_connection()
    conn.execute(
        'INSERT INTO books (title, author, genre, rating, image) VALUES (?, ?, ?, ?, ?)', 
        (title, author, genre, rating, image)
    )
    conn.commit()
    conn.close()
    return jsonify({'message': 'Created'}), 201

# Endpoint usuwający książkę na podstawie identyfikatora (metoda DELETE)
@app.route('/books/<int:id>', methods=['DELETE'])
def delete_book(id):
    conn = get_db_connection()
    conn.execute('DELETE FROM books WHERE id = ?', (id,))
    conn.commit()
    conn.close()
    return jsonify({'message': 'Deleted'})

if __name__ == '__main__':
    app.run(debug=True)
