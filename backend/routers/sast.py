from fastapi import APIRouter, HTTPException, Depends, UploadFile, File, Form, BackgroundTasks
from pydantic import BaseModel, HttpUrl
from typing import List, Optional, Dict, Any
import os
import uuid
import tempfile
import subprocess
import json
import asyncio
from datetime import datetime
import aiofiles
import zipfile
import tarfile

from config import settings, VulnerabilitySeverity
from database import db, supabase
from routers.auth import oauth2_scheme, verify_token

router = APIRouter()

# Pydantic модели
class SASTScanRequest(BaseModel):
    repository_url: Optional[str] = None
    branch: str = "main"
    language: str
    rules: Optional[List[str]] = []
    exclude_paths: Optional[List[str]] = []

class VulnerabilityInfo(BaseModel):
    id: str
    severity: str
    title: str
    description: str
    file_path: str
    line_number: int
    column_number: Optional[int] = None
    rule_id: str
    cwe_id: Optional[str] = None
    owasp_category: Optional[str] = None
    code_snippet: Optional[str] = None

class SASTResultResponse(BaseModel):
    id: str
    scan_id: str
    repository_url: Optional[str]
    commit_id: Optional[str]
    branch: str
    vulnerabilities: List[VulnerabilityInfo]
    summary: Dict[str, Any]
    report_url: str
    status: str
    scan_duration: Optional[int]
    created_at: datetime

class SASTSummary(BaseModel):
    total_vulnerabilities: int
    critical_count: int
    high_count: int
    medium_count: int
    low_count: int
    info_count: int
    files_scanned: int
    languages_detected: List[str]

# Утилиты для SAST анализа
class SASTAnalyzer:
    def __init__(self):
        self.supported_tools = {
            "python": ["bandit", "semgrep"],
            "javascript": ["eslint", "semgrep"],
            "typescript": ["eslint", "semgrep"],
            "java": ["semgrep"],
            "go": ["gosec", "semgrep"],
            "php": ["semgrep"],
            "c": ["semgrep"],
            "cpp": ["semgrep"]
        }
    
    async def extract_archive(self, file_path: str, extract_to: str) -> str:
        """Извлечение архива"""
        try:
            if file_path.endswith('.zip'):
                with zipfile.ZipFile(file_path, 'r') as zip_ref:
                    zip_ref.extractall(extract_to)
            elif file_path.endswith(('.tar.gz', '.tar')):
                with tarfile.open(file_path, 'r:*') as tar_ref:
                    tar_ref.extractall(extract_to)
            else:
                raise ValueError("Unsupported archive format")
            
            return extract_to
        except Exception as e:
            raise Exception(f"Failed to extract archive: {str(e)}")
    
    async def detect_language(self, code_path: str) -> List[str]:
        """Определение языков программирования в проекте"""
        languages = []
        
        for root, dirs, files in os.walk(code_path):
            for file in files:
                ext = os.path.splitext(file)[1].lower()
                if ext == '.py':
                    languages.append('python')
                elif ext in ['.js', '.jsx']:
                    languages.append('javascript')
                elif ext in ['.ts', '.tsx']:
                    languages.append('typescript')
                elif ext == '.java':
                    languages.append('java')
                elif ext == '.go':
                    languages.append('go')
                elif ext == '.php':
                    languages.append('php')
                elif ext in ['.c', '.h']:
                    languages.append('c')
                elif ext in ['.cpp', '.hpp', '.cc', '.cxx']:
                    languages.append('cpp')
        
        return list(set(languages))
    
    async def run_bandit_scan(self, code_path: str) -> Dict[str, Any]:
        """Запуск Bandit для Python"""
        try:
            cmd = [
                "bandit", "-r", code_path, "-f", "json",
                "--skip", "B101,B601"  # Пропуск некоторых правил
            ]
            
            result = subprocess.run(
                cmd, capture_output=True, text=True, timeout=settings.SAST_TIMEOUT_SECONDS
            )
            
            if result.stdout:
                return json.loads(result.stdout)
            return {"results": []}
            
        except subprocess.TimeoutExpired:
            raise Exception("Bandit scan timeout")
        except Exception as e:
            raise Exception(f"Bandit scan failed: {str(e)}")
    
    async def run_semgrep_scan(self, code_path: str, language: str) -> Dict[str, Any]:
        """Запуск Semgrep"""
        try:
            # Определение набора правил
            ruleset = "p/owasp-top-ten"
            if language == "python":
                ruleset = "p/python"
            elif language in ["javascript", "typescript"]:
                ruleset = "p/javascript"
            elif language == "java":
                ruleset = "p/java"
            elif language == "go":
                ruleset = "p/golang"
            
            cmd = [
                "semgrep", "--config", ruleset, "--json",
                "--timeout", str(settings.SAST_TIMEOUT_SECONDS),
                code_path
            ]
            
            result = subprocess.run(
                cmd, capture_output=True, text=True, timeout=settings.SAST_TIMEOUT_SECONDS
            )
            
            if result.stdout:
                return json.loads(result.stdout)
            return {"results": []}
            
        except subprocess.TimeoutExpired:
            raise Exception("Semgrep scan timeout")
        except Exception as e:
            raise Exception(f"Semgrep scan failed: {str(e)}")
    
    async def run_eslint_scan(self, code_path: str) -> Dict[str, Any]:
        """Запуск ESLint для JavaScript/TypeScript"""
        try:
            cmd = [
                "eslint", code_path, "--format", "json",
                "--ext", ".js,.jsx,.ts,.tsx"
            ]
            
            result = subprocess.run(
                cmd, capture_output=True, text=True, timeout=settings.SAST_TIMEOUT_SECONDS
            )
            
            if result.stdout:
                return json.loads(result.stdout)
            return []
            
        except subprocess.TimeoutExpired:
            raise Exception("ESLint scan timeout")
        except Exception as e:
            # ESLint может возвращать ненулевой код при наличии ошибок
            if result.stdout:
                return json.loads(result.stdout)
            return []
    
    def normalize_vulnerability(self, vuln: Dict[str, Any], tool: str) -> VulnerabilityInfo:
        """Нормализация данных уязвимости в единый формат"""
        
        if tool == "bandit":
            return VulnerabilityInfo(
                id=str(uuid.uuid4()),
                severity=self.map_bandit_severity(vuln.get("issue_severity", "MEDIUM")),
                title=vuln.get("test_name", "Unknown"),
                description=vuln.get("issue_text", ""),
                file_path=vuln.get("filename", ""),
                line_number=vuln.get("line_number", 0),
                rule_id=vuln.get("test_id", ""),
                code_snippet=vuln.get("code", "")
            )
        
        elif tool == "semgrep":
            return VulnerabilityInfo(
                id=str(uuid.uuid4()),
                severity=self.map_semgrep_severity(vuln.get("extra", {}).get("severity", "INFO")),
                title=vuln.get("check_id", "Unknown"),
                description=vuln.get("extra", {}).get("message", ""),
                file_path=vuln.get("path", ""),
                line_number=vuln.get("start", {}).get("line", 0),
                column_number=vuln.get("start", {}).get("col", 0),
                rule_id=vuln.get("check_id", ""),
                owasp_category=vuln.get("extra", {}).get("metadata", {}).get("owasp", ""),
                cwe_id=vuln.get("extra", {}).get("metadata", {}).get("cwe", "")
            )
        
        elif tool == "eslint":
            return VulnerabilityInfo(
                id=str(uuid.uuid4()),
                severity=self.map_eslint_severity(vuln.get("severity", 1)),
                title=vuln.get("ruleId", "Unknown"),
                description=vuln.get("message", ""),
                file_path=vuln.get("filePath", ""),
                line_number=vuln.get("line", 0),
                column_number=vuln.get("column", 0),
                rule_id=vuln.get("ruleId", "")
            )
        
        return VulnerabilityInfo(
            id=str(uuid.uuid4()),
            severity="info",
            title="Unknown",
            description="",
            file_path="",
            line_number=0,
            rule_id=""
        )
    
    def map_bandit_severity(self, severity: str) -> str:
        """Маппинг серьезности Bandit"""
        mapping = {
            "HIGH": VulnerabilitySeverity.HIGH,
            "MEDIUM": VulnerabilitySeverity.MEDIUM,
            "LOW": VulnerabilitySeverity.LOW
        }
        return mapping.get(severity.upper(), VulnerabilitySeverity.INFO)
    
    def map_semgrep_severity(self, severity: str) -> str:
        """Маппинг серьезности Semgrep"""
        mapping = {
            "ERROR": VulnerabilitySeverity.HIGH,
            "WARNING": VulnerabilitySeverity.MEDIUM,
            "INFO": VulnerabilitySeverity.INFO
        }
        return mapping.get(severity.upper(), VulnerabilitySeverity.INFO)
    
    def map_eslint_severity(self, severity: int) -> str:
        """Маппинг серьезности ESLint"""
        if severity == 2:
            return VulnerabilitySeverity.HIGH
        elif severity == 1:
            return VulnerabilitySeverity.MEDIUM
        return VulnerabilitySeverity.INFO
    
    async def analyze_code(self, code_path: str, language: str) -> List[VulnerabilityInfo]:
        """Анализ кода с использованием подходящих инструментов"""
        vulnerabilities = []
        
        # Получение доступных инструментов для языка
        tools = self.supported_tools.get(language, ["semgrep"])
        
        for tool in tools:
            try:
                if tool == "bandit" and language == "python":
                    result = await self.run_bandit_scan(code_path)
                    for vuln in result.get("results", []):
                        vulnerabilities.append(self.normalize_vulnerability(vuln, "bandit"))
                
                elif tool == "semgrep":
                    result = await self.run_semgrep_scan(code_path, language)
                    for vuln in result.get("results", []):
                        vulnerabilities.append(self.normalize_vulnerability(vuln, "semgrep"))
                
                elif tool == "eslint" and language in ["javascript", "typescript"]:
                    result = await self.run_eslint_scan(code_path)
                    for file_result in result:
                        for vuln in file_result.get("messages", []):
                            vuln["filePath"] = file_result.get("filePath", "")
                            vulnerabilities.append(self.normalize_vulnerability(vuln, "eslint"))
                            
            except Exception as e:
                print(f"Error running {tool}: {e}")
                continue
        
        return vulnerabilities

# Инициализация анализатора
analyzer = SASTAnalyzer()

# Background task для анализа
async def perform_sast_analysis(
    scan_id: str,
    code_path: str,
    language: str,
    user_id: str,
    repository_url: Optional[str] = None,
    branch: str = "main"
):
    """Фоновый анализ кода"""
    start_time = datetime.utcnow()
    
    try:
        # Определение языков в проекте
        detected_languages = await analyzer.detect_language(code_path)
        if language not in detected_languages and detected_languages:
            language = detected_languages[0]  # Использовать первый найденный язык
        
        # Анализ кода
        vulnerabilities = await analyzer.analyze_code(code_path, language)
        
        # Подсчет статистики
        severity_counts = {
            VulnerabilitySeverity.CRITICAL: 0,
            VulnerabilitySeverity.HIGH: 0,
            VulnerabilitySeverity.MEDIUM: 0,
            VulnerabilitySeverity.LOW: 0,
            VulnerabilitySeverity.INFO: 0
        }
        
        for vuln in vulnerabilities:
            severity_counts[vuln.severity] += 1
        
        # Подсчет количества файлов
        files_count = 0
        for root, dirs, files in os.walk(code_path):
            files_count += len(files)
        
        summary = SASTSummary(
            total_vulnerabilities=len(vulnerabilities),
            critical_count=severity_counts[VulnerabilitySeverity.CRITICAL],
            high_count=severity_counts[VulnerabilitySeverity.HIGH],
            medium_count=severity_counts[VulnerabilitySeverity.MEDIUM],
            low_count=severity_counts[VulnerabilitySeverity.LOW],
            info_count=severity_counts[VulnerabilitySeverity.INFO],
            files_scanned=files_count,
            languages_detected=detected_languages
        )
        
        end_time = datetime.utcnow()
        scan_duration = int((end_time - start_time).total_seconds())
        
        # Сохранение результатов в БД
        sast_data = {
            "scan_id": scan_id,
            "repository_url": repository_url,
            "branch": branch,
            "vulnerabilities": [vuln.dict() for vuln in vulnerabilities],
            "summary": summary.dict(),
            "report_url": f"/api/sast/reports/{scan_id}",
            "status": "completed",
            "scan_duration": scan_duration,
            "author_id": user_id
        }
        
        await db.create_sast_result(sast_data)
        
        # Логирование
        await db.log_audit_event({
            "user_id": user_id,
            "action": "sast_scan_completed",
            "resource_type": "sast_scan",
            "resource_id": scan_id,
            "details": {
                "language": language,
                "vulnerabilities_found": len(vulnerabilities),
                "duration": scan_duration
            }
        })
        
    except Exception as e:
        # Обновление статуса на ошибку
        supabase.table('sast_results').update({
            "status": "failed",
            "summary": {"error": str(e)}
        }).eq('scan_id', scan_id).execute()
        
        # Логирование ошибки
        await db.log_audit_event({
            "user_id": user_id,
            "action": "sast_scan_failed",
            "resource_type": "sast_scan",
            "resource_id": scan_id,
            "details": {"error": str(e)}
        })
    
    finally:
        # Очистка временных файлов
        try:
            import shutil
            if os.path.exists(code_path):
                shutil.rmtree(code_path)
        except:
            pass

# Роутеры
@router.post("/scan/upload", response_model=Dict[str, str])
async def scan_uploaded_file(
    background_tasks: BackgroundTasks,
    language: str = Form(...),
    file: UploadFile = File(...),
    token: str = Depends(oauth2_scheme)
):
    """SAST анализ загруженного файла/архива"""
    
    payload = verify_token(token)
    user_id = payload.get("user_id")
    
    # Проверка языка
    if language not in settings.SAST_SUPPORTED_LANGUAGES:
        raise HTTPException(
            status_code=400,
            detail=f"Language not supported. Supported: {', '.join(settings.SAST_SUPPORTED_LANGUAGES)}"
        )
    
    # Проверка размера файла
    content = await file.read()
    if len(content) > settings.SAST_MAX_FILE_SIZE:
        raise HTTPException(
            status_code=400,
            detail=f"File too large. Max size: {settings.SAST_MAX_FILE_SIZE // (1024*1024)} MB"
        )
    
    await file.seek(0)
    
    try:
        # Создание временных директорий
        temp_dir = tempfile.mkdtemp()
        file_path = os.path.join(temp_dir, file.filename)
        
        # Сохранение файла
        async with aiofiles.open(file_path, 'wb') as f:
            await f.write(content)
        
        # Извлечение архива если нужно
        code_path = temp_dir
        if file.filename.endswith(('.zip', '.tar.gz', '.tar')):
            extract_dir = os.path.join(temp_dir, 'extracted')
            os.makedirs(extract_dir)
            await analyzer.extract_archive(file_path, extract_dir)
            code_path = extract_dir
        
        # Генерация scan_id
        scan_id = str(uuid.uuid4())
        
        # Создание записи в БД
        sast_data = {
            "scan_id": scan_id,
            "vulnerabilities": [],
            "summary": {},
            "report_url": f"/api/sast/reports/{scan_id}",
            "status": "running",
            "author_id": user_id
        }
        
        await db.create_sast_result(sast_data)
        
        # Запуск анализа в фоне
        background_tasks.add_task(
            perform_sast_analysis,
            scan_id, code_path, language, user_id
        )
        
        return {
            "scan_id": scan_id,
            "status": "started",
            "message": "SAST analysis started"
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Scan failed: {str(e)}")

@router.post("/scan/repository", response_model=Dict[str, str])
async def scan_repository(
    background_tasks: BackgroundTasks,
    scan_request: SASTScanRequest,
    token: str = Depends(oauth2_scheme)
):
    """SAST анализ Git репозитория"""
    
    payload = verify_token(token)
    user_id = payload.get("user_id")
    
    if not scan_request.repository_url:
        raise HTTPException(status_code=400, detail="Repository URL is required")
    
    # Проверка языка
    if scan_request.language not in settings.SAST_SUPPORTED_LANGUAGES:
        raise HTTPException(
            status_code=400,
            detail=f"Language not supported. Supported: {', '.join(settings.SAST_SUPPORTED_LANGUAGES)}"
        )
    
    try:
        # Клонирование репозитория
        temp_dir = tempfile.mkdtemp()
        
        clone_cmd = [
            "git", "clone", "--depth", "1",
            "-b", scan_request.branch,
            scan_request.repository_url,
            temp_dir
        ]
        
        result = subprocess.run(
            clone_cmd, capture_output=True, text=True, timeout=300
        )
        
        if result.returncode != 0:
            raise Exception(f"Git clone failed: {result.stderr}")
        
        # Генерация scan_id
        scan_id = str(uuid.uuid4())
        
        # Создание записи в БД
        sast_data = {
            "scan_id": scan_id,
            "repository_url": scan_request.repository_url,
            "branch": scan_request.branch,
            "vulnerabilities": [],
            "summary": {},
            "report_url": f"/api/sast/reports/{scan_id}",
            "status": "running",
            "author_id": user_id
        }
        
        await db.create_sast_result(sast_data)
        
        # Запуск анализа в фоне
        background_tasks.add_task(
            perform_sast_analysis,
            scan_id, temp_dir, scan_request.language, user_id,
            scan_request.repository_url, scan_request.branch
        )
        
        return {
            "scan_id": scan_id,
            "status": "started",
            "message": "Repository scan started"
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Repository scan failed: {str(e)}")

@router.get("/results/{scan_id}", response_model=SASTResultResponse)
async def get_scan_result(scan_id: str, token: str = Depends(oauth2_scheme)):
    """Получение результатов SAST анализа"""
    
    verify_token(token)
    
    try:
        result = supabase.table('sast_results').select('*').eq('scan_id', scan_id).execute()
        
        if not result.data:
            raise HTTPException(status_code=404, detail="Scan not found")
        
        scan_data = result.data[0]
        
        # Преобразование vulnerabilities в правильный формат
        vulnerabilities = [
            VulnerabilityInfo(**vuln) for vuln in scan_data.get('vulnerabilities', [])
        ]
        
        return SASTResultResponse(
            id=scan_data['id'],
            scan_id=scan_data['scan_id'],
            repository_url=scan_data.get('repository_url'),
            commit_id=scan_data.get('commit_id'),
            branch=scan_data.get('branch', 'main'),
            vulnerabilities=vulnerabilities,
            summary=scan_data.get('summary', {}),
            report_url=scan_data['report_url'],
            status=scan_data['status'],
            scan_duration=scan_data.get('scan_duration'),
            created_at=datetime.fromisoformat(scan_data['created_at'])
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get scan result: {str(e)}")

@router.get("/results", response_model=List[SASTResultResponse])
async def get_scan_results(
    limit: int = 50,
    offset: int = 0,
    status: Optional[str] = None,
    token: str = Depends(oauth2_scheme)
):
    """Получение списка результатов SAST анализов"""
    
    verify_token(token)
    
    try:
        query = supabase.table('sast_results').select('*')
        
        if status:
            query = query.eq('status', status)
        
        result = query.order('created_at', desc=True).range(offset, offset + limit - 1).execute()
        
        scans = []
        for scan_data in result.data:
            vulnerabilities = [
                VulnerabilityInfo(**vuln) for vuln in scan_data.get('vulnerabilities', [])
            ]
            
            scans.append(SASTResultResponse(
                id=scan_data['id'],
                scan_id=scan_data['scan_id'],
                repository_url=scan_data.get('repository_url'),
                commit_id=scan_data.get('commit_id'),
                branch=scan_data.get('branch', 'main'),
                vulnerabilities=vulnerabilities,
                summary=scan_data.get('summary', {}),
                report_url=scan_data['report_url'],
                status=scan_data['status'],
                scan_duration=scan_data.get('scan_duration'),
                created_at=datetime.fromisoformat(scan_data['created_at'])
            ))
        
        return scans
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get scan results: {str(e)}")

@router.delete("/results/{scan_id}")
async def delete_scan_result(scan_id: str, token: str = Depends(oauth2_scheme)):
    """Удаление результата SAST анализа"""
    
    payload = verify_token(token)
    user_id = payload.get("user_id")
    user_role = payload.get("role")
    
    # Проверка прав (только админы могут удалять)
    if user_role not in ["admin", "super_admin"]:
        raise HTTPException(status_code=403, detail="Insufficient permissions")
    
    try:
        # Проверка существования
        result = supabase.table('sast_results').select('*').eq('scan_id', scan_id).execute()
        if not result.data:
            raise HTTPException(status_code=404, detail="Scan not found")
        
        # Удаление
        supabase.table('sast_results').delete().eq('scan_id', scan_id).execute()
        
        # Логирование
        await db.log_audit_event({
            "user_id": user_id,
            "action": "sast_result_deleted",
            "resource_type": "sast_scan",
            "resource_id": scan_id,
            "details": {"scan_id": scan_id}
        })
        
        return {"message": "Scan result deleted successfully"}
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Delete failed: {str(e)}")

@router.get("/languages")
async def get_supported_languages(token: str = Depends(oauth2_scheme)):
    """Получение списка поддерживаемых языков"""
    
    verify_token(token)
    
    return {
        "supported_languages": settings.SAST_SUPPORTED_LANGUAGES,
        "tools": analyzer.supported_tools
    } 