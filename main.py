"""
Encar Copilot (Endy) - FastAPI 메인 애플리케이션
사내 지식 어시스턴트 백엔드 서버
"""
from fastapi import FastAPI, HTTPException, Header, Request
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse
from fastapi.middleware.cors import CORSMiddleware
from typing import Optional
from pathlib import Path

from models import QuestionRequest, AnswerResponse, Feedback, LoginRequest, LoginResponse
from database import db
from search_engine import search_engine
from auth import auth_manager
from config.settings import settings
from services import AnswerService

# 시맨틱 검색 엔진
try:
    from semantic_search import SemanticSearchEngine
    semantic_engine = None  # startup_event에서 초기화
    SEMANTIC_SEARCH_ENABLED = settings.SEMANTIC_SEARCH_ENABLED
except ImportError:
    SEMANTIC_SEARCH_ENABLED = False
    semantic_engine = None
    print("⚠️  시맨틱 검색 비활성화. 'pip install sentence-transformers faiss-cpu'로 설치하세요.")

# 답변 서비스 (startup_event에서 초기화)
answer_service = None


# FastAPI 앱 초기화
app = FastAPI(
    title="Encar Copilot (Endy)",
    description="사내 지식 어시스턴트 API",
    version="2.0.0"
)

# CORS 설정
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 정적 파일 및 템플릿 설정
app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates")


# ==================== 헬퍼 함수 ====================

def get_current_user(authorization: Optional[str] = Header(None)):
    """현재 로그인한 사용자 조회"""
    if not authorization:
        return None
    
    token = authorization.replace("Bearer ", "") if authorization.startswith("Bearer ") else authorization
    return auth_manager.get_current_user(token)


# ==================== 라우트 ====================

@app.get("/", response_class=HTMLResponse)
async def home(request: Request):
    """메인 페이지"""
    return templates.TemplateResponse("index.html", {"request": request})


# ==================== 인증 API ====================

@app.post("/api/login", response_model=LoginResponse)
async def login(login_request: LoginRequest):
    """로그인"""
    return auth_manager.login(login_request)


@app.post("/api/logout")
async def logout(authorization: Optional[str] = Header(None)):
    """로그아웃"""
    if not authorization:
        raise HTTPException(status_code=401, detail="인증 토큰이 없습니다")
    
    token = authorization.replace("Bearer ", "") if authorization.startswith("Bearer ") else authorization
    success = auth_manager.logout(token)
    
    return {
        "success": success, 
        "message": "로그아웃되었습니다" if success else "유효하지 않은 세션입니다"
    }


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
    # 인증 확인 (선택사항)
    user = get_current_user(authorization)
    
    # 질문 검증
    if not question_request.question.strip():
        raise HTTPException(status_code=400, detail="질문을 입력해주세요")
    
    # 답변 서비스로 처리
    try:
        return answer_service.process_question(question_request.question.strip())
    except Exception as e:
        print(f"❌ 답변 처리 오류: {e}")
        raise HTTPException(status_code=500, detail="답변 처리 중 오류가 발생했습니다")


# ==================== 피드백 API ====================

@app.post("/api/feedback")
async def submit_feedback(
    feedback: Feedback,
    authorization: Optional[str] = Header(None)
):
    """피드백 제출"""
    user = get_current_user(authorization)
    
    if db.add_feedback(feedback):
        return {"success": True, "message": "피드백이 저장되었습니다"}
    else:
        raise HTTPException(status_code=500, detail="피드백 저장 중 오류가 발생했습니다")


@app.get("/api/feedback/stats")
async def get_feedback_stats(authorization: Optional[str] = Header(None)):
    """피드백 통계 조회 (관리자용)"""
    user = get_current_user(authorization)
    
    if not user:
        raise HTTPException(status_code=401, detail="인증이 필요합니다")
    
    return db.get_feedback_stats()


# ==================== FAQ 관리 API ====================

@app.get("/api/faqs")
async def get_faqs(category: Optional[str] = None):
    """FAQ 목록 조회"""
    if category and category != 'all':
        faqs = db.get_faqs_by_category(category)
    else:
        faqs = db.get_all_faqs()
    
    return {"faqs": [faq.dict() for faq in faqs]}


@app.get("/api/categories")
async def get_categories():
    """카테고리 목록 조회"""
    categories = db.get_all_categories()
    return {"categories": categories}


# ==================== 서버 이벤트 ====================

@app.on_event("startup")
async def startup_event():
    """서버 시작 시 실행"""
    global semantic_engine, answer_service
    
    print("🚀 Encar Copilot (Endy) v2.0 서버 시작")
    print(f"📊 FAQ 데이터: {len(db.get_all_faqs())}개 로드됨")
    print(f"👥 사용자 데이터: {len(db.get_all_users())}명 등록됨")
    
    # 시맨틱 검색 엔진 초기화
    if SEMANTIC_SEARCH_ENABLED:
        try:
            # MD 파일 변경 확인 및 인덱스 자동 재생성
            md_files_path = Path(settings.MD_FILES_DIR)
            index_path = Path(settings.SEMANTIC_INDEX_DIR)
            
            needs_rebuild = False
            
            if not index_path.exists():
                print("⚠️  시맨틱 인덱스가 없습니다. 자동 생성합니다...")
                needs_rebuild = True
            else:
                index_file = index_path / 'faiss.index'
                if index_file.exists():
                    index_mtime = index_file.stat().st_mtime
                    md_files = list(md_files_path.glob('*.md'))
                    
                    if md_files:
                        latest_md_mtime = max(f.stat().st_mtime for f in md_files)
                        if latest_md_mtime > index_mtime:
                            print("📝 MD 파일 변경 감지! 인덱스 자동 재생성...")
                            needs_rebuild = True
            
            # 인덱스 재생성
            if needs_rebuild:
                print("🔄 시맨틱 인덱스 자동 생성 중...")
                from semantic_search import build_semantic_search_index
                build_semantic_search_index()
                print("✅ 인덱스 생성 완료!")
            
            # 엔진 로드
            print("🔍 시맨틱 검색 엔진 로딩 중...")
            semantic_engine = SemanticSearchEngine()
            semantic_engine.load_index()
            print("✅ 시맨틱 검색 활성화!")
            
        except Exception as e:
            print(f"⚠️  시맨틱 검색 로드 실패: {e}")
            print("    키워드 검색만 사용합니다.")
    else:
        print("ℹ️  시맨틱 검색 비활성화 (키워드 검색만 사용)")
    
    # 답변 서비스 초기화
    answer_service = AnswerService(
        semantic_engine=semantic_engine,
        keyword_engine=search_engine,
        db=db
    )
    print("✅ 답변 서비스 초기화 완료!")


@app.on_event("shutdown")
async def shutdown_event():
    """서버 종료 시 실행"""
    print("👋 Encar Copilot (Endy) 서버 종료")
    cleaned = auth_manager.cleanup_expired_sessions()
    print(f"🧹 {cleaned}개의 만료된 세션 정리 완료")


# ==================== 메인 실행 ====================

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "main:app",
        host=settings.HOST,
        port=settings.PORT,
        reload=settings.RELOAD,
        log_level=settings.LOG_LEVEL
    )
