"""
애플리케이션 설정 관리
환경 변수 및 기본 설정 중앙화
"""
from pydantic_settings import BaseSettings
from typing import Optional


class Settings(BaseSettings):
    """애플리케이션 설정"""
    
    # 서버 설정
    HOST: str = "0.0.0.0"
    PORT: int = 8000
    RELOAD: bool = True
    LOG_LEVEL: str = "info"
    
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
    
    # CORS 설정
    CORS_ORIGINS: list = ["*"]  # 실제 배포 시 특정 도메인으로 제한
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"


# 싱글톤 인스턴스
settings = Settings()

