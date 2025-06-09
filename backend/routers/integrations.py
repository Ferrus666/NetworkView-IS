from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from typing import List, Optional, Dict, Any
import httpx
from datetime import datetime

from config import settings, IntegrationType
from database import db, supabase
from routers.auth import oauth2_scheme, verify_token

router = APIRouter()

# Pydantic модели
class IntegrationConfig(BaseModel):
    name: str
    type: str
    url: str
    credentials: Dict[str, Any]
    settings: Optional[Dict[str, Any]] = {}
    is_active: bool = True

class IntegrationStatus(BaseModel):
    id: str
    name: str
    type: str
    status: str
    last_sync: Optional[datetime]
    error_message: Optional[str]

@router.get("/", response_model=List[IntegrationStatus])
async def get_integrations(token: str = Depends(oauth2_scheme)):
    """Получение списка интеграций"""
    
    verify_token(token)
    
    try:
        result = supabase.table('integrations').select('*').execute()
        
        integrations = []
        for int_data in result.data or []:
            integrations.append(IntegrationStatus(
                id=int_data['id'],
                name=int_data['name'],
                type=int_data['type'],
                status=int_data['status'],
                last_sync=datetime.fromisoformat(int_data['last_sync']) if int_data.get('last_sync') else None,
                error_message=int_data.get('error_message')
            ))
        
        return integrations
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get integrations: {str(e)}")

@router.post("/test")
async def test_integration(
    integration_config: IntegrationConfig,
    token: str = Depends(oauth2_scheme)
):
    """Тестирование интеграции"""
    
    verify_token(token)
    
    try:
        if integration_config.type == IntegrationType.NETBOX:
            return await test_netbox_connection(integration_config)
        elif integration_config.type == IntegrationType.ZABBIX:
            return await test_zabbix_connection(integration_config)
        elif integration_config.type == IntegrationType.LANSWEEPER:
            return await test_lansweeper_connection(integration_config)
        else:
            raise HTTPException(status_code=400, detail="Integration type not supported")
            
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Test failed: {str(e)}")

async def test_netbox_connection(config: IntegrationConfig) -> Dict[str, Any]:
    """Тестирование подключения к NetBox"""
    try:
        async with httpx.AsyncClient() as client:
            headers = {
                "Authorization": f"Token {config.credentials.get('token')}",
                "Accept": "application/json"
            }
            
            response = await client.get(
                f"{config.url}/api/dcim/devices/",
                headers=headers,
                timeout=30
            )
            
            if response.status_code == 200:
                data = response.json()
                return {
                    "status": "success",
                    "message": f"Connected successfully. Found {data.get('count', 0)} devices."
                }
            else:
                return {
                    "status": "error",
                    "message": f"Connection failed: {response.status_code}"
                }
                
    except Exception as e:
        return {
            "status": "error",
            "message": f"Connection error: {str(e)}"
        }

async def test_zabbix_connection(config: IntegrationConfig) -> Dict[str, Any]:
    """Тестирование подключения к Zabbix"""
    try:
        async with httpx.AsyncClient() as client:
            # Аутентификация
            auth_data = {
                "jsonrpc": "2.0",
                "method": "user.login",
                "params": {
                    "user": config.credentials.get('username'),
                    "password": config.credentials.get('password')
                },
                "id": 1
            }
            
            response = await client.post(
                f"{config.url}/api_jsonrpc.php",
                json=auth_data,
                timeout=30
            )
            
            if response.status_code == 200:
                result = response.json()
                if "result" in result:
                    return {
                        "status": "success",
                        "message": "Connected successfully to Zabbix"
                    }
                else:
                    return {
                        "status": "error",
                        "message": f"Authentication failed: {result.get('error', {}).get('data', 'Unknown error')}"
                    }
            else:
                return {
                    "status": "error",
                    "message": f"Connection failed: {response.status_code}"
                }
                
    except Exception as e:
        return {
            "status": "error",
            "message": f"Connection error: {str(e)}"
        }

async def test_lansweeper_connection(config: IntegrationConfig) -> Dict[str, Any]:
    """Тестирование подключения к Lansweeper"""
    try:
        async with httpx.AsyncClient() as client:
            headers = {
                "Authorization": f"Bearer {config.credentials.get('token')}",
                "Accept": "application/json"
            }
            
            response = await client.get(
                f"{config.url}/api/v2/assets",
                headers=headers,
                params={"limit": 1},
                timeout=30
            )
            
            if response.status_code == 200:
                return {
                    "status": "success",
                    "message": "Connected successfully to Lansweeper"
                }
            else:
                return {
                    "status": "error",
                    "message": f"Connection failed: {response.status_code}"
                }
                
    except Exception as e:
        return {
            "status": "error",
            "message": f"Connection error: {str(e)}"
        }

@router.post("/sync/{integration_id}")
async def sync_integration(integration_id: str, token: str = Depends(oauth2_scheme)):
    """Синхронизация данных интеграции"""
    
    payload = verify_token(token)
    user_id = payload.get("user_id")
    
    try:
        # Получение интеграции
        result = supabase.table('integrations').select('*').eq('id', integration_id).execute()
        if not result.data:
            raise HTTPException(status_code=404, detail="Integration not found")
        
        integration = result.data[0]
        
        # Выполнение синхронизации в зависимости от типа
        if integration['type'] == IntegrationType.NETBOX:
            sync_result = await sync_netbox_data(integration)
        elif integration['type'] == IntegrationType.LANSWEEPER:
            sync_result = await sync_lansweeper_data(integration)
        else:
            raise HTTPException(status_code=400, detail="Sync not implemented for this integration type")
        
        # Обновление статуса интеграции
        supabase.table('integrations').update({
            'last_sync': datetime.utcnow().isoformat(),
            'status': 'active' if sync_result['status'] == 'success' else 'error',
            'error_message': sync_result.get('error_message')
        }).eq('id', integration_id).execute()
        
        # Логирование
        await db.log_audit_event({
            "user_id": user_id,
            "action": "integration_synced",
            "resource_type": "integration",
            "resource_id": integration_id,
            "details": sync_result
        })
        
        return sync_result
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Sync failed: {str(e)}")

async def sync_netbox_data(integration: Dict[str, Any]) -> Dict[str, Any]:
    """Синхронизация данных из NetBox"""
    try:
        async with httpx.AsyncClient() as client:
            headers = {
                "Authorization": f"Token {integration['credentials']['token']}",
                "Accept": "application/json"
            }
            
            # Получение устройств
            response = await client.get(
                f"{integration['url']}/api/dcim/devices/",
                headers=headers,
                timeout=60
            )
            
            if response.status_code != 200:
                return {
                    "status": "error",
                    "error_message": f"Failed to fetch devices: {response.status_code}"
                }
            
            devices_data = response.json()
            synced_count = 0
            
            for device in devices_data.get('results', []):
                # Создание/обновление устройства в БД
                device_data = {
                    'name': device.get('name', ''),
                    'device_type': device.get('device_type', {}).get('display', 'unknown'),
                    'status': 'online' if device.get('status', {}).get('value') == 'active' else 'offline',
                    'vendor': device.get('device_type', {}).get('manufacturer', {}).get('name', ''),
                    'model': device.get('device_type', {}).get('model', ''),
                    'serial_number': device.get('serial', ''),
                    'metadata': {
                        'netbox_id': device.get('id'),
                        'site': device.get('site', {}).get('name', ''),
                        'rack': device.get('rack', {}).get('name', '')
                    }
                }
                
                # Получение IP адреса
                if device.get('primary_ip'):
                    ip_response = await client.get(
                        f"{integration['url']}/api/ipam/ip-addresses/{device['primary_ip']['id']}/",
                        headers=headers
                    )
                    if ip_response.status_code == 200:
                        ip_data = ip_response.json()
                        device_data['ip_address'] = ip_data.get('address', '').split('/')[0]
                
                # Проверка существования устройства
                existing = supabase.table('network_devices').select('id').eq('serial_number', device_data['serial_number']).execute()
                
                if existing.data:
                    # Обновление
                    supabase.table('network_devices').update(device_data).eq('id', existing.data[0]['id']).execute()
                else:
                    # Создание
                    supabase.table('network_devices').insert(device_data).execute()
                
                synced_count += 1
            
            return {
                "status": "success",
                "message": f"Synced {synced_count} devices from NetBox"
            }
            
    except Exception as e:
        return {
            "status": "error",
            "error_message": str(e)
        }

async def sync_lansweeper_data(integration: Dict[str, Any]) -> Dict[str, Any]:
    """Синхронизация данных из Lansweeper"""
    try:
        async with httpx.AsyncClient() as client:
            headers = {
                "Authorization": f"Bearer {integration['credentials']['token']}",
                "Accept": "application/json"
            }
            
            # Получение активов
            response = await client.get(
                f"{integration['url']}/api/v2/assets",
                headers=headers,
                params={"limit": 1000},
                timeout=60
            )
            
            if response.status_code != 200:
                return {
                    "status": "error",
                    "error_message": f"Failed to fetch assets: {response.status_code}"
                }
            
            assets_data = response.json()
            synced_count = 0
            
            for asset in assets_data.get('data', []):
                # Создание/обновление устройства в БД
                device_data = {
                    'name': asset.get('name', ''),
                    'device_type': asset.get('type', 'workstation'),
                    'os_version': asset.get('operatingSystem', ''),
                    'status': 'online' if asset.get('lastSeen') else 'offline',
                    'ip_address': asset.get('ipAddress'),
                    'vendor': asset.get('manufacturer', ''),
                    'model': asset.get('model', ''),
                    'metadata': {
                        'lansweeper_id': asset.get('id'),
                        'domain': asset.get('domain', ''),
                        'last_seen': asset.get('lastSeen')
                    }
                }
                
                # Проверка существования устройства по IP
                existing = supabase.table('network_devices').select('id').eq('ip_address', device_data['ip_address']).execute()
                
                if existing.data:
                    # Обновление
                    supabase.table('network_devices').update(device_data).eq('id', existing.data[0]['id']).execute()
                else:
                    # Создание
                    supabase.table('network_devices').insert(device_data).execute()
                
                synced_count += 1
            
            return {
                "status": "success",
                "message": f"Synced {synced_count} assets from Lansweeper"
            }
            
    except Exception as e:
        return {
            "status": "error",
            "error_message": str(e)
        } 