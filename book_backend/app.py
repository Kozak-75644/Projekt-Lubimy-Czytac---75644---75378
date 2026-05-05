from flask import Flask, request, jsonify
from flask_cors import CORS
import sqlite3

app = Flask(__name__)
CORS(app)

def get_db_connection():
    conn = sqlite3.connect('books.db')
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_db_connection()
    conn.execute('''
        CREATE TABLE IF NOT EXISTS books (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT NOT NULL,
            author TEXT NOT NULL,
            genre TEXT,
            rating INTEGER
        )
    ''')
    conn.commit()
    conn.close()

init_db()

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
            'rating': book['rating']
        } for book in books
    ]
    return jsonify(books_list)

@app.route('/books', methods=['POST'])
def add_book():
    new_book = request.get_json()
    title = new_book.get('title')
    author = new_book.get('author')
    genre = new_book.get('genre', '')
    rating = new_book.get('rating', 0)

    conn = get_db_connection()
    conn.execute(
        'INSERT INTO books (title, author, genre, rating) VALUES (?, ?, ?, ?)', 
        (title, author, genre, rating)
    )
    conn.commit()
    conn.close()
    return jsonify({'message': 'Created'}), 201

@app.route('/books/<int:id>', methods=['PUT'])
def update_book(id):
    updated_book = request.get_json()
    title = updated_book.get('title')
    author = updated_book.get('author')
    genre = updated_book.get('genre', '')
    rating = updated_book.get('rating', 0)

    conn = get_db_connection()
    conn.execute(
        'UPDATE books SET title = ?, author = ?, genre = ?, rating = ? WHERE id = ?',
        (title, author, genre, rating, id)
    )
    conn.commit()
    conn.close()
    return jsonify({'message': 'Updated'})

@app.route('/books/<int:id>', methods=['DELETE'])
def delete_book(id):
    conn = get_db_connection()
    conn.execute('DELETE FROM books WHERE id = ?', (id,))
    conn.commit()
    conn.close()
    return jsonify({'message': 'Deleted'})

if __name__ == '__main__':
    app.run(debug=True)
