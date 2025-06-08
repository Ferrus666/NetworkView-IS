from pydantic import BaseModel, EmailStr, validator
from typing import Optional, List, Dict, Any
from datetime import datetime
from enum import Enum

# Базовые схемы
class UserRole(str, Enum):
    USER = "user"
    ADMIN = "admin"
    AUDITOR = "auditor"
    SUPER_ADMIN = "super_admin"

class UserBase(BaseModel):
    username: str
    email: EmailStr
    role: UserRole = UserRole.USER
    is_active: bool = True

class UserCreate(UserBase):
    password: str

class UserResponse(UserBase):
    id: int
    created_at: datetime
    
    class Config:
        from_attributes = True

# Схемы для документов
class DocumentCategory(str, Enum):
    ISO = "ISO"
    GOST = "ГОСТ"
    FZ = "ФЗ"
    ORDERS = "Приказы"
    NIST = "NIST"
    PCI_DSS = "PCI DSS"
    GDPR = "GDPR"
    OWASP = "OWASP"
    CIS = "CIS"
    HIPAA = "HIPAA"
    COBIT = "COBIT"

class DocumentCreate(BaseModel):
    title: str
    category: DocumentCategory
    tags: List[str] = []
    
    @validator('title')
    def title_must_not_be_empty(cls, v):
        if not v.strip():
            raise ValueError('Название документа не может быть пустым')
        return v

class DocumentResponse(BaseModel):
    id: int
    title: str
    filename: str
    category: str
    tags: str  # JSON строка
    content_preview: Optional[str]
    file_size: int
    file_type: str
    uploaded_by: int
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True

class DocumentSearch(BaseModel):
    query: str
    categories: Optional[List[str]] = None
    tags: Optional[List[str]] = None
    date_from: Optional[datetime] = None
    date_to: Optional[datetime] = None

# Схемы для диаграмм
class DiagramCreate(BaseModel):
    name: str
    description: Optional[str] = ""
    
    @validator('name')
    def name_must_not_be_empty(cls, v):
        if not v.strip():
            raise ValueError('Название диаграммы не может быть пустым')
        return v

class DiagramResponse(BaseModel):
    id: int
    name: str
    filename: str
    file_path: str
    file_type: str
    description: Optional[str]
    annotations: Optional[str]  # JSON строка
    uploaded_by: int
    created_at: datetime
    
    class Config:
        from_attributes = True

# Схемы для SAST
class SASTLanguage(str, Enum):
    PYTHON = "python"
    JAVASCRIPT = "javascript"
    JAVA = "java"
    GO = "go"
    PHP = "php"
    C = "c"
    CPP = "cpp"

class SASTScanStatus(str, Enum):
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"

class SASTScanRequest(BaseModel):
    project_name: str
    repository_url: Optional[str] = None
    branch: str = "main"
    language: Optional[SASTLanguage] = None
    
    @validator('project_name')
    def project_name_must_not_be_empty(cls, v):
        if not v.strip():
            raise ValueError('Название проекта не может быть пустым')
        return v

class SASTResultResponse(BaseModel):
    id: int
    project_name: str
    repository_url: Optional[str]
    branch: Optional[str]
    commit_hash: Optional[str]
    scan_results: Optional[str]  # JSON строка
    vulnerabilities_count: int
    critical_count: int
    high_count: int
    medium_count: int
    low_count: int
    scan_status: str
    started_at: datetime
    completed_at: Optional[datetime]
    
    class Config:
        from_attributes = True

class VulnerabilitySummary(BaseModel):
    total: int
    critical: int
    high: int
    medium: int
    low: int
    info: int

# Схемы для мониторинга
class DeviceType(str, Enum):
    ROUTER = "router"
    SWITCH = "switch"
    SERVER = "server"
    WORKSTATION = "workstation"
    PRINTER = "printer"
    FIREWALL = "firewall"
    ACCESS_POINT = "access_point"
    UPS = "ups"
    CAMERA = "camera"
    OTHER = "other"

class DeviceStatus(str, Enum):
    ACTIVE = "active"
    INACTIVE = "inactive"
    ERROR = "error"
    UNKNOWN = "unknown"

class NetworkDeviceCreate(BaseModel):
    name: str
    ip_address: str
    device_type: DeviceType
    
    @validator('name')
    def name_must_not_be_empty(cls, v):
        if not v.strip():
            raise ValueError('Имя устройства не может быть пустым')
        return v
    
    @validator('ip_address')
    def validate_ip_address(cls, v):
        import ipaddress
        try:
            ipaddress.ip_address(v)
        except ValueError:
            raise ValueError('Некорректный IP адрес')
        return v

class NetworkDeviceResponse(BaseModel):
    id: int
    name: str
    ip_address: str
    device_type: str
    status: str
    cpu_usage: float
    memory_usage: float
    network_traffic: float
    last_ping: Optional[datetime]
    created_at: datetime
    
    class Config:
        from_attributes = True

class MonitoringStats(BaseModel):
    total_devices: int
    active_devices: int
    inactive_devices: int
    error_devices: int
    device_types: Dict[str, int]
    average_metrics: Dict[str, float]
    integrations: Dict[str, bool]

class PingResult(BaseModel):
    device_id: int
    ip_address: str
    status: str
    response_time: Optional[float]
    timestamp: str

# Схемы для аудита
class AuditLogResponse(BaseModel):
    id: int
    user_id: int
    action: str
    resource: str
    resource_id: Optional[str]
    details: Optional[str]  # JSON строка
    ip_address: Optional[str]
    user_agent: Optional[str]
    created_at: datetime
    
    class Config:
        from_attributes = True

# Схемы для статистики
class SystemStats(BaseModel):
    total_documents: int
    total_diagrams: int
    total_sast_scans: int
    total_devices: int
    active_users: int
    disk_usage_mb: float
    
class DocumentStats(BaseModel):
    total_documents: int
    by_category: Dict[str, int]
    by_file_type: Dict[str, int]
    total_size_mb: float

class DiagramStats(BaseModel):
    total_diagrams: int
    by_file_type: Dict[str, int]
    supported_formats: List[str]

class SASTStats(BaseModel):
    total_scans: int
    completed_scans: int
    running_scans: int
    failed_scans: int
    vulnerability_summary: VulnerabilitySummary
    supported_languages: List[str]

# Схемы для интеграций
class IntegrationConfig(BaseModel):
    name: str
    enabled: bool
    url: Optional[str]
    status: str
    last_check: Optional[datetime]

class SystemHealth(BaseModel):
    status: str
    timestamp: datetime
    database: str
    redis: str
    disk_space: Dict[str, Any]
    memory_usage: Dict[str, Any]
    integrations: List[IntegrationConfig]

# Схемы для уведомлений
class NotificationCreate(BaseModel):
    title: str
    message: str
    notification_type: str
    recipients: List[str]
    
class NotificationResponse(BaseModel):
    id: int
    title: str
    message: str
    notification_type: str
    status: str
    created_at: datetime
    sent_at: Optional[datetime]
    
    class Config:
        from_attributes = True

# Схемы для экспорта
class ExportRequest(BaseModel):
    resource_type: str  # documents, diagrams, sast_results, devices
    format: str  # json, csv, pdf
    filters: Optional[Dict[str, Any]] = None
    
class ExportResponse(BaseModel):
    export_id: str
    status: str
    file_path: Optional[str]
    created_at: datetime
    expires_at: datetime

# Схемы для настроек
class UserSettings(BaseModel):
    theme: str = "light"  # light, dark
    language: str = "ru"  # ru, en
    notifications_enabled: bool = True
    email_notifications: bool = True
    dashboard_layout: Optional[Dict[str, Any]] = None

class SystemSettings(BaseModel):
    maintenance_mode: bool = False
    max_file_size_mb: int = 50
    session_timeout_minutes: int = 30
    backup_enabled: bool = True
    monitoring_interval_seconds: int = 30

# Схемы для API ключей
class APIKeyCreate(BaseModel):
    name: str
    permissions: List[str]
    expires_at: Optional[datetime] = None

class APIKeyResponse(BaseModel):
    id: int
    name: str
    key_hash: str
    permissions: List[str]
    is_active: bool
    created_at: datetime
    expires_at: Optional[datetime]
    last_used: Optional[datetime]
    
    class Config:
        from_attributes = True

# Схемы для отчетов
class ReportCreate(BaseModel):
    name: str
    report_type: str
    parameters: Dict[str, Any]
    schedule: Optional[str] = None  # cron expression

class ReportResponse(BaseModel):
    id: int
    name: str
    report_type: str
    status: str
    file_path: Optional[str]
    created_at: datetime
    generated_at: Optional[datetime]
    
    class Config:
        from_attributes = True

# Схемы для резервного копирования
class BackupCreate(BaseModel):
    backup_type: str  # full, incremental
    include_files: bool = True
    
class BackupResponse(BaseModel):
    id: int
    backup_type: str
    status: str
    file_path: Optional[str]
    size_mb: Optional[float]
    created_at: datetime
    completed_at: Optional[datetime]
    
    class Config:
        from_attributes = True 