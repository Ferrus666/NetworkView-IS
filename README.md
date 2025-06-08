# NetworkView IS 2.0 - Система управления сетевой инфраструктурой

![NetworkView IS](https://img.shields.io/badge/NetworkView%20IS-v2.0.0-blue.svg)
![License](https://img.shields.io/badge/license-MIT-green.svg)
![Python](https://img.shields.io/badge/python-3.11+-brightgreen.svg)
![React](https://img.shields.io/badge/react-18.2+-brightgreen.svg)
![FastAPI](https://img.shields.io/badge/fastapi-0.104+-brightgreen.svg)

## 📋 Описание

NetworkView IS 2.0 - это современное веб-приложение для управления сетевой инфраструктурой, обеспечивающее:

- 📚 **Централизованный доступ к нормативной документации** по информационной безопасности
- 🗺️ **Интерактивную визуализацию сети** с поддержкой .drawio и .visio файлов
- 🔍 **Статический анализ безопасности кода (SAST)** с интеграцией Git-репозиториев
- 📊 **Мониторинг состояния сети в реальном времени** с интеграцией внешних систем

## 🏗️ Архитектура

### Backend (FastAPI + Python)
```
backend/
├── main.py                 # Основное приложение FastAPI
├── requirements.txt        # Python зависимости
├── api/
│   ├── documents.py        # API документации
│   ├── diagrams.py         # API диаграмм
│   ├── sast.py            # API SAST анализа
│   └── monitoring.py       # API мониторинга
├── models.py              # SQLAlchemy модели
├── schemas.py             # Pydantic схемы
└── uploads/               # Загруженные файлы
    ├── documents/
    ├── diagrams/
    └── code/
```

### Frontend (React + TypeScript)
```
frontend/
├── src/
│   ├── App.tsx            # Главное приложение
│   ├── main.tsx           # Точка входа
│   ├── components/        # React компоненты
│   │   ├── layout/        # Компоненты макета
│   │   ├── documents/     # Виджет документации
│   │   ├── diagrams/      # Виджет диаграмм
│   │   ├── sast/          # Виджет SAST
│   │   └── monitoring/    # Виджет мониторинга
│   ├── pages/             # Страницы приложения
│   ├── hooks/             # Custom React хуки
│   ├── store/             # Redux store
│   └── utils/             # Утилиты
├── package.json
├── tsconfig.json
└── vite.config.ts
```

## 🚀 Быстрый старт

### Системные требования

- **Python** 3.11+
- **Node.js** 18.0+
- **Redis** 5.0+ (опционально)
- **PostgreSQL** 12+ (опционально, по умолчанию SQLite)

### Установка

1. **Клонирование репозитория**
   ```bash
   git clone https://github.com/your-org/networkview-is.git
   cd networkview-is
   ```

2. **Установка всех зависимостей**
   ```bash
   npm run setup
   ```

3. **Настройка переменных окружения**
   ```bash
   # backend/.env
   SECRET_KEY=your-super-secret-key
   DATABASE_URL=sqlite:///./networkview.db
   REDIS_URL=redis://localhost:6379
   
   # Интеграции (опционально)
   ZABBIX_URL=http://your-zabbix.local
   ZABBIX_USERNAME=admin
   ZABBIX_PASSWORD=password
   PROMETHEUS_URL=http://localhost:9090
   ```

4. **Запуск в режиме разработки**
   ```bash
   npm run dev
   ```

5. **Доступ к приложению**
   - Frontend: http://localhost:3000
   - Backend API: http://localhost:8000
   - API Documentation: http://localhost:8000/docs

### Первый вход

- **Логин:** admin
- **Пароль:** admin123

## 🎯 Основные модули

### 1. 📚 Нормативная документация

**Возможности:**
- Загрузка документов (PDF, DOCX, TXT, MD)
- Категоризация по стандартам (ISO, ГОСТ, ФЗ, NIST, PCI DSS, GDPR, OWASP, CIS, HIPAA, COBIT)
- Полнотекстовый поиск с поддержкой Elasticsearch
- Система тегов и метаданных
- Экспорт в различные форматы
- Интеграция с внешними системами (Confluence, Jira)

**Поддерживаемые стандарты:**
- ISO/IEC 27001, 27002
- GDPR, ФЗ-152, ФЗ-187
- NIST SP 800-53
- PCI DSS
- OWASP Top 10
- CIS Controls
- HIPAA
- COBIT

### 2. 🗺️ Интерактивная визуализация сети

**Возможности:**
- Импорт файлов .drawio и .visio
- Интерактивная навигация по схемам
- Аннотации и комментарии
- Интеграция с CMDB
- Экспорт в PNG/SVG/JSON
- Поддержка модели C4

**Поддерживаемые элементы:**
- Серверы и рабочие станции
- Сетевое оборудование
- Виртуальные машины
- Микросервисы
- Облачные ресурсы

### 3. 🔍 SAST-анализ кода

**Возможности:**
- Интеграция с Git-репозиториями (GitHub, GitLab, Bitbucket)
- Загрузка архивов с кодом
- Поддержка множественных языков программирования
- Категоризация уязвимостей по OWASP Top 10
- Интеграция с CI/CD
- Экспорт отчетов

**Поддерживаемые языки:**
- Python (Bandit + Semgrep)
- JavaScript/TypeScript (ESLint + Semgrep)
- Java (Semgrep)
- Go (Semgrep + gosec)
- PHP (Semgrep)
- C/C++ (Semgrep)

**Инструменты анализа:**
- Semgrep (универсальный)
- Bandit (Python)
- ESLint (JavaScript)
- gosec (Go)

### 4. 📊 Мониторинг сети

**Возможности:**
- Мониторинг устройств в реальном времени
- Интеграция с Zabbix и Prometheus
- WebSocket для live-обновлений
- Ping-тестирование
- Метрики производительности
- Уведомления о сбоях

**Интеграции:**
- Zabbix API
- Prometheus/Grafana
- SNMP
- SSH мониторинг
- Webhook уведомления

## 🔐 Система безопасности

### Аутентификация и авторизация
- OAuth 2.0 / JWT токены
- Доменная аутентификация (SSO)
- Ролевая модель доступа:
  - **Супер администратор** - полный доступ
  - **Администратор** - управление контентом
  - **Пользователь** - просмотр и комментирование
  - **Аудитор** - генерация отчетов

### Шифрование
- TLS 1.3 для передачи данных
- AES-256 для хранения файлов
- Безопасное хранение паролей (bcrypt)

### Аудит
- Полное логирование действий пользователей
- Хранение логов 3 месяца
- Экспорт аудит-логов
- IP-адреса и User-Agent

## 📊 API Документация

### Основные эндпоинты

#### Аутентификация
```http
POST   /auth/token                    # Получить JWT токен
GET    /auth/me                       # Информация о пользователе
```

#### Документы
```http
GET    /api/documents                 # Список документов
POST   /api/documents/upload          # Загрузить документ
GET    /api/documents/{id}            # Информация о документе
GET    /api/documents/{id}/download   # Скачать документ
DELETE /api/documents/{id}            # Удалить документ
GET    /api/documents/search/advanced # Расширенный поиск
```

#### Диаграммы
```http
GET    /api/diagrams                  # Список диаграмм
POST   /api/diagrams/upload           # Загрузить диаграмму
GET    /api/diagrams/{id}/data        # Данные диаграммы
POST   /api/diagrams/{id}/annotations # Обновить аннотации
GET    /api/diagrams/{id}/download    # Экспорт диаграммы
```

#### SAST
```http
POST   /api/sast/scan/repository      # Сканирование репозитория
POST   /api/sast/scan/upload          # Сканирование архива
GET    /api/sast/scans                # Список сканирований
GET    /api/sast/scans/{id}           # Результаты сканирования
GET    /api/sast/scans/{id}/report    # Отчет по сканированию
```

#### Мониторинг
```http
GET    /api/monitoring/devices        # Список устройств
POST   /api/monitoring/devices        # Добавить устройство
POST   /api/monitoring/devices/{id}/ping # Ping устройства
GET    /api/monitoring/stats/summary  # Статистика мониторинга
WS     /api/monitoring/ws             # WebSocket для real-time
```

### WebSocket Events

```javascript
// Подключение
const socket = io('ws://localhost:8000/api/monitoring/ws');

// События устройств
socket.on('devices_update', (devices) => {
    console.log('Обновление устройств:', devices);
});

// Результат ping
socket.emit('ping_device', { device_id: 1 });
socket.on('ping_result', (result) => {
    console.log('Результат ping:', result);
});
```

## 🔧 Конфигурация

### Переменные окружения

```bash
# Backend
SECRET_KEY=your-secret-key
DATABASE_URL=postgresql://user:pass@localhost/networkview
REDIS_URL=redis://localhost:6379
ZABBIX_URL=http://zabbix.local
PROMETHEUS_URL=http://prometheus.local:9090

# Файлы
MAX_FILE_SIZE=500MB
UPLOAD_PATH=/app/uploads

# Безопасность
TOKEN_EXPIRE_MINUTES=30
CORS_ORIGINS=["http://localhost:3000"]

# Интеграции
TELEGRAM_BOT_TOKEN=your-bot-token
EMAIL_SMTP_HOST=smtp.gmail.com
EMAIL_SMTP_PORT=587
```

### Конфигурация интеграций

#### Zabbix
```python
ZABBIX_CONFIG = {
    "url": "http://zabbix.local",
    "username": "admin",
    "password": "password",
    "enabled": True
}
```

#### Prometheus
```python
PROMETHEUS_CONFIG = {
    "url": "http://prometheus.local:9090",
    "enabled": True
}
```

## 📈 Производительность

### Масштабируемость
- **Пользователи:** до 1000+ одновременных
- **Документы:** до 10,000+
- **Схемы сети:** до 100+ с 1000+ элементов
- **SAST:** проекты до 100k строк кода
- **Мониторинг:** до 100+ устройств в real-time

### Оптимизация
- Redis кэширование
- Асинхронная обработка задач
- Lazy loading компонентов
- Виртуализация больших списков
- Сжатие статических ресурсов

## 🔄 CI/CD и деплой

### Docker Compose
```yaml
version: '3.8'
services:
  backend:
    build: ./backend
    ports:
      - "8000:8000"
    environment:
      - DATABASE_URL=postgresql://user:pass@db:5432/networkview
      - REDIS_URL=redis://redis:6379
    depends_on:
      - db
      - redis

  frontend:
    build: ./frontend
    ports:
      - "3000:3000"
    depends_on:
      - backend

  db:
    image: postgres:15
    environment:
      POSTGRES_DB: networkview
      POSTGRES_USER: user
      POSTGRES_PASSWORD: password

  redis:
    image: redis:7-alpine
```

### Kubernetes
```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: networkview-backend
spec:
  replicas: 3
  selector:
    matchLabels:
      app: networkview-backend
  template:
    metadata:
      labels:
        app: networkview-backend
    spec:
      containers:
      - name: backend
        image: networkview/backend:latest
        ports:
        - containerPort: 8000
        env:
        - name: DATABASE_URL
          valueFrom:
            secretKeyRef:
              name: networkview-secrets
              key: database-url
```

## 🧪 Тестирование

### Backend тесты
```bash
cd backend
pytest tests/ -v --cov=.
```

### Frontend тесты
```bash
cd frontend
npm test
npm run test:coverage
```

### E2E тесты
```bash
npm run test:e2e
```

## 📦 Сборка для продакшена

```bash
# Сборка frontend
cd frontend
npm run build

# Сборка Docker образов
docker build -t networkview/backend ./backend
docker build -t networkview/frontend ./frontend

# Или использование docker-compose
docker-compose -f docker-compose.prod.yml up -d
```

## 🤝 Интеграции

### Поддерживаемые системы
- **SIEM:** Splunk, QRadar, ArcSight
- **GRC:** ServiceNow, MetricStream
- **CMDB:** ServiceNow, Device42
- **Мониторинг:** Zabbix, Prometheus, Nagios
- **Репозитории:** GitHub, GitLab, Bitbucket
- **Документооборот:** Confluence, SharePoint
- **Таск-трекеры:** Jira, Trello
- **Уведомления:** Telegram, Email, Slack

### REST API
- OpenAPI 3.0 спецификация
- Swagger UI документация
- Rate limiting
- Versioning support

### Webhooks
```javascript
// Настройка webhook для уведомлений
{
  "url": "https://hooks.slack.com/...",
  "events": ["device_down", "high_vulnerability", "scan_completed"],
  "secret": "webhook-secret"
}
```

## 📚 Документация

- [API Reference](http://localhost:8000/docs)
- [User Guide](./docs/user-guide.md)
- [Admin Guide](./docs/admin-guide.md)
- [Developer Guide](./docs/developer-guide.md)
- [Deployment Guide](./docs/deployment.md)

## 🐛 Известные проблемы

- [ ] Поддержка .visio файлов ограничена базовыми функциями
- [ ] PDF экспорт отчетов в разработке
- [ ] Мобильная версия требует доработки

## 🗺️ Roadmap

### v2.1 (Q1 2024)
- [ ] Полная поддержка .visio файлов
- [ ] AI-ассистент для анализа документов
- [ ] Расширенная интеграция с облачными провайдерами

### v2.2 (Q2 2024)
- [ ] Mobile-first UI
- [ ] GraphQL API
- [ ] Advanced analytics dashboard

### v2.3 (Q3 2024)
- [ ] Machine Learning для предиктивного анализа
- [ ] Blockchain для аудита изменений
- [ ] Advanced threat intelligence

## 📄 Лицензия

MIT License - см. [LICENSE](LICENSE) файл.

## 👥 Команда

- **Архитектор проекта:** NetworkView Team
- **Backend разработчик:** Python/FastAPI Expert
- **Frontend разработчик:** React/TypeScript Expert
- **DevOps инженер:** Kubernetes/Docker Expert

## 📞 Поддержка

- **Email:** support@networkview.local
- **Документация:** [Wiki](./docs/)
- **Issues:** [GitHub Issues](https://github.com/your-org/networkview-is/issues)
- **Discussions:** [GitHub Discussions](https://github.com/your-org/networkview-is/discussions) 