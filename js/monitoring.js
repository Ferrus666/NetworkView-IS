/**
 * NetworkView IS - Модуль мониторинга сети
 * Отслеживание состояния устройств и событий безопасности
 */

class MonitoringManager {
    constructor(app) {
        this.app = app;
        this.isMonitoring = false;
        this.monitoringInterval = null;
        this.lastUpdateTime = null;
        this.deviceStats = {
            total: 0,
            online: 0,
            offline: 0,
            warning: 0
        };
        
        this.init();
    }

    /**
     * Инициализация модуля мониторинга
     */
    init() {
        this.initEventListeners();
        this.loadSampleDevices();
        this.loadSampleLogs();
        this.startMonitoring();
    }

    /**
     * Инициализация обработчиков событий
     */
    initEventListeners() {
        // Очистка логов
        document.getElementById('clearLogsBtn').addEventListener('click', () => {
            this.clearLogs();
        });

        // Экспорт логов
        document.getElementById('exportLogsBtn').addEventListener('click', () => {
            this.exportLogs();
        });

        // Фильтры логов
        document.getElementById('logLevelFilter').addEventListener('change', (e) => {
            this.filterLogs();
        });

        document.getElementById('logDateFilter').addEventListener('change', (e) => {
            this.filterLogs();
        });
    }

    /**
     * Загрузка примеров устройств
     */
    loadSampleDevices() {
        const sampleDevices = [
            {
                id: 'dev_001',
                name: 'Главный маршрутизатор',
                type: 'router',
                ip: '192.168.1.1',
                mac: '00:1A:2B:3C:4D:5E',
                status: 'online',
                lastSeen: new Date(),
                location: 'Серверная комната',
                manufacturer: 'Cisco',
                model: 'ISR 4321',
                uptime: '45 дней 12 ч 34 мин',
                metrics: {
                    cpu: 23,
                    memory: 45,
                    temperature: 42,
                    loadAverage: 0.8
                },
                ports: [
                    { number: 1, status: 'up', speed: '1Gbps' },
                    { number: 2, status: 'up', speed: '1Gbps' },
                    { number: 3, status: 'down', speed: '1Gbps' },
                    { number: 4, status: 'up', speed: '1Gbps' }
                ]
            },
            {
                id: 'dev_002',
                name: 'Коммутатор Level 2',
                type: 'switch',
                ip: '192.168.1.10',
                mac: '00:1A:2B:3C:4D:5F',
                status: 'online',
                lastSeen: new Date(Date.now() - 2000),
                location: 'Серверная комната',
                manufacturer: 'Cisco',
                model: 'Catalyst 2960',
                uptime: '32 дня 8 ч 15 мин',
                metrics: {
                    cpu: 12,
                    memory: 28,
                    temperature: 38,
                    loadAverage: 0.3
                },
                vlans: ['VLAN 10', 'VLAN 20', 'VLAN 30']
            },
            {
                id: 'dev_003',
                name: 'Файловый сервер',
                type: 'server',
                ip: '192.168.1.100',
                mac: '00:1A:2B:3C:4D:60',
                status: 'online',
                lastSeen: new Date(Date.now() - 5000),
                location: 'Серверная комната',
                manufacturer: 'Dell',
                model: 'PowerEdge R750',
                uptime: '120 дней 5 ч 22 мин',
                metrics: {
                    cpu: 65,
                    memory: 78,
                    temperature: 52,
                    diskUsage: 45
                },
                services: ['SMB', 'FTP', 'SSH']
            },
            {
                id: 'dev_004',
                name: 'Рабочая станция ИТ-01',
                type: 'workstation',
                ip: '192.168.1.201',
                mac: '00:1A:2B:3C:4D:61',
                status: 'online',
                lastSeen: new Date(Date.now() - 30000),
                location: 'Офис 101',
                manufacturer: 'HP',
                model: 'EliteDesk 800',
                uptime: '2 дня 14 ч 45 мин',
                metrics: {
                    cpu: 45,
                    memory: 68,
                    temperature: 45
                },
                user: 'Иванов И.И.',
                department: 'ИТ отдел'
            },
            {
                id: 'dev_005',
                name: 'Принтер HP LaserJet',
                type: 'printer',
                ip: '192.168.1.150',
                mac: '00:1A:2B:3C:4D:62',
                status: 'warning',
                lastSeen: new Date(Date.now() - 120000),
                location: 'Офис 102',
                manufacturer: 'HP',
                model: 'LaserJet Pro 400',
                uptime: '15 дней 3 ч 12 мин',
                metrics: {
                    tonerLevel: 15,
                    paperLevel: 80,
                    totalPages: 45632
                },
                issues: ['Низкий уровень тонера']
            },
            {
                id: 'dev_006',
                name: 'Камера видеонаблюдения #1',
                type: 'camera',
                ip: '192.168.1.180',
                mac: '00:1A:2B:3C:4D:63',
                status: 'offline',
                lastSeen: new Date(Date.now() - 300000),
                location: 'Вход в здание',
                manufacturer: 'Hikvision',
                model: 'DS-2CD2043G0-I',
                uptime: '0 дней 0 ч 0 мин',
                metrics: {
                    resolution: '4MP',
                    nightVision: true,
                    recording: false
                },
                issues: ['Нет связи с устройством']
            }
        ];

        this.app.devices = sampleDevices;
        this.updateDeviceStats();
        this.renderDevices();
    }

    /**
     * Загрузка примеров логов
     */
    loadSampleLogs() {
        const sampleLogs = [
            {
                id: 1,
                timestamp: new Date(),
                level: 'INFO',
                source: 'System',
                message: 'Система мониторинга NetworkView IS запущена',
                details: { module: 'monitoring', version: '1.0.0' }
            },
            {
                id: 2,
                timestamp: new Date(Date.now() - 60000),
                level: 'INFO',
                source: 'Router',
                message: 'Маршрутизатор 192.168.1.1 подключен к сети',
                details: { device: 'dev_001', status: 'online' }
            },
            {
                id: 3,
                timestamp: new Date(Date.now() - 120000),
                level: 'WARNING',
                source: 'Printer',
                message: 'Низкий уровень тонера в принтере HP LaserJet (192.168.1.150)',
                details: { device: 'dev_005', tonerLevel: 15 }
            },
            {
                id: 4,
                timestamp: new Date(Date.now() - 180000),
                level: 'ERROR',
                source: 'Camera',
                message: 'Потеря связи с камерой видеонаблюдения #1 (192.168.1.180)',
                details: { device: 'dev_006', lastSeen: new Date(Date.now() - 300000) }
            },
            {
                id: 5,
                timestamp: new Date(Date.now() - 240000),
                level: 'INFO',
                source: 'Server',
                message: 'Файловый сервер выполнил резервное копирование данных',
                details: { device: 'dev_003', backupSize: '2.5 GB' }
            },
            {
                id: 6,
                timestamp: new Date(Date.now() - 300000),
                level: 'WARNING',
                source: 'Server',
                message: 'Высокое использование CPU на файловом сервере (78%)',
                details: { device: 'dev_003', cpuUsage: 78 }
            }
        ];

        this.app.logs = sampleLogs;
        this.filteredLogs = [...this.app.logs];
        this.renderLogs();
    }

    /**
     * Обновление статистики устройств
     */
    updateDeviceStats() {
        this.deviceStats.total = this.app.devices.length;
        this.deviceStats.online = this.app.devices.filter(d => d.status === 'online').length;
        this.deviceStats.offline = this.app.devices.filter(d => d.status === 'offline').length;
        this.deviceStats.warning = this.app.devices.filter(d => d.status === 'warning').length;

        // Обновление UI
        document.getElementById('activeDevices').textContent = this.deviceStats.online;
        document.getElementById('inactiveDevices').textContent = this.deviceStats.offline + this.deviceStats.warning;
        document.getElementById('deviceCount').textContent = this.deviceStats.total;
    }

    /**
     * Рендеринг списка устройств
     */
    renderDevices() {
        const devicesList = document.getElementById('devicesList');
        devicesList.innerHTML = '';

        this.app.devices.forEach(device => {
            const deviceElement = this.createDeviceElement(device);
            devicesList.appendChild(deviceElement);
        });

        this.updateDeviceStats();
    }

    /**
     * Создание элемента устройства
     */
    createDeviceElement(device) {
        const deviceElement = document.createElement('div');
        deviceElement.className = 'device-item';
        
        const statusText = {
            online: 'Активен',
            offline: 'Неактивен',
            warning: 'Предупреждение'
        };

        const lastSeenText = this.formatTimeDifference(device.lastSeen);

        deviceElement.innerHTML = `
            <div class="flex items-center justify-between w-full">
                <div class="flex items-center flex-1">
                    <div class="device-status ${device.status}"></div>
                    <div class="flex-1">
                        <div class="flex items-center justify-between">
                            <h4 class="text-sm font-medium text-gray-900">${device.name}</h4>
                            <span class="text-xs text-gray-500">${device.ip}</span>
                        </div>
                        <div class="flex items-center justify-between text-xs text-gray-600">
                            <span>${device.type} - ${device.manufacturer} ${device.model}</span>
                            <span>Обновлено: ${lastSeenText}</span>
                        </div>
                        ${device.status === 'warning' && device.issues ? 
                            `<div class="text-xs text-orange-600 mt-1">${device.issues.join(', ')}</div>` : 
                            ''
                        }
                        ${device.metrics ? 
                            `<div class="flex space-x-2 mt-1">
                                ${device.metrics.cpu ? `<span class="text-xs text-gray-500">CPU: ${device.metrics.cpu}%</span>` : ''}
                                ${device.metrics.memory ? `<span class="text-xs text-gray-500">RAM: ${device.metrics.memory}%</span>` : ''}
                                ${device.metrics.temperature ? `<span class="text-xs text-gray-500">T: ${device.metrics.temperature}°C</span>` : ''}
                            </div>` : 
                            ''
                        }
                    </div>
                </div>
                <div class="flex space-x-1 ml-2">
                    <button class="p-1 text-blue-500 hover:text-blue-700" 
                            onclick="monitoringManager.showDeviceDetails('${device.id}')"
                            title="Подробности">
                        <i class="fas fa-info-circle text-sm"></i>
                    </button>
                    <button class="p-1 text-green-500 hover:text-green-700" 
                            onclick="monitoringManager.pingDevice('${device.id}')"
                            title="Пинг">
                        <i class="fas fa-satellite-dish text-sm"></i>
                    </button>
                    <button class="p-1 text-orange-500 hover:text-orange-700" 
                            onclick="monitoringManager.showDeviceMetrics('${device.id}')"
                            title="Метрики">
                        <i class="fas fa-chart-bar text-sm"></i>
                    </button>
                </div>
            </div>
        `;

        return deviceElement;
    }

    /**
     * Форматирование разности времени
     */
    formatTimeDifference(date) {
        const now = new Date();
        const diff = now - date;
        const seconds = Math.floor(diff / 1000);
        const minutes = Math.floor(seconds / 60);
        const hours = Math.floor(minutes / 60);
        const days = Math.floor(hours / 24);

        if (days > 0) return `${days}д назад`;
        if (hours > 0) return `${hours}ч назад`;
        if (minutes > 0) return `${minutes}м назад`;
        return `${seconds}с назад`;
    }

    /**
     * Показ подробностей устройства
     */
    showDeviceDetails(deviceId) {
        const device = this.app.devices.find(d => d.id === deviceId);
        if (!device) return;

        const modal = document.getElementById('elementModal');
        const modalTitle = document.getElementById('elementModalTitle');
        const modalContent = document.getElementById('elementModalContent');

        modalTitle.textContent = `Устройство: ${device.name}`;
        modalContent.innerHTML = `
            <div class="space-y-4">
                <div class="grid grid-cols-2 gap-4">
                    <div>
                        <label class="block text-sm font-medium text-gray-700">IP-адрес</label>
                        <div class="mt-1 text-sm text-gray-900">${device.ip}</div>
                    </div>
                    <div>
                        <label class="block text-sm font-medium text-gray-700">MAC-адрес</label>
                        <div class="mt-1 text-sm text-gray-900">${device.mac}</div>
                    </div>
                    <div>
                        <label class="block text-sm font-medium text-gray-700">Тип</label>
                        <div class="mt-1 text-sm text-gray-900">${device.type}</div>
                    </div>
                    <div>
                        <label class="block text-sm font-medium text-gray-700">Статус</label>
                        <div class="mt-1 flex items-center">
                            <div class="device-status ${device.status}"></div>
                            <span class="text-sm text-gray-900 ml-2">${device.status}</span>
                        </div>
                    </div>
                    <div>
                        <label class="block text-sm font-medium text-gray-700">Производитель</label>
                        <div class="mt-1 text-sm text-gray-900">${device.manufacturer}</div>
                    </div>
                    <div>
                        <label class="block text-sm font-medium text-gray-700">Модель</label>
                        <div class="mt-1 text-sm text-gray-900">${device.model}</div>
                    </div>
                    <div>
                        <label class="block text-sm font-medium text-gray-700">Местоположение</label>
                        <div class="mt-1 text-sm text-gray-900">${device.location}</div>
                    </div>
                    <div>
                        <label class="block text-sm font-medium text-gray-700">Время работы</label>
                        <div class="mt-1 text-sm text-gray-900">${device.uptime}</div>
                    </div>
                </div>

                ${device.metrics ? `
                    <div>
                        <label class="block text-sm font-medium text-gray-700 mb-2">Метрики производительности</label>
                        <div class="grid grid-cols-2 gap-2">
                            ${Object.entries(device.metrics).map(([key, value]) => `
                                <div class="bg-gray-50 p-2 rounded">
                                    <div class="text-xs text-gray-600">${key}</div>
                                    <div class="text-sm font-medium">${value}${typeof value === 'number' && key !== 'totalPages' ? (key.includes('temperature') ? '°C' : '%') : ''}</div>
                                </div>
                            `).join('')}
                        </div>
                    </div>
                ` : ''}

                ${device.services ? `
                    <div>
                        <label class="block text-sm font-medium text-gray-700 mb-2">Сервисы</label>
                        <div class="flex flex-wrap gap-1">
                            ${device.services.map(service => `
                                <span class="px-2 py-1 bg-blue-100 text-blue-800 text-xs rounded">${service}</span>
                            `).join('')}
                        </div>
                    </div>
                ` : ''}

                ${device.issues ? `
                    <div>
                        <label class="block text-sm font-medium text-gray-700 mb-2">Проблемы</label>
                        <div class="space-y-1">
                            ${device.issues.map(issue => `
                                <div class="flex items-center text-sm text-red-600">
                                    <i class="fas fa-exclamation-triangle mr-2"></i>
                                    ${issue}
                                </div>
                            `).join('')}
                        </div>
                    </div>
                ` : ''}

                <div class="flex space-x-2 pt-4">
                    <button class="px-4 py-2 bg-blue-500 text-white rounded-md hover:bg-blue-600 transition-colors text-sm"
                            onclick="monitoringManager.pingDevice('${device.id}')">
                        <i class="fas fa-satellite-dish mr-1"></i>Пинг
                    </button>
                    <button class="px-4 py-2 bg-green-500 text-white rounded-md hover:bg-green-600 transition-colors text-sm"
                            onclick="monitoringManager.restartDevice('${device.id}')">
                        <i class="fas fa-redo mr-1"></i>Перезагрузка
                    </button>
                    <button class="px-4 py-2 bg-orange-500 text-white rounded-md hover:bg-orange-600 transition-colors text-sm"
                            onclick="monitoringManager.updateDevice('${device.id}')">
                        <i class="fas fa-sync mr-1"></i>Обновить
                    </button>
                </div>
            </div>
        `;

        modal.classList.remove('hidden');
    }

    /**
     * Пинг устройства
     */
    async pingDevice(deviceId) {
        const device = this.app.devices.find(d => d.id === deviceId);
        if (!device) return;

        this.app.showNotification('info', 'Пинг устройства', `Отправка пинга на ${device.name} (${device.ip})...`);

        // Симуляция пинга
        setTimeout(() => {
            const success = device.status === 'online' ? Math.random() > 0.1 : Math.random() > 0.8;
            const responseTime = Math.floor(Math.random() * 100) + 1;

            if (success) {
                this.app.showNotification('success', 'Пинг успешен', `${device.name} отвечает (${responseTime} мс)`);
                this.addLogEntry('INFO', 'Monitoring', `Пинг ${device.name} (${device.ip}) успешен - ${responseTime} мс`);
            } else {
                this.app.showNotification('error', 'Пинг неудачен', `${device.name} не отвечает`);
                this.addLogEntry('ERROR', 'Monitoring', `Пинг ${device.name} (${device.ip}) неудачен - превышен таймаут`);
            }
        }, 2000 + Math.random() * 3000);
    }

    /**
     * Перезагрузка устройства
     */
    async restartDevice(deviceId) {
        const device = this.app.devices.find(d => d.id === deviceId);
        if (!device) return;

        if (!confirm(`Вы уверены, что хотите перезагрузить ${device.name}?`)) {
            return;
        }

        this.app.showNotification('info', 'Перезагрузка устройства', `Отправка команды перезагрузки на ${device.name}...`);
        this.addLogEntry('WARNING', 'Monitoring', `Инициирована перезагрузка ${device.name} (${device.ip})`);

        // Симуляция перезагрузки
        device.status = 'offline';
        this.renderDevices();

        setTimeout(() => {
            device.status = 'online';
            device.lastSeen = new Date();
            device.uptime = '0 дней 0 ч 1 мин';
            this.renderDevices();
            this.app.showNotification('success', 'Устройство перезагружено', `${device.name} успешно перезагружено`);
            this.addLogEntry('INFO', 'Monitoring', `${device.name} (${device.ip}) успешно перезагружено`);
        }, 10000);
    }

    /**
     * Обновление информации об устройстве
     */
    async updateDevice(deviceId) {
        const device = this.app.devices.find(d => d.id === deviceId);
        if (!device) return;

        this.app.showNotification('info', 'Обновление устройства', `Получение актуальной информации о ${device.name}...`);

        // Симуляция обновления
        setTimeout(() => {
            // Случайное изменение метрик
            if (device.metrics) {
                if (device.metrics.cpu) device.metrics.cpu = Math.floor(Math.random() * 100);
                if (device.metrics.memory) device.metrics.memory = Math.floor(Math.random() * 100);
                if (device.metrics.temperature) device.metrics.temperature = Math.floor(Math.random() * 20) + 30;
            }

            device.lastSeen = new Date();
            this.renderDevices();
            this.app.showNotification('success', 'Устройство обновлено', `Информация о ${device.name} актуализирована`);
            this.addLogEntry('INFO', 'Monitoring', `Обновлена информация о ${device.name} (${device.ip})`);
        }, 2000);
    }

    /**
     * Запуск мониторинга
     */
    startMonitoring() {
        if (this.isMonitoring) return;

        this.isMonitoring = true;
        this.monitoringInterval = setInterval(() => {
            this.performMonitoringCycle();
        }, 30000); // Каждые 30 секунд

        this.app.showNotification('info', 'Мониторинг запущен', 'Автоматический мониторинг устройств активен');
        document.getElementById('systemStatus').textContent = 'Активен';
    }

    /**
     * Остановка мониторинга
     */
    stopMonitoring() {
        if (!this.isMonitoring) return;

        this.isMonitoring = false;
        if (this.monitoringInterval) {
            clearInterval(this.monitoringInterval);
            this.monitoringInterval = null;
        }

        this.app.showNotification('warning', 'Мониторинг остановлен', 'Автоматический мониторинг устройств приостановлен');
        document.getElementById('systemStatus').textContent = 'Приостановлен';
    }

    /**
     * Цикл мониторинга
     */
    performMonitoringCycle() {
        this.lastUpdateTime = new Date();

        // Симуляция изменений в устройствах
        this.app.devices.forEach(device => {
            // Случайные изменения метрик
            if (device.metrics && Math.random() > 0.7) {
                if (device.metrics.cpu) {
                    device.metrics.cpu = Math.max(0, Math.min(100, device.metrics.cpu + (Math.random() - 0.5) * 20));
                }
                if (device.metrics.memory) {
                    device.metrics.memory = Math.max(0, Math.min(100, device.metrics.memory + (Math.random() - 0.5) * 10));
                }
            }

            // Случайные изменения статуса (редко)
            if (Math.random() > 0.95) {
                const statuses = ['online', 'offline', 'warning'];
                const newStatus = statuses[Math.floor(Math.random() * statuses.length)];
                if (newStatus !== device.status) {
                    device.status = newStatus;
                    device.lastSeen = new Date();
                    this.addLogEntry(
                        newStatus === 'offline' ? 'ERROR' : 'WARNING',
                        'Monitoring',
                        `Изменение статуса ${device.name} (${device.ip}): ${newStatus}`
                    );
                }
            }

            // Обновление времени последней активности для онлайн устройств
            if (device.status === 'online') {
                device.lastSeen = new Date();
            }
        });

        this.renderDevices();

        // Генерация случайных событий безопасности
        if (Math.random() > 0.8) {
            this.generateSecurityEvent();
        }
    }

    /**
     * Генерация событий безопасности
     */
    generateSecurityEvent() {
        const events = [
            {
                level: 'WARNING',
                message: 'Обнаружена попытка несанкционированного доступа',
                source: 'Security'
            },
            {
                level: 'INFO',
                message: 'Выполнено плановое обновление антивирусных баз',
                source: 'Security'
            },
            {
                level: 'ERROR',
                message: 'Заблокировано вредоносное соединение',
                source: 'Firewall'
            },
            {
                level: 'INFO',
                message: 'Пользователь выполнил успешную аутентификацию',
                source: 'Authentication'
            }
        ];

        const event = events[Math.floor(Math.random() * events.length)];
        this.addLogEntry(event.level, event.source, event.message);
    }

    /**
     * Добавление записи в лог
     */
    addLogEntry(level, source, message, details = null) {
        const logEntry = {
            id: Date.now() + Math.random(),
            timestamp: new Date(),
            level,
            source,
            message,
            details
        };

        this.app.logs.unshift(logEntry);
        
        // Ограничение размера лога
        if (this.app.logs.length > 1000) {
            this.app.logs = this.app.logs.slice(0, 1000);
        }

        this.filterLogs();
    }

    /**
     * Фильтрация логов
     */
    filterLogs() {
        let filtered = [...this.app.logs];

        const levelFilter = document.getElementById('logLevelFilter').value;
        const dateFilter = document.getElementById('logDateFilter').value;

        if (levelFilter) {
            filtered = filtered.filter(log => log.level === levelFilter);
        }

        if (dateFilter) {
            const filterDate = new Date(dateFilter);
            filtered = filtered.filter(log => {
                const logDate = new Date(log.timestamp);
                return logDate.toDateString() === filterDate.toDateString();
            });
        }

        this.filteredLogs = filtered;
        this.renderLogs();
    }

    /**
     * Рендеринг логов
     */
    renderLogs() {
        const logsList = document.getElementById('logsList');
        logsList.innerHTML = '';

        if (!this.filteredLogs || this.filteredLogs.length === 0) {
            logsList.innerHTML = `
                <div class="text-center py-4 text-gray-500">
                    <i class="fas fa-list text-2xl mb-2"></i>
                    <p>Нет записей для отображения</p>
                </div>
            `;
            return;
        }

        this.filteredLogs.slice(0, 100).forEach(log => {
            const logElement = document.createElement('div');
            logElement.className = `log-entry ${log.level.toLowerCase()}`;
            logElement.innerHTML = `
                <div class="flex items-start justify-between">
                    <div class="flex-1">
                        <span class="log-timestamp">${new Date(log.timestamp).toLocaleString('ru-RU')}</span>
                        <span class="log-level ${log.level.toLowerCase()}">[${log.level}]</span>
                        <span class="text-sm text-gray-700">[${log.source}]</span>
                        <div class="log-message mt-1">${log.message}</div>
                        ${log.details ? `<div class="text-xs text-gray-600 mt-1">Детали: ${JSON.stringify(log.details)}</div>` : ''}
                    </div>
                    <button class="ml-2 text-gray-400 hover:text-gray-600" 
                            onclick="monitoringManager.showLogDetails(${log.id})"
                            title="Подробности">
                        <i class="fas fa-info-circle text-sm"></i>
                    </button>
                </div>
            `;
            logsList.appendChild(logElement);
        });
    }

    /**
     * Показ подробностей лога
     */
    showLogDetails(logId) {
        const log = this.app.logs.find(l => l.id === logId);
        if (!log) return;

        this.app.showNotification('info', 'Детали события', 
            `${log.timestamp.toLocaleString('ru-RU')} - ${log.source}: ${log.message}`);
    }

    /**
     * Очистка логов
     */
    clearLogs() {
        if (!confirm('Вы уверены, что хотите очистить журнал событий?')) {
            return;
        }

        this.app.logs = [];
        this.filteredLogs = [];
        this.renderLogs();
        this.app.showNotification('success', 'Логи очищены', 'Журнал событий успешно очищен');
    }

    /**
     * Экспорт логов
     */
    async exportLogs() {
        const exportData = {
            exportDate: new Date().toISOString(),
            totalEntries: this.filteredLogs.length,
            logs: this.filteredLogs
        };

        const dataStr = JSON.stringify(exportData, null, 2);
        const dataBlob = new Blob([dataStr], { type: 'application/json' });
        const url = URL.createObjectURL(dataBlob);
        
        const link = document.createElement('a');
        link.href = url;
        link.download = `networkview_logs_${new Date().toISOString().split('T')[0]}.json`;
        link.click();
        
        URL.revokeObjectURL(url);
        this.app.showNotification('success', 'Логи экспортированы', `Экспортировано ${this.filteredLogs.length} записей`);
    }
}

// Инициализация менеджера мониторинга
document.addEventListener('DOMContentLoaded', () => {
    setTimeout(() => {
        if (window.app) {
            window.monitoringManager = new MonitoringManager(window.app);
            
            // Переопределяем методы рендеринга в основном приложении
            window.app.renderDevices = () => {
                window.monitoringManager.renderDevices();
            };
            
            window.app.renderLogs = () => {
                window.monitoringManager.renderLogs();
            };
        }
    }, 100);
}); 