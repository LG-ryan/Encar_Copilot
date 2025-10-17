"""
데이터 모델 정의
Encar Copilot의 모든 데이터 구조를 정의합니다.
"""
from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime


class FAQItem(BaseModel):
    """FAQ 항목 모델"""
    id: int
    category: str = Field(..., description="카테고리 (HR, IT, 총무, 경영지원 등)")
    question: str = Field(..., description="질문")
    main_answer: str = Field(..., description="주요 답변")
    keywords: List[str] = Field(..., description="검색용 키워드 리스트")
    department: str = Field(..., description="담당 부서")
    link: Optional[str] = Field(None, description="관련 문서 링크")
    created_at: Optional[str] = Field(default_factory=lambda: datetime.now().isoformat())
    updated_at: Optional[str] = Field(default_factory=lambda: datetime.now().isoformat())


class QuestionRequest(BaseModel):
    """질문 요청 모델"""
    question: str = Field(..., description="사용자 질문")
    user_id: Optional[str] = Field(None, description="사용자 ID (익명화)")


class AnswerResponse(BaseModel):
    """답변 응답 모델"""
    answer: str = Field(..., description="답변 내용")
    department: str = Field(..., description="담당 부서")
    link: Optional[str] = Field(None, description="관련 문서 링크")
    category: str = Field(..., description="카테고리")
    confidence_score: float = Field(..., description="신뢰도 점수 (0-1)")
    related_questions: List[str] = Field(default_factory=list, description="관련 질문 목록")
    response_time: float = Field(..., description="응답 시간 (초)")


class Feedback(BaseModel):
    """피드백 모델 (간단한 좋아요/싫어요)"""
    question_id: int = Field(..., description="질문 ID")
    user_question: str = Field(..., description="사용자 질문")
    is_helpful: bool = Field(..., description="도움이 되었는지 여부")
    user_id: Optional[str] = Field(None, description="사용자 ID (익명화)")
    timestamp: str = Field(default_factory=lambda: datetime.now().isoformat())
    comment: Optional[str] = Field(None, description="추가 의견")


class DetailedFeedback(BaseModel):
    """상세 피드백 모델 (싫어요 + 이유 + 의견)"""
    question_id: int = Field(..., description="질문 ID")
    user_question: str = Field(..., description="사용자 질문")
    is_helpful: bool = Field(default=False, description="도움이 되었는지 여부 (항상 False)")
    reasons: List[str] = Field(default_factory=list, description="싫어요 이유 목록")
    comment: Optional[str] = Field(None, description="주관식 의견")
    user_id: Optional[str] = Field(None, description="사용자 ID")
    user_name: Optional[str] = Field(None, description="사용자 이름")
    matched_section: Optional[str] = Field(None, description="매칭된 섹션 제목")
    timestamp: str = Field(default_factory=lambda: datetime.now().isoformat())


class User(BaseModel):
    """사용자 모델 (MVP용 간단한 버전)"""
    employee_id: str = Field(..., description="사번")
    name: str = Field(..., description="이름")
    department: str = Field(..., description="소속 부서")
    email: Optional[str] = Field(None, description="이메일")
    created_at: str = Field(default_factory=lambda: datetime.now().isoformat())


class LoginRequest(BaseModel):
    """로그인 요청 모델"""
    employee_id: str = Field(..., description="사번")
    name: str = Field(..., description="이름")


class LoginResponse(BaseModel):
    """로그인 응답 모델"""
    success: bool
    message: str
    user: Optional[dict] = None
    session_token: Optional[str] = None


