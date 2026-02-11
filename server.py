"""
Fantasy Dashboard Web Server
FastAPI бэкенд для Mini App с WebSocket чатом
"""

import os
import json
import asyncio
from pathlib import Path
from typing import List, Dict
from datetime import datetime
from fastapi import FastAPI, HTTPException, Header, Request, WebSocket, WebSocketDisconnect
from fastapi.responses import HTMLResponse, FileResponse, JSONResponse
from fastapi.middleware.cors import CORSMiddleware
import uvicorn
import httpx

# Конфигурация
API_SECRET = os.getenv('API_SECRET', 'fantasy-secret-2026')
BOT_TOKEN = os.getenv('BOT_TOKEN', '')
OWNER_CHAT_ID = os.getenv('OWNER_CHAT_ID', '')
DATA_FILE = Path(__file__).parent / 'data.json'
INDEX_FILE = Path(__file__).parent / 'index.html'
CHAT_FILE = Path(__file__).parent / 'chat_history.json'

# Telegram API
TELEGRAM_API = f"https://api.telegram.org/bot{BOT_TOKEN}"

# Создаём приложение
app = FastAPI(
    title="Fantasy Dashboard API",
    description="API для Telegram Mini App с Clawdbot чатом",
    version="2.0.0"
)

# CORS для Telegram
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ===== WEBSOCKET MANAGER =====

class ConnectionManager:
    """Менеджер WebSocket соединений"""
    
    def __init__(self):
        self.active_connections: List[WebSocket] = []
        self.chat_history: List[Dict] = []
        self._load_history()
    
    def _load_history(self):
        """Загрузить историю чата"""
        try:
            if CHAT_FILE.exists():
                with open(CHAT_FILE, 'r', encoding='utf-8') as f:
                    self.chat_history = json.load(f)
        except:
            self.chat_history = []
    
    def _save_history(self):
        """Сохранить историю чата"""
        try:
            # Храним последние 100 сообщений
            with open(CHAT_FILE, 'w', encoding='utf-8') as f:
                json.dump(self.chat_history[-100:], f, ensure_ascii=False, indent=2)
        except:
            pass
    
    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)
        # Отправляем историю при подключении
        if self.chat_history:
            await websocket.send_json({
                "type": "history",
                "messages": self.chat_history[-50:]  # Последние 50 сообщений
            })
    
    def disconnect(self, websocket: WebSocket):
        if websocket in self.active_connections:
            self.active_connections.remove(websocket)
    
    async def broadcast(self, message: dict):
        """Отправить сообщение всем подключенным клиентам"""
        self.chat_history.append(message)
        self._save_history()
        
        disconnected = []
        for connection in self.active_connections:
            try:
                await connection.send_json(message)
            except:
                disconnected.append(connection)
        
        for conn in disconnected:
            self.disconnect(conn)
    
    def add_message(self, role: str, content: str, metadata: dict = None):
        """Добавить сообщение в историю"""
        msg = {
            "id": len(self.chat_history) + 1,
            "role": role,  # "user" или "assistant"
            "content": content,
            "timestamp": datetime.now().isoformat(),
            "metadata": metadata or {}
        }
        return msg

manager = ConnectionManager()

# ===== УТИЛИТЫ =====

async def send_to_telegram(text: str):
    """Отправить сообщение в Telegram чат владельца"""
    if not BOT_TOKEN or not OWNER_CHAT_ID:
        print("⚠️ BOT_TOKEN or OWNER_CHAT_ID not set")
        return False
    
    try:
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{TELEGRAM_API}/sendMessage",
                json={
                    "chat_id": OWNER_CHAT_ID,
                    "text": f"🎮 [MiniApp]\n{text}",
                    "parse_mode": "HTML"
                },
                timeout=10
            )
            return response.status_code == 200
    except Exception as e:
        print(f"❌ Telegram send error: {e}")
        return False

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

@app.get("/chat", response_class=HTMLResponse)
async def chat_page():
    """Страница чата"""
    return await root()

@app.get("/dashboard", response_class=HTMLResponse)
async def dashboard():
    """Dashboard (alias для Mini App)"""
    return await root()

@app.get("/api/data")
async def get_data():
    """Получить данные персонажа"""
    data = load_data()
    return JSONResponse(content=data)

@app.post("/api/data")
async def update_data(request: Request, authorization: str = Header(None)):
    """Обновить данные персонажа"""
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
    return {
        "status": "ok", 
        "service": "Fantasy Dashboard",
        "version": "2.0.0",
        "connections": len(manager.active_connections)
    }

@app.get("/api/chat/history")
async def get_chat_history(limit: int = 50):
    """Получить историю чата"""
    return {"messages": manager.chat_history[-limit:]}

# ===== WEBSOCKET =====

@app.websocket("/ws/chat")
async def websocket_chat(websocket: WebSocket):
    """WebSocket для real-time чата"""
    await manager.connect(websocket)
    
    try:
        while True:
            # Получаем сообщение от клиента
            data = await websocket.receive_json()
            
            if data.get("type") == "message":
                content = data.get("content", "")
                
                # Сообщение от пользователя
                user_msg = manager.add_message(
                    role="user",
                    content=content,
                    metadata={"source": "miniapp"}
                )
                await manager.broadcast(user_msg)
                
                # Отправляем в Telegram → Clawdbot
                await send_to_telegram(content)
                
                # Отправляем статус "typing"
                await manager.broadcast({
                    "type": "status",
                    "status": "typing"
                })
            
            elif data.get("type") == "ping":
                await websocket.send_json({"type": "pong"})
    
    except WebSocketDisconnect:
        manager.disconnect(websocket)

@app.post("/api/chat/message")
async def post_message(request: Request):
    """HTTP endpoint для отправки сообщений (от бота)"""
    try:
        data = await request.json()
        role = data.get("role", "assistant")
        content = data.get("content", "")
        metadata = data.get("metadata", {})
        
        msg = manager.add_message(role, content, metadata)
        await manager.broadcast(msg)
        
        return {"status": "ok", "message_id": msg["id"]}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@app.post("/api/chat/status")
async def post_status(request: Request):
    """Обновить статус (typing, online, etc)"""
    try:
        data = await request.json()
        await manager.broadcast({
            "type": "status",
            "status": data.get("status", "online")
        })
        return {"status": "ok"}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

# ===== ЗАПУСК =====

if __name__ == '__main__':
    print("""
    ========================================
       Fantasy Dashboard + Chat Server
    ========================================
    Endpoints:
      GET  /              - Mini App
      GET  /chat          - Chat page
      WS   /ws/chat       - WebSocket chat
      GET  /api/health    - Health check
      GET  /api/chat/history - Chat history
      POST /api/chat/message - Send message
    ========================================
    """)
    
    uvicorn.run(
        "server:app",
        host="0.0.0.0",
        port=int(os.getenv('PORT', 8000)),
        reload=True
    )
