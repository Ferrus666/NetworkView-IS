/**
 * NetworkView IS - Основной файл приложения
 * Управляет всеми компонентами системы
 */

class NetworkViewIS {
    constructor() {
        this.socket = null;
        this.documents = [];
        this.diagrams = [];
        this.devices = [];
        this.logs = [];
        this.currentDiagram = null;
        this.settings = this.loadSettings();
        
        this.init();
    }

    /**
     * Инициализация приложения
     */
    init() {
        this.initSocket();
        this.initEventListeners();
        this.loadInitialData();
        this.startMonitoring();
        this.showNotification('success', 'NetworkView IS запущен', 'Система успешно инициализирована');
    }

    /**
     * Инициализация WebSocket соединения
     */
    initSocket() {
        this.socket = io('http://localhost:3000');
        
        this.socket.on('connect', () => {
            console.log('Подключение к серверу установлено');
            this.updateConnectionStatus(true);
        });

        this.socket.on('disconnect', () => {
            console.log('Соединение с сервером разорвано');
            this.updateConnectionStatus(false);
        });

        this.socket.on('device_status_update', (devices) => {
            this.updateDeviceStatuses(devices);
        });

        this.socket.on('new_log', (logEntry) => {
            this.addLogEntry(logEntry);
        });

        this.socket.on('diagram_updated', (diagramData) => {
            this.updateDiagram(diagramData);
        });
    }

    /**
     * Инициализация обработчиков событий
     */
    initEventListeners() {
        // Модальные окна
        document.getElementById('closeModalBtn').addEventListener('click', () => {
            this.closeModal('documentModal');
        });

        document.getElementById('closeElementModalBtn').addEventListener('click', () => {
            this.closeModal('elementModal');
        });

        // Настройки
        document.getElementById('settingsBtn').addEventListener('click', () => {
            this.showSettings();
        });

        // Drag and drop для всех виджетов
        this.initDragAndDrop();
        
        // Клавиатурные сочетания
        document.addEventListener('keydown', (e) => {
            if (e.ctrlKey && e.key === 's') {
                e.preventDefault();
                this.saveSettings();
            }
            if (e.key === 'Escape') {
                this.closeAllModals();
            }
        });

        // Адаптивность - изменение размера окна
        window.addEventListener('resize', () => {
            this.handleResize();
        });
    }

    /**
     * Загрузка начальных данных
     */
    async loadInitialData() {
        try {
            // Загрузка документов
            const documentsResponse = await fetch('/api/documents');
            this.documents = await documentsResponse.json();
            this.renderDocuments();

            // Загрузка диаграмм
            const diagramsResponse = await fetch('/api/diagrams');
            this.diagrams = await diagramsResponse.json();
            this.populateDiagramList();

            // Загрузка устройств
            const devicesResponse = await fetch('/api/devices');
            this.devices = await devicesResponse.json();
            this.renderDevices();

            // Загрузка логов
            const logsResponse = await fetch('/api/logs');
            this.logs = await logsResponse.json();
            this.renderLogs();

        } catch (error) {
            console.error('Ошибка при загрузке данных:', error);
            this.showNotification('error', 'Ошибка загрузки', 'Не удалось загрузить начальные данные');
        }
    }

    /**
     * Запуск мониторинга
     */
    startMonitoring() {
        // Обновление статуса устройств каждые 30 секунд
        setInterval(() => {
            this.updateDeviceStatuses();
        }, 30000);

        // Обновление времени каждую секунду
        setInterval(() => {
            this.updateClock();
        }, 1000);
    }

    /**
     * Инициализация Drag and Drop
     */
    initDragAndDrop() {
        const dropZones = [
            { element: document.getElementById('documentsWidget'), handler: this.handleDocumentDrop.bind(this) },
            { element: document.getElementById('diagramWidget'), handler: this.handleDiagramDrop.bind(this) }
        ];

        dropZones.forEach(zone => {
            zone.element.addEventListener('dragover', (e) => {
                e.preventDefault();
                zone.element.classList.add('drag-over');
            });

            zone.element.addEventListener('dragleave', (e) => {
                if (!zone.element.contains(e.relatedTarget)) {
                    zone.element.classList.remove('drag-over');
                }
            });

            zone.element.addEventListener('drop', (e) => {
                e.preventDefault();
                zone.element.classList.remove('drag-over');
                zone.handler(e.dataTransfer.files);
            });
        });
    }

    /**
     * Обработка загрузки документов
     */
    async handleDocumentDrop(files) {
        for (const file of files) {
            if (this.isValidDocumentFile(file)) {
                await this.uploadDocument(file);
            } else {
                this.showNotification('warning', 'Неподдерживаемый файл', `Файл ${file.name} не поддерживается`);
            }
        }
    }

    /**
     * Обработка загрузки диаграмм
     */
    async handleDiagramDrop(files) {
        for (const file of files) {
            if (file.name.endsWith('.drawio') || file.name.endsWith('.xml')) {
                await this.uploadDiagram(file);
            } else {
                this.showNotification('warning', 'Неподдерживаемый файл', `Файл ${file.name} должен быть .drawio или .xml`);
            }
        }
    }

    /**
     * Проверка типа документа
     */
    isValidDocumentFile(file) {
        const validTypes = ['application/pdf', 'application/vnd.openxmlformats-officedocument.wordprocessingml.document', 'text/plain'];
        const validExtensions = ['.pdf', '.docx', '.txt'];
        return validTypes.includes(file.type) || validExtensions.some(ext => file.name.toLowerCase().endsWith(ext));
    }

    /**
     * Загрузка документа
     */
    async uploadDocument(file) {
        const formData = new FormData();
        formData.append('document', file);

        try {
            const response = await fetch('/api/documents/upload', {
                method: 'POST',
                body: formData
            });

            if (response.ok) {
                const result = await response.json();
                this.documents.push(result);
                this.renderDocuments();
                this.showNotification('success', 'Документ загружен', `Файл ${file.name} успешно загружен`);
            } else {
                throw new Error('Ошибка загрузки документа');
            }
        } catch (error) {
            console.error('Ошибка загрузки документа:', error);
            this.showNotification('error', 'Ошибка загрузки', `Не удалось загрузить файл ${file.name}`);
        }
    }

    /**
     * Загрузка диаграммы
     */
    async uploadDiagram(file) {
        const formData = new FormData();
        formData.append('diagram', file);

        try {
            const response = await fetch('/api/diagrams/upload', {
                method: 'POST',
                body: formData
            });

            if (response.ok) {
                const result = await response.json();
                this.diagrams.push(result);
                this.populateDiagramList();
                this.showNotification('success', 'Диаграмма загружена', `Файл ${file.name} успешно обработан`);
            } else {
                throw new Error('Ошибка загрузки диаграммы');
            }
        } catch (error) {
            console.error('Ошибка загрузки диаграммы:', error);
            this.showNotification('error', 'Ошибка загрузки', `Не удалось загрузить файл ${file.name}`);
        }
    }

    /**
     * Обновление статуса подключения
     */
    updateConnectionStatus(connected) {
        const statusElement = document.querySelector('.bg-green-400');
        const statusText = statusElement.nextElementSibling;
        
        if (connected) {
            statusElement.className = 'w-3 h-3 bg-green-400 rounded-full animate-pulse';
            statusText.textContent = 'Онлайн';
        } else {
            statusElement.className = 'w-3 h-3 bg-red-400 rounded-full';
            statusText.textContent = 'Офлайн';
        }
    }

    /**
     * Обновление статусов устройств
     */
    updateDeviceStatuses(devices = null) {
        if (devices) {
            this.devices = devices;
        }
        this.renderDevices();
    }

    /**
     * Добавление записи в лог
     */
    addLogEntry(logEntry) {
        this.logs.unshift(logEntry);
        if (this.logs.length > 1000) {
            this.logs = this.logs.slice(0, 1000);
        }
        this.renderLogs();
    }

    /**
     * Обновление диаграммы
     */
    updateDiagram(diagramData) {
        // Обновление диаграммы в реальном времени
        if (window.diagramManager && this.currentDiagram && this.currentDiagram.id === diagramData.id) {
            window.diagramManager.updateDiagram(diagramData);
        }
    }

    /**
     * Обновление часов
     */
    updateClock() {
        const now = new Date();
        const timeString = now.toLocaleTimeString('ru-RU');
        const statusBar = document.querySelector('.status-bar');
        if (statusBar) {
            const timeElement = statusBar.querySelector('.time');
            if (timeElement) {
                timeElement.textContent = timeString;
            }
        }
    }

    /**
     * Обработка изменения размера окна
     */
    handleResize() {
        // Адаптация диаграммы под новый размер
        if (window.diagramManager && this.currentDiagram) {
            window.diagramManager.resize();
        }
    }

    /**
     * Показ уведомления
     */
    showNotification(type, title, message) {
        const notification = document.createElement('div');
        notification.className = `notification ${type}`;
        notification.innerHTML = `
            <div class="flex items-start">
                <div class="flex-shrink-0 pt-0.5">
                    <i class="fas ${this.getNotificationIcon(type)} text-lg"></i>
                </div>
                <div class="ml-3 flex-1">
                    <h4 class="text-sm font-medium text-gray-900">${title}</h4>
                    <p class="mt-1 text-sm text-gray-600">${message}</p>
                </div>
                <button class="ml-4 inline-flex text-gray-400 hover:text-gray-600" onclick="this.parentElement.parentElement.remove()">
                    <i class="fas fa-times"></i>
                </button>
            </div>
        `;

        document.body.appendChild(notification);

        // Автоматическое удаление через 5 секунд
        setTimeout(() => {
            if (notification.parentElement) {
                notification.remove();
            }
        }, 5000);
    }

    /**
     * Получение иконки для уведомления
     */
    getNotificationIcon(type) {
        const icons = {
            success: 'fa-check-circle',
            warning: 'fa-exclamation-triangle',
            error: 'fa-times-circle',
            info: 'fa-info-circle'
        };
        return icons[type] || icons.info;
    }

    /**
     * Закрытие модального окна
     */
    closeModal(modalId) {
        const modal = document.getElementById(modalId);
        if (modal) {
            modal.classList.add('hidden');
        }
    }

    /**
     * Закрытие всех модальных окон
     */
    closeAllModals() {
        const modals = document.querySelectorAll('[id$="Modal"]');
        modals.forEach(modal => {
            modal.classList.add('hidden');
        });
    }

    /**
     * Показ настроек
     */
    showSettings() {
        // Реализация настроек системы
        this.showNotification('info', 'Настройки', 'Функция настроек будет добавлена в следующих версиях');
    }

    /**
     * Загрузка настроек
     */
    loadSettings() {
        const saved = localStorage.getItem('networkview-settings');
        return saved ? JSON.parse(saved) : {
            theme: 'light',
            autoUpdate: true,
            notifications: true,
            language: 'ru'
        };
    }

    /**
     * Сохранение настроек
     */
    saveSettings() {
        localStorage.setItem('networkview-settings', JSON.stringify(this.settings));
        this.showNotification('success', 'Настройки сохранены', 'Конфигурация успешно сохранена');
    }

    /**
     * Рендеринг документов (переопределяется в documents.js)
     */
    renderDocuments() {
        // Базовая реализация
        console.log('Рендеринг документов:', this.documents.length);
    }

    /**
     * Заполнение списка диаграмм
     */
    populateDiagramList() {
        const select = document.getElementById('diagramList');
        select.innerHTML = '<option value="">Выберите схему...</option>';
        
        this.diagrams.forEach(diagram => {
            const option = document.createElement('option');
            option.value = diagram.id;
            option.textContent = diagram.name;
            select.appendChild(option);
        });
    }

    /**
     * Рендеринг устройств (переопределяется в monitoring.js)
     */
    renderDevices() {
        console.log('Рендеринг устройств:', this.devices.length);
    }

    /**
     * Рендеринг логов
     */
    renderLogs() {
        const logsList = document.getElementById('logsList');
        logsList.innerHTML = '';

        this.logs.slice(0, 100).forEach(log => {
            const logElement = document.createElement('div');
            logElement.className = `log-entry ${log.level.toLowerCase()}`;
            logElement.innerHTML = `
                <span class="log-timestamp">${new Date(log.timestamp).toLocaleString('ru-RU')}</span>
                <span class="log-level ${log.level.toLowerCase()}">${log.level}</span>
                <span class="log-message">${log.message}</span>
            `;
            logsList.appendChild(logElement);
        });
    }

    /**
     * Экспорт данных
     */
    async exportData(type) {
        try {
            const response = await fetch(`/api/export/${type}`);
            const blob = await response.blob();
            const url = window.URL.createObjectURL(blob);
            const a = document.createElement('a');
            a.href = url;
            a.download = `networkview_${type}_${new Date().toISOString().split('T')[0]}.json`;
            a.click();
            window.URL.revokeObjectURL(url);
            
            this.showNotification('success', 'Экспорт завершен', `Данные ${type} успешно экспортированы`);
        } catch (error) {
            console.error('Ошибка экспорта:', error);
            this.showNotification('error', 'Ошибка экспорта', 'Не удалось экспортировать данные');
        }
    }
}

// Инициализация приложения при загрузке страницы
document.addEventListener('DOMContentLoaded', () => {
    window.app = new NetworkViewIS();
    
    // Добавление статусбара
    const statusBar = document.createElement('div');
    statusBar.className = 'status-bar';
    statusBar.innerHTML = `
        <div class="flex items-center space-x-4">
            <span>NetworkView IS v1.0.0</span>
            <span>Устройств: <span id="deviceCount">0</span></span>
            <span>Документов: <span id="documentCount">0</span></span>
        </div>
        <div class="flex items-center space-x-4">
            <span class="time">${new Date().toLocaleTimeString('ru-RU')}</span>
            <span>Статус: <span id="systemStatus">Инициализация...</span></span>
        </div>
    `;
    document.body.appendChild(statusBar);
}); 