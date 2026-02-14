"""
Skills Parser для Fantasy Dashboard
Динамически парсит _REGISTRY.md — автоматически подхватывает новые категории
"""

import re

def parse_registry_md(content: str) -> dict:
    """Парсит _REGISTRY.md в JSON структуру для FD"""
    categories = {}
    current_category = None
    
    # Заголовки которые НЕ являются категориями скиллов
    skip_headers = {
        "ТОМА", "ЧАСТО ИСПОЛЬЗУЕМЫЕ", "АРХИВ", "СТАТИСТИКА", 
        "АЛГОРИТМ ПОИСКА СКИЛЛА", "КОНТРАКТЫ КРИТИЧЕСКИХ СКИЛЛОВ"
    }
    
    # Emoji для категорий (по ключевым словам)
    category_emoji = {
        "СИСТЕМА": "⚙️",
        "CRM": "💼",
        "МЕССЕНДЖЕР": "💬",
        "ДОКУМЕНТ": "📋",
        "РОСПАТЕНТ": "🏛️",
        "АВТОМАТИЗАЦ": "🔧",
        "ИССЛЕДОВАН": "🔍",
        "ИНФРАСТРУКТУР": "🖥️",
        "УТИЛИТ": "🛠️",
        "ОТЧЁТ": "📊",
        "АНАЛИТИК": "📈",
    }
    
    # Emoji для скиллов по ключевым словам в названии
    skill_emoji = {
        "bitrix": "🔶", "mcrm": "📊", "crm": "💼",
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
        "forward": "↗️", "firstvds": "🖧", "history": "📜",
        "report": "📊", "analytics": "📈", "fd-": "🎮",
        "messenger": "💬", "new-": "✨", "rules": "📋",
    }
    
    def get_category_emoji(name: str) -> str:
        """Подобрать emoji для категории"""
        name_upper = name.upper()
        for key, emoji in category_emoji.items():
            if key in name_upper:
                return emoji
        return "📁"  # дефолт
    
    def get_skill_emoji(skill_name: str) -> str:
        """Подобрать emoji для скилла"""
        skill_lower = skill_name.lower()
        for key, emoji in skill_emoji.items():
            if key in skill_lower:
                return emoji
        return "📄"  # дефолт
    
    def format_category_name(raw_name: str) -> str:
        """Форматировать название категории"""
        # Убираем emoji и лишние символы
        clean = re.sub(r'[🔧📦⭐]', '', raw_name).strip()
        # Убираем "(вспомогательные)" и подобное
        clean = re.sub(r'\([^)]*\)', '', clean).strip()
        return clean
    
    lines = content.split("\n")
    
    for line in lines:
        line = line.strip()
        
        # Ищем заголовки категорий (## НАЗВАНИЕ)
        header_match = re.match(r"^## (.+)$", line)
        if header_match:
            raw_header = header_match.group(1).strip()
            header_clean = format_category_name(raw_header).upper()
            
            # Пропускаем служебные заголовки
            skip = False
            for skip_key in skip_headers:
                if skip_key in header_clean:
                    skip = True
                    current_category = None
                    break
            
            if not skip and header_clean:
                current_category = header_clean
                if current_category not in categories:
                    categories[current_category] = {
                        "emoji": get_category_emoji(current_category),
                        "name": format_category_name(raw_header).title(),
                        "skills": []
                    }
            continue
        
        # Ищем строки скиллов в таблице (| `skill-name` | триггеры | описание |)
        if current_category and line.startswith("|"):
            skill_match = re.match(r"\|\s*`([^`]+)`\s*\|([^|]*)\|([^|]*)\|", line)
            if skill_match:
                skill_name = skill_match.group(1).strip()
                triggers = skill_match.group(2).strip()
                description = skill_match.group(3).strip()
                
                # Пропускаем устаревшие скиллы
                if "устарел" in description.lower():
                    continue
                
                categories[current_category]["skills"].append({
                    "name": skill_name,
                    "emoji": get_skill_emoji(skill_name),
                    "triggers": triggers,
                    "description": description
                })
    
    return categories


# Тест
if __name__ == "__main__":
    test_content = """
## ТОМА
| Том | Описание |

## ОТЧЁТЫ
| Скилл | Триггеры | Описание |
| `session-report` | статус, контекст | Отчёт по сессии |
| `architecture-report` | диагностика | Отчёт по архитектуре |

## СИСТЕМА
| Скилл | Триггеры | Описание |
| `skill-creator` | создай скилл | Создание скиллов |
"""
    result = parse_registry_md(test_content)
    import json
    print(json.dumps(result, ensure_ascii=False, indent=2))
