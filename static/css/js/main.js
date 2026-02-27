// Обработка всех событий после загрузки DOM
document.addEventListener('DOMContentLoaded', function() {
    console.log('DOM loaded - initializing event handlers');
    
    // Обработка добавления в избранное для карточек книг
    const favoriteButtons = document.querySelectorAll('.add-favorite');
    favoriteButtons.forEach(button => {
        button.addEventListener('click', function() {
            const bookId = this.dataset.bookId;
            addToFavorites(bookId, this);
        });
    });

    // Обработка кнопки избранного на странице деталей книги
    const favoriteBtn = document.getElementById('favoriteBtn');
    if (favoriteBtn) {
        console.log('Found favorite button for book:', favoriteBtn.dataset.bookId);
        favoriteBtn.addEventListener('click', function() {
            const bookId = this.dataset.bookId;
            const isFavorite = this.classList.contains('btn-danger');
            toggleFavorite(bookId, this, isFavorite);
        });
    }

    // Обработка добавления в мои книги на странице рекомендаций
    const addToMyBooksButtons = document.querySelectorAll('.add-to-my-books');
    addToMyBooksButtons.forEach(button => {
        button.addEventListener('click', function() {
            const bookId = this.dataset.bookId;
            console.log('Add to my books clicked:', bookId);
            showStatusModal(bookId);
        });
    });

    // Обработка кнопки "В мои книги" на странице деталей книги
    const addToMyBooksBtn = document.querySelector('[data-bs-target="#statusModal"]');
    if (addToMyBooksBtn) {
        addToMyBooksBtn.addEventListener('click', function() {
            const bookId = document.getElementById('favoriteBtn')?.dataset.bookId;
            console.log('Add to my books modal opened for book:', bookId);
        });
    }


    // Обработка кнопок статуса в модальном окне (делегирование событий)
    document.addEventListener('click', function(e) {
        if (e.target.classList.contains('status-btn') || e.target.closest('.status-btn')) {
            const button = e.target.classList.contains('status-btn') ? e.target : e.target.closest('.status-btn');
            const status = button.dataset.status;
            const bookId = document.getElementById('favoriteBtn')?.dataset.bookId;
            
            console.log('Status button clicked:', status, 'for book:', bookId);
            
            if (bookId) {
                addToMyBooks(bookId, status);
            } else {
                showNotification('Ошибка: не найден ID книги', 'error');
            }
        }
        
        if (e.target.classList.contains('btn-status') || e.target.closest('.btn-status')) {
            const button = e.target.classList.contains('btn-status') ? e.target : e.target.closest('.btn-status');
            const status = button.dataset.status;
            const bookId = button.closest('.modal') ? 
                document.querySelector('[data-book-id]')?.dataset.bookId : 
                button.dataset.bookId;
            
            console.log('Modal status button clicked:', status, 'for book:', bookId);
            
            if (bookId) {
                addToMyBooks(bookId, status);
            }
        }
    });

    // Обработка формы отзыва
    const reviewForm = document.getElementById('reviewForm');
    if (reviewForm) {
        reviewForm.addEventListener('submit', function(e) {
            e.preventDefault();
            submitReview(this);
        });
    }
});

// Функция для переключения избранного (для страницы деталей книги)
async function toggleFavorite(bookId, button, isFavorite) {
    try {
        const response = await fetch(`/api/избранное/${bookId}`, {
            method: isFavorite ? 'DELETE' : 'POST',
            headers: {
                'Content-Type': 'application/json',
            }
        });
        
        const result = await response.json();
        
        if (result.success) {
            if (isFavorite) {
                button.classList.remove('btn-danger');
                button.classList.add('btn-outline-danger');
                button.innerHTML = '<i class="far fa-heart"></i> В избранное';
                showNotification('Книга удалена из избранного', 'info');
            } else {
                button.classList.remove('btn-outline-danger');
                button.classList.add('btn-danger');
                button.innerHTML = '<i class="fas fa-heart"></i> В избранном';
                showNotification('Книга добавлена в избранное!', 'success');
            }
        } else {
            showNotification(result.error || 'Ошибка при работе с избранным', 'error');
        }
    } catch (error) {
        console.error('Error:', error);
        showNotification('Ошибка при работе с избранным', 'error');
    }
}

// Функция для добавления в избранное (для карточек книг)
async function addToFavorites(bookId, button) {
    try {
        const response = await fetch(`/api/избранное/${bookId}`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            }
        });
        
        const result = await response.json();
        
        if (result.success) {
            button.innerHTML = '<i class="fas fa-heart"></i> В избранном';
            button.classList.add('added');
            button.disabled = true;
            showNotification('Книга добавлена в избранное!', 'success');
        } else {
            showNotification(result.error || 'Ошибка при добавлении в избранное', 'error');
        }
    } catch (error) {
        console.error('Error:', error);
        showNotification('Ошибка при добавлении в избранное', 'error');
    }
}

// Функция для показа уведомлений
function showNotification(message, type) {
    // Удаляем существующие уведомления
    const existingAlerts = document.querySelectorAll('.alert.position-fixed');
    existingAlerts.forEach(alert => alert.remove());
    
    const alert = document.createElement('div');
    alert.className = `alert alert-${type === 'success' ? 'success' : 'danger'} alert-dismissible fade show position-fixed`;
    alert.style.cssText = 'top: 20px; right: 20px; z-index: 1050; min-width: 300px;';
    alert.innerHTML = `
        ${message}
        <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
    `;
    
    document.body.appendChild(alert);
    
    setTimeout(() => {
        if (alert.parentNode) {
            alert.remove();
        }
    }, 3000);
}

// Глобальные функции для работы с моими книгами
async function addToMyBooks(bookId, status) {
    try {
        console.log('Adding book to my books:', bookId, status);
        
        const response = await fetch('/api/мои-книги', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                book_id: parseInt(bookId),
                status: status
            })
        });
        
        const result = await response.json();
        
        if (result.success) {
            showNotification('Книга добавлена в вашу коллекцию!', 'success');
            
            // Обновляем кнопку на странице рекомендаций
            const button = document.querySelector(`.add-to-my-books[data-book-id="${bookId}"]`);
            if (button) {
                button.innerHTML = '<i class="fas fa-check"></i> Добавлено';
                button.classList.add('btn-success');
                button.classList.remove('btn-outline-success');
                button.disabled = true;
            }

            // Закрываем модальное окно
            const modal = document.getElementById('statusModal');
            if (modal) {
                const bsModal = bootstrap.Modal.getInstance(modal);
                if (bsModal) {
                    bsModal.hide();
                }
            }
            
            // Обновляем страницу через секунду
            setTimeout(() => {
                if (window.location.pathname.includes('/книги/')) {
                    location.reload();
                }
            }, 1000);
            
        } else {
            showNotification(result.error || 'Ошибка при добавлении книги', 'error');
        }
    } catch (error) {
        console.error('Error adding book:', error);
        showNotification('Ошибка при добавлении книги', 'error');
    }
}

// Функция для показа модального окна выбора статуса
function showStatusModal(bookId) {
    console.log('Showing status modal for book:', bookId);
    
    // Удаляем существующее модальное окно если есть
    const existingModal = document.getElementById('statusModal');
    if (existingModal) existingModal.remove();

    const modalHtml = `
    <div class="modal fade" id="statusModal" tabindex="-1">
        <div class="modal-dialog">
            <div class="modal-content">
                <div class="modal-header">
                    <h5 class="modal-title">Добавить в мои книги</h5>
                    <button type="button" class="btn-close" data-bs-dismiss="modal"></button>
                </div>
                <div class="modal-body">
                    <p>Выберите статус для этой книги:</p>
                    <div class="d-grid gap-2">
                        <button type="button" class="btn btn-status" data-status="want_to_read" data-book-id="${bookId}">
                            <i class="fas fa-bookmark"></i> Хочу прочитать
                        </button>
                        <button type="button" class="btn btn-status" data-status="reading" data-book-id="${bookId}">
                            <i class="fas fa-book-open"></i> Читаю сейчас
                        </button>
                        <button type="button" class="btn btn-status" data-status="read" data-book-id="${bookId}">
                            <i class="fas fa-check"></i> Прочитано
                        </button>
                    </div>
                </div>
            </div>
        </div>
    </div>
`;
    
    document.body.insertAdjacentHTML('beforeend', modalHtml);
    const modalElement = document.getElementById('statusModal');
    const modal = new bootstrap.Modal(modalElement);
    modal.show();
    
    // Удаляем модальное окно после закрытия
    modalElement.addEventListener('hidden.bs.modal', function() {
        this.remove();
    });
}

// Функция для отправки отзыва
async function submitReview(form) {
    try {
        const formData = new FormData(form);
        const bookId = document.getElementById('favoriteBtn')?.dataset.bookId;
        
        if (!bookId) {
            showNotification('Ошибка: не найден ID книги', 'error');
            return;
        }
        
        formData.append('book_id', bookId);
        
        const response = await fetch('/api/отзыв', {
            method: 'POST',
            body: formData
        });
        
        const result = await response.json();
        
        if (result.success) {
            showNotification('Отзыв сохранен!', 'success');
            setTimeout(() => location.reload(), 1000);
        } else {
            showNotification(result.error || 'Ошибка при сохранении отзыва', 'error');
        }
    } catch (error) {
        console.error('Error:', error);
        showNotification('Ошибка при сохранении отзыва', 'error');
    }
}

// Добавляем глобальные функции для отладки
window.debugFunctions = {
    showNotification,
    addToMyBooks,
    showStatusModal
};

console.log('main.js loaded successfully');