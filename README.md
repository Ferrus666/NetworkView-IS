# 🏦 BMK Security Cabinet 2.0

> Личный кабинет инженера по информационной безопасности банка БМК

## 📋 Описание проекта

BMK Security Cabinet - это комплексное веб-приложение для управления задачами информационной безопасности в банковской среде. Система обеспечивает централизованный доступ к нормативной документации, интерактивную визуализацию сети, статический анализ безопасности кода (SAST), мониторинг сети в реальном времени, а также интеграции с внешними системами.

## ✨ Основные возможности

### 🔐 Аутентификация и авторизация
- Многоуровневая система ролей (Super Admin, Admin, User, Auditor, Read-only)
- Двухфакторная аутентификация (2FA)
- JWT-токены с автоматическим обновлением
- Блокировка аккаунта при превышении попыток входа
- Логирование всех действий пользователей

### 📚 Централизованное управление документацией
- Хранение и категоризация нормативных документов (ФСТЭК, ФСБ, ЦБ РФ, ISO 27001)
- Полнотекстовый поиск с поддержкой фильтров
- Система версионирования документов
- Генерация интерактивных чек-листов для аудитов
- Markdown-редактор для создания внутренних инструкций
- Статистика скачиваний и популярности документов

### 🔍 SAST (Static Application Security Testing)
- Анализ кода на уязвимости для Python, JavaScript, Java, Go, PHP, C/C++
- Интеграция с Semgrep, Bandit, ESLint
- Сканирование Git-репозиториев и загруженных архивов
- Детальные отчеты с классификацией уязвимостей по OWASP Top 10
- Экспорт результатов в PDF, JSON, CSV
- Интеграция с CI/CD pipeline через REST API

### 🌐 Визуализация сетевой инфраструктуры
- Интерактивные сетевые диаграммы с поддержкой C4 модели
- Импорт схем из draw.io и Visio
- Аннотации и комментарии к элементам сети
- Фильтрация и поиск по устройствам
- Отображение статуса устройств в реальном времени
- Масштабируемый просмотр с поддержкой больших топологий

### 📊 Мониторинг сети в реальном времени
- Отображение состояния сетевых устройств
- Метрики производительности (CPU, RAM, трафик)
- WebSocket для обновлений в реальном времени
- Система уведомлений и алертов
- Исторические графики метрик
- Настраиваемые пороги предупреждений

### 🔗 Интеграции с внешними системами
- **NetBox**: Синхронизация данных об устройствах и IP-адресах
- **Zabbix**: Получение метрик мониторинга
- **Prometheus**: Сбор и отображение метрик
- **Lansweeper**: Инвентаризация IT-активов
- **Is-info**: Обмен данными об инцидентах
- **OpenData**: Доступ к реестрам уязвимостей

## 🏗️ Архитектура системы

### Frontend (React + TypeScript)
- **React 18** с TypeScript для типобезопасности
- **Material-UI** в красно-белой стилистике банка БМК
- **Zustand** для управления состоянием
- **React Query** для кэширования API запросов
- **Cytoscape.js** для визуализации сетевых диаграмм
- **Chart.js** для графиков и метрик

### Backend (FastAPI + Python)
- **FastAPI** для высокопроизводительного API
- **Supabase** в качестве основной базы данных
- **Redis** для кэширования и сессий
- **Celery** для фоновых задач
- **WebSocket** для real-time коммуникации
- **JWT** аутентификация с refresh токенами

### База данных (Supabase/PostgreSQL)
- Таблицы: users, documents, sast_results, network_devices, monitoring_logs
- Row-Level Security (RLS) для безопасности данных
- JSONB поля для гибкого хранения метаданных
- Полнотекстовый поиск с pg_trgm

### Инфраструктура
- **Docker** и **Docker Compose** для контейнеризации
- **Nginx** как reverse proxy с SSL/TLS
- **Portainer** для управления контейнерами
- **Redis** для кэширования и очередей задач

## 🎨 Дизайн-система

### Цветовая палитра БМК
- **Основной красный**: #D32F2F
- **Темно-красный**: #B71C1C  
- **Белый**: #FFFFFF
- **Светло-серый**: #F5F5F5
- **Темно-серый**: #424242

### Компоненты UI
- Кастомная тема Material-UI
- Анимации и переходы
- Адаптивный дизайн для всех устройств
- Темная/светлая тема (опционально)

## 🚀 Быстрый старт

### Предварительные требования
- Docker 20.0+
- Docker Compose 2.0+
- 8 GB RAM (рекомендуется 16 GB)
- 20 GB свободного места на диске

### Установка

1. **Клонирование проекта**
   ```bash
   git clone <repository-url>
   cd bmk-security-cabinet
   ```

2. **Настройка переменных окружения**
   ```bash
   cp .env.example .env
   # Отредактируйте .env файл
   ```

3. **Запуск через Docker Compose**
   ```bash
   docker-compose up -d
   ```

4. **Доступ к приложению**
   - Frontend: http://localhost:3000
   - Backend API: http://localhost:8000
   - API Docs: http://localhost:8000/docs

### Первоначальная настройка

1. Создайте администратора:
   ```bash
   curl -X POST http://localhost:8000/auth/register \
     -H "Content-Type: application/json" \
     -d '{"username":"admin","email":"admin@bmk.local","password":"admin123","role":"super_admin"}'
   ```

2. Войдите в систему с созданными учетными данными

3. Настройте интеграции в разделе "Интеграции"

## 📖 Подробная документация

- [📋 Полная инструкция по развертыванию](DEPLOYMENT.md)
- [🔧 Руководство администратора](docs/ADMIN_GUIDE.md) 
- [👨‍💻 API документация](http://localhost:8000/docs)
- [🎯 Руководство пользователя](docs/USER_GUIDE.md)

## 🔧 Конфигурация

### Переменные окружения

#### Backend
```bash
SECRET_KEY=your-secret-key
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_KEY=your-anon-key
DATABASE_URL=postgresql://user:pass@host:port/db
REDIS_URL=redis://redis:6379
```

#### Frontend
```bash
VITE_API_URL=http://localhost:8000
VITE_SUPABASE_URL=https://your-project.supabase.co
VITE_SUPABASE_ANON_KEY=your-anon-key
```

#### Интеграции
```bash
ZABBIX_URL=http://zabbix-server
ZABBIX_USERNAME=api-user
ZABBIX_PASSWORD=api-password
PROMETHEUS_URL=http://prometheus:9090
NETBOX_URL=http://netbox
NETBOX_TOKEN=your-token
```

## 📊 Мониторинг и метрики

### Встроенный мониторинг
- Health check эндпоинты
- Метрики производительности
- Логирование событий безопасности
- Аудит действий пользователей

### Внешний мониторинг
- Интеграция с Prometheus
- Grafana дашборды (опционально)
- Sentry для отслеживания ошибок
- ELK Stack для анализа логов

## 🔒 Безопасность

### Меры безопасности
- TLS 1.3 шифрование
- JWT токены с коротким временем жизни
- Rate limiting для API
- SQL injection защита через ORM
- XSS защита через CSP headers
- CSRF токены для форм

### Соответствие стандартам
- OWASP Top 10
- ISO 27001
- Требования ЦБ РФ
- NIST Cybersecurity Framework

## 🧪 Тестирование

### Запуск тестов
```bash
# Backend тесты
cd backend && python -m pytest

# Frontend тесты  
cd frontend && npm test

# E2E тесты
npm run test:e2e
```

### Покрытие кода
- Backend: pytest-cov
- Frontend: Jest coverage reports

## 🚀 Развертывание в продакшн

### Рекомендации для продакшн
1. Настройте HTTPS с валидными SSL сертификатами
2. Используйте внешний PostgreSQL и Redis
3. Настройте мониторинг и алерты
4. Регулярное резервное копирование
5. Обновления безопасности

### Docker Swarm / Kubernetes
- Готовые Helm чарты (в разработке)
- Docker Swarm stack файлы
- Горизонтальное масштабирование

## 🤝 Вклад в проект

1. Fork проекта
2. Создайте feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit изменения (`git commit -m 'Add some AmazingFeature'`)
4. Push в branch (`git push origin feature/AmazingFeature`)
5. Откройте Pull Request

## 📄 Лицензия

Распространяется под лицензией MIT. См. `LICENSE` для дополнительной информации.

## 📞 Поддержка и контакты

- 🐛 **Issues**: [GitHub Issues](https://github.com/your-repo/issues)
- 📧 **Email**: security@bmk.local
- 📖 **Wiki**: [Документация проекта](https://github.com/your-repo/wiki)

## 🛣️ Дорожная карта

### v2.1 (Q1 2024)
- [ ] Модуль управления инцидентами
- [ ] Интеграция с SIEM системами
- [ ] Mobile приложение (React Native)
- [ ] Расширенная аналитика

### v2.2 (Q2 2024)  
- [ ] AI-ассистент для анализа уязвимостей
- [ ] Автоматизация реагирования на инциденты
- [ ] Интеграция с ticketing системами
- [ ] Advanced RBAC с тонкими правами

### v3.0 (Q3 2024)
- [ ] Microservices архитектура
- [ ] Kubernetes native deployment
- [ ] Multi-tenant поддержка
- [ ] GraphQL API

## 🙏 Благодарности

- [FastAPI](https://fastapi.tiangolo.com/) за отличный Python web framework
- [React](https://reactjs.org/) за мощную библиотеку UI
- [Material-UI](https://mui.com/) за beautiful design system
- [Supabase](https://supabase.com/) за modern database platform
- [Docker](https://docker.com/) за containerization

---

<div align="center">
  <strong>Сделано с ❤️ для обеспечения безопасности банка БМК</strong>
</div> 