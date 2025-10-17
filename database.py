"""
데이터베이스 관리 모듈
JSON 파일을 사용한 간단한 데이터베이스 관리 (MVP)
파일 잠금을 통한 동시 쓰기 방지 기능 포함
"""
import json
import os
import time
from typing import List, Optional, Dict
from pathlib import Path
from models import FAQItem, User, Feedback


class Database:
    """데이터베이스 관리 클래스"""
    
    def __init__(self):
        self.data_dir = "data"
        self.faq_file = os.path.join(self.data_dir, "faq_data.json")
        self.users_file = os.path.join(self.data_dir, "users.json")
        self.feedback_file = os.path.join(self.data_dir, "feedback.json")
        
        # 데이터 디렉토리가 없으면 생성
        if not os.path.exists(self.data_dir):
            os.makedirs(self.data_dir)
    
    def _get_lock_file(self, file_path: str) -> str:
        """잠금 파일 경로 생성"""
        return f"{file_path}.lock"
    
    def _acquire_lock(self, file_path: str, timeout: float = 5.0) -> bool:
        """
        파일 잠금 획득 (단순 파일 기반 잠금)
        
        Args:
            file_path: 잠글 파일 경로
            timeout: 최대 대기 시간 (초)
        
        Returns:
            잠금 획득 성공 여부
        """
        lock_file = self._get_lock_file(file_path)
        start_time = time.time()
        
        while True:
            try:
                # 잠금 파일이 없으면 생성 (원자적 연산)
                fd = os.open(lock_file, os.O_CREAT | os.O_EXCL | os.O_WRONLY)
                os.write(fd, str(os.getpid()).encode())
                os.close(fd)
                return True
            except FileExistsError:
                # 잠금 파일이 이미 존재하면 대기
                if time.time() - start_time > timeout:
                    print(f"⚠️  파일 잠금 타임아웃: {file_path}")
                    return False
                time.sleep(0.01)  # 10ms 대기
    
    def _release_lock(self, file_path: str):
        """파일 잠금 해제"""
        lock_file = self._get_lock_file(file_path)
        try:
            os.remove(lock_file)
        except FileNotFoundError:
            pass  # 이미 삭제됨
    
    def _read_json(self, file_path: str) -> dict:
        """JSON 파일 읽기 (잠금 사용)"""
        if not self._acquire_lock(file_path):
            return {}
        
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except FileNotFoundError:
            return {}
        except json.JSONDecodeError:
            return {}
        finally:
            self._release_lock(file_path)
    
    def _write_json(self, file_path: str, data: dict):
        """JSON 파일 쓰기 (잠금 사용)"""
        if not self._acquire_lock(file_path):
            raise IOError(f"파일 잠금 획득 실패: {file_path}")
        
        try:
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
        finally:
            self._release_lock(file_path)
    
    # FAQ 관련 메서드
    def get_all_faqs(self) -> List[FAQItem]:
        """모든 FAQ 항목 조회"""
        data = self._read_json(self.faq_file)
        faqs = data.get("faqs", [])
        return [FAQItem(**faq) for faq in faqs]
    
    def get_faq_by_id(self, faq_id: int) -> Optional[FAQItem]:
        """ID로 FAQ 항목 조회"""
        faqs = self.get_all_faqs()
        for faq in faqs:
            if faq.id == faq_id:
                return faq
        return None
    
    def get_faqs_by_category(self, category: str) -> List[FAQItem]:
        """카테고리별 FAQ 조회"""
        faqs = self.get_all_faqs()
        return [faq for faq in faqs if faq.category == category]
    
    def get_all_categories(self) -> List[str]:
        """모든 카테고리 목록 조회"""
        faqs = self.get_all_faqs()
        categories = set(faq.category for faq in faqs)
        return sorted(list(categories))
    
    def add_faq(self, faq: FAQItem) -> bool:
        """새로운 FAQ 추가"""
        try:
            data = self._read_json(self.faq_file)
            faqs = data.get("faqs", [])
            faqs.append(faq.dict())
            data["faqs"] = faqs
            self._write_json(self.faq_file, data)
            return True
        except Exception as e:
            print(f"FAQ 추가 중 오류 발생: {e}")
            return False
    
    def update_faq(self, faq_id: int, updated_faq: FAQItem) -> bool:
        """FAQ 업데이트"""
        try:
            data = self._read_json(self.faq_file)
            faqs = data.get("faqs", [])
            for i, faq in enumerate(faqs):
                if faq["id"] == faq_id:
                    faqs[i] = updated_faq.dict()
                    data["faqs"] = faqs
                    self._write_json(self.faq_file, data)
                    return True
            return False
        except Exception as e:
            print(f"FAQ 업데이트 중 오류 발생: {e}")
            return False
    
    # 사용자 관련 메서드
    def get_all_users(self) -> List[User]:
        """모든 사용자 조회"""
        data = self._read_json(self.users_file)
        users = data.get("users", [])
        return [User(**user) for user in users]
    
    def get_user_by_employee_id(self, employee_id: str) -> Optional[User]:
        """사번으로 사용자 조회"""
        users = self.get_all_users()
        for user in users:
            if user.employee_id == employee_id:
                return user
        return None
    
    def add_user(self, user: User) -> bool:
        """새로운 사용자 추가"""
        try:
            data = self._read_json(self.users_file)
            users = data.get("users", [])
            users.append(user.dict())
            data["users"] = users
            self._write_json(self.users_file, data)
            return True
        except Exception as e:
            print(f"사용자 추가 중 오류 발생: {e}")
            return False
    
    # 피드백 관련 메서드
    def get_all_feedbacks(self) -> List[Feedback]:
        """모든 피드백 조회"""
        data = self._read_json(self.feedback_file)
        feedbacks = data.get("feedbacks", [])
        return [Feedback(**feedback) for feedback in feedbacks]
    
    def add_feedback(self, feedback: Feedback) -> bool:
        """피드백 추가"""
        try:
            data = self._read_json(self.feedback_file)
            feedbacks = data.get("feedbacks", [])
            feedbacks.append(feedback.dict())
            data["feedbacks"] = feedbacks
            self._write_json(self.feedback_file, data)
            return True
        except Exception as e:
            print(f"피드백 추가 중 오류 발생: {e}")
            return False
    
    def add_detailed_feedback(self, feedback) -> bool:
        """상세 피드백 추가 (싫어요 + 이유 + 의견)"""
        try:
            data = self._read_json(self.feedback_file)
            
            # 상세 피드백 저장
            detailed_feedbacks = data.get("detailed_feedbacks", [])
            feedback_dict = feedback.dict()
            feedback_dict["id"] = f"fb_{feedback.question_id}"
            detailed_feedbacks.append(feedback_dict)
            data["detailed_feedbacks"] = detailed_feedbacks
            
            self._write_json(self.feedback_file, data)
            print(f"✅ 상세 피드백 저장: 질문='{feedback.user_question}', 이유={feedback.reasons}")
            return True
        except Exception as e:
            print(f"❌ 상세 피드백 추가 중 오류 발생: {e}")
            return False
    
    def get_feedback_stats(self) -> Dict:
        """피드백 통계 조회 (개선된 버전)"""
        try:
            data = self._read_json(self.feedback_file)
            feedbacks = data.get("feedbacks", [])
            detailed_feedbacks = data.get("detailed_feedbacks", [])
            
            total = len(feedbacks)
            positive = sum(1 for f in feedbacks if f.get("is_helpful", False))
            negative = total - positive
            
            # 상세 피드백 통계
            negative_reasons = {}
            sections_needing_improvement = {}
            
            for df in detailed_feedbacks:
                # 이유별 집계
                for reason in df.get("reasons", []):
                    negative_reasons[reason] = negative_reasons.get(reason, 0) + 1
                
                # 섹션별 집계
                section = df.get("matched_section", "알 수 없음")
                sections_needing_improvement[section] = sections_needing_improvement.get(section, 0) + 1
            
            # 개선 필요 섹션 정렬 (많은 순)
            sorted_sections = sorted(
                [{"section": k, "count": v} for k, v in sections_needing_improvement.items()],
                key=lambda x: x["count"],
                reverse=True
            )
            
            return {
                "total": total,
                "positive": positive,
                "negative": negative,
                "positive_rate": round(positive / total * 100, 1) if total > 0 else 0,
                "detailed_feedbacks_count": len(detailed_feedbacks),
                "negative_reasons": negative_reasons,
                "sections_needing_improvement": sorted_sections[:10]  # 상위 10개
            }
        except Exception as e:
            print(f"❌ 통계 조회 중 오류 발생: {e}")
            return {
                "total": 0,
                "positive": 0,
                "negative": 0,
                "positive_rate": 0,
                "detailed_feedbacks_count": 0,
                "negative_reasons": {},
                "sections_needing_improvement": []
            }
    
    def get_detailed_feedbacks(self, limit: int = 100) -> List[Dict]:
        """상세 피드백 조회"""
        try:
            data = self._read_json(self.feedback_file)
            detailed_feedbacks = data.get("detailed_feedbacks", [])
            return detailed_feedbacks[:limit]
        except Exception as e:
            print(f"❌ 상세 피드백 조회 중 오류 발생: {e}")
            return []
    
    def get_negative_feedbacks(self) -> List[Dict]:
        """부정 피드백만 조회"""
        try:
            data = self._read_json(self.feedback_file)
            detailed_feedbacks = data.get("detailed_feedbacks", [])
            return [f for f in detailed_feedbacks if not f.get("is_helpful", True)]
        except Exception as e:
            print(f"❌ 부정 피드백 조회 중 오류 발생: {e}")
            return []


# 싱글톤 인스턴스
db = Database()


