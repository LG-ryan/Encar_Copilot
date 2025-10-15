"""
답변 처리 서비스
시맨틱 검색 및 키워드 검색을 통합하여 최적의 답변 제공
"""
import time
from typing import Optional, List, Tuple, Dict
from models import AnswerResponse, FAQItem
from config.settings import settings


class AnswerService:
    """답변 처리 비즈니스 로직"""
    
    def __init__(self, semantic_engine=None, keyword_engine=None, db=None):
        """
        Args:
            semantic_engine: SemanticSearchEngine 인스턴스
            keyword_engine: SearchEngine 인스턴스 (키워드 검색)
            db: Database 인스턴스
        """
        self.semantic = semantic_engine
        self.keyword = keyword_engine
        self.db = db
        
        # 카테고리 매핑 (H2 → 카테고리)
        self.md_category_map = {
            '업무 환경 세팅': 'IT',
            '업무 Tool 소개': 'IT',
            '복리후생': '복리후생',
            '근태 및 휴가': 'HR',
            '급여 및 경비': 'HR',
            '사무실 이용': '총무',
            '인사 서비스': 'HR',
            '엔카 소개': '총무',
            '꿀팁 모음': '총무',
        }
    
    def process_question(self, question: str) -> AnswerResponse:
        """
        질문 처리 메인 로직
        
        Args:
            question: 사용자 질문
            
        Returns:
            AnswerResponse
        """
        start_time = time.time()
        
        # 시맨틱 검색 시도
        if self.semantic:
            try:
                result = self._semantic_search(question, start_time)
                if result:
                    return result
            except Exception as e:
                print(f"⚠️  시맨틱 검색 오류: {e}, 키워드 검색으로 전환")
        
        # 폴백: 키워드 검색
        if self.keyword and self.db:
            return self._keyword_search(question, start_time)
        
        # 검색 실패
        return self._no_result_response(question, start_time)
    
    def _semantic_search(self, question: str, start_time: float) -> Optional[AnswerResponse]:
        """
        시맨틱 검색 수행
        
        Args:
            question: 사용자 질문
            start_time: 시작 시간
            
        Returns:
            AnswerResponse 또는 None
        """
        # 정규화 버전도 검색 (띄어쓰기 제거)
        normalized_question = question.replace(" ", "")
        
        # 원본 + 정규화 검색 결과 병합
        results = self.semantic.search(question, top_k=10)
        if normalized_question != question:
            results_normalized = self.semantic.search(normalized_question, top_k=5)
            results = self._merge_search_results(results, results_normalized)
        
        if not results:
            return None
        
        # FAQ vs MD 분리
        faq_results = [(doc, score) for doc, score in results if doc.get('source') == 'FAQ']
        md_results = [(doc, score) for doc, score in results if doc.get('source') != 'FAQ']
        
        # MD 우선 전략
        best_match, score, is_md = self._select_best_match(faq_results, md_results)
        
        if not best_match:
            return None
        
        # 신뢰도 검증
        min_threshold = settings.SEMANTIC_THRESHOLD_MD if is_md else settings.SEMANTIC_THRESHOLD_FAQ
        if score < min_threshold:
            return None
        
        # 답변 구성
        if is_md:
            return self._build_md_answer(question, best_match, score, results, start_time)
        else:
            return self._build_faq_answer(best_match, score, results, start_time)
    
    def _merge_search_results(
        self, 
        results1: List[Tuple[Dict, float]], 
        results2: List[Tuple[Dict, float]]
    ) -> List[Tuple[Dict, float]]:
        """검색 결과 병합 (중복 제거)"""
        seen_titles = set()
        combined = []
        
        for doc, score in results1 + results2:
            if doc['title'] not in seen_titles:
                seen_titles.add(doc['title'])
                combined.append((doc, score))
        
        return sorted(combined, key=lambda x: x[1], reverse=True)[:10]
    
    def _select_best_match(
        self, 
        faq_results: List[Tuple[Dict, float]], 
        md_results: List[Tuple[Dict, float]]
    ) -> Tuple[Optional[Dict], float, bool]:
        """
        FAQ vs MD 중 최적 결과 선택
        
        Returns:
            (best_match, score, is_md)
        """
        best_md = md_results[0] if md_results else None
        best_faq = faq_results[0] if faq_results else None
        
        # MD 우선 (점수가 충분히 높을 때)
        if best_md:
            md_doc, md_score = best_md
            if md_score >= settings.SEMANTIC_THRESHOLD_MD:
                return md_doc, md_score, True
            elif best_faq:
                # MD 점수가 낮으면 FAQ로 폴백
                faq_doc, faq_score = best_faq
                return faq_doc, faq_score, False
            else:
                return md_doc, md_score, True
        elif best_faq:
            faq_doc, faq_score = best_faq
            return faq_doc, faq_score, False
        
        return None, 0.0, False
    
    def _build_md_answer(
        self, 
        question: str, 
        best_match: Dict, 
        score: float, 
        results: List[Tuple[Dict, float]], 
        start_time: float
    ) -> AnswerResponse:
        """MD 파일 기반 답변 구성"""
        # 고득점 섹션 필터링
        high_score_sections = [
            (doc, s) for doc, s in results[:5] 
            if s >= settings.SEMANTIC_THRESHOLD_MD
        ]
        
        # 마인드맵 모드 또는 직접 답변
        if len(high_score_sections) >= 2:
            answer, related_questions = self._check_mindmap_mode(
                question, high_score_sections
            )
        else:
            answer, related_questions = self._build_single_answer(
                high_score_sections, results
            )
        
        # 카테고리 결정
        category = self._get_category(best_match)
        
        return AnswerResponse(
            answer=answer,
            department='엔디(Endy)',
            link=None,
            category=category,
            confidence_score=round(score, 2),
            related_questions=related_questions,
            response_time=round(time.time() - start_time, 3)
        )
    
    def _check_mindmap_mode(
        self, 
        question: str, 
        high_score_sections: List[Tuple[Dict, float]]
    ) -> Tuple[str, List[Dict]]:
        """
        마인드맵 모드 체크 (유사 섹션이 여러 개인 경우)
        
        Returns:
            (answer, related_questions)
        """
        best_score = high_score_sections[0][1]
        
        # 점수가 비슷한 섹션들 찾기
        similar_sections = [
            (doc, s) for doc, s in high_score_sections 
            if best_score - s <= settings.SEMANTIC_SCORE_DIFF
        ]
        
        # 마인드맵 모드 조건: 2개 이상 + 충분히 높은 점수
        if len(similar_sections) >= 2 and best_score >= settings.SEMANTIC_MINDMAP_THRESHOLD:
            # 여러 옵션 제공
            answer = f"**'{question}'** 관련하여 여러 섹션이 있습니다:\n\n"
            
            for i, (doc, _) in enumerate(similar_sections[:4], 1):
                preview = doc['content'][:100].replace('\n', ' ') + "..."
                answer += f"**{i}. {doc['title']}**\n{preview}\n\n"
            
            answer += "💡 더 구체적으로 질문하시거나, 위 섹션 중 하나를 선택해주세요!"
            
            related_questions = [
                {"question": doc['title']} 
                for doc, _ in similar_sections[:4]
                if not doc['title'].startswith('[Page')
            ]
            
            return answer, related_questions
        
        # 명확한 답변이 있으면 직접 제공
        return self._build_single_answer(high_score_sections[:1], [])
    
    def _build_single_answer(
        self, 
        high_score_sections: List[Tuple[Dict, float]], 
        all_results: List[Tuple[Dict, float]]
    ) -> Tuple[str, List[Dict]]:
        """단일 답변 구성"""
        answer_parts = []
        current_title = None
        
        for doc, s in high_score_sections[:1]:  # 상위 1개만
            current_title = doc['title']  # 현재 선택된 제목 저장
            content = doc['content']
            
            # "질문/답변" 형식 제거 - 답변만 추출
            if '**답변:**' in content:
                answer_part = content.split('**답변:**')[1]
                if '###' in answer_part:
                    answer_part = answer_part.split('###')[0]
                content = answer_part.strip()
            
            answer_parts.append(f"**{doc['title']}**\n\n{content}")
        
        answer = "\n\n---\n\n".join(answer_parts) if answer_parts else "관련 정보를 찾지 못했습니다."
        
        # 관련 질문 (현재 선택된 섹션 제외)
        related_questions = [
            {"question": doc['title']} 
            for doc, _ in all_results[1:6]  # 2~6번째 결과 (1번째는 현재 답변)
            if doc.get('title') 
            and not doc['title'].startswith('[Page')
            and doc['title'] != current_title  # 현재 제목 제외!
        ][:3]  # 최대 3개
        
        return answer, related_questions
    
    def _build_faq_answer(
        self, 
        best_match: Dict, 
        score: float, 
        results: List[Tuple[Dict, float]], 
        start_time: float
    ) -> AnswerResponse:
        """FAQ 기반 답변 구성"""
        # 답변 추출
        content = best_match['content']
        answer = content.split('\n\n답변: ')[1] if '\n\n답변: ' in content else content
        
        # 관련 질문
        related_questions = [
            {"question": doc['title']} 
            for doc, _ in results[1:4]
            if doc.get('source') == 'FAQ'
        ]
        
        return AnswerResponse(
            answer=answer,
            department='엔디(Endy)',
            link=best_match.get('link'),
            category=best_match.get('category', '일반'),
            confidence_score=round(score, 2),
            related_questions=related_questions,
            response_time=round(time.time() - start_time, 3)
        )
    
    def _get_category(self, doc: Dict) -> str:
        """문서의 카테고리 결정"""
        doc_category = doc.get('category', '')
        return self.md_category_map.get(doc_category, '총무')
    
    def _keyword_search(self, question: str, start_time: float) -> AnswerResponse:
        """키워드 기반 검색 (폴백)"""
        faqs = self.db.get_all_faqs()
        match = self.keyword.get_best_match(
            question, faqs, 
            threshold=settings.KEYWORD_SEARCH_THRESHOLD
        )
        
        if match:
            faq, score = match
            related = self.keyword.get_related_questions(faq, faqs, max_count=3)
            related_questions = [{"question": r['question']} for r in related]
            
            return AnswerResponse(
                answer=faq.main_answer,
                department='엔디(Endy)',
                link=faq.link,
                category=faq.category,
                confidence_score=round(score, 2),
                related_questions=related_questions,
                response_time=round(time.time() - start_time, 3)
            )
        
        return self._no_result_response(question, start_time)
    
    def _no_result_response(self, question: str, start_time: float) -> AnswerResponse:
        """검색 결과 없음 응답"""
        return AnswerResponse(
            answer="죄송합니다. 관련된 답변을 찾지 못했습니다. 다른 표현으로 질문해주시거나, 담당 부서에 직접 문의해주세요.",
            department='엔디(Endy)',
            link=None,
            category='일반',
            confidence_score=0.0,
            related_questions=[],
            response_time=round(time.time() - start_time, 3)
        )

