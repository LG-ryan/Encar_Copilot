"""
구조화된 로깅 시스템
JSON 포맷 로그 + 파일 로테이션 + 개인정보 마스킹
"""
import logging
import json
from datetime import datetime
from pathlib import Path
from logging.handlers import RotatingFileHandler
from typing import Any, Dict, Optional
from .privacy import mask_pii_in_text, safe_log_dict


class JSONFormatter(logging.Formatter):
    """JSON 포맷 로거"""
    
    def format(self, record: logging.LogRecord) -> str:
        """로그 레코드를 JSON으로 변환"""
        log_obj = {
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
            "module": record.module,
            "function": record.funcName,
            "line": record.lineno,
        }
        
        # 추가 필드 (extra 파라미터로 전달된 것들)
        if hasattr(record, "user_id"):
            log_obj["user_id"] = getattr(record, "user_id")
        if hasattr(record, "trace_id"):
            log_obj["trace_id"] = getattr(record, "trace_id")
        if hasattr(record, "duration_ms"):
            log_obj["duration_ms"] = getattr(record, "duration_ms")
        
        # 예외 정보
        if record.exc_info:
            log_obj["exception"] = self.formatException(record.exc_info)
        
        return json.dumps(log_obj, ensure_ascii=False)


class MaskingFormatter(logging.Formatter):
    """개인정보 마스킹 포매터"""
    
    def format(self, record: logging.LogRecord) -> str:
        """로그 메시지에서 개인정보 마스킹"""
        # 원본 메시지 마스킹
        original_msg = record.getMessage()
        record.msg = mask_pii_in_text(original_msg)
        record.args = ()  # args는 이미 getMessage()에서 처리됨
        
        return super().format(record)


def setup_logger(
    name: str = "encar_copilot",
    log_file: Optional[str] = None,
    log_level: str = "INFO",
    max_bytes: int = 10 * 1024 * 1024,  # 10MB
    backup_count: int = 5,
    enable_console: bool = True,
    enable_file: bool = True,
    json_format: bool = True
) -> logging.Logger:
    """
    로거 설정
    
    Args:
        name: 로거 이름
        log_file: 로그 파일 경로
        log_level: 로그 레벨
        max_bytes: 파일 최대 크기
        backup_count: 백업 파일 개수
        enable_console: 콘솔 출력 활성화
        enable_file: 파일 출력 활성화
        json_format: JSON 포맷 사용
        
    Returns:
        설정된 로거
    """
    logger = logging.getLogger(name)
    logger.setLevel(getattr(logging, log_level.upper()))
    logger.handlers.clear()  # 기존 핸들러 제거
    
    # 콘솔 핸들러
    if enable_console:
        console_handler = logging.StreamHandler()
        console_handler.setLevel(logging.INFO)
        
        if json_format:
            console_handler.setFormatter(JSONFormatter())
        else:
            console_formatter = MaskingFormatter(
                '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
            )
            console_handler.setFormatter(console_formatter)
        
        logger.addHandler(console_handler)
    
    # 파일 핸들러
    if enable_file and log_file:
        # 로그 디렉토리 생성
        log_path = Path(log_file)
        log_path.parent.mkdir(parents=True, exist_ok=True)
        
        file_handler = RotatingFileHandler(
            log_file,
            maxBytes=max_bytes,
            backupCount=backup_count,
            encoding='utf-8'
        )
        file_handler.setLevel(logging.DEBUG)
        
        if json_format:
            file_handler.setFormatter(JSONFormatter())
        else:
            file_formatter = MaskingFormatter(
                '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
            )
            file_handler.setFormatter(file_formatter)
        
        logger.addHandler(file_handler)
    
    return logger


# 글로벌 로거 인스턴스
_logger: Optional[logging.Logger] = None


def get_logger() -> logging.Logger:
    """글로벌 로거 반환"""
    global _logger
    if _logger is None:
        from config.settings import settings
        _logger = setup_logger(
            name="encar_copilot",
            log_file=settings.LOG_FILE,
            log_level=settings.LOG_LEVEL,
            max_bytes=settings.LOG_MAX_BYTES,
            backup_count=settings.LOG_BACKUP_COUNT,
            enable_console=True,
            enable_file=True,
            json_format=(settings.ENVIRONMENT == "production")
        )
    return _logger


def log_api_request(
    method: str,
    path: str,
    user_id: Optional[str] = None,
    duration_ms: Optional[float] = None,
    status_code: Optional[int] = None
):
    """API 요청 로깅"""
    logger = get_logger()
    extra = {}
    
    if user_id:
        extra["user_id"] = user_id
    if duration_ms:
        extra["duration_ms"] = duration_ms
    
    message = f"{method} {path}"
    if status_code:
        message += f" - {status_code}"
    
    logger.info(message, extra=extra)


def log_llm_request(
    question: str,
    matched_category: Optional[str] = None,
    cached: bool = False,
    duration_ms: Optional[float] = None
):
    """LLM 요청 로깅 (개인정보 자동 마스킹)"""
    logger = get_logger()
    
    # 질문은 자동으로 마스킹됨 (MaskingFormatter)
    message = f"LLM 검색: {question[:100]}"
    
    extra = {
        "cached": cached,
        "matched_category": matched_category
    }
    if duration_ms:
        extra["duration_ms"] = duration_ms
    
    logger.info(message, extra=extra)


def log_error(
    message: str,
    error: Optional[Exception] = None,
    context: Optional[Dict[str, Any]] = None
):
    """에러 로깅"""
    logger = get_logger()
    
    extra = {}
    if context:
        # 컨텍스트 데이터 안전하게 변환
        extra = safe_log_dict(context)
    
    if error:
        logger.error(message, exc_info=error, extra=extra)
    else:
        logger.error(message, extra=extra)

