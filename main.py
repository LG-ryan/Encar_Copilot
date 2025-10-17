"""
Encar Copilot (Endy) - FastAPI 메인 애플리케이션
사내 지식 어시스턴트 백엔드 서버
"""
from fastapi import FastAPI, HTTPException, Header, Request
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse, StreamingResponse, JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from fastapi.exceptions import RequestValidationError
from starlette.exceptions import HTTPException as StarletteHTTPException
from typing import Optional
from pathlib import Path
import time

from models import QuestionRequest, AnswerResponse, Feedback, DetailedFeedback, LoginRequest, LoginResponse
from database import db
from search_engine import search_engine
from auth import auth_manager
from config.settings import settings
from services import AnswerService
from utils.exceptions import EncarCopilotException, RateLimitError, AuthorizationError
from utils.logger import get_logger, log_error, log_api_request
from utils.rate_limiter import get_rate_limiter
from utils.metrics import (
    get_metrics, track_api_request, track_llm_request,
    track_cache_operation, track_feedback, track_error
)
from utils.auth import UserRole, check_permission

# 로거 초기화
logger = get_logger()

# 레이트리밋 초기화
rate_limiter = get_rate_limiter()

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

# CORS 설정 (보안 강화)
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.allowed_origins_list,  # 환경변수에서 로드
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE"],
    allow_headers=["Authorization", "Content-Type"],
)


# 보안 헤더 미들웨어
@app.middleware("http")
async def add_security_headers(request: Request, call_next):
    """보안 헤더 추가"""
    response = await call_next(request)
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["X-XSS-Protection"] = "1; mode=block"
    response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
    
    # CSP (Content Security Policy)
    if settings.ENVIRONMENT == "production":
        response.headers["Content-Security-Policy"] = (
            "default-src 'self'; "
            "script-src 'self' 'unsafe-inline' https://cdn.jsdelivr.net; "
            "style-src 'self' 'unsafe-inline'; "
            "img-src 'self' data: https:; "
            "font-src 'self' data:; "
            "connect-src 'self';"
        )
    
    return response


# 전역 예외 처리
@app.exception_handler(EncarCopilotException)
async def encar_copilot_exception_handler(request: Request, exc: EncarCopilotException):
    """커스텀 예외 처리"""
    log_error(
        f"[{exc.error_code}] {exc.message}",
        context={"path": request.url.path, "details": exc.details}
    )
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "error": exc.error_code,
            "message": exc.message,
            "details": exc.details
        }
    )


@app.exception_handler(StarletteHTTPException)
async def http_exception_handler(request: Request, exc: StarletteHTTPException):
    """HTTP 예외 처리"""
    log_error(
        f"HTTP {exc.status_code}: {exc.detail}",
        context={"path": request.url.path}
    )
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "error": "http_error",
            "message": str(exc.detail),
            "details": {}
        }
    )


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    """입력 검증 예외 처리"""
    log_error(
        "입력 검증 실패",
        context={"path": request.url.path, "errors": exc.errors()}
    )
    return JSONResponse(
        status_code=422,
        content={
            "error": "validation_error",
            "message": "입력 값이 유효하지 않습니다",
            "details": {"errors": exc.errors()}
        }
    )


@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    """글로벌 예외 처리"""
    log_error(
        "예상치 못한 오류 발생",
        error=exc,
        context={"path": request.url.path}
    )
    return JSONResponse(
        status_code=500,
        content={
            "error": "internal_error",
            "message": "일시적인 오류가 발생했습니다. 잠시 후 다시 시도해주세요.",
            "details": {}
        }
    )

# 정적 파일 및 템플릿 설정
app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates")

# 캐시 버스팅을 위한 버전 정보 (서버 시작 시간 기반)
APP_VERSION = str(int(time.time()))


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
    return templates.TemplateResponse("index.html", {
        "request": request,
        "version": APP_VERSION
    })


# ==================== 헬스체크 & 모니터링 ====================

@app.get("/health")
async def health_check():
    """
    헬스체크 엔드포인트
    
    시스템 상태를 확인하고 각 구성 요소의 정상 여부를 반환합니다.
    - status: healthy, degraded, unhealthy
    - checks: 각 구성 요소별 상태
    """
    from datetime import datetime
    import os
    
    checks = {
        "llm_service": False,
        "database": False,
        "disk_space": False
    }
    
    # LLM 서비스 체크
    try:
        if answer_service and answer_service.llm and answer_service.llm.enabled:
            checks["llm_service"] = True
    except:
        pass
    
    # 데이터베이스 체크 (JSON 파일 접근 가능 여부)
    try:
        if Path(settings.USERS_FILE).exists():
            checks["database"] = True
    except:
        pass
    
    # 디스크 공간 체크 (최소 1GB 남아있어야 함)
    try:
        import shutil
        stats = shutil.disk_usage(".")
        free_gb = stats.free / (1024 ** 3)
        checks["disk_space"] = free_gb > 1.0
    except:
        checks["disk_space"] = True  # 체크 실패 시 OK로 간주
    
    # 전체 상태 판단
    if all(checks.values()):
        status = "healthy"
        status_code = 200
    elif any(checks.values()):
        status = "degraded"
        status_code = 200
    else:
        status = "unhealthy"
        status_code = 503
    
    response = {
        "status": status,
        "timestamp": datetime.utcnow().isoformat() + "Z",
        "version": "2.0.0",
        "checks": checks
    }
    
    return JSONResponse(
        status_code=status_code,
        content=response
    )


@app.get("/readiness")
async def readiness_check():
    """
    준비 상태 체크 (Kubernetes readiness probe용)
    
    서버가 트래픽을 받을 준비가 되었는지 확인
    """
    if answer_service is None:
        return JSONResponse(
            status_code=503,
            content={"ready": False, "message": "서비스 초기화 중"}
        )
    
    return {"ready": True}


@app.get("/liveness")
async def liveness_check():
    """
    생존 상태 체크 (Kubernetes liveness probe용)
    
    서버가 살아있는지만 확인 (단순 응답)
    """
    return {"alive": True}


@app.get("/metrics")
async def metrics():
    """
    Prometheus 메트릭 엔드포인트
    
    - api_requests_total: API 요청 수
    - api_response_seconds: API 응답 시간
    - llm_requests_total: LLM 요청 수
    - cache_operations_total: 캐시 히트/미스
    - feedback_total: 피드백 수
    - errors_total: 에러 수
    """
    if not settings.ENABLE_METRICS:
        return JSONResponse(
            status_code=404,
            content={"error": "metrics_disabled", "message": "메트릭이 비활성화되어 있습니다"}
        )
    
    from fastapi import Response
    metrics_data, content_type = get_metrics()
    return Response(content=metrics_data, media_type=content_type)


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

@app.get("/api/category/{category}/questions")
async def get_category_questions(
    category: str,
    limit: int = 10,
    authorization: Optional[str] = Header(None)
):
    """
    카테고리별 대표 질문 조회
    - 카테고리: HR, IT, 총무, 복리후생, 비즈니스, 기업 소개
    """
    # 인증 확인 (선택사항)
    user = get_current_user(authorization)
    
    # 카테고리 검증
    valid_categories = ['HR', 'IT', '총무', '복리후생', '비즈니스', '기업 소개']
    if category not in valid_categories:
        raise HTTPException(status_code=400, detail=f"유효하지 않은 카테고리입니다. 가능한 카테고리: {', '.join(valid_categories)}")
    
    # 대표 질문 조회
    try:
        questions = answer_service.get_category_questions(category, limit)
        return {
            "success": True,
            "category": category,
            "questions": questions,
            "count": len(questions)
        }
    except Exception as e:
        print(f"⚠️  카테고리 질문 조회 오류: {e}")
        raise HTTPException(status_code=500, detail="카테고리 질문을 불러오는데 실패했습니다")


@app.post("/api/ask", response_model=AnswerResponse)
async def ask_question(
    question_request: QuestionRequest,
    authorization: Optional[str] = Header(None)
):
    """
    질문에 대한 답변 제공 (일반 응답)
    - 시맨틱 검색 우선 (의미 기반, 자연어 이해)
    - 폴백: 키워드 기반 검색
    """
    start_time = time.time()
    
    # 인증 확인 (선택사항)
    user = get_current_user(authorization)
    user_id = user.get("employee_id") if user else "anonymous"
    
    # 레이트리밋 체크
    allowed, message = rate_limiter.is_allowed(
        user_id,
        max_per_minute=settings.RATE_LIMIT_PER_MINUTE,
        max_per_hour=settings.RATE_LIMIT_PER_HOUR
    )
    if not allowed:
        track_error("rate_limit")
        raise RateLimitError(message)
    
    # 질문 검증
    if not question_request.question.strip():
        track_error("validation_error")
        raise HTTPException(status_code=400, detail="질문을 입력해주세요")
    
    # 질문 길이 제한 (DOS 방어)
    if len(question_request.question) > 500:
        track_error("validation_error")
        raise HTTPException(status_code=400, detail="질문이 너무 깁니다 (최대 500자)")
    
    # 답변 서비스로 처리
    try:
        result = answer_service.process_question(question_request.question.strip())
        
        # 메트릭 수집
        duration_ms = (time.time() - start_time) * 1000
        track_api_request("POST", "/api/ask", 200)
        
        # LLM 캐시 여부 추적
        if hasattr(result, 'source') and result.source == 'cache':
            track_cache_operation("hit")
        else:
            track_cache_operation("miss")
            track_llm_request("success")
        
        logger.info(
            f"질문 처리 완료: {question_request.question[:50]}...",
            extra={"user_id": user_id, "duration_ms": duration_ms}
        )
        
        return result
    except Exception as e:
        track_error("processing_error")
        track_api_request("POST", "/api/ask", 500)
        log_error(f"답변 처리 오류: {e}", error=e, context={"user_id": user_id})
        raise HTTPException(status_code=500, detail="답변 처리 중 오류가 발생했습니다")


@app.post("/api/ask/stream")
async def ask_question_stream(
    question_request: QuestionRequest,
    authorization: Optional[str] = Header(None)
):
    """
    질문에 대한 답변 제공 (스트리밍 응답)
    - 답변을 실시간으로 스트리밍
    - 체감 속도 2배 향상
    """
    # 인증 확인 (선택사항)
    user = get_current_user(authorization)
    
    # 질문 검증
    if not question_request.question.strip():
        raise HTTPException(status_code=400, detail="질문을 입력해주세요")
    
    # 스트리밍 응답 생성
    async def generate_stream():
        try:
            # LLM 서비스를 통한 스트리밍
            result = answer_service.process_question_stream(question_request.question.strip())
            for chunk in result:
                yield chunk
        except Exception as e:
            print(f"❌ 스트리밍 처리 오류: {e}")
            yield f"data: {{'error': '답변 처리 중 오류가 발생했습니다'}}\n\n"
    
    return StreamingResponse(
        generate_stream(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
        }
    )


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


@app.post("/api/feedback/detailed")
async def submit_detailed_feedback(
    feedback: DetailedFeedback,
    authorization: Optional[str] = Header(None)
):
    """상세 피드백 제출 (싫어요 + 이유 + 의견)"""
    user = get_current_user(authorization)
    
    # 사용자 정보 추가
    if user:
        feedback.user_id = user.get("employee_id")
        feedback.user_name = user.get("name")
    
    if db.add_detailed_feedback(feedback):
        return {"success": True, "message": "상세 피드백이 저장되었습니다"}
    else:
        raise HTTPException(status_code=500, detail="상세 피드백 저장 중 오류가 발생했습니다")


@app.get("/api/feedback/detailed")
async def get_detailed_feedbacks(
    limit: int = 100,
    authorization: Optional[str] = Header(None)
):
    """상세 피드백 조회 (관리자 전용)"""
    user = get_current_user(authorization)
    
    if not user:
        raise HTTPException(status_code=401, detail="인증이 필요합니다")
    
    # 관리자 권한 확인
    if not check_permission(user, UserRole.ADMIN):
        raise AuthorizationError("관리자만 접근 가능합니다")
    
    return {"feedbacks": db.get_detailed_feedbacks(limit)}


@app.get("/api/feedback/negative")
async def get_negative_feedbacks(authorization: Optional[str] = Header(None)):
    """부정적 피드백 조회 (관리자 전용)"""
    user = get_current_user(authorization)
    
    if not user:
        raise HTTPException(status_code=401, detail="인증이 필요합니다")
    
    # 관리자 권한 확인
    if not check_permission(user, UserRole.ADMIN):
        raise AuthorizationError("관리자만 접근 가능합니다")
    
    return {"feedbacks": db.get_negative_feedbacks()}


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
            
            # 엔진 로드 (RAG 버전)
            print("🔍 시맨틱 검색 엔진 로딩 중...")
            from semantic_search import SemanticSearchEngineRAG
            semantic_engine = SemanticSearchEngineRAG()
            semantic_engine.load_index()
            print("✅ 시맨틱 검색 활성화 (RAG 모드)!")
            
        except Exception as e:
            print(f"⚠️  시맨틱 검색 로드 실패: {e}")
            print("    키워드 검색만 사용합니다.")
    else:
        print("ℹ️  시맨틱 검색 비활성화 (키워드 검색만 사용)")
    
    # LLM 서비스 초기화
    llm_service_instance = None
    try:
        from services.llm_service import llm_service
        llm_service_instance = llm_service
    except Exception as e:
        print(f"ℹ️  LLM 서비스 초기화 실패: {e}")
    
    # 답변 서비스 초기화
    answer_service = AnswerService(
        semantic_engine=semantic_engine,
        keyword_engine=search_engine,
        db=db,
        llm_service=llm_service_instance  # LLM 서비스 추가
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
