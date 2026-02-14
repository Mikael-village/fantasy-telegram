#!/usr/bin/env python3
"""Fix right panel - replace services with messengers"""

with open('/var/www/fantasy-telegram/index.html', 'r', encoding='utf-8') as f:
    content = f.read()

old_panel = '''        <div class="side-panel">
            <button class="side-btn" onclick="openService('https://www1.fips.ru/registers-web/', 'ФИПС', false)" title="Все реестры">🏛️</button>
            <button class="side-btn" onclick="alert('В разработке')" title="Избранное">⭐</button>
            <button class="side-btn" onclick="alert('В разработке')" title="Недавние">🕐</button>
            <button class="side-btn" onclick="alert('В разработке')" title="Поиск">🔎</button>
            <button class="side-btn" onclick="openCRM()" title="CRM">📊</button>
        </div>
    </div>

    <!-- File Actions Modal -->'''

new_panel = '''        <div class="side-panel">
            <button class="side-btn" onclick="openMessenger('Telegram')" title="Telegram">✈️</button>
            <button class="side-btn" onclick="openMessenger('MAX')" title="MAX">💬</button>
            <button class="side-btn" onclick="openMessenger('WhatsApp')" title="WhatsApp">💚</button>
            <button class="side-btn" onclick="openMessenger('Mail')" title="Почта">📧</button>
            <button class="side-btn" onclick="openCRM()" title="CRM">📊</button>
        </div>
    </div>

    <!-- File Actions Modal -->'''

if old_panel in content:
    content = content.replace(old_panel, new_panel)
    with open('/var/www/fantasy-telegram/index.html', 'w', encoding='utf-8') as f:
        f.write(content)
    print('SUCCESS: Panel replaced')
else:
    print('ERROR: Old panel not found')
