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
            '엔카 소개': '기업 소개',
            '복리후생': '복리후생',
            '근태 및 휴가': 'HR',
            '인사 서비스': 'HR',
            '급여 및 경비': 'HR',
            '사무실 이용': '총무',
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
        2-pass 계층적 시맨틱 검색
        Pass 1: 넓게 찾기 (카테고리 파악)
        Pass 2: 깊게 파기 (세부 질문 매칭)
        
        Args:
            question: 사용자 질문
            start_time: 시작 시간
            
        Returns:
            AnswerResponse 또는 None
        """
        # Pass 1: 넓게 검색 (top_k=20)
        results = self.semantic.search(question, top_k=20)
        
        if not results:
            return None
        
        # FAQ vs MD 분리
        faq_results = [(doc, score) for doc, score in results if doc.get('source') == 'FAQ']
        md_results = [(doc, score) for doc, score in results if doc.get('source') != 'FAQ']
        
        # MD 결과가 있으면 계층 분석
        if md_results:
            return self._hierarchical_md_search(question, md_results, faq_results, start_time)
        elif faq_results:
            # FAQ만 있으면 기존 방식
            return self._build_faq_answer(faq_results[0][0], faq_results[0][1], results, start_time)
        
            return None
        
    def _hierarchical_md_search(
        self, 
        question: str, 
        md_results: List[Tuple[Dict, float]], 
        faq_results: List[Tuple[Dict, float]], 
        start_time: float
    ) -> Optional[AnswerResponse]:
        """
        계층적 MD 검색 (2-pass)
        1. H2 카테고리별 점수 집계
        2. 최적 카테고리 내에서 세부 질문 매칭
        """
        # Pass 1: H2 카테고리별 점수 집계
        category_scores = {}
        for doc, score in md_results:
            h2 = doc.get('h2', doc.get('category', '기타'))
            if h2 not in category_scores:
                category_scores[h2] = {'total_score': 0, 'count': 0, 'docs': []}
            category_scores[h2]['total_score'] += score
            category_scores[h2]['count'] += 1
            category_scores[h2]['docs'].append((doc, score))
        
        # 카테고리 평균 점수 계산
        for cat in category_scores:
            category_scores[cat]['avg_score'] = (
                category_scores[cat]['total_score'] / category_scores[cat]['count']
            )
        
        # 최고 점수 카테고리
        best_category = max(category_scores.items(), key=lambda x: x[1]['avg_score'])
        category_name, category_data = best_category
        best_category_score = category_data['avg_score']
        
        # Pass 2: 최적 카테고리 내 세부 질문 매칭
        category_docs = sorted(category_data['docs'], key=lambda x: x[1], reverse=True)
        best_doc, best_score = category_docs[0]
        
        # 명확도 판단
        is_clear = self._is_clear_match(best_score, category_docs)
        
        if is_clear:
            # 명확한 질문 → 바로 답변
            return self._build_direct_answer(question, best_doc, best_score, category_docs, start_time)
        else:
            # 애매한 질문 → drill-down (마인드맵)
            return self._build_drilldown_answer(question, category_name, category_docs, start_time)
    
    def _is_clear_match(self, best_score: float, docs: List[Tuple[Dict, float]]) -> bool:
        """
        명확한 매칭인지 판단
        - 최고 점수가 0.5 이상
        - 또는 2등과의 점수 차이가 0.15 이상
        """
        if best_score >= 0.5:
            return True
        
        if len(docs) >= 2:
            second_score = docs[1][1]
            if best_score - second_score >= 0.15:
                return True
        
        return False
    
    def _build_direct_answer(
        self,
        question: str,
        best_doc: Dict,
        score: float,
        category_docs: List[Tuple[Dict, float]],
        start_time: float
    ) -> AnswerResponse:
        """명확한 질문에 대한 직접 답변"""
        # 답변 추출
        if 'answer' in best_doc:
            answer_text = best_doc['answer']
            section_info = f"**[{best_doc.get('h3', '')}]**\n\n" if best_doc.get('h3') else ""
            answer = f"{section_info}{answer_text}"
        else:
            # 기존 방식 (하위 호환)
            content = best_doc['content']
            if '**답변:**' in content:
                answer = content.split('**답변:**')[1].strip()
            else:
                answer = content
        
        # 관련 질문 (중복 제거)
        seen_titles = {best_doc['title']}
        related_questions = []
        
        for doc, _ in category_docs[1:10]:
            title = doc.get('title', '')
            if title and title not in seen_titles and not title.startswith('[Page'):
                seen_titles.add(title)
                related_questions.append({"question": title})
                if len(related_questions) >= 3:
                    break
        
        category = self._get_category(best_doc)
        
        return AnswerResponse(
            answer=answer,
            department='엔디(Endy)',
            link=None,
            category=category,
            confidence_score=round(score, 2),
            related_questions=related_questions,
            response_time=round(time.time() - start_time, 3)
        )
    
    def _build_drilldown_answer(
        self,
        question: str,
        category_name: str,
        category_docs: List[Tuple[Dict, float]],
        start_time: float
    ) -> AnswerResponse:
        """애매한 질문에 대한 drill-down 답변 (마인드맵)"""
        # H3 섹션별로 그룹화
        section_groups = {}
        for doc, score in category_docs[:10]:
            h3 = doc.get('h3', doc.get('section', '기타'))
            if h3 not in section_groups:
                section_groups[h3] = []
            section_groups[h3].append((doc, score))
        
        # 답변 구성
        answer = f"**'{question}'**과 관련된 질문들을 찾았습니다:\n\n"
        answer += f"📂 **[{category_name}]** 카테고리\n\n"
        
        shown_titles = set()
        related_questions = []
        
        # 섹션별로 질문 제시
        for i, (section, docs) in enumerate(list(section_groups.items())[:4], 1):
            answer += f"**{i}. {section}**\n"
            
            for doc, score in docs[:3]:  # 섹션당 최대 3개
                title = doc.get('title', '')
                if title and title not in shown_titles and not title.startswith('[Page'):
                    answer += f"   • {title}\n"
                    shown_titles.add(title)
                    related_questions.append({"question": title})
            answer += "\n"
        
        answer += "💡 구체적인 질문을 선택하시면 상세 답변을 확인하실 수 있습니다!"
        
        category = self._get_category(category_docs[0][0])
        
        return AnswerResponse(
            answer=answer,
            department='엔디(Endy)',
            link=None,
            category=category,
            confidence_score=round(category_docs[0][1], 2),
            related_questions=related_questions[:6],  # 최대 6개
            response_time=round(time.time() - start_time, 3)
        )
    
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
        # MD 파일의 경우 h2 (대분류) 확인
        h2 = doc.get('h2', '')
        if h2 and h2 in self.md_category_map:
            return self.md_category_map[h2]
        
        # FAQ의 경우 category 필드 확인
        doc_category = doc.get('category', '')
        if doc_category:
            return doc_category
        
        # 기본값
        return '일반'
    
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
        """검색 결과 없음 응답 (특정 키워드 감지 포함)"""
        # 특정 키워드별 맞춤 응답
        question_lower = question.lower()
        
        # 진단/진단센터 관련
        if '진단' in question or '진단센터' in question or '광고지원센터' in question:
            return AnswerResponse(
                answer="💡 **진단센터 관련 문의**\n\n"
                      "진단센터/광고지원센터 관련 정보는 현재 준비 중입니다.\n\n"
                      "📱 **모바일 진단 App**: 엔카 광고지원센터에서 차량 진단 업무 처리\n"
                      "📍 **전국 60여개 광고지원센터** 운영 중\n"
                      "🔗 다운로드: https://mobile.encar.io/\n\n"
                      "자세한 사항은 **IT팀** 또는 **현장 운영팀**에 문의해주세요.",
                department='엔디(Endy)',
                link='https://mobile.encar.io/',
                category='IT',
                confidence_score=0.3,
                related_questions=[
                    {"question": "모바일 앱은 어떻게 다운받나요?"},
                    {"question": "지점 분포는 어떻게 되나요?"}
                ],
                response_time=round(time.time() - start_time, 3)
            )
        
        # 기타 검색 실패
        return AnswerResponse(
            answer="죄송합니다. 관련된 답변을 찾지 못했습니다. 다른 표현으로 질문해주시거나, 담당 부서에 직접 문의해주세요.",
            department='엔디(Endy)',
            link=None,
            category='일반',
            confidence_score=0.0,
            related_questions=[],
            response_time=round(time.time() - start_time, 3)
        )

