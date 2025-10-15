"""
질문 매칭 엔진
키워드 기반 검색 및 유사도 계산
"""
import re
from typing import List, Tuple, Dict, Optional
from models import FAQItem
from difflib import SequenceMatcher


class SearchEngine:
    """질문 매칭 엔진 클래스"""
    
    def __init__(self):
        pass
    
    def extract_keywords(self, text: str) -> List[str]:
        """
        텍스트에서 키워드 추출
        간단한 토큰화 방식 사용 (MVP)
        """
        # 특수문자 제거 및 공백 기준 분리
        text = re.sub(r'[^\w\s]', ' ', text)
        words = text.split()
        
        # 한 글자 단어 제외
        keywords = [w for w in words if len(w) > 1]
        
        return keywords
    
    def calculate_keyword_score(self, question: str, faq: FAQItem) -> float:
        """
        질문과 FAQ 간의 키워드 매칭 점수 계산
        """
        question_lower = question.lower()
        
        # FAQ의 키워드, 질문, 답변에서 검색
        faq_keywords = set([k.lower() for k in faq.keywords])
        faq_question_lower = faq.question.lower()
        faq_answer_lower = faq.main_answer.lower()
        
        # 부분 문자열 매칭 (단어 검색 개선)
        if question_lower in faq_question_lower or question_lower in faq_answer_lower:
            return 1.0  # 정확히 포함되면 높은 점수
        
        # 키워드에 포함되어 있는지 확인
        for keyword in faq_keywords:
            if question_lower in keyword or keyword in question_lower:
                return 0.8  # 키워드에 포함되면 높은 점수
        
        # 기존 방식 (Jaccard)
        question_keywords = set(self.extract_keywords(question_lower))
        faq_question_keywords = set(self.extract_keywords(faq_question_lower))
        
        all_faq_keywords = faq_keywords.union(faq_question_keywords)
        
        if not question_keywords or not all_faq_keywords:
            return 0.0
        
        # 교집합 개수 / 합집합 개수 (Jaccard 유사도)
        intersection = len(question_keywords.intersection(all_faq_keywords))
        union = len(question_keywords.union(all_faq_keywords))
        
        return intersection / union if union > 0 else 0.0
    
    def calculate_text_similarity(self, text1: str, text2: str) -> float:
        """
        두 텍스트 간의 유사도 계산 (시퀀스 매칭)
        """
        return SequenceMatcher(None, text1.lower(), text2.lower()).ratio()
    
    def calculate_total_score(self, question: str, faq: FAQItem) -> float:
        """
        종합 점수 계산 (키워드 점수 + 텍스트 유사도)
        """
        keyword_score = self.calculate_keyword_score(question, faq)
        text_similarity = self.calculate_text_similarity(question, faq.question)
        
        # 가중치: 키워드 70%, 텍스트 유사도 30%
        total_score = (keyword_score * 0.7) + (text_similarity * 0.3)
        
        return total_score
    
    def search(self, question: str, faqs: List[FAQItem], top_k: int = 5) -> List[Tuple[FAQItem, float]]:
        """
        질문에 대한 최적의 FAQ 검색
        
        Args:
            question: 사용자 질문
            faqs: FAQ 리스트
            top_k: 상위 k개 결과 반환
            
        Returns:
            (FAQ, 점수) 튜플 리스트
        """
        results = []
        
        for faq in faqs:
            score = self.calculate_total_score(question, faq)
            results.append((faq, score))
        
        # 점수 기준 내림차순 정렬
        results.sort(key=lambda x: x[1], reverse=True)
        
        # 상위 k개 반환
        return results[:top_k]
    
    def get_best_match(self, question: str, faqs: List[FAQItem], threshold: float = 0.3) -> Optional[Tuple[FAQItem, float]]:
        """
        가장 적합한 FAQ 반환
        
        Args:
            question: 사용자 질문
            faqs: FAQ 리스트
            threshold: 최소 점수 임계값
            
        Returns:
            (FAQ, 점수) 튜플 또는 None
        """
        results = self.search(question, faqs, top_k=1)
        
        if results and results[0][1] >= threshold:
            return results[0]
        
        return None
    
    def get_related_questions(self, current_faq: FAQItem, all_faqs: List[FAQItem], max_count: int = 5) -> List[Dict]:
        """
        관련 질문 추천
        
        Args:
            current_faq: 현재 FAQ
            all_faqs: 전체 FAQ 리스트
            max_count: 최대 추천 개수
            
        Returns:
            관련 질문 리스트
        """
        related = []
        
        for faq in all_faqs:
            # 자기 자신은 제외
            if faq.id == current_faq.id:
                continue
            
            # 같은 카테고리 우선
            score = 0.0
            if faq.category == current_faq.category:
                score += 0.5
            
            # 키워드 유사도
            current_keywords = set([k.lower() for k in current_faq.keywords])
            faq_keywords = set([k.lower() for k in faq.keywords])
            
            if current_keywords and faq_keywords:
                intersection = len(current_keywords.intersection(faq_keywords))
                union = len(current_keywords.union(faq_keywords))
                score += (intersection / union) * 0.5
            
            if score > 0:
                related.append({
                    "id": faq.id,
                    "question": faq.question,
                    "category": faq.category,
                    "score": score
                })
        
        # 점수 기준 정렬
        related.sort(key=lambda x: x["score"], reverse=True)
        
        # 상위 max_count개 반환 (score 제외)
        return [{"id": r["id"], "question": r["question"], "category": r["category"]} 
                for r in related[:max_count]]


# 싱글톤 인스턴스
search_engine = SearchEngine()

