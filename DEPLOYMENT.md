# 🚀 Инструкция по развертыванию BMK Security Cabinet

## 📋 Обзор

Данная инструкция описывает пошаговое развертывание веб-приложения "Личный кабинет инженера ИБ банка БМК" через Docker Compose и Portainer с использованием базы данных Supabase.

## 🎯 Системные требования

### Минимальные требования
- **ОС:** Windows 10/11, Linux Ubuntu 20.04+, macOS 10.15+
- **RAM:** 8 GB (рекомендуется 16 GB)
- **Диск:** 20 GB свободного места
- **CPU:** 4 cores (рекомендуется 8 cores)

### Необходимое ПО
- **Docker:** 20.0+
- **Docker Compose:** 2.0+
- **Portainer:** 2.19+ (опционально)

## 🔧 Подготовка к установке

### 1. Установка Docker

#### Windows 10/11
1. Скачайте Docker Desktop с официального сайта: https://www.docker.com/products/docker-desktop/
2. Запустите установщик и следуйте инструкциям
3. Перезагрузите компьютер
4. Проверьте установку:
   ```cmd
   docker --version
   docker-compose --version
   ```

#### Linux (Ubuntu/Debian)
```bash
# Обновление системы
sudo apt update && sudo apt upgrade -y

# Установка Docker
curl -fsSL https://get.docker.com -o get-docker.sh
sudo sh get-docker.sh

# Добавление пользователя в группу docker
sudo usermod -aG docker $USER

# Установка Docker Compose
sudo apt install docker-compose-plugin

# Перезагрузка для применения изменений
sudo reboot

# Проверка установки
docker --version
docker compose version
```

#### macOS
1. Скачайте Docker Desktop для Mac: https://www.docker.com/products/docker-desktop/
2. Установите приложение
3. Запустите Docker Desktop
4. Проверьте установку в терминале:
   ```bash
   docker --version
   docker-compose --version
   ```

### 2. Установка Portainer (опционально)

```bash
# Создание volume для Portainer
docker volume create portainer_data

# Запуск Portainer
docker run -d -p 8080:8000 -p 9443:9443 --name portainer --restart=always \
  -v /var/run/docker.sock:/var/run/docker.sock \
  -v portainer_data:/data \
  portainer/portainer-ce:latest
```

Доступ к Portainer: https://localhost:9443

## 🗂️ Структура проекта

Убедитесь, что у вас есть следующая структура файлов:

```
bmk-security-cabinet/
├── docker-compose.yml
├── backend/
│   ├── Dockerfile
│   ├── requirements.txt
│   ├── main.py
│   ├── config.py
│   ├── database.py
│   └── routers/
│       ├── auth.py
│       ├── documents.py
│       ├── sast.py
│       ├── monitoring.py
│       ├── network.py
│       └── integrations.py
├── frontend/
│   ├── Dockerfile
│   ├── package.json
│   ├── vite.config.ts
│   └── src/
│       ├── main.tsx
│       ├── App.tsx
│       ├── theme/
│       ├── contexts/
│       ├── services/
│       └── pages/
├── nginx/
│   └── nginx.conf
└── uploads/
```

## 🐳 Развертывание через Docker Compose

### 1. Клонирование или создание проекта

```bash
# Если проект в Git
git clone <repository-url>
cd bmk-security-cabinet

# Или создание новой директории
mkdir bmk-security-cabinet
cd bmk-security-cabinet
```

### 2. Создание переменных окружения

Создайте файл `.env` в корне проекта:

```bash
# Backend
SECRET_KEY=bmk-security-cabinet-super-secret-key-2024
SUPABASE_URL=https://sfrijfmrmfkcnmwutfvs.supabase.co
SUPABASE_KEY=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InNmcmlqZm1ybWZrY25td3V0ZnZzIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NDk0ODkwMDAsImV4cCI6MjA2NTA2NTAwMH0.mqT8Tvh57_mBC3Zu9TSG_-pQl7S_JmHvSb3gCU0R8i0
DATABASE_URL=postgresql://postgres.sfrijfmrmfkcnmwutfvs:[Lky8cdya6]@aws-0-eu-north-1.pooler.supabase.com:6543/postgres
REDIS_URL=redis://redis:6379

# Frontend
VITE_API_URL=http://localhost:8000
VITE_SUPABASE_URL=https://sfrijfmrmfkcnmwutfvs.supabase.co
VITE_SUPABASE_ANON_KEY=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InNmcmlqZm1ybWZrY25td3V0ZnZzIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NDk0ODkwMDAsImV4cCI6MjA2NTA2NTAwMH0.mqT8Tvh57_mBC3Zu9TSG_-pQl7S_JmHvSb3gCU0R8i0

# Интеграции (опционально)
ZABBIX_URL=
ZABBIX_USERNAME=
ZABBIX_PASSWORD=
PROMETHEUS_URL=http://prometheus:9090
NETBOX_URL=
NETBOX_TOKEN=
```

### 3. Создание директорий

```bash
# Создание необходимых директорий
mkdir -p uploads
mkdir -p logs
mkdir -p nginx

# Установка прав
chmod 755 uploads logs
```

### 4. Запуск приложения

```bash
# Сборка и запуск всех сервисов
docker-compose up -d

# Проверка статуса
docker-compose ps

# Просмотр логов
docker-compose logs -f

# Просмотр логов конкретного сервиса
docker-compose logs -f backend
docker-compose logs -f frontend
```

### 5. Проверка работоспособности

После запуска проверьте доступность сервисов:

- **Frontend:** http://localhost:3000
- **Backend API:** http://localhost:8000
- **API Docs:** http://localhost:8000/docs
- **Health Check:** http://localhost:8000/health

## 🌐 Развертывание через Portainer

### 1. Создание стека в Portainer

1. Откройте Portainer: https://localhost:9443
2. Перейдите в **Stacks** → **Add stack**
3. Введите имя стека: `bmk-security-cabinet`
4. Вставьте содержимое `docker-compose.yml`
5. В разделе **Environment variables** добавьте переменные из `.env`
6. Нажмите **Deploy the stack**

### 2. Настройка переменных окружения в Portainer

В веб-интерфейсе Portainer добавьте следующие переменные:

```
SECRET_KEY=bmk-security-cabinet-super-secret-key-2024
SUPABASE_URL=https://sfrijfmrmfkcnmwutfvs.supabase.co
SUPABASE_KEY=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InNmcmlqZm1ybWZrY25td3V0ZnZzIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NDk0ODkwMDAsImV4cCI6MjA2NTA2NTAwMH0.mqT8Tvh57_mBC3Zu9TSG_-pQl7S_JmHvSb3gCU0R8i0
DATABASE_URL=postgresql://postgres.sfrijfmrmfkcnmwutfvs:[Lky8cdya6]@aws-0-eu-north-1.pooler.supabase.com:6543/postgres
REDIS_URL=redis://redis:6379
VITE_API_URL=http://localhost:8000
VITE_SUPABASE_URL=https://sfrijfmrmfkcnmwutfvs.supabase.co
VITE_SUPABASE_ANON_KEY=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InNmcmlqZm1ybWZrY25td3V0ZnZzIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NDk0ODkwMDAsImV4cCI6MjA2NTA2NTAwMH0.mqT8Tvh57_mBC3Zu9TSG_-pQl7S_JmHvSb3gCU0R8i0
```

### 3. Мониторинг через Portainer

После развертывания в Portainer вы можете:

- Просматривать статус контейнеров
- Мониторить использование ресурсов
- Просматривать логи в режиме реального времени
- Управлять контейнерами (restart, stop, start)
- Обновлять стек

## 🗄️ Настройка базы данных Supabase

### 1. Создание таблиц

Таблицы создаются автоматически при первом запуске backend. Если нужно создать их вручную, выполните следующие SQL команды в Supabase SQL Editor:

```sql
-- Пользователи
CREATE TABLE IF NOT EXISTS users (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    email VARCHAR(255) UNIQUE NOT NULL,
    username VARCHAR(100) UNIQUE NOT NULL,
    hashed_password TEXT NOT NULL,
    role VARCHAR(50) DEFAULT 'user',
    is_active BOOLEAN DEFAULT true,
    is_verified BOOLEAN DEFAULT false,
    last_login TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Документы
CREATE TABLE IF NOT EXISTS documents (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    title VARCHAR(255) NOT NULL,
    description TEXT,
    category VARCHAR(100),
    file_url TEXT NOT NULL,
    file_name VARCHAR(255),
    file_size INTEGER,
    version VARCHAR(20) DEFAULT '1.0',
    author_id UUID REFERENCES users(id),
    status VARCHAR(50) DEFAULT 'draft',
    tags TEXT[],
    download_count INTEGER DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Результаты SAST
CREATE TABLE IF NOT EXISTS sast_results (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    scan_id VARCHAR(100) UNIQUE NOT NULL,
    repository_url TEXT,
    commit_id VARCHAR(100),
    branch VARCHAR(100),
    vulnerabilities JSONB NOT NULL,
    summary JSONB,
    report_url TEXT,
    status VARCHAR(50) DEFAULT 'completed',
    scan_duration INTEGER,
    author_id UUID REFERENCES users(id),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Сетевые устройства
CREATE TABLE IF NOT EXISTS network_devices (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    name VARCHAR(255) NOT NULL,
    ip_address INET,
    device_type VARCHAR(100),
    os_version VARCHAR(100),
    status VARCHAR(50) DEFAULT 'unknown',
    location VARCHAR(255),
    vendor VARCHAR(100),
    model VARCHAR(100),
    serial_number VARCHAR(100),
    last_seen TIMESTAMP,
    metadata JSONB,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Логи мониторинга
CREATE TABLE IF NOT EXISTS monitoring_logs (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    device_id VARCHAR(100),
    device_name VARCHAR(255),
    metric_name VARCHAR(100),
    metric_value DECIMAL,
    status VARCHAR(50),
    alert_level VARCHAR(20),
    message TEXT,
    source VARCHAR(50),
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Логи аудита
CREATE TABLE IF NOT EXISTS audit_logs (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID REFERENCES users(id),
    action VARCHAR(100) NOT NULL,
    resource_type VARCHAR(50),
    resource_id UUID,
    details JSONB,
    ip_address INET,
    user_agent TEXT,
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

### 2. Создание администратора

После запуска приложения создайте первого пользователя-администратора:

```bash
# Через API
curl -X POST http://localhost:8000/auth/register \
  -H "Content-Type: application/json" \
  -d '{
    "username": "admin",
    "email": "admin@bmk.local",
    "password": "admin123",
    "role": "super_admin"
  }'
```

## 🔧 Настройка интеграций

### 1. Zabbix

```bash
# В .env файле
ZABBIX_URL=http://your-zabbix-server
ZABBIX_USERNAME=api_user
ZABBIX_PASSWORD=api_password
ZABBIX_ENABLED=true
```

### 2. Prometheus

```bash
# В .env файле
PROMETHEUS_URL=http://your-prometheus:9090
PROMETHEUS_ENABLED=true
```

### 3. NetBox

```bash
# В .env файле
NETBOX_URL=http://your-netbox
NETBOX_TOKEN=your-api-token
NETBOX_ENABLED=true
```

## 🐛 Устранение неполадок

### 1. Проблемы с Docker

```bash
# Проверка статуса Docker
docker info

# Очистка системы Docker
docker system prune -a

# Перезапуск Docker (Windows/Mac)
# Через Docker Desktop: Settings → Troubleshoot → Reset to factory defaults

# Перезапуск Docker (Linux)
sudo systemctl restart docker
```

### 2. Проблемы с контейнерами

```bash
# Просмотр логов
docker-compose logs backend
docker-compose logs frontend
docker-compose logs redis

# Перезапуск сервисов
docker-compose restart backend
docker-compose restart frontend

# Полная пересборка
docker-compose down
docker-compose build --no-cache
docker-compose up -d
```

### 3. Проблемы с базой данных

```bash
# Проверка подключения к Supabase
docker-compose exec backend python -c "
from database import supabase
print('Supabase connection:', supabase.table('users').select('*', count='exact').execute())
"
```

### 4. Проблемы с портами

```bash
# Проверка занятых портов
netstat -tulpn | grep :3000
netstat -tulpn | grep :8000

# Windows
netstat -ano | findstr :3000
netstat -ano | findstr :8000
```

## 📊 Мониторинг и обслуживание

### 1. Просмотр метрик

```bash
# Использование ресурсов
docker stats

# Дисковое пространство
docker system df
```

### 2. Логирование

```bash
# Настройка ротации логов
echo '{
  "log-driver": "json-file",
  "log-opts": {
    "max-size": "10m",
    "max-file": "3"
  }
}' | sudo tee /etc/docker/daemon.json

sudo systemctl restart docker
```

### 3. Резервное копирование

```bash
# Backup volumes
docker run --rm -v bmk-security-cabinet_redis_data:/data -v $(pwd):/backup alpine tar czf /backup/redis_backup.tar.gz -C /data .

# Backup uploads
tar czf uploads_backup.tar.gz uploads/
```

## 🚀 Обновление приложения

### 1. Обновление через Docker Compose

```bash
# Остановка сервисов
docker-compose down

# Обновление кода (если из Git)
git pull

# Пересборка и запуск
docker-compose build --no-cache
docker-compose up -d
```

### 2. Обновление через Portainer

1. В Portainer перейдите к стеку
2. Нажмите **Editor**
3. Обновите конфигурацию
4. Нажмите **Update the stack**

## 🔐 Безопасность

### 1. Настройка HTTPS (продакшн)

```bash
# Получение SSL сертификата
sudo apt install certbot
sudo certbot certonly --standalone -d your-domain.com

# Обновление nginx.conf для HTTPS
# Раскомментировать SSL секцию в nginx/nginx.conf
```

### 2. Firewall

```bash
# Ubuntu/Debian
sudo ufw enable
sudo ufw allow 22
sudo ufw allow 80
sudo ufw allow 443
sudo ufw deny 3000  # Закрыть прямой доступ к frontend
sudo ufw deny 8000  # Закрыть прямой доступ к API
```

## 📞 Поддержка

При возникновении проблем:

1. Проверьте логи: `docker-compose logs -f`
2. Убедитесь в правильности переменных окружения
3. Проверьте доступность Supabase
4. Обратитесь к документации Docker и Portainer

## ✅ Контрольный список установки

- [ ] Docker и Docker Compose установлены
- [ ] Portainer установлен (опционально)
- [ ] Файлы проекта созданы
- [ ] Переменные окружения настроены
- [ ] Контейнеры запущены успешно
- [ ] Frontend доступен на http://localhost:3000
- [ ] Backend API доступен на http://localhost:8000
- [ ] Создан администратор системы
- [ ] Протестированы основные функции

## 🎉 Поздравляем!

Ваш личный кабинет инженера ИБ банка БМК успешно развернут и готов к использованию!

**Стартовые учетные данные:**
- URL: http://localhost:3000
- Email: admin@bmk.local
- Пароль: admin123 (рекомендуется сменить) 