/**
 * NetworkView IS - Серверная часть
 * Express сервер с WebSocket поддержкой для работы с диаграммами и мониторингом
 */

const express = require('express');
const http = require('http');
const socketIo = require('socket.io');
const cors = require('cors');
const multer = require('multer');
const xml2js = require('xml2js');
const fs = require('fs').promises;
const path = require('path');
const { v4: uuidv4 } = require('uuid');
const helmet = require('helmet');
const rateLimit = require('express-rate-limit');

// Создание Express приложения
const app = express();
const server = http.createServer(app);
const io = socketIo(server, {
    cors: {
        origin: "*",
        methods: ["GET", "POST"]
    }
});

const PORT = process.env.PORT || 3000;

// Middleware
app.use(helmet({
    contentSecurityPolicy: false // Отключаем для разработки
}));

app.use(cors());
app.use(express.json({ limit: '50mb' }));
app.use(express.urlencoded({ extended: true, limit: '50mb' }));

// Rate limiting
const limiter = rateLimit({
    windowMs: 15 * 60 * 1000, // 15 минут
    max: 100 // максимум 100 запросов с одного IP
});
app.use('/api/', limiter);

// Статические файлы
app.use(express.static(path.join(__dirname, '..')));

// Настройка multer для загрузки файлов
const storage = multer.diskStorage({
    destination: function (req, file, cb) {
        const uploadDir = path.join(__dirname, '..', 'uploads');
        ensureDirectoryExists(uploadDir);
        cb(null, uploadDir);
    },
    filename: function (req, file, cb) {
        const uniqueSuffix = Date.now() + '-' + Math.round(Math.random() * 1E9);
        cb(null, file.fieldname + '-' + uniqueSuffix + path.extname(file.originalname));
    }
});

const upload = multer({ 
    storage: storage,
    limits: {
        fileSize: 50 * 1024 * 1024 // 50MB
    },
    fileFilter: function (req, file, cb) {
        // Проверка типов файлов
        if (file.fieldname === 'document') {
            const allowedTypes = ['application/pdf', 'application/vnd.openxmlformats-officedocument.wordprocessingml.document', 'text/plain'];
            if (allowedTypes.includes(file.mimetype) || file.originalname.match(/\.(pdf|docx|txt)$/)) {
                cb(null, true);
            } else {
                cb(new Error('Неподдерживаемый тип файла для документа'));
            }
        } else if (file.fieldname === 'diagram') {
            if (file.originalname.match(/\.(drawio|xml)$/)) {
                cb(null, true);
            } else {
                cb(new Error('Неподдерживаемый тип файла для диаграммы'));
            }
        } else {
            cb(new Error('Неизвестное поле файла'));
        }
    }
});

// База данных в памяти (в продакшене использовать реальную БД)
let database = {
    documents: [],
    diagrams: [],
    devices: [],
    logs: [],
    users: [],
    settings: {}
};

// Инициализация директорий
async function ensureDirectoryExists(dirPath) {
    try {
        await fs.access(dirPath);
    } catch (error) {
        await fs.mkdir(dirPath, { recursive: true });
    }
}

// Загрузка данных при старте
async function loadDatabase() {
    try {
        const dataPath = path.join(__dirname, 'data.json');
        const data = await fs.readFile(dataPath, 'utf8');
        database = { ...database, ...JSON.parse(data) };
        console.log('База данных загружена');
    } catch (error) {
        console.log('Создание новой базы данных');
        await saveDatabase();
    }
}

// Сохранение данных
async function saveDatabase() {
    try {
        const dataPath = path.join(__dirname, 'data.json');
        await fs.writeFile(dataPath, JSON.stringify(database, null, 2));
    } catch (error) {
        console.error('Ошибка сохранения базы данных:', error);
    }
}

// API Маршруты

// Получение документов
app.get('/api/documents', (req, res) => {
    try {
        const { category, type, search } = req.query;
        let documents = [...database.documents];

        if (category) {
            documents = documents.filter(doc => doc.category === category);
        }

        if (type) {
            documents = documents.filter(doc => doc.type === type);
        }

        if (search) {
            const searchLower = search.toLowerCase();
            documents = documents.filter(doc => 
                doc.name.toLowerCase().includes(searchLower) ||
                doc.description.toLowerCase().includes(searchLower) ||
                (doc.tags && doc.tags.some(tag => tag.toLowerCase().includes(searchLower)))
            );
        }

        res.json(documents);
    } catch (error) {
        console.error('Ошибка получения документов:', error);
        res.status(500).json({ error: 'Внутренняя ошибка сервера' });
    }
});

// Загрузка документа
app.post('/api/documents/upload', upload.single('document'), async (req, res) => {
    try {
        if (!req.file) {
            return res.status(400).json({ error: 'Файл не был загружен' });
        }

        const document = {
            id: uuidv4(),
            name: req.file.originalname,
            description: req.body.description || 'Загруженный документ',
            category: req.body.category || 'Общие',
            type: path.extname(req.file.originalname).substring(1).toUpperCase(),
            size: formatFileSize(req.file.size),
            uploadDate: new Date().toISOString().split('T')[0],
            tags: req.body.tags ? req.body.tags.split(',').map(tag => tag.trim()) : [],
            url: `/uploads/${req.file.filename}`,
            filename: req.file.filename,
            status: 'active'
        };

        database.documents.push(document);
        await saveDatabase();

        // Отправка обновления всем подключенным клиентам
        io.emit('document_uploaded', document);

        res.json(document);
    } catch (error) {
        console.error('Ошибка загрузки документа:', error);
        res.status(500).json({ error: 'Ошибка загрузки документа' });
    }
});

// Получение диаграмм
app.get('/api/diagrams', (req, res) => {
    try {
        res.json(database.diagrams);
    } catch (error) {
        console.error('Ошибка получения диаграмм:', error);
        res.status(500).json({ error: 'Внутренняя ошибка сервера' });
    }
});

// Загрузка диаграммы
app.post('/api/diagrams/upload', upload.single('diagram'), async (req, res) => {
    try {
        if (!req.file) {
            return res.status(400).json({ error: 'Файл не был загружен' });
        }

        const fileContent = await fs.readFile(req.file.path, 'utf8');
        const diagram = await parseDiagramFile(fileContent, req.file.originalname);
        
        diagram.id = uuidv4();
        diagram.filename = req.file.filename;
        diagram.uploadDate = new Date().toISOString().split('T')[0];

        database.diagrams.push(diagram);
        await saveDatabase();

        // Отправка обновления всем подключенным клиентам
        io.emit('diagram_uploaded', diagram);

        res.json(diagram);
    } catch (error) {
        console.error('Ошибка загрузки диаграммы:', error);
        res.status(500).json({ error: 'Ошибка обработки диаграммы' });
    }
});

// Получение устройств
app.get('/api/devices', (req, res) => {
    try {
        res.json(database.devices);
    } catch (error) {
        console.error('Ошибка получения устройств:', error);
        res.status(500).json({ error: 'Внутренняя ошибка сервера' });
    }
});

// Обновление статуса устройства
app.put('/api/devices/:id/status', async (req, res) => {
    try {
        const { id } = req.params;
        const { status } = req.body;

        const device = database.devices.find(d => d.id === id);
        if (!device) {
            return res.status(404).json({ error: 'Устройство не найдено' });
        }

        device.status = status;
        device.lastSeen = new Date().toISOString();
        
        await saveDatabase();

        // Отправка обновления всем подключенным клиентам
        io.emit('device_status_update', database.devices);

        // Добавление записи в лог
        const logEntry = {
            id: uuidv4(),
            timestamp: new Date().toISOString(),
            level: status === 'offline' ? 'ERROR' : 'INFO',
            source: 'API',
            message: `Статус устройства ${device.name} изменен на ${status}`,
            details: { deviceId: id, newStatus: status }
        };

        database.logs.unshift(logEntry);
        io.emit('new_log', logEntry);

        res.json(device);
    } catch (error) {
        console.error('Ошибка обновления устройства:', error);
        res.status(500).json({ error: 'Ошибка обновления устройства' });
    }
});

// Получение логов
app.get('/api/logs', (req, res) => {
    try {
        const { level, startDate, endDate, limit = 100 } = req.query;
        let logs = [...database.logs];

        if (level) {
            logs = logs.filter(log => log.level === level);
        }

        if (startDate) {
            logs = logs.filter(log => new Date(log.timestamp) >= new Date(startDate));
        }

        if (endDate) {
            logs = logs.filter(log => new Date(log.timestamp) <= new Date(endDate));
        }

        // Ограничение количества записей
        logs = logs.slice(0, parseInt(limit));

        res.json(logs);
    } catch (error) {
        console.error('Ошибка получения логов:', error);
        res.status(500).json({ error: 'Внутренняя ошибка сервера' });
    }
});

// Экспорт данных
app.get('/api/export/:type', (req, res) => {
    try {
        const { type } = req.params;
        let data;

        switch (type) {
            case 'documents':
                data = database.documents;
                break;
            case 'diagrams':
                data = database.diagrams;
                break;
            case 'devices':
                data = database.devices;
                break;
            case 'logs':
                data = database.logs;
                break;
            case 'all':
                data = database;
                break;
            default:
                return res.status(400).json({ error: 'Неизвестный тип экспорта' });
        }

        const exportData = {
            type,
            exportDate: new Date().toISOString(),
            totalRecords: Array.isArray(data) ? data.length : Object.keys(data).length,
            data
        };

        res.setHeader('Content-Disposition', `attachment; filename=networkview_${type}_${new Date().toISOString().split('T')[0]}.json`);
        res.setHeader('Content-Type', 'application/json');
        res.json(exportData);
    } catch (error) {
        console.error('Ошибка экспорта:', error);
        res.status(500).json({ error: 'Ошибка экспорта данных' });
    }
});

// Статистика системы
app.get('/api/stats', (req, res) => {
    try {
        const stats = {
            documents: {
                total: database.documents.length,
                byCategory: {},
                byType: {}
            },
            diagrams: {
                total: database.diagrams.length
            },
            devices: {
                total: database.devices.length,
                online: database.devices.filter(d => d.status === 'online').length,
                offline: database.devices.filter(d => d.status === 'offline').length,
                warning: database.devices.filter(d => d.status === 'warning').length
            },
            logs: {
                total: database.logs.length,
                today: database.logs.filter(l => {
                    const today = new Date().toDateString();
                    return new Date(l.timestamp).toDateString() === today;
                }).length,
                byLevel: {}
            },
            lastUpdate: new Date().toISOString()
        };

        // Статистика документов по категориям
        database.documents.forEach(doc => {
            stats.documents.byCategory[doc.category] = (stats.documents.byCategory[doc.category] || 0) + 1;
            stats.documents.byType[doc.type] = (stats.documents.byType[doc.type] || 0) + 1;
        });

        // Статистика логов по уровням
        database.logs.forEach(log => {
            stats.logs.byLevel[log.level] = (stats.logs.byLevel[log.level] || 0) + 1;
        });

        res.json(stats);
    } catch (error) {
        console.error('Ошибка получения статистики:', error);
        res.status(500).json({ error: 'Ошибка получения статистики' });
    }
});

// WebSocket обработчики
io.on('connection', (socket) => {
    console.log('Новое подключение:', socket.id);

    // Отправка текущего состояния новому клиенту
    socket.emit('initial_data', {
        documents: database.documents,
        diagrams: database.diagrams,
        devices: database.devices,
        logs: database.logs.slice(0, 100)
    });

    // Обработчик запроса пинга устройства
    socket.on('ping_device', async (deviceId) => {
        try {
            const device = database.devices.find(d => d.id === deviceId);
            if (device) {
                // Симуляция пинга
                const success = Math.random() > 0.1;
                const responseTime = Math.floor(Math.random() * 100) + 1;

                const result = {
                    deviceId,
                    success,
                    responseTime: success ? responseTime : null,
                    timestamp: new Date().toISOString()
                };

                socket.emit('ping_result', result);

                // Добавление записи в лог
                const logEntry = {
                    id: uuidv4(),
                    timestamp: new Date().toISOString(),
                    level: success ? 'INFO' : 'ERROR',
                    source: 'Network',
                    message: success 
                        ? `Пинг ${device.name} (${device.ip}) успешен - ${responseTime} мс`
                        : `Пинг ${device.name} (${device.ip}) неудачен`,
                    details: result
                };

                database.logs.unshift(logEntry);
                io.emit('new_log', logEntry);
            }
        } catch (error) {
            socket.emit('ping_result', { deviceId, success: false, error: error.message });
        }
    });

    // Обработчик отключения
    socket.on('disconnect', () => {
        console.log('Отключение:', socket.id);
    });
});

// Вспомогательные функции

// Форматирование размера файла
function formatFileSize(bytes) {
    if (bytes === 0) return '0 Bytes';
    const k = 1024;
    const sizes = ['Bytes', 'KB', 'MB', 'GB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
}

// Парсинг файла диаграммы
async function parseDiagramFile(content, filename) {
    try {
        const parser = new xml2js.Parser();
        const result = await parser.parseStringPromise(content);
        
        // Базовая структура диаграммы
        const diagram = {
            name: filename.replace(/\.[^/.]+$/, ''),
            description: 'Диаграмма, импортированная из ' + filename,
            nodes: [],
            edges: [],
            rawXml: content
        };

        // Упрощенный парсинг mxGraph XML
        if (result.mxfile && result.mxfile.diagram) {
            const diagramData = result.mxfile.diagram[0];
            if (diagramData.mxGraphModel) {
                const graphModel = diagramData.mxGraphModel[0];
                if (graphModel.root && graphModel.root[0].mxCell) {
                    const cells = graphModel.root[0].mxCell;
                    
                    cells.forEach((cell, index) => {
                        const cellData = cell.$;
                        if (cellData && cellData.vertex === '1') {
                            // Это вершина (узел)
                            const geometry = cell.mxGeometry ? cell.mxGeometry[0].$ : {};
                            diagram.nodes.push({
                                id: cellData.id || `node_${index}`,
                                type: 'imported',
                                name: cellData.value || `Узел ${index}`,
                                ip: '192.168.1.' + (100 + index),
                                status: 'online',
                                x: parseFloat(geometry.x) || Math.random() * 400,
                                y: parseFloat(geometry.y) || Math.random() * 300,
                                metadata: {
                                    source: 'Import from ' + filename,
                                    originalId: cellData.id
                                }
                            });
                        } else if (cellData && cellData.edge === '1') {
                            // Это ребро (связь)
                            diagram.edges.push({
                                id: cellData.id || `edge_${index}`,
                                from: cellData.source,
                                to: cellData.target,
                                port: '80',
                                subnet: '192.168.1.0/24',
                                bandwidth: '1 Gbps',
                                protocol: 'Ethernet'
                            });
                        }
                    });
                }
            }
        }

        // Если парсинг не дал результатов, создаем базовую диаграмму
        if (diagram.nodes.length === 0) {
            diagram.nodes.push({
                id: 'imported_node_1',
                type: 'server',
                name: 'Импортированный узел',
                ip: '192.168.1.50',
                status: 'online',
                x: 200,
                y: 150,
                metadata: {
                    source: 'Import from ' + filename
                }
            });
        }

        return diagram;
    } catch (error) {
        console.error('Ошибка парсинга диаграммы:', error);
        throw new Error('Не удалось обработать файл диаграммы');
    }
}

// Периодическое обновление данных устройств
setInterval(() => {
    // Симуляция изменений в устройствах
    database.devices.forEach(device => {
        if (Math.random() > 0.95) { // 5% шанс изменения
            const oldStatus = device.status;
            const statuses = ['online', 'offline', 'warning'];
            device.status = statuses[Math.floor(Math.random() * statuses.length)];
            
            if (oldStatus !== device.status) {
                device.lastSeen = new Date().toISOString();
                
                const logEntry = {
                    id: uuidv4(),
                    timestamp: new Date().toISOString(),
                    level: device.status === 'offline' ? 'ERROR' : 'WARNING',
                    source: 'Monitor',
                    message: `Изменение статуса ${device.name}: ${oldStatus} → ${device.status}`,
                    details: { deviceId: device.id, oldStatus, newStatus: device.status }
                };

                database.logs.unshift(logEntry);
                io.emit('new_log', logEntry);
                io.emit('device_status_update', database.devices);
            }
        }
    });
}, 60000); // Каждую минуту

// Автосохранение базы данных
setInterval(saveDatabase, 300000); // Каждые 5 минут

// Обработка завершения работы
process.on('SIGINT', async () => {
    console.log('Сохранение данных перед завершением...');
    await saveDatabase();
    process.exit(0);
});

process.on('SIGTERM', async () => {
    console.log('Сохранение данных перед завершением...');
    await saveDatabase();
    process.exit(0);
});

// Инициализация и запуск сервера
async function startServer() {
    try {
        // Создание необходимых директорий
        await ensureDirectoryExists(path.join(__dirname, '..', 'uploads'));
        
        // Загрузка базы данных
        await loadDatabase();
        
        // Запуск сервера
        server.listen(PORT, () => {
            console.log(`\n🚀 NetworkView IS Server запущен на порту ${PORT}`);
            console.log(`📁 Статические файлы: http://localhost:${PORT}`);
            console.log(`🔗 API: http://localhost:${PORT}/api`);
            console.log(`⚡ WebSocket: ws://localhost:${PORT}`);
            console.log(`📊 Статистика: http://localhost:${PORT}/api/stats`);
            console.log('\n✅ Сервер готов к работе!\n');
        });
    } catch (error) {
        console.error('Ошибка запуска сервера:', error);
        process.exit(1);
    }
}

// Запуск сервера
startServer(); 