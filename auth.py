"""
인증 시스템
간단한 사번/이름 기반 인증 (MVP)
"""
import secrets
import json
import os
from typing import Optional, Dict
from datetime import datetime, timedelta
from pathlib import Path
from models import User, LoginRequest, LoginResponse
from database import db


class AuthManager:
    """인증 관리 클래스 (세션 영속화 지원)"""
    
    def __init__(self):
        # 세션 파일 경로
        self.session_file = Path("data/sessions.json")
        self.session_timeout = timedelta(hours=8)  # 8시간 세션 유지
        
        # 세션 저장소 (파일에서 로드)
        self.sessions: Dict[str, Dict] = self._load_sessions()
    
    def _load_sessions(self) -> Dict:
        """세션 파일에서 로드"""
        if not self.session_file.exists():
            return {}
        
        try:
            with open(self.session_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
                
                # datetime 문자열을 객체로 복원
                for token, session in data.items():
                    session['login_time'] = datetime.fromisoformat(session['login_time'])
                    session['expire_time'] = datetime.fromisoformat(session['expire_time'])
                
                print(f"✅ {len(data)}개 세션 로드 완료")
                return data
        except Exception as e:
            print(f"⚠️  세션 로드 실패: {e}, 새로 시작합니다")
            return {}
    
    def _save_sessions(self):
        """세션 파일에 저장"""
        try:
            # data 디렉토리 확인
            self.session_file.parent.mkdir(parents=True, exist_ok=True)
            
            # datetime 객체를 문자열로 변환
            data = {}
            for token, session in self.sessions.items():
                data[token] = {
                    'user': session['user'],
                    'login_time': session['login_time'].isoformat(),
                    'expire_time': session['expire_time'].isoformat()
                }
            
            # 파일에 저장
            with open(self.session_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
                
        except Exception as e:
            print(f"⚠️  세션 저장 실패: {e}")
    
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
        
        # 파일에 영속화
        self._save_sessions()
        
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
            # 파일에 영속화
            self._save_sessions()
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
        
        if expired_tokens:
            # 파일에 영속화
            self._save_sessions()
        
        return len(expired_tokens)


# 싱글톤 인스턴스
auth_manager = AuthManager()


