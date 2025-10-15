# 프로젝트 구조

## 디렉토리 구조

```
encar-copilot/
│
├── 📁 data/                        # 데이터 저장소
│   ├── faq_data.json              # FAQ 데이터베이스 (15개 샘플)
│   ├── users.json                 # 사용자 데이터 (테스트 계정 3개)
│   └── feedback.json              # 피드백 데이터
│
├── 📁 static/                      # 정적 파일
│   ├── 📁 css/
│   │   └── style.css              # 커스텀 스타일
│   └── 📁 js/
│       └── app.js                 # 프론트엔드 로직
│
├── 📁 templates/                   # HTML 템플릿
│   └── index.html                 # 메인 UI
│
├── 📄 main.py                      # FastAPI 메인 애플리케이션
├── 📄 models.py                    # 데이터 모델 (Pydantic)
├── 📄 database.py                  # 데이터베이스 관리
├── 📄 search_engine.py             # 질문 매칭 엔진
├── 📄 auth.py                      # 인증 시스템
├── 📄 run.py                       # 서버 실행 스크립트
│
├── 📄 requirements.txt             # Python 의존성
├── 📄 .gitignore                   # Git 무시 파일
├── 📄 .env.example                 # 환경 변수 예시
│
├── 📄 README.md                    # 프로젝트 소개
├── 📄 INSTALLATION.md              # 설치 가이드
├── 📄 USAGE_GUIDE.md               # 사용 가이드
├── 📄 CHANGELOG.md                 # 변경 이력
├── 📄 PROJECT_STRUCTURE.md         # 프로젝트 구조 (현재 문서)
└── 📄 PRD v3.0 — Encar Copilot (엔카 코파일럿).md  # 제품 요구사항 문서
```

## 파일별 설명

### 🔧 백엔드 코어 파일

#### `main.py`
- FastAPI 애플리케이션의 진입점
- 모든 API 엔드포인트 정의
- CORS, 미들웨어 설정
- 약 250줄

**주요 엔드포인트:**
- `POST /api/login` - 로그인
- `POST /api/ask` - 질문 응답
- `POST /api/feedback` - 피드백 제출
- `GET /api/questions` - FAQ 목록
- `GET /api/categories` - 카테고리 목록
- `GET /health` - 헬스 체크

#### `models.py`
- Pydantic 모델 정의
- 데이터 유효성 검증
- API 요청/응답 스키마

**주요 모델:**
- `FAQItem` - FAQ 항목
- `QuestionRequest` - 질문 요청
- `AnswerResponse` - 답변 응답
- `Feedback` - 피드백
- `User` - 사용자
- `LoginRequest/Response` - 로그인

#### `database.py`
- JSON 파일 기반 데이터베이스 관리
- CRUD 작업 처리
- 싱글톤 패턴 적용

**주요 메서드:**
- `get_all_faqs()` - 모든 FAQ 조회
- `get_faq_by_id()` - ID로 FAQ 조회
- `get_user_by_employee_id()` - 사용자 조회
- `add_feedback()` - 피드백 추가
- `get_feedback_stats()` - 통계 조회

#### `search_engine.py`
- 키워드 기반 질문 매칭 엔진
- 유사도 계산 알고리즘
- 관련 질문 추천

**주요 알고리즘:**
- 키워드 추출 (정규식 기반)
- Jaccard 유사도 (키워드 매칭)
- SequenceMatcher (텍스트 유사도)
- 가중치 조합 (70% 키워드 + 30% 텍스트)

#### `auth.py`
- 사번/이름 기반 인증
- 세션 토큰 관리
- 메모리 기반 세션 저장소

**보안 기능:**
- 세션 토큰 생성 (32바이트 URL-safe)
- 8시간 자동 만료
- 세션 유효성 검증

### 🎨 프론트엔드 파일

#### `templates/index.html`
- 메인 UI 템플릿
- Tailwind CSS 사용
- 반응형 디자인
- 약 250줄

**주요 섹션:**
- 헤더 (로고, 사용자 정보)
- 로그인 모달
- 환영 카드 (예시 질문)
- 채팅 영역
- 입력 영역
- 푸터

#### `static/js/app.js`
- 프론트엔드 로직
- API 통신 관리
- UI 상태 관리
- 약 400줄

**주요 함수:**
- `handleLogin()` - 로그인 처리
- `handleQuestion()` - 질문 제출
- `addBotMessage()` - 봇 응답 표시
- `submitFeedback()` - 피드백 전송
- `validateSession()` - 세션 검증

#### `static/css/style.css`
- 커스텀 스타일
- Encar 브랜드 컬러 정의
- 애니메이션 효과
- 스크롤바 스타일

### 📊 데이터 파일

#### `data/faq_data.json`
- FAQ 데이터베이스
- 15개 샘플 질문/답변
- 카테고리: HR, IT, 총무, 복리후생

**구조:**
```json
{
  "faqs": [
    {
      "id": 1,
      "category": "HR",
      "question": "연차는 언제 생기나요?",
      "main_answer": "...",
      "keywords": ["연차", "발생", ...],
      "department": "P&C팀",
      "link": "https://..."
    }
  ]
}
```

#### `data/users.json`
- 테스트 사용자 계정
- 3개 계정 등록

#### `data/feedback.json`
- 사용자 피드백 저장
- 통계 분석용

### 📚 문서 파일

| 파일명 | 용도 | 대상 |
|--------|------|------|
| `README.md` | 프로젝트 소개 | 개발자, 사용자 |
| `INSTALLATION.md` | 설치 가이드 | 개발자 |
| `USAGE_GUIDE.md` | 사용 가이드 | 최종 사용자 |
| `CHANGELOG.md` | 변경 이력 | 개발자, 관리자 |
| `PROJECT_STRUCTURE.md` | 구조 설명 | 개발자 |
| `PRD v3.0` | 제품 요구사항 | PM, 개발자 |

### ⚙️ 설정 파일

#### `requirements.txt`
- Python 의존성 목록
- 버전 고정

**주요 패키지:**
- `fastapi` - 웹 프레임워크
- `uvicorn` - ASGI 서버
- `pydantic` - 데이터 검증
- `passlib` - 암호화
- `python-jose` - JWT (향후 사용)

#### `.gitignore`
- Git 무시 파일 설정
- `__pycache__/`, `venv/`, `.env` 등

#### `.env.example`
- 환경 변수 템플릿
- 실제 `.env` 파일 생성 시 참고

## 데이터 흐름

```
┌─────────────┐
│   사용자    │
└──────┬──────┘
       │ 1. 질문 입력
       ↓
┌─────────────┐
│ app.js      │
│ (Frontend)  │
└──────┬──────┘
       │ 2. POST /api/ask
       ↓
┌─────────────┐
│ main.py     │
│ (FastAPI)   │
└──────┬──────┘
       │ 3. 질문 처리 요청
       ↓
┌─────────────┐
│search_engine│
│   .py       │
└──────┬──────┘
       │ 4. FAQ 검색 요청
       ↓
┌─────────────┐
│ database.py │
└──────┬──────┘
       │ 5. 데이터 조회
       ↓
┌─────────────┐
│faq_data.json│
└──────┬──────┘
       │ 6. FAQ 반환
       ↓
┌─────────────┐
│search_engine│ 7. 유사도 계산
│   .py       │    관련 질문 추천
└──────┬──────┘
       │ 8. 최적 답변 반환
       ↓
┌─────────────┐
│ main.py     │ 9. AnswerResponse 생성
└──────┬──────┘
       │ 10. JSON 응답
       ↓
┌─────────────┐
│ app.js      │ 11. UI 업데이트
└──────┬──────┘
       │ 12. 답변 표시
       ↓
┌─────────────┐
│   사용자    │
└─────────────┘
```

## 확장 계획

### v1.5 (2026 Q1)
```
추가 예정 파일:
├── admin/
│   ├── dashboard.html
│   └── faq_manager.html
└── analytics.py
```

### v2.0 (2026 Q2)
```
추가 예정:
├── ai/
│   ├── openai_service.py
│   └── embedding.py
└── config.py
```

### v3.0 (2026 Q3)
```
추가 예정:
├── integrations/
│   ├── teams_bot.py
│   └── outlook_addin.py
└── migrations/
    └── postgres/
```

## 코드 메트릭스

| 파일 | 줄 수 | 주요 기능 |
|------|-------|-----------|
| `main.py` | ~250 | API 엔드포인트 |
| `models.py` | ~90 | 데이터 모델 |
| `database.py` | ~150 | DB 관리 |
| `search_engine.py` | ~140 | 검색 엔진 |
| `auth.py` | ~120 | 인증 시스템 |
| `app.js` | ~400 | 프론트엔드 로직 |
| `index.html` | ~250 | UI 템플릿 |

**총 코드 라인:** ~1,400줄

## 성능 고려사항

### 현재 (MVP)
- **응답 시간**: 평균 0.5초 미만 (목표: 3초)
- **동시 사용자**: 최대 50명 (메모리 기반)
- **FAQ 개수**: 15개

### 확장 시
- **데이터베이스**: PostgreSQL 마이그레이션
- **캐싱**: Redis 도입
- **로드 밸런싱**: Nginx + 다중 워커

## 보안

### 현재 구현
- ✅ 사번/이름 기반 인증
- ✅ 세션 토큰 관리
- ✅ HTTPS 권장
- ✅ 익명화된 피드백

### 향후 강화
- SSO/OAuth 2.0
- RBAC (역할 기반 접근 제어)
- API Rate Limiting
- 로그 모니터링

## 기여 가이드

새로운 기능 추가 시:
1. `models.py`에 데이터 모델 정의
2. `database.py`에 CRUD 메서드 추가
3. `main.py`에 API 엔드포인트 추가
4. `app.js`에 프론트엔드 로직 추가
5. 문서 업데이트


