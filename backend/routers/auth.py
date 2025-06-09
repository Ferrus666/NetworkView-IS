from fastapi import APIRouter, HTTPException, Depends, status
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from pydantic import BaseModel, EmailStr
from typing import Optional
import bcrypt
from datetime import datetime, timedelta
from jose import JWTError, jwt
import redis

from config import settings
from database import db

router = APIRouter()

# OAuth2 схема
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/token")

# Redis клиент для блокировки
redis_client = redis.Redis.from_url(settings.REDIS_URL, decode_responses=True)

# Pydantic модели
class UserCreate(BaseModel):
    username: str
    email: EmailStr
    password: str
    role: Optional[str] = "user"

class UserLogin(BaseModel):
    email: str
    password: str

class UserResponse(BaseModel):
    id: str
    username: str
    email: str
    role: str
    is_active: bool
    created_at: datetime

class Token(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str

class TokenData(BaseModel):
    email: Optional[str] = None

# Утилиты для работы с паролями
def hash_password(password: str) -> str:
    """Хеширование пароля"""
    salt = bcrypt.gensalt(rounds=settings.BCRYPT_ROUNDS)
    return bcrypt.hashpw(password.encode('utf-8'), salt).decode('utf-8')

def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Проверка пароля"""
    return bcrypt.checkpw(plain_password.encode('utf-8'), hashed_password.encode('utf-8'))

# JWT утилиты
def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    """Создание access токена"""
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, settings.JWT_SECRET_KEY, algorithm=settings.JWT_ALGORITHM)
    return encoded_jwt

def create_refresh_token(data: dict):
    """Создание refresh токена"""
    to_encode = data.copy()
    expire = datetime.utcnow() + timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, settings.JWT_SECRET_KEY, algorithm=settings.JWT_ALGORITHM)
    return encoded_jwt

def verify_token(token: str):
    """Проверка JWT токена"""
    try:
        payload = jwt.decode(token, settings.JWT_SECRET_KEY, algorithms=[settings.JWT_ALGORITHM])
        email: str = payload.get("sub")
        if email is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid token",
                headers={"WWW-Authenticate": "Bearer"},
            )
        token_data = TokenData(email=email)
        return payload
    except JWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token",
            headers={"WWW-Authenticate": "Bearer"},
        )

# Проверка лимита попыток входа
async def check_login_attempts(email: str) -> bool:
    """Проверка количества попыток входа"""
    key = f"login_attempts:{email}"
    attempts = redis_client.get(key)
    if attempts and int(attempts) >= settings.MAX_LOGIN_ATTEMPTS:
        ttl = redis_client.ttl(key)
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail=f"Too many login attempts. Try again in {ttl} seconds."
        )
    return True

async def increment_login_attempts(email: str):
    """Увеличение счетчика попыток входа"""
    key = f"login_attempts:{email}"
    pipe = redis_client.pipeline()
    pipe.incr(key)
    pipe.expire(key, settings.LOGIN_ATTEMPT_TIMEOUT_MINUTES * 60)
    pipe.execute()

async def reset_login_attempts(email: str):
    """Сброс счетчика попыток входа"""
    key = f"login_attempts:{email}"
    redis_client.delete(key)

# Роутеры
@router.post("/register", response_model=UserResponse)
async def register_user(user: UserCreate):
    """Регистрация нового пользователя"""
    
    # Проверка длины пароля
    if len(user.password) < settings.PASSWORD_MIN_LENGTH:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Password must be at least {settings.PASSWORD_MIN_LENGTH} characters long"
        )
    
    # Проверка существования пользователя
    existing_user = await db.get_user_by_email(user.email)
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="User with this email already exists"
        )
    
    # Хеширование пароля
    hashed_password = hash_password(user.password)
    
    # Создание пользователя
    user_data = {
        "username": user.username,
        "email": user.email,
        "hashed_password": hashed_password,
        "role": user.role,
        "is_active": True,
        "is_verified": False
    }
    
    created_user = await db.create_user(user_data)
    if not created_user:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create user"
        )
    
    # Логирование события
    await db.log_audit_event({
        "user_id": created_user["id"],
        "action": "user_registered",
        "resource_type": "user",
        "resource_id": created_user["id"],
        "details": {"username": user.username, "email": user.email}
    })
    
    return UserResponse(**created_user)

@router.post("/token", response_model=Token)
async def login_user(form_data: OAuth2PasswordRequestForm = Depends()):
    """Вход пользователя"""
    
    # Проверка лимита попыток
    await check_login_attempts(form_data.username)
    
    # Получение пользователя (по email или username)
    user = await db.get_user_by_email(form_data.username)
    if not user:
        # Попробуем найти по username
        from database import supabase
        result = supabase.table('users').select('*').eq('username', form_data.username).execute()
        user = result.data[0] if result.data else None
    
    # Проверка пользователя и пароля
    if not user or not verify_password(form_data.password, user["hashed_password"]):
        await increment_login_attempts(form_data.username)
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email/username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # Проверка активности пользователя
    if not user["is_active"]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="User account is disabled"
        )
    
    # Сброс счетчика попыток входа
    await reset_login_attempts(form_data.username)
    
    # Создание токенов
    access_token = create_access_token(
        data={"sub": user["email"], "role": user["role"], "user_id": user["id"]}
    )
    refresh_token = create_refresh_token(
        data={"sub": user["email"], "type": "refresh"}
    )
    
    # Обновление времени последнего входа
    from database import supabase
    supabase.table('users').update({"last_login": datetime.utcnow().isoformat()}).eq('id', user['id']).execute()
    
    # Логирование события
    await db.log_security_event({
        "event_type": "user_login",
        "severity": "info",
        "user_id": user["id"],
        "details": {"email": user["email"], "username": user["username"]}
    })
    
    return Token(
        access_token=access_token,
        refresh_token=refresh_token,
        token_type="bearer"
    )

@router.post("/refresh", response_model=Token)
async def refresh_access_token(refresh_token: str):
    """Обновление access токена через refresh токен"""
    try:
        payload = jwt.decode(refresh_token, settings.JWT_SECRET_KEY, algorithms=[settings.JWT_ALGORITHM])
        email: str = payload.get("sub")
        token_type: str = payload.get("type")
        
        if email is None or token_type != "refresh":
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid refresh token"
            )
        
        # Получение пользователя
        user = await db.get_user_by_email(email)
        if not user or not user["is_active"]:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="User not found or disabled"
            )
        
        # Создание нового access токена
        new_access_token = create_access_token(
            data={"sub": user["email"], "role": user["role"], "user_id": user["id"]}
        )
        new_refresh_token = create_refresh_token(
            data={"sub": user["email"], "type": "refresh"}
        )
        
        return Token(
            access_token=new_access_token,
            refresh_token=new_refresh_token,
            token_type="bearer"
        )
        
    except JWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid refresh token"
        )

@router.get("/me", response_model=UserResponse)
async def get_current_user_info(token: str = Depends(oauth2_scheme)):
    """Получение информации о текущем пользователе"""
    payload = verify_token(token)
    email = payload.get("sub")
    
    user = await db.get_user_by_email(email)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    return UserResponse(**user)

@router.post("/logout")
async def logout_user(token: str = Depends(oauth2_scheme)):
    """Выход пользователя (добавление токена в черный список)"""
    payload = verify_token(token)
    user_id = payload.get("user_id")
    
    # Добавление токена в Redis blacklist
    token_key = f"blacklist:{token}"
    redis_client.setex(token_key, settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60, "blacklisted")
    
    # Логирование события
    await db.log_security_event({
        "event_type": "user_logout",
        "severity": "info",
        "user_id": user_id,
        "details": {"action": "logout"}
    })
    
    return {"message": "Successfully logged out"}

@router.post("/change-password")
async def change_password(
    current_password: str,
    new_password: str,
    token: str = Depends(oauth2_scheme)
):
    """Смена пароля пользователя"""
    payload = verify_token(token)
    email = payload.get("sub")
    
    # Проверка длины нового пароля
    if len(new_password) < settings.PASSWORD_MIN_LENGTH:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Password must be at least {settings.PASSWORD_MIN_LENGTH} characters long"
        )
    
    # Получение пользователя
    user = await db.get_user_by_email(email)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    # Проверка текущего пароля
    if not verify_password(current_password, user["hashed_password"]):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Incorrect current password"
        )
    
    # Хеширование нового пароля
    new_hashed_password = hash_password(new_password)
    
    # Обновление пароля в БД
    from database import supabase
    result = supabase.table('users').update({
        "hashed_password": new_hashed_password,
        "updated_at": datetime.utcnow().isoformat()
    }).eq('id', user['id']).execute()
    
    # Логирование события
    await db.log_security_event({
        "event_type": "password_changed",
        "severity": "info",
        "user_id": user["id"],
        "details": {"email": email}
    })
    
    return {"message": "Password changed successfully"}

# Middleware для проверки заблокированных токенов
async def check_blacklisted_token(token: str = Depends(oauth2_scheme)):
    """Проверка токена на нахождение в черном списке"""
    token_key = f"blacklist:{token}"
    if redis_client.exists(token_key):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token has been revoked"
        )
    return token 