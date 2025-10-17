"""
LLM 기반 검색 서비스
OpenAI API를 사용한 메타데이터 기반 문서 검색 및 답변 생성
"""
import json
import os
from pathlib import Path
from typing import Optional, Dict, List
from openai import OpenAI


class LLMSearchService:
    """LLM 기반 검색 및 답변 생성 서비스"""
    
    def __init__(self):
        """초기화"""
        # OpenAI API 키 설정 (환경변수에서 로드)
        self.api_key = os.getenv("OPENAI_API_KEY", "")
        if self.api_key:
            self.client = OpenAI(api_key=self.api_key)
            self.enabled = True
            print("✅ LLM 서비스 활성화 (OpenAI API)")
        else:
            self.client = None
            self.enabled = False
            print("⚠️  LLM 서비스 비활성화 (OPENAI_API_KEY 미설정)")
        
        # 메타데이터 로드
        self.metadata = self._load_metadata()
        self.documents_cache = {}  # MD 파일 캐시
        self.answer_cache = {}  # 답변 캐시 (질문 → 답변) - 프롬프트 변경 시 자동 초기화됨 (v20250117_10)
    
    def _load_metadata(self) -> Dict:
        """메타데이터 JSON 로드"""
        metadata_path = Path("data/documents_metadata.json")
        
        if not metadata_path.exists():
            print("⚠️  메타데이터 파일 없음")
            return {"categories": {}}
        
        try:
            with open(metadata_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            print(f"✅ 메타데이터 로드: {len(data.get('categories', {}))}개 카테고리")
            return data
        except Exception as e:
            print(f"❌ 메타데이터 로드 실패: {e}")
            return {"categories": {}}
    
    def _load_document(self, filename: str, start_line: int = None, end_line: int = None) -> str:
        """
        MD 문서 로드 (캐시 사용)
        
        Args:
            filename: 파일명
            start_line: 시작 줄 (1부터 시작, None이면 전체)
            end_line: 끝 줄 (포함, None이면 전체)
        
        Returns:
            문서 내용 (특정 범위 또는 전체)
        """
        doc_path = Path("docs") / filename
        
        if not doc_path.exists():
            return ""
        
        try:
            # 전체 파일을 캐시에 저장
            if filename not in self.documents_cache:
                with open(doc_path, 'r', encoding='utf-8') as f:
                    self.documents_cache[filename] = f.readlines()
            
            lines = self.documents_cache[filename]
            
            # 특정 범위만 반환
            if start_line is not None and end_line is not None:
                # 인덱스는 0부터 시작하므로 -1
                return ''.join(lines[start_line-1:end_line])
            else:
                return ''.join(lines)
            
        except Exception as e:
            print(f"❌ 문서 로드 실패 ({filename}): {e}")
            return ""
    
    def extract_keywords(self, question: str) -> List[str]:
        """
        LLM을 사용하여 질문에서 키워드 추출
        
        Args:
            question: 사용자 질문
        
        Returns:
            추출된 키워드 리스트
        """
        if not self.enabled:
            # LLM 비활성화 시 간단한 토큰화
            return self._simple_tokenize(question)
        
        try:
            response = self.client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[
                    {
                        "role": "system",
                        "content": "당신은 한국어 질문에서 핵심 키워드를 추출하는 전문가입니다. 질문을 분석하여 3-5개의 핵심 키워드만 추출하세요. 키워드는 쉼표로 구분하여 반환하세요."
                    },
                    {
                        "role": "user",
                        "content": f"다음 질문에서 핵심 키워드를 추출하세요: {question}"
                    }
                ],
                temperature=0.3,
                max_tokens=50
            )
            
            keywords_str = response.choices[0].message.content.strip()
            keywords = [k.strip() for k in keywords_str.split(',')]
            
            print(f"🔍 LLM 키워드 추출: {question} → {keywords}")
            return keywords
            
        except Exception as e:
            print(f"⚠️  LLM 키워드 추출 실패: {e}, 폴백 사용")
            return self._simple_tokenize(question)
    
    def _simple_tokenize(self, text: str) -> List[str]:
        """간단한 토큰화 (LLM 실패 시 폴백)"""
        import re
        words = re.findall(r'[가-힣a-zA-Z0-9]+', text)
        return [w for w in words if len(w) >= 2][:5]
    
    def classify_question_intent(self, question: str) -> str:
        """
        질문 의도 분류
        
        Returns:
            'concept': 개념/소개 질문
            'howto': 방법 질문
            'when': 시기 질문
            'where': 장소/위치 질문
            'howmuch': 금액 질문
            'general': 일반 질문
        """
        if any(kw in question for kw in ["뭐예요", "무엇", "궁금해요", "궁금", "소개", "알려줘", "설명", "이란", "란"]):
            return 'concept'
        elif any(kw in question for kw in ["어떻게", "방법", "사용", "신청", "처리", "등록", "설치"]):
            return 'howto'
        elif any(kw in question for kw in ["언제", "기간", "일정", "시간", "날짜", "몇시", "몇일"]):
            return 'when'
        elif any(kw in question for kw in ["어디", "위치", "장소", "볼 수 있", "확인", "찾"]):
            return 'where'
        elif any(kw in question for kw in ["얼마", "금액", "비용", "가격", "요금"]):
            return 'howmuch'
        else:
            return 'general'
    
    def get_prompt_by_intent(self, intent: str, contact_team: str, contact_name: str, contact_phone: str) -> str:
        """의도별 최적화된 프롬프트 생성"""
        
        if intent == 'concept':
            return f"""당신은 엔카 사내 지식 어시스턴트 '엔디'입니다.
따뜻하고 친근한 톤으로 **서비스나 제도를 소개**해주세요.

🎯 **톤앤매너**:
- 친근하고 따뜻한 말투: "~예요!", "~할 수 있어요!", "~해요 😊"
- 사무적 표현 금지

📝 **답변 구조**:
[서비스/제도에 대한 친근한 소개 1~2문장]

**특징**
• 첫 번째 특징이나 장점
• 두 번째 특징이나 장점
• 세 번째 특징이나 장점

**참고**
추가로 알아두면 좋을 정보를 2~3문장으로 자세히 설명 (선택사항)

**문의**
{contact_team} {contact_name}({contact_phone})

✅ **작성 규칙**:
1. 섹션 제목 다음 줄에 바로 내용 (공백 없음)
2. 각 섹션 사이에만 정확히 한 줄 공백
3. 서비스의 개념과 장점 중심으로 설명
4. 사용 방법은 간단히만 언급"""

        elif intent == 'where':
            return f"""당신은 엔카 사내 지식 어시스턴트 '엔디'입니다.
따뜻하고 친근한 톤으로 **위치나 접근 방법**을 안내해주세요.

🎯 **톤앤매너**:
- 친근하고 따뜻한 말투: "~예요!", "~하시면 돼요!", "~해주세요 😊"

📝 **답변 구조**:
[위치나 접근 방법을 1~2문장으로 직접 안내]

**위치/접근 방법**
• 구체적인 위치나 경로
• 온라인 접근 방법 (해당 시)
• 추가 정보

**참고**
유용한 팁이나 주의사항 (선택사항)

**문의**
{contact_team} {contact_name}({contact_phone})

✅ **작성 규칙**:
1. 섹션 제목 다음 줄에 바로 내용 (공백 없음)
2. 각 섹션 사이에만 정확히 한 줄 공백"""

        else:  # 'howto', 'when', 'howmuch', 'general'
            return f"""당신은 엔카 사내 지식 어시스턴트 '엔디'입니다.
따뜻하고 친근한 톤으로 답변하며, 사용자가 쉽게 이해할 수 있도록 도와줍니다.

🎯 **톤앤매너 (필수 준수)**:
- 친근하고 따뜻한 말투: "~하실 수 있어요!", "~해주세요 😊", "~하시면 돼요!"
- 사무적 표현 절대 금지: "별도 등록이 필요하지 않습니다" (X) → "따로 등록 안 하셔도 돼요!" (O)
- 문장 끝: "~예요", "~해요", "~하시면 돼요", "~할 수 있어요"
- 1~2줄 단위로 나누어 스캔하기 쉽게 작성

📝 **답변 구조 (반드시 이 순서대로)**:
[질문에 대한 직접적인 답 1~2문장, 친근한 톤으로]

**방법**
1. 첫 번째 단계 (구체적으로: 어디서, 무엇을, 어떻게)
2. 두 번째 단계
3. 세 번째 단계 (필요시)

**참고**
주의사항이나 추가 팁을 2~3문장으로 자세하고 친절하게 설명 (선택사항)

**문의**
{contact_team} {contact_name}({contact_phone})

✅ **작성 규칙 (절대 준수)**:
1. **방법** 섹션은 단계가 명확하면 "1. 2. 3." 형식의 번호 사용 (필수는 아님)
2. 섹션 제목(**방법**, **참고**, **문의**) 다음 줄에 바로 내용 (공백 없음)
3. 각 섹션 사이에만 정확히 한 줄 공백
4. 볼드(**텍스트**)는 섹션 제목에만 사용 (본문에 절대 사용 금지)
5. 첫 문장은 라벨 없이 바로 답변 시작
6. 톤앤매너: 친근하고 자세하게
7. 오타 절대 금지

예시:
질문: "휴가는 어떻게 신청하나요?"
답변:
그룹웨어에서 신청하시면 돼요! 아주 간단해요 😊

**방법**
1. 그룹웨어 접속 후 '휴가 신청' 메뉴를 눌러주세요
2. 날짜와 휴가 종류를 선택하고 제출하시면 끝!
3. PC-OFF에 자동으로 반영돼요 (따로 등록 안 하셔도 돼요)

**참고**
신청 후 1~2분 안에 PC-OFF에 자동으로 반영돼요. 만약 반영이 안 되면 IT팀에 연락 주세요. 빠르게 도와드릴게요!

**문의**
{contact_team} {contact_name}({contact_phone})
"""
    
    def find_matching_category(self, keywords: List[str]) -> Optional[Dict]:
        """
        키워드로 매칭되는 카테고리 찾기
        
        Args:
            keywords: 추출된 키워드 리스트
        
        Returns:
            매칭된 카테고리 정보 (dict) 또는 None
        """
        categories = self.metadata.get("categories", {})
        
        # 각 카테고리별 매칭 점수 계산
        scores = {}
        
        for cat_id, cat_info in categories.items():
            cat_keywords = cat_info.get("keywords", [])
            
            # 키워드 매칭 개수 카운트
            matches = sum(1 for kw in keywords if any(kw in ck or ck in kw for ck in cat_keywords))
            
            if matches > 0:
                scores[cat_id] = {
                    "score": matches,
                    "info": cat_info
                }
        
        if not scores:
            print("❌ 매칭된 카테고리 없음")
            return None
        
        # 가장 높은 점수의 카테고리 반환
        best_match = max(scores.items(), key=lambda x: x[1]["score"])
        best_cat_id, best_data = best_match
        
        # 임계값 검증: 최소 2개 이상의 키워드가 매칭되어야 함
        MIN_MATCH_SCORE = 2
        if best_data['score'] < MIN_MATCH_SCORE:
            print(f"⚠️  매칭 점수 부족: {best_cat_id} (점수: {best_data['score']} < {MIN_MATCH_SCORE})")
            return None
        
        print(f"📂 매칭된 카테고리: {best_cat_id} (점수: {best_data['score']})")
        
        return {
            "category_id": best_cat_id,
            **best_data["info"]
        }
    
    def find_best_section_by_llm(self, question: str) -> Optional[Dict]:
        """
        LLM을 사용하여 질문에 가장 적합한 문서 섹션 찾기
        (키워드 매칭 실패 시 사용)
        
        Args:
            question: 사용자 질문
            
        Returns:
            선택된 카테고리 정보 또는 None
        """
        if not self.enabled:
            return None
        
        try:
            categories = self.metadata.get("categories", {})
            
            # GPT에게 제공할 섹션 목록 생성 (H2 > H3 > H4 경로)
            section_list = []
            for cat_id, info in categories.items():
                # 메타데이터 키 이름 확인
                h2 = info.get("h2") or info.get("h2_section", "")
                h3 = info.get("h3") or info.get("h3_section", "")
                h4 = info.get("h4") or info.get("h4_section", "")
                
                # 섹션 경로 생성
                section_path = " > ".join(filter(None, [h2, h3, h4]))
                if section_path:  # 빈 경로는 제외
                    section_list.append(f"{cat_id}: {section_path}")
            
            # 최대 100개 섹션까지만 (토큰 제한)
            section_text = "\n".join(section_list[:100])
            
            # GPT에게 최적 섹션 선택 요청
            response = self.client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[
                    {
                        "role": "system",
                        "content": """당신은 사용자 질문에 가장 적합한 문서 섹션을 찾는 전문가입니다.

규칙:
1. 사용자 질문의 의도를 정확히 파악하세요
2. 제공된 섹션 목록에서 가장 관련성 높은 섹션을 선택하세요
3. 섹션 ID만 반환하세요 (예: "HR_5" 또는 "IT_0")
4. 적합한 섹션이 없으면 "NONE"을 반환하세요
5. 설명 없이 ID만 반환하세요

예시:
질문: "휴가는 어떻게 신청하나요?"
답변: HR_13

질문: "주변 맛집 추천 부탁해요"
답변: 총무_50"""
                    },
                    {
                        "role": "user",
                        "content": f"""[질문]
{question}

[섹션 목록]
{section_text}

가장 적합한 섹션 ID를 선택하세요 (ID만 반환):"""
                    }
                ],
                temperature=0.3,
                max_tokens=20
            )
            
            selected_id = response.choices[0].message.content.strip()
            
            # "NONE" 또는 유효하지 않은 ID 처리
            if selected_id == "NONE" or selected_id not in categories:
                print(f"⚠️  LLM이 적합한 섹션을 찾지 못함: {selected_id}")
                return None
            
            print(f"🎯 LLM이 선택한 섹션: {selected_id}")
            
            return {
                "category_id": selected_id,
                **categories[selected_id]
            }
            
        except Exception as e:
            print(f"❌ LLM 섹션 추천 실패: {e}")
            return None
    
    def generate_answer_stream(self, question: str, document_content: str, category_info: Dict):
        """
        LLM을 사용하여 문서 기반 답변 생성 (스트리밍)
        
        Args:
            question: 사용자 질문
            document_content: 관련 문서 내용
            category_info: 카테고리 정보 (contact 포함)
        
        Yields:
            답변 청크 (실시간 스트리밍)
        """
        if not self.enabled:
            yield self._generate_fallback_answer(question, document_content, category_info)
            return
        
        try:
            # 문서가 너무 길면 잘라내기
            max_doc_length = 20000
            if len(document_content) > max_doc_length:
                document_content = document_content[:max_doc_length] + "\n\n...(이하 생략)"
            
            # 담당자 정보 안전하게 추출
            contact = {}
            if isinstance(category_info, dict):
                contact = category_info.get('contact', {})
                if not isinstance(contact, dict):
                    contact = {}
            
            contact_team = contact.get('team', '담당팀') if contact else '담당팀'
            contact_name = contact.get('name', '담당자') if contact else '담당자'
            contact_phone = contact.get('phone', '연락처') if contact else '연락처'
            
            stream = self.client.chat.completions.create(
                model="gpt-3.5-turbo-16k",
                messages=[
                    {
                        "role": "system",
                        "content": f"""당신은 엔카 사내 지식 어시스턴트 '엔디'입니다. 
따뜻하고 친근한 톤으로 답변하며, 사용자가 쉽게 이해할 수 있도록 도와줍니다.

🎯 **톤앤매너 (필수 준수)**:
- 친근하고 따뜻한 말투: "~하실 수 있어요!", "~해주세요 😊", "~하시면 돼요!"
- 사무적 표현 절대 금지: "별도 등록이 필요하지 않습니다" (X) → "따로 등록 안 하셔도 돼요!" (O)
- 문장 끝: "~예요", "~해요", "~하시면 돼요", "~할 수 있어요"
- 1~2줄 단위로 나누어 스캔하기 쉽게 작성

📝 **답변 구조 (반드시 이 순서대로)**:
[질문에 대한 직접적인 답 1~2문장, 친근한 톤으로]

**방법**
1. 첫 번째 단계 (구체적으로: 어디서, 무엇을, 어떻게)
2. 두 번째 단계
3. 세 번째 단계 (필요시)

**참고**
주의사항이나 추가 팁을 2~3문장으로 자세하고 친절하게 설명 (선택사항)

**문의**
{contact_team} {contact_name}({contact_phone})

✅ **작성 규칙**:
1. 섹션 제목(**방법**, **참고**, **문의**) 바로 다음 줄에 내용 작성 (공백 없음)
2. 각 섹션 사이에만 정확히 한 줄 공백
3. 리스트는 번호(1. 2. 3.) 또는 점(•)으로 통일
4. 볼드(**텍스트**)는 섹션 제목에만 사용
5. 첫 문장은 라벨 없이 바로 답변 시작
6. 오타 절대 금지

예시:
질문: "휴가는 어떻게 신청하나요?"
답변:
그룹웨어에서 신청하시면 돼요! 아주 간단해요 😊

**방법**
1. 그룹웨어 접속 후 '휴가 신청' 메뉴를 눌러주세요
2. 날짜와 휴가 종류를 선택하고 제출하시면 끝!
3. PC-OFF에 자동으로 반영돼요 (따로 등록 안 하셔도 돼요)

**참고**
신청 후 1~2분 안에 PC-OFF에 자동으로 반영돼요. 만약 반영이 안 되면 IT팀에 연락 주세요. 빠르게 도와드릴게요!

**문의**
{contact_team} {contact_name}({contact_phone})
"""
                    },
                    {
                        "role": "user",
                        "content": f"""다음 문서를 읽고, 사용자 질문에 답변하세요.
원문을 그대로 복사하지 말고, 질문 의도에 맞게 재구성하세요.

[문서 내용]
{document_content}

[질문]
{question}

중요: 
- 답변 첫 문장은 라벨 없이 바로 시작
- 섹션 제목 다음 줄에 바로 내용 (공백 없음)
- 친근하고 따뜻한 톤 유지"""
                    }
                ],
                temperature=0.1,
                max_tokens=1500,
                stream=True  # 스트리밍 활성화
            )
            
            for chunk in stream:
                if chunk.choices[0].delta.content:
                    yield chunk.choices[0].delta.content
            
        except Exception as e:
            print(f"⚠️  LLM 스트리밍 실패: {e}, 폴백 사용")
            yield self._generate_fallback_answer(question, document_content, category_info)
    
    def generate_answer(self, question: str, document_content: str, category_info: Dict) -> str:
        """
        LLM을 사용하여 문서 기반 답변 생성
        
        Args:
            question: 사용자 질문
            document_content: 관련 문서 내용
            category_info: 카테고리 정보
        
        Returns:
            생성된 답변
        """
        if not self.enabled:
            return self._generate_fallback_answer(question, document_content, category_info)
        
        # 문서 내용이 너무 짧으면 경고
        if len(document_content) < 200:
            section_title = category_info.get('title', 'Unknown')
            print(f"⚠️  [정보 부족] 질문: '{question}' / 섹션: '{section_title}' / 내용: {len(document_content)}자")
            print(f"   📝 관리자 확인 필요: MD 파일에 해당 섹션의 내용을 보완해주세요.")
        
        try:
            # 문서가 너무 길면 잘라내기 (GPT-3.5 토큰 제한: ~16K 토큰)
            # 한글 1자 = 약 2토큰, 여유있게 20,000자로 제한
            max_doc_length = 20000
            if len(document_content) > max_doc_length:
                document_content = document_content[:max_doc_length] + "\n\n...(이하 생략)"
            
            # 담당자 정보 안전하게 추출
            contact = {}
            if isinstance(category_info, dict):
                contact = category_info.get('contact', {})
                if not isinstance(contact, dict):
                    contact = {}
            
            contact_team = contact.get('team', '담당팀') if contact else '담당팀'
            contact_name = contact.get('name', '담당자') if contact else '담당자'
            contact_phone = contact.get('phone', '연락처') if contact else '연락처'
            
            # ✅ 질문 의도 분류
            intent = self.classify_question_intent(question)
            print(f"🎯 질문 의도: {intent}")
            
            # ✅ 의도별 최적화된 프롬프트 생성
            system_prompt = self.get_prompt_by_intent(intent, contact_team, contact_name, contact_phone)
            
            response = self.client.chat.completions.create(
                model="gpt-3.5-turbo-16k",  # 16K 토큰 모델 사용
                messages=[
                    {
                        "role": "system",
                        "content": system_prompt
                    },
                    {
                        "role": "user",
                        "content": f"""다음 문서를 읽고, 사용자 질문에 답변하세요.
원문을 그대로 복사하지 말고, 엔디의 친근한 톤으로 재구성하세요.

[문서 내용]
{document_content}

[질문]
{question}

[질문 유형]
{intent}

중요 (절대 준수): 
- 답변 첫 문장은 라벨 없이 바로 시작
- 섹션 제목 다음 줄에 바로 내용 (공백 없음)
- **방법** 섹션은 단계가 명확하면 "1. 2. 3." 번호 사용 (필수 아님)
- 볼드(**텍스트**)는 섹션 제목에만 사용 (본문 절대 사용 금지)
- 톤앤매너: 친근하고 자세하게
- 질문 유형({intent})에 맞는 구조로 답변"""
                    }
                ],
                temperature=0.1,  # 일관성을 위해 낮춤
                max_tokens=1500
            )
            
            answer = response.choices[0].message.content.strip()
            print(f"💬 LLM 답변 생성 완료 ({len(answer)}자)")
            
            return answer
            
        except Exception as e:
            print(f"⚠️  LLM 답변 생성 실패: {e}, 폴백 사용")
            return self._generate_fallback_answer(question, document_content, category_info)
    
    def _generate_fallback_answer(self, question: str, document_content: str, category_info: Dict) -> str:
        """LLM 실패 시 폴백 답변 (문서 일부 + 담당자 정보)"""
        # 문서에서 질문과 관련된 부분 찾기 (간단한 키워드 매칭)
        keywords = self._simple_tokenize(question)
        
        # 문서를 줄 단위로 분할
        lines = document_content.split('\n')
        relevant_lines = []
        
        for line in lines[:100]:  # 처음 100줄만 검색
            if any(kw in line for kw in keywords):
                relevant_lines.append(line)
            
            if len(relevant_lines) >= 10:
                break
        
        if relevant_lines:
            answer = "관련 정보를 찾았습니다:\n\n" + "\n".join(relevant_lines[:5])
        else:
            answer = "죄송합니다. 관련 정보를 찾지 못했습니다."
        
        # 담당자 정보 추가 (안전하게 처리)
        contact = {}
        if isinstance(category_info, dict):
            contact = category_info.get('contact', {})
            if not isinstance(contact, dict):
                contact = {}
        
        team = contact.get('team', '담당팀') if contact else '담당팀'
        name = contact.get('name', '담당자') if contact else '담당자'
        phone = contact.get('phone', '연락처 미등록') if contact else '연락처 미등록'
        
        answer += f"\n\n📞 자세한 내용은 {team} {name}({phone})에게 문의해주세요."
        
        return answer
    
    def _get_cache_key(self, question: str) -> str:
        """질문을 정규화하여 캐시 키 생성 (의미있는 특수문자 유지)"""
        import re
        # 공백만 제거, 특수문자(+, -, _ 등)는 유지하여 구분 가능하도록
        normalized = re.sub(r'\s+', '', question.lower())
        return normalized
    
    def search_and_answer_stream(self, question: str):
        """
        질문에 대한 답변 생성 (스트리밍)
        
        Args:
            question: 사용자 질문
            
        Yields:
            답변 청크 (실시간 스트리밍)
        """
        # 1단계: 키워드 추출
        keywords = self.extract_keywords(question)
        
        # 2단계: 카테고리 매칭
        category_info = self.find_matching_category(keywords)
        
        if not category_info:
            yield "죄송합니다. 관련 정보를 찾지 못했습니다. 다른 키워드로 질문해주시겠어요?"
            return
        
        # 3단계: 문서 로드 (특정 섹션만)
        filename = category_info.get("filename", "")
        start_line = category_info.get("start_line")
        end_line = category_info.get("end_line")
        
        document_content = self._load_document(filename, start_line, end_line)
        
        if not document_content:
            contact = category_info.get('contact', {})
            yield f"문서를 찾을 수 없습니다. {contact.get('team', '담당팀')} {contact.get('name', '담당자')}({contact.get('phone', '연락처 미등록')})에게 문의해주세요."
            return
        
        # 4단계: LLM 답변 생성 (스트리밍)
        for chunk in self.generate_answer_stream(question, document_content, category_info):
            yield chunk
    
    def search_and_answer(self, question: str) -> Dict:
        """
        질문에 대한 답변 생성 (전체 프로세스)
        
        Args:
            question: 사용자 질문
        
        Returns:
            답변 정보 (dict)
        """
        # 캐시 확인
        cache_key = self._get_cache_key(question)
        if cache_key in self.answer_cache:
            cached = self.answer_cache[cache_key]
            print(f"💾 캐시된 답변 사용: {question}")
            return {
                "success": True,
                "answer": cached["answer"],
                "category": cached.get("category"),
                "contact": cached.get("contact"),
                "matched_category": cached.get("matched_category"),  # ✅ 유사 질문 추출용
                "cached": True
            }
        
        # 1단계: 키워드 추출
        keywords = self.extract_keywords(question)
        
        # 2단계: 키워드 매칭 (엄격)
        category_info = self.find_matching_category(keywords)
        
        # ✅ 3단계: 키워드 매칭 실패 시 LLM에게 직접 물어보기
        if not category_info:
            print("🤖 LLM 기반 섹션 추천 시도...")
            category_info = self.find_best_section_by_llm(question)
        
        if not category_info:
            return {
                "success": False,
                "answer": "죄송해요, 관련 정보를 찾지 못했어요. 😢\n\n다른 방식으로 질문해주시거나, 담당 부서에 직접 문의해주세요!",
                "category": None,
                "contact": None
            }
        
        # 3단계: 문서 로드 (특정 섹션만)
        filename = category_info.get("filename", "")
        start_line = category_info.get("start_line")
        end_line = category_info.get("end_line")
        
        # 특정 섹션만 로드 (라인 범위가 있으면)
        document_content = self._load_document(filename, start_line, end_line)
        
        if not document_content:
            contact = category_info.get('contact', {})
            return {
                "success": False,
                "answer": f"문서를 찾을 수 없습니다. {contact.get('team', '담당팀')} {contact.get('name', '담당자')}({contact.get('phone', '연락처 미등록')})에게 문의해주세요.",
                "category": category_info.get("category_id"),
                "contact": contact
            }
        
        # 디버깅: 어떤 섹션을 읽었는지 출력
        section_info = category_info.get("title", "알 수 없음")
        print(f"📖 읽은 섹션: {section_info} (라인 {start_line}-{end_line}, {len(document_content)}자)")
        
        # 4단계: LLM 답변 생성
        answer = self.generate_answer(question, document_content, category_info)
        
        # 답변 캐시 저장
        result = {
            "success": True,
            "answer": answer,
            "category": category_info.get("display_name"),
            "contact": category_info.get("contact"),
            "keywords": keywords,
            "matched_category": category_info.get("category_id")
        }
        
        self.answer_cache[cache_key] = {
            "answer": answer,
            "category": category_info.get("display_name"),
            "contact": category_info.get("contact"),
            "matched_category": category_info.get("category_id")  # ✅ 유사 질문 추출용
        }
        print(f"💾 답변 캐시 저장: {question}")
        
        return result


# 싱글톤 인스턴스
llm_service = LLMSearchService()

