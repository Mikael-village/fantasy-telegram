/**
 * Fantasy Dashboard Analytics
 * Собирает статистику использования функций
 */

const FDAnalytics = {
    storageKey: 'fd_analytics',
    
    // Инициализация
    init() {
        this.data = this.load();
        this.trackSession();
        console.log('[Analytics] Initialized');
    },
    
    // Загрузка данных из localStorage
    load() {
        try {
            const stored = localStorage.getItem(this.storageKey);
            if (stored) {
                return JSON.parse(stored);
            }
        } catch (e) {
            console.error('[Analytics] Load error:', e);
        }
        return this.getEmptyData();
    },
    
    // Пустая структура данных
    getEmptyData() {
        return {
            version: 1,
            firstUse: new Date().toISOString(),
            lastUse: null,
            sessions: 0,
            totalTime: 0, // секунды
            features: {
                // Нижняя панель
                'btn_archive': { name: 'Архив', clicks: 0, lastUsed: null },
                'btn_downloads': { name: 'Загрузки', clicks: 0, lastUsed: null },
                'btn_ai_chat': { name: 'Чат AI', clicks: 0, lastUsed: null },
                'btn_assistant': { name: 'Помощник', clicks: 0, lastUsed: null },
                'btn_mcrm': { name: 'MCRM', clicks: 0, lastUsed: null },
                
                // Правая панель
                'btn_telegram': { name: 'Telegram', clicks: 0, lastUsed: null },
                'btn_max': { name: 'MAX', clicks: 0, lastUsed: null },
                'btn_wcp': { name: 'WCP', clicks: 0, lastUsed: null },
                'btn_mail': { name: 'Почта', clicks: 0, lastUsed: null },
                
                // AI функции
                'ai_voice_message': { name: 'Голосовое сообщение', clicks: 0, lastUsed: null },
                'ai_text_message': { name: 'Текстовое сообщение', clicks: 0, lastUsed: null },
                
                // Файлы
                'file_open': { name: 'Открытие файла', clicks: 0, lastUsed: null },
                'folder_navigate': { name: 'Навигация по папкам', clicks: 0, lastUsed: null },
                'tab_downloads': { name: 'Вкладка Загрузки', clicks: 0, lastUsed: null },
                'tab_clients': { name: 'Вкладка Клиенты', clicks: 0, lastUsed: null }
            },
            daily: {} // { 'YYYY-MM-DD': { sessions: N, features: {...} } }
        };
    },
    
    // Сохранение данных
    save() {
        try {
            localStorage.setItem(this.storageKey, JSON.stringify(this.data));
        } catch (e) {
            console.error('[Analytics] Save error:', e);
        }
    },
    
    // Отслеживание сессии
    trackSession() {
        this.data.sessions++;
        this.data.lastUse = new Date().toISOString();
        this.sessionStart = Date.now();
        
        // Ежедневная статистика
        const today = new Date().toISOString().split('T')[0];
        if (!this.data.daily[today]) {
            this.data.daily[today] = { sessions: 0, features: {} };
        }
        this.data.daily[today].sessions++;
        
        this.save();
        
        // Отслеживать время при закрытии
        window.addEventListener('beforeunload', () => {
            const duration = Math.round((Date.now() - this.sessionStart) / 1000);
            this.data.totalTime += duration;
            this.save();
        });
    },
    
    // Трекинг клика по функции
    track(featureId) {
        const now = new Date().toISOString();
        const today = now.split('T')[0];
        
        // Общая статистика
        if (this.data.features[featureId]) {
            this.data.features[featureId].clicks++;
            this.data.features[featureId].lastUsed = now;
        } else {
            // Новая функция
            this.data.features[featureId] = {
                name: featureId,
                clicks: 1,
                lastUsed: now
            };
        }
        
        // Дневная статистика
        if (!this.data.daily[today]) {
            this.data.daily[today] = { sessions: 0, features: {} };
        }
        if (!this.data.daily[today].features[featureId]) {
            this.data.daily[today].features[featureId] = 0;
        }
        this.data.daily[today].features[featureId]++;
        
        this.save();
        console.log(`[Analytics] Tracked: ${featureId}`);
    },
    
    // Получить отчёт
    getReport() {
        const features = Object.entries(this.data.features)
            .map(([id, data]) => ({ id, ...data }))
            .sort((a, b) => b.clicks - a.clicks);
        
        const used = features.filter(f => f.clicks > 0);
        const unused = features.filter(f => f.clicks === 0);
        
        // Топ за последние 7 дней
        const last7days = [];
        for (let i = 0; i < 7; i++) {
            const date = new Date();
            date.setDate(date.getDate() - i);
            last7days.push(date.toISOString().split('T')[0]);
        }
        
        const weeklyStats = {};
        last7days.forEach(day => {
            if (this.data.daily[day]) {
                Object.entries(this.data.daily[day].features || {}).forEach(([id, count]) => {
                    weeklyStats[id] = (weeklyStats[id] || 0) + count;
                });
            }
        });
        
        const weeklyTop = Object.entries(weeklyStats)
            .map(([id, clicks]) => ({ 
                id, 
                name: this.data.features[id]?.name || id,
                clicks 
            }))
            .sort((a, b) => b.clicks - a.clicks);
        
        return {
            summary: {
                firstUse: this.data.firstUse,
                lastUse: this.data.lastUse,
                totalSessions: this.data.sessions,
                totalTimeMinutes: Math.round(this.data.totalTime / 60),
                totalFeatures: features.length,
                usedFeatures: used.length,
                unusedFeatures: unused.length
            },
            topAll: used.slice(0, 10),
            topWeek: weeklyTop.slice(0, 10),
            unused: unused.map(f => f.name),
            raw: this.data
        };
    },
    
    // Сброс статистики
    reset() {
        this.data = this.getEmptyData();
        this.save();
        console.log('[Analytics] Reset complete');
    }
};

// Инициализация при загрузке
document.addEventListener('DOMContentLoaded', () => {
    FDAnalytics.init();
});

// Экспорт для использования в HTML
window.FDAnalytics = FDAnalytics;
