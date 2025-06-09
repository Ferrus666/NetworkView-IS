from pydantic_settings import BaseSettings
from typing import List
import os

class Settings(BaseSettings):
    # Основные настройки
    SECRET_KEY: str = "bmk-security-cabinet-super-secret-key-2024"
    DEBUG: bool = True
    ENVIRONMENT: str = "development"
    
    # Supabase настройки
    SUPABASE_URL: str = "https://sfrijfmrmfkcnmwutfvs.supabase.co"
    SUPABASE_KEY: str = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InNmcmlqZm1ybWZrY25td3V0ZnZzIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NDk0ODkwMDAsImV4cCI6MjA2NTA2NTAwMH0.mqT8Tvh57_mBC3Zu9TSG_-pQl7S_JmHvSb3gCU0R8i0"
    SUPABASE_SERVICE_ROLE_KEY: str = ""
    
    # База данных
    DATABASE_URL: str = "postgresql://postgres.sfrijfmrmfkcnmwutfvs:[Lky8cdya6]@aws-0-eu-north-1.pooler.supabase.com:6543/postgres"
    
    # Redis
    REDIS_URL: str = "redis://redis:6379"
    
    # CORS
    CORS_ORIGINS: List[str] = ["http://localhost:3000", "http://127.0.0.1:3000"]
    
    # JWT
    JWT_SECRET_KEY: str = "bmk-jwt-secret-key-2024"
    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7
    
    # Файлы
    MAX_FILE_SIZE: int = 500 * 1024 * 1024  # 500 MB
    UPLOAD_PATH: str = "/app/uploads"
    ALLOWED_EXTENSIONS: List[str] = [".pdf", ".docx", ".xlsx", ".zip", ".tar.gz", ".drawio", ".vsdx"]
    
    # Интеграции
    # Zabbix
    ZABBIX_URL: str = ""
    ZABBIX_USERNAME: str = ""
    ZABBIX_PASSWORD: str = ""
    ZABBIX_ENABLED: bool = False
    
    # Prometheus
    PROMETHEUS_URL: str = "http://prometheus:9090"
    PROMETHEUS_ENABLED: bool = False
    
    # NetBox
    NETBOX_URL: str = ""
    NETBOX_TOKEN: str = ""
    NETBOX_ENABLED: bool = False
    
    # Lansweeper
    LANSWEEPER_URL: str = ""
    LANSWEEPER_TOKEN: str = ""
    LANSWEEPER_ENABLED: bool = False
    
    # Is-info
    IS_INFO_URL: str = ""
    IS_INFO_TOKEN: str = ""
    IS_INFO_ENABLED: bool = False
    
    # OpenData
    OPENDATA_URL: str = ""
    OPENDATA_TOKEN: str = ""
    OPENDATA_ENABLED: bool = False
    
    # Email
    EMAIL_SMTP_HOST: str = ""
    EMAIL_SMTP_PORT: int = 587
    EMAIL_USERNAME: str = ""
    EMAIL_PASSWORD: str = ""
    EMAIL_FROM: str = "noreply@bmk.local"
    EMAIL_USE_TLS: bool = True
    
    # Telegram
    TELEGRAM_BOT_TOKEN: str = ""
    TELEGRAM_CHAT_ID: str = ""
    TELEGRAM_ENABLED: bool = False
    
    # Логирование
    LOG_LEVEL: str = "INFO"
    LOG_FILE: str = "/app/logs/app.log"
    
    # Celery
    CELERY_BROKER_URL: str = "redis://redis:6379"
    CELERY_RESULT_BACKEND: str = "redis://redis:6379"
    
    # Sentry
    SENTRY_DSN: str = ""
    SENTRY_ENABLED: bool = False
    
    # Метрики
    PROMETHEUS_METRICS_ENABLED: bool = True
    PROMETHEUS_METRICS_PORT: int = 9000
    
    # Безопасность
    BCRYPT_ROUNDS: int = 12
    PASSWORD_MIN_LENGTH: int = 8
    SESSION_TIMEOUT_MINUTES: int = 60
    MAX_LOGIN_ATTEMPTS: int = 5
    LOGIN_ATTEMPT_TIMEOUT_MINUTES: int = 15
    
    # Rate limiting
    RATE_LIMIT_REQUESTS: int = 100
    RATE_LIMIT_WINDOW: int = 60  # seconds
    
    # SAST
    SAST_TIMEOUT_SECONDS: int = 300
    SAST_MAX_FILE_SIZE: int = 100 * 1024 * 1024  # 100 MB
    SAST_SUPPORTED_LANGUAGES: List[str] = ["python", "javascript", "typescript", "java", "go", "php", "c", "cpp"]
    
    class Config:
        env_file = ".env"
        case_sensitive = True

# Создание экземпляра настроек
settings = Settings()

# Банковские цвета БМК
class BMKColors:
    PRIMARY_RED = "#D32F2F"
    SECONDARY_RED = "#B71C1C"
    WHITE = "#FFFFFF"
    LIGHT_GRAY = "#F5F5F5"
    DARK_GRAY = "#424242"
    SUCCESS_GREEN = "#4CAF50"
    WARNING_ORANGE = "#FF9800"
    ERROR_RED = "#F44336"
    INFO_BLUE = "#2196F3"

# Роли пользователей
class UserRoles:
    SUPER_ADMIN = "super_admin"
    ADMIN = "admin"
    USER = "user"
    AUDITOR = "auditor"
    READONLY = "readonly"

# Статусы документов
class DocumentStatus:
    DRAFT = "draft"
    APPROVED = "approved"
    ARCHIVED = "archived"
    UNDER_REVIEW = "under_review"

# Типы интеграций
class IntegrationType:
    ZABBIX = "zabbix"
    PROMETHEUS = "prometheus"
    NETBOX = "netbox"
    LANSWEEPER = "lansweeper"
    IS_INFO = "is_info"
    OPENDATA = "opendata"

# Уровни серьезности уязвимостей
class VulnerabilitySeverity:
    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"
    INFO = "info" 