from fastapi import APIRouter, HTTPException, Depends, Query
from pydantic import BaseModel
from typing import List, Optional, Dict, Any
from datetime import datetime, timedelta
import httpx
import asyncio
import json

from config import settings
from database import db, supabase
from routers.auth import oauth2_scheme, verify_token

router = APIRouter()

# Pydantic модели
class DeviceStatus(BaseModel):
    device_id: str
    device_name: str
    ip_address: str
    status: str  # online, offline, warning
    cpu_usage: Optional[float] = None
    memory_usage: Optional[float] = None
    disk_usage: Optional[float] = None
    network_in: Optional[float] = None
    network_out: Optional[float] = None
    last_seen: datetime
    alerts: Optional[List[str]] = []

class NetworkMetrics(BaseModel):
    total_devices: int
    online_devices: int
    offline_devices: int
    warning_devices: int
    total_traffic_in: float
    total_traffic_out: float
    average_cpu: float
    average_memory: float
    timestamp: datetime

class MonitoringAlert(BaseModel):
    id: str
    device_id: str
    device_name: str
    alert_type: str
    severity: str
    message: str
    status: str  # active, resolved, acknowledged
    created_at: datetime
    resolved_at: Optional[datetime] = None

class MonitoringLog(BaseModel):
    id: str
    device_id: str
    device_name: str
    metric_name: str
    metric_value: float
    status: str
    alert_level: str
    message: str
    source: str
    timestamp: datetime

# Интеграции с системами мониторинга
class PrometheusClient:
    def __init__(self):
        self.url = settings.PROMETHEUS_URL
        self.enabled = settings.PROMETHEUS_ENABLED
    
    async def query_metric(self, query: str) -> Dict[str, Any]:
        """Запрос метрики из Prometheus"""
        if not self.enabled:
            return {"data": {"result": []}}
        
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    f"{self.url}/api/v1/query",
                    params={"query": query},
                    timeout=30
                )
                return response.json()
        except Exception as e:
            print(f"Prometheus query error: {e}")
            return {"data": {"result": []}}
    
    async def query_range(self, query: str, start: datetime, end: datetime, step: str = "1m") -> Dict[str, Any]:
        """Запрос метрики за период"""
        if not self.enabled:
            return {"data": {"result": []}}
        
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    f"{self.url}/api/v1/query_range",
                    params={
                        "query": query,
                        "start": start.timestamp(),
                        "end": end.timestamp(),
                        "step": step
                    },
                    timeout=30
                )
                return response.json()
        except Exception as e:
            print(f"Prometheus range query error: {e}")
            return {"data": {"result": []}}
    
    async def get_device_metrics(self, device_id: str) -> Dict[str, Any]:
        """Получение метрик устройства"""
        metrics = {}
        
        # CPU Usage
        cpu_query = f'100 - (avg by (instance) (rate(node_cpu_seconds_total{{mode="idle",instance=~"{device_id}.*"}}[5m])) * 100)'
        cpu_result = await self.query_metric(cpu_query)
        
        # Memory Usage
        memory_query = f'(1 - (node_memory_MemAvailable_bytes{{instance=~"{device_id}.*"}} / node_memory_MemTotal_bytes{{instance=~"{device_id}.*"}})) * 100'
        memory_result = await self.query_metric(memory_query)
        
        # Disk Usage
        disk_query = f'100 - ((node_filesystem_avail_bytes{{instance=~"{device_id}.*",mountpoint="/"}} * 100) / node_filesystem_size_bytes{{instance=~"{device_id}.*",mountpoint="/"}})'
        disk_result = await self.query_metric(disk_query)
        
        # Network Traffic
        network_in_query = f'rate(node_network_receive_bytes_total{{instance=~"{device_id}.*"}}[5m])'
        network_out_query = f'rate(node_network_transmit_bytes_total{{instance=~"{device_id}.*"}}[5m])'
        
        network_in_result = await self.query_metric(network_in_query)
        network_out_result = await self.query_metric(network_out_query)
        
        # Парсинг результатов
        if cpu_result["data"]["result"]:
            metrics["cpu_usage"] = float(cpu_result["data"]["result"][0]["value"][1])
        
        if memory_result["data"]["result"]:
            metrics["memory_usage"] = float(memory_result["data"]["result"][0]["value"][1])
        
        if disk_result["data"]["result"]:
            metrics["disk_usage"] = float(disk_result["data"]["result"][0]["value"][1])
        
        if network_in_result["data"]["result"]:
            metrics["network_in"] = sum(float(r["value"][1]) for r in network_in_result["data"]["result"])
        
        if network_out_result["data"]["result"]:
            metrics["network_out"] = sum(float(r["value"][1]) for r in network_out_result["data"]["result"])
        
        return metrics

class ZabbixClient:
    def __init__(self):
        self.url = settings.ZABBIX_URL
        self.username = settings.ZABBIX_USERNAME
        self.password = settings.ZABBIX_PASSWORD
        self.enabled = settings.ZABBIX_ENABLED
        self.auth_token = None
    
    async def authenticate(self):
        """Аутентификация в Zabbix API"""
        if not self.enabled:
            return
        
        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    f"{self.url}/api_jsonrpc.php",
                    json={
                        "jsonrpc": "2.0",
                        "method": "user.login",
                        "params": {
                            "user": self.username,
                            "password": self.password
                        },
                        "id": 1
                    },
                    timeout=30
                )
                result = response.json()
                self.auth_token = result.get("result")
        except Exception as e:
            print(f"Zabbix auth error: {e}")
    
    async def get_hosts(self) -> List[Dict[str, Any]]:
        """Получение списка хостов"""
        if not self.enabled or not self.auth_token:
            return []
        
        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    f"{self.url}/api_jsonrpc.php",
                    json={
                        "jsonrpc": "2.0",
                        "method": "host.get",
                        "params": {
                            "output": ["hostid", "host", "name", "status"],
                            "selectInterfaces": ["ip"]
                        },
                        "auth": self.auth_token,
                        "id": 1
                    },
                    timeout=30
                )
                result = response.json()
                return result.get("result", [])
        except Exception as e:
            print(f"Zabbix hosts error: {e}")
            return []
    
    async def get_host_items(self, host_id: str) -> List[Dict[str, Any]]:
        """Получение элементов данных хоста"""
        if not self.enabled or not self.auth_token:
            return []
        
        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    f"{self.url}/api_jsonrpc.php",
                    json={
                        "jsonrpc": "2.0",
                        "method": "item.get",
                        "params": {
                            "output": ["itemid", "name", "key_", "lastvalue", "units"],
                            "hostids": host_id,
                            "filter": {
                                "status": 0  # Active items only
                            }
                        },
                        "auth": self.auth_token,
                        "id": 1
                    },
                    timeout=30
                )
                result = response.json()
                return result.get("result", [])
        except Exception as e:
            print(f"Zabbix items error: {e}")
            return []

# Инициализация клиентов
prometheus_client = PrometheusClient()
zabbix_client = ZabbixClient()

# Утилиты
async def determine_device_status(metrics: Dict[str, Any]) -> str:
    """Определение статуса устройства на основе метрик"""
    cpu = metrics.get("cpu_usage", 0)
    memory = metrics.get("memory_usage", 0)
    disk = metrics.get("disk_usage", 0)
    
    # Критические пороги
    if cpu > 90 or memory > 90 or disk > 90:
        return "offline"  # Считаем критическое состояние как offline
    
    # Предупреждающие пороги
    if cpu > 75 or memory > 75 or disk > 75:
        return "warning"
    
    return "online"

async def generate_alerts(device: DeviceStatus) -> List[str]:
    """Генерация предупреждений для устройства"""
    alerts = []
    
    if device.cpu_usage and device.cpu_usage > 90:
        alerts.append(f"High CPU usage: {device.cpu_usage:.1f}%")
    
    if device.memory_usage and device.memory_usage > 90:
        alerts.append(f"High memory usage: {device.memory_usage:.1f}%")
    
    if device.disk_usage and device.disk_usage > 90:
        alerts.append(f"High disk usage: {device.disk_usage:.1f}%")
    
    # Проверка последней активности
    if device.last_seen < datetime.utcnow() - timedelta(minutes=5):
        alerts.append("Device not responding")
    
    return alerts

# Роутеры
@router.get("/devices", response_model=List[DeviceStatus])
async def get_device_statuses(token: str = Depends(oauth2_scheme)):
    """Получение статуса всех устройств"""
    
    verify_token(token)
    
    try:
        devices = []
        
        # Получение устройств из БД
        result = supabase.table('network_devices').select('*').execute()
        db_devices = result.data or []
        
        # Аутентификация в Zabbix если включен
        if zabbix_client.enabled:
            await zabbix_client.authenticate()
        
        for db_device in db_devices:
            device_id = db_device['id']
            
            # Получение метрик из Prometheus
            prometheus_metrics = await prometheus_client.get_device_metrics(device_id)
            
            # Создание объекта устройства
            device = DeviceStatus(
                device_id=device_id,
                device_name=db_device['name'],
                ip_address=str(db_device['ip_address']) if db_device['ip_address'] else "",
                status=db_device.get('status', 'unknown'),
                cpu_usage=prometheus_metrics.get('cpu_usage'),
                memory_usage=prometheus_metrics.get('memory_usage'),
                disk_usage=prometheus_metrics.get('disk_usage'),
                network_in=prometheus_metrics.get('network_in'),
                network_out=prometheus_metrics.get('network_out'),
                last_seen=datetime.fromisoformat(db_device.get('last_seen', datetime.utcnow().isoformat()))
            )
            
            # Определение статуса на основе метрик
            if prometheus_metrics:
                device.status = await determine_device_status(prometheus_metrics)
            
            # Генерация предупреждений
            device.alerts = await generate_alerts(device)
            
            # Обновление статуса в БД
            supabase.table('network_devices').update({
                'status': device.status,
                'last_seen': datetime.utcnow().isoformat()
            }).eq('id', device_id).execute()
            
            devices.append(device)
        
        return devices
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get device statuses: {str(e)}")

@router.get("/devices/{device_id}", response_model=DeviceStatus)
async def get_device_status(device_id: str, token: str = Depends(oauth2_scheme)):
    """Получение статуса конкретного устройства"""
    
    verify_token(token)
    
    try:
        # Получение устройства из БД
        result = supabase.table('network_devices').select('*').eq('id', device_id).execute()
        if not result.data:
            raise HTTPException(status_code=404, detail="Device not found")
        
        db_device = result.data[0]
        
        # Получение метрик
        prometheus_metrics = await prometheus_client.get_device_metrics(device_id)
        
        device = DeviceStatus(
            device_id=device_id,
            device_name=db_device['name'],
            ip_address=str(db_device['ip_address']) if db_device['ip_address'] else "",
            status=db_device.get('status', 'unknown'),
            cpu_usage=prometheus_metrics.get('cpu_usage'),
            memory_usage=prometheus_metrics.get('memory_usage'),
            disk_usage=prometheus_metrics.get('disk_usage'),
            network_in=prometheus_metrics.get('network_in'),
            network_out=prometheus_metrics.get('network_out'),
            last_seen=datetime.fromisoformat(db_device.get('last_seen', datetime.utcnow().isoformat()))
        )
        
        # Определение статуса и предупреждений
        if prometheus_metrics:
            device.status = await determine_device_status(prometheus_metrics)
        
        device.alerts = await generate_alerts(device)
        
        return device
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get device status: {str(e)}")

@router.get("/metrics/overview", response_model=NetworkMetrics)
async def get_network_metrics(token: str = Depends(oauth2_scheme)):
    """Получение общих метрик сети"""
    
    verify_token(token)
    
    try:
        # Получение всех устройств
        devices = await get_device_statuses(token)
        
        # Подсчет статистики
        total_devices = len(devices)
        online_devices = len([d for d in devices if d.status == "online"])
        offline_devices = len([d for d in devices if d.status == "offline"])
        warning_devices = len([d for d in devices if d.status == "warning"])
        
        # Суммарный трафик
        total_traffic_in = sum(d.network_in or 0 for d in devices)
        total_traffic_out = sum(d.network_out or 0 for d in devices)
        
        # Средние значения
        cpu_values = [d.cpu_usage for d in devices if d.cpu_usage is not None]
        memory_values = [d.memory_usage for d in devices if d.memory_usage is not None]
        
        average_cpu = sum(cpu_values) / len(cpu_values) if cpu_values else 0
        average_memory = sum(memory_values) / len(memory_values) if memory_values else 0
        
        return NetworkMetrics(
            total_devices=total_devices,
            online_devices=online_devices,
            offline_devices=offline_devices,
            warning_devices=warning_devices,
            total_traffic_in=total_traffic_in,
            total_traffic_out=total_traffic_out,
            average_cpu=average_cpu,
            average_memory=average_memory,
            timestamp=datetime.utcnow()
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get network metrics: {str(e)}")

@router.get("/logs", response_model=List[MonitoringLog])
async def get_monitoring_logs(
    limit: int = Query(50, le=100),
    offset: int = Query(0, ge=0),
    device_id: Optional[str] = Query(None),
    alert_level: Optional[str] = Query(None),
    token: str = Depends(oauth2_scheme)
):
    """Получение логов мониторинга"""
    
    verify_token(token)
    
    try:
        query = supabase.table('monitoring_logs').select('*')
        
        # Фильтры
        if device_id:
            query = query.eq('device_id', device_id)
        if alert_level:
            query = query.eq('alert_level', alert_level)
        
        result = query.order('timestamp', desc=True).range(offset, offset + limit - 1).execute()
        
        logs = []
        for log_data in result.data or []:
            logs.append(MonitoringLog(
                id=log_data['id'],
                device_id=log_data['device_id'],
                device_name=log_data['device_name'],
                metric_name=log_data['metric_name'],
                metric_value=float(log_data['metric_value']),
                status=log_data['status'],
                alert_level=log_data['alert_level'],
                message=log_data['message'],
                source=log_data['source'],
                timestamp=datetime.fromisoformat(log_data['timestamp'])
            ))
        
        return logs
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get logs: {str(e)}")

@router.post("/logs")
async def create_monitoring_log(
    log_data: Dict[str, Any],
    token: str = Depends(oauth2_scheme)
):
    """Создание записи в логах мониторинга"""
    
    payload = verify_token(token)
    user_id = payload.get("user_id")
    
    try:
        # Создание записи в БД
        result = supabase.table('monitoring_logs').insert(log_data).execute()
        
        # Логирование действия
        await db.log_audit_event({
            "user_id": user_id,
            "action": "monitoring_log_created",
            "resource_type": "monitoring_log",
            "resource_id": result.data[0]['id'] if result.data else None,
            "details": log_data
        })
        
        return {"message": "Log created successfully"}
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to create log: {str(e)}")

@router.get("/devices/{device_id}/metrics/history")
async def get_device_metrics_history(
    device_id: str,
    period: str = Query("1h", description="Time period: 1h, 24h, 7d, 30d"),
    token: str = Depends(oauth2_scheme)
):
    """Получение исторических метрик устройства"""
    
    verify_token(token)
    
    try:
        # Определение временного диапазона
        now = datetime.utcnow()
        if period == "1h":
            start_time = now - timedelta(hours=1)
            step = "1m"
        elif period == "24h":
            start_time = now - timedelta(days=1)
            step = "5m"
        elif period == "7d":
            start_time = now - timedelta(days=7)
            step = "1h"
        elif period == "30d":
            start_time = now - timedelta(days=30)
            step = "6h"
        else:
            raise HTTPException(status_code=400, detail="Invalid period")
        
        # Запрос метрик из Prometheus
        cpu_query = f'100 - (avg by (instance) (rate(node_cpu_seconds_total{{mode="idle",instance=~"{device_id}.*"}}[5m])) * 100)'
        memory_query = f'(1 - (node_memory_MemAvailable_bytes{{instance=~"{device_id}.*"}} / node_memory_MemTotal_bytes{{instance=~"{device_id}.*"}})) * 100'
        
        cpu_data = await prometheus_client.query_range(cpu_query, start_time, now, step)
        memory_data = await prometheus_client.query_range(memory_query, start_time, now, step)
        
        return {
            "cpu_usage": cpu_data["data"]["result"],
            "memory_usage": memory_data["data"]["result"],
            "period": period,
            "start_time": start_time.isoformat(),
            "end_time": now.isoformat()
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get metrics history: {str(e)}")

@router.get("/alerts", response_model=List[MonitoringAlert])
async def get_monitoring_alerts(
    limit: int = Query(50, le=100),
    offset: int = Query(0, ge=0),
    status: Optional[str] = Query(None),
    severity: Optional[str] = Query(None),
    token: str = Depends(oauth2_scheme)
):
    """Получение активных предупреждений"""
    
    verify_token(token)
    
    try:
        # Получение предупреждений из логов безопасности
        query = supabase.table('security_logs').select('*')
        
        if status:
            query = query.eq('resolved', status == "resolved")
        if severity:
            query = query.eq('severity', severity)
        
        result = query.order('timestamp', desc=True).range(offset, offset + limit - 1).execute()
        
        alerts = []
        for alert_data in result.data or []:
            alerts.append(MonitoringAlert(
                id=alert_data['id'],
                device_id=alert_data.get('details', {}).get('device_id', ''),
                device_name=alert_data.get('details', {}).get('device_name', ''),
                alert_type=alert_data['event_type'],
                severity=alert_data['severity'],
                message=alert_data.get('details', {}).get('message', ''),
                status="resolved" if alert_data['resolved'] else "active",
                created_at=datetime.fromisoformat(alert_data['timestamp']),
                resolved_at=None
            ))
        
        return alerts
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get alerts: {str(e)}")

@router.put("/alerts/{alert_id}/acknowledge")
async def acknowledge_alert(alert_id: str, token: str = Depends(oauth2_scheme)):
    """Подтверждение предупреждения"""
    
    payload = verify_token(token)
    user_id = payload.get("user_id")
    
    try:
        # Обновление статуса предупреждения
        result = supabase.table('security_logs').update({
            'resolved': True
        }).eq('id', alert_id).execute()
        
        if not result.data:
            raise HTTPException(status_code=404, detail="Alert not found")
        
        # Логирование действия
        await db.log_audit_event({
            "user_id": user_id,
            "action": "alert_acknowledged",
            "resource_type": "monitoring_alert",
            "resource_id": alert_id,
            "details": {"alert_id": alert_id}
        })
        
        return {"message": "Alert acknowledged successfully"}
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to acknowledge alert: {str(e)}") 