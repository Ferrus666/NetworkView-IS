from fastapi import FastAPI, Depends, HTTPException, status, File, UploadFile, Form
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhostmiddleware import TrustedHostMiddleware
from fastapi.responses import JSONResponse, FileResponse
from fastapi.staticfiles import StaticFiles
from sqlalchemy import create_engine, Column, Integer, String, DateTime, Boolean, Text, Float
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session
from passlib.context import CryptContext
from jose import JWTError, jwt
from datetime import datetime, timedelta
from typing import Optional, List, Dict, Any
import os
import uuid
import aiofiles
import asyncio
import logging
import redis
import json
from pathlib import Path
import zipfile
import shutil
from contextlib import asynccontextmanager
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
import uvicorn

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[
        logging.FileHandler("app.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# Конфигурация
SECRET_KEY = os.getenv("SECRET_KEY", "your-super-secret-key-change-in-production")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./networkview.db")
REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379")
UPLOAD_DIR = Path("uploads")
MAX_FILE_SIZE = 500 * 1024 * 1024  # 500MB

# Создание директорий
UPLOAD_DIR.mkdir(exist_ok=True)
(UPLOAD_DIR / "documents").mkdir(exist_ok=True)
(UPLOAD_DIR / "diagrams").mkdir(exist_ok=True)
(UPLOAD_DIR / "code").mkdir(exist_ok=True)

# База данных
engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

# Redis для кэширования
try:
    redis_client = redis.from_url(REDIS_URL, decode_responses=True)
    redis_client.ping()
    logger.info("Redis подключен успешно")
except Exception as e:
    logger.warning(f"Redis недоступен: {e}")
    redis_client = None

# Модели данных
class User(Base):
    __tablename__ = "users"
    
    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, unique=True, index=True)
    email = Column(String, unique=True, index=True)
    hashed_password = Column(String)
    role = Column(String, default="user")  # user, admin, auditor, super_admin
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)

class Document(Base):
    __tablename__ = "documents"
    
    id = Column(Integer, primary_key=True, index=True)
    title = Column(String, index=True)
    filename = Column(String)
    file_path = Column(String)
    category = Column(String)  # ISO, ГОСТ, ФЗ, etc.
    tags = Column(Text)  # JSON array
    content_preview = Column(Text)
    file_size = Column(Integer)
    file_type = Column(String)
    uploaded_by = Column(Integer)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow)

class NetworkDevice(Base):
    __tablename__ = "network_devices"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, index=True)
    ip_address = Column(String, index=True)
    device_type = Column(String)  # router, switch, server, etc.
    status = Column(String, default="unknown")  # active, inactive, error
    cpu_usage = Column(Float, default=0.0)
    memory_usage = Column(Float, default=0.0)
    network_traffic = Column(Float, default=0.0)
    last_ping = Column(DateTime)
    created_at = Column(DateTime, default=datetime.utcnow)

class Diagram(Base):
    __tablename__ = "diagrams"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, index=True)
    filename = Column(String)
    file_path = Column(String)
    file_type = Column(String)  # drawio, visio
    description = Column(Text)
    annotations = Column(Text)  # JSON
    uploaded_by = Column(Integer)
    created_at = Column(DateTime, default=datetime.utcnow)

class SASTResult(Base):
    __tablename__ = "sast_results"
    
    id = Column(Integer, primary_key=True, index=True)
    project_name = Column(String, index=True)
    repository_url = Column(String)
    branch = Column(String)
    commit_hash = Column(String)
    scan_results = Column(Text)  # JSON
    vulnerabilities_count = Column(Integer, default=0)
    critical_count = Column(Integer, default=0)
    high_count = Column(Integer, default=0)
    medium_count = Column(Integer, default=0)
    low_count = Column(Integer, default=0)
    scan_status = Column(String, default="pending")  # pending, running, completed, failed
    started_at = Column(DateTime, default=datetime.utcnow)
    completed_at = Column(DateTime)

class AuditLog(Base):
    __tablename__ = "audit_logs"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer)
    action = Column(String)
    resource = Column(String)
    resource_id = Column(String)
    details = Column(Text)  # JSON
    ip_address = Column(String)
    user_agent = Column(String)
    created_at = Column(DateTime, default=datetime.utcnow)

# Создание таблиц
Base.metadata.create_all(bind=engine)

# Аутентификация
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="auth/token")

def get_password_hash(password):
    return pwd_context.hash(password)

def verify_password(plain_password, hashed_password):
    return pwd_context.verify(plain_password, hashed_password)

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=15)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# Lifecycle события
@asynccontextmanager
async def lifespan(app: FastAPI):
    # Инициализация при запуске
    await init_db()
    print("🚀 Приложение запущено")
    
    # Создание супер администратора по умолчанию
    db = SessionLocal()
    try:
        admin_user = db.query(User).filter(User.username == "admin").first()
        if not admin_user:
            admin_user = User(
                username="admin",
                email="admin@networkview.local",
                hashed_password=get_password_hash("admin123"),
                role="super_admin"
            )
            db.add(admin_user)
            db.commit()
            logger.info("Супер администратор создан: admin/admin123")
    finally:
        db.close()
    
    yield
    
    # Очистка при остановке
    print("🛑 Приложение остановлено")

# Создание FastAPI приложения
app = FastAPI(
    title="BMK Security Cabinet",
    description="Личный кабинет инженера по информационной безопасности банка БМК",
    version="2.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan
)

# Настройка CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Подключение статических файлов
app.mount("/uploads", StaticFiles(directory="uploads"), name="uploads")

# Безопасность
security = HTTPBearer()

async def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)):
    """Получение текущего пользователя по JWT токену"""
    try:
        from auth.jwt_handler import verify_token
        payload = verify_token(credentials.credentials)
        return payload
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token",
            headers={"WWW-Authenticate": "Bearer"},
        )

# Подключение роутеров
app.include_router(auth.router, prefix="/auth", tags=["Authentication"])
app.include_router(documents.router, prefix="/api/documents", tags=["Documents"])
app.include_router(sast.router, prefix="/api/sast", tags=["SAST Analysis"])
app.include_router(monitoring.router, prefix="/api/monitoring", tags=["Network Monitoring"])
app.include_router(network.router, prefix="/api/network", tags=["Network Visualization"])
app.include_router(integrations.router, prefix="/api/integrations", tags=["Integrations"])

# Основные эндпоинты
@app.get("/")
async def root():
    """Главная страница API"""
    return {
        "message": "BMK Security Cabinet API",
        "version": "2.0.0",
        "docs": "/docs",
        "redoc": "/redoc"
    }

@app.get("/health")
async def health_check():
    """Проверка состояния сервиса"""
    try:
        # Проверка Redis
        redis_status = redis_client.ping()
        
        # Проверка Supabase
        from database import supabase
        supabase_status = True  # Здесь можно добавить проверку подключения
        
        return {
            "status": "healthy",
            "redis": "ok" if redis_status else "error",
            "supabase": "ok" if supabase_status else "error",
            "version": "2.0.0"
        }
    except Exception as e:
        return {
            "status": "unhealthy",
            "error": str(e)
        }

@app.get("/api/user/profile")
async def get_user_profile(current_user = Depends(get_current_user)):
    """Получение профиля пользователя"""
    return {
        "user_id": current_user.get("sub"),
        "email": current_user.get("email"),
        "role": current_user.get("role", "user")
    }

# Эндпоинт для WebSocket (мониторинг в реальном времени)
from fastapi import WebSocket, WebSocketDisconnect
import json
import asyncio

class ConnectionManager:
    def __init__(self):
        self.active_connections: list[WebSocket] = []

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)

    def disconnect(self, websocket: WebSocket):
        self.active_connections.remove(websocket)

    async def send_personal_message(self, message: str, websocket: WebSocket):
        await websocket.send_text(message)

    async def broadcast(self, message: str):
        for connection in self.active_connections:
            try:
                await connection.send_text(message)
            except:
                await self.disconnect(connection)

manager = ConnectionManager()

@app.websocket("/ws/monitoring")
async def websocket_endpoint(websocket: WebSocket):
    await manager.connect(websocket)
    try:
        while True:
            # Симуляция данных мониторинга
            monitoring_data = {
                "timestamp": "2024-01-15T10:30:00Z",
                "devices": [
                    {"id": 1, "name": "Server-01", "status": "online", "cpu": 45.2, "ram": 67.8},
                    {"id": 2, "name": "Router-01", "status": "online", "cpu": 23.1, "ram": 34.5},
                    {"id": 3, "name": "Switch-01", "status": "offline", "cpu": 0, "ram": 0}
                ],
                "network_traffic": {
                    "incoming": 1024.5,
                    "outgoing": 756.3
                }
            }
            await websocket.send_text(json.dumps(monitoring_data))
            await asyncio.sleep(5)  # Отправка данных каждые 5 секунд
    except WebSocketDisconnect:
        manager.disconnect(websocket)

if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=True
    ) 