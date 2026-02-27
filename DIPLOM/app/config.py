# app/config.py
from pydantic_settings import BaseSettings
import os
from dotenv import load_dotenv

load_dotenv()

class Settings(BaseSettings):
    DATABASE_URL: str = os.getenv("DATABASE_URL", "sqlite:///./book_recommendation.db")
    TELEGRAM_BOT_TOKEN: str = os.getenv("TELEGRAM_BOT_TOKEN", "")
    SECRET_KEY: str = os.getenv("SECRET_KEY", "your-secret-key-12345-change-in-production")
    ALGORITHM: str = "HS256"
    
    class Config:
        env_file = ".env"

settings = Settings()