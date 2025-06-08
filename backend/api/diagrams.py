from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form, Query
from fastapi.responses import FileResponse, JSONResponse
from sqlalchemy.orm import Session
from typing import List, Optional, Dict, Any
import json
import uuid
import aiofiles
import xml.etree.ElementTree as ET
import base64
import zipfile
from pathlib import Path
from datetime import datetime
import logging

from ..main import get_db, get_current_active_user, require_role, redis_client
from ..models import User, Diagram, AuditLog
from ..schemas import DiagramCreate, DiagramResponse

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/diagrams", tags=["diagrams"])

# Поддерживаемые форматы диаграмм
ALLOWED_DIAGRAM_FORMATS = {
    "drawio": "application/xml",
    "xml": "application/xml",
    "vsdx": "application/vnd.ms-visio.drawing.main+xml",
    "png": "image/png",
    "jpg": "image/jpeg",
    "svg": "image/svg+xml"
}

def parse_drawio_file(file_path: Path) -> Dict[str, Any]:
    """Парсинг .drawio файла и извлечение метаданных"""
    try:
        tree = ET.parse(file_path)
        root = tree.getroot()
        
        # Извлечение диаграмм
        diagrams = []
        
        # Обработка mxfile структуры
        if root.tag == "mxfile":
            for diagram in root.findall("diagram"):
                diagram_data = {
                    "id": diagram.get("id", ""),
                    "name": diagram.get("name", "Без названия"),
                    "content": diagram.text or ""
                }
                
                # Декодирование содержимого диаграммы
                if diagram_data["content"]:
                    try:
                        # Содержимое обычно в base64 и сжато
                        decoded = base64.b64decode(diagram_data["content"])
                        # Здесь можно добавить распаковку и дальнейший парсинг
                        diagram_data["decoded"] = True
                    except Exception as e:
                        logger.warning(f"Не удалось декодировать диаграмму: {e}")
                        diagram_data["decoded"] = False
                
                diagrams.append(diagram_data)
        
        # Извлечение элементов для анализа
        elements = []
        connections = []
        
        # Поиск mxCell элементов
        for cell in root.findall(".//mxCell"):
            cell_data = {
                "id": cell.get("id", ""),
                "value": cell.get("value", ""),
                "style": cell.get("style", ""),
                "vertex": cell.get("vertex") == "1",
                "edge": cell.get("edge") == "1",
                "source": cell.get("source"),
                "target": cell.get("target")
            }
            
            if cell_data["vertex"]:
                elements.append(cell_data)
            elif cell_data["edge"]:
                connections.append(cell_data)
        
        return {
            "diagrams": diagrams,
            "elements": elements,
            "connections": connections,
            "total_elements": len(elements),
            "total_connections": len(connections),
            "format": "drawio"
        }
        
    except ET.ParseError as e:
        logger.error(f"Ошибка парсинга XML: {e}")
        return {"error": "Невалидный XML файл", "format": "unknown"}
    except Exception as e:
        logger.error(f"Ошибка парсинга диаграммы: {e}")
        return {"error": str(e), "format": "unknown"}

def extract_visio_metadata(file_path: Path) -> Dict[str, Any]:
    """Извлечение метаданных из Visio файлов"""
    try:
        # Для .vsdx файлов (ZIP архивы)
        if file_path.suffix.lower() == ".vsdx":
            with zipfile.ZipFile(file_path, 'r') as zip_file:
                # Поиск основных файлов Visio
                files = zip_file.namelist()
                
                metadata = {
                    "format": "visio",
                    "files": files,
                    "pages": [],
                    "total_elements": 0
                }
                
                # Поиск страниц
                for file_name in files:
                    if "pages/page" in file_name and file_name.endswith(".xml"):
                        try:
                            with zip_file.open(file_name) as page_file:
                                page_xml = ET.parse(page_file)
                                page_data = {
                                    "name": file_name,
                                    "elements": len(page_xml.findall(".//Shape"))
                                }
                                metadata["pages"].append(page_data)
                                metadata["total_elements"] += page_data["elements"]
                        except Exception as e:
                            logger.warning(f"Ошибка чтения страницы {file_name}: {e}")
                
                return metadata
        
        return {"format": "visio", "error": "Неподдерживаемый формат Visio"}
        
    except Exception as e:
        logger.error(f"Ошибка обработки Visio файла: {e}")
        return {"format": "visio", "error": str(e)}

async def cache_diagram_data(diagram_id: int, parsed_data: Dict[str, Any]):
    """Кэширование данных диаграммы в Redis"""
    try:
        if redis_client:
            await redis_client.hset(
                f"diagram:{diagram_id}",
                mapping={
                    "parsed_data": json.dumps(parsed_data),
                    "cached_at": datetime.utcnow().isoformat()
                }
            )
            await redis_client.expire(f"diagram:{diagram_id}", 3600)  # 1 час
    except Exception as e:
        logger.error(f"Ошибка кэширования диаграммы {diagram_id}: {e}")

@router.get("/", response_model=List[DiagramResponse])
async def get_diagrams(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, le=1000),
    file_type: Optional[str] = Query(None),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Получение списка диаграмм"""
    
    query = db.query(Diagram)
    
    if file_type and file_type in ALLOWED_DIAGRAM_FORMATS:
        query = query.filter(Diagram.file_type == file_type)
    
    diagrams = query.offset(skip).limit(limit).all()
    
    # Логирование
    db.add(AuditLog(
        user_id=current_user.id,
        action="LIST_DIAGRAMS",
        resource="diagrams",
        details=json.dumps({"count": len(diagrams)})
    ))
    db.commit()
    
    return diagrams

@router.post("/upload", response_model=DiagramResponse)
async def upload_diagram(
    name: str = Form(...),
    description: str = Form(""),
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role(["admin", "super_admin"]))
):
    """Загрузка диаграммы"""
    
    # Проверка типа файла
    file_extension = file.filename.split('.')[-1].lower()
    if file_extension not in ALLOWED_DIAGRAM_FORMATS:
        raise HTTPException(
            status_code=400,
            detail=f"Неподдерживаемый тип файла. Разрешены: {list(ALLOWED_DIAGRAM_FORMATS.keys())}"
        )
    
    # Проверка размера (100MB для диаграмм)
    if file.size > 100 * 1024 * 1024:
        raise HTTPException(
            status_code=400,
            detail="Размер файла не должен превышать 100MB"
        )
    
    # Создание уникального имени файла
    file_id = str(uuid.uuid4())
    filename = f"{file_id}.{file_extension}"
    file_path = Path("uploads/diagrams") / filename
    
    # Сохранение файла
    try:
        async with aiofiles.open(file_path, 'wb') as f:
            content = await file.read()
            await f.write(content)
    except Exception as e:
        logger.error(f"Ошибка сохранения файла: {e}")
        raise HTTPException(status_code=500, detail="Ошибка сохранения файла")
    
    # Парсинг диаграммы
    parsed_data = {}
    if file_extension in ["drawio", "xml"]:
        parsed_data = parse_drawio_file(file_path)
    elif file_extension == "vsdx":
        parsed_data = extract_visio_metadata(file_path)
    
    # Создание записи в БД
    diagram = Diagram(
        name=name,
        filename=file.filename,
        file_path=str(file_path),
        file_type=file_extension,
        description=description,
        annotations=json.dumps(parsed_data),
        uploaded_by=current_user.id
    )
    
    db.add(diagram)
    db.commit()
    db.refresh(diagram)
    
    # Кэширование
    await cache_diagram_data(diagram.id, parsed_data)
    
    # Логирование
    db.add(AuditLog(
        user_id=current_user.id,
        action="UPLOAD_DIAGRAM",
        resource="diagrams",
        resource_id=str(diagram.id),
        details=json.dumps({
            "name": name,
            "file_type": file_extension,
            "file_size": file.size,
            "elements_count": parsed_data.get("total_elements", 0)
        })
    ))
    db.commit()
    
    return diagram

@router.get("/{diagram_id}", response_model=DiagramResponse)
async def get_diagram(
    diagram_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Получение информации о диаграмме"""
    
    diagram = db.query(Diagram).filter(Diagram.id == diagram_id).first()
    if not diagram:
        raise HTTPException(status_code=404, detail="Диаграмма не найдена")
    
    # Логирование просмотра
    db.add(AuditLog(
        user_id=current_user.id,
        action="VIEW_DIAGRAM",
        resource="diagrams",
        resource_id=str(diagram_id)
    ))
    db.commit()
    
    return diagram

@router.get("/{diagram_id}/data")
async def get_diagram_data(
    diagram_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Получение данных диаграммы для визуализации"""
    
    diagram = db.query(Diagram).filter(Diagram.id == diagram_id).first()
    if not diagram:
        raise HTTPException(status_code=404, detail="Диаграмма не найдена")
    
    # Проверка кэша
    cached_data = None
    try:
        if redis_client:
            cached_data = await redis_client.hget(f"diagram:{diagram_id}", "parsed_data")
            if cached_data:
                cached_data = json.loads(cached_data)
    except Exception as e:
        logger.warning(f"Ошибка чтения кэша: {e}")
    
    # Если нет кэша, парсим заново
    if not cached_data:
        file_path = Path(diagram.file_path)
        if not file_path.exists():
            raise HTTPException(status_code=404, detail="Файл диаграммы не найден")
        
        if diagram.file_type in ["drawio", "xml"]:
            cached_data = parse_drawio_file(file_path)
        elif diagram.file_type == "vsdx":
            cached_data = extract_visio_metadata(file_path)
        else:
            cached_data = {"error": "Неподдерживаемый формат для парсинга"}
        
        # Обновляем кэш
        await cache_diagram_data(diagram_id, cached_data)
    
    # Добавляем аннотации из БД
    if diagram.annotations:
        try:
            stored_annotations = json.loads(diagram.annotations)
            cached_data["stored_annotations"] = stored_annotations
        except Exception as e:
            logger.warning(f"Ошибка парсинга аннотаций: {e}")
    
    return {
        "diagram_id": diagram_id,
        "name": diagram.name,
        "file_type": diagram.file_type,
        "data": cached_data
    }

@router.post("/{diagram_id}/annotations")
async def update_diagram_annotations(
    diagram_id: int,
    annotations: Dict[str, Any],
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role(["admin", "super_admin"]))
):
    """Обновление аннотаций диаграммы"""
    
    diagram = db.query(Diagram).filter(Diagram.id == diagram_id).first()
    if not diagram:
        raise HTTPException(status_code=404, detail="Диаграмма не найдена")
    
    # Обновление аннотаций
    diagram.annotations = json.dumps(annotations)
    db.commit()
    
    # Инвалидация кэша
    try:
        if redis_client:
            await redis_client.delete(f"diagram:{diagram_id}")
    except Exception as e:
        logger.warning(f"Ошибка инвалидации кэша: {e}")
    
    # Логирование
    db.add(AuditLog(
        user_id=current_user.id,
        action="UPDATE_ANNOTATIONS",
        resource="diagrams",
        resource_id=str(diagram_id),
        details=json.dumps({"annotations_keys": list(annotations.keys())})
    ))
    db.commit()
    
    return {"message": "Аннотации успешно обновлены"}

@router.get("/{diagram_id}/download")
async def download_diagram(
    diagram_id: int,
    format: str = Query("original", regex="^(original|png|svg|json)$"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Скачивание диаграммы в различных форматах"""
    
    diagram = db.query(Diagram).filter(Diagram.id == diagram_id).first()
    if not diagram:
        raise HTTPException(status_code=404, detail="Диаграмма не найдена")
    
    file_path = Path(diagram.file_path)
    if not file_path.exists():
        raise HTTPException(status_code=404, detail="Файл не найден на диске")
    
    # Логирование скачивания
    db.add(AuditLog(
        user_id=current_user.id,
        action="DOWNLOAD_DIAGRAM",
        resource="diagrams",
        resource_id=str(diagram_id),
        details=json.dumps({"format": format})
    ))
    db.commit()
    
    if format == "original":
        return FileResponse(
            path=str(file_path),
            filename=diagram.filename,
            media_type=ALLOWED_DIAGRAM_FORMATS.get(diagram.file_type, "application/octet-stream")
        )
    elif format == "json":
        # Возврат парсенных данных как JSON
        if diagram.file_type in ["drawio", "xml"]:
            parsed_data = parse_drawio_file(file_path)
        elif diagram.file_type == "vsdx":
            parsed_data = extract_visio_metadata(file_path)
        else:
            parsed_data = {"error": "Неподдерживаемый формат"}
        
        return JSONResponse(content=parsed_data)
    else:
        # Для PNG/SVG экспорта потребуется дополнительная обработка
        raise HTTPException(
            status_code=501, 
            detail=f"Экспорт в формат {format} пока не реализован"
        )

@router.delete("/{diagram_id}")
async def delete_diagram(
    diagram_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role(["admin", "super_admin"]))
):
    """Удаление диаграммы"""
    
    diagram = db.query(Diagram).filter(Diagram.id == diagram_id).first()
    if not diagram:
        raise HTTPException(status_code=404, detail="Диаграмма не найдена")
    
    # Удаление файла
    try:
        file_path = Path(diagram.file_path)
        if file_path.exists():
            file_path.unlink()
    except Exception as e:
        logger.error(f"Ошибка удаления файла: {e}")
    
    # Удаление из кэша
    try:
        if redis_client:
            await redis_client.delete(f"diagram:{diagram_id}")
    except Exception as e:
        logger.warning(f"Ошибка удаления из кэша: {e}")
    
    # Удаление из БД
    db.delete(diagram)
    
    # Логирование
    db.add(AuditLog(
        user_id=current_user.id,
        action="DELETE_DIAGRAM",
        resource="diagrams",
        resource_id=str(diagram_id),
        details=json.dumps({"name": diagram.name})
    ))
    db.commit()
    
    return {"message": "Диаграмма успешно удалена"}

@router.get("/{diagram_id}/elements")
async def get_diagram_elements(
    diagram_id: int,
    element_type: Optional[str] = Query(None, regex="^(vertex|edge|all)$"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Получение элементов диаграммы"""
    
    diagram_data = await get_diagram_data(diagram_id, db, current_user)
    
    if "error" in diagram_data["data"]:
        return {"error": diagram_data["data"]["error"]}
    
    elements = diagram_data["data"].get("elements", [])
    connections = diagram_data["data"].get("connections", [])
    
    if element_type == "vertex":
        return {"elements": elements}
    elif element_type == "edge":
        return {"connections": connections}
    else:
        return {
            "elements": elements,
            "connections": connections,
            "summary": {
                "total_elements": len(elements),
                "total_connections": len(connections)
            }
        }

@router.get("/stats/summary")
async def get_diagrams_stats(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Статистика по диаграммам"""
    
    total_diagrams = db.query(Diagram).count()
    
    # Статистика по типам файлов
    file_type_stats = {}
    for file_type in ALLOWED_DIAGRAM_FORMATS.keys():
        count = db.query(Diagram).filter(Diagram.file_type == file_type).count()
        if count > 0:
            file_type_stats[file_type] = count
    
    return {
        "total_diagrams": total_diagrams,
        "by_file_type": file_type_stats,
        "supported_formats": list(ALLOWED_DIAGRAM_FORMATS.keys())
    } 