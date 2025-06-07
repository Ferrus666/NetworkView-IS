# NetworkView IS - Информационная система управления сетевой инфраструктурой

![NetworkView IS](https://img.shields.io/badge/NetworkView%20IS-v1.0.0-blue.svg)
![License](https://img.shields.io/badge/license-MIT-green.svg)
![Node.js](https://img.shields.io/badge/node.js-18+-brightgreen.svg)

## 📋 Описание

NetworkView IS - это современная веб-система для управления сетевой инфраструктурой и документацией по информационной безопасности. Система предоставляет интуитивный интерфейс с четырьмя основными модулями для комплексного управления ИТ-ресурсами организации.

### ✨ Основные возможности

- 📚 **Управление нормативной документацией ИБ** - централизованное хранение и поиск документов
- 🗺️ **Интерактивные сетевые диаграммы** - импорт и визуализация схем из .drawio файлов
- 📊 **Мониторинг сети в реальном времени** - отслеживание состояния устройств
- 📝 **Журналирование событий** - централизованный сбор и анализ логов

## 🏗️ Архитектура системы

```
NetworkView IS/
├── index.html              # Главная страница
├── css/
│   └── style.css           # Стили интерфейса
├── js/
│   ├── app.js              # Основное приложение
│   ├── documents.js        # Модуль документов
│   ├── diagrams.js         # Модуль диаграмм
│   └── monitoring.js       # Модуль мониторинга
├── server/
│   └── index.js            # Express сервер
├── uploads/                # Загруженные файлы
└── package.json
```

## 🚀 Быстрый старт

### Требования

- **Node.js** 18.0.0 или выше
- **npm** 9.0.0 или выше
- **Браузер** с поддержкой ES6+ (Chrome 80+, Firefox 75+, Safari 13+)

### Установка

1. **Клонируйте репозиторий или скачайте архив**
   ```bash
   git clone https://github.com/your-org/networkview-is.git
   cd networkview-is
   ```

2. **Установите зависимости**
   ```bash
   npm install
   ```

3. **Запустите сервер разработки**
   ```bash
   npm run dev
   ```

4. **Откройте браузер**
   ```
   http://localhost:3001
   ```

### Альтернативные команды запуска

```bash
# Только сервер
npm run dev:server

# Только клиент
npm run dev:client

# Продакшн режим
npm start
```

## 🎯 Функциональные модули

### 1. 📚 Модуль документации ИБ

**Возможности:**
- Загрузка документов (PDF, DOCX, TXT)
- Категоризация по типам (ГОСТ, ISO, ФЗ, Приказы)
- Полнотекстовый поиск по названию и тегам
- Предварительный просмотр с поддержкой Markdown
- Система тегов и метаданных

**Поддерживаемые форматы:**
- PDF (до 50MB)
- Microsoft Word (.docx)
- Текстовые файлы (.txt)

**Примеры документов:**
- ФЗ-152 "О персональных данных"
- ISO/IEC 27001:2013
- ГОСТ Р 57580-2017
- Приказы ФСТЭК России

### 2. 🗺️ Модуль диаграмм

**Возможности:**
- Импорт файлов .drawio и .xml
- Интерактивная визуализация сетевых схем
- Информация об узлах (IP, тип, статус, метрики)
- Данные о соединениях (порты, подсети, пропускная способность)
- Масштабирование и навигация
- Экспорт в различные форматы

**Поддерживаемые элементы:**
- Маршрутизаторы и коммутаторы
- Серверы и рабочие станции
- Виртуальные машины
- Сетевое оборудование

### 3. 📊 Модуль мониторинга

**Возможности:**
- Мониторинг состояния устройств в реальном времени
- Отображение метрик производительности (CPU, память, температура)
- Ping-тестирование устройств
- Автоматическое обнаружение изменений статуса
- Уведомления о критических событиях

**Типы устройств:**
- Сетевое оборудование
- Серверы и станции
- Принтеры и периферия
- Системы безопасности

### 4. 📝 Модуль журналирования

**Возможности:**
- Централизованный сбор событий
- Фильтрация по уровню важности (INFO, WARNING, ERROR)
- Поиск по датам и источникам
- Экспорт логов в JSON формате
- Автоматическая архивация старых записей

## 🔧 API Документация

### Основные эндпоинты

#### Документы
```http
GET    /api/documents                 # Получить список документов
POST   /api/documents/upload          # Загрузить документ
```

#### Диаграммы
```http
GET    /api/diagrams                  # Получить список диаграмм
POST   /api/diagrams/upload           # Загрузить диаграмму
```

#### Устройства
```http
GET    /api/devices                   # Получить список устройств
PUT    /api/devices/:id/status        # Обновить статус устройства
```

#### Логи
```http
GET    /api/logs                      # Получить логи
GET    /api/logs?level=ERROR          # Фильтр по уровню
GET    /api/logs?startDate=2024-01-01 # Фильтр по дате
```

#### Экспорт и статистика
```http
GET    /api/export/:type              # Экспорт данных
GET    /api/stats                     # Статистика системы
```

### WebSocket события

```javascript
// Подключение к WebSocket
const socket = io('http://localhost:3000');

// Получение обновлений устройств
socket.on('device_status_update', (devices) => {
    console.log('Обновление устройств:', devices);
});

// Новые записи в логах
socket.on('new_log', (logEntry) => {
    console.log('Новая запись:', logEntry);
});

// Ping устройства
socket.emit('ping_device', deviceId);
socket.on('ping_result', (result) => {
    console.log('Результат пинга:', result);
});
```

## ⚙️ Конфигурация

### Переменные окружения

```bash
# .env файл
PORT=3000                    # Порт сервера
NODE_ENV=development         # Режим работы
MAX_FILE_SIZE=52428800      # Максимальный размер файла (50MB)
DB_PATH=./server/data.json  # Путь к файлу базы данных
UPLOAD_DIR=./uploads        # Директория загрузок
```

### Настройки системы

```json
{
  "theme": "light",           // Тема интерфейса
  "autoUpdate": true,         // Автообновление данных
  "notifications": true,      // Уведомления
  "language": "ru",          // Язык интерфейса
  "monitoringInterval": 30   // Интервал мониторинга (сек)
}
```

## 🔒 Безопасность

### Реализованные меры
- **Rate Limiting** - ограничение количества запросов
- **Helmet.js** - защита HTTP заголовков
- **Валидация файлов** - проверка типов и размеров
- **CORS настройки** - контроль доступа между доменами
- **Санитизация данных** - очистка пользовательского ввода

### Рекомендации для продакшена
- Настройте HTTPS
- Используйте реальную базу данных (PostgreSQL/MongoDB)
- Настройте аутентификацию и авторизацию
- Реализуйте резервное копирование
- Настройте мониторинг и логирование

## 📱 Адаптивность

Система полностью адаптирована для различных устройств:

- **Desktop** (1920px+) - полная функциональность
- **Tablet** (768px-1919px) - адаптированный интерфейс
- **Mobile** (до 767px) - упрощенная компоновка

## 🛠️ Разработка

### Структура кода

```javascript
// Основное приложение
class NetworkViewIS {
    constructor() {
        this.socket = null;
        this.documents = [];
        this.diagrams = [];
        this.devices = [];
        this.logs = [];
    }
}

// Модули
class DocumentManager extends BaseModule {}
class DiagramManager extends BaseModule {}
class MonitoringManager extends BaseModule {}
```

### Расширение функциональности

1. **Добавление нового модуля:**
   ```javascript
   class NewModule {
       constructor(app) {
           this.app = app;
           this.init();
       }
   }
   ```

2. **Добавление API эндпоинта:**
   ```javascript
   app.get('/api/new-endpoint', (req, res) => {
       res.json({ message: 'New endpoint' });
   });
   ```

3. **Добавление WebSocket события:**
   ```javascript
   socket.on('new_event', (data) => {
       io.emit('response_event', processedData);
   });
   ```

## 🧪 Тестирование

### Функциональное тестирование
```bash
# Проверка загрузки документов
curl -X POST -F "document=@test.pdf" http://localhost:3000/api/documents/upload

# Проверка API статистики
curl http://localhost:3000/api/stats

# Проверка экспорта
curl http://localhost:3000/api/export/all
```

### Нагрузочное тестирование
- Используйте Apache JMeter для тестирования производительности
- Тестируйте WebSocket соединения с помощью Artillery.io
- Проверьте обработку больших файлов

## 🚀 Развертывание

### Docker
```dockerfile
FROM node:18-alpine
WORKDIR /app
COPY package*.json ./
RUN npm ci --only=production
COPY . .
EXPOSE 3000
CMD ["node", "server/index.js"]
```

### PM2 (Process Manager)
```bash
npm install -g pm2
pm2 start server/index.js --name "networkview-is"
pm2 startup
pm2 save
```

### Nginx (обратный прокси)
```nginx
server {
    listen 80;
    server_name your-domain.com;
    
    location / {
        proxy_pass http://localhost:3000;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection 'upgrade';
        proxy_set_header Host $host;
        proxy_cache_bypass $http_upgrade;
    }
}
```

## 📊 Мониторинг и логирование

### Метрики системы
- Количество активных соединений
- Использование памяти и CPU
- Количество обработанных запросов
- Размер базы данных

### Логирование
```javascript
// Настройка Winston logger
const winston = require('winston');

const logger = winston.createLogger({
    level: 'info',
    format: winston.format.json(),
    transports: [
        new winston.transports.File({ filename: 'error.log', level: 'error' }),
        new winston.transports.File({ filename: 'combined.log' })
    ]
});
```

## 🤝 Вклад в развитие

1. Создайте fork репозитория
2. Создайте ветку для новой функции (`git checkout -b feature/new-feature`)
3. Внесите изменения и добавьте тесты
4. Зафиксируйте изменения (`git commit -am 'Add new feature'`)
5. Отправьте изменения (`git push origin feature/new-feature`)
6. Создайте Pull Request

## 📄 Лицензия

Данный проект распространяется под лицензией MIT. Подробности в файле [LICENSE](LICENSE).

## 👥 Команда разработки

- **Архитектор системы** - Дизайн и архитектура
- **Frontend разработчик** - Пользовательский интерфейс
- **Backend разработчик** - Серверная логика
- **DevOps инженер** - Развертывание и инфраструктура

## 📞 Поддержка

- **Email:** support@networkview-is.ru
- **Документация:** [https://docs.networkview-is.ru](https://docs.networkview-is.ru)
- **Issues:** [GitHub Issues](https://github.com/your-org/networkview-is/issues)
- **Telegram:** @networkview_support

## 🎯 Roadmap

### Версия 1.1.0
- [ ] Система аутентификации и авторизации
- [ ] Интеграция с Active Directory
- [ ] Расширенная аналитика и отчеты
- [ ] Мобильное приложение

### Версия 1.2.0
- [ ] Интеграция с системами мониторинга (Zabbix, Nagios)
- [ ] AI-анализ сетевого трафика
- [ ] Автоматическое обнаружение устройств
- [ ] Система уведомлений (Email, SMS, Slack)

### Версия 2.0.0
- [ ] Микросервисная архитектура
- [ ] Поддержка мультитенантности
- [ ] Интеграция с облачными провайдерами
- [ ] Расширенная визуализация данных

---

**NetworkView IS** - ваш надежный помощник в управлении сетевой инфраструктурой! 🚀 