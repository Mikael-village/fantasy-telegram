// Fantasy Dashboard - Main Application
// Generated: 2026-02-14

const API_BASE = window.location.origin;
let currentPath = '';
let pathHistory = [];
let currentRootPath = '';
let openedWindows = {};

const isMobile = /Android|webOS|iPhone|iPad|iPod|BlackBerry|IEMobile|Opera Mini/i.test(navigator.userAgent);

const messengerLinks = {
    'Telegram': { web: 'https://web.telegram.org/', app: 'tg://resolve' },
    'MAX': { web: 'https://web.max.ru/', app: 'https://max.ru/im' },
    'WhatsApp': { web: 'https://web.whatsapp.com/', app: 'whatsapp://chat' },
    'Mail': { web: 'https://e.mail.ru/inbox/', app: 'https://e.mail.ru/' },
    'VK': { web: 'https://vk.com/', app: 'vk://' }
};

// ===== INIT =====
document.addEventListener('DOMContentLoaded', () => {
    updateDate();
    setInterval(updateDate, 60000);
    loadVersionInfo();
    
    if (window.Telegram?.WebApp) {
        Telegram.WebApp.ready();
        Telegram.WebApp.expand();
    }
});

// ===== VERSION INFO =====
async function loadVersionInfo() {
    try {
        const response = await fetch(`${API_BASE}/api/version`);
        if (!response.ok) return;
        
        const data = await response.json();
        
        // Отображаем версию
        const versionEl = document.getElementById('versionText');
        if (versionEl && data.version) {
            versionEl.textContent = `v${data.version}`;
        }
        
        // Отображаем дату последнего обновления
        const updateEl = document.getElementById('lastUpdateText');
        if (updateEl && data.lastUpdate) {
            const date = new Date(data.lastUpdate);
            const formatted = date.toLocaleString('ru-RU', {
                day: '2-digit',
                month: '2-digit',
                year: 'numeric',
                hour: '2-digit',
                minute: '2-digit'
            });
            updateEl.textContent = formatted;
        }
    } catch (e) {
        console.log('Version info not available');
    }
}

function updateDate() {
    const now = new Date();
    const options = { day: 'numeric', month: 'long', year: 'numeric' };
    document.getElementById('currentDate').textContent = now.toLocaleDateString('ru-RU', options);
}

// ===== VIEW MANAGEMENT =====
function showView(viewId) {
    document.querySelectorAll('.content-view').forEach(v => v.classList.remove('active'));
    document.getElementById(viewId).classList.add('active');
}

function closeView() {
    showView('emptyView');
    document.getElementById('serviceIframe').src = 'about:blank';
}

// ===== BOTTOM NAV ACTIONS =====
function openArchive() {
    currentRootPath = 'АРХИВ';
    openFolder('АРХИВ');
}

function openDownloads() {
    showView('downloadsView');
    loadDownloadsTab('Загрузки');
}

function openCRM() {
    showView('crmView');
    document.getElementById('crmIframe').src = 'https://crm.rko.center/leads';
}

function openHelper() {
    showView('helperView');
    loadSkills();
}

// ===== MESSENGER POPUP =====
function toggleMessengerPopup() {
    const popup = document.getElementById('messengerPopup');
    const overlay = document.getElementById('overlay');
    popup.classList.toggle('active');
    overlay.classList.toggle('active');
}

function closeMessengerPopup() {
    document.getElementById('messengerPopup').classList.remove('active');
    document.getElementById('overlay').classList.remove('active');
}

function openMessenger(name) {
    closeMessengerPopup();
    const links = messengerLinks[name];
    if (!links) return;
    
    if (isMobile && links.app) {
        const start = Date.now();
        window.location.href = links.app;
        
        setTimeout(() => {
            if (Date.now() - start < 2000) {
                window.open(links.web, '_blank');
            }
        }, 1500);
    } else {
        window.open(links.web, '_blank');
    }
}

// ===== SERVICES =====
function openService(url, name, canIframe) {
    if (canIframe && !isMobile) {
        showView('serviceView');
        document.getElementById('serviceTitle').textContent = name;
        document.getElementById('serviceIframe').src = url;
    } else {
        window.open(url, '_blank');
    }
}

// ===== FILE BROWSER =====
let archiveRootPath = 'АРХИВ';

async function openFolder(path) {
    showLoading(true);
    currentPath = path;
    pathHistory.push(path);

    try {
        const response = await fetch(`${API_BASE}/api/pc/files?path=${encodeURIComponent(path)}`);
        const data = await response.json();

        if (data.error) {
            alert(data.pc_online === false ? 'ПК не подключён' : 'Ошибка: ' + data.error);
            showLoading(false);
            return;
        }

        renderFiles(data.items || [], 'fileList');
        document.getElementById('currentPath').textContent = path.split('/').pop() || path;
        updateFileBreadcrumb();
        showView('fileBrowser');
    } catch (e) {
        alert('Ошибка: ' + e.message);
    }

    showLoading(false);
}

function updateFileBreadcrumb() {
    const bc = document.getElementById('fileBreadcrumb');
    const relativePath = currentPath.replace(archiveRootPath, '').replace(/^\//, '');
    
    if (!relativePath) {
        bc.innerHTML = '';
        return;
    }

    const parts = relativePath.split('/').filter(p => p);
    let html = `<span class="breadcrumb-item" onclick="openFolder('${archiveRootPath}')">🗄️ Архив</span>`;
    
    let buildPath = archiveRootPath;
    parts.forEach((part, i) => {
        buildPath += '/' + part;
        const isLast = i === parts.length - 1;
        html += `<span class="breadcrumb-sep">›</span>`;
        if (isLast) {
            html += `<span class="breadcrumb-item current">${part}</span>`;
        } else {
            html += `<span class="breadcrumb-item" onclick="openFolder('${buildPath}')">${part}</span>`;
        }
    });

    bc.innerHTML = html;
}

function goBack() {
    pathHistory.pop();
    if (pathHistory.length > 0) {
        const prev = pathHistory.pop();
        openFolder(prev);
    } else {
        closeView();
    }
}

// ===== DOWNLOADS TAB =====
let downloadsCurrentPath = '';
let downloadsRootPath = '';

function switchTab(folder, btn) {
    document.querySelectorAll('.folder-tab').forEach(t => t.classList.remove('active'));
    btn.classList.add('active');
    downloadsRootPath = folder;
    loadDownloadsFolder(folder);
}

async function loadDownloadsFolder(folder) {
    showLoading(true);
    downloadsCurrentPath = folder;

    try {
        const response = await fetch(`${API_BASE}/api/pc/files?path=${encodeURIComponent(folder)}`);
        const data = await response.json();

        if (data.error) {
            document.getElementById('downloadsFileList').innerHTML = 
                `<div class="empty-state"><span class="empty-state-icon">⚠️</span><span>${data.error}</span></div>`;
        } else {
            renderDownloadsFiles(data.items || []);
            updateBreadcrumb();
        }
    } catch (e) {
        document.getElementById('downloadsFileList').innerHTML = 
            `<div class="empty-state"><span class="empty-state-icon">⚠️</span><span>${e.message}</span></div>`;
    }

    showLoading(false);
}

function renderDownloadsFiles(items) {
    const list = document.getElementById('downloadsFileList');
    list.innerHTML = '';

    if (items.length === 0) {
        list.innerHTML = '<div class="empty-state"><span class="empty-state-icon">📭</span><span>Пусто</span></div>';
        return;
    }

    items.forEach(file => {
        const isFolder = file.type === 'folder';
        const item = document.createElement('div');
        item.className = 'file-item';
        item.onclick = () => {
            if (isFolder) {
                loadDownloadsFolder(downloadsCurrentPath + '/' + file.name);
            } else {
                showFileActions(downloadsCurrentPath + '/' + file.name, file.name);
            }
        };

        item.innerHTML = `
            <div class="file-icon ${isFolder ? 'folder' : ''}">${isFolder ? '📁' : getFileIcon(file.name)}</div>
            <div class="file-info">
                <div class="file-name">${file.name}</div>
                <div class="file-meta">${isFolder ? 'Папка' : formatSize(file.size || 0)}</div>
            </div>
        `;
        list.appendChild(item);
    });
}

function updateBreadcrumb() {
    const bc = document.getElementById('downloadsBreadcrumb');
    const relativePath = downloadsCurrentPath.replace(downloadsRootPath, '').replace(/^\//, '');
    
    if (!relativePath) {
        bc.innerHTML = '';
        return;
    }

    const parts = relativePath.split('/').filter(p => p);
    let html = `<span class="breadcrumb-item" onclick="loadDownloadsFolder('${downloadsRootPath}')">${downloadsRootPath === 'Загрузки' ? '📥' : '👥'} Корень</span>`;
    
    let buildPath = downloadsRootPath;
    parts.forEach((part, i) => {
        buildPath += '/' + part;
        const isLast = i === parts.length - 1;
        html += `<span class="breadcrumb-sep">›</span>`;
        if (isLast) {
            html += `<span class="breadcrumb-item current">${part}</span>`;
        } else {
            html += `<span class="breadcrumb-item" onclick="loadDownloadsFolder('${buildPath}')">${part}</span>`;
        }
    });

    bc.innerHTML = html;
}

async function loadDownloadsTab(folder) {
    downloadsRootPath = folder;
    loadDownloadsFolder(folder);
}

function renderFiles(items, listId, basePath = currentPath) {
    const list = document.getElementById(listId);
    list.innerHTML = '';

    if (items.length === 0) {
        list.innerHTML = '<div class="empty-state"><span class="empty-state-icon">📭</span><span>Пусто</span></div>';
        return;
    }

    items.forEach(file => {
        const isFolder = file.type === 'folder';
        const item = document.createElement('div');
        item.className = 'file-item';
        item.onclick = () => {
            if (isFolder) {
                openFolder(basePath + '/' + file.name);
            } else {
                showFileActions(basePath + '/' + file.name, file.name);
            }
        };

        item.innerHTML = `
            <div class="file-icon ${isFolder ? 'folder' : ''}">${isFolder ? '📁' : getFileIcon(file.name)}</div>
            <div class="file-info">
                <div class="file-name">${file.name}</div>
                <div class="file-meta">${isFolder ? 'Папка' : formatSize(file.size || 0)}</div>
            </div>
        `;
        list.appendChild(item);
    });
}

// ===== HELPER =====
async function showFile(filename) {
    showLoading(true);
    try {
        const basePath = 'Jarvis.Mir/Jarvis.Dom';
        const response = await fetch(`${API_BASE}/api/pc/file?path=${encodeURIComponent(basePath + '/' + filename)}`);
        const data = await response.json();
        
        if (data.error) {
            alert('Ошибка: ' + data.error);
        } else if (data.content) {
            showTextContent(filename, data.content);
        } else {
            alert('Файл пуст или не найден');
        }
    } catch (e) {
        alert('Ошибка: ' + e.message);
    }
    showLoading(false);
}

function showTextContent(title, content) {
    const modal = document.createElement('div');
    modal.className = 'text-modal';
    modal.innerHTML = `
        <div class="text-modal-content">
            <div class="text-modal-header">
                <span>${title}</span>
                <button onclick="this.closest('.text-modal').remove()">✕</button>
            </div>
            <pre class="text-modal-body">${escapeHtml(content)}</pre>
        </div>
    `;
    document.body.appendChild(modal);
}

// ===== RULES MODAL (USER.md) =====
async function showRulesModal() {
    showLoading(true);
    try {
        const basePath = 'Jarvis.Mir/Jarvis.Dom';
        const response = await fetch(`${API_BASE}/api/pc/file?path=${encodeURIComponent(basePath + '/USER.md')}`);
        const data = await response.json();
        
        if (data.error) {
            alert('Ошибка: ' + data.error);
            showLoading(false);
            return;
        }
        
        const rules = parseRulesFromMd(data.content || '');
        showRulesContent(rules);
    } catch (e) {
        alert('Ошибка: ' + e.message);
    }
    showLoading(false);
}

function parseRulesFromMd(content) {
    const rules = [];
    const lines = content.split('\n');
    let inRulesSection = false;
    let currentRule = null;
    
    for (let i = 0; i < lines.length; i++) {
        const line = lines[i];
        
        // Начало раздела правил
        if (line.includes('ЖЕЛЕЗНЫЕ ПРАВИЛА') || line.includes('🚨')) {
            inRulesSection = true;
            continue;
        }
        
        // Конец раздела (следующий раздел верхнего уровня или конец файла)
        if (inRulesSection && line.match(/^##\s+[^#]/) && !line.includes('🔒') && !line.includes('🛡️')) {
            break;
        }
        
        if (!inRulesSection) continue;
        
        // Новое правило (### 🔒 или ### 🛡️)
        if (line.match(/^###\s+🔒/) || line.match(/^###\s+🛡️/)) {
            if (currentRule) rules.push(currentRule);
            const title = line.replace(/^###\s+/, '').replace(/🔒|🛡️/g, '').trim();
            const icon = line.includes('🛡️') ? '🛡️' : '🔒';
            currentRule = { icon, title, description: [] };
            continue;
        }
        
        // Содержимое правила
        if (currentRule && line.trim()) {
            // Пропускаем технические строки
            if (line.startsWith('**Порядок:') || line.startsWith('Иначе =')) {
                const cleanLine = line
                    .replace(/\*\*/g, '')
                    .replace(/→/g, '→')
                    .trim();
                currentRule.description.push(cleanLine);
            } else if (line.startsWith('**') || line.startsWith('НИКОГДА') || line.startsWith('При ') || line.startsWith('После ') || line.startsWith('Перед ')) {
                const cleanLine = line
                    .replace(/\*\*/g, '')
                    .replace(/⛔/g, '')
                    .trim();
                if (cleanLine && !cleanLine.startsWith('---') && !cleanLine.startsWith('```')) {
                    currentRule.description.push(cleanLine);
                }
            }
        }
    }
    
    if (currentRule) rules.push(currentRule);
    return rules;
}

function showRulesContent(rules) {
    const modal = document.createElement('div');
    modal.className = 'text-modal';
    modal.onclick = (e) => { if (e.target === modal) modal.remove(); };
    
    let rulesHtml = '';
    rules.forEach(rule => {
        rulesHtml += `
            <div class="rule-item">
                <div class="rule-header">
                    <span class="rule-icon">${rule.icon}</span>
                    <span class="rule-title">${escapeHtml(rule.title)}</span>
                </div>
                <div class="rule-description">
                    ${rule.description.map(d => `<p>${escapeHtml(d)}</p>`).join('')}
                </div>
            </div>
        `;
    });
    
    modal.innerHTML = `
        <div class="text-modal-content rules-modal">
            <div class="text-modal-header">
                <span>📜 Правила</span>
                <div class="header-actions">
                    <button class="open-file-btn" onclick="showFile('USER.md')">📄 Файл</button>
                    <button onclick="this.closest('.text-modal').remove()">✕</button>
                </div>
            </div>
            <div class="rules-list">
                ${rulesHtml || '<p style="color: var(--text-secondary); text-align: center;">Правила не найдены</p>'}
            </div>
        </div>
    `;
    document.body.appendChild(modal);
}

// ===== GUIDES MODAL (AGENTS.md) =====
async function showGuidesModal() {
    showLoading(true);
    try {
        const basePath = 'Jarvis.Mir/Jarvis.Dom';
        const response = await fetch(`${API_BASE}/api/pc/file?path=${encodeURIComponent(basePath + '/AGENTS.md')}`);
        const data = await response.json();
        
        if (data.error) {
            alert('Ошибка: ' + data.error);
            showLoading(false);
            return;
        }
        
        const sections = parseGuidesFromMd(data.content || '');
        showGuidesContent(sections);
    } catch (e) {
        alert('Ошибка: ' + e.message);
    }
    showLoading(false);
}

function parseGuidesFromMd(content) {
    const sections = [];
    const lines = content.split('\n');
    let currentSection = null;
    
    for (let i = 0; i < lines.length; i++) {
        const line = lines[i];
        
        // Новый раздел (## заголовок)
        if (line.match(/^##\s+/)) {
            if (currentSection) sections.push(currentSection);
            
            let title = line.replace(/^##\s+/, '').trim();
            let icon = '📌';
            
            // Извлекаем эмодзи если есть
            const emojiMatch = title.match(/^([\u{1F300}-\u{1F9FF}]|[\u{2600}-\u{26FF}]|[\u{2700}-\u{27BF}])/u);
            if (emojiMatch) {
                icon = emojiMatch[1];
                title = title.replace(icon, '').trim();
            }
            
            currentSection = { icon, title, content: [] };
            continue;
        }
        
        // Содержимое раздела
        if (currentSection && line.trim()) {
            // Пропускаем таблицы и код
            if (line.startsWith('|') || line.startsWith('```')) continue;
            
            // Очищаем markdown
            let cleanLine = line
                .replace(/^\s*[-*]\s*/, '• ')  // списки
                .replace(/`([^`]+)`/g, '$1')   // код
                .replace(/\*\*([^*]+)\*\*/g, '$1')  // жирный
                .replace(/\[([^\]]+)\]\([^)]+\)/g, '$1')  // ссылки
                .replace(/→/g, '→')
                .trim();
            
            if (cleanLine && !cleanLine.startsWith('#')) {
                currentSection.content.push(cleanLine);
            }
        }
    }
    
    if (currentSection) sections.push(currentSection);
    return sections;
}

function showGuidesContent(sections) {
    const modal = document.createElement('div');
    modal.className = 'text-modal';
    modal.onclick = (e) => { if (e.target === modal) modal.remove(); };
    
    let sectionsHtml = '';
    sections.forEach(section => {
        sectionsHtml += `
            <div class="guide-item">
                <div class="guide-header">
                    <span class="guide-icon">${section.icon}</span>
                    <span class="guide-title">${escapeHtml(section.title)}</span>
                </div>
                <div class="guide-content">
                    ${section.content.map(c => `<p>${escapeHtml(c)}</p>`).join('')}
                </div>
            </div>
        `;
    });
    
    modal.innerHTML = `
        <div class="text-modal-content rules-modal">
            <div class="text-modal-header">
                <span>📖 Руководства</span>
                <div class="header-actions">
                    <button class="open-file-btn" onclick="showFile('AGENTS.md')">📄 Файл</button>
                    <button onclick="this.closest('.text-modal').remove()">✕</button>
                </div>
            </div>
            <div class="rules-list">
                ${sectionsHtml || '<p style="color: var(--text-secondary); text-align: center;">Руководства не найдены</p>'}
            </div>
        </div>
    `;
    document.body.appendChild(modal);
}

function escapeHtml(text) {
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}

// Skills - загружаются с API из _REGISTRY.md
let skillsCatalog = {};
let allSkills = [];

async function loadSkills() {
    const container = document.getElementById('skillsCategories');
    container.innerHTML = '<div class="loading-skills">Загрузка скиллов...</div>';
    allSkills = [];

    try {
        const response = await fetch(`${API_BASE}/api/skills`);
        const data = await response.json();
        
        if (data.error) {
            container.innerHTML = `<div class="error-state">⚠️ ${data.error}</div>`;
            return;
        }
        
        skillsCatalog = data.categories || {};
    } catch (e) {
        container.innerHTML = `<div class="error-state">⚠️ Ошибка загрузки: ${e.message}</div>`;
        return;
    }
    
    container.innerHTML = '';
    
    // Собираем все скиллы для поиска
    Object.entries(skillsCatalog).forEach(([categoryKey, categoryData]) => {
        const skills = categoryData.skills || [];
        skills.forEach(skill => {
            allSkills.push({ ...skill, category: `${categoryData.emoji} ${categoryData.name}` });
        });
    });

    // Рендерим категории
    Object.entries(skillsCatalog).forEach(([categoryKey, categoryData]) => {
        const skills = categoryData.skills || [];
        if (skills.length === 0) return;
        
        const categoryDiv = document.createElement('div');
        categoryDiv.className = 'skill-category';
        categoryDiv.innerHTML = `
            <div class="skill-category-header" onclick="toggleCategory(this)">
                <span class="skill-category-icon">${categoryData.emoji}</span>
                <span>${categoryData.name}</span>
                <span class="skill-category-count">${skills.length}</span>
            </div>
            <div class="skill-category-items">
                ${skills.map(skill => `
                    <div class="skill-category-item" onclick="openSkill('${skill.id}')">
                        <span class="skill-emoji">${skill.emoji}</span>
                        <span class="skill-name">${skill.name}</span>
                        <span class="skill-arrow">›</span>
                    </div>
                `).join('')}
            </div>
        `;
        container.appendChild(categoryDiv);
    });
}

function toggleCategory(header) {
    const category = header.parentElement;
    category.classList.toggle('expanded');
}

function filterSkills(query) {
    const container = document.getElementById('skillsCategories');
    query = query.toLowerCase().trim();

    if (!query) {
        loadSkills();
        return;
    }

    const filtered = allSkills.filter(skill => 
        skill.name.toLowerCase().includes(query) ||
        skill.triggers.toLowerCase().includes(query) ||
        skill.id.toLowerCase().includes(query)
    );

    container.innerHTML = '';

    if (filtered.length === 0) {
        container.innerHTML = '<div class="skill-item" style="color: var(--text-secondary)">Ничего не найдено</div>';
        return;
    }

    filtered.forEach(skill => {
        const div = document.createElement('div');
        div.className = 'skill-category-item';
        div.style.background = 'var(--bg-secondary)';
        div.style.borderRadius = '8px';
        div.style.marginBottom = '8px';
        div.style.border = '1px solid var(--border)';
        div.onclick = () => openSkill(skill.id);
        div.innerHTML = `
            <span class="skill-emoji">${skill.emoji}</span>
            <span class="skill-name">${skill.name}</span>
            <span class="skill-arrow">›</span>
        `;
        container.appendChild(div);
    });
}

async function openSkill(skillName) {
    showLoading(true);
    try {
        const response = await fetch(`${API_BASE}/api/pc/file?path=${encodeURIComponent('Jarvis.Mir/Jarvis.Dom/skills/' + skillName + '/SKILL.md')}`);
        const data = await response.json();
        
        if (data.content) {
            showTextContent(skillName + '/SKILL.md', data.content);
        } else {
            alert('SKILL.md не найден');
        }
    } catch (e) {
        alert('Ошибка: ' + e.message);
    }
    showLoading(false);
}

function showSkillGroup(group) {
    alert(`Группа скиллов: ${group}\n(В разработке)`);
}

// ===== FILE ACTIONS =====
let selectedFile = null;
let clipboardFile = null;

function showFileActions(path, filename) {
    selectedFile = { path, filename };
    document.getElementById('fileActionsTitle').textContent = filename;
    document.getElementById('fileActionsModal').style.display = 'flex';
}

function closeFileActions(event) {
    if (event && event.target !== event.currentTarget) return;
    document.getElementById('fileActionsModal').style.display = 'none';
    selectedFile = null;
}

async function fileActionOpen() {
    const file = selectedFile;
    closeFileActions();
    if (!file) {
        alert('Файл не выбран');
        return;
    }
    
    const ext = file.filename.split('.').pop().toLowerCase();
    const textExts = ['txt', 'md', 'json', 'js', 'py', 'html', 'css', 'xml', 'yaml', 'yml', 'log', 'bat', 'sh', 'ini', 'cfg', 'env', 'gitignore', 'docx', 'odt', 'doc'];
    const imageExts = ['jpg', 'jpeg', 'png', 'gif', 'webp', 'bmp', 'svg'];
    
    showLoading(true);
    
    try {
        if (textExts.includes(ext) || file.filename.startsWith('.')) {
            const url = `${API_BASE}/api/pc/file?path=${encodeURIComponent(file.path)}`;
            console.log('Fetching:', url);
            const response = await fetch(url);
            const data = await response.json();
            console.log('Response:', data);
            
            if (data.content) {
                showTextContent(file.filename, data.content);
            } else if (data.error) {
                alert('Ошибка: ' + data.error);
            } else {
                alert('Файл пуст или не удалось прочитать');
            }
        } else if (imageExts.includes(ext)) {
            const url = `${API_BASE}/api/pc/file/download?path=${encodeURIComponent(file.path)}`;
            showImagePreview(file.filename, url);
        } else if (ext === 'pdf') {
            const url = `${API_BASE}/api/pc/file/download?path=${encodeURIComponent(file.path)}`;
            showPdfPreview(file.filename, url);
        } else {
            alert('Формат ' + ext + ' не поддерживается для просмотра. Скачиваю...');
            downloadFile(file.path, file.filename);
        }
    } catch (e) {
        console.error('Error:', e);
        alert('Ошибка: ' + e.message);
    }
    
    showLoading(false);
}

function fileActionCopy() {
    const file = selectedFile;
    closeFileActions();
    if (!file) return;
    
    clipboardFile = { ...file };
    document.getElementById('clipboardFileName').textContent = file.filename;
    document.getElementById('clipboardIndicator').classList.add('active');
}

function clearClipboard() {
    clipboardFile = null;
    document.getElementById('clipboardIndicator').classList.remove('active');
}

function fileActionDownload() {
    const file = selectedFile;
    closeFileActions();
    if (!file) return;
    downloadFile(file.path, file.filename);
}

function downloadFile(path, filename) {
    const url = `${API_BASE}/api/pc/file/download?path=${encodeURIComponent(path)}`;
    const a = document.createElement('a');
    a.href = url;
    a.download = filename;
    a.target = '_blank';
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
}

async function fileActionSaveToPC() {
    const file = selectedFile;
    closeFileActions();
    if (!file) return;
    
    showLoading(true);
    try {
        const response = await fetch(`${API_BASE}/api/pc/save-to-downloads?path=${encodeURIComponent(file.path)}`, {
            method: 'POST'
        });
        const data = await response.json();
        
        if (data.error) {
            alert('Ошибка: ' + data.error);
        } else if (data.success) {
            showToast(`✅ Сохранено: ${data.filename}`);
        }
    } catch (e) {
        alert('Ошибка: ' + e.message);
    }
    showLoading(false);
}

function showToast(message) {
    const toast = document.createElement('div');
    toast.className = 'toast-notification';
    toast.textContent = message;
    toast.style.cssText = 'position:fixed;bottom:80px;left:50%;transform:translateX(-50%);background:#333;color:#fff;padding:12px 24px;border-radius:8px;z-index:10000;animation:fadeIn 0.3s';
    document.body.appendChild(toast);
    setTimeout(() => toast.remove(), 3000);
}

function showImagePreview(title, url) {
    const modal = document.createElement('div');
    modal.className = 'text-modal';
    modal.onclick = (e) => { if (e.target === modal) modal.remove(); };
    modal.innerHTML = `
        <div class="text-modal-content">
            <div class="text-modal-header">
                <span>${title}</span>
                <button onclick="this.closest('.text-modal').remove()">✕</button>
            </div>
            <div class="text-modal-body" style="text-align:center;padding:8px;">
                <img src="${url}" alt="${title}" style="max-height:70vh;">
            </div>
        </div>
    `;
    document.body.appendChild(modal);
}

function showPdfPreview(title, url) {
    const modal = document.createElement('div');
    modal.className = 'text-modal';
    modal.onclick = (e) => { if (e.target === modal) modal.remove(); };
    modal.innerHTML = `
        <div class="text-modal-content" style="max-width:90%;height:85vh;">
            <div class="text-modal-header">
                <span>${title}</span>
                <button onclick="this.closest('.text-modal').remove()">✕</button>
            </div>
            <div class="text-modal-body" style="padding:0;flex:1;">
                <iframe src="${url}" style="width:100%;height:100%;"></iframe>
            </div>
        </div>
    `;
    document.body.appendChild(modal);
}

// ===== HELPERS =====
function showLoading(show) {
    document.getElementById('loading').classList.toggle('active', show);
}

function getFileIcon(name) {
    const ext = name.split('.').pop().toLowerCase();
    const icons = {
        pdf: '📕', doc: '📄', docx: '📄', xls: '📊', xlsx: '📊',
        jpg: '🖼️', jpeg: '🖼️', png: '🖼️', gif: '🖼️',
        zip: '📦', rar: '📦', mp3: '🎵', mp4: '🎬', txt: '📝'
    };
    return icons[ext] || '📄';
}

function formatSize(bytes) {
    if (!bytes) return '';
    const k = 1024, sizes = ['B', 'KB', 'MB', 'GB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return parseFloat((bytes / Math.pow(k, i)).toFixed(1)) + ' ' + sizes[i];
}

// ===== PWA SERVICE WORKER =====
if ('serviceWorker' in navigator) {
    navigator.serviceWorker.register('/sw.js')
        .then(reg => console.log('SW registered'))
        .catch(err => console.log('SW error:', err));
}

// ===== AI CHAT =====
const AI_API_URL = '/api/ai/chat';  // Прокси через VPS
let isRecording = false;
let recognition = null;
let aiChatHistory = [];

function openAiChat() {
    showView('aiChatView');
    checkAiStatus();
}

function showView(viewId) {
    document.querySelectorAll('.content-view').forEach(v => v.classList.remove('active'));
    document.getElementById(viewId).classList.add('active');
}

function closeView() {
    showView('emptyView');
}

// Voice input - Telegram style (hold to record, slide up to lock)
let voiceStartY = 0;
let voiceLocked = false;

function startVoiceRecord(event) {
    event.preventDefault();
    
    if (!('webkitSpeechRecognition' in window) && !('SpeechRecognition' in window)) {
        alert('Голосовой ввод не поддерживается в этом браузере');
        return;
    }
    
    // Remember start position for slide detection
    voiceStartY = event.touches ? event.touches[0].clientY : event.clientY;
    voiceLocked = false;
    
    const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
    recognition = new SpeechRecognition();
    recognition.lang = 'ru-RU';
    recognition.continuous = true;
    recognition.interimResults = true;

    recognition.onstart = () => {
        isRecording = true;
        document.getElementById('voiceContainer').classList.add('recording');
        document.getElementById('voiceBtn').classList.add('recording');
        document.getElementById('voiceIcon').textContent = '🔴';
    };

    recognition.onresult = (event) => {
        const transcript = Array.from(event.results)
            .map(r => r[0].transcript)
            .join('');
        document.getElementById('aiTextInput').value = transcript;
    };

    recognition.onerror = (event) => {
        console.error('Speech recognition error:', event.error);
        resetVoiceState();
    };

    recognition.onend = () => {
        // Only auto-reset if not locked
        if (!voiceLocked && isRecording) {
            const input = document.getElementById('aiTextInput');
            if (input.value.trim()) {
                sendAiMessage();
            }
            resetVoiceState();
        }
    };

    recognition.start();
}

function handleVoiceMove(event) {
    if (!isRecording) return;
    
    const currentY = event.touches ? event.touches[0].clientY : event.clientY;
    const deltaY = voiceStartY - currentY;
    
    // If slid up more than 50px - lock recording
    if (deltaY > 50 && !voiceLocked) {
        voiceLocked = true;
        document.getElementById('voiceContainer').classList.add('locked');
        document.getElementById('voiceContainer').classList.remove('recording');
    }
}

function endVoiceRecord(event) {
    event.preventDefault();
    
    if (!isRecording) return;
    
    // If locked, don't stop - wait for explicit send/cancel
    if (voiceLocked) return;
    
    // Stop recognition - onend will handle sending
    if (recognition) {
        recognition.stop();
    }
}

function sendVoiceMessage() {
    if (recognition) {
        recognition.stop();
    }
    const input = document.getElementById('aiTextInput');
    if (input.value.trim()) {
        sendAiMessage();
    }
    resetVoiceState();
}

function cancelVoiceRecord() {
    if (recognition) {
        recognition.stop();
    }
    document.getElementById('aiTextInput').value = '';
    resetVoiceState();
}

function resetVoiceState() {
    isRecording = false;
    voiceLocked = false;
    document.getElementById('voiceContainer').classList.remove('recording', 'locked');
    document.getElementById('voiceBtn').classList.remove('recording');
    document.getElementById('voiceIcon').textContent = '🎤';
}

function stopRecording() {
    if (recognition) {
        recognition.stop();
    }
}

function handleAiInputKeypress(event) {
    if (event.key === 'Enter') {
        sendAiMessage();
    }
}

async function sendAiMessage() {
    const input = document.getElementById('aiTextInput');
    const message = input.value.trim();
    if (!message) return;

    // Add user message to chat
    addChatMessage(message, 'user');
    input.value = '';

    // Add to history
    aiChatHistory.push({ role: 'user', content: message });

    // Show thinking
    const thinkingId = addChatMessage('�����...', 'assistant thinking');

    try {
        const response = await fetch(AI_API_URL, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                model: 'anthropic/claude-opus-4-5',
                messages: aiChatHistory
            })
        });

        const data = await response.json();
        
        // Remove thinking message
        document.getElementById(thinkingId)?.remove();

        if (data.choices && data.choices[0]) {
            const reply = data.choices[0].message.content;
            addChatMessage(reply, 'assistant');
            aiChatHistory.push({ role: 'assistant', content: reply });
            
            // Speak the response
            speakText(reply);
        } else if (data.error) {
            addChatMessage('������: ' + data.error.message, 'assistant');
        }
    } catch (error) {
        document.getElementById(thinkingId)?.remove();
        addChatMessage('������ �����: ' + error.message, 'assistant');
    }
}

function addChatMessage(text, type) {
    const container = document.getElementById('aiChatMessages');
    const msgId = 'msg-' + Date.now();
    const div = document.createElement('div');
    div.id = msgId;
    div.className = 'ai-message ' + type;
    div.innerHTML = '<div class="message-content">' + escapeHtml(text) + '</div>';
    container.appendChild(div);
    container.scrollTop = container.scrollHeight;
    return msgId;
}

function escapeHtml(text) {
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}

// Text-to-speech
function speakText(text) {
    if (!('speechSynthesis' in window)) return;
    
    const utterance = new SpeechSynthesisUtterance(text);
    utterance.lang = 'ru-RU';
    utterance.rate = 1.0;
    speechSynthesis.speak(utterance);
}

// Check AI status
async function checkAiStatus() {
    try {
        const response = await fetch(AI_API_URL.replace('/v1/chat/completions', '/'), {
            method: 'GET',
            mode: 'no-cors'
        });
        document.getElementById('aiStatusIndicator').textContent = '??';
    } catch {
        document.getElementById('aiStatusIndicator').textContent = '??';
    }
}
