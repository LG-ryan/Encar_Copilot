"""
데이터베이스 관리 모듈
JSON 파일을 사용한 간단한 데이터베이스 관리 (MVP)
"""
import json
import os
from typing import List, Optional, Dict
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
    
    def _read_json(self, file_path: str) -> dict:
        """JSON 파일 읽기"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except FileNotFoundError:
            return {}
        except json.JSONDecodeError:
            return {}
    
    def _write_json(self, file_path: str, data: dict):
        """JSON 파일 쓰기"""
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
    
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
    
    def get_feedback_stats(self) -> Dict:
        """피드백 통계 조회"""
        feedbacks = self.get_all_feedbacks()
        total = len(feedbacks)
        if total == 0:
            return {
                "total": 0,
                "positive": 0,
                "negative": 0,
                "positive_rate": 0
            }
        
        positive = sum(1 for f in feedbacks if f.is_helpful)
        negative = total - positive
        positive_rate = (positive / total) * 100
        
        return {
            "total": total,
            "positive": positive,
            "negative": negative,
            "positive_rate": round(positive_rate, 2)
        }


# 싱글톤 인스턴스
db = Database()


