"""
Fantasy Dashboard Web Server
FastAPI бэкенд для Mini App
"""

import os
import json
from pathlib import Path
from fastapi import FastAPI, HTTPException, Header, Request
from fastapi.responses import HTMLResponse, FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
import uvicorn

# Конфигурация
API_SECRET = os.getenv('API_SECRET', 'your-secret-token')
DATA_FILE = Path(__file__).parent / 'data.json'
INDEX_FILE = Path(__file__).parent / 'index.html'

# Создаём приложение
app = FastAPI(
    title="Fantasy Dashboard API",
    description="API для Telegram Mini App RPG-дашборда",
    version="1.0.0"
)

# CORS для Telegram
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Telegram Web Apps
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ===== УТИЛИТЫ =====

def load_data() -> dict:
    """Загрузить данные из JSON"""
    try:
        with open(DATA_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)
    except FileNotFoundError:
        return {"error": "Data file not found"}

def save_data(data: dict):
    """Сохранить данные в JSON"""
    with open(DATA_FILE, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

# ===== ЭНДПОИНТЫ =====

@app.get("/", response_class=HTMLResponse)
async def root():
    """Главная страница — Mini App"""
    if INDEX_FILE.exists():
        return FileResponse(INDEX_FILE, media_type='text/html')
    return HTMLResponse("<h1>Fantasy Dashboard</h1><p>index.html not found</p>")

@app.get("/dashboard", response_class=HTMLResponse)
async def dashboard():
    """Alias для Mini App"""
    return await root()

@app.get("/api/data")
async def get_data():
    """Получить данные персонажа"""
    data = load_data()
    return JSONResponse(content=data)

@app.post("/api/data")
async def update_data(request: Request, authorization: str = Header(None)):
    """Обновить данные персонажа (требует авторизации)"""
    # Проверка токена
    if authorization != f"Bearer {API_SECRET}":
        raise HTTPException(status_code=401, detail="Unauthorized")
    
    try:
        new_data = await request.json()
        save_data(new_data)
        return {"status": "ok", "message": "Data updated"}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@app.get("/api/health")
async def health():
    """Health check"""
    return {"status": "ok", "service": "Fantasy Dashboard"}

# ===== ЗАПУСК =====

if __name__ == '__main__':
    # Для локальной разработки
    # Для HTTPS в продакшене используй reverse proxy (nginx) или Railway/Render
    print("""
    ========================================
       Fantasy Dashboard Server
    ========================================
    Endpoints:
      GET  /           - Mini App
      GET  /dashboard  - Mini App (alias)
      GET  /api/data   - Get data
      POST /api/data   - Update data
      GET  /api/health - Health check
    ========================================
    """)
    
    uvicorn.run(
        "server:app",
        host="0.0.0.0",
        port=int(os.getenv('PORT', 8000)),
        reload=True
    )
