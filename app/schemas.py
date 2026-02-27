from pydantic import BaseModel, EmailStr, ConfigDict
from typing import Optional, List
from datetime import date, datetime

class UserProfileUpdate(BaseModel):
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    email: Optional[EmailStr] = None
    password: Optional[str] = None
    bio: Optional[str] = None
    theme: Optional[str] = None

class UserSchema(BaseModel):
    model_config = ConfigDict(from_attributes=True)

class UserCreate(BaseModel):
    login: str
    password: str
    email: Optional[str] = None
    first_name: Optional[str] = None
    last_name: Optional[str] = None


class UserProfileUpdate(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    email: Optional[str] = None
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    phone: Optional[str] = None
    bio: Optional[str] = None
    theme: Optional[str] = None
    avatar: Optional[str] = None
    new_password: Optional[str] = None
    current_password: Optional[str] = None


class UserResponse(BaseModel):
    id: int
    login: str
    email: Optional[str] = None
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    avatar: Optional[str] = None
    bio: Optional[str] = None
    theme: Optional[str] = "purple"
    created_at: Optional[datetime] = None
    model_config = ConfigDict(from_attributes=True)

    @property
    def avatar_url(self) -> Optional[str]:
        if self.avatar and self.avatar != 'default.jpg':
            return f"/static/avatars/{self.avatar}"
        return None


class UserUpdate(BaseModel):
    email: Optional[EmailStr] = None
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    phone: Optional[str] = None
    bio: Optional[str] = None
    theme: Optional[str] = None

class UserProfileResponse(BaseModel):
    id: int
    login: str
    email: Optional[str] = None
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    phone: Optional[str] = None
    bio: Optional[str] = None
    avatar_url: Optional[str] = None
    theme: Optional[str] = 'purple'
    created_at: datetime
    model_config = ConfigDict(from_attributes=True)

class AuthorBase(BaseModel):
    name: str
    bio: Optional[str] = None

class Author(AuthorBase):
    id: int
    model_config = ConfigDict(from_attributes=True)

class GenreBase(BaseModel):
    name: str
    description: Optional[str] = None

class Genre(GenreBase):
    id: int
    model_config = ConfigDict(from_attributes=True)

class BookBase(BaseModel):
    title: str
    description: Optional[str] = None
    publication_year: Optional[int] = None
    average_rating: Optional[float] = None
    page_count: Optional[int] = None

class Book(BookBase):
    id: int
    author: Author
    genres: List['Genre'] = []
    model_config = ConfigDict(from_attributes=True)

class UserLogin(BaseModel):
    login: str
    password: str

class UserProfile(BaseModel):
    id: int
    login: str
    email: Optional[str] = None
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    created_at: datetime
    model_config = ConfigDict(from_attributes=True)

class Token(BaseModel):
    access_token: str
    token_type: str

class UserFavoriteBase(BaseModel):
    book_id: int

class UserFavorite(UserFavoriteBase):
    id: int
    user_id: int
    book: Book
    created_at: datetime
    model_config = ConfigDict(from_attributes=True)

class UserBookCreate(BaseModel):
    book_id: int
    read_status: str = 'want_to_read'
    user_rating: Optional[int] = None
    notes: Optional[str] = None

class UserBook(UserBookCreate):
    id: int
    user_id: int
    book: Book
    created_at: datetime
    updated_at: datetime
    model_config = ConfigDict(from_attributes=True)

class ReviewCreate(BaseModel):
    book_id: int
    rating: Optional[int] = None
    review_text: Optional[str] = None

class Review(ReviewCreate):
    id: int
    user_id: int
    created_at: datetime
    model_config = ConfigDict(from_attributes=True)

class BookDetail(Book):
    user_review: Optional[Review] = None
    user_book_status: Optional[str] = None
    in_favorites: bool = False