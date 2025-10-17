"""
간단한 인메모리 레이트리밋
(Production에서는 Redis 기반 추천)
"""
import time
from collections import defaultdict, deque
from typing import Optional


class RateLimiter:
    """인메모리 레이트리밋"""
    
    def __init__(self):
        # user_id -> [(timestamp, count)]
        self.requests = defaultdict(deque)
        self.cleanup_interval = 60  # 1분마다 정리
        self.last_cleanup = time.time()
    
    def is_allowed(
        self,
        user_id: str,
        max_per_minute: int = 10,
        max_per_hour: int = 100
    ) -> tuple[bool, Optional[str]]:
        """
        요청 허용 여부 확인
        
        Args:
            user_id: 사용자 ID
            max_per_minute: 분당 최대 요청 수
            max_per_hour: 시간당 최대 요청 수
            
        Returns:
            (허용 여부, 거부 메시지)
        """
        now = time.time()
        
        # 주기적 정리
        if now - self.last_cleanup > self.cleanup_interval:
            self._cleanup()
            self.last_cleanup = now
        
        # 사용자 요청 기록
        user_requests = self.requests[user_id]
        
        # 1시간 이전 요청 제거
        while user_requests and now - user_requests[0] > 3600:
            user_requests.popleft()
        
        # 1분간 요청 수 확인
        minute_requests = sum(
            1 for ts in user_requests if now - ts <= 60
        )
        
        if minute_requests >= max_per_minute:
            return False, f"분당 {max_per_minute}회 요청 제한을 초과했습니다. 잠시 후 다시 시도해주세요."
        
        # 1시간간 요청 수 확인
        if len(user_requests) >= max_per_hour:
            return False, f"시간당 {max_per_hour}회 요청 제한을 초과했습니다. 잠시 후 다시 시도해주세요."
        
        # 요청 기록
        user_requests.append(now)
        return True, None
    
    def _cleanup(self):
        """오래된 요청 기록 정리"""
        now = time.time()
        to_remove = []
        
        for user_id, requests in self.requests.items():
            # 1시간 이전 요청 제거
            while requests and now - requests[0] > 3600:
                requests.popleft()
            
            # 빈 큐 제거
            if not requests:
                to_remove.append(user_id)
        
        for user_id in to_remove:
            del self.requests[user_id]


# 글로벌 레이트리밋 인스턴스
_rate_limiter: Optional[RateLimiter] = None


def get_rate_limiter() -> RateLimiter:
    """글로벌 레이트리밋 인스턴스 반환"""
    global _rate_limiter
    if _rate_limiter is None:
        _rate_limiter = RateLimiter()
    return _rate_limiter

