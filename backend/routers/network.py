from fastapi import APIRouter, HTTPException, Depends, UploadFile, File
from pydantic import BaseModel
from typing import List, Optional, Dict, Any
import json
from datetime import datetime

from database import db, supabase
from routers.auth import oauth2_scheme, verify_token

router = APIRouter()

# Pydantic модели
class NetworkNode(BaseModel):
    id: str
    label: str
    type: str  # server, router, switch, workstation
    ip_address: Optional[str] = None
    status: str  # online, offline, warning
    metadata: Optional[Dict[str, Any]] = {}
    position: Optional[Dict[str, float]] = {}

class NetworkEdge(BaseModel):
    id: str
    source: str
    target: str
    label: Optional[str] = None
    type: str  # ethernet, wifi, vpn
    bandwidth: Optional[str] = None
    protocol: Optional[str] = None

class NetworkTopology(BaseModel):
    nodes: List[NetworkNode]
    edges: List[NetworkEdge]
    metadata: Optional[Dict[str, Any]] = {}

class NetworkAnnotation(BaseModel):
    id: str
    device_id: str
    annotation_type: str
    title: str
    content: str
    position_x: float
    position_y: float
    author_id: str
    is_visible: bool
    created_at: datetime

@router.get("/topology", response_model=NetworkTopology)
async def get_network_topology(token: str = Depends(oauth2_scheme)):
    """Получение топологии сети"""
    
    verify_token(token)
    
    try:
        # Получение устройств
        devices_result = supabase.table('network_devices').select('*').execute()
        devices = devices_result.data or []
        
        # Преобразование в узлы
        nodes = []
        for device in devices:
            node = NetworkNode(
                id=device['id'],
                label=device['name'],
                type=device.get('device_type', 'server'),
                ip_address=str(device['ip_address']) if device['ip_address'] else None,
                status=device.get('status', 'unknown'),
                metadata=device.get('metadata', {}),
                position={"x": 0, "y": 0}  # Позиции можно хранить в metadata
            )
            nodes.append(node)
        
        # Создание связей (пример - можно расширить)
        edges = []
        for i, device in enumerate(devices):
            if i > 0:
                edge = NetworkEdge(
                    id=f"edge_{i}",
                    source=devices[i-1]['id'],
                    target=device['id'],
                    type="ethernet",
                    label="1Gbps"
                )
                edges.append(edge)
        
        return NetworkTopology(
            nodes=nodes,
            edges=edges,
            metadata={"total_nodes": len(nodes), "total_edges": len(edges)}
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get topology: {str(e)}")

@router.post("/annotations")
async def create_annotation(
    annotation_data: Dict[str, Any],
    token: str = Depends(oauth2_scheme)
):
    """Создание аннотации на сети"""
    
    payload = verify_token(token)
    user_id = payload.get("user_id")
    
    try:
        annotation_data['author_id'] = user_id
        result = supabase.table('network_annotations').insert(annotation_data).execute()
        
        return {"message": "Annotation created", "id": result.data[0]['id'] if result.data else None}
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to create annotation: {str(e)}")

@router.get("/annotations", response_model=List[NetworkAnnotation])
async def get_annotations(token: str = Depends(oauth2_scheme)):
    """Получение аннотаций сети"""
    
    verify_token(token)
    
    try:
        result = supabase.table('network_annotations').select('*').execute()
        
        annotations = []
        for ann_data in result.data or []:
            annotations.append(NetworkAnnotation(
                id=ann_data['id'],
                device_id=ann_data['device_id'],
                annotation_type=ann_data['annotation_type'],
                title=ann_data['title'],
                content=ann_data['content'],
                position_x=float(ann_data['position_x']),
                position_y=float(ann_data['position_y']),
                author_id=ann_data['author_id'],
                is_visible=ann_data['is_visible'],
                created_at=datetime.fromisoformat(ann_data['created_at'])
            ))
        
        return annotations
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get annotations: {str(e)}")

@router.post("/import/drawio")
async def import_drawio(
    file: UploadFile = File(...),
    token: str = Depends(oauth2_scheme)
):
    """Импорт схемы из draw.io"""
    
    verify_token(token)
    
    try:
        content = await file.read()
        # Здесь должна быть логика парсинга draw.io файла
        # Для примера возвращаем заглушку
        
        return {"message": "Draw.io file imported successfully", "nodes_imported": 0}
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Import failed: {str(e)}") 