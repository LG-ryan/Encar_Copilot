"""
커스텀 예외 클래스
"""
from typing import Optional, Dict, Any


class EncarCopilotException(Exception):
    """기본 예외 클래스"""
    
    def __init__(
        self,
        message: str,
        error_code: str = "internal_error",
        status_code: int = 500,
        details: Optional[Dict[str, Any]] = None
    ):
        self.message = message
        self.error_code = error_code
        self.status_code = status_code
        self.details = details or {}
        super().__init__(message)


class AuthenticationError(EncarCopilotException):
    """인증 실패"""
    
    def __init__(self, message: str = "인증이 필요합니다", details: Optional[Dict] = None):
        super().__init__(
            message=message,
            error_code="authentication_required",
            status_code=401,
            details=details
        )


class AuthorizationError(EncarCopilotException):
    """권한 부족"""
    
    def __init__(self, message: str = "권한이 없습니다", details: Optional[Dict] = None):
        super().__init__(
            message=message,
            error_code="insufficient_permissions",
            status_code=403,
            details=details
        )


class ResourceNotFoundError(EncarCopilotException):
    """리소스 없음"""
    
    def __init__(self, message: str = "요청한 리소스를 찾을 수 없습니다", details: Optional[Dict] = None):
        super().__init__(
            message=message,
            error_code="not_found",
            status_code=404,
            details=details
        )


class ValidationError(EncarCopilotException):
    """입력 검증 실패"""
    
    def __init__(self, message: str = "입력 값이 유효하지 않습니다", details: Optional[Dict] = None):
        super().__init__(
            message=message,
            error_code="validation_error",
            status_code=422,
            details=details
        )


class RateLimitError(EncarCopilotException):
    """요청 제한 초과"""
    
    def __init__(self, message: str = "요청 횟수를 초과했습니다. 잠시 후 다시 시도해주세요", details: Optional[Dict] = None):
        super().__init__(
            message=message,
            error_code="rate_limit_exceeded",
            status_code=429,
            details=details
        )


class LLMServiceError(EncarCopilotException):
    """LLM 서비스 오류"""
    
    def __init__(self, message: str = "AI 서비스에 일시적인 문제가 발생했습니다", details: Optional[Dict] = None):
        super().__init__(
            message=message,
            error_code="llm_service_error",
            status_code=503,
            details=details
        )


class DatabaseError(EncarCopilotException):
    """데이터베이스 오류"""
    
    def __init__(self, message: str = "데이터베이스 오류가 발생했습니다", details: Optional[Dict] = None):
        super().__init__(
            message=message,
            error_code="database_error",
            status_code=500,
            details=details
        )

