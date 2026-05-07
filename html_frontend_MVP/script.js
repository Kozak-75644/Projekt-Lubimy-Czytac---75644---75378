// server's URL 
const API_URL = 'example'; 

document.addEventListener('DOMContentLoaded', () => {
    const bookForm = document.getElementById('add-book-form');
    const booksListContainer = document.getElementById('books-list');
    const detailsSection = document.getElementById('book-details-section');
    const detailsContent = document.getElementById('book-details-content');
    const closeDetailsBtn = document.getElementById('close-details');

    fetchBooks();

    bookForm.addEventListener('submit', async (e) => {
        e.preventDefault();

        const newBook = {
            title: document.getElementById('title').value,
            author: document.getElementById('author').value,
            genre: document.getElementById('genre').value,
            rating: parseInt(document.getElementById('rating').value) || 0
        };
        try {
            const response = await fetch(API_URL, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify(newBook)
            });

            if (response.ok) {
                bookForm.reset(); 
                fetchBooks();
            } else {
                console.error('Server error when adding a book');
            }
        } catch (error) {
            console.error('Connection error:', error);
            alert('Failed to connect to the server. Is the backend running??');
        }
    });
    async function fetchBooks() {
        try {
            const response = await fetch(API_URL);
            const books = await response.json();

            booksListContainer.innerHTML = ''; 

            if (books.length === 0) {
                booksListContainer.innerHTML = '<p>No books available.</p>';
                return;
            }
            books.forEach(book => {
                const bookElement = document.createElement('div');
                bookElement.classList.add('book-card');
                bookElement.innerHTML = `
                    <h3>${book.title}</h3>
                    <p><strong>Author:</strong> ${book.author}</p>
                    <button onclick="showDetails('${book.title}', '${book.author}', '${book.genre}', ${book.rating})">View Details</button>
                    <button onclick="deleteBook(${book.id})" style="background-color: #e74c3c; margin-left: 10px;">Delete</button>
                `;
                booksListContainer.appendChild(bookElement);
            });
        } catch (error) {
            booksListContainer.innerHTML = '<p>Error loading books. Server might be offline.</p>';
            console.error(error);
        }
    }
    closeDetailsBtn.addEventListener('click', () => {
        detailsSection.style.display = 'none';
    });
    window.showDetails = function(title, author, genre, rating) {
        detailsContent.innerHTML = `
            <p><strong>Title:</strong> ${title}</p>
            <p><strong>Author:</strong> ${author}</p>
            <p><strong>Genre:</strong> ${genre || 'Not specified'}</p>
            <p><strong>Rating:</strong> ${rating}/10</p>
        `;
        detailsSection.style.display = 'block';
    };
    const requiredInputs = document.querySelectorAll('input[required]');
    requiredInputs.forEach(input => {
        input.addEventListener('invalid', function(e) {
            e.target.setCustomValidity('Please fill out this field.');
        });
        input.addEventListener('input', function(e) {
            e.target.setCustomValidity('');
        });
    });
    window.deleteBook = async function(bookId) {

        if (!confirm('Are you sure you want to delete this book?')) {
            return;
        }
        try {
            const response = await fetch(`${API_URL}/${bookId}`, {
                method: 'DELETE'
            });
            if (response.ok) {
                fetchBooks();
            } else {
                console.error('Failed to delete book on the server');
                alert('Failed to delete book.');
            }
        } catch (error) {
            console.error('Connection error while deleting:', error);
            alert('Connection error. Server might be down.');
        }
    };
});
