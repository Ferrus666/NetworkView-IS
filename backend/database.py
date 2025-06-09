from supabase import create_client, Client
from config import settings
import asyncio
import json
from typing import Optional, Dict, Any, List

# Инициализация Supabase клиента
supabase: Client = create_client(settings.SUPABASE_URL, settings.SUPABASE_KEY)

async def init_db():
    """Инициализация базы данных и создание необходимых таблиц"""
    try:
        # Создание таблиц если они не существуют
        await create_tables()
        print("✅ База данных инициализирована")
    except Exception as e:
        print(f"❌ Ошибка инициализации БД: {e}")

async def create_tables():
    """Создание необходимых таблиц в Supabase"""
    
    # Пользователи
    users_table = """
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
    """
    
    # Документы
    documents_table = """
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
    """
    
    # Чек-листы
    checklists_table = """
    CREATE TABLE IF NOT EXISTS checklists (
        id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
        title VARCHAR(255) NOT NULL,
        standard VARCHAR(100) NOT NULL,
        items JSONB NOT NULL,
        status VARCHAR(50) DEFAULT 'in_progress',
        author_id UUID REFERENCES users(id),
        assignee_id UUID REFERENCES users(id),
        completion_percentage INTEGER DEFAULT 0,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );
    """
    
    # SAST результаты
    sast_results_table = """
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
    """
    
    # Мониторинг логи
    monitoring_logs_table = """
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
    """
    
    # Сетевые устройства
    network_devices_table = """
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
    """
    
    # Аннотации сети
    network_annotations_table = """
    CREATE TABLE IF NOT EXISTS network_annotations (
        id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
        device_id UUID REFERENCES network_devices(id),
        annotation_type VARCHAR(50),
        title VARCHAR(255),
        content TEXT,
        position_x DECIMAL,
        position_y DECIMAL,
        author_id UUID REFERENCES users(id),
        is_visible BOOLEAN DEFAULT true,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );
    """
    
    # Интеграции
    integrations_table = """
    CREATE TABLE IF NOT EXISTS integrations (
        id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
        name VARCHAR(100) NOT NULL,
        type VARCHAR(50) NOT NULL,
        url TEXT NOT NULL,
        credentials JSONB,
        settings JSONB,
        is_active BOOLEAN DEFAULT true,
        last_sync TIMESTAMP,
        status VARCHAR(50) DEFAULT 'inactive',
        error_message TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );
    """
    
    # Логи аудита
    audit_logs_table = """
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
    """
    
    # Логи безопасности
    security_logs_table = """
    CREATE TABLE IF NOT EXISTS security_logs (
        id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
        event_type VARCHAR(100) NOT NULL,
        severity VARCHAR(20) DEFAULT 'info',
        user_id UUID REFERENCES users(id),
        ip_address INET,
        user_agent TEXT,
        details JSONB,
        resolved BOOLEAN DEFAULT false,
        timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );
    """
    
    # Уведомления
    notifications_table = """
    CREATE TABLE IF NOT EXISTS notifications (
        id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
        user_id UUID REFERENCES users(id),
        title VARCHAR(255) NOT NULL,
        message TEXT NOT NULL,
        type VARCHAR(50) DEFAULT 'info',
        is_read BOOLEAN DEFAULT false,
        action_url TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );
    """
    
    tables = [
        users_table,
        documents_table,
        checklists_table,
        sast_results_table,
        monitoring_logs_table,
        network_devices_table,
        network_annotations_table,
        integrations_table,
        audit_logs_table,
        security_logs_table,
        notifications_table
    ]
    
    # Выполнение SQL через Supabase RPC
    for table_sql in tables:
        try:
            # Используем RPC функцию для выполнения SQL
            result = supabase.rpc('exec_sql', {'sql': table_sql}).execute()
            print(f"✅ Таблица создана/обновлена")
        except Exception as e:
            print(f"⚠️ Таблица уже существует или ошибка: {e}")

class DatabaseManager:
    """Менеджер для работы с базой данных"""
    
    def __init__(self):
        self.client = supabase
    
    async def create_user(self, user_data: Dict[str, Any]) -> Dict[str, Any]:
        """Создание пользователя"""
        try:
            result = self.client.table('users').insert(user_data).execute()
            return result.data[0] if result.data else None
        except Exception as e:
            print(f"Ошибка создания пользователя: {e}")
            return None
    
    async def get_user_by_email(self, email: str) -> Optional[Dict[str, Any]]:
        """Получение пользователя по email"""
        try:
            result = self.client.table('users').select('*').eq('email', email).execute()
            return result.data[0] if result.data else None
        except Exception as e:
            print(f"Ошибка получения пользователя: {e}")
            return None
    
    async def create_document(self, document_data: Dict[str, Any]) -> Dict[str, Any]:
        """Создание документа"""
        try:
            result = self.client.table('documents').insert(document_data).execute()
            return result.data[0] if result.data else None
        except Exception as e:
            print(f"Ошибка создания документа: {e}")
            return None
    
    async def get_documents(self, limit: int = 50, offset: int = 0) -> List[Dict[str, Any]]:
        """Получение списка документов"""
        try:
            result = self.client.table('documents').select('*').range(offset, offset + limit - 1).execute()
            return result.data or []
        except Exception as e:
            print(f"Ошибка получения документов: {e}")
            return []
    
    async def create_sast_result(self, sast_data: Dict[str, Any]) -> Dict[str, Any]:
        """Создание результата SAST анализа"""
        try:
            result = self.client.table('sast_results').insert(sast_data).execute()
            return result.data[0] if result.data else None
        except Exception as e:
            print(f"Ошибка создания SAST результата: {e}")
            return None
    
    async def log_audit_event(self, audit_data: Dict[str, Any]) -> Dict[str, Any]:
        """Логирование события аудита"""
        try:
            result = self.client.table('audit_logs').insert(audit_data).execute()
            return result.data[0] if result.data else None
        except Exception as e:
            print(f"Ошибка логирования аудита: {e}")
            return None
    
    async def log_security_event(self, security_data: Dict[str, Any]) -> Dict[str, Any]:
        """Логирование события безопасности"""
        try:
            result = self.client.table('security_logs').insert(security_data).execute()
            return result.data[0] if result.data else None
        except Exception as e:
            print(f"Ошибка логирования безопасности: {e}")
            return None
    
    async def create_notification(self, notification_data: Dict[str, Any]) -> Dict[str, Any]:
        """Создание уведомления"""
        try:
            result = self.client.table('notifications').insert(notification_data).execute()
            return result.data[0] if result.data else None
        except Exception as e:
            print(f"Ошибка создания уведомления: {e}")
            return None

# Создание экземпляра менеджера БД
db = DatabaseManager() 