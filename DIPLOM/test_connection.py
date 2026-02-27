import sys
import os
from sqlalchemy import create_engine, text
from app.database import SessionLocal
from app import models

def test_database():
    try:
        db = SessionLocal()
        
        # Проверим количество книг
        book_count = db.query(models.Book).count()
        print(f"📚 Книг в базе: {book_count}")
        
        # Проверим авторов
        author_count = db.query(models.Author).count()
        print(f"👤 Авторов в базе: {author_count}")
        
        # Проверим жанры
        genre_count = db.query(models.Genre).count()
        print(f"📂 Жанров в базе: {genre_count}")
        
        # Проверим поиск
        books = db.query(models.Book).join(models.Author).filter(
            models.Author.name.ilike('%Пушкин%')
        ).all()
        
        print(f"🔍 Найдено книг Пушкина: {len(books)}")
        
        # Покажем несколько книг
        print("\n📖 Примеры книг:")
        some_books = db.query(models.Book).limit(3).all()
        for book in some_books:
            print(f"   - {book.title} (ID: {book.id})")
        
        db.close()
        print("\n✅ База данных подключена и работает!")
        
    except Exception as e:
        print(f"❌ Ошибка: {e}")

if __name__ == "__main__":
    test_database()