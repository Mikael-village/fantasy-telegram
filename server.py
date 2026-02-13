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
BRIDGE_SECRET = os.getenv('BRIDGE_SECRET', 'fantasy-bridge-2026')
BOT_TOKEN = os.getenv('BOT_TOKEN', '')
OWNER_CHAT_ID = os.getenv('OWNER_CHAT_ID', '')
DATA_FILE = Path(__file__).parent / 'data.json'
INDEX_FILE = Path(__file__).parent / 'index.html'
CHAT_FILE = Path(__file__).parent / 'chat_history.json'
SOUL_FILE = Path(__file__).parent / 'soul.json'

# Файловый менеджер - базовая директория
FILES_ROOT = Path(os.getenv('FILES_ROOT', 'C:/BRANDONLINE'))

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

# ===== PWA STATIC FILES =====

@app.get("/manifest.json")
async def manifest():
    """PWA Manifest"""
    manifest_file = Path(__file__).parent / 'manifest.json'
    if manifest_file.exists():
        return FileResponse(manifest_file, media_type='application/manifest+json')
    raise HTTPException(status_code=404, detail="Manifest not found")

@app.get("/sw.js")
async def service_worker():
    """Service Worker"""
    sw_file = Path(__file__).parent / 'sw.js'
    if sw_file.exists():
        return FileResponse(sw_file, media_type='application/javascript')
    raise HTTPException(status_code=404, detail="Service worker not found")

@app.get("/icon-{size}.png")
async def pwa_icon(size: int):
    """PWA Icons"""
    icon_file = Path(__file__).parent / f'icon-{size}.png'
    if icon_file.exists():
        return FileResponse(icon_file, media_type='image/png')
    raise HTTPException(status_code=404, detail="Icon not found")

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

@app.get("/api/soul")
async def get_soul():
    """Получить данные вкладки Душа (папка клиентов)"""
    try:
        if SOUL_FILE.exists():
            with open(SOUL_FILE, 'r', encoding='utf-8') as f:
                return json.load(f)
        else:
            return {
                "error": "Soul data not synced yet",
                "items": []
            }
    except Exception as e:
        return {
            "error": str(e),
            "items": []
        }

# AI Status tracking
AI_STATUS_FILE = Path(__file__).parent / 'ai_status.json'

@app.get("/api/ai/status")
async def get_ai_status():
    """Проверить статус AI (Помощник Микаела)"""
    try:
        if AI_STATUS_FILE.exists():
            with open(AI_STATUS_FILE, 'r', encoding='utf-8') as f:
                data = json.load(f)
                
            # Проверяем время последнего пинга
            last_ping = datetime.fromisoformat(data.get('last_ping', '2000-01-01'))
            diff_seconds = (datetime.now() - last_ping).total_seconds()
            
            # Онлайн если пинг был меньше 2 минут назад
            return {
                "online": diff_seconds < 120,
                "last_ping": data.get('last_ping'),
                "diff_seconds": int(diff_seconds)
            }
        else:
            return {"online": False, "last_ping": None}
    except Exception as e:
        return {"online": False, "error": str(e)}

@app.post("/api/ai/ping")
async def ai_ping():
    """AI отправляет пинг чтобы показать что онлайн"""
    try:
        data = {
            "last_ping": datetime.now().isoformat(),
            "status": "online"
        }
        with open(AI_STATUS_FILE, 'w', encoding='utf-8') as f:
            json.dump(data, f)
        return {"status": "ok", "ping": data["last_ping"]}
    except Exception as e:
        return {"status": "error", "error": str(e)}

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

# ===== PC BRIDGE =====

class PCBridge:
    """Менеджер соединения с PC"""
    
    def __init__(self):
        self.pc_websocket: WebSocket = None
        self.pending_requests: Dict[str, asyncio.Future] = {}
        self.request_counter = 0
    
    @property
    def is_connected(self):
        return self.pc_websocket is not None
    
    async def connect(self, websocket: WebSocket):
        self.pc_websocket = websocket
        print(f"[PC Bridge] PC connected")
    
    def disconnect(self):
        self.pc_websocket = None
        # Cancel pending requests
        for future in self.pending_requests.values():
            if not future.done():
                future.set_exception(Exception("PC disconnected"))
        self.pending_requests.clear()
        print(f"[PC Bridge] PC disconnected")
    
    async def request(self, action: str, path: str = "", timeout: float = 30.0) -> dict:
        """Отправить запрос к PC и ждать ответа"""
        if not self.is_connected:
            return {"error": "PC not connected", "pc_online": False}
        
        self.request_counter += 1
        request_id = f"req_{self.request_counter}"
        
        future = asyncio.get_event_loop().create_future()
        self.pending_requests[request_id] = future
        
        try:
            await self.pc_websocket.send_json({
                "type": "request",
                "id": request_id,
                "action": action,
                "path": path
            })
            
            result = await asyncio.wait_for(future, timeout=timeout)
            return result
        except asyncio.TimeoutError:
            return {"error": "Request timeout"}
        except Exception as e:
            return {"error": str(e)}
        finally:
            self.pending_requests.pop(request_id, None)
    
    def handle_response(self, data: dict):
        """Обработать ответ от PC"""
        request_id = data.get("id")
        if request_id and request_id in self.pending_requests:
            future = self.pending_requests[request_id]
            if not future.done():
                future.set_result(data)

pc_bridge = PCBridge()

@app.websocket("/ws/pc-bridge")
async def websocket_pc_bridge(websocket: WebSocket):
    """WebSocket для подключения PC"""
    await websocket.accept()
    
    try:
        # Ждём авторизацию
        auth_data = await asyncio.wait_for(websocket.receive_json(), timeout=10)
        
        if auth_data.get("type") != "auth" or auth_data.get("secret") != BRIDGE_SECRET:
            await websocket.close(code=4001, reason="Unauthorized")
            return
        
        await pc_bridge.connect(websocket)
        await websocket.send_json({"type": "auth_ok"})
        
        while True:
            data = await websocket.receive_json()
            
            if data.get("type") == "response":
                pc_bridge.handle_response(data)
            elif data.get("type") == "pong":
                pass  # Keep-alive response
                
    except WebSocketDisconnect:
        pc_bridge.disconnect()
    except Exception as e:
        print(f"[PC Bridge] Error: {e}")
        pc_bridge.disconnect()

@app.get("/api/pc/status")
async def pc_status():
    """Статус подключения PC"""
    return {"connected": pc_bridge.is_connected}

@app.get("/api/pc/files")
async def pc_list_files(path: str = ""):
    """Список файлов на PC (через bridge)"""
    return await pc_bridge.request("list", path)

@app.get("/api/pc/file")
async def pc_read_file(path: str):
    """Прочитать файл на PC"""
    return await pc_bridge.request("read", path)

@app.get("/api/pc/file/download")
async def pc_download_file(path: str):
    """Скачать файл с PC через bridge"""
    result = await pc_bridge.request("download", path, timeout=60.0)
    
    if result.get("error"):
        raise HTTPException(status_code=400, detail=result["error"])
    
    import base64
    content = base64.b64decode(result.get("content", ""))
    filename = result.get("name", "file")
    
    from fastapi.responses import Response
    return Response(
        content=content,
        media_type="application/octet-stream",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'}
    )

# ===== ФАЙЛОВЫЙ МЕНЕДЖЕР (локальный, для VPS) =====

def safe_path(relative_path: str) -> Path:
    """Безопасное разрешение пути (только внутри FILES_ROOT)"""
    # Нормализуем путь
    clean_path = relative_path.replace('\\', '/').strip('/')
    full_path = (FILES_ROOT / clean_path).resolve()
    
    # Проверяем что путь внутри FILES_ROOT
    try:
        full_path.relative_to(FILES_ROOT.resolve())
    except ValueError:
        raise HTTPException(status_code=403, detail="Access denied: path outside root")
    
    return full_path

@app.get("/api/files")
async def list_files(path: str = ""):
    """Список файлов и папок"""
    try:
        target = safe_path(path)
        
        if not target.exists():
            raise HTTPException(status_code=404, detail="Path not found")
        
        if not target.is_dir():
            raise HTTPException(status_code=400, detail="Not a directory")
        
        items = []
        for item in sorted(target.iterdir(), key=lambda x: (not x.is_dir(), x.name.lower())):
            try:
                stat = item.stat()
                items.append({
                    "name": item.name,
                    "type": "folder" if item.is_dir() else "file",
                    "size": stat.st_size if item.is_file() else None,
                    "modified": datetime.fromtimestamp(stat.st_mtime).isoformat(),
                    "extension": item.suffix.lower() if item.is_file() else None
                })
            except (PermissionError, OSError):
                continue
        
        return {
            "path": path,
            "parent": str(Path(path).parent) if path else None,
            "items": items
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/file")
async def read_file(path: str):
    """Прочитать содержимое файла"""
    try:
        target = safe_path(path)
        
        if not target.exists():
            raise HTTPException(status_code=404, detail="File not found")
        
        if not target.is_file():
            raise HTTPException(status_code=400, detail="Not a file")
        
        # Проверяем размер (макс 1MB для текстовых)
        if target.stat().st_size > 1_000_000:
            raise HTTPException(status_code=413, detail="File too large (max 1MB)")
        
        # Определяем тип файла
        text_extensions = {'.txt', '.md', '.json', '.py', '.js', '.html', '.css', '.yaml', '.yml', '.xml', '.csv', '.log', '.bat', '.sh', '.ps1', '.env', '.gitignore', '.toml', '.ini', '.cfg'}
        
        if target.suffix.lower() in text_extensions or target.suffix == '':
            try:
                content = target.read_text(encoding='utf-8')
                return {
                    "path": path,
                    "name": target.name,
                    "content": content,
                    "type": "text",
                    "size": len(content)
                }
            except UnicodeDecodeError:
                return {
                    "path": path,
                    "name": target.name,
                    "content": None,
                    "type": "binary",
                    "message": "Binary file, cannot display"
                }
        else:
            return {
                "path": path,
                "name": target.name,
                "content": None,
                "type": "binary",
                "message": f"Binary file ({target.suffix})"
            }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.put("/api/file")
async def save_file(request: Request):
    """Сохранить файл"""
    try:
        data = await request.json()
        path = data.get("path", "")
        content = data.get("content", "")
        
        target = safe_path(path)
        
        # Создаём родительские директории если нужно
        target.parent.mkdir(parents=True, exist_ok=True)
        
        # Сохраняем
        target.write_text(content, encoding='utf-8')
        
        return {"status": "ok", "path": path, "size": len(content)}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/folder")
async def create_folder(request: Request):
    """Создать папку"""
    try:
        data = await request.json()
        path = data.get("path", "")
        
        target = safe_path(path)
        target.mkdir(parents=True, exist_ok=True)
        
        return {"status": "ok", "path": path}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.delete("/api/file")
async def delete_file(path: str, confirm: bool = False):
    """Удалить файл или папку"""
    if not confirm:
        raise HTTPException(status_code=400, detail="Confirmation required (confirm=true)")
    
    try:
        target = safe_path(path)
        
        if not target.exists():
            raise HTTPException(status_code=404, detail="Path not found")
        
        if target.is_file():
            target.unlink()
        else:
            # Удаляем только пустые папки для безопасности
            if any(target.iterdir()):
                raise HTTPException(status_code=400, detail="Folder not empty")
            target.rmdir()
        
        return {"status": "ok", "deleted": path}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/files/open")
async def open_file(path: str):
    """Открыть/скачать файл"""
    try:
        target = safe_path(path)
        
        if not target.exists():
            raise HTTPException(status_code=404, detail="File not found")
        
        if not target.is_file():
            raise HTTPException(status_code=400, detail="Not a file")
        
        return FileResponse(
            path=target,
            filename=target.name,
            media_type='application/octet-stream'
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/files", response_class=HTMLResponse)
async def files_page():
    """Страница файлового менеджера"""
    return await root()

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
