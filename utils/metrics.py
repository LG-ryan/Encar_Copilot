"""
Prometheus 메트릭 수집
"""
from prometheus_client import Counter, Histogram, Gauge, generate_latest, CONTENT_TYPE_LATEST
from functools import wraps
import time
from typing import Optional


# ====================  메트릭 정의 ====================

# API 요청 카운터
api_requests_total = Counter(
    'api_requests_total',
    'Total API requests',
    ['method', 'endpoint', 'status']
)

# API 응답 시간
api_response_time = Histogram(
    'api_response_seconds',
    'API response time in seconds',
    ['method', 'endpoint']
)

# LLM 요청 카운터
llm_requests_total = Counter(
    'llm_requests_total',
    'Total LLM API requests',
    ['status']  # success, error, cached
)

# LLM 응답 시간
llm_response_time = Histogram(
    'llm_response_seconds',
    'LLM response time in seconds'
)

# 캐시 히트/미스
cache_operations_total = Counter(
    'cache_operations_total',
    'Cache operations',
    ['operation']  # hit, miss
)

# 동시 사용자 수
active_users = Gauge(
    'active_users',
    'Number of active users'
)

# 피드백 카운터
feedback_total = Counter(
    'feedback_total',
    'Total user feedback',
    ['type']  # helpful, not_helpful
)

# 에러 카운터
errors_total = Counter(
    'errors_total',
    'Total errors',
    ['error_type']
)


# ==================== 헬퍼 함수 ====================

def track_api_request(method: str, endpoint: str, status: int):
    """API 요청 추적"""
    api_requests_total.labels(method=method, endpoint=endpoint, status=status).inc()


def track_llm_request(status: str):
    """LLM 요청 추적"""
    llm_requests_total.labels(status=status).inc()


def track_cache_operation(operation: str):
    """캐시 작업 추적"""
    cache_operations_total.labels(operation=operation).inc()


def track_feedback(is_helpful: bool):
    """피드백 추적"""
    feedback_type = "helpful" if is_helpful else "not_helpful"
    feedback_total.labels(type=feedback_type).inc()


def track_error(error_type: str):
    """에러 추적"""
    errors_total.labels(error_type=error_type).inc()


def get_metrics() -> tuple[bytes, str]:
    """Prometheus 메트릭 반환"""
    return generate_latest(), CONTENT_TYPE_LATEST


# ==================== 데코레이터 ====================

def track_time(metric: Histogram):
    """시간 측정 데코레이터"""
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            start_time = time.time()
            try:
                result = func(*args, **kwargs)
                return result
            finally:
                duration = time.time() - start_time
                metric.observe(duration)
        return wrapper
    return decorator


def track_time_async(metric: Histogram):
    """비동기 시간 측정 데코레이터"""
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            start_time = time.time()
            try:
                result = await func(*args, **kwargs)
                return result
            finally:
                duration = time.time() - start_time
                metric.observe(duration)
        return wrapper
    return decorator

