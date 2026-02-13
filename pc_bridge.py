"""
Fantasy Dashboard - PC Bridge
Подключается к VPS и проксирует локальные файловые операции
"""

import asyncio
import json
import os
import aiohttp
from pathlib import Path
from datetime import datetime

# Конфигурация
VPS_URL = os.getenv('VPS_URL', 'ws://188.120.249.151:8000/ws/pc-bridge')
BRIDGE_SECRET = os.getenv('BRIDGE_SECRET', 'fantasy-bridge-2026')
FILES_ROOT = Path(os.getenv('FILES_ROOT', 'C:/BRANDONLINE'))
RECONNECT_DELAY = 5  # секунд

print(f"""
========================================
  Fantasy Dashboard - PC Bridge
========================================
VPS: {VPS_URL}
Root: {FILES_ROOT}
========================================
""")

async def handle_request(data: dict) -> dict:
    """Обработать запрос от VPS"""
    action = data.get('action')
    path = data.get('path', '')
    
    try:
        if action == 'list':
            return await list_files(path)
        elif action == 'read':
            return await read_file(path)
        elif action == 'download':
            return await download_file(path)
        elif action == 'open':
            return await get_file_url(path)
        elif action == 'ping':
            return {'status': 'ok', 'time': datetime.now().isoformat()}
        else:
            return {'error': f'Unknown action: {action}'}
    except Exception as e:
        return {'error': str(e)}

def safe_path(relative_path: str) -> Path:
    """Безопасное разрешение пути"""
    clean = relative_path.replace('\\', '/').strip('/')
    full = (FILES_ROOT / clean).resolve()
    
    # Проверка что внутри корня
    try:
        full.relative_to(FILES_ROOT.resolve())
    except ValueError:
        raise PermissionError(f"Access denied: {relative_path}")
    
    return full

async def list_files(path: str) -> dict:
    """Список файлов в папке"""
    target = safe_path(path)
    
    if not target.exists():
        return {'error': 'Path not found', 'path': path}
    
    if not target.is_dir():
        return {'error': 'Not a directory', 'path': path}
    
    items = []
    for item in sorted(target.iterdir(), key=lambda x: (not x.is_dir(), x.name.lower())):
        try:
            stat = item.stat()
            items.append({
                'name': item.name,
                'type': 'folder' if item.is_dir() else 'file',
                'size': stat.st_size if item.is_file() else None,
                'modified': datetime.fromtimestamp(stat.st_mtime).isoformat(),
                'extension': item.suffix.lower() if item.is_file() else None
            })
        except (PermissionError, OSError):
            continue
    
    return {
        'path': path,
        'parent': str(Path(path).parent) if path else None,
        'items': items
    }

async def read_file(path: str) -> dict:
    """Прочитать текстовый файл"""
    target = safe_path(path)
    
    if not target.exists():
        return {'error': 'File not found'}
    
    if not target.is_file():
        return {'error': 'Not a file'}
    
    if target.stat().st_size > 5_000_000:
        return {'error': 'File too large (max 5MB)'}
    
    ext = target.suffix.lower()
    text_ext = {'.txt', '.md', '.json', '.py', '.js', '.html', '.css', '.yaml', '.yml', '.xml', '.csv', '.log', '.bat', '.sh', '.ps1', '.ini', '.cfg', '.env', '.gitignore'}
    
    # DOCX файлы
    if ext == '.docx':
        try:
            from docx import Document
            doc = Document(target)
            content = '\n\n'.join([p.text for p in doc.paragraphs])
            return {'content': content, 'type': 'text', 'name': target.name, 'format': 'docx'}
        except ImportError:
            return {'error': 'python-docx not installed', 'type': 'binary'}
        except Exception as e:
            return {'error': f'Cannot read docx: {str(e)}', 'type': 'binary'}
    
    # ODT файлы
    if ext == '.odt':
        try:
            from odf import text as odftext
            from odf.opendocument import load
            doc = load(target)
            paragraphs = doc.getElementsByType(odftext.P)
            content = '\n\n'.join([p.firstChild.data if p.firstChild else '' for p in paragraphs])
            return {'content': content, 'type': 'text', 'name': target.name, 'format': 'odt'}
        except ImportError:
            return {'error': 'odfpy not installed', 'type': 'binary'}
        except Exception as e:
            return {'error': f'Cannot read odt: {str(e)}', 'type': 'binary'}
    
    # Обычные текстовые файлы
    if ext in text_ext or ext == '':
        try:
            content = target.read_text(encoding='utf-8')
            return {'content': content, 'type': 'text', 'name': target.name}
        except UnicodeDecodeError:
            return {'error': 'Binary file', 'type': 'binary'}
    else:
        return {'error': 'Unsupported format', 'type': 'binary', 'extension': ext}

async def download_file(path: str) -> dict:
    """Скачать файл (вернуть содержимое в base64)"""
    import base64
    target = safe_path(path)
    
    if not target.exists():
        return {'error': 'File not found'}
    
    if not target.is_file():
        return {'error': 'Not a file'}
    
    # Лимит 50MB
    if target.stat().st_size > 50_000_000:
        return {'error': 'File too large (max 50MB)'}
    
    content = target.read_bytes()
    return {
        'name': target.name,
        'size': len(content),
        'content': base64.b64encode(content).decode('ascii')
    }

async def get_file_url(path: str) -> dict:
    """Получить информацию о файле для скачивания"""
    target = safe_path(path)
    
    if not target.exists():
        return {'error': 'File not found'}
    
    return {
        'name': target.name,
        'size': target.stat().st_size,
        'path': str(target),
        'downloadable': True
    }

async def main():
    """Основной цикл подключения к VPS"""
    while True:
        try:
            print(f"[{datetime.now().strftime('%H:%M:%S')}] Connecting to VPS...")
            
            async with aiohttp.ClientSession() as session:
                async with session.ws_connect(VPS_URL) as ws:
                    print(f"[{datetime.now().strftime('%H:%M:%S')}] ✅ Connected!")
                    
                    # Авторизация
                    await ws.send_json({
                        'type': 'auth',
                        'secret': BRIDGE_SECRET
                    })
                    
                    async for msg in ws:
                        if msg.type == aiohttp.WSMsgType.TEXT:
                            try:
                                data = json.loads(msg.data)
                                
                                if data.get('type') == 'request':
                                    # Обработка запроса
                                    request_id = data.get('id')
                                    result = await handle_request(data)
                                    result['id'] = request_id
                                    result['type'] = 'response'
                                    await ws.send_json(result)
                                    
                                elif data.get('type') == 'ping':
                                    await ws.send_json({'type': 'pong'})
                                    
                            except json.JSONDecodeError:
                                print(f"Invalid JSON: {msg.data[:100]}")
                                
                        elif msg.type == aiohttp.WSMsgType.ERROR:
                            print(f"WebSocket error: {ws.exception()}")
                            break
                        elif msg.type == aiohttp.WSMsgType.CLOSED:
                            print("WebSocket closed")
                            break
                            
        except aiohttp.ClientError as e:
            print(f"[{datetime.now().strftime('%H:%M:%S')}] Connection error: {e}")
        except Exception as e:
            print(f"[{datetime.now().strftime('%H:%M:%S')}] Error: {e}")
        
        print(f"[{datetime.now().strftime('%H:%M:%S')}] Reconnecting in {RECONNECT_DELAY}s...")
        await asyncio.sleep(RECONNECT_DELAY)

if __name__ == '__main__':
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\nStopped.")
