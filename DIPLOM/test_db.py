import sys
import os
from sqlalchemy import create_engine, text

# Настройки из вашего .env
DATABASE_URL = "postgresql://postgres:123qwe@localhost:5432/book_recommendation_system"

def test_connection():
    try:
        engine = create_engine(DATABASE_URL)
        with engine.connect() as conn:
            result = conn.execute(text("SELECT version();"))
            print("✅ Подключение к PostgreSQL успешно!")
            print(f"📊 Версия PostgreSQL: {result.fetchone()[0]}")
            
            # Проверим существующие таблицы
            result = conn.execute(text("""
                SELECT table_name 
                FROM information_schema.tables 
                WHERE table_schema = 'public'
            """))
            tables = [row[0] for row in result]
            print(f"📋 Таблицы в базе: {tables}")
            
        return True
    except Exception as e:
        print(f"❌ Ошибка подключения: {e}")
        return False

if __name__ == "__main__":
    test_connection()