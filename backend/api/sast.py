from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form, Query, BackgroundTasks
from sqlalchemy.orm import Session
from typing import List, Optional, Dict, Any
import json
import uuid
import aiofiles
import asyncio
import subprocess
import tempfile
import shutil
import zipfile
from pathlib import Path
from datetime import datetime
import logging
import os
import git
from urllib.parse import urlparse

from ..main import get_db, get_current_active_user, require_role, redis_client
from ..models import User, SASTResult, AuditLog
from ..schemas import SASTScanRequest, SASTResultResponse

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/sast", tags=["sast"])

# Поддерживаемые языки программирования
SUPPORTED_LANGUAGES = {
    "python": {
        "extensions": [".py"],
        "tools": ["bandit", "semgrep"],
        "patterns": ["*.py"]
    },
    "javascript": {
        "extensions": [".js", ".jsx", ".ts", ".tsx"],
        "tools": ["eslint", "semgrep"],
        "patterns": ["*.js", "*.jsx", "*.ts", "*.tsx"]
    },
    "java": {
        "extensions": [".java"],
        "tools": ["semgrep"],
        "patterns": ["*.java"]
    },
    "go": {
        "extensions": [".go"],
        "tools": ["semgrep", "gosec"],
        "patterns": ["*.go"]
    },
    "php": {
        "extensions": [".php"],
        "tools": ["semgrep"],
        "patterns": ["*.php"]
    },
    "c": {
        "extensions": [".c", ".h"],
        "tools": ["semgrep"],
        "patterns": ["*.c", "*.h"]
    },
    "cpp": {
        "extensions": [".cpp", ".hpp", ".cc", ".cxx"],
        "tools": ["semgrep"],
        "patterns": ["*.cpp", "*.hpp", "*.cc", "*.cxx"]
    }
}

# Категории уязвимостей
VULNERABILITY_CATEGORIES = {
    "injection": "Injection Flaws",
    "broken_auth": "Broken Authentication",
    "sensitive_exposure": "Sensitive Data Exposure",
    "xml_external": "XML External Entities",
    "broken_access": "Broken Access Controls",
    "security_misconfig": "Security Misconfiguration",
    "xss": "Cross-Site Scripting",
    "insecure_deserialization": "Insecure Deserialization",
    "known_vulnerabilities": "Using Components with Known Vulnerabilities",
    "insufficient_logging": "Insufficient Logging & Monitoring"
}

def detect_project_language(project_path: Path) -> Dict[str, int]:
    """Определение языков программирования в проекте"""
    language_stats = {}
    
    for lang, config in SUPPORTED_LANGUAGES.items():
        count = 0
        for pattern in config["patterns"]:
            count += len(list(project_path.rglob(pattern)))
        if count > 0:
            language_stats[lang] = count
    
    return language_stats

async def run_bandit_scan(project_path: Path) -> Dict[str, Any]:
    """Запуск Bandit для Python кода"""
    try:
        cmd = [
            "bandit", 
            "-r", str(project_path),
            "-f", "json",
            "-o", str(project_path / "bandit_results.json")
        ]
        
        process = await asyncio.create_subprocess_exec(
            *cmd,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE
        )
        
        stdout, stderr = await process.communicate()
        
        # Чтение результатов
        results_file = project_path / "bandit_results.json"
        if results_file.exists():
            with open(results_file, 'r') as f:
                results = json.load(f)
            results_file.unlink()  # Удаляем временный файл
            return results
        
        return {"error": "Bandit не создал файл результатов"}
        
    except Exception as e:
        logger.error(f"Ошибка запуска Bandit: {e}")
        return {"error": str(e)}

async def run_semgrep_scan(project_path: Path, language: str = None) -> Dict[str, Any]:
    """Запуск Semgrep анализа"""
    try:
        cmd = ["semgrep", "--json", "--config=auto"]
        
        if language:
            # Добавляем специфичные для языка правила
            lang_configs = {
                "python": "--config=p/python",
                "javascript": "--config=p/javascript",
                "java": "--config=p/java",
                "go": "--config=p/go",
                "php": "--config=p/php"
            }
            if language in lang_configs:
                cmd.append(lang_configs[language])
        
        cmd.extend(["--output", str(project_path / "semgrep_results.json")])
        cmd.append(str(project_path))
        
        process = await asyncio.create_subprocess_exec(
            *cmd,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
            cwd=project_path
        )
        
        stdout, stderr = await process.communicate()
        
        # Чтение результатов
        results_file = project_path / "semgrep_results.json"
        if results_file.exists():
            with open(results_file, 'r') as f:
                results = json.load(f)
            results_file.unlink()
            return results
        
        return {"error": "Semgrep не создал файл результатов"}
        
    except Exception as e:
        logger.error(f"Ошибка запуска Semgrep: {e}")
        return {"error": str(e)}

def categorize_vulnerabilities(scan_results: List[Dict]) -> Dict[str, Any]:
    """Категоризация уязвимостей по критичности"""
    categories = {
        "critical": [],
        "high": [],
        "medium": [],
        "low": [],
        "info": []
    }
    
    severity_mapping = {
        "CRITICAL": "critical",
        "HIGH": "high", 
        "MEDIUM": "medium",
        "LOW": "low",
        "INFO": "info",
        "WARNING": "medium",
        "ERROR": "high"
    }
    
    for vuln in scan_results:
        severity = vuln.get("severity", "INFO").upper()
        category = severity_mapping.get(severity, "info")
        categories[category].append(vuln)
    
    return {
        "vulnerabilities": categories,
        "summary": {
            "critical": len(categories["critical"]),
            "high": len(categories["high"]),
            "medium": len(categories["medium"]),
            "low": len(categories["low"]),
            "info": len(categories["info"]),
            "total": sum(len(v) for v in categories.values())
        }
    }

async def clone_repository(repo_url: str, branch: str = "main") -> Path:
    """Клонирование Git репозитория"""
    temp_dir = Path(tempfile.mkdtemp(prefix="sast_"))
    
    try:
        # Валидация URL
        parsed_url = urlparse(repo_url)
        if not parsed_url.scheme or not parsed_url.netloc:
            raise ValueError("Невалидный URL репозитория")
        
        # Клонирование
        repo = git.Repo.clone_from(repo_url, temp_dir, branch=branch, depth=1)
        logger.info(f"Репозиторий клонирован: {repo_url} ({branch})")
        
        return temp_dir
        
    except Exception as e:
        # Очистка при ошибке
        if temp_dir.exists():
            shutil.rmtree(temp_dir)
        raise HTTPException(
            status_code=400,
            detail=f"Ошибка клонирования репозитория: {str(e)}"
        )

async def extract_archive(file_path: Path) -> Path:
    """Извлечение архива с кодом"""
    temp_dir = Path(tempfile.mkdtemp(prefix="sast_"))
    
    try:
        if file_path.suffix.lower() == ".zip":
            with zipfile.ZipFile(file_path, 'r') as zip_file:
                zip_file.extractall(temp_dir)
        elif file_path.suffix.lower() in [".tar", ".tar.gz", ".tgz"]:
            import tarfile
            with tarfile.open(file_path, 'r:*') as tar_file:
                tar_file.extractall(temp_dir)
        else:
            raise ValueError("Неподдерживаемый формат архива")
        
        return temp_dir
        
    except Exception as e:
        if temp_dir.exists():
            shutil.rmtree(temp_dir)
        raise HTTPException(
            status_code=400,
            detail=f"Ошибка извлечения архива: {str(e)}"
        )

async def perform_sast_scan(project_path: Path, scan_id: int, language: str = None):
    """Выполнение SAST анализа"""
    db = SessionLocal()
    
    try:
        # Обновление статуса
        scan_record = db.query(SASTResult).filter(SASTResult.id == scan_id).first()
        if not scan_record:
            return
        
        scan_record.scan_status = "running"
        db.commit()
        
        # Определение языков в проекте
        if not language:
            languages = detect_project_language(project_path)
            primary_language = max(languages.keys(), key=lambda k: languages[k]) if languages else None
        else:
            primary_language = language
        
        all_results = []
        
        # Запуск сканеров в зависимости от языка
        if primary_language == "python":
            bandit_results = await run_bandit_scan(project_path)
            if "results" in bandit_results:
                all_results.extend(bandit_results["results"])
        
        # Semgrep для всех языков
        semgrep_results = await run_semgrep_scan(project_path, primary_language)
        if "results" in semgrep_results:
            all_results.extend(semgrep_results["results"])
        
        # Категоризация результатов
        categorized = categorize_vulnerabilities(all_results)
        
        # Обновление результатов в БД
        scan_record.scan_results = json.dumps({
            "language": primary_language,
            "scanners_used": ["semgrep"] + (["bandit"] if primary_language == "python" else []),
            "raw_results": all_results,
            "categorized": categorized
        })
        
        scan_record.vulnerabilities_count = categorized["summary"]["total"]
        scan_record.critical_count = categorized["summary"]["critical"]
        scan_record.high_count = categorized["summary"]["high"]
        scan_record.medium_count = categorized["summary"]["medium"]
        scan_record.low_count = categorized["summary"]["low"]
        scan_record.scan_status = "completed"
        scan_record.completed_at = datetime.utcnow()
        
        db.commit()
        
        logger.info(f"SAST сканирование завершено: {scan_id}")
        
    except Exception as e:
        logger.error(f"Ошибка SAST сканирования {scan_id}: {e}")
        
        scan_record.scan_status = "failed"
        scan_record.scan_results = json.dumps({"error": str(e)})
        scan_record.completed_at = datetime.utcnow()
        db.commit()
        
    finally:
        db.close()
        # Очистка временных файлов
        if project_path.exists():
            shutil.rmtree(project_path)

@router.post("/scan/repository", response_model=SASTResultResponse)
async def scan_repository(
    repository_url: str = Form(...),
    branch: str = Form("main"),
    project_name: str = Form(...),
    background_tasks: BackgroundTasks = BackgroundTasks(),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Запуск SAST анализа Git репозитория"""
    
    # Создание записи о сканировании
    scan_record = SASTResult(
        project_name=project_name,
        repository_url=repository_url,
        branch=branch,
        scan_status="pending"
    )
    
    db.add(scan_record)
    db.commit()
    db.refresh(scan_record)
    
    # Логирование
    db.add(AuditLog(
        user_id=current_user.id,
        action="START_SAST_SCAN",
        resource="sast",
        resource_id=str(scan_record.id),
        details=json.dumps({
            "project_name": project_name,
            "repository_url": repository_url,
            "branch": branch
        })
    ))
    db.commit()
    
    # Запуск фонового сканирования
    async def scan_task():
        project_path = None
        try:
            project_path = await clone_repository(repository_url, branch)
            await perform_sast_scan(project_path, scan_record.id)
        except Exception as e:
            logger.error(f"Ошибка в фоновом сканировании: {e}")
            if project_path and project_path.exists():
                shutil.rmtree(project_path)
    
    background_tasks.add_task(scan_task)
    
    return scan_record

@router.post("/scan/upload", response_model=SASTResultResponse)
async def scan_uploaded_code(
    project_name: str = Form(...),
    language: Optional[str] = Form(None),
    file: UploadFile = File(...),
    background_tasks: BackgroundTasks = BackgroundTasks(),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Запуск SAST анализа загруженного архива с кодом"""
    
    # Проверка размера файла (500MB)
    if file.size > 500 * 1024 * 1024:
        raise HTTPException(
            status_code=400,
            detail="Размер файла не должен превышать 500MB"
        )
    
    # Проверка формата файла
    file_extension = file.filename.split('.')[-1].lower()
    if file_extension not in ["zip", "tar", "gz", "tgz"]:
        raise HTTPException(
            status_code=400,
            detail="Поддерживаемые форматы: .zip, .tar, .tar.gz, .tgz"
        )
    
    # Проверка языка
    if language and language not in SUPPORTED_LANGUAGES:
        raise HTTPException(
            status_code=400,
            detail=f"Неподдерживаемый язык. Доступные: {list(SUPPORTED_LANGUAGES.keys())}"
        )
    
    # Сохранение файла
    file_id = str(uuid.uuid4())
    filename = f"{file_id}.{file_extension}"
    file_path = Path("uploads/code") / filename
    
    try:
        async with aiofiles.open(file_path, 'wb') as f:
            content = await file.read()
            await f.write(content)
    except Exception as e:
        logger.error(f"Ошибка сохранения файла: {e}")
        raise HTTPException(status_code=500, detail="Ошибка сохранения файла")
    
    # Создание записи о сканировании
    scan_record = SASTResult(
        project_name=project_name,
        repository_url=f"upload://{filename}",
        branch="uploaded",
        scan_status="pending"
    )
    
    db.add(scan_record)
    db.commit()
    db.refresh(scan_record)
    
    # Логирование
    db.add(AuditLog(
        user_id=current_user.id,
        action="START_SAST_UPLOAD_SCAN",
        resource="sast",
        resource_id=str(scan_record.id),
        details=json.dumps({
            "project_name": project_name,
            "language": language,
            "file_size": file.size,
            "filename": file.filename
        })
    ))
    db.commit()
    
    # Запуск фонового сканирования
    async def scan_task():
        project_path = None
        try:
            project_path = await extract_archive(file_path)
            await perform_sast_scan(project_path, scan_record.id, language)
        except Exception as e:
            logger.error(f"Ошибка в фоновом сканировании: {e}")
        finally:
            # Удаление загруженного архива
            if file_path.exists():
                file_path.unlink()
            if project_path and project_path.exists():
                shutil.rmtree(project_path)
    
    background_tasks.add_task(scan_task)
    
    return scan_record

@router.get("/scans", response_model=List[SASTResultResponse])
async def get_scans(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, le=1000),
    status: Optional[str] = Query(None),
    project_name: Optional[str] = Query(None),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Получение списка SAST сканирований"""
    
    query = db.query(SASTResult)
    
    if status:
        query = query.filter(SASTResult.scan_status == status)
    
    if project_name:
        search_term = f"%{project_name}%"
        query = query.filter(SASTResult.project_name.ilike(search_term))
    
    scans = query.order_by(SASTResult.started_at.desc()).offset(skip).limit(limit).all()
    
    return scans

@router.get("/scans/{scan_id}", response_model=SASTResultResponse)
async def get_scan_result(
    scan_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Получение результатов SAST сканирования"""
    
    scan = db.query(SASTResult).filter(SASTResult.id == scan_id).first()
    if not scan:
        raise HTTPException(status_code=404, detail="Сканирование не найдено")
    
    # Логирование просмотра результатов
    db.add(AuditLog(
        user_id=current_user.id,
        action="VIEW_SAST_RESULT",
        resource="sast",
        resource_id=str(scan_id)
    ))
    db.commit()
    
    return scan

@router.get("/scans/{scan_id}/report")
async def get_scan_report(
    scan_id: int,
    format: str = Query("json", regex="^(json|csv|pdf)$"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Экспорт отчета о сканировании"""
    
    scan = db.query(SASTResult).filter(SASTResult.id == scan_id).first()
    if not scan:
        raise HTTPException(status_code=404, detail="Сканирование не найдено")
    
    if scan.scan_status != "completed":
        raise HTTPException(status_code=400, detail="Сканирование не завершено")
    
    scan_results = json.loads(scan.scan_results) if scan.scan_results else {}
    
    if format == "json":
        return {
            "scan_id": scan_id,
            "project_name": scan.project_name,
            "scan_date": scan.started_at,
            "completion_date": scan.completed_at,
            "summary": {
                "total_vulnerabilities": scan.vulnerabilities_count,
                "critical": scan.critical_count,
                "high": scan.high_count,
                "medium": scan.medium_count,
                "low": scan.low_count
            },
            "detailed_results": scan_results
        }
    elif format == "csv":
        # Генерация CSV отчета
        import csv
        import io
        
        output = io.StringIO()
        writer = csv.writer(output)
        
        # Заголовки
        writer.writerow([
            "File", "Line", "Severity", "Rule", "Message", "Category"
        ])
        
        # Данные
        if "categorized" in scan_results:
            for severity, vulns in scan_results["categorized"]["vulnerabilities"].items():
                for vuln in vulns:
                    writer.writerow([
                        vuln.get("path", ""),
                        vuln.get("line", ""),
                        severity.upper(),
                        vuln.get("rule_id", ""),
                        vuln.get("message", ""),
                        vuln.get("category", "")
                    ])
        
        return Response(
            content=output.getvalue(),
            media_type="text/csv",
            headers={"Content-Disposition": f"attachment; filename=sast_report_{scan_id}.csv"}
        )
    else:
        raise HTTPException(status_code=501, detail="PDF экспорт пока не реализован")

@router.delete("/scans/{scan_id}")
async def delete_scan(
    scan_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role(["admin", "super_admin"]))
):
    """Удаление результатов сканирования"""
    
    scan = db.query(SASTResult).filter(SASTResult.id == scan_id).first()
    if not scan:
        raise HTTPException(status_code=404, detail="Сканирование не найдено")
    
    db.delete(scan)
    
    # Логирование
    db.add(AuditLog(
        user_id=current_user.id,
        action="DELETE_SAST_SCAN",
        resource="sast",
        resource_id=str(scan_id),
        details=json.dumps({"project_name": scan.project_name})
    ))
    db.commit()
    
    return {"message": "Результаты сканирования удалены"}

@router.get("/stats/summary")
async def get_sast_stats(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Статистика SAST сканирований"""
    
    total_scans = db.query(SASTResult).count()
    completed_scans = db.query(SASTResult).filter(SASTResult.scan_status == "completed").count()
    
    # Суммарная статистика по уязвимостям
    total_vulns = db.query(SASTResult).with_entities(
        func.sum(SASTResult.vulnerabilities_count).label('total'),
        func.sum(SASTResult.critical_count).label('critical'),
        func.sum(SASTResult.high_count).label('high'),
        func.sum(SASTResult.medium_count).label('medium'),
        func.sum(SASTResult.low_count).label('low')
    ).first()
    
    return {
        "total_scans": total_scans,
        "completed_scans": completed_scans,
        "running_scans": db.query(SASTResult).filter(SASTResult.scan_status == "running").count(),
        "failed_scans": db.query(SASTResult).filter(SASTResult.scan_status == "failed").count(),
        "vulnerability_summary": {
            "total": total_vulns.total or 0,
            "critical": total_vulns.critical or 0,
            "high": total_vulns.high or 0,
            "medium": total_vulns.medium or 0,
            "low": total_vulns.low or 0
        },
        "supported_languages": list(SUPPORTED_LANGUAGES.keys())
    } 