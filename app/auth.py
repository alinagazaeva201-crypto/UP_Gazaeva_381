# app/auth.py
from datetime import datetime, timedelta
from fastapi import Request, Depends
from sqlalchemy.orm import Session
from app.database import get_db
from app import models
import json
import base64

SECRET_KEY = "your-secret-key-12345-change-in-production"

def create_access_token(data: dict):
    # Простая реализация токена
    data["exp"] = (datetime.utcnow() + timedelta(hours=6)).timestamp()
    token_data = json.dumps(data)
    return base64.b64encode(token_data.encode()).decode()

def decode_access_token(token: str):
    try:
        data = base64.b64decode(token).decode()
        payload = json.loads(data)
        exp = payload.get("exp")
        if exp and datetime.utcnow().timestamp() > exp:
            return None
        return payload
    except:
        return None

async def get_current_user(request: Request, db: Session = Depends(get_db)):
    token = request.cookies.get("access_token")
    if not token:
        return None
    
    payload = decode_access_token(token)
    if payload is None:
        return None
    
    user_id: int = payload.get("user_id")
    if user_id is None:
        return None
    
    user = db.query(models.User).filter(models.User.id == user_id).first()
    return user