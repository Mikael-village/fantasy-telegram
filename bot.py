"""
Fantasy Dashboard Telegram Bot
Бот для управления RPG-дашбордом AI-ассистента
"""

import os
import json
import logging
from dotenv import load_dotenv

# Загрузка .env
load_dotenv()
from datetime import datetime
from telegram import Update, WebAppInfo, KeyboardButton, ReplyKeyboardMarkup, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes

# Настройка логирования
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# Конфигурация
BOT_TOKEN = os.getenv('BOT_TOKEN', 'YOUR_BOT_TOKEN_HERE')
WEBAPP_URL = os.getenv('WEBAPP_URL', 'https://your-domain.com')
DATA_FILE = 'data.json'

# ===== РАБОТА С ДАННЫМИ =====

def load_data() -> dict:
    """Загрузить данные из JSON"""
    try:
        with open(DATA_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)
    except FileNotFoundError:
        return get_default_data()

def save_data(data: dict):
    """Сохранить данные в JSON"""
    with open(DATA_FILE, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

def get_default_data() -> dict:
    """Данные по умолчанию"""
    return {
        "character": {
            "name": "Помощник Микаела",
            "title": "Хранитель Контекста",
            "class": "Архимаг Автоматизации",
            "level": 1
        },
        "hp": {"current": 100, "max": 100},
        "mana": {"used": 0, "max": 200000},
        "xp": {"current": 0, "total": 10},
        "stats": {
            "STR": {"label": "Сила обработки", "value": 50},
            "INT": {"label": "Интеллект", "value": 50},
            "WIS": {"label": "Мудрость", "value": 50},
            "DEX": {"label": "Скорость", "value": 50},
            "CHR": {"label": "Общение", "value": 50}
        },
        "spells": [],
        "knowledge": [],
        "quests": []
    }

# ===== КЛАВИАТУРЫ =====

def get_main_keyboard() -> ReplyKeyboardMarkup:
    """Главная клавиатура с кнопкой Mini App"""
    keyboard = [
        [KeyboardButton(
            text="⚔️ Fantasy Dashboard",
            web_app=WebAppInfo(url=f"{WEBAPP_URL}/dashboard")
        )],
        [KeyboardButton("📊 Статус"), KeyboardButton("❓ Помощь")]
    ]
    return ReplyKeyboardMarkup(keyboard, resize_keyboard=True)

# ===== КОМАНДЫ =====

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Команда /start"""
    welcome_text = """
⚔️ *Приветствую тебя, Странник!*

Я — хранитель _Книги Судеб_, что ведёт летопись деяний великого Архимага Автоматизации.

🎮 *Доступные заклинания:*
• /dashboard — открыть Fantasy Dashboard
• /status — текущее состояние героя
• /quest <название> — добавить новый квест
• /done <название> — завершить квест
• /hp <число> — установить здоровье
• /mana <число> — установить использованный контекст
• /level — повысить уровень
• /addspell — добавить заклинание
• /addknowledge — добавить свиток знаний

Нажми кнопку *⚔️ Fantasy Dashboard* чтобы узреть свою судьбу!
    """
    await update.message.reply_text(
        welcome_text,
        parse_mode='Markdown',
        reply_markup=get_main_keyboard()
    )

async def dashboard(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Команда /dashboard"""
    await update.message.reply_text(
        "🏰 Нажми кнопку ниже, чтобы открыть Fantasy Dashboard:",
        reply_markup=get_main_keyboard()
    )

async def status(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Команда /status - показать текущее состояние"""
    data = load_data()
    char = data['character']
    hp = data['hp']
    mana = data['mana']
    xp = data['xp']
    
    # Подсчёт квестов
    active_quests = sum(1 for q in data['quests'] if q['status'] == 'active')
    done_quests = sum(1 for q in data['quests'] if q['status'] == 'done')
    
    status_text = f"""
⚔️ *{char['name']}*
_{char['title']}_
Класс: {char['class']}
Уровень: ⭐ {char['level']}

❤️ Здоровье: {hp['current']}/{hp['max']}
💙 Контекст: {mana['used']:,}/{mana['max']:,} ({round(mana['used']/mana['max']*100)}%)
⭐ Опыт: {xp['current']}/{xp['total']} квестов

📜 Квесты: {done_quests} ✅ / {active_quests} ⏳
📖 Заклинаний: {len(data['spells'])}
🔮 Свитков знаний: {len(data['knowledge'])}
    """
    await update.message.reply_text(status_text, parse_mode='Markdown')

async def add_quest(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Команда /quest <название> - добавить квест"""
    if not context.args:
        await update.message.reply_text("⚠️ Укажи название квеста: /quest Название задачи")
        return
    
    quest_name = ' '.join(context.args)
    data = load_data()
    
    data['quests'].append({
        "name": quest_name,
        "status": "active",
        "date": datetime.now().strftime("%Y-%m-%d")
    })
    
    save_data(data)
    await update.message.reply_text(f"📜 Квест добавлен: ⏳ *{quest_name}*", parse_mode='Markdown')

async def complete_quest(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Команда /done <название> - завершить квест"""
    if not context.args:
        await update.message.reply_text("⚠️ Укажи название квеста: /done Название задачи")
        return
    
    quest_name = ' '.join(context.args).lower()
    data = load_data()
    
    found = False
    for quest in data['quests']:
        if quest['name'].lower() == quest_name and quest['status'] == 'active':
            quest['status'] = 'done'
            quest['date'] = datetime.now().strftime("%Y-%m-%d")
            found = True
            break
    
    if found:
        # Увеличиваем XP
        data['xp']['current'] += 1
        save_data(data)
        await update.message.reply_text(
            f"✅ Квест завершён: *{quest['name']}*\n⭐ +1 XP!",
            parse_mode='Markdown'
        )
    else:
        await update.message.reply_text("❌ Активный квест с таким названием не найден")

async def set_hp(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Команда /hp <число> - установить HP"""
    if not context.args:
        await update.message.reply_text("⚠️ Укажи значение: /hp 85")
        return
    
    try:
        value = int(context.args[0])
        data = load_data()
        data['hp']['current'] = max(0, min(value, data['hp']['max']))
        save_data(data)
        await update.message.reply_text(f"❤️ Здоровье установлено: {data['hp']['current']}/{data['hp']['max']}")
    except ValueError:
        await update.message.reply_text("⚠️ Укажи число: /hp 85")

async def set_mana(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Команда /mana <число> - установить использованный контекст"""
    if not context.args:
        await update.message.reply_text("⚠️ Укажи значение: /mana 90000")
        return
    
    try:
        value = int(context.args[0])
        data = load_data()
        data['mana']['used'] = max(0, min(value, data['mana']['max']))
        save_data(data)
        pct = round(data['mana']['used'] / data['mana']['max'] * 100)
        await update.message.reply_text(f"💙 Контекст: {data['mana']['used']:,}/{data['mana']['max']:,} ({pct}%)")
    except ValueError:
        await update.message.reply_text("⚠️ Укажи число: /mana 90000")

async def level_up(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Команда /level - повысить уровень"""
    data = load_data()
    data['character']['level'] += 1
    save_data(data)
    await update.message.reply_text(
        f"🎉 *LEVEL UP!*\n\nТеперь ты ⭐ Уровень {data['character']['level']}!",
        parse_mode='Markdown'
    )

async def add_knowledge(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Команда /addknowledge <название> - добавить свиток знаний"""
    if not context.args:
        await update.message.reply_text("⚠️ Укажи название: /addknowledge Название свитка")
        return
    
    name = ' '.join(context.args)
    data = load_data()
    
    data['knowledge'].append({
        "name": name,
        "icon": "📜"
    })
    
    save_data(data)
    await update.message.reply_text(f"📜 Свиток добавлен: *{name}*", parse_mode='Markdown')

async def add_spell(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Команда /addspell название|иконка|категория|уровень|описание"""
    if not context.args:
        await update.message.reply_text(
            "⚠️ Формат: /addspell Название|⚡|Боевая магия|5|Описание заклинания"
        )
        return
    
    try:
        parts = ' '.join(context.args).split('|')
        if len(parts) != 5:
            raise ValueError("Неверный формат")
        
        name, icon, category, level, desc = parts
        data = load_data()
        
        data['spells'].append({
            "name": name.strip(),
            "icon": icon.strip(),
            "category": category.strip(),
            "level": int(level.strip()),
            "desc": desc.strip()
        })
        
        save_data(data)
        await update.message.reply_text(
            f"✨ Заклинание добавлено: {icon} *{name}* (Lv.{level})",
            parse_mode='Markdown'
        )
    except Exception as e:
        await update.message.reply_text(
            f"⚠️ Ошибка. Формат: /addspell Название|⚡|Боевая магия|5|Описание"
        )

async def update_data(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработка команды актуализации данных"""
    await update.message.reply_text(
        "✨ *Данные в Книге Судеб обновлены!*\n\nОткрой Fantasy Dashboard чтобы увидеть изменения.",
        parse_mode='Markdown',
        reply_markup=get_main_keyboard()
    )

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Команда /help"""
    help_text = """
📖 *Книга Заклинаний Управления*

*Основные команды:*
/start — начать
/dashboard — открыть дашборд
/status — текущее состояние

*Управление квестами:*
/quest <название> — новый квест
/done <название> — завершить квест

*Параметры персонажа:*
/hp <число> — установить HP
/mana <число> — установить контекст
/level — повысить уровень

*Добавление:*
/addknowledge <название>
/addspell Название|⚡|Категория|5|Описание

*Категории заклинаний:*
• Боевая магия
• Артефакты
• Аура поддержки
    """
    await update.message.reply_text(help_text, parse_mode='Markdown')

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработка текстовых сообщений"""
    text = update.message.text.lower()
    
    if 'статус' in text or '📊' in text:
        await status(update, context)
    elif 'помощь' in text or '❓' in text:
        await help_command(update, context)
    elif 'актуализируй' in text and 'fantasy' in text:
        await update_data(update, context)

# ===== MAIN =====

def main():
    """Запуск бота"""
    if BOT_TOKEN == 'YOUR_BOT_TOKEN_HERE':
        logger.error("⚠️ Укажи BOT_TOKEN в переменных окружения!")
        return
    
    # Создаём приложение
    application = Application.builder().token(BOT_TOKEN).build()
    
    # Регистрируем обработчики
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("dashboard", dashboard))
    application.add_handler(CommandHandler("status", status))
    application.add_handler(CommandHandler("quest", add_quest))
    application.add_handler(CommandHandler("done", complete_quest))
    application.add_handler(CommandHandler("hp", set_hp))
    application.add_handler(CommandHandler("mana", set_mana))
    application.add_handler(CommandHandler("level", level_up))
    application.add_handler(CommandHandler("addknowledge", add_knowledge))
    application.add_handler(CommandHandler("addspell", add_spell))
    application.add_handler(CommandHandler("help", help_command))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    
    # Запуск
    logger.info("🚀 Fantasy Bot запущен!")
    application.run_polling(allowed_updates=Update.ALL_TYPES)

if __name__ == '__main__':
    main()
