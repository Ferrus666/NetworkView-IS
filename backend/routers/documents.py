from fastapi import APIRouter, HTTPException, Depends, UploadFile, File, Form, Query
from fastapi.responses import FileResponse
from pydantic import BaseModel
from typing import List, Optional
import os
import uuid
import aiofiles
from datetime import datetime
import mimetypes

from config import settings, DocumentStatus
from database import db, supabase
from routers.auth import oauth2_scheme, verify_token

router = APIRouter()

# Pydantic модели
class DocumentBase(BaseModel):
    title: str
    description: Optional[str] = None
    category: str
    tags: Optional[List[str]] = []
    status: str = DocumentStatus.DRAFT

class DocumentCreate(DocumentBase):
    pass

class DocumentUpdate(DocumentBase):
    title: Optional[str] = None
    category: Optional[str] = None

class DocumentResponse(DocumentBase):
    id: str
    file_url: str
    file_name: str
    file_size: int
    version: str
    author_id: str
    download_count: int
    created_at: datetime
    updated_at: datetime

class DocumentSearch(BaseModel):
    query: Optional[str] = None
    category: Optional[str] = None
    tags: Optional[List[str]] = []
    status: Optional[str] = None

# Утилиты
def allowed_file_extension(filename: str) -> bool:
    """Проверка разрешенного расширения файла"""
    ext = os.path.splitext(filename)[1].lower()
    return ext in settings.ALLOWED_EXTENSIONS

def get_file_size(file_path: str) -> int:
    """Получение размера файла"""
    try:
        return os.path.getsize(file_path)
    except:
        return 0

async def save_uploaded_file(file: UploadFile, file_id: str) -> tuple:
    """Сохранение загруженного файла"""
    # Создание уникального имени файла
    file_extension = os.path.splitext(file.filename)[1]
    unique_filename = f"{file_id}{file_extension}"
    file_path = os.path.join(settings.UPLOAD_PATH, unique_filename)
    
    # Создание директории если не существует
    os.makedirs(settings.UPLOAD_PATH, exist_ok=True)
    
    # Сохранение файла
    async with aiofiles.open(file_path, 'wb') as f:
        content = await file.read()
        await f.write(content)
    
    file_size = len(content)
    file_url = f"/uploads/{unique_filename}"
    
    return file_path, file_url, file_size

# Роутеры
@router.post("/upload", response_model=DocumentResponse)
async def upload_document(
    title: str = Form(...),
    description: str = Form(None),
    category: str = Form(...),
    tags: str = Form(""),  # Comma-separated tags
    file: UploadFile = File(...),
    token: str = Depends(oauth2_scheme)
):
    """Загрузка нового документа"""
    
    # Проверка токена
    payload = verify_token(token)
    user_id = payload.get("user_id")
    
    # Проверка файла
    if not file.filename:
        raise HTTPException(status_code=400, detail="No file provided")
    
    if not allowed_file_extension(file.filename):
        raise HTTPException(
            status_code=400, 
            detail=f"File type not allowed. Allowed types: {', '.join(settings.ALLOWED_EXTENSIONS)}"
        )
    
    # Проверка размера файла
    content = await file.read()
    if len(content) > settings.MAX_FILE_SIZE:
        raise HTTPException(
            status_code=400,
            detail=f"File too large. Maximum size: {settings.MAX_FILE_SIZE // (1024*1024)} MB"
        )
    
    # Возврат указателя в начало файла
    await file.seek(0)
    
    # Генерация уникального ID
    file_id = str(uuid.uuid4())
    
    try:
        # Сохранение файла
        file_path, file_url, file_size = await save_uploaded_file(file, file_id)
        
        # Обработка тегов
        tag_list = [tag.strip() for tag in tags.split(",") if tag.strip()] if tags else []
        
        # Создание записи в БД
        document_data = {
            "id": file_id,
            "title": title,
            "description": description,
            "category": category,
            "file_url": file_url,
            "file_name": file.filename,
            "file_size": file_size,
            "author_id": user_id,
            "tags": tag_list,
            "status": DocumentStatus.DRAFT,
            "version": "1.0",
            "download_count": 0
        }
        
        created_doc = await db.create_document(document_data)
        if not created_doc:
            # Удаление файла при ошибке
            try:
                os.remove(file_path)
            except:
                pass
            raise HTTPException(status_code=500, detail="Failed to create document")
        
        # Логирование
        await db.log_audit_event({
            "user_id": user_id,
            "action": "document_uploaded",
            "resource_type": "document",
            "resource_id": file_id,
            "details": {"title": title, "filename": file.filename, "size": file_size}
        })
        
        return DocumentResponse(**created_doc)
        
    except Exception as e:
        # Очистка при ошибке
        try:
            os.remove(file_path)
        except:
            pass
        raise HTTPException(status_code=500, detail=f"Upload failed: {str(e)}")

@router.get("/", response_model=List[DocumentResponse])
async def get_documents(
    limit: int = Query(50, le=100),
    offset: int = Query(0, ge=0),
    category: Optional[str] = Query(None),
    status: Optional[str] = Query(None),
    search: Optional[str] = Query(None),
    token: str = Depends(oauth2_scheme)
):
    """Получение списка документов"""
    
    verify_token(token)
    
    try:
        # Построение запроса
        query = supabase.table('documents').select('*')
        
        # Фильтры
        if category:
            query = query.eq('category', category)
        if status:
            query = query.eq('status', status)
        if search:
            query = query.ilike('title', f'%{search}%')
        
        # Пагинация и сортировка
        result = query.order('created_at', desc=True).range(offset, offset + limit - 1).execute()
        
        documents = result.data or []
        return [DocumentResponse(**doc) for doc in documents]
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get documents: {str(e)}")

@router.get("/{document_id}", response_model=DocumentResponse)
async def get_document(document_id: str, token: str = Depends(oauth2_scheme)):
    """Получение документа по ID"""
    
    verify_token(token)
    
    try:
        result = supabase.table('documents').select('*').eq('id', document_id).execute()
        if not result.data:
            raise HTTPException(status_code=404, detail="Document not found")
        
        document = result.data[0]
        return DocumentResponse(**document)
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get document: {str(e)}")

@router.get("/{document_id}/download")
async def download_document(document_id: str, token: str = Depends(oauth2_scheme)):
    """Скачивание документа"""
    
    payload = verify_token(token)
    user_id = payload.get("user_id")
    
    try:
        # Получение документа
        result = supabase.table('documents').select('*').eq('id', document_id).execute()
        if not result.data:
            raise HTTPException(status_code=404, detail="Document not found")
        
        document = result.data[0]
        file_path = os.path.join(settings.UPLOAD_PATH, os.path.basename(document['file_url']))
        
        # Проверка существования файла
        if not os.path.exists(file_path):
            raise HTTPException(status_code=404, detail="File not found")
        
        # Увеличение счетчика скачиваний
        supabase.table('documents').update({
            "download_count": document['download_count'] + 1
        }).eq('id', document_id).execute()
        
        # Логирование
        await db.log_audit_event({
            "user_id": user_id,
            "action": "document_downloaded",
            "resource_type": "document",
            "resource_id": document_id,
            "details": {"title": document['title'], "filename": document['file_name']}
        })
        
        # Определение MIME типа
        mime_type, _ = mimetypes.guess_type(file_path)
        
        return FileResponse(
            path=file_path,
            filename=document['file_name'],
            media_type=mime_type
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Download failed: {str(e)}")

@router.put("/{document_id}", response_model=DocumentResponse)
async def update_document(
    document_id: str,
    document_update: DocumentUpdate,
    token: str = Depends(oauth2_scheme)
):
    """Обновление документа"""
    
    payload = verify_token(token)
    user_id = payload.get("user_id")
    
    try:
        # Проверка существования документа
        result = supabase.table('documents').select('*').eq('id', document_id).execute()
        if not result.data:
            raise HTTPException(status_code=404, detail="Document not found")
        
        # Подготовка данных для обновления
        update_data = document_update.dict(exclude_unset=True)
        update_data['updated_at'] = datetime.utcnow().isoformat()
        
        # Обновление в БД
        result = supabase.table('documents').update(update_data).eq('id', document_id).execute()
        
        if not result.data:
            raise HTTPException(status_code=500, detail="Failed to update document")
        
        updated_doc = result.data[0]
        
        # Логирование
        await db.log_audit_event({
            "user_id": user_id,
            "action": "document_updated",
            "resource_type": "document",
            "resource_id": document_id,
            "details": {"changes": update_data}
        })
        
        return DocumentResponse(**updated_doc)
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Update failed: {str(e)}")

@router.delete("/{document_id}")
async def delete_document(document_id: str, token: str = Depends(oauth2_scheme)):
    """Удаление документа"""
    
    payload = verify_token(token)
    user_id = payload.get("user_id")
    user_role = payload.get("role")
    
    # Проверка прав (только админы могут удалять)
    if user_role not in ["admin", "super_admin"]:
        raise HTTPException(status_code=403, detail="Insufficient permissions")
    
    try:
        # Получение документа
        result = supabase.table('documents').select('*').eq('id', document_id).execute()
        if not result.data:
            raise HTTPException(status_code=404, detail="Document not found")
        
        document = result.data[0]
        
        # Удаление файла
        file_path = os.path.join(settings.UPLOAD_PATH, os.path.basename(document['file_url']))
        try:
            if os.path.exists(file_path):
                os.remove(file_path)
        except:
            pass  # Файл может не существовать
        
        # Удаление из БД
        supabase.table('documents').delete().eq('id', document_id).execute()
        
        # Логирование
        await db.log_audit_event({
            "user_id": user_id,
            "action": "document_deleted",
            "resource_type": "document",
            "resource_id": document_id,
            "details": {"title": document['title'], "filename": document['file_name']}
        })
        
        return {"message": "Document deleted successfully"}
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Delete failed: {str(e)}")

@router.post("/search", response_model=List[DocumentResponse])
async def search_documents(
    search_params: DocumentSearch,
    limit: int = Query(50, le=100),
    offset: int = Query(0, ge=0),
    token: str = Depends(oauth2_scheme)
):
    """Поиск документов"""
    
    verify_token(token)
    
    try:
        # Построение запроса
        query = supabase.table('documents').select('*')
        
        # Текстовый поиск
        if search_params.query:
            query = query.or_(f'title.ilike.%{search_params.query}%,description.ilike.%{search_params.query}%')
        
        # Фильтры
        if search_params.category:
            query = query.eq('category', search_params.category)
        if search_params.status:
            query = query.eq('status', search_params.status)
        if search_params.tags:
            # Поиск по тегам (PostgreSQL array contains)
            for tag in search_params.tags:
                query = query.contains('tags', [tag])
        
        # Пагинация и сортировка
        result = query.order('created_at', desc=True).range(offset, offset + limit - 1).execute()
        
        documents = result.data or []
        return [DocumentResponse(**doc) for doc in documents]
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Search failed: {str(e)}")

@router.get("/categories/list")
async def get_categories(token: str = Depends(oauth2_scheme)):
    """Получение списка категорий документов"""
    
    verify_token(token)
    
    try:
        # Получение уникальных категорий
        result = supabase.table('documents').select('category').execute()
        
        categories = list(set([doc['category'] for doc in result.data if doc['category']]))
        return {"categories": sorted(categories)}
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get categories: {str(e)}")

@router.get("/stats/summary")
async def get_documents_stats(token: str = Depends(oauth2_scheme)):
    """Получение статистики документов"""
    
    verify_token(token)
    
    try:
        # Общее количество документов
        total_result = supabase.table('documents').select('id', count='exact').execute()
        total_count = total_result.count
        
        # По категориям
        category_result = supabase.table('documents').select('category').execute()
        categories = {}
        for doc in category_result.data:
            cat = doc['category'] or 'Без категории'
            categories[cat] = categories.get(cat, 0) + 1
        
        # По статусам
        status_result = supabase.table('documents').select('status').execute()
        statuses = {}
        for doc in status_result.data:
            status = doc['status']
            statuses[status] = statuses.get(status, 0) + 1
        
        return {
            "total_documents": total_count,
            "by_category": categories,
            "by_status": statuses
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get stats: {str(e)}") 