from sqlalchemy.orm import Session
import pandas as pd
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
from app import crud, models
from typing import List
import numpy as np

class RecommendationEngine:
    def __init__(self):
        self.vectorizer = None
        self.tfidf_matrix = None
        self.book_ids = None
        
    def fit(self, db: Session):
        """Обучает модель на основе описаний книг"""
        books = crud.get_books(db)
        if not books:
            return
            
        book_data = []
        for book in books:
            # Создаем текстовое представление книги
            genres = " ".join([genre.name for genre in book.genres])
            text = f"{book.title} {book.description or ''} {genres} {book.author.name}"
            book_data.append({
                'id': book.id,
                'text': text
            })
        
        df = pd.DataFrame(book_data)
        self.book_ids = df['id'].tolist()
        
        # Создаем TF-IDF матрицу
        self.vectorizer = TfidfVectorizer(
            max_features=1000,
            stop_words='russian',
            ngram_range=(1, 2)
        )
        self.tfidf_matrix = self.vectorizer.fit_transform(df['text'])
    
    def get_similar_books(self, book_id: int, limit: int = 5) -> List[int]:
        """Находит похожие книги по содержанию"""
        if self.tfidf_matrix is None or book_id not in self.book_ids:
            return []
            
        try:
            book_idx = self.book_ids.index(book_id)
            cosine_similarities = cosine_similarity(
                self.tfidf_matrix[book_idx:book_idx+1], 
                self.tfidf_matrix
            ).flatten()
            
            # Получаем индексы самых похожих книг (исключая саму книгу)
            similar_indices = cosine_similarities.argsort()[::-1][1:limit+1]
            similar_books = [self.book_ids[i] for i in similar_indices]
            
            return similar_books
        except:
            return []# Глобальный экземпляр движка рекомендаций
recommendation_engine = RecommendationEngine()

def get_content_based_recommendations(db: Session, book_id: int, limit: int = 5):
    """Рекомендации на основе содержания"""
    return recommendation_engine.get_similar_books(book_id, limit)

def get_popular_books(db: Session, limit: int = 10):
    """Популярные книги (по рейтингу)"""
    books = db.query(models.Book).filter(
        models.Book.average_rating.isnot(None)
    ).order_by(
        models.Book.average_rating.desc()
    ).limit(limit).all()
    return books

def get_books_by_genres(db: Session, genre_ids: List[int], limit: int = 10):
    """Книги по выбранным жанрам"""
    if not genre_ids:
        return []
        
    books = db.query(models.Book).join(models.Book.genres).filter(
        models.Genre.id.in_(genre_ids)
    ).distinct().limit(limit).all()
    
    return books
