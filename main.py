"""
Encar Copilot (Endy) - FastAPI 메인 애플리케이션
사내 지식 어시스턴트 백엔드 서버
"""
from fastapi import FastAPI, HTTPException, Header, Request
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from typing import Optional
import time
from datetime import datetime

from models import (
    QuestionRequest, AnswerResponse, Feedback,
    LoginRequest, LoginResponse
)
from database import db
from search_engine import search_engine
from auth import auth_manager

# 시맨틱 검색 엔진 (로컬, 무료)
try:
    from semantic_search import SemanticSearchEngine
    semantic_engine = None  # 시작 시 로드
    SEMANTIC_SEARCH_ENABLED = True
except ImportError:
    SEMANTIC_SEARCH_ENABLED = False
    print("⚠️  시맨틱 검색이 비활성화되었습니다. 'pip install sentence-transformers faiss-cpu'로 설치하세요.")


# FastAPI 앱 초기화
app = FastAPI(
    title="Encar Copilot (Endy)",
    description="사내 지식 어시스턴트 API",
    version="1.0.0"
)

# CORS 설정
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # 실제 배포 시에는 특정 도메인만 허용
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 정적 파일 및 템플릿 설정
app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates")


# 헬퍼 함수: 세션 토큰 검증
def get_current_user(authorization: Optional[str] = Header(None)):
    """현재 로그인한 사용자 조회"""
    if not authorization:
        return None
    
    # Bearer 토큰 형식 처리
    token = authorization.replace("Bearer ", "") if authorization.startswith("Bearer ") else authorization
    
    user = auth_manager.get_current_user(token)
    return user


# ==================== 메인 페이지 ====================

@app.get("/", response_class=HTMLResponse)
async def home(request: Request):
    """메인 페이지"""
    return templates.TemplateResponse("index.html", {"request": request})


# ==================== 인증 API ====================

@app.post("/api/login", response_model=LoginResponse)
async def login(login_request: LoginRequest):
    """
    로그인
    - 사번과 이름으로 간단한 인증
    """
    return auth_manager.login(login_request)


@app.post("/api/logout")
async def logout(authorization: Optional[str] = Header(None)):
    """로그아웃"""
    if not authorization:
        raise HTTPException(status_code=401, detail="인증 토큰이 없습니다")
    
    token = authorization.replace("Bearer ", "") if authorization.startswith("Bearer ") else authorization
    success = auth_manager.logout(token)
    
    if success:
        return {"success": True, "message": "로그아웃되었습니다"}
    else:
        return {"success": False, "message": "유효하지 않은 세션입니다"}


@app.get("/api/me")
async def get_me(authorization: Optional[str] = Header(None)):
    """현재 로그인한 사용자 정보 조회"""
    user = get_current_user(authorization)
    
    if not user:
        raise HTTPException(status_code=401, detail="인증이 필요합니다")
    
    return {"success": True, "user": user.dict()}


# ==================== 질문 응답 API ====================

@app.post("/api/ask", response_model=AnswerResponse)
async def ask_question(
    question_request: QuestionRequest,
    authorization: Optional[str] = Header(None)
):
    """
    질문에 대한 답변 제공
    - 시맨틱 검색 우선 (의미 기반, 자연어 이해)
    - 폴백: 키워드 기반 검색
    """
    # 인증 확인 (선택사항, MVP에서는 느슨하게)
    user = get_current_user(authorization)
    
    # 시작 시간 기록
    start_time = time.time()
    
    # 질문 텍스트 검증
    if not question_request.question.strip():
        raise HTTPException(status_code=400, detail="질문을 입력해주세요")
    
    question = question_request.question.strip()
    # 질문 정규화 (띄어쓰기 제거)
    normalized_question = question.replace(" ", "")
    
    # 시맨틱 검색 시도 (활성화된 경우)
    if SEMANTIC_SEARCH_ENABLED and semantic_engine:
        try:
            # 시맨틱 검색으로 상위 결과 찾기 (원본 + 정규화 버전)
            results = semantic_engine.search(question, top_k=10)
            if normalized_question != question:
                results_normalized = semantic_engine.search(normalized_question, top_k=5)
                # 두 결과 병합 (중복 제거)
                seen_titles = set()
                combined = []
                for doc, score in results + results_normalized:
                    if doc['title'] not in seen_titles:
                        seen_titles.add(doc['title'])
                        combined.append((doc, score))
                results = sorted(combined, key=lambda x: x[1], reverse=True)[:10]
            
            if results and len(results) > 0:
                # FAQ와 MD 파일 결과 분리
                faq_results = [(doc, score) for doc, score in results if doc.get('source') == 'FAQ']
                md_results = [(doc, score) for doc, score in results if doc.get('source') != 'FAQ']
                
                # MD 파일 최우선! (FAQ는 보조)
                best_md = md_results[0] if md_results else None
                best_faq = faq_results[0] if faq_results else None
                
                # MD 파일이 있으면 무조건 MD 우선 (점수가 충분히 높을 때만)
                if best_md:
                    md_doc, md_score = best_md
                    # MD 점수가 최소 임계값(0.2) 이상이면 MD 사용 (관련 없는 질문 필터링)
                    if md_score >= 0.2:
                        best_match, score = best_md
                    elif best_faq:
                        # MD 점수가 너무 낮으면 FAQ로 폴백
                        best_match, score = best_faq
                    else:
                        best_match, score = best_md
                elif best_faq:
                    # MD 결과가 없으면 FAQ 사용
                    best_match, score = best_faq
                else:
                    best_match, score = results[0]
                
                # 신뢰도가 충분히 높으면 (MD 파일은 0.2, FAQ는 0.15)
                min_threshold = 0.2 if best_match.get('source') != 'FAQ' else 0.15
                if score >= min_threshold:
                    # FAQ 소스인지 MD 소스인지 확인
                    if best_match.get('source') == 'FAQ':
                        # FAQ 답변
                        response_time = time.time() - start_time
                        
                        # 관련 질문 추천 (시맨틱 검색 결과 활용)
                        related_questions = [
                            {"question": doc['title']} 
                            for doc, _ in results[1:4]  # 2~4번째 결과
                            if doc.get('source') == 'FAQ'
                        ]
                        
                        return AnswerResponse(
                            answer=best_match['content'].split('\n\n답변: ')[1] if '\n\n답변: ' in best_match['content'] else best_match['content'],
                            department='엔디(Endy)',  # 항상 엔디로 통일
                            link=best_match.get('link'),
                            category=best_match.get('category', '일반'),
                            confidence_score=round(score, 2),
                            related_questions=related_questions,
                            response_time=round(response_time, 3)
                        )
                    else:
                        # MD 파일 답변 (엔카생활가이드 등)
                        response_time = time.time() - start_time
                        
                        # 관련 섹션들 모아서 답변 구성
                        answer_parts = []
                        high_score_sections = []  # 높은 점수 섹션들
                        
                        for doc, s in results[:5]:  # 상위 5개 결과 확인
                            if s >= 0.25:  # 관련도 임계값 상향 (0.15 → 0.25)
                                high_score_sections.append((doc, s))
                        
                        # 점수가 비슷한 섹션이 여러 개면 → 선택 옵션 제공
                        if len(high_score_sections) >= 2:
                            # 최고 점수와 차이가 0.08 이내인 섹션들 (0.1 → 0.08로 엄격화)
                            best_score = high_score_sections[0][1]
                            similar_sections = [
                                (doc, s) for doc, s in high_score_sections 
                                if best_score - s <= 0.08
                            ]
                            
                            # 마인드맵 모드 조건 강화: 최고 점수가 0.35 이상이고 2개 이상일 때만
                            if len(similar_sections) >= 2 and best_score >= 0.35:
                                # 여러 옵션 제공 (마인드맵 스타일)
                                answer = f"**'{question}'** 관련하여 여러 섹션이 있습니다:\n\n"
                                for i, (doc, _) in enumerate(similar_sections[:4], 1):
                                    # 섹션 미리보기 (처음 100자)
                                    preview = doc['content'][:100].replace('\n', ' ') + "..."
                                    answer += f"**{i}. {doc['title']}**\n{preview}\n\n"
                                
                                answer += "💡 더 구체적으로 질문하시거나, 위 섹션 중 하나를 선택해주세요!"
                                
                                # 관련 질문으로 섹션 제목들 제공
                                related_questions = [
                                    {"question": doc['title']} 
                                    for doc, _ in similar_sections[:4]
                                ]
                            else:
                                # 하나만 명확하면 바로 답변 (질문 제외, 답변만 표시)
                                for doc, s in high_score_sections[:1]:  # 상위 1개만
                                    # 질문/답변 형식 제거 - 답변만 추출
                                    content = doc['content']
                                    
                                    # "**질문:**" 이후 "**답변:**" 부분만 추출
                                    if '**답변:**' in content:
                                        # 답변 부분만 추출
                                        answer_part = content.split('**답변:**')[1]
                                        # 다음 섹션 시작(###) 전까지만
                                        if '###' in answer_part:
                                            answer_part = answer_part.split('###')[0]
                                        content = answer_part.strip()
                                    
                                    # H3 청킹으로 자연스럽게 짧아지므로 길이 제한 제거
                                    answer_parts.append(f"**{doc['title']}**\n\n{content}")
                                
                                answer = "\n\n---\n\n".join(answer_parts)
                                
                                # 추가 관련 질문 (노이즈 필터링: [Page XX] 제외)
                                related_questions = [
                                    {"question": doc['title']} 
                                    for doc, _ in results[3:6]
                                    if doc.get('title') and not doc['title'].startswith('[Page')
                                ]
                        else:
                            # 결과가 1개뿐이면 바로 답변 (질문 제외, 답변만 표시)
                            for doc, s in high_score_sections:
                                content = doc['content']
                                
                                # "**질문:**" 이후 "**답변:**" 부분만 추출
                                if '**답변:**' in content:
                                    answer_part = content.split('**답변:**')[1]
                                    # 다음 섹션 시작(###) 전까지만
                                    if '###' in answer_part:
                                        answer_part = answer_part.split('###')[0]
                                    content = answer_part.strip()
                                
                                # H3 청킹으로 자연스럽게 짧아지므로 길이 제한 제거
                                answer_parts.append(f"**{doc['title']}**\n\n{content}")
                            
                            answer = "\n\n---\n\n".join(answer_parts) if answer_parts else "관련 정보를 찾지 못했습니다."
                            
                            # 추가 관련 질문
                            related_questions = [
                                {"question": doc['title']} 
                                for doc, _ in results[3:6]
                                if doc.get('title') and not doc['title'].startswith('[Page')
                            ]
                        
                        # MD 파일의 카테고리 매핑 (H2 기준)
                        md_category_map = {
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
                        
                        # category 필드 우선 사용 (H3 청킹 후)
                        doc_category = best_match.get('category', '')
                        category = md_category_map.get(doc_category, '총무')  # category 필드로 매핑
                        
                        return AnswerResponse(
                            answer=answer,
                            department='엔디(Endy)',  # 항상 엔디로 통일
                            link=None,
                            category=category,
                            confidence_score=round(score, 2),
                            related_questions=related_questions,
                            response_time=round(response_time, 3)
                        )
        except Exception as e:
            # 시맨틱 검색 실패 시 키워드 검색으로 폴백
            print(f"⚠️  시맨틱 검색 오류: {e}, 키워드 검색으로 전환")
    
    # 폴백: 기존 키워드 기반 검색
    all_faqs = db.get_all_faqs()
    
    if not all_faqs:
        raise HTTPException(status_code=500, detail="FAQ 데이터를 불러올 수 없습니다")
    
    # 최적의 FAQ 검색 (개선된 부분 문자열 매칭 사용)
    result = search_engine.get_best_match(
        question, 
        all_faqs,
        threshold=0.1  # 부분 문자열 매칭으로 인해 임계값 상향
    )
    
    # 응답 시간 계산
    response_time = time.time() - start_time
    
    # 신뢰도 임계값 설정 (낮은 점수면 질문 목록 제시)
    CONFIDENCE_THRESHOLD = 0.25  # 이 값보다 낮으면 질문 목록 제시
    
    # 결과가 있지만 신뢰도가 낮은 경우
    if result:
        best_faq, score = result
        
        # 신뢰도가 낮으면 관련 질문 목록 제시
        if score < CONFIDENCE_THRESHOLD:
            # 검색어와 관련된 FAQ 찾기
            suggestions = []
            search_keywords = question.lower().replace('?', '').strip()
            
            for faq in all_faqs:
                if (search_keywords in faq.question.lower() or 
                    search_keywords in faq.main_answer.lower() or
                    any(search_keywords in kw.lower() for kw in faq.keywords)):
                    suggestions.append(faq.question)
            
            if suggestions:
                answer_text = f"'{question}'에 대해 이런 질문들이 있어요. 원하시는 내용을 선택해주세요:\n\n"
                for i, sugg in enumerate(suggestions[:5], 1):
                    answer_text += f"{i}. {sugg}\n"
                answer_text += "\n💡 더 구체적으로 질문하시면 정확한 답변을 드릴 수 있어요!"
                
                return AnswerResponse(
                    answer=answer_text,
                    department="엔디(Endy)",
                    link=None,
                    category="일반",
                    confidence_score=round(score, 2),
                    related_questions=[{"question": q} for q in suggestions[:5]],
                    response_time=response_time
                )
    
    # 답변이 없는 경우 - 관련 질문 제안
    if not result:
        # 검색어와 관련된 FAQ 찾기 (키워드, 질문, 답변에서 검색)
        suggestions = []
        search_keywords = question.lower().replace('?', '').strip()
        
        for faq in all_faqs:
            # 질문, 답변, 키워드에 검색어가 포함되어 있으면 추가
            if (search_keywords in faq.question.lower() or 
                search_keywords in faq.main_answer.lower() or
                any(search_keywords in kw.lower() for kw in faq.keywords)):
                suggestions.append(faq.question)
        
        if suggestions:
            answer_text = f"'{question}' 관련해서 이런 질문들이 있어요:\n\n"
            for i, sugg in enumerate(suggestions[:5], 1):
                answer_text += f"{i}. {sugg}\n"
            answer_text += "\n💡 위 질문 중 하나를 선택해보세요!"
        else:
            answer_text = f"'{question}'에 대한 정보를 찾지 못했어요.\n\n💡 이렇게 물어보세요:\n• '연차는 언제 생기나요?'\n• '와이파이 비밀번호'\n• '휴가 신청 방법'"
        
        return AnswerResponse(
            answer=answer_text,
            department="엔디(Endy)",
            link=None,
            category="일반",
            confidence_score=0.0,
            related_questions=[{"question": q} for q in suggestions[:5]] if suggestions else [],
            response_time=response_time
        )
    
    best_faq, score = result
    
    # 관련 질문 추천
    related_questions = search_engine.get_related_questions(
        best_faq, 
        all_faqs, 
        max_count=5
    )
    
    return AnswerResponse(
        answer=best_faq.main_answer,
        department='엔디(Endy)',  # 항상 엔디로 통일
        link=best_faq.link,
        category=best_faq.category,
        confidence_score=round(score, 2),
        related_questions=related_questions,
        response_time=round(response_time, 3)
    )


@app.get("/api/questions")
async def get_all_questions():
    """모든 FAQ 질문 목록 조회"""
    faqs = db.get_all_faqs()
    
    return {
        "success": True,
        "count": len(faqs),
        "questions": [
            {
                "id": faq.id,
                "category": faq.category,
                "question": faq.question,
                "department": faq.department
            }
            for faq in faqs
        ]
    }


@app.get("/api/categories")
async def get_categories():
    """카테고리 목록 조회"""
    categories = db.get_all_categories()
    
    return {
        "success": True,
        "categories": categories
    }


@app.get("/api/questions/category/{category}")
async def get_questions_by_category(category: str):
    """카테고리별 질문 조회"""
    faqs = db.get_faqs_by_category(category)
    
    return {
        "success": True,
        "category": category,
        "count": len(faqs),
        "questions": [
            {
                "id": faq.id,
                "question": faq.question,
                "department": faq.department
            }
            for faq in faqs
        ]
    }


# ==================== 피드백 API ====================

@app.post("/api/feedback")
async def submit_feedback(
    feedback: Feedback,
    authorization: Optional[str] = Header(None)
):
    """
    피드백 제출
    - 답변이 도움이 되었는지 평가
    """
    # 현재 사용자 정보 (있으면 추가)
    user = get_current_user(authorization)
    if user:
        feedback.user_id = user.employee_id
    
    # 피드백 저장
    success = db.add_feedback(feedback)
    
    if success:
        return {
            "success": True,
            "message": "피드백 감사합니다! 더 나은 서비스를 제공하겠습니다."
        }
    else:
        raise HTTPException(status_code=500, detail="피드백 저장에 실패했습니다")


@app.get("/api/feedback/stats")
async def get_feedback_stats(authorization: Optional[str] = Header(None)):
    """
    피드백 통계 조회
    - 관리자용 API
    """
    # 인증 확인 (실제로는 관리자 권한 확인 필요)
    user = get_current_user(authorization)
    if not user:
        raise HTTPException(status_code=401, detail="인증이 필요합니다")
    
    stats = db.get_feedback_stats()
    
    return {
        "success": True,
        "stats": stats
    }


# ==================== 헬스 체크 ====================

@app.get("/health")
async def health_check():
    """서버 상태 확인"""
    return {
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "service": "Encar Copilot (Endy)",
        "version": "1.0.0"
    }


@app.get("/api/info")
async def get_info():
    """서비스 정보"""
    faqs = db.get_all_faqs()
    categories = db.get_all_categories()
    stats = db.get_feedback_stats()
    
    return {
        "service": "Encar Copilot (Endy)",
        "version": "1.0.0",
        "description": "사내 지식 어시스턴트",
        "stats": {
            "total_faqs": len(faqs),
            "categories": categories,
            "feedback_stats": stats
        }
    }


# ==================== 에러 핸들러 ====================

@app.exception_handler(404)
async def not_found_handler(request: Request, exc: HTTPException):
    """404 에러 핸들러"""
    return JSONResponse(
        status_code=404,
        content={"detail": "요청하신 페이지를 찾을 수 없습니다"}
    )


@app.exception_handler(500)
async def internal_error_handler(request: Request, exc: Exception):
    """500 에러 핸들러"""
    return JSONResponse(
        status_code=500,
        content={"detail": "서버 오류가 발생했습니다"}
    )


# ==================== 시작 및 종료 이벤트 ====================

@app.on_event("startup")
async def startup_event():
    """서버 시작 시 실행"""
    global semantic_engine
    
    print("🚀 Encar Copilot (Endy) 서버 시작")
    print(f"📊 FAQ 데이터: {len(db.get_all_faqs())}개 로드됨")
    print(f"👥 사용자 데이터: {len(db.get_all_users())}명 등록됨")
    
    # 시맨틱 검색 엔진 로드 (자동 인덱싱)
    if SEMANTIC_SEARCH_ENABLED:
        try:
            import os
            from pathlib import Path
            
            # MD 파일 변경 확인
            md_files_path = Path('docs')
            index_path = Path('data/semantic_index')
            
            needs_rebuild = False
            
            if not index_path.exists():
                print("⚠️  시맨틱 인덱스가 없습니다. 자동 생성합니다...")
                needs_rebuild = True
            else:
                # 인덱스 파일 수정 시간
                index_file = index_path / 'faiss.index'
                if index_file.exists():
                    index_mtime = index_file.stat().st_mtime
                    
                    # MD 파일들의 최신 수정 시간
                    md_files = list(md_files_path.glob('*.md'))
                    if md_files:
                        latest_md_mtime = max(f.stat().st_mtime for f in md_files)
                        
                        if latest_md_mtime > index_mtime:
                            print("📝 MD 파일 변경 감지! 인덱스 자동 재생성...")
                            needs_rebuild = True
            
            # 인덱스 재생성 필요 시
            if needs_rebuild:
                print("🔄 시맨틱 인덱스 자동 생성 중...")
                from semantic_search import build_semantic_search_index
                build_semantic_search_index()
                print("✅ 인덱스 생성 완료!")
            
            # 인덱스 로드
            print("🔍 시맨틱 검색 엔진 로딩 중...")
            semantic_engine = SemanticSearchEngine()
            semantic_engine.load_index()
            print("✅ 시맨틱 검색 활성화!")
            
        except Exception as e:
            print(f"⚠️  시맨틱 검색 로드 실패: {e}")
            print("    키워드 검색만 사용합니다.")
    else:
        print("ℹ️  시맨틱 검색 비활성화 (키워드 검색만 사용)")


@app.on_event("shutdown")
async def shutdown_event():
    """서버 종료 시 실행"""
    print("👋 Encar Copilot (Endy) 서버 종료")
    # 만료된 세션 정리
    cleaned = auth_manager.cleanup_expired_sessions()
    print(f"🧹 {cleaned}개의 만료된 세션 정리 완료")


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )

