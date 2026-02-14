# Fantasy Dashboard — План оптимизации

## ⚠️ ИСТОРИЯ ПОПЫТОК

### Попытка 1 (2026-02-14 02:00)
**Статус:** ❌ ОТКАТ

**Что сделали:**
- Извлекли CSS/JS из index.html через Python regex
- Создали static/css/main.css и static/js/app.js
- Добавили StaticFiles в server.py

**Причина поломки:**
Python-скрипт при добавлении `<link>` тега сломал HTML синтаксис:
```html
<!-- СЛОМАНО: -->
<link rel=" stylesheet\ href=\/static/css/main.css\>

<!-- ДОЛЖНО БЫТЬ: -->
<link rel="stylesheet" href="/static/css/main.css">
```

**Урок:** НЕ использовать regex для модификации HTML. Либо:
1. Редактировать вручную
2. Использовать HTML-парсер (BeautifulSoup)
3. Создавать новый файл с нуля

**Что осталось после отката:**
- ✅ logrotate настроен
- ✅ gzip включен в nginx
- ✅ Кэширование статики в nginx настроено
- ✅ Папки static/css и static/js созданы
- ✅ StaticFiles в server.py добавлен
- 📁 index_broken.html — сломанная версия (для анализа)
- 📁 index_old_backup.html — рабочий бэкап

---

## 📋 ТЕКУЩЕЕ СОСТОЯНИЕ

- **index.html**: 60KB, 1726 строк (монолит HTML+CSS+JS)
- **server.py**: 25KB, 737 строк
- **bot.py**: 14KB, 361 строк
- **bot.log**: 21MB (нет ротации!)
- **Хостинг**: VPS Ubuntu, systemd, nginx

## 🎯 ЦЕЛИ

1. **Масштабируемость** — легко добавлять новый функционал
2. **Читаемость** — любой разработчик разберётся
3. **Скорость** — быстрая загрузка
4. **Кэширование** — не качать заново каждый раз
5. **PWA** — использовать возможности устройства

---

## 🔴 P0 — КРИТИЧНО (выполнить первым)

### 1. Ротация логов

```bash
sudo tee /etc/logrotate.d/fantasy-dashboard << 'EOF'
/var/www/fantasy-dashboard/bot.log {
    daily
    rotate 7
    maxsize 10M
    compress
    delaycompress
    notifempty
    missingok
    create 0644 root root
}
EOF

# Проверить
sudo logrotate -d /etc/logrotate.d/fantasy-dashboard
```

### 2. Gzip в nginx

```nginx
# /etc/nginx/conf.d/gzip.conf
gzip on;
gzip_types text/html text/css application/javascript application/json;
gzip_min_length 1024;
gzip_vary on;
```

```bash
sudo nginx -t && sudo systemctl reload nginx
```

### 3. Разбить index.html на модули

**Структура:**
```
/var/www/fantasy-telegram/
├── index.html          # Минимальный HTML (~2KB)
├── static/
│   ├── css/
│   │   └── main.css    # Все стили
│   └── js/
│       ├── app.js      # Точка входа
│       ├── fileManager.js
│       ├── messengers.js
│       ├── aiStatus.js
│       └── search.js
├── server.py
└── bot.py
```

**index.html (новый):**
```html
<!DOCTYPE html>
<html lang="ru">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Fantasy Dashboard</title>
    <link rel="stylesheet" href="/static/css/main.css">
    <link rel="manifest" href="/manifest.json">
    <script src="https://telegram.org/js/telegram-web-app.js"></script>
</head>
<body>
    <div id="app"></div>
    <script type="module" src="/static/js/app.js"></script>
</body>
</html>
```

### 4. Добавить роут для static в server.py

```python
from fastapi.staticfiles import StaticFiles

# После создания app
app.mount("/static", StaticFiles(directory="static"), name="static")
```

---

## 🟡 P1 — ВАЖНО (после P0)

### 5. Кэширование статики в nginx

```nginx
location /static/ {
    expires 1y;
    add_header Cache-Control "public, immutable";
}
```

### 6. Service Worker для офлайн

```javascript
// sw.js
const CACHE_VERSION = 'v1.0.0';
const CACHE_FILES = [
    '/',
    '/static/css/main.css',
    '/static/js/app.js',
    '/manifest.json'
];

self.addEventListener('install', e => {
    e.waitUntil(
        caches.open(CACHE_VERSION)
            .then(cache => cache.addAll(CACHE_FILES))
    );
});

self.addEventListener('fetch', e => {
    // API не кэшируем
    if (e.request.url.includes('/api/')) return;
    
    e.respondWith(
        caches.match(e.request)
            .then(cached => cached || fetch(e.request))
    );
});
```

### 7. Регистрация SW в app.js

```javascript
if ('serviceWorker' in navigator) {
    navigator.serviceWorker.register('/sw.js');
}
```

---

## 🟢 P2 — ОПЦИОНАЛЬНО

### 8. Минификация (если нужно ещё быстрее)

```bash
# Установить
npm i -g terser clean-css-cli

# Минифицировать
terser static/js/*.js -o static/js/app.min.js -c -m
cleancss static/css/main.css -o static/css/main.min.css
```

### 9. Vite (если проект растёт)

```bash
npm create vite@latest . -- --template vanilla
```

---

## ✅ ЧЕКЛИСТ ВЫПОЛНЕНИЯ

- [x] Настроить logrotate
- [x] Включить gzip в nginx
- [x] Создать папку static/css и static/js
- [x] Добавить StaticFiles в server.py
- [x] Настроить кэширование в nginx
- [x] **Вынести CSS из index.html в main.css** ✅ 2026-02-14
- [x] **Вынести JS из index.html в app.js** ✅ 2026-02-14
- [x] **Создать новый минимальный index.html** ✅ 2026-02-14
- [x] **Задеплоить и проверить** ✅ 2026-02-14 (HTTP 200 все файлы)
- [x] **Обновить sw.js для кэширования** ✅ 2026-02-14 (версия v2)

---

## 🚀 БЫСТРЫЙ СТАРТ (следующая сессия)

**Триггер:** "Начать оптимизацию Fantasy Dashboard" или "Оптимизация FD"

**План:**
1. Прочитать этот файл (`apps/fantasy-telegram/OPTIMIZATION.md`)
2. Вручную создать новый index.html (не через regex!)
3. Скопировать CSS в `static/css/main.css`
4. Скопировать JS в `static/js/app.js`
5. Задеплоить и проверить

**Ключевое правило:** Создавать файлы ВРУЧНУЮ или через Write, НЕ через sed/regex на существующем HTML

---

## 📈 ОЖИДАЕМЫЙ РЕЗУЛЬТАТ

| Метрика | До | После |
|---------|-----|-------|
| Размер HTML | 60KB | ~2KB |
| Передача (gzip) | 60KB | ~15KB |
| Первая загрузка | ~3s | ~1.2s |
| Повторная загрузка | ~1.5s | <100ms |

---

*Создано: 2026-02-14*
