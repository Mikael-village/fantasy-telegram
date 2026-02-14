#!/usr/bin/env python3
"""Fix full layout according to spec"""

with open('/var/www/fantasy-telegram/index.html', 'r', encoding='utf-8') as f:
    content = f.read()

# Fix RIGHT panel (messengers) - from bottom to top: TG, MAX, WA, Mail, placeholder
old_right = '''        <div class="side-panel">
            <button class="side-btn" onclick="openMessenger('Telegram')" title="Telegram">✈️</button>
            <button class="side-btn" onclick="openMessenger('MAX')" title="MAX">💬</button>
            <button class="side-btn" onclick="openMessenger('WhatsApp')" title="WhatsApp">💚</button>
            <button class="side-btn" onclick="openMessenger('Mail')" title="Почта">📧</button>
            <button class="side-btn" onclick="openCRM()" title="CRM">📊</button>
        </div>'''

new_right = '''        <div class="side-panel">
            <button class="side-btn" disabled title="Заглушка">⬜</button>
            <button class="side-btn" onclick="openMessenger('Mail')" title="Почта"><img src="https://www.google.com/s2/favicons?domain=mail.ru&sz=32" alt="Mail"></button>
            <button class="side-btn" onclick="openMessenger('WhatsApp')" title="WhatsApp"><img src="https://www.google.com/s2/favicons?domain=whatsapp.com&sz=32" alt="WA"></button>
            <button class="side-btn" onclick="openMessenger('MAX')" title="MAX"><img src="/max-icon-small.png" alt="MAX"></button>
            <button class="side-btn" onclick="openMessenger('Telegram')" title="Telegram"><img src="https://www.google.com/s2/favicons?domain=telegram.org&sz=32" alt="TG"></button>
        </div>'''

# Fix LEFT panel - 5 placeholders
old_left = '''        <div class="side-panel">
            <button class="side-btn" onclick="openService('https://brand-search.ru/', 'Поиск ТЗ', false)" title="brand-search.ru">🔍</button>
            <button class="side-btn" onclick="openService('https://linkmark.ru/', 'Linkmark', true)" title="linkmark.ru">🔗</button>
            <button class="side-btn" onclick="openService('https://www1.fips.ru/registers-web/action?acName=clickRegister&regName=RUTM', 'ФИПС ТЗ', false)" title="Реестр ТЗ">📋</button>
            <button class="side-btn" onclick="openService('https://www1.fips.ru/registers-web/action?acName=clickRegister&regName=RUTMAP', 'ФИПС Заявки', false)" title="Реестр заявок">📝</button>
            <button class="side-btn" onclick="openService('https://www.pochta.ru/tracking', 'Почта РФ', true)" title="Почта РФ">📦</button>
        </div>'''

new_left = '''        <div class="side-panel">
            <button class="side-btn" disabled title="Заглушка 1">➊</button>
            <button class="side-btn" disabled title="Заглушка 2">➋</button>
            <button class="side-btn" disabled title="Заглушка 3">➌</button>
            <button class="side-btn" disabled title="Заглушка 4">➍</button>
            <button class="side-btn" disabled title="Заглушка 5">➎</button>
        </div>'''

changes = 0
if old_right in content:
    content = content.replace(old_right, new_right)
    changes += 1
    print('RIGHT panel fixed')
else:
    print('RIGHT panel not found (may need manual fix)')

if old_left in content:
    content = content.replace(old_left, new_left)
    changes += 1
    print('LEFT panel fixed')
else:
    print('LEFT panel not found (may need manual fix)')

if changes > 0:
    with open('/var/www/fantasy-telegram/index.html', 'w', encoding='utf-8') as f:
        f.write(content)
    print(f'SUCCESS: {changes} panels fixed')
else:
    print('No changes made')
