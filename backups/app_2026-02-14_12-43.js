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
    
    if (window.Telegram?.WebApp) {
        Telegram.WebApp.ready();
        Telegram.WebApp.expand();
    }
});

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

function escapeHtml(text) {
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}

// Skills catalog
const skillsCatalog = {
    '📋 Документы': [
        { id: 'new-contract', name: 'Новый договор', emoji: '📝', triggers: 'новый договор, подготовь договор' },
        { id: 'contracts-brandonline', name: 'Система договоров', emoji: '📑', triggers: 'договор РТЗ, договор на лого, КП' },
    ],
    '💼 CRM': [
        { id: 'bitrix-assistant', name: 'Битрикс CRM', emoji: '🔶', triggers: 'битрикс, дела, компании' },
        { id: 'mcrm', name: 'MCRM (новая)', emoji: '📊', triggers: 'MCRM, миграция' },
    ],
    '💬 Мессенджеры': [
        { id: 'messenger-telegram', name: 'Телеграм', emoji: '✈️', triggers: 'напиши в телеграм' },
        { id: 'messenger-whatsapp', name: 'WhatsApp', emoji: '💚', triggers: 'напиши в whatsapp' },
        { id: 'messenger-max', name: 'MAX (VK)', emoji: '💙', triggers: 'напиши в max' },
    ],
    '🏛️ Роспатент': [
        { id: 'fips-expertise', name: 'Экспертиза ФИПС', emoji: '📋', triggers: 'ответ на уведомление, основание отказа' },
        { id: 'fips-monitor', name: 'Мониторинг заявок', emoji: '👁️', triggers: 'проверить заявку, статус' },
    ],
    '🔧 Автоматизация': [
        { id: 'desktop-control', name: 'Управление ПК', emoji: '🖥️', triggers: 'кликни, нажми, введи' },
        { id: 'macro-recorder', name: 'Запись макросов', emoji: '⏺️', triggers: 'запиши макрос' },
        { id: 'windows-apps', name: 'Приложения Windows', emoji: '🪟', triggers: 'создай программу' },
    ],
    '🔍 Исследование': [
        { id: 'site-research', name: 'Изучение сайта', emoji: '🌐', triggers: 'изучи сайт' },
        { id: 'service-onboarding', name: 'Онбординг сервиса', emoji: '🎓', triggers: 'изучи сервис, разберись' },
    ],
    '⚙️ Система': [
        { id: 'system-architecture', name: 'Архитектура правил', emoji: '🏗️', triggers: 'зафиксируй, запомни' },
        { id: 'skill-creator', name: 'Создание скиллов', emoji: '✨', triggers: 'создай скилл' },
        { id: 'self-improvement', name: 'Самоулучшение', emoji: '📈', triggers: 'после ошибки, рефлексия' },
        { id: 'execution-discipline', name: 'Дисциплина выполнения', emoji: '✅', triggers: 'сложная задача' },
        { id: 'context-save', name: 'Сохранение контекста', emoji: '💾', triggers: 'сохранить контекст' },
        { id: 'workspace-structure', name: 'Структура папок', emoji: '📁', triggers: 'найди файл, где лежит' },
    ],
    '🖥️ Инфраструктура': [
        { id: 'firstvds', name: 'VPS сервер', emoji: '🖧', triggers: 'деплой на VPS, FirstVDS' },
        { id: 'fantasy-dashboard', name: 'Fantasy Dashboard', emoji: '🎮', triggers: 'fantasy, фэнтези' },
    ],
};

let allSkills = [];

async function loadSkills() {
    const container = document.getElementById('skillsCategories');
    container.innerHTML = '';
    allSkills = [];

    Object.entries(skillsCatalog).forEach(([category, skills]) => {
        skills.forEach(skill => {
            allSkills.push({ ...skill, category });
        });
    });

    Object.entries(skillsCatalog).forEach(([category, skills]) => {
        const categoryDiv = document.createElement('div');
        categoryDiv.className = 'skill-category';
        categoryDiv.innerHTML = `
            <div class="skill-category-header" onclick="toggleCategory(this)">
                <span class="skill-category-icon">${category.split(' ')[0]}</span>
                <span>${category.split(' ').slice(1).join(' ')}</span>
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
