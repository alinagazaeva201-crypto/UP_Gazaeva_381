from sqlalchemy.orm import Session
from sqlalchemy import or_, and_, func
from typing import List, Optional
import random
from app import models, schemas

# Добавляем новые функции для работы с пользователями
# В файле crud.py в функции update_user_profile добавьте обновление темы

def update_user_profile(db: Session, user_id: int, user_update: schemas.UserProfileUpdate):
    user = db.query(models.User).filter(models.User.id == user_id).first()
    if not user:
        return None
    
    # Проверяем текущий пароль если меняем пароль
    if user_update.new_password:
        if not user_update.current_password or not user.check_password(user_update.current_password):
            return {"error": "Неверный текущий пароль"}
        user.set_password(user_update.new_password)
    
    # Обновляем остальные поля (только если они не None)
    if user_update.email is not None:
        user.email = user_update.email
    if user_update.first_name is not None:
        user.first_name = user_update.first_name
    if user_update.last_name is not None:
        user.last_name = user_update.last_name
    if user_update.phone is not None:
        user.phone = user_update.phone
    if user_update.bio is not None:
        user.bio = user_update.bio
    if user_update.theme is not None:  # <-- ДОБАВЬТЕ ЭТОТ БЛОК
        user.theme = user_update.theme
    
    db.commit()
    db.refresh(user)
    return user

def update_user_avatar(db: Session, user_id: int, avatar: str):
    db_user = db.query(models.User).filter(models.User.id == user_id).first()
    if db_user:
        db_user.avatar = avatar
        db.commit()
        db.refresh(db_user)
        return db_user
    return None

def update_user_profile(db: Session, user_id: int, user_update: schemas.UserProfileUpdate):
    """Обновление профиля пользователя"""
    db_user = db.query(models.User).filter(models.User.id == user_id).first()
    if db_user:
        update_data = user_update.dict(exclude_unset=True)
        for field, value in update_data.items():
            setattr(db_user, field, value)
        db.commit()
        db.refresh(db_user)
        return db_user
    return None

# Функции для пользователей
def create_user_with_password(db: Session, user: schemas.UserCreate):
    existing_user = db.query(models.User).filter(
        models.User.login == user.login
    ).first()
    
    if existing_user:
        return None
    
    db_user = models.User(
        login=user.login,
        email=user.email,
        first_name=user.first_name,
        last_name=user.last_name
    )
    db_user.set_password(user.password)
    
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return db_user

def authenticate_user(db: Session, login: str, password: str):
    user = db.query(models.User).filter(models.User.login == login).first()
    if not user or not user.check_password(password):
        return None
    return user

def get_user_by_id(db: Session, user_id: int):
    return db.query(models.User).filter(models.User.id == user_id).first()

# Функции для книг
def get_books(db: Session, skip: int = 0, limit: int = 100):
    return db.query(models.Book).offset(skip).limit(limit).all()

def get_book(db: Session, book_id: int):
    return db.query(models.Book).filter(models.Book.id == book_id).first()

def get_book_with_user_data(db: Session, book_id: int, user_id: int):
    book = db.query(models.Book).filter(models.Book.id == book_id).first()
    if not book:
        return None
    
    # Проверяем, в избранном ли книга
    favorite = db.query(models.UserFavorite).filter(
        models.UserFavorite.user_id == user_id,
        models.UserFavorite.book_id == book_id
    ).first()
    
    # Проверяем статус чтения
    user_book = db.query(models.UserBook).filter(
        models.UserBook.user_id == user_id,
        models.UserBook.book_id == book_id
    ).first()
    
    # Получаем отзыв пользователя
    user_review = db.query(models.UserReview).filter(
        models.UserReview.user_id == user_id,
        models.UserReview.book_id == book_id
    ).first()
    
    return {
        'book': book,
        'in_favorites': favorite is not None,
        'user_book_status': user_book.read_status if user_book else None,
        'user_review': user_review
    }

def search_books(db: Session, query: str, limit: int = 10):
    search = f"%{query}%"
    return db.query(models.Book).join(models.Author).join(models.Book.genres).filter(
        or_(
            models.Book.title.ilike(search),
            models.Book.description.ilike(search),
            models.Author.name.ilike(search),
            models.Genre.name.ilike(search)
        )
    ).distinct().limit(limit).all()

def get_random_book(db: Session):
    total = db.query(models.Book).count()
    if total == 0:
        return None
    random_index = random.randint(0, total - 1)
    return db.query(models.Book).offset(random_index).first()

# Функции для избранного
def get_user_favorites(db: Session, user_id: int):
    return db.query(models.UserFavorite).filter(
        models.UserFavorite.user_id == user_id
    ).all()

def add_to_favorites(db: Session, user_id: int, book_id: int):
    existing = db.query(models.UserFavorite).filter(
        models.UserFavorite.user_id == user_id,
        models.UserFavorite.book_id == book_id
    ).first()
    
    if existing:
        return existing
    
    db_favorite = models.UserFavorite(user_id=user_id, book_id=book_id)
    db.add(db_favorite)
    db.commit()
    db.refresh(db_favorite)
    return db_favorite

def remove_from_favorites(db: Session, user_id: int, book_id: int):
    favorite = db.query(models.UserFavorite).filter(
        models.UserFavorite.user_id == user_id,
        models.UserFavorite.book_id == book_id
    ).first()
    
    if favorite:
        db.delete(favorite)
        db.commit()
        return True
    return False

# Функции для библиотек
def get_libraries_with_book(db: Session, book_id: int):
    return db.query(models.LibraryBook).filter(
        models.LibraryBook.book_id == book_id,
        models.LibraryBook.available == True
    ).all()

def get_all_libraries(db: Session):
    return db.query(models.Library).all()

# Функции для жанров
def get_genres(db: Session):
    return db.query(models.Genre).all()

# Функции для пользовательских книг (статусы чтения)
def add_user_book(db: Session, user_id: int, user_book: schemas.UserBookCreate):
    existing = db.query(models.UserBook).filter(
        models.UserBook.user_id == user_id,
        models.UserBook.book_id == user_book.book_id
    ).first()
    
    if existing:
        # Обновляем существующую запись
        existing.read_status = user_book.read_status
        existing.user_rating = user_book.user_rating
        existing.notes = user_book.notes
    else:
        # Создаем новую запись
        existing = models.UserBook(
            user_id=user_id,
            book_id=user_book.book_id,
            read_status=user_book.read_status,
            user_rating=user_book.user_rating,
            notes=user_book.notes
        )
        db.add(existing)
    
    db.commit()
    db.refresh(existing)
    return existing

def get_user_books_by_status(db: Session, user_id: int, status: str = None):
    query = db.query(models.UserBook).filter(models.UserBook.user_id == user_id)
    if status:
        query = query.filter(models.UserBook.read_status == status)
    return query.all()

# Функции для отзывов
def add_review(db: Session, user_id: int, review: schemas.ReviewCreate):
    existing = db.query(models.UserReview).filter(
        models.UserReview.user_id == user_id,
        models.UserReview.book_id == review.book_id
    ).first()
    
    if existing:
        # Обновляем существующий отзыв
        existing.rating = review.rating
        existing.review_text = review.review_text
    else:
        # Создаем новый отзыв
        existing = models.UserReview(
            user_id=user_id,
            book_id=review.book_id,
            rating=review.rating,
            review_text=review.review_text
        )
        db.add(existing)
    
    db.commit()
    db.refresh(existing)
    return existing

def get_book_reviews(db: Session, book_id: int):
    return db.query(models.UserReview).filter(
        models.UserReview.book_id == book_id
    ).all()

# Рекомендации
def get_recommendations(db: Session, user_id: int, limit: int = 10):
    
    user_favorites = db.query(models.UserFavorite.book_id).filter(
        models.UserFavorite.user_id == user_id
    ).all()
    
    user_books = db.query(models.UserBook.book_id).filter(
        models.UserBook.user_id == user_id
    ).all()
    
    read_book_ids = [book_id for (book_id,) in user_favorites + user_books]
    
    if not read_book_ids:
        
        return get_popular_books(db, limit)
    
    favorite_genres = db.query(models.Genre.id).join(models.BookGenre).filter(
        models.BookGenre.book_id.in_(read_book_ids)
    ).distinct().all()
    
    favorite_authors = db.query(models.Book.author_id).filter(
        models.Book.id.in_(read_book_ids)
    ).distinct().all()
    
    genre_ids = [genre_id for (genre_id,) in favorite_genres]
    author_ids = [author_id for (author_id,) in favorite_authors]
    
    # Рекомендуем книги тех же жанров и авторов, которые пользователь еще не читал
    recommended_books = db.query(models.Book).join(models.Book.genres).filter(
        models.Book.id.notin_(read_book_ids),
        or_(
            models.Book.author_id.in_(author_ids),
            models.Genre.id.in_(genre_ids)
        )
    ).distinct().limit(limit).all()
    
    # Если рекомендаций мало, дополняем популярными книгами
    if len(recommended_books) < limit:
        popular_books = get_popular_books(db, limit - len(recommended_books))
        recommended_book_ids = [book.id for book in recommended_books]
        additional_books = [book for book in popular_books if book.id not in recommended_book_ids and book.id not in read_book_ids]
        recommended_books.extend(additional_books)
    
    return recommended_books

def get_popular_books(db: Session, limit: int = 10):
    books = db.query(models.Book).filter(
        models.Book.average_rating.isnot(None)
    ).order_by(
        models.Book.average_rating.desc()
    ).limit(limit).all()
    return books
