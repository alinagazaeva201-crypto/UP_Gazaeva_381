from fastapi import FastAPI, Depends, HTTPException, Request, Form, File, UploadFile
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse, RedirectResponse, JSONResponse
from sqlalchemy.orm import Session
from typing import List, Optional
from fastapi import FastAPI, Depends, HTTPException, Request, Form, File, UploadFile, Query
from .schemas import UserSchema
from app.models import User
import uvicorn
import os
import shutil
from datetime import datetime
import random
import uuid
from pathlib import Path
from PIL import Image
import io

# Импортируем только необходимые функции
from app.database import get_db, engine, SessionLocal
from app import models
from app import crud, schemas, auth
from app.auth import get_current_user, create_access_token

# Создаем таблицы
models.Base.metadata.create_all(bind=engine)

# Полностью отключаем документацию
app = FastAPI(
    title="Книжная рекомендательная система",
    version="1.0.0",
    docs_url=None,
    redoc_url=None,
    openapi_url=None
)

# Настройки для аватаров
AVATAR_DIR = Path("static/avatars")
AVATAR_DIR.mkdir(parents=True, exist_ok=True)
ALLOWED_EXTENSIONS = {"jpg", "jpeg", "png", "gif", "webp"}
MAX_FILE_SIZE = 5 * 1024 * 1024  # 5MB


# Настройка статических файлов и шаблонов
app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates")

# Функция для получения БД без Depends
def get_db_dependency():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# Главная страница
@app.get("/", response_class=HTMLResponse)
async def read_root(request: Request):
    db = next(get_db_dependency())
    try:
        user = await get_current_user(request, db)
        
        if user:
            popular_books = crud.get_popular_books(db, 12)
            genres = crud.get_genres(db)
            
            return templates.TemplateResponse("index.html", {
                "request": request,
                "popular_books": popular_books,
                "genres": genres,
                "user": user
            })
        else:
            return templates.TemplateResponse("landing.html", {
                "request": request,
                "user": None
            })
    finally:
        db.close()

# Лендинг страница
@app.get("/главная", response_class=HTMLResponse)
async def landing_page(request: Request):
    return templates.TemplateResponse("landing.html", {"request": request})

# Страница входа
@app.get("/вход", response_class=HTMLResponse)
async def login_page(request: Request):
    db = next(get_db_dependency())
    try:
        user = await get_current_user(request, db)
        if user:
            return RedirectResponse(url="/", status_code=303)
        return templates.TemplateResponse("login.html", {"request": request})
    finally:
        db.close()
@app.post("/api/test-upload")
async def test_upload(
    file: UploadFile = File(...)
):
    """Простой тестовый эндпоинт без аутентификации"""
    try:
        contents = await file.read()
        filename = f"test_{file.filename}"
        filepath = AVATAR_DIR / filename
        
        print(f"Тестовая загрузка: {filename}, размер: {len(contents)} байт")
        
        # Просто сохраняем как есть
        with open(filepath, "wb") as f:
            f.write(contents)
        
        # Проверяем
        if filepath.exists():
            print(f"Тестовый файл сохранён: {filepath}, размер: {filepath.stat().st_size} байт")
            return JSONResponse({
                "success": True,
                "message": f"Файл {filename} сохранен",
                "path": str(filepath.absolute()),
                "size": len(contents)
            })
        else:
            print("ОШИБКА: Тестовый файл не создался!")
            return JSONResponse({
                "success": False,
                "error": "Файл не был создан"
            }, status_code=500)
            
    except Exception as e:
        print(f"Ошибка в test_upload: {e}")
        import traceback
        traceback.print_exc()
        return JSONResponse({
            "success": False,
            "error": str(e)
        }, status_code=500)
    
@app.post("/вход", response_class=HTMLResponse)
async def login_user(
    request: Request,
    login: str = Form(...),
    password: str = Form(...)
):
    db = next(get_db_dependency())
    try:
        user = crud.authenticate_user(db, login, password)
        if not user:
            return templates.TemplateResponse("login.html", {
                "request": request,
                "error": "Неверный логин или пароль"
            })
        
        access_token = create_access_token({"user_id": user.id})
        response = RedirectResponse(url="/", status_code=303)
        response.set_cookie(key="access_token", value=access_token, httponly=True)
        return response
    finally:
        db.close()

# Страница регистрации
@app.get("/регистрация", response_class=HTMLResponse)
async def register_page(request: Request):
    db = next(get_db_dependency())
    try:
        user = await get_current_user(request, db)
        if user:
            return RedirectResponse(url="/", status_code=303)
        return templates.TemplateResponse("register.html", {"request": request})
    finally:
        db.close()

@app.post("/регистрация", response_class=HTMLResponse)
async def register_user(
    request: Request,
    login: str = Form(...),
    password: str = Form(...),
    email: str = Form(None),
    first_name: str = Form(None),
    last_name: str = Form(None)
):
    db = next(get_db_dependency())
    try:
        user_data = schemas.UserCreate(
            login=login,
            password=password,
            email=email,
            first_name=first_name,
            last_name=last_name
        )
        
        user = crud.create_user_with_password(db, user_data)
        if not user:
            return templates.TemplateResponse("register.html", {
                "request": request,
                "error": "Пользователь с таким логином уже существует"
            })
        
        return RedirectResponse(url="/вход", status_code=303)
    finally:
        db.close()

# Выход
@app.get("/выход")
async def logout():
    response = RedirectResponse(url="/")
    response.delete_cookie("access_token")
    return response

# Страница всех книг
@app.get("/книги", response_class=HTMLResponse)
async def books_page(request: Request, search: str = Query(None)):
    db = next(get_db_dependency())
    try:
        user = await get_current_user(request, db)
        if not user:
            return RedirectResponse(url="/вход", status_code=303)
        
        if search:
            books = crud.search_books(db, search, 50)
        else:
            books = crud.get_books(db, 0, 50)
        
        return templates.TemplateResponse("books.html", {
            "request": request,
            "books": books,
            "search_query": search,
            "user": user
        })
    finally:
        db.close()

# Страница рекомендаций
@app.get("/рекомендации", response_class=HTMLResponse)
async def recommendations_page(request: Request):
    db = next(get_db_dependency())
    try:
        user = await get_current_user(request, db)
        if not user:
            return RedirectResponse(url="/вход", status_code=303)
        
        recommendations = crud.get_recommendations(db, user.id, 12)
        
        return templates.TemplateResponse("recommendations.html", {
            "request": request,
            "recommendations": recommendations,
            "user": user
        })
    finally:
        db.close()

# Страница профиля
@app.get("/профиль", response_class=HTMLResponse)
async def profile_page(request: Request):
    db = next(get_db_dependency())
    try:
        user = await get_current_user(request, db)
        if not user:
            return RedirectResponse(url="/вход", status_code=303)
        
        # Получаем избранные книги
        favorites = crud.get_user_favorites(db, user.id)
        favorite_books = [fav.book for fav in favorites] if favorites else []
        
        # Получаем книги пользователя по статусам
        want_to_read = crud.get_user_books_by_status(db, user.id, 'want_to_read') or []
        reading = crud.get_user_books_by_status(db, user.id, 'reading') or []
        read = crud.get_user_books_by_status(db, user.id, 'read') or []
        
        # Получаем статистику пользователя
        user_stats = {
            "favorites": len(favorite_books),
            "want_to_read": len(want_to_read),
            "reading": len(reading),
            "read": len(read)
        }
        
        return templates.TemplateResponse("profile.html", {
            "request": request,
            "user": user,
            "user_stats": user_stats,
            "favorite_books": favorite_books,
            "want_to_read_books": [ub.book for ub in want_to_read] if want_to_read else [],
            "reading_books": [ub.book for ub in reading] if reading else [],
            "read_books": [ub.book for ub in read] if read else []
        })
    finally:
        db.close()

# Детальная страница книги
@app.get("/книги/{book_id}", response_class=HTMLResponse)
async def book_detail_page(request: Request, book_id: int):
    db = next(get_db_dependency())
    try:
        user = await get_current_user(request, db)
        if not user:
            return RedirectResponse(url="/вход", status_code=303)
        
        book_data = crud.get_book_with_user_data(db, book_id, user.id)
        if not book_data:
            raise HTTPException(status_code=404, detail="Книга не найдена")
        
        reviews = crud.get_book_reviews(db, book_id)
        
        return templates.TemplateResponse("book_detail.html", {
            "request": request,
            "book": book_data['book'],
            "in_favorites": book_data['in_favorites'],
            "user_book_status": book_data['user_book_status'],
            "user_review": book_data['user_review'],
            "reviews": reviews,
            "user": user
        })
    finally:
        db.close()

# Telegram Bot страница
@app.get("/telegram-bot")
async def telegram_bot_page(request: Request):
    """Страница с информацией о Telegram боте"""
    db = next(get_db_dependency())
    try:
        user = await get_current_user(request, db)
        return templates.TemplateResponse(
            "telegram_bot.html",
            {"request": request, "user": user}
        )
    finally:
        db.close()

# API эндпоинты
@app.post("/api/create-default-avatars")
async def create_default_avatars(current_user = Depends(get_current_user)):
    """Создание стандартных аватаров"""
    try:
        # Создаем 5 стандартных аватаров
        avatars = [
            ("avatar1.png", "#667eea", "#764ba2"),
            ("avatar2.png", "#f472b6", "#db2777"),
            ("avatar3.png", "#3b82f6", "#2563eb"),
            ("avatar4.png", "#10b981", "#059669"),
            ("avatar5.png", "#f59e0b", "#d97706")
        ]
        
        from PIL import Image, ImageDraw
        for avatar_name, color1, color2 in avatars:
            # Создаем простое изображение аватара
            img = Image.new('RGB', (100, 100), color=color1)
            draw = ImageDraw.Draw(img)
            # Рисуем круг
            draw.ellipse([10, 10, 90, 90], fill=color2)
            
            # Сохраняем изображение
            avatar_path = DEFAULT_AVATARS_DIR / avatar_name
            img.save(avatar_path)
            print(f"Создан аватар: {avatar_path}")
        
        return JSONResponse({"success": True, "message": "Аватары созданы"})
    except Exception as e:
        print(f"Ошибка создания аватаров: {str(e)}")
        return JSONResponse({"success": False, "error": str(e)})

@app.post("/api/upload-avatar")
async def upload_avatar(
    file: UploadFile = File(...),
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    try:
        if file.content_type not in ["image/jpeg", "image/png", "image/gif", "image/webp"]:
            raise HTTPException(status_code=400, detail="Неверный формат файла")

        file_ext = file.filename.split('.')[-1]
        new_filename = f"user_{current_user.id}_avatar.{file_ext}"
        filepath = AVATAR_DIR / new_filename

        with open(filepath, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)

        current_user.avatar = new_filename
        db.commit()

        return JSONResponse({
            "success": True,
            "avatar_url": new_filename,
            "message": "Аватар успешно загружен"
        })

    except Exception as e:
        print(f"Ошибка загрузки аватара: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Ошибка загрузки: {str(e)}")


    
@app.post("/api/обновить-тему")
async def update_user_theme(
    request: Request,
    theme_data: dict,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    if not current_user:
        raise HTTPException(status_code=401, detail="Не авторизован")
    
    # Создаем объект обновления профиля
    user_update = schemas.UserProfileUpdate(theme=theme_data.get('theme'))
    
    # Обновляем тему пользователя
    updated_user = crud.update_user_profile(db, current_user.id, user_update)
    
    if updated_user and hasattr(updated_user, 'error'):
        raise HTTPException(status_code=400, detail=updated_user['error'])
    
    return {"success": True, "message": "Тема обновлена", "theme": theme_data.get('theme')}
# После создания AVATAR_DIR добавьте:
DEFAULT_AVATARS_DIR = AVATAR_DIR / "default"
DEFAULT_AVATARS_DIR.mkdir(parents=True, exist_ok=True)



# Страница редактирования профиля
@app.get("/редактировать-профиль", response_class=HTMLResponse)
async def edit_profile_page(request: Request):
    db = next(get_db_dependency())
    try:
        user = await get_current_user(request, db)
        if not user:
            return RedirectResponse(url="/вход", status_code=303)

        return templates.TemplateResponse("edit_profile.html", {
            "request": request,
            "user": user
        })
    finally:
        db.close()

# Обработчик формы редактирования профиля
@app.post("/редактировать-профиль", response_class=HTMLResponse)
async def update_profile(
    request: Request,
    first_name: str = Form(None),
    last_name: str = Form(None),
    email: str = Form(None),
    current_password: str = Form(None),
    new_password: str = Form(None),
    confirm_password: str = Form(None)
):
    db = next(get_db_dependency())
    try:
        user = await get_current_user(request, db)
        if not user:
            return RedirectResponse(url="/вход", status_code=303)

        # Обновляем основную информацию
        user_update = schemas.UserProfileUpdate(
            first_name=first_name,
            last_name=last_name,
            email=email
        )

        # Обновляем пароль, если он указан
        if new_password and new_password == confirm_password:
            if not auth.verify_password(current_password, user.hashed_password):
                return templates.TemplateResponse("edit_profile.html", {
                    "request": request,
                    "user": user,
                    "error": "Текущий пароль неверен"
                })
            user_update.password = new_password

        updated_user = crud.update_user_profile(db, user.id, user_update)

        if updated_user and hasattr(updated_user, 'error'):
            return templates.TemplateResponse("edit_profile.html", {
                "request": request,
                "user": user,
                "error": updated_user['error']
            })

        return RedirectResponse(url="/профиль", status_code=303)

    except Exception as e:
        print(f"Ошибка обновления профиля: {str(e)}")
        return templates.TemplateResponse("edit_profile.html", {
            "request": request,
            "user": user,
            "error": f"Ошибка обновления профиля: {str(e)}"
        })
    finally:
        db.close()


@app.post("/api/select-avatar")
async def select_avatar(data: dict, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    avatar_name = data.get("avatar_name")

    current_user.avatar = avatar_name
    db.commit()

    return {
        "success": True,
        "avatar_url": f"/static/avatars/default/{avatar_name}"
    }
@app.post("/api/обновить-био")
async def update_bio(
    bio: str = Form(None),
    current_user = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Обновление информации "О себе"
    """
    try:
        user_update = schemas.UserProfileUpdate(bio=bio)
        updated_user = crud.update_user_profile(db, current_user.id, user_update)
        
        if updated_user and hasattr(updated_user, 'error'):
            raise HTTPException(status_code=400, detail=updated_user['error'])
        
        return JSONResponse({
            "success": True,
            "bio": bio,
            "message": "Информация успешно обновлена"
        })
        
    except Exception as e:
        print(f"Ошибка обновления био: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Ошибка обновления: {str(e)}")

# API для избранного
@app.post("/api/избранное/{book_id}")
async def add_to_favorites_api(book_id: int, request: Request):
    db = next(get_db_dependency())
    try:
        user = await get_current_user(request, db)
        if not user:
            return JSONResponse({"success": False, "error": "Не авторизован"})
        
        # Проверяем существование книги
        book = crud.get_book(db, book_id)
        if not book:
            return JSONResponse({"success": False, "error": "Книга не найдена"})
        
        result = crud.add_to_favorites(db, user.id, book_id)
        return JSONResponse({"success": True, "favorite_id": result.id})
    except Exception as e:
        return JSONResponse({"success": False, "error": str(e)})
    finally:
        db.close()

@app.delete("/api/избранное/{book_id}")
async def remove_from_favorites_api(book_id: int, request: Request):
    db = next(get_db_dependency())
    try:
        user = await get_current_user(request, db)
        if not user:
            return JSONResponse({"success": False, "error": "Не авторизован"})
        
        result = crud.remove_from_favorites(db, user.id, book_id)
        return JSONResponse({"success": result})
    except Exception as e:
        return JSONResponse({"success": False, "error": str(e)})
    finally:
        db.close()

# API для моих книг
@app.post("/api/мои-книги")
async def add_to_my_books_api(request: Request):
    db = next(get_db_dependency())
    try:
        user = await get_current_user(request, db)
        if not user:
            return JSONResponse({"success": False, "error": "Не авторизован"})
        
        # Получаем JSON данные вместо Form
        data = await request.json()
        book_id = data.get('book_id')
        status = data.get('status', 'want_to_read')
        
        if not book_id:
            return JSONResponse({"success": False, "error": "ID книги обязателен"})
        
        # Проверяем существование книги
        book = crud.get_book(db, book_id)
        if not book:
            return JSONResponse({"success": False, "error": "Книга не найдена"})
        
        user_book_data = schemas.UserBookCreate(
            book_id=book_id,
            read_status=status
        )
        
        result = crud.add_user_book(db, user.id, user_book_data)
        return JSONResponse({"success": True, "user_book_id": result.id})
    except Exception as e:
        return JSONResponse({"success": False, "error": str(e)})
    finally:
        db.close()

# API для удаления из коллекции
@app.post("/api/удалить-из-коллекции")
async def remove_from_collection_api(request: Request):
    db = next(get_db_dependency())
    try:
        user = await get_current_user(request, db)
        if not user:
            return JSONResponse({"success": False, "error": "Не авторизован"})
        
        data = await request.json()
        book_id = data.get('book_id')
        
        if not book_id:
            return JSONResponse({"success": False, "error": "ID книги обязателен"})
        
        # Удаляем запись из user_books
        user_book = db.query(models.UserBook).filter(
            models.UserBook.user_id == user.id,
            models.UserBook.book_id == book_id
        ).first()
        
        if user_book:
            db.delete(user_book)
            db.commit()
            return JSONResponse({"success": True})
        else:
            return JSONResponse({"success": False, "error": "Книга не найдена в коллекции"})
            
    except Exception as e:
        return JSONResponse({"success": False, "error": str(e)})
    finally:
        db.close()

# API для отзывов
@app.post("/api/отзыв")
async def add_review_api(
    request: Request,
    book_id: int = Form(...),
    rating: int = Form(None),
    review_text: str = Form(None)
):
    db = next(get_db_dependency())
    try:
        user = await get_current_user(request, db)
        if not user:
            return JSONResponse({"success": False, "error": "Не авторизован"})
        
        review_data = schemas.ReviewCreate(
            book_id=book_id,
            rating=rating,
            review_text=review_text
        )
        
        result = crud.add_review(db, user.id, review_data)
        return JSONResponse({"success": True, "review_id": result.id})
    except Exception as e:
        return JSONResponse({"success": False, "error": str(e)})
    finally:
        db.close()

# API для получения информации о книге
@app.get("/api/книга/{book_id}")
async def get_book_api(book_id: int, request: Request):
    db = next(get_db_dependency())
    try:
        user = await get_current_user(request, db)
        if not user:
            return JSONResponse({"success": False, "error": "Не авторизован"})
        
        book_data = crud.get_book_with_user_data(db, book_id, user.id)
        if not book_data:
            return JSONResponse({"success": False, "error": "Книга не найдена"})
        
        # Преобразуем в словарь для JSON
        book_dict = {
            'book': {
                'id': book_data['book'].id,
                'title': book_data['book'].title,
                'description': book_data['book'].description,
                'publication_year': book_data['book'].publication_year,
                'average_rating': book_data['book'].average_rating,
                'page_count': book_data['book'].page_count,
                'author': {
                    'id': book_data['book'].author.id,
                    'name': book_data['book'].author.name
                } if book_data['book'].author else None,
                'genres': [{'id': g.id, 'name': g.name} for g in book_data['book'].genres]
            },
            'in_favorites': book_data['in_favorites'],
            'user_book_status': book_data['user_book_status'],
            'user_review': {
                'id': book_data['user_review'].id,
                'rating': book_data['user_review'].rating,
                'review_text': book_data['user_review'].review_text
            } if book_data['user_review'] else None
        }
        
        return JSONResponse({"success": True, "data": book_dict})
    except Exception as e:
        return JSONResponse({"success": False, "error": str(e)})
    finally:
        db.close()

# API для Telegram бота
@app.get("/api/random-book")
async def get_random_book_api():
    """API для получения случайной книги (для Telegram бота)"""
    db = next(get_db_dependency())
    try:
        books = crud.get_books(db, 0, 1000)
        
        if not books:
            return JSONResponse({
                "success": False,
                "error": "Книги не найдены"
            })
        
        random_book = random.choice(books)
        
        book_data = {
            "id": random_book.id,
            "title": random_book.title,
            "author": random_book.author.name if random_book.author else "Автор не указан",
            "description": random_book.description or "Описание отсутствует",
            "publication_year": random_book.publication_year,
            "genres": [genre.name for genre in random_book.genres],
            "page_count": random_book.page_count,
            "average_rating": float(random_book.average_rating) if random_book.average_rating else 0.0
        }
        
        return JSONResponse({
            "success": True,
            "book": book_data
        })
        
    except Exception as e:
        return JSONResponse({
            "success": False,
            "error": f"Ошибка при получении книги: {str(e)}"
        })
    finally:
        db.close()

@app.post("/api/chat")
async def chat_handler_api(request: dict):
    """API для обработки сообщений от Telegram бота"""
    try:
        user_message = request.get("message", "").lower().strip()
        
        # Простые ответы на популярные запросы
        responses = {
            "привет": "Привет! Я книжный бот. Чем могу помочь? 📚",
            "hello": "Hello! I'm a book bot. How can I help you? 📚",
            "книги": "У нас есть множество книг! Попробуйте команду 'Случайная книга' или воспользуйтесь поиском.",
            "рекомендации": "Для получения рекомендаций зайдите в наше веб-приложение!",
            "помощь": "Доступные команды:\n• Случайная книга\n• Поиск [название]\n• Жанры\n• Помощь",
            "help": "Available commands:\n• Random book\n• Search [title]\n• Genres\n• Help",
            "жанры": "У нас есть книги различных жанров: фантастика, детективы, романы, научная литература и многое другое!",
            "genres": "We have books of various genres: fiction, detective stories, novels, scientific literature and much more!"
        }
        
        # Поиск по ключевым словам
        response_text = responses.get(user_message)
        if not response_text:
            if "случайная" in user_message or "random" in user_message:
                # Перенаправляем на эндпоинт случайной книги
                db = next(get_db_dependency())
                try:
                    books = crud.get_books(db, 0, 100)
                    if books:
                        random_book = random.choice(books)
                        response_text = f"📖 {random_book.title}\n✍️ Автор: {random_book.author.name if random_book.author else 'Не указан'}\n📚 Жанр: {', '.join([g.name for g in random_book.genres])}\n⭐ Рейтинг: {random_book.average_rating or 'Нет оценок'}"
                    else:
                        response_text = "❌ Книги временно недоступны"
                except:
                    response_text = "❌ Ошибка при получении книги"
                finally:
                    db.close()
            elif user_message.startswith("поиск ") or user_message.startswith("search "):
                response_text = "🔍 Для поиска книг воспользуйтесь нашим веб-приложением!"
            else:
                response_text = "Я пока не умею отвечать на такие вопросы 😊\nПопробуйте спросить о книгах или воспользуйтесь командой 'Помощь'"
        
        return JSONResponse({
            "success": True,
            "response": response_text
        })
        
    except Exception as e:
        return JSONResponse({
            "success": False,
            "error": f"Ошибка обработки сообщения: {str(e)}"
        })

@app.get("/api/books/search")
async def search_books_api(query: str = Query(..., description="Поисковый запрос")):
    """API для поиска книг (для Telegram бота)"""
    db = next(get_db_dependency())
    try:
        if not query or len(query.strip()) < 2:
            return JSONResponse({
                "success": False,
                "error": "Поисковый запрос должен содержать минимум 2 символа"
            })
        
        books = crud.search_books(db, query, 10)  # Ограничиваем 10 результатами
        
        if not books:
            return JSONResponse({
                "success": True,
                "message": f"По запросу '{query}' ничего не найдено",
                "books": []
            })
        
        # Форматируем книги для ответа
        formatted_books = []
        for book in books:
            formatted_books.append({
                "id": book.id,
                "title": book.title,
                "author": book.author.name if book.author else "Автор не указан",
                "genres": [genre.name for genre in book.genres],
                "average_rating": float(book.average_rating) if book.average_rating else 0.0
            })
        
        return JSONResponse({
            "success": True,
            "books": formatted_books,
            "count": len(formatted_books)
        })
        
    except Exception as e:
        return JSONResponse({
            "success": False,
            "error": f"Ошибка поиска: {str(e)}"
        })
    finally:
        db.close()

# Terms and Privacy pages
@app.get("/terms", response_class=HTMLResponse)
async def terms_page(request: Request):
    db = next(get_db_dependency())
    try:
        user = await get_current_user(request, db)
        return templates.TemplateResponse("terms.html", {"request": request, "user": user})
    finally:
        db.close()

@app.get("/privacy", response_class=HTMLResponse)
async def privacy_page(request: Request):
    db = next(get_db_dependency())
    try:
        user = await get_current_user(request, db)
        return templates.TemplateResponse("privacy.html", {"request": request, "user": user})
    finally:
        db.close()

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000, reload=True)