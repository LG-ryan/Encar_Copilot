"""
인증/인가 유틸리티
RBAC (Role-Based Access Control) 구현
"""
from fastapi import Header, HTTPException
from functools import wraps
from typing import Optional, List, Callable
from auth import auth_manager


class UserRole:
    """사용자 역할 상수"""
    ADMIN = "admin"  # 관리자: 모든 권한
    USER = "user"    # 일반 사용자: 기본 권한


def get_user_role(user: Optional[dict]) -> str:
    """사용자 역할 조회"""
    if not user:
        return None
    
    # user 딕셔너리에서 role 추출
    # 기본값은 'user'
    return user.get("role", UserRole.USER)


def require_auth(allow_anonymous: bool = False):
    """
    인증 필수 데코레이터
    
    Args:
        allow_anonymous: 익명 사용자 허용 여부
    """
    def decorator(func: Callable):
        @wraps(func)
        async def wrapper(*args, authorization: Optional[str] = Header(None), **kwargs):
            if not authorization and not allow_anonymous:
                raise HTTPException(
                    status_code=401,
                    detail="인증이 필요합니다"
                )
            
            # 토큰 파싱
            if authorization:
                token = authorization.replace("Bearer ", "") if authorization.startswith("Bearer ") else authorization
                user = auth_manager.get_current_user(token)
                
                if not user and not allow_anonymous:
                    raise HTTPException(
                        status_code=401,
                        detail="유효하지 않은 토큰입니다"
                    )
                
                kwargs["current_user"] = user
            else:
                kwargs["current_user"] = None
            
            return await func(*args, authorization=authorization, **kwargs)
        
        return wrapper
    return decorator


def require_role(allowed_roles: List[str]):
    """
    역할 기반 접근 제어 데코레이터
    
    Args:
        allowed_roles: 허용된 역할 리스트 (예: [UserRole.ADMIN])
    
    사용 예:
        @app.get("/api/admin/users")
        @require_role([UserRole.ADMIN])
        async def get_users(current_user: dict, ...):
            pass
    """
    def decorator(func: Callable):
        @wraps(func)
        async def wrapper(*args, authorization: Optional[str] = Header(None), **kwargs):
            if not authorization:
                raise HTTPException(
                    status_code=401,
                    detail="인증이 필요합니다"
                )
            
            # 토큰 파싱
            token = authorization.replace("Bearer ", "") if authorization.startswith("Bearer ") else authorization
            user = auth_manager.get_current_user(token)
            
            if not user:
                raise HTTPException(
                    status_code=401,
                    detail="유효하지 않은 토큰입니다"
                )
            
            # 역할 확인
            user_role = get_user_role(user)
            if user_role not in allowed_roles:
                raise HTTPException(
                    status_code=403,
                    detail=f"권한이 없습니다. 필요한 역할: {', '.join(allowed_roles)}"
                )
            
            kwargs["current_user"] = user
            return await func(*args, authorization=authorization, **kwargs)
        
        return wrapper
    return decorator


def check_permission(user: Optional[dict], required_role: str) -> bool:
    """
    권한 체크 헬퍼 함수
    
    Args:
        user: 사용자 정보
        required_role: 필요한 역할
        
    Returns:
        권한 여부
    """
    if not user:
        return False
    
    user_role = get_user_role(user)
    
    # Admin은 모든 권한 보유
    if user_role == UserRole.ADMIN:
        return True
    
    return user_role == required_role

