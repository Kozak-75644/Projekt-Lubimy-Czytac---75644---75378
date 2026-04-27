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
            author TEXT NOT NULL
        )
    ''')
    conn.commit()
    conn.close()

# Запускаємо створення таблиці при старті програми
init_db()

@app.route('/books', methods=['GET'])
def get_books():
    conn = get_db_connection()
    books = conn.execute('SELECT * FROM books').fetchall() 
    conn.close()

    books_list = [{'id': book['id'], 'title': book['title'], 'author': book['author']} for book in books]
    return jsonify(books_list)


@app.route('/books', methods=['POST'])
def add_book():
    new_book = request.get_json() 
    title = new_book['title']
    author = new_book['author']

    conn = get_db_connection()
    conn.execute('INSERT INTO books (title, author) VALUES (?, ?)', (title, author))
    conn.commit()
    conn.close()

    return jsonify({'message': 'Книгу успішно додано!'}), 201


# Запуск сервера
if __name__ == '__main__':
    # debug=True означає, що сервер буде сам перезавантажуватись, якщо ти зміниш код
    app.run(debug=True)
