"""
답변 처리 서비스
LLM, 시맨틱 검색 및 키워드 검색을 통합하여 최적의 답변 제공
"""
import time
import os
from typing import Optional, List, Tuple, Dict
from models import AnswerResponse, FAQItem
from config.settings import settings


class AnswerService:
    """답변 처리 비즈니스 로직"""
    
    def __init__(self, semantic_engine=None, keyword_engine=None, db=None, llm_service=None):
        """
        Args:
            semantic_engine: SemanticSearchEngine 인스턴스
            keyword_engine: SearchEngine 인스턴스 (키워드 검색)
            db: Database 인스턴스
            llm_service: LLMSearchService 인스턴스 (OpenAI 기반)
        """
        self.semantic = semantic_engine
        self.keyword = keyword_engine
        self.db = db
        self.llm = llm_service  # LLM 서비스 추가
        
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
            '자리 배치도': '총무',  # ✅ 자리 배치도 추가
            '엔카닷컴 소개': '비즈니스',
            '비교견적 서비스': '비즈니스',
            '기업 혁신': '비즈니스',
        }
    
    def get_category_questions(self, category: str, limit: int = 10) -> List[str]:
        """
        카테고리별 대표 질문 반환 (메타데이터 기반)
        
        Args:
            category: 카테고리 이름 (HR, IT, 총무, 복리후생, 비즈니스, 기업 소개)
            limit: 반환할 질문 수 (기본 10개)
            
        Returns:
            대표 질문 리스트
        """
        # LLM 서비스가 있으면 메타데이터에서 질문 생성 (enabled 여부 무관, 메타데이터만 있으면 OK)
        if self.llm and hasattr(self.llm, 'metadata'):
            return self._get_questions_from_metadata(category, limit)
        
        # 시맨틱 검색이 있으면 기존 방식 사용
        if self.semantic:
            return self._get_questions_from_semantic(category, limit)
        
        # 둘 다 없으면 빈 배열
        return []
    
    def _get_questions_from_metadata(self, category: str, limit: int = 10) -> List[str]:
        """메타데이터에서 카테고리별 대표 질문 생성 (자연스러운 질문 형태로)"""
        metadata = self.llm.metadata.get("categories", {})
        questions = []
        
        for section_id, section_data in metadata.items():
            display_name = section_data.get("display_name")
            if display_name == category:
                # 섹션 제목을 자연스러운 질문 형태로 변환
                title = section_data.get("title", "")
                if not title:
                    continue
                
                # 제목 분석하여 적절한 질문 형태로 변환
                question = self._convert_to_natural_question(title)
                
                if question:
                    questions.append(question)
                    
                    if len(questions) >= limit:
                        break
        
        return questions[:limit]
    
    def _convert_to_natural_question(self, title: str) -> str:
        """제목을 자연스러운 질문으로 변환"""
        title = title.strip()
        
        # 패턴별로 다양한 질문 형태 생성
        if "방법" in title:
            # "연차 신청 방법" → "연차는 어떻게 신청하나요?"
            base = title.replace("방법", "").strip()
            return f"{base}은 어떻게 하나요?"
        
        elif "신청" in title or "확인" in title:
            # "휴가 신청" → "휴가는 어떻게 신청하나요?"
            # "취소" → "취소는 어떻게 하나요?"
            if "취소" in title:
                return f"{title.replace('취소', '')}취소는 어떻게 하나요?"
            else:
                return f"{title}은 어떻게 하나요?"
        
        elif "사용" in title:
            # "연차 사용" → "연차는 어떻게 사용하나요?"
            return f"{title} 방법이 궁금해요"
        
        elif "관리" in title or "현황" in title or "분포" in title or "배치" in title:
            # "외부인 방문 관리" → "외부인 방문은 어떻게 관리하나요?"
            # "지점 분포 현황" → "지점은 어디에 있나요?"
            if "현황" in title or "분포" in title:
                base = title.replace("현황", "").replace("분포", "").strip()
                return f"{base}는 어디에 있나요?"
            else:
                base = title.replace("관리", "").strip()
                return f"{base}는 어떻게 관리하나요?"
        
        elif "총정리" in title or "지도" in title:
            # "사이트 총정리" → "관련 사이트는 어디인가요?"
            base = title.replace("총정리", "").replace("지도", "").strip()
            return f"{base}는 어디서 볼 수 있나요?"
        
        elif "이용" in title or "예약" in title:
            # "리조트 이용" → "리조트는 어떻게 이용하나요?"
            base = title.replace("이용", "").replace("및", "").replace("예약", "").strip()
            return f"{base}는 어떻게 이용하나요?"
        
        elif "지원" in title or "혜택" in title or "서비스" in title:
            # "경조사 지원" → "경조사 지원에는 어떤 게 있나요?"
            # "임직원 혜택" → "임직원 혜택은 뭐가 있나요?"
            base = title.replace("지원", "").replace("혜택", "").replace("서비스", "").strip()
            if "임직원" in base:
                return f"{title}은 뭐가 있나요?"
            else:
                return f"{title}에는 어떤 게 있나요?"
        
        elif "정산" in title or "처리" in title:
            # "BBL 정산" → "BBL은 어떻게 정산하나요?"
            base = title.replace("정산", "").replace("처리", "").strip()
            return f"{base}은 어떻게 정산하나요?"
        
        elif "활동" in title:
            # "조직문화 활동" → "조직문화 활동에는 뭐가 있나요?"
            return f"{title}에는 뭐가 있나요?"
        
        elif "플랫폼" in title or "시스템" in title:
            # "핵심 플랫폼" → "핵심 플랫폼은 무엇인가요?"
            return f"{title}은 무엇인가요?"
        
        elif "혁신" in title or "개요" in title:
            # "기술 혁신" → "어떤 기술을 사용하나요?"
            if "기술" in title:
                return "어떤 기술을 사용하나요?"
            elif "개요" in title:
                base = title.replace("개요", "").strip()
                return f"{base}에 대해 알려주세요"
            else:
                return f"{title}에 대해 알려주세요"
        
        elif "키트" in title or "APP" in title:
            # "웰컴 키트" → "웰컴 키트는 무엇인가요?"
            return f"{title}는 무엇인가요?"
        
        elif "조직" in title and "팀" in title:
            # "조직도 및 팀" → "조직 구조는 어떻게 되나요?"
            return "조직 구조는 어떻게 되나요?"
        
        elif "미션" in title or "비전" in title or "연혁" in title:
            # "미션, 비전 및 연혁" → "회사의 미션과 비전은 무엇인가요?"
            return "회사의 미션과 비전은 무엇인가요?"
        
        elif "상품" in title and "서비스" in title:
            # "대표 상품 및 서비스" → "주요 상품과 서비스는 무엇인가요?"
            return "주요 상품과 서비스는 무엇인가요?"
        
        elif "법" in title or "엔티튜드" in title:
            # "엔카스럽게 사는 법, 엔티튜드" → "엔카의 핵심 가치는 무엇인가요?"
            return "엔카의 핵심 가치는 무엇인가요?"
        
        elif len(title) <= 8 and ("휴가" in title or "반차" in title):
            # 짧은 휴가 관련 키워드
            return f"{title}는 언제 사용하나요?"
        
        elif "보험" in title:
            return f"{title}은 어떤 것인가요?"
        
        elif len(title) <= 10:
            # 짧은 일반 키워드 (받침 여부에 따라 가/이 선택)
            last_char = title[-1]
            # 받침 있으면 '이', 없으면 '가'
            if (ord(last_char) - 0xAC00) % 28 > 0:  # 한글 받침 판단
                return f"{title}이 궁금해요"
            else:
                return f"{title}가 궁금해요"
        
        else:
            # 긴 제목
            return f"{title}에 대해 알려주세요"
    
    def _get_questions_from_semantic(self, category: str, limit: int = 10) -> List[str]:
        """시맨틱 검색 엔진에서 질문 추출 (기존 방식)"""
        # 해당 카테고리에 속하는 H2 섹션 찾기
        h2_sections = [h2 for h2, cat in self.md_category_map.items() if cat == category]
        
        if not h2_sections:
            return []
        
        # 시맨틱 인덱스에서 해당 카테고리의 문서 필터링
        questions = []
        seen_titles = set()
        
        for doc in self.semantic.documents:
            # 카테고리가 일치하는 문서만
            doc_category = self._get_category(doc)
            if doc_category != category:
                continue
            
            # 질문 추출 (title이 있고, 중복 제거)
            title = doc.get('title', '').strip()
            if title and title not in seen_titles and not title.startswith('[Page'):
                questions.append(title)
                seen_titles.add(title)
                
                if len(questions) >= limit:
                    break
        
        return questions
    
    def _get_related_questions_from_llm(self, matched_category: str, current_question: str, limit: int = 3) -> List[str]:
        """
        LLM 메타데이터에서 유사한 질문 추출 (3단계 폴백)
        
        Args:
            matched_category: 매칭된 카테고리 ID (예: "HR_5", "IT_0")
            current_question: 현재 질문 (중복 제거용)
            limit: 반환할 질문 수
            
        Returns:
            유사한 질문 리스트
        """
        if not self.llm or not self.llm.metadata:
            print("   ⚠️ LLM 또는 메타데이터 없음")
            return []
        
        try:
            categories = self.llm.metadata.get("categories", self.llm.metadata)
            related_questions = []
            
            # 매칭된 카테고리 정보 가져오기
            matched_info = categories.get(matched_category)
            if not matched_info:
                print(f"   ⚠️ 매칭된 카테고리 정보 없음: {matched_category}")
                return []
            
            matched_h2 = matched_info.get("h2") or matched_info.get("h2_section", "")
            matched_display_name = matched_info.get("display_name", "")
            matched_keywords = set(matched_info.get("keywords", []))
            
            print(f"   📍 매칭된 정보 - H2: '{matched_h2}', 카테고리: '{matched_display_name}'")
            
            # ========== 1단계: 같은 H2 섹션에서 찾기 ==========
            if matched_h2:
                print(f"   🔍 1단계: 같은 H2 섹션('{matched_h2}')에서 검색")
                related_questions.extend(
                    self._find_related_in_h2(categories, matched_category, matched_h2, current_question, limit)
                )
            
            # ========== 2단계: 같은 카테고리(display_name)에서 찾기 ==========
            if len(related_questions) < limit and matched_display_name:
                print(f"   🔍 2단계: 같은 카테고리('{matched_display_name}')에서 검색")
                related_questions.extend(
                    self._find_related_in_category(categories, matched_category, matched_display_name, current_question, limit - len(related_questions))
                )
            
            # ========== 3단계: 키워드 유사도로 찾기 ==========
            if len(related_questions) < limit and matched_keywords:
                print(f"   🔍 3단계: 키워드 유사도로 검색")
                related_questions.extend(
                    self._find_related_by_keywords(categories, matched_category, matched_keywords, current_question, limit - len(related_questions))
                )
            
            print(f"   ✅ 최종 유사 질문 {len(related_questions)}개 추출됨: {related_questions}")
            return related_questions[:limit]
            
        except Exception as e:
            print(f"   ❌ 유사 질문 추출 오류: {e}")
            import traceback
            traceback.print_exc()
            return []
    
    def _find_related_in_h2(self, categories: dict, matched_category: str, matched_h2: str, current_question: str, limit: int) -> List[str]:
        """1단계: 같은 H2 섹션에서 유사한 질문 찾기"""
        related_questions = []
        
        for category_id, info in categories.items():
            if category_id == matched_category:
                continue
            
            current_h2 = info.get("h2") or info.get("h2_section", "")
            if current_h2 == matched_h2:
                title = (info.get("h4") or info.get("h4_section") or 
                        info.get("h3") or info.get("h3_section") or 
                        info.get("title", ""))
                
                if title:
                    natural_question = self._convert_to_natural_question(title)
                    if natural_question != current_question and natural_question not in related_questions:
                        related_questions.append(natural_question)
                        if len(related_questions) >= limit:
                            break
        
        print(f"      → H2에서 {len(related_questions)}개 발견")
        return related_questions
    
    def _find_related_in_category(self, categories: dict, matched_category: str, matched_display_name: str, current_question: str, limit: int) -> List[str]:
        """2단계: 같은 카테고리(display_name)에서 유사한 질문 찾기"""
        related_questions = []
        
        for category_id, info in categories.items():
            if category_id == matched_category:
                continue
            
            if info.get("display_name") == matched_display_name:
                title = (info.get("h4") or info.get("h4_section") or 
                        info.get("h3") or info.get("h3_section") or 
                        info.get("title", ""))
                
                if title:
                    natural_question = self._convert_to_natural_question(title)
                    if natural_question != current_question and natural_question not in related_questions:
                        related_questions.append(natural_question)
                        if len(related_questions) >= limit:
                            break
        
        print(f"      → 카테고리에서 {len(related_questions)}개 발견")
        return related_questions
    
    def _find_related_by_keywords(self, categories: dict, matched_category: str, matched_keywords: set, current_question: str, limit: int) -> List[str]:
        """3단계: 키워드 유사도로 유사한 질문 찾기"""
        related_questions = []
        candidates = []
        
        for category_id, info in categories.items():
            if category_id == matched_category:
                continue
            
            category_keywords = set(info.get("keywords", []))
            # 교집합 개수로 유사도 계산
            similarity = len(matched_keywords & category_keywords)
            
            if similarity > 0:
                title = (info.get("h4") or info.get("h4_section") or 
                        info.get("h3") or info.get("h3_section") or 
                        info.get("title", ""))
                
                if title:
                    natural_question = self._convert_to_natural_question(title)
                    if natural_question != current_question:
                        candidates.append((similarity, natural_question))
        
        # 유사도 높은 순으로 정렬
        candidates.sort(key=lambda x: x[0], reverse=True)
        
        for _, question in candidates[:limit]:
            if question not in related_questions:
                related_questions.append(question)
        
        print(f"      → 키워드 유사도로 {len(related_questions)}개 발견")
        return related_questions
    
    def process_question(self, question: str) -> AnswerResponse:
        """
        질문 처리 메인 로직 (LLM 우선)
        
        우선순위:
        1. LLM 서비스 (OpenAI API) - API 키 있을 때
        2. 시맨틱 검색 (RAG)
        3. 키워드 검색 (폴백)
        
        Args:
            question: 사용자 질문
            
        Returns:
            AnswerResponse
        """
        start_time = time.time()
        
        # 1순위: LLM 검색 시도 (API 키 있을 때)
        if self.llm and self.llm.enabled:
            try:
                result = self._llm_search(question, start_time)
                if result:
                    print("✅ LLM 검색 성공")
                    return result
            except Exception as e:
                print(f"⚠️  LLM 검색 오류: {e}, 다음 방법 시도")
        
        # 2순위: 시맨틱 검색 시도 (현재 비활성화됨)
        if self.semantic:
            try:
                result = self._semantic_search(question, start_time)
                if result:
                    print("✅ 시맨틱 검색 성공")
                    return result
            except Exception as e:
                print(f"⚠️  시맨틱 검색 오류: {e}")
        
        # ❌ 3순위: 키워드 검색 폴백 제거 (오답 방지)
        # 대신 친절한 안내 응답 제공
        print("ℹ️  검색 결과 없음 - 친절한 안내 제공")
        return self._enhanced_no_result_response(question, start_time)
    
    def process_question_stream(self, question: str):
        """
        질문 처리 (스트리밍 응답)
        
        Args:
            question: 사용자 질문
            
        Yields:
            답변 청크 (Server-Sent Events 형식)
        """
        # LLM 서비스만 스트리밍 지원
        if not (self.llm and self.llm.enabled):
            # 스트리밍 미지원 시 일반 응답
            result = self.process_question(question)
            yield f"data: {result.answer}\n\n"
            yield "data: [DONE]\n\n"
            return
        
        try:
            # LLM 스트리밍 검색
            llm_result = self.llm.search_and_answer_stream(question)
            for chunk in llm_result:
                # Server-Sent Events 형식으로 전송
                yield f"data: {chunk}\n\n"
            yield "data: [DONE]\n\n"
            
        except Exception as e:
            print(f"⚠️  스트리밍 오류: {e}")
            # 폴백: 일반 응답
            result = self.process_question(question)
            yield f"data: {result.answer}\n\n"
            yield "data: [DONE]\n\n"
    
    def _llm_search(self, question: str, start_time: float) -> Optional[AnswerResponse]:
        """
        LLM 기반 검색 및 답변 생성
        
        Args:
            question: 사용자 질문
            start_time: 시작 시간
            
        Returns:
            AnswerResponse 또는 None
        """
        result = self.llm.search_and_answer(question)
        
        if not result.get("success"):
            return None
        
        # 유사한 질문 추출 (같은 H2 카테고리 내에서)
        matched_cat = result.get("matched_category", "")
        print(f"🔗 유사 질문 추출 시도: matched_category='{matched_cat}'")
        
        related_questions = self._get_related_questions_from_llm(
            matched_cat,
            current_question=question,
            limit=3
        )
        
        print(f"✅ 유사 질문 {len(related_questions)}개 추출됨: {related_questions}")
        
        return AnswerResponse(
            answer=result["answer"],
            department='엔디(Endy)',
            link=None,
            category=result.get("category", "일반"),
            confidence_score=0.95,  # LLM은 높은 신뢰도
            related_questions=related_questions,
            response_time=round(time.time() - start_time, 3)
        )
    
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
        """명확한 질문에 대한 직접 답변 (RAG 지원)"""
        # RAG 자연어 청크 처리
        chunk_type = best_doc.get('chunk_type', 'qa')
        
        if chunk_type == 'natural':
            # 자연어 청크: 계층 정보 + 내용 그대로 반환
            hierarchy = []
            if best_doc.get('h2'):
                hierarchy.append(best_doc['h2'])
            if best_doc.get('h3'):
                hierarchy.append(best_doc['h3'])
            if best_doc.get('h4'):
                hierarchy.append(best_doc['h4'])
            
            hierarchy_str = " > ".join(hierarchy) if hierarchy else ""
            answer = f"**[{hierarchy_str}]**\n\n{best_doc['content']}" if hierarchy_str else best_doc['content']
        
        elif 'answer' in best_doc and best_doc['answer']:
            # FAQ 형식 (질문/답변 구조)
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
                related_questions.append(title)
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
        
        # 섹션별로 질문 제시 (섹션명과 질문이 같으면 질문만 표시)
        for i, (section, docs) in enumerate(list(section_groups.items())[:4], 1):
            # 섹션명 추가
            shown_titles.add(section)
            related_questions.append(section)
            
            # 섹션명과 다른 하위 질문만 추가
            for doc, score in docs[:2]:  # 섹션당 최대 2개 (섹션명 제외하고 하위 질문)
                title = doc.get('title', '')
                # 섹션명과 질문이 유사하면 스킵
                if title and title not in shown_titles and not title.startswith('[Page') and title != section:
                    shown_titles.add(title)
                    related_questions.append(title)
        
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
            doc['title'] 
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
            related_questions = [r['question'] for r in related]
            
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
                    "모바일 앱은 어떻게 다운받나요?",
                    "지점 분포는 어떻게 되나요?"
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
    
    def _enhanced_no_result_response(self, question: str, start_time: float) -> AnswerResponse:
        """개선된 '결과 없음' 응답 (카테고리 힌트 포함)"""
        
        # 질문에서 카테고리 힌트 추출
        category_hint = ""
        hint_questions = []
        
        if any(kw in question for kw in ["휴가", "연차", "반차", "근태", "출장", "경조사"]):
            category_hint = "\n\n💡 **혹시 찾으시는 정보가 'HR' 카테고리에 있을 수 있어요!**\n상단의 'HR' 버튼을 눌러보세요."
            hint_questions = ["연차는 어떻게 사용하나요?", "휴가 신청 방법이 궁금해요"]
        elif any(kw in question for kw in ["네트워크", "VDI", "PC", "노트북", "와이파이", "프로그램", "설치"]):
            category_hint = "\n\n💡 **혹시 찾으시는 정보가 'IT' 카테고리에 있을 수 있어요!**\n상단의 'IT' 버튼을 눌러보세요."
            hint_questions = ["VDI는 어떻게 접속하나요?", "네트워크 에이전트 설치 방법"]
        elif any(kw in question for kw in ["복지", "건강검진", "BBL", "상품권", "포상"]):
            category_hint = "\n\n💡 **혹시 찾으시는 정보가 '복리후생' 카테고리에 있을 수 있어요!**\n상단의 '복리후생' 버튼을 눌러보세요."
            hint_questions = ["건강검진은 어떻게 받나요?", "BBL 정산 방법이 궁금해요"]
        elif any(kw in question for kw in ["사무실", "주차", "명함", "택배", "출입"]):
            category_hint = "\n\n💡 **혹시 찾으시는 정보가 '총무' 카테고리에 있을 수 있어요!**\n상단의 '총무' 버튼을 눌러보세요."
            hint_questions = ["주차권은 어떻게 신청하나요?", "명함 신청 방법"]
        
        answer = f"""죄송해요, "{question}"에 대한 정보를 찾지 못했어요. 😢{category_hint}

**다른 방법으로 질문해보세요**
• 다른 단어로 바꿔서 질문해주세요
• 좀 더 구체적으로 질문해주세요
• 상단 카테고리 버튼에서 찾아보세요

그래도 안 되면 담당 부서에 직접 문의해주세요!"""
        
        return AnswerResponse(
            answer=answer,
            department='엔디(Endy)',
            link=None,
            category='안내',
            confidence_score=0.0,
            related_questions=hint_questions,
            response_time=round(time.time() - start_time, 3)
        )


