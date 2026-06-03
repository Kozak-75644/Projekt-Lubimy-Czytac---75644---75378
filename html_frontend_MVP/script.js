const API_URL = 'https://bohdanmelch.pythonanywhere.com'; 

document.addEventListener('DOMContentLoaded', () => {
    const bookForm = document.getElementById('add-book-form');
    const booksListContainer = document.getElementById('books-list');
    const detailsSection = document.getElementById('book-details-section');
    const detailsContent = document.getElementById('book-details-content');
    const closeDetailsBtn = document.getElementById('close-details');
    
    // Auth elements
    const authModal = document.getElementById('auth-modal');
    const authChoices = document.getElementById('auth-choices');
    const loginForm = document.getElementById('login-form');
    const registerForm = document.getElementById('register-form');
    const userControls = document.getElementById('user-info');
    const loginBtnMain = document.getElementById('login-btn-main');

   
    let currentUserId = localStorage.getItem('user_id');
    updateAuthUI();

    fetchBooks();


    loginBtnMain.onclick = () => { authModal.style.display = 'block'; resetAuthModal(); };
    document.getElementById('close-auth').onclick = () => authModal.style.display = 'none';
    document.getElementById('show-login').onclick = () => { authChoices.style.display = 'none'; loginForm.style.display = 'block'; };
    document.getElementById('show-register').onclick = () => { authChoices.style.display = 'none'; registerForm.style.display = 'block'; };
    document.querySelectorAll('.back-btn').forEach(btn => btn.onclick = resetAuthModal);
    document.getElementById('logout-btn').onclick = () => { 
        localStorage.removeItem('user_id'); 
        localStorage.removeItem('user_role'); 
        localStorage.removeItem('username'); 
        currentUserId = null; 
        updateAuthUI(); 
        fetchBooks(); 
    };

    function resetAuthModal() {
        authChoices.style.display = 'block';
        loginForm.style.display = 'none';
        registerForm.style.display = 'none';
        loginForm.reset(); registerForm.reset();
    }

    function updateAuthUI() {
        if (currentUserId) {
            loginBtnMain.style.display = 'none';
            userControls.style.display = 'block';
            document.getElementById('user-name-display').innerText = `Hello, ${localStorage.getItem('username')}!`;
        } else {
            loginBtnMain.style.display = 'block';
            userControls.style.display = 'none';
        }
    }

  
    registerForm.addEventListener('submit', async (e) => {
        e.preventDefault();
        const payload = { username: document.getElementById('reg-username').value, email: document.getElementById('reg-email').value, password: document.getElementById('reg-password').value };
        try {
            const res = await fetch(`${API_URL}/register`, { method: 'POST', headers: {'Content-Type': 'application/json'}, body: JSON.stringify(payload) });
            const data = await res.json();
            if (res.ok) {
                alert('Account created! Please log in.');
                resetAuthModal();
                document.getElementById('show-login').click();
            } else if (data.error === 'Email już istnieje') {
                alert('You already have an account, try log in.');
            }
        } catch (err) { console.error(err); }
    });


    loginForm.addEventListener('submit', async (e) => {
        e.preventDefault();
        const payload = { email: document.getElementById('login-email').value, password: document.getElementById('login-password').value };
        try {
            const res = await fetch(`${API_URL}/login`, { method: 'POST', headers: {'Content-Type': 'application/json'}, body: JSON.stringify(payload) });
            const data = await res.json();
            if (res.ok) {
                localStorage.setItem('user_id', data.user_id);
                localStorage.setItem('user_role', data.role);
                localStorage.setItem('username', data.username);
                currentUserId = data.user_id;
                authModal.style.display = 'none';
                updateAuthUI();
                fetchBooks();
                alert('Logged in successfully!');
            } else {
                alert('Wrong email or password');
            }
        } catch (err) { console.error(err); }
    });


    bookForm.addEventListener('submit', async (e) => {
        e.preventDefault();
        const newBook = {
            title: document.getElementById('title').value,
            author: document.getElementById('author').value,
            genre: document.getElementById('genre').value,
            rating: parseInt(document.getElementById('rating').value) || 0,
            image: document.getElementById('image').value
        };
        const response = await fetch(`${API_URL}/books`, { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(newBook) });
        if (response.ok) { bookForm.reset(); fetchBooks(); }
    });

    async function fetchBooks() {
        const response = await fetch(`${API_URL}/books`);
        const books = await response.json();
        booksListContainer.innerHTML = ''; 
        if (books.length === 0) { booksListContainer.innerHTML = '<p>No books available.</p>'; return; }
        
        books.forEach(book => {
            const bookElement = document.createElement('div');
            bookElement.classList.add('book-card');
            const userRole = localStorage.getItem('user_role');
            bookElement.innerHTML = `
                 ${book.image ? `<img src="${book.image}" alt="Book cover" class="book-cover">` : ''}
                <h3>${book.title}</h3>
                <p><strong>Author:</strong> ${book.author}</p>
                <button onclick="showDetails(${book.id}, '${book.title.replace(/'/g, "\\'")}', '${book.author.replace(/'/g, "\\'")}', '${book.genre}', ${book.rating}, '${book.image}')">View Details</button>
                ${userRole === 'admin' ? `<button onclick="deleteBook(${book.id})" style="background-color: #e74c3c; margin-left: 10px;">Delete</button>` : ''}
            `;
            booksListContainer.appendChild(bookElement);
        });
    }

    closeDetailsBtn.addEventListener('click', () => { detailsSection.style.display = 'none'; });

  
    window.showDetails = async function(id, title, author, genre, rating, imageURL) {
        detailsContent.innerHTML = '<p>Loading details...</p>';
        detailsSection.style.display = 'block';

        const commentsRes = await fetch(`${API_URL}/books/${id}/comments`);
        const comments = await commentsRes.json();
        
        let commentsHTML = '<h3>Reviews</h3>';
        if (comments.length === 0) {
            commentsHTML += '<p>No reviews yet.</p>';
        } else {
            comments.forEach(c => {
                commentsHTML += `<div class="comment-box">
                    <p style="font-size: 0.8rem; color: #7f8c8d; margin: 0 0 5px 0;"><strong>${c.username}</strong> wrote:</p>
                    <p style="margin: 0;">${c.content}</p>
                </div>`;
            });
        }

        let addCommentHTML = '';
        if (currentUserId) {
            document.getElementById('add-comment-form').addEventListener('submit', async (e) => {
                e.preventDefault();
                const content = document.getElementById('new-comment-text').value;
                await fetch(`${API_URL}/books/${id}/comments`, {
                    method: 'POST',
                    headers: {'Content-Type': 'application/json'},
                    body: JSON.stringify({ 
                        content: content,
                        user_id: currentUserId
                    })
                });
                showDetails(id, title, author, genre, rating, imageURL); 
            });
        }
    };

        detailsContent.innerHTML = `
             ${imageURL && imageURL !== 'undefined' ? `<img src="${imageURL}" alt="Book cover" style="max-width: 100%; max-height: 200px; border-radius: 5px; margin-bottom: 15px;">` : ''}
            <p><strong>Title:</strong> ${title}</p>
            <p><strong>Author:</strong> ${author}</p>
            <p><strong>Genre:</strong> ${genre || 'Not specified'}</p>
            <p><strong>Rating:</strong> ${rating}/10</p>
            <div id="comments-container">
                ${commentsHTML}
                ${addCommentHTML}
            </div>
        `;

        if (currentUserId) {
            document.getElementById('add-comment-form').addEventListener('submit', async (e) => {
                e.preventDefault();
                const content = document.getElementById('new-comment-text').value;
                await fetch(`${API_URL}/books/${id}/comments`, {
                    method: 'POST',
                    headers: {'Content-Type': 'application/json'},
                    body: JSON.stringify({ content: content })
                });
                showDetails(id, title, author, genre, rating, imageURL); 
            });
        }
    };

    window.deleteBook = async function(bookId) {
        if (!confirm('Are you sure you want to delete this book?')) return;
        const response = await fetch(`${API_URL}/books/${bookId}`, { 
            method: 'DELETE',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify({ user_id: currentUserId }) // Отправляем серверу, кто мы
        });
        const data = await response.json();
        if (response.ok) {
            fetchBooks();
        } else {
            alert(data.error || 'Failed to delete book');
        }
    };

const profileModal = document.getElementById('profile-modal');
    document.getElementById('profile-btn').onclick = async () => {
        profileModal.style.display = 'block';
        const profileInfo = document.getElementById('profile-info');
        profileInfo.innerHTML = '<p>Loading profile data...</p>';
        try {
            const res = await fetch(`${API_URL}/users/${currentUserId}/profile`);
            const data = await res.json();
            
            if (res.ok) {
                const date = new Date(data.created_at).toLocaleDateString();
                let commentsHtml = '<h4>My Reviews</h4>';
                if (data.comments_count === 0) {
                    commentsHtml += '<p>You haven\'t written any reviews yet.</p>';
                } else {
                    data.comments.forEach(c => {
                        commentsHtml += `<div class="profile-review">
                            <strong>Book: ${c.book_title}</strong>
                            <p style="margin: 5px 0 0 0;">${c.content}</p>
                        </div>`;
                    });
                }
                profileInfo.innerHTML = `
                    <p><strong>Username:</strong> ${data.username}</p>
                    <p><strong>Role:</strong> ${data.role === 'admin' ? '👑 Admin' : 'User'}</p>
                    <p><strong>Registered on:</strong> ${date}</p>
                    <p><strong>Total reviews:</strong> ${data.comments_count}</p>
                    <hr style="margin: 15px 0;">
                    ${commentsHtml}
                `;
            } else {
                profileInfo.innerHTML = '<p>Error loading profile.</p>';
            }
        } catch (e) {
            profileInfo.innerHTML = '<p>Connection error.</p>';
        }
    };
    document.getElementById('close-profile').onclick = () => profileModal.style.display = 'none';
});
