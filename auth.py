"""
인증 시스템
간단한 사번/이름 기반 인증 (MVP)
"""
import secrets
from typing import Optional, Dict
from datetime import datetime, timedelta
from models import User, LoginRequest, LoginResponse
from database import db


class AuthManager:
    """인증 관리 클래스"""
    
    def __init__(self):
        # 세션 저장소 (메모리 기반, 실제로는 Redis 등 사용 권장)
        self.sessions: Dict[str, Dict] = {}
        self.session_timeout = timedelta(hours=8)  # 8시간 세션 유지
    
    def generate_session_token(self) -> str:
        """세션 토큰 생성"""
        return secrets.token_urlsafe(32)
    
    def login(self, login_request: LoginRequest) -> LoginResponse:
        """
        로그인 처리
        
        Args:
            login_request: 로그인 요청 (사번, 이름)
            
        Returns:
            LoginResponse
        """
        # 사용자 조회
        user = db.get_user_by_employee_id(login_request.employee_id)
        
        if not user:
            return LoginResponse(
                success=False,
                message="등록되지 않은 사용자입니다.",
                user=None,
                session_token=None
            )
        
        # 이름 확인 (간단한 검증)
        if user.name != login_request.name:
            return LoginResponse(
                success=False,
                message="사번과 이름이 일치하지 않습니다.",
                user=None,
                session_token=None
            )
        
        # 세션 토큰 생성
        session_token = self.generate_session_token()
        
        # 세션 저장
        self.sessions[session_token] = {
            "user": user.dict(),
            "login_time": datetime.now(),
            "expire_time": datetime.now() + self.session_timeout
        }
        
        return LoginResponse(
            success=True,
            message="로그인 성공",
            user=user.dict(),
            session_token=session_token
        )
    
    def logout(self, session_token: str) -> bool:
        """
        로그아웃 처리
        
        Args:
            session_token: 세션 토큰
            
        Returns:
            성공 여부
        """
        if session_token in self.sessions:
            del self.sessions[session_token]
            return True
        return False
    
    def validate_session(self, session_token: str) -> Optional[User]:
        """
        세션 검증
        
        Args:
            session_token: 세션 토큰
            
        Returns:
            User 객체 또는 None
        """
        if session_token not in self.sessions:
            return None
        
        session = self.sessions[session_token]
        
        # 세션 만료 확인
        if datetime.now() > session["expire_time"]:
            del self.sessions[session_token]
            return None
        
        # 세션 갱신
        session["expire_time"] = datetime.now() + self.session_timeout
        
        return User(**session["user"])
    
    def get_current_user(self, session_token: Optional[str]) -> Optional[User]:
        """
        현재 로그인한 사용자 조회
        
        Args:
            session_token: 세션 토큰
            
        Returns:
            User 객체 또는 None
        """
        if not session_token:
            return None
        
        return self.validate_session(session_token)
    
    def cleanup_expired_sessions(self):
        """만료된 세션 정리"""
        now = datetime.now()
        expired_tokens = [
            token for token, session in self.sessions.items()
            if now > session["expire_time"]
        ]
        
        for token in expired_tokens:
            del self.sessions[token]
        
        return len(expired_tokens)


# 싱글톤 인스턴스
auth_manager = AuthManager()


