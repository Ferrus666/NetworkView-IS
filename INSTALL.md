# 🚀 Руководство по установке NetworkView IS 2.0

## 📋 Системные требования

### Минимальные требования
- **ОС:** Linux Ubuntu 20.04+, Windows 10+, macOS 10.15+
- **RAM:** 4 GB (рекомендуется 8 GB)
- **Диск:** 10 GB свободного места
- **CPU:** 2 cores (рекомендуется 4 cores)

### Необходимое ПО
- **Python:** 3.11+
- **Node.js:** 18.0+
- **Git:** 2.0+
- **Docker:** 20.0+ (опционально)
- **PostgreSQL:** 12+ (опционально)
- **Redis:** 5.0+ (опционально)

## 🏗️ Способы установки

### 1. Быстрая установка с Docker Compose (Рекомендуется)

```bash
# 1. Клонирование репозитория
git clone https://github.com/your-org/networkview-is.git
cd networkview-is

# 2. Запуск всех сервисов
docker-compose up -d

# 3. Проверка статуса
docker-compose ps

# 4. Просмотр логов
docker-compose logs -f
```

**Доступ к сервисам:**
- Frontend: http://localhost:3000
- Backend API: http://localhost:8000
- API Docs: http://localhost:8000/docs
- Kibana: http://localhost:5601
- Grafana: http://localhost:3001
- Flower: http://localhost:5555

### 2. Установка для разработки

#### 2.1. Клонирование и подготовка

```bash
# Клонирование
git clone https://github.com/your-org/networkview-is.git
cd networkview-is

# Установка всех зависимостей
npm run setup
```

#### 2.2. Настройка Backend

```bash
cd backend

# Создание виртуального окружения
python -m venv venv

# Активация (Linux/Mac)
source venv/bin/activate
# Активация (Windows)
venv\Scripts\activate

# Установка зависимостей
pip install -r requirements.txt

# Создание файла окружения
cp .env.example .env
# Отредактируйте .env файл под ваши настройки

# Инициализация базы данных
alembic upgrade head

# Запуск сервера разработки
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

#### 2.3. Настройка Frontend

```bash
cd frontend

# Установка зависимостей
npm install

# Создание файла окружения
cp .env.example .env.local
# Отредактируйте .env.local под ваши настройки

# Запуск сервера разработки
npm run dev
```

#### 2.4. Одновременный запуск (из корневой директории)

```bash
# Запуск backend и frontend одновременно
npm run dev
```

### 3. Продакшн установка

#### 3.1. Установка на сервер

```bash
# Обновление системы
sudo apt update && sudo apt upgrade -y

# Установка зависимостей
sudo apt install -y python3.11 python3.11-venv nodejs npm postgresql redis-server nginx

# Клонирование проекта
git clone https://github.com/your-org/networkview-is.git
cd networkview-is

# Создание пользователя для приложения
sudo useradd -m -s /bin/bash networkview
sudo chown -R networkview:networkview .
```

#### 3.2. Настройка базы данных

```bash
# Вход в PostgreSQL
sudo -u postgres psql

# Создание БД и пользователя
CREATE DATABASE networkview;
CREATE USER networkview WITH ENCRYPTED PASSWORD 'your_password';
GRANT ALL PRIVILEGES ON DATABASE networkview TO networkview;
\q
```

#### 3.3. Настройка Backend

```bash
# Переход к пользователю приложения
sudo -u networkview -i
cd /path/to/networkview-is/backend

# Создание venv и установка зависимостей
python3.11 -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# Настройка окружения
cat > .env << EOF
SECRET_KEY=your-super-secret-production-key
DATABASE_URL=postgresql://networkview:your_password@localhost:5432/networkview
REDIS_URL=redis://localhost:6379
CORS_ORIGINS=["https://your-domain.com"]
MAX_FILE_SIZE=500
UPLOAD_PATH=/var/www/networkview/uploads
EOF

# Инициализация БД
alembic upgrade head

# Создание системного сервиса
sudo tee /etc/systemd/system/networkview-backend.service > /dev/null << EOF
[Unit]
Description=NetworkView IS Backend
After=network.target

[Service]
Type=exec
User=networkview
Group=networkview
WorkingDirectory=/path/to/networkview-is/backend
Environment=PATH=/path/to/networkview-is/backend/venv/bin
ExecStart=/path/to/networkview-is/backend/venv/bin/uvicorn main:app --host 0.0.0.0 --port 8000
Restart=always

[Install]
WantedBy=multi-user.target
EOF

# Запуск сервиса
sudo systemctl daemon-reload
sudo systemctl enable networkview-backend
sudo systemctl start networkview-backend
```

#### 3.4. Настройка Frontend

```bash
cd /path/to/networkview-is/frontend

# Установка зависимостей
npm ci --production

# Настройка окружения
cat > .env.production << EOF
VITE_API_URL=https://your-domain.com/api
VITE_WS_URL=wss://your-domain.com/ws
EOF

# Сборка
npm run build

# Копирование в nginx
sudo cp -r dist/* /var/www/html/
```

#### 3.5. Настройка Nginx

```bash
sudo tee /etc/nginx/sites-available/networkview << EOF
server {
    listen 80;
    server_name your-domain.com;
    
    # Redirect to HTTPS
    return 301 https://\$server_name\$request_uri;
}

server {
    listen 443 ssl http2;
    server_name your-domain.com;
    
    # SSL Configuration
    ssl_certificate /path/to/ssl/cert.pem;
    ssl_certificate_key /path/to/ssl/key.pem;
    
    # Frontend
    location / {
        root /var/www/html;
        try_files \$uri \$uri/ /index.html;
    }
    
    # Backend API
    location /api/ {
        proxy_pass http://localhost:8000/api/;
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto \$scheme;
    }
    
    # WebSocket
    location /ws/ {
        proxy_pass http://localhost:8000/ws/;
        proxy_http_version 1.1;
        proxy_set_header Upgrade \$http_upgrade;
        proxy_set_header Connection "upgrade";
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
    }
    
    # Static files
    location /uploads/ {
        alias /var/www/networkview/uploads/;
        expires 1y;
    }
}
EOF

# Активация сайта
sudo ln -s /etc/nginx/sites-available/networkview /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl reload nginx
```

## 🔧 Конфигурация

### Backend (.env)

```bash
# Основные настройки
SECRET_KEY=your-super-secret-key
DEBUG=False
ENVIRONMENT=production

# База данных
DATABASE_URL=postgresql://user:password@localhost:5432/networkview

# Redis
REDIS_URL=redis://localhost:6379

# Безопасность
CORS_ORIGINS=["https://your-domain.com"]
ALLOWED_HOSTS=["your-domain.com"]

# Файлы
MAX_FILE_SIZE=500
UPLOAD_PATH=/var/www/networkview/uploads

# Интеграции
ZABBIX_URL=http://zabbix.local
ZABBIX_USERNAME=admin
ZABBIX_PASSWORD=password
ZABBIX_ENABLED=True

PROMETHEUS_URL=http://prometheus.local:9090
PROMETHEUS_ENABLED=True

# Email
EMAIL_SMTP_HOST=smtp.gmail.com
EMAIL_SMTP_PORT=587
EMAIL_USERNAME=your-email@gmail.com
EMAIL_PASSWORD=your-app-password

# Telegram
TELEGRAM_BOT_TOKEN=your-bot-token
TELEGRAM_CHAT_ID=your-chat-id

# Логирование
LOG_LEVEL=INFO
LOG_FILE=/var/log/networkview/app.log

# Celery
CELERY_BROKER_URL=redis://localhost:6379
CELERY_RESULT_BACKEND=redis://localhost:6379
```

### Frontend (.env.production)

```bash
# API
VITE_API_URL=https://your-domain.com/api
VITE_WS_URL=wss://your-domain.com/ws

# Настройки приложения
VITE_APP_NAME=NetworkView IS
VITE_APP_VERSION=2.0.0
VITE_DEFAULT_THEME=light
VITE_DEFAULT_LANGUAGE=ru

# Интеграции
VITE_SENTRY_DSN=your-sentry-dsn
VITE_GOOGLE_ANALYTICS_ID=your-ga-id

# Функциональность
VITE_MAX_FILE_SIZE=524288000
VITE_SUPPORTED_LANGUAGES=["ru", "en"]
```

## 🔍 Проверка установки

### 1. Проверка сервисов

```bash
# Backend
curl http://localhost:8000/health

# Frontend
curl http://localhost:3000

# База данных
psql -h localhost -U networkview -d networkview -c "SELECT version();"

# Redis
redis-cli ping
```

### 2. Проверка логов

```bash
# Backend
tail -f /var/log/networkview/app.log

# Nginx
sudo tail -f /var/log/nginx/error.log

# PostgreSQL
sudo tail -f /var/log/postgresql/postgresql-*.log

# Systemd сервисы
sudo journalctl -u networkview-backend -f
```

### 3. Тест функциональности

```bash
# Создание тестового пользователя
curl -X POST http://localhost:8000/auth/register \
  -H "Content-Type: application/json" \
  -d '{"username": "test", "email": "test@example.com", "password": "test123"}'

# Логин
curl -X POST http://localhost:8000/auth/token \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "username=admin&password=admin123"
```

## 🛠️ Настройка интеграций

### Zabbix

```bash
# В Zabbix создайте API пользователя
# Настройте в .env:
ZABBIX_URL=http://your-zabbix.local
ZABBIX_USERNAME=api_user
ZABBIX_PASSWORD=api_password
ZABBIX_ENABLED=True
```

### Prometheus

```bash
# Настройка Prometheus для сбора метрик
# prometheus.yml
global:
  scrape_interval: 30s

scrape_configs:
  - job_name: 'networkview'
    static_configs:
      - targets: ['localhost:8000']
    metrics_path: '/metrics'
```

### Elasticsearch

```bash
# Установка Elasticsearch
wget -qO - https://artifacts.elastic.co/GPG-KEY-elasticsearch | sudo apt-key add -
echo "deb https://artifacts.elastic.co/packages/8.x/apt stable main" | sudo tee /etc/apt/sources.list.d/elastic-8.x.list
sudo apt update && sudo apt install elasticsearch

# Настройка
sudo systemctl enable elasticsearch
sudo systemctl start elasticsearch

# Проверка
curl http://localhost:9200
```

## 🔐 Настройка безопасности

### SSL/TLS сертификат

```bash
# Получение бесплатного SSL от Let's Encrypt
sudo apt install certbot python3-certbot-nginx

# Получение сертификата
sudo certbot --nginx -d your-domain.com

# Автоматическое обновление
sudo crontab -e
# Добавить: 0 12 * * * /usr/bin/certbot renew --quiet
```

### Настройка firewall

```bash
# UFW
sudo ufw enable
sudo ufw allow ssh
sudo ufw allow 80/tcp
sudo ufw allow 443/tcp
sudo ufw deny 8000/tcp  # Закрыть прямой доступ к API
sudo ufw status
```

### Backup

```bash
# Создание скрипта резервного копирования
cat > /usr/local/bin/networkview-backup.sh << 'EOF'
#!/bin/bash
BACKUP_DIR="/var/backups/networkview"
DATE=$(date +%Y%m%d_%H%M%S)

# Создание директории
mkdir -p $BACKUP_DIR

# Backup базы данных
pg_dump -U networkview networkview > $BACKUP_DIR/db_$DATE.sql

# Backup файлов
tar -czf $BACKUP_DIR/uploads_$DATE.tar.gz /var/www/networkview/uploads

# Удаление старых backup'ов (старше 30 дней)
find $BACKUP_DIR -type f -mtime +30 -delete

echo "Backup completed: $DATE"
EOF

chmod +x /usr/local/bin/networkview-backup.sh

# Добавление в cron
sudo crontab -e
# Добавить: 0 2 * * * /usr/local/bin/networkview-backup.sh
```

## 🐛 Устранение неполадок

### Частые проблемы

1. **Backend не запускается**
   ```bash
   # Проверка зависимостей
   pip check
   
   # Проверка портов
   sudo netstat -tlnp | grep :8000
   
   # Проверка логов
   journalctl -u networkview-backend
   ```

2. **Frontend не собирается**
   ```bash
   # Очистка кэша
   npm cache clean --force
   rm -rf node_modules package-lock.json
   npm install
   
   # Проверка TypeScript
   npm run type-check
   ```

3. **База данных недоступна**
   ```bash
   # Проверка статуса PostgreSQL
   sudo systemctl status postgresql
   
   # Проверка подключения
   pg_isready -h localhost -p 5432
   
   # Проверка логов
   sudo tail -f /var/log/postgresql/postgresql-*.log
   ```

4. **Redis недоступен**
   ```bash
   # Проверка статуса
   sudo systemctl status redis-server
   
   # Проверка подключения
   redis-cli ping
   
   # Проверка конфигурации
   redis-cli config get "*"
   ```

### Мониторинг

```bash
# Установка htop для мониторинга ресурсов
sudo apt install htop

# Мониторинг дискового пространства
df -h

# Мониторинг памяти
free -h

# Мониторинг процессов
ps aux | grep -E "(uvicorn|nginx|postgres|redis)"
```

## 📞 Поддержка

При возникновении проблем:

1. Проверьте [документацию](./README.md)
2. Изучите [известные проблемы](https://github.com/your-org/networkview-is/issues)
3. Создайте [новый issue](https://github.com/your-org/networkview-is/issues/new)
4. Обратитесь в [поддержку](mailto:support@networkview.local)

## 🎉 Поздравляем!

Если вы дошли до этого момента, NetworkView IS 2.0 успешно установлен и готов к использованию!

**Следующие шаги:**
1. Войдите в систему (admin/admin123)
2. Измените пароль администратора
3. Настройте интеграции
4. Загрузите первые документы
5. Добавьте сетевые устройства

**Полезные ссылки:**
- [Руководство пользователя](./docs/user-guide.md)
- [Руководство администратора](./docs/admin-guide.md)
- [API документация](http://localhost:8000/docs) 