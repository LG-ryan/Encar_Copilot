"""
애플리케이션 설정 관리
환경 변수 및 기본 설정 중앙화
"""
from pydantic_settings import BaseSettings
from typing import Optional, List


class Settings(BaseSettings):
    """애플리케이션 설정"""
    
    # 서버 설정
    HOST: str = "0.0.0.0"
    PORT: int = 8000
    RELOAD: bool = True
    LOG_LEVEL: str = "info"
    ENVIRONMENT: str = "development"  # development, staging, production
    
    # 보안 설정
    OPENAI_API_KEY: Optional[str] = None  # 환경변수에서 로드
    SECRET_KEY: str = "encar-copilot-secret-key-change-in-production"  # JWT/세션 암호화용
    ALLOWED_ORIGINS: str = "http://localhost:8000,https://encar.com"  # CORS 허용 도메인
    
    # 레이트리밋 설정
    RATE_LIMIT_PER_MINUTE: int = 10  # 사용자당 분당 요청 수
    RATE_LIMIT_PER_HOUR: int = 100   # 사용자당 시간당 요청 수
    
    # 데이터베이스 설정 (Phase 2에서 사용)
    DATABASE_URL: Optional[str] = None  # PostgreSQL 연결 문자열
    REDIS_URL: Optional[str] = None     # Redis 캐시 연결 문자열
    
    # 시맨틱 검색 설정
    SEMANTIC_SEARCH_ENABLED: bool = True
    SEMANTIC_MODEL: str = "jhgan/ko-sroberta-multitask"
    
    # 검색 임계값
    SEMANTIC_THRESHOLD_MD: float = 0.25  # MD 파일 최소 신뢰도
    SEMANTIC_THRESHOLD_FAQ: float = 0.15  # FAQ 최소 신뢰도
    SEMANTIC_MINDMAP_THRESHOLD: float = 0.35  # 마인드맵 모드 최소 점수
    SEMANTIC_SCORE_DIFF: float = 0.08  # 유사 섹션 점수 차이
    KEYWORD_SEARCH_THRESHOLD: float = 0.03  # 키워드 검색 임계값
    
    # 세션 설정
    SESSION_TIMEOUT_HOURS: int = 8
    
    # 파일 경로
    DATA_DIR: str = "data"
    FAQ_FILE: str = "data/faq_data.json"
    USERS_FILE: str = "data/users.json"
    FEEDBACK_FILE: str = "data/feedback.json"
    SEMANTIC_INDEX_DIR: str = "data/semantic_index"
    MD_FILES_DIR: str = "docs"
    
    # CORS 설정 (레거시 호환성)
    CORS_ORIGINS: list = ["*"]  # 사용 안 함, ALLOWED_ORIGINS 사용
    
    # 로깅 설정
    LOG_FILE: str = "logs/encar_copilot.log"
    LOG_MAX_BYTES: int = 10 * 1024 * 1024  # 10MB
    LOG_BACKUP_COUNT: int = 5
    
    # 관찰성 설정
    ENABLE_METRICS: bool = True  # Prometheus 메트릭 활성화
    ENABLE_HEALTH_CHECK: bool = True  # 헬스체크 활성화
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
    
    @property
    def allowed_origins_list(self) -> List[str]:
        """ALLOWED_ORIGINS를 리스트로 변환"""
        return [origin.strip() for origin in self.ALLOWED_ORIGINS.split(",")]


# 싱글톤 인스턴스
settings = Settings()

