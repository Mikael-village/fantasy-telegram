"""
Парсер _REGISTRY.md для API /api/skills
"""
import re

def parse_registry_md(content: str) -> dict:
    """Парсит _REGISTRY.md в JSON структуру для FD"""
    categories = {}
    current_category = None
    
    # Маппинг заголовков на emoji и названия
    category_map = {
        "СИСТЕМА": {"emoji": "⚙️", "name": "Система"},
        "CRM": {"emoji": "💼", "name": "CRM"},
        "МЕССЕНДЖЕРЫ": {"emoji": "💬", "name": "Мессенджеры"},
        "ДОКУМЕНТЫ": {"emoji": "📋", "name": "Документы"},
        "РОСПАТЕНТ": {"emoji": "🏛️", "name": "Роспатент"},
        "АВТОМАТИЗАЦИЯ": {"emoji": "🔧", "name": "Автоматизация"},
        "ИССЛЕДОВАНИЕ": {"emoji": "🔍", "name": "Исследование"},
        "ИНФРАСТРУКТУРА": {"emoji": "🖥️", "name": "Инфраструктура"},
        "УТИЛИТЫ": {"emoji": "🛠️", "name": "Утилиты"},
    }
    
    # Emoji для скиллов по ключевым словам
    emoji_map = {
        "bitrix": "🔶", "mcrm": "📊",
        "telegram": "✈️", "whatsapp": "💚", "max": "💙",
        "договор": "📝", "контракт": "📝", "contract": "📝",
        "fips": "📋", "desktop": "🖥️", "macro": "⏺️",
        "site": "🌐", "research": "🔍", "vps": "🖧",
        "fantasy": "🎮", "skill": "✨", "system": "🏗️",
        "context": "💾", "workspace": "📁", "session": "📊",
        "voice": "🎤", "self": "📈", "critic": "🔍",
        "violation": "⚠️", "execution": "✅", "work": "📋",
        "yupp": "🤖", "prompting": "💬", "training": "🎯",
        "complex": "🧩", "architecture": "🏛️", "python": "🐍",
        "windows": "🪟", "sound": "🔊", "large": "📦",
        "brand": "🔍", "service": "🎓", "explorer": "🧭",
        "forward": "↗️", "firstvds": "🖧"
    }
    
    lines = content.split("\n")
    for line in lines:
        # Ищем заголовки категорий
        header_match = re.match(r"^## (.+)$", line.strip())
        if header_match:
            header = header_match.group(1).upper()
            for key in category_map:
                if key in header:
                    current_category = key
                    if current_category not in categories:
                        cat_info = category_map[current_category]
                        categories[current_category] = {
                            "emoji": cat_info["emoji"],
                            "name": cat_info["name"],
                            "skills": []
                        }
                    break
            else:
                # Категория не найдена в маппинге - сбросить
                if "ЧАСТО" in header or "АРХИВ" in header or "СТАТИСТИКА" in header or "АЛГОРИТМ" in header or "КОНТРАКТЫ" in header:
                    current_category = None
            continue
        
        # Ищем строки таблицы со скиллами
        if current_category and line.startswith("|") and "`" in line:
            parts = [p.strip() for p in line.split("|")]
            if len(parts) >= 4:
                skill_match = re.search(r"`([^`]+)`", parts[1])
                if skill_match:
                    skill_id = skill_match.group(1)
                    triggers = parts[2] if len(parts) > 2 else ""
                    description = parts[3] if len(parts) > 3 else ""
                    
                    # Пропускаем заголовок таблицы
                    if skill_id == "Скилл" or "---" in skill_id:
                        continue
                    
                    # Определяем emoji
                    emoji = "📄"
                    search_text = (skill_id + " " + triggers).lower()
                    for key, em in emoji_map.items():
                        if key in search_text:
                            emoji = em
                            break
                    
                    # Название из описания
                    name = description.split("—")[0].strip() if "—" in description else description
                    if len(name) > 35:
                        name = name[:32] + "..."
                    
                    categories[current_category]["skills"].append({
                        "id": skill_id,
                        "name": name,
                        "emoji": emoji,
                        "triggers": triggers
                    })
    
    return categories
