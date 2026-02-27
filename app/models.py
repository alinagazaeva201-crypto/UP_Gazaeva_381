from sqlalchemy import Column, Integer, String, Text, Boolean, ForeignKey, DateTime, Date, JSON, Float
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.database import Base
import hashlib
from sqlalchemy.ext.declarative import declarative_base
from datetime import datetime

Base = declarative_base()

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    login = Column(String(100), unique=True, index=True)
    email = Column(String(255), unique=True, index=True, nullable=True)
    first_name = Column(String(100), nullable=True)
    last_name = Column(String(100), nullable=True)
    avatar = Column(String(255), nullable=True, default="default.jpg")
    theme = Column(String(50), nullable=True, default="purple")
    bio = Column(Text, nullable=True)
    phone = Column(String(20), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    password_hash = Column(String(255))
    is_active = Column(Boolean, default=True)
    
    
    # Дополнительные поля, если они нужны (оставляем, если они есть в БД)
    avatar_url = Column(Text, nullable=True)
    selected_avatar = Column(String(50), nullable=True)
    
    
    preferences = Column(JSON, nullable=True)
    reset_password_token = Column(String(255), nullable=True)
    reset_password_expires = Column(DateTime, nullable=True)
   
    
    favorites = relationship("UserFavorite", back_populates="user")
    user_books = relationship("UserBook", back_populates="user")
    reviews = relationship("UserReview", back_populates="user")

    def set_password(self, password: str):
        salt = "book_system_salt_2024"
        self.password_hash = hashlib.sha256((password + salt).encode()).hexdigest()

    def check_password(self, password: str) -> bool:
        salt = "book_system_salt_2024"
        return self.password_hash == hashlib.sha256((password + salt).encode()).hexdigest()
    
class Author(Base):
    __tablename__ = "authors"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(200), nullable=False)
    bio = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    books = relationship("Book", back_populates="author")

class Genre(Base):
    __tablename__ = "genres"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False, unique=True)
    description = Column(Text, nullable=True)

class Book(Base):
    __tablename__ = "books"
    
    id = Column(Integer, primary_key=True, index=True)
    title = Column(String(500), nullable=False)
    author_id = Column(Integer, ForeignKey("authors.id"))
    description = Column(Text, nullable=True)
    isbn = Column(String(20), nullable=True)
    publication_year = Column(Integer, nullable=True)
    cover_url = Column(Text, nullable=True)
    average_rating = Column(Float, nullable=True)
    page_count = Column(Integer, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    author = relationship("Author", back_populates="books")
    genres = relationship("Genre", secondary="book_genres", backref="books")
    library_books = relationship("LibraryBook", back_populates="book")
    favorites = relationship("UserFavorite", back_populates="book")
    user_books = relationship("UserBook", back_populates="book")
    reviews = relationship("UserReview", back_populates="book")

class BookGenre(Base):
    __tablename__ = "book_genres"
    
    book_id = Column(Integer, ForeignKey("books.id", ondelete="CASCADE"), primary_key=True)
    genre_id = Column(Integer, ForeignKey("genres.id", ondelete="CASCADE"), primary_key=True)

class Library(Base):
    __tablename__ = "libraries"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(300), nullable=False)
    address = Column(Text, nullable=False)
    latitude = Column(Float, nullable=True)
    longitude = Column(Float, nullable=True)
    phone = Column(String(50), nullable=True)
    working_hours = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    library_books = relationship("LibraryBook", back_populates="library")

class LibraryBook(Base):
    __tablename__ = "library_books"
    
    id = Column(Integer, primary_key=True, index=True)
    library_id = Column(Integer, ForeignKey("libraries.id", ondelete="CASCADE"))
    book_id = Column(Integer, ForeignKey("books.id", ondelete="CASCADE"))
    available = Column(Boolean, default=True)
    total_copies = Column(Integer, default=1)
    available_copies = Column(Integer, default=1)
    last_updated = Column(DateTime(timezone=True), server_default=func.now())
    
    library = relationship("Library", back_populates="library_books")
    book = relationship("Book", back_populates="library_books")

class UserFavorite(Base):
    __tablename__ = "user_favorites"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"))
    book_id = Column(Integer, ForeignKey("books.id", ondelete="CASCADE"))
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    user = relationship("User", back_populates="favorites")
    book = relationship("Book", back_populates="favorites")

class UserBook(Base):
    __tablename__ = "user_books"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"))
    book_id = Column(Integer, ForeignKey("books.id", ondelete="CASCADE"))
    read_status = Column(String(20), default='want_to_read')  # 'want_to_read', 'reading', 'read', 'abandoned'
    user_rating = Column(Integer, nullable=True)
    date_started = Column(Date, nullable=True)
    date_finished = Column(Date, nullable=True)
    notes = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    
    user = relationship("User", back_populates="user_books")
    book = relationship("Book", back_populates="user_books")

class UserReview(Base):
    __tablename__ = "user_reviews"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"))
    book_id = Column(Integer, ForeignKey("books.id", ondelete="CASCADE"))
    rating = Column(Integer, nullable=True)
    review_text = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    user = relationship("User", back_populates="reviews")
    book = relationship("Book", back_populates="reviews")
    