import requests
import time
import json
import os
import re
import random
from dotenv import load_dotenv

# Загружаем переменные окружения
load_dotenv()

# Конфигурация
BOT_TOKEN = os.getenv("BOT_TOKEN", "7738004937:AAGLA3OGzuZ6rgXJoSLwrvqEu4yoWGdigNI")
API_BASE_URL = os.getenv("API_BASE_URL", "http://127.0.0.1:8000")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")

class AdvancedBookBot:
    def __init__(self, token):
        self.token = token
        self.base_url = f"https://api.telegram.org/bot{token}"
        self.user_states = {}
        self.chat_history = {}

        # База знаний книг
        self.books_knowledge_base = {
            "любовные романы": [
                {"title": "Гордость и предубеждение", "author": "Джейн Остин", "available": True},
                {"title": "Грозовой перевал", "author": "Эмили Бронте", "available": True},
                {"title": "Поющие в терновнике", "author": "Колин Маккалоу", "available": False},
                {"title": "Джейн Эйр", "author": "Шарлотта Бронте", "available": True},
            ],
            "фантастика": [
                {"title": "451° по Фаренгейту", "author": "Рэй Брэдбери", "available": True},
                {"title": "1984", "author": "Джордж Оруэлл", "available": True},
                {"title": "Мастер и Маргарита", "author": "Михаил Булгаков", "available": True},
                {"title": "Пикник на обочине", "author": "Аркадий и Борис Стругацкие", "available": True},
            ],
            "детективы": [
                {"title": "Убийство в Восточном экспрессе", "author": "Агата Кристи", "available": True},
                {"title": "Шерлок Холмс: Собака Баскервилей", "author": "Артур Конан Дойл", "available": True},
                {"title": "Десять негритят", "author": "Агата Кристи", "available": True},
            ],
            "классика": [
                {"title": "Война и мир", "author": "Лев Толстой", "available": True},
                {"title": "Преступление и наказание", "author": "Федор Достоевский", "available": True},
                {"title": "Анна Каренина", "author": "Лев Толстой", "available": True},
            ],
            "фэнтези": [
                {"title": "Властелин Колец", "author": "Дж. Р. Р. Толкин", "available": True},
                {"title": "Гарри Поттер", "author": "Дж. К. Роулинг", "available": True},
                {"title": "Игра престолов", "author": "Джордж Р. Р. Мартин", "available": True}
            ]
        }

        # База данных авторов
        self.authors_knowledge_base = {
    "Пушкин Александр Сергеевич": [
        {
            "title": "Евгений Онегин",
            "available": True,
            "description": "Роман в стихах, который рассказывает о жизни молодого дворянина Евгения Онегина. Это произведение стало энциклопедией русской жизни начала XIX века и содержит множество лирических отступлений."
        },
        {
            "title": "Руслан и Людмила",
            "available": True,
            "description": "Поэма о любви и приключениях, где главный герой Руслан отправляется на поиски похищенной невесты Людмилы. Полна волшебства, битв и фантастических существ."
        },
        {
            "title": "Капитанская дочка",
            "available": True,
            "description": "Исторический роман о любви Петра Гринёва и Маши Мироновой на фоне Пугачёвского восстания. Произведение показывает сложные нравственные выборы и человеческие судьбы."
        },
    ],
    "Толстой Лев Николаевич": [
        {
            "title": "Война и мир",
            "available": True,
            "description": "Эпический роман, охватывающий события войны 1812 года. История нескольких семей, их любви, дружбы и трагедий на фоне исторических событий."
        },
        {
            "title": "Анна Каренина",
            "available": True,
            "description": "Трагическая история любви Анны Карениной и офицера Вронского. Роман затрагивает темы морали, семьи и общественных условностей."
        },
    ],
    "Достоевский Фёдор Михайлович": [
        {
            "title": "Преступление и наказание",
            "available": True,
            "description": "Психологический роман о студенте Раскольникове, совершившем убийство и мучающемся от угрызений совести. Произведение исследует темы вины, искупления и нравственности."
        },
        {
            "title": "Идиот",
            "available": True,
            "description": "Роман о князе Мышкине, чистом и добром человеке, который сталкивается с жестокостью и корыстью окружающего мира. История о любви, ревности и трагедии."
        },
    ],
    "Чехов Антон Павлович": [
        {
            "title": "Вишнёвый сад",
            "available": True,
            "description": "Пьеса о судьбе дворянского имения и его владельцев. Символ уходящей эпохи и перемен в русской жизни на рубеже XIX–XX веков."
        },
        {
            "title": "Чайка",
            "available": True,
            "description": "Драма о любви, творчестве и неудовлетворённости жизнью. Главные герои — актриса и писатель — сталкиваются с кризисом смысла и поиском себя."
        },
    ],
    "Гоголь Николай Васильевич": [
        {
            "title": "Мёртвые души",
            "available": True,
            "description": "Поэма о приключениях Чичикова, покупающего «мёртвые души» для обогащения. Сатирическое произведение, раскрывающее пороки российского общества."
        },
        {
            "title": "Ревизор",
            "available": True,
            "description": "Комедия о чиновнике Хлестакове, которого приняли за ревизора в провинциальном городе. Остроумная сатира на бюрократию и человеческую глупость."
        },
    ],
    "Тургенев Иван Сергеевич": [
        {
            "title": "Отцы и дети",
            "available": True,
            "description": "Роман о конфликте поколений, где нигилист Базаров сталкивается с традиционными ценностями дворянства. Произведение поднимает вопросы прогресса и человеческих отношений."
        },
        {
            "title": "Муму",
            "available": True,
            "description": "Трогательная история о глухонемом крестьянине Герасиме и его преданной собаке Муму. Рассказ о жестокости и несправедливости крепостного права."
        },
    ]
}


    def create_authors_keyboard(self):
        """Создает клавиатуру с авторами"""
        authors = list(self.authors_knowledge_base.keys())
        keyboard_buttons = []
        for i in range(0, len(authors), 2):
            row = []
            if i < len(authors):
                row.append(authors[i])
            if i + 1 < len(authors):
                row.append(authors[i + 1])
            if row:
                keyboard_buttons.append(row)
        keyboard_buttons.append(["🔙 Назад"])
        keyboard = {
            "keyboard": keyboard_buttons,
            "resize_keyboard": True,
            "one_time_keyboard": False
        }
        return keyboard

    def get_books_by_author(self, author_name):
        """Получить книги по автору"""
        return self.authors_knowledge_base.get(author_name, [])

    def create_search_keyboard(self):
        """Клавиатура для поиска"""
        keyboard = {
            "keyboard": [
                ["🔍 Ввести запрос"],
                ["👤 По автору"],
                ["🔙 Назад"]
            ],
            "resize_keyboard": True,
            "one_time_keyboard": False
        }
        return keyboard

    def send_message(self, chat_id, text, reply_markup=None):
        """Отправка сообщения с клавиатурой"""
        url = f"{self.base_url}/sendMessage"
        payload = {
            'chat_id': chat_id,
            'text': text,
            'parse_mode': 'HTML'
        }
        if reply_markup:
            payload['reply_markup'] = reply_markup

        try:
            response = requests.post(url, json=payload, timeout=10)
            return response.status_code == 200
        except Exception as e:
            print(f"❌ Ошибка отправки: {e}")
            return False

    def get_updates(self, offset=None):
        """Получение обновлений"""
        url = f"{self.base_url}/getUpdates"
        params = {'offset': offset, 'timeout': 30}
        try:
            response = requests.get(url, params=params, timeout=35)
            if response.status_code == 200:
                return response.json()
        except Exception as e:
            print(f"❌ Ошибка получения обновлений: {e}")
        return None

    def get_random_book(self):
        """Получить случайную книгу из API"""
        try:
            response = requests.get(f"{API_BASE_URL}/api/random-book", timeout=10)
            print(f"🔍 Запрос к API: {API_BASE_URL}/api/random-book")
            print(f"📊 Ответ API: {response.status_code}")

            if response.status_code == 200:
                data = response.json()
                print(f"📦 Данные от API: {data}")

                if data.get('success') and data.get('book'):
                    book = data['book']
                    return book
                else:
                    print(f"❌ API вернуло ошибку: {data.get('error')}")
            else:
                print(f"❌ Ошибка HTTP: {response.status_code}")

        except Exception as e:
            print(f"❌ Ошибка API при получении случайной книги: {e}")

        return None

    def search_books(self, query):
        """Поиск книг по запросу"""
        try:
            response = requests.get(
                f"{API_BASE_URL}/api/books/search",
                params={"query": query},
                timeout=10
            )
            print(f"🔍 Поиск в API: {query}")
            print(f"📊 Ответ поиска: {response.status_code}")

            if response.status_code == 200:
                data = response.json()
                if data.get('success') and data.get('books'):
                    return data['books']

        except Exception as e:
            print(f"❌ Ошибка поиска: {e}")

        return None

    def get_books_by_genre(self, genre):
        """Получить книги по жанру"""
        try:
            return self.search_books(genre)
        except Exception as e:
            print(f"❌ Ошибка получения книг по жанру: {e}")
        return None

    def get_recommendations(self, user_id=None):
        """Получить рекомендации"""
        all_books = []
        for genre_books in self.books_knowledge_base.values():
            all_books.extend(genre_books)
        return random.sample(all_books, min(4, len(all_books)))

    def get_genres(self):
        """Получить список жанров"""
        return [
            {"name": "Фантастика"}, {"name": "Детектив"},
            {"name": "Любовные романы"}, {"name": "Фэнтези"},
            {"name": "Классика"}, {"name": "Приключения"}
        ]

    def chat_with_gpt(self, message, chat_id=None):
        """Общение с ChatGPT через OpenAI API"""
        if not OPENAI_API_KEY:
            return self.chat_with_local_ai(message, chat_id)

        try:
            if chat_id not in self.chat_history:
                self.chat_history[chat_id] = []

            system_message = {
                "role": "system",
                "content": """Ты - книжный эксперт и помощник в библиотеке. Твоя задача помогать пользователям с выбором книг, рекомендациями и информацией о литературе."""
            }

            if len(self.chat_history[chat_id]) > 6:
                self.chat_history[chat_id] = self.chat_history[chat_id][-6:]

            messages = [system_message] + self.chat_history[chat_id] + [
                {"role": "user", "content": message}
            ]

            headers = {
                "Authorization": f"Bearer {OPENAI_API_KEY}",
                "Content-Type": "application/json"
            }

            payload = {
                "model": "gpt-3.5-turbo",
                "messages": messages,
                "max_tokens": 500,
                "temperature": 0.7
            }

            response = requests.post(
                "https://api.openai.com/v1/chat/completions",
                headers=headers,
                json=payload,
                timeout=30
            )

            if response.status_code == 200:
                data = response.json()
                gpt_response = data['choices'][0]['message']['content']

                self.chat_history[chat_id].append({"role": "user", "content": message})
                self.chat_history[chat_id].append({"role": "assistant", "content": gpt_response})

                return gpt_response
            else:
                print(f"❌ Ошибка OpenAI API: {response.status_code}")
                return self.chat_with_local_ai(message, chat_id)

        except Exception as e:
            print(f"❌ Ошибка ChatGPT: {e}")
            return self.chat_with_local_ai(message, chat_id)

    def chat_with_local_ai(self, message, chat_id=None):
        """Локальный AI когда ChatGPT недоступен"""
        user_message_lower = message.lower()

        if any(word in user_message_lower for word in ['привет', 'здравствуй', 'hello', 'hi']):
            return "👋 Привет! Я ваш книжный помощник. Рад помочь с выбором литературы! Какие книги вас интересуют?"

        elif any(word in user_message_lower for word in ['рекоменд', 'посоветуй', 'что почитать']):
            if 'фантастик' in user_message_lower or 'космос' in user_message_lower:
                return self._get_detailed_recommendation("фантастика")
            elif 'любов' in user_message_lower or 'роман' in user_message_lower:
                return self._get_detailed_recommendation("любовные романы")
            elif 'детектив' in user_message_lower:
                return self._get_detailed_recommendation("детективы")
            elif 'фэнтези' in user_message_lower or 'маги' in user_message_lower:
                return self._get_detailed_recommendation("фэнтези")
            elif 'классик' in user_message_lower:
                return self._get_detailed_recommendation("классика")
            else:
                return self._get_general_recommendation()

        elif any(word in user_message_lower for word in ['найди', 'поиск', 'ищи']):
            return "🔍 Для поиска конкретных книг лучше использовать кнопку 'Поиск' в главном меню. Там вы можете искать по названиям, авторам или жанрам!"

        elif any(word in user_message_lower for word in ['автор', 'писатель']):
            return self._get_author_info(user_message_lower)

        elif any(word in user_message_lower for word in ['жанр', 'категори']):
            return "📚 У нас есть книги различных жанров:\n\n• Фантастика - книги о будущем, космосе, технологиях\n• Детективы - загадочные истории и расследования\n• Любовные романы - истории о чувствах и отношениях\n• Фэнтези - магические миры и приключения\n• Классика - проверенная временем литература\n\nКакой жанр вас интересует?"

        elif any(word in user_message_lower for word in ['спасибо', 'благодар']):
            return "😊 Пожалуйста! Всегда рад помочь с выбором книг. Если возникнут еще вопросы - обращайтесь!"

        elif any(word in user_message_lower for word in ['пока', 'прощай', 'до свидан']):
            return "📖 До свидания! Заходите еще за книжными рекомендациями. Хорошего дня и приятного чтения!"

        else:
            return self._get_creative_response(message)

    def _get_detailed_recommendation(self, genre):
        """Детальные рекомендации по жанру"""
        books = self.books_knowledge_base.get(genre, [])
        if books:
            response = f"📚 Отличный выбор! Вот рекомендации по жанру '{genre}':\n\n"
            for i, book in enumerate(books[:4], 1):
                status = "✅" if book['available'] else "⏳"
                response += f"{i}. {status} <b>\"{book['title']}\"</b> - {book['author']}\n"

            if genre == "любовные романы":
                response += "\n💖 Эти книги расскажут о прекрасных историях любви с глубокими персонажами и эмоциональными сюжетами."
            elif genre == "фантастика":
                response += "\n🚀 Эти произведения перенесут вас в удивительные миры будущего и заставят задуматься о технологиях и обществе."
            elif genre == "детективы":
                response += "\n🕵️‍♂️ Захватывающие истории с интригующими загадками и неожиданными развязками."
            elif genre == "фэнтези":
                response += "\n✨ Магические миры, эпические приключения и удивительные существа ждут вас!"
            elif genre == "классика":
                response += "\n🏛️ Вечная литература, проверенная временем и поколениями читателей."

            response += "\n\nКакая книга заинтересовала вас больше всего?"
            return response
        else:
            return f"В жанре '{genre}' пока нет книг в базе. Попробуйте другой жанр!"

    def _get_general_recommendation(self):
        """Общие рекомендации"""
        response = "📖 Вот несколько отличных книг для начала:\n\n"
        popular_books = [
            {"title": "Гордость и предубеждение", "author": "Джейн Остин", "genre": "любовные романы"},
            {"title": "1984", "author": "Джордж Оруэлл", "genre": "фантастика"},
            {"title": "Убийство в Восточном экспрессе", "author": "Агата Кристи", "genre": "детективы"},
            {"title": "Властелин Колец", "author": "Дж. Р. Р. Толкин", "genre": "фэнтези"}
        ]

        for i, book in enumerate(popular_books, 1):
            response += f"{i}. ✅ <b>\"{book['title']}\"</b> - {book['author']}\n"
            response += f"   🏷️ {book['genre']}\n\n"

        response += "Эти книги - проверенная классика! Могу посоветовать что-то конкретное по жанру или настроению."
        return response

    def _get_author_info(self, message):
        """Информация об авторах"""
        authors_info = {
            "достоевск": "Фёдор Достоевский - великий русский писатель, автор 'Преступления и наказания', 'Идиота', 'Братьев Карамазовых'",
            "толст": "Лев Толстой - классик русской литературы, создатель 'Войны и мира', 'Анны Карениной'",
            "пушкин": "Александр Пушкин - основатель современного русского литературного языка",
            "остин": "Джейн Остин - английская писательница, мастер любовного романа",
            "оруэлл": "Джордж Оруэлл - автор антиутопий '1984' и 'Скотный двор'",
            "толкиен": "Дж. Р. Р. Толкин - создатель мира Средиземья, автор 'Властелина Колец'",
            "кристи": "Агата Кристи - королева детектива, создательница Эркюля Пуаро и мисс Марпл"
        }

        for author_key, author_info in authors_info.items():
            if author_key in message:
                return f"👤 <b>Информация об авторе:</b>\n\n{author_info}"

        return "🤔 Какого автора вас интересует? Могу рассказать о популярных писателях и их творчестве."

    def _get_creative_response(self, message):
        """Креативные ответы на нестандартные вопросы"""
        creative_responses = [
            "📚 Интересный вопрос! Как книжный эксперт, я рекомендую обратить внимание на классическую литературу - она часто дает ответы на вечные вопросы.",
            "💭 Замечательно, что вы интересуетесь книгами! Могу предложить обсудить ваши литературные предпочтения - это поможет подобрать идеальные книги для вас.",
            "🔍 Позвольте я помогу вам найти подходящие книги. Расскажите, что вы любите читать или какое настроение ищете?",
            "📖 Книги - это целые миры! Хотите окунуться в приключения, romance, детективную интригу или философские размышления?",
            "✨ Как книжный помощник, я считаю: нет неинтересных тем, есть неподходящие книги! Давайте найдем то, что вас увлечет."
        ]
        return random.choice(creative_responses)

    def create_main_keyboard(self):
        """Создает основную клавиатуру"""
        keyboard = {
            "keyboard": [
                ["📚 Случайная книга", "🔍 Поиск"],
                ["📂 Жанры", "💬 Помощник"],
                ["ℹ️ О боте"]
            ],
            "resize_keyboard": True,
            "one_time_keyboard": False
        }
        return keyboard

    def create_genres_keyboard(self):
        """Создает клавиатуру с жанрами"""
        genres = self.get_genres()
        keyboard_buttons = []

        for i in range(0, len(genres), 2):
            row = []
            if i < len(genres):
                row.append(genres[i]['name'])
            if i + 1 < len(genres):
                row.append(genres[i + 1]['name'])
            if row:
                keyboard_buttons.append(row)

        keyboard_buttons.append(["🔙 Назад"])

        keyboard = {
            "keyboard": keyboard_buttons,
            "resize_keyboard": True,
            "one_time_keyboard": False
        }
        return keyboard

    def create_back_keyboard(self):
        """Клавиатура только с кнопкой Назад"""
        keyboard = {
            "keyboard": [["🔙 Назад"]],
            "resize_keyboard": True,
            "one_time_keyboard": False
        }
        return keyboard

    def create_assistant_keyboard(self):
        """Клавиатура для помощника"""
        keyboard = {
            "keyboard": [
                ["📖 Рекомендации", "🚀 Фантастика"],
                ["💖 Романы", "🕵️ Детективы"],
                ["📚 Классика", "✨ Фэнтези"],
                ["🔙 Назад"]
            ],
            "resize_keyboard": True,
            "one_time_keyboard": False
        }
        return keyboard

    def process_message(self, chat_id, text):
        """Обработка входящего сообщения"""
        text = text.strip()
        user_state = self.user_states.get(chat_id, "main")

        print(f"📱 Обработка: {text}, состояние: {user_state}")

        # Обработка команды назад
        if text == "🔙 Назад":
            self.user_states[chat_id] = "main"
            message = "📖 <b>Главное меню</b>\n\nВыберите действие:"
            return message, self.create_main_keyboard()

        # Команда /start
        if text == "/start":
            self.user_states[chat_id] = "main"
            message = (
                "📖 <b>Добро пожаловать в Книжный Бот!</b>\n\n"
                "Я помогу вам найти интересные книги:\n"
                "• 📚 <b>Случайная книга</b> - случайная рекомендация\n"
                "• 🔍 <b>Поиск</b> - поиск книг по жанру\n"
                "• 📂 <b>Жанры</b> - книги по категориям\n"
                "• 💬 <b>Помощник</b> - умный AI-консультант по книгам\n\n"
                "<i>Выберите действие:</i>"
            )
            return message, self.create_main_keyboard()

        # Основное меню
        if user_state == "main":
            if text == "📚 Случайная книга":
                book = self.get_random_book()
                if book:
                    title = book.get('title', 'Без названия')
                    author = book.get('author', 'Автор не указан')
                    description = book.get('description', 'Описание отсутствует')
                    genres = book.get('genres', [])

                    message = (
                        f"🎲 <b>Случайная книга:</b>\n\n"
                        f"📚 <b>{title}</b>\n"
                        f"👤 Автор: {author}\n"
                    )

                    if genres:
                        message += f"📖 Жанры: {', '.join(genres)}\n"

                    if description and description != 'Описание отсутствует':
                        message += f"📝 {description}\n"

                else:
                    all_books = []
                    for genre_books in self.books_knowledge_base.values():
                        all_books.extend(genre_books)

                    if all_books:
                        book = random.choice(all_books)
                        message = (
                            f"🎲 <b>Случайная книга (локальная база):</b>\n\n"
                            f"📚 <b>{book['title']}</b>\n"
                            f"👤 Автор: {book['author']}\n"
                        )
                    else:
                        message = "❌ Не удалось получить книгу. Попробуйте позже."

                return message, self.create_main_keyboard()

            elif text == "🔍 Поиск":
                self.user_states[chat_id] = "search"
                message = "🔍 <b>Поиск книг</b>\n\nВыберите действие:"
                return message, self.create_search_keyboard()

            elif text == "📂 Жанры":
                self.user_states[chat_id] = "genres"
                message = "📂 <b>Выберите жанр:</b>"
                return message, self.create_genres_keyboard()

            elif text == "💬 Помощник":
                self.user_states[chat_id] = "assistant"
                message = (
                    "🤖 <b>Умный книжный помощник</b>\n\n"
                    "Я ваш AI-консультант по книгам! Могу:\n\n"
                    "• 💬 Общаться на любые книжные темы\n"
                    "• 📚 Давать персонализированные рекомендации\n"
                    "• 🔍 Помогать с выбором книг по настроению\n"
                    "• 🎯 Предлагать книги по вашим интересам\n"
                    "• 📖 Рассказывать о авторах и произведениях\n\n"
                    "<i>Задайте любой вопрос о книгах или используйте быстрые кнопки:</i>"
                )
                return message, self.create_assistant_keyboard()

            elif text == "ℹ️ О боте":
                message = (
                    "🤖 <b>О книжном боте</b>\n\n"
                    "Этот бот помогает находить и рекомендовать книги.\n\n"
                    "📚 <b>Функции:</b>\n"
                    "• Поиск книг по жанрам\n"
                    "• Случайные рекомендации\n"
                    "• 💬 Умный AI-помощник (ChatGPT)\n"
                    "• Информация о доступности\n\n"
                    "Используйте кнопки меню для навигации!"
                )
                return message, self.create_main_keyboard()

        # Состояние поиска
        elif user_state == "search":
            if text == "🔙 Назад":
                self.user_states[chat_id] = "main"
                message = "🔍 Поиск отменен"
                return message, self.create_main_keyboard()

            elif text == "👤 По автору":
                self.user_states[chat_id] = "search_by_author"
                message = "👤 <b>Выберите автора:</b>"
                return message, self.create_authors_keyboard()

            elif text == "🔍 Ввести запрос":
                self.user_states[chat_id] = "input_search_query"
                message = "🔍 <b>Введите название книги, автора или описание:</b>"
                return message, self.create_back_keyboard()

        # Состояние ввода запроса
        elif user_state == "input_search_query":
            books = self.search_books(text)
            self.user_states[chat_id] = "main"

            if books and len(books) > 0:
                message = f"🔍 <b>Найдено по запросу '{text}':</b>\n\n"
                for i, book in enumerate(books[:5], 1):
                    title = book.get('title', 'Без названия')
                    author = book.get('author', 'Автор не указан')
                    message += f"{i}. <b>{title}</b>\n"
                    message += f"   👤 {author}\n\n"
            else:
                message = f"❌ По запросу '{text}' книги не найдены.\n\nПопробуйте другой запрос."

            return message, self.create_main_keyboard()

        # Состояние поиска по автору
        # Состояние поиска по автору
        elif user_state == "search_by_author":
            if text == "🔙 Назад":
                self.user_states[chat_id] = "search"
                message = "👤 Возврат к поиску"
                return message, self.create_search_keyboard()

            books = self.get_books_by_author(text)
            if books:
                message = f"📚 <b>Книги автора {text}:</b>\n\n"
                for i, book in enumerate(books, 1):
                    status = "✅" if book.get('available', True) else "⏳"
                    title = book.get('title', 'Без названия')
                    description = book.get('description', 'Описание отсутствует')
                    message += f"{i}. {status} <b>{title}</b>\n"
                    message += f"   {description}\n\n"
            else:
                message = f"❌ Книги автора {text} не найдены."

            self.user_states[chat_id] = "search"
            return message, self.create_search_keyboard()


        # Состояние помощника
        elif user_state == "assistant":
            if text == "🔙 Назад":
                self.user_states[chat_id] = "main"
                if chat_id in self.chat_history:
                    self.chat_history[chat_id] = []
                message = "💬 Чат с помощником завершен"
                return message, self.create_main_keyboard()

            quick_actions = {
                "📖 Рекомендации": "Посоветуй интересные книги для начала",
                "🚀 Фантастика": "Рекомендуй книги в жанре фантастики",
                "💖 Романы": "Посоветуй любовные романы",
                "🕵️ Детективы": "Рекомендуй детективные романы",
                "📚 Классика": "Посоветуй классическую литературу",
                "✨ Фэнтези": "Рекомендуй книги в жанре фэнтези"
            }

            if text in quick_actions:
                query = quick_actions[text]
            else:
                query = text

            self.send_message(chat_id, "💭 <i>Думаю над ответом...</i>")

            response = self.chat_with_gpt(query, chat_id)

            message = f"🤖 <b>Книжный помощник:</b>\n\n{response}\n\n<i>Задайте следующий вопрос или используйте кнопки:</i>"
            return message, self.create_assistant_keyboard()

        # Неизвестная команда
        return "❌ Неизвестная команда. Используйте кнопки меню.", self.create_main_keyboard()

    def run(self):
        """Запуск бота"""
        print("🤖 Книжный бот запущен...")

        # Проверяем доступность бота
        try:
            response = requests.get(f"{self.base_url}/getMe", timeout=10)
            if response.status_code == 200:
                bot_info = response.json()
                if bot_info.get('ok'):
                    print(f"✅ Бот @{bot_info['result']['username']} успешно подключен")
                else:
                    print("❌ Неверный токен бота")
                    return
            else:
                print("❌ Ошибка подключения к Telegram API")
                return
        except Exception as e:
            print(f"❌ Ошибка проверки бота: {e}")
            return

        # Проверяем доступность OpenAI API
        if OPENAI_API_KEY:
            print("✅ OpenAI API ключ найден")
        else:
            print("⚠️ OpenAI API ключ не найден, используется локальный AI")

        print("📚 Ожидание сообщений...")
        last_update_id = None

        while True:
            try:
                updates = self.get_updates(last_update_id)

                if updates and 'result' in updates:
                    for update in updates['result']:
                        last_update_id = update['update_id'] + 1

                        if 'message' in update and 'text' in update['message']:
                            chat_id = update['message']['chat']['id']
                            text = update['message']['text']

                            print(f"💬 Получено от {chat_id}: {text}")

                            response, keyboard = self.process_message(chat_id, text)
                            if self.send_message(chat_id, response, keyboard):
                                print(f"✅ Отправлен ответ пользователю {chat_id}")
                            else:
                                print(f"❌ Ошибка отправки ответа пользователю {chat_id}")

                time.sleep(1)

            except KeyboardInterrupt:
                print("\n🛑 Бот остановлен пользователем")
                break
            except Exception as e:
                print(f"❌ Ошибка в основном цикле: {e}")
                time.sleep(5)

def main():
    print("🚀 Запуск книжного бота с ChatGPT...")

    # Проверяем доступность API
    try:
        response = requests.get(f"{API_BASE_URL}/", timeout=5)
        if response.status_code == 200:
            print("✅ API сервер доступен")
        else:
            print("⚠️ API сервер отвечает с ошибкой")
    except:
        print("⚠️ Не удалось подключиться к API серверу")
        print("💡 Бот будет работать в автономном режиме")

    # Запускаем бота
    bot = AdvancedBookBot(BOT_TOKEN)
    bot.run()

if __name__ == "__main__":
    main()
