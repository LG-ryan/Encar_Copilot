# Encar Copilot - 엔디(Endy) 🚗💬

> 전사 구성원이 회사 관련 정보를 쉽고 빠르게 찾을 수 있도록 지원하는 사내 지식 어시스턴트

[![Python](https://img.shields.io/badge/Python-3.11+-blue.svg)](https://www.python.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.104+-green.svg)](https://fastapi.tiangolo.com/)
[![License](https://img.shields.io/badge/License-Internal-red.svg)](LICENSE)
[![Status](https://img.shields.io/badge/Status-MVP-orange.svg)](CHANGELOG.md)

---


## 📁 프로젝트 구조

```
Encar Copilot/
├── 📂 data/              # 데이터 파일
│   ├── faq_data.json     # FAQ 데이터
│   ├── users.json        # 사용자 정보
│   └── feedback.json     # 피드백 로그
│
├── 📂 docs/              # 문서 및 가이드
│   └── 엔카생활가이드.md  # 메인 가이드
│
├── 📂 static/            # 정적 파일
│   ├── css/             # 스타일시트
│   └── js/              # JavaScript
│
├── 📂 templates/         # HTML 템플릿
│   └── index.html       # 메인 페이지
│
├── 📂 tools/             # 유틸리티 도구
│   └── *.py             # 각종 도구 스크립트
│
├── 📂 scripts/           # 자동화 스크립트
│   └── *.py, *.bat      # 실행 스크립트
│
├── 📂 archives/          # 백업 파일
│   └── 백업 및 임시 파일
│
├── 📂 documentation/     # 프로젝트 문서
│   └── *.md             # 마크다운 문서
│
├── 🐍 main.py           # FastAPI 메인 서버
├── 🔍 semantic_search.py # 시맨틱 검색 엔진
├── 🗄️ database.py       # 데이터베이스 관리
├── 🔐 auth.py           # 인증 관리
├── 🔎 search_engine.py  # 검색 엔진
├── 📦 models.py         # 데이터 모델
├── 🚀 run.py            # 서버 실행 스크립트
├── 📋 requirements.txt  # 패키지 의존성
└── 📖 README.md         # 프로젝트 설명
```

---


## 🌟 특징 (v3.0 완전 개편!)

### 🚀 NEW! v3.0 시맨틱 검색 (GPT-like)
- 🧠 **자연어 이해**: "휴가가 언제 생겨?" → "연차는 입사일로부터..." ✅
- 🎯 **의미 기반 검색**: 키워드 없이도 의도 파악
- 📚 **전체 문서 검색**: FAQ + 엔카생활가이드 + 추가 MD 파일
- 🔄 **하이브리드 검색**: 시맨틱 → 키워드 자동 폴백
- 💯 **무료 & 로컬**: 외부 API 없이 100% 로컬 처리
- ⚡ **빠른 속도**: 1-2초 내 답변 (벡터 DB 최적화)

### 핵심 기능
- ⚡ **빠른 응답**: 평균 1-2초 이내 답변
- 🎯 **높은 정확도**: 시맨틱 검색으로 90% 이상 정확도
- 🤖 **대화형 UI**: 친근하고 자연스러운 대화 경험
- 📊 **피드백 시스템**: 사용자 피드백으로 지속적 개선
- 💡 **관련 질문 추천**: AI가 추천하는 유사 질문
- 🔒 **보안**: 인증된 사용자만 접근 가능
- 📱 **반응형**: 모바일, 태블릿, 데스크탑 모두 지원

### 🎉 v2.0 UX 개선사항
- ⌨️ **타이핑 효과**: 답변이 타자기처럼 한 글자씩 표시
- 🔍 **자동완성**: 입력 중 관련 질문 추천 (키보드 네비게이션 지원)
- 📜 **질문 히스토리**: 최근 10개 질문 자동 저장 및 빠른 재검색
- 🤝 **답변 공유**: 동료와 정보 쉽게 공유 (모바일 최적화)
- 💬 **상세 피드백**: 부정 피드백 시 구체적 이유 수집
- 🏷️ **카테고리 필터**: 원하는 분야만 집중 검색 (HR/IT/총무/복리후생)
- ✨ **부드러운 애니메이션**: 슬라이드 + 바운스 효과
- 📚 **FAQ 대폭 확장**: 15개 → 20개 (엔카생활가이드 기반)

---

## 프로젝트 개요

**Encar Copilot - 엔디(Endy)**는 "Encar의 든든한 Buddy"라는 의미를 담아, HR, IT, 총무, 경영지원 등 여러 부서에 흩어져 있는 정보를 통합하여 제공하는 사내 지식 어시스턴트입니다. 직원들이 '누구에게 물어봐야 할지 모르는 시간'을 줄이고 3초 내로 정확한 답변과 관련 문서를 안내받을 수 있게 합니다.

## 주요 기능

- ✅ **시맨틱 검색 엔진**: 의미 기반 자연어 이해 (GPT-like)
- ✅ **통합 문서 데이터베이스**: FAQ + 엔카생활가이드 + 추가 MD 파일
- ✅ **대화형 인터페이스**: 따뜻하고 자연스러운 대화체 응답
- ✅ **피드백 시스템**: 사용자 피드백을 통한 지속적 개선
- ✅ **관련 질문 추천**: 유사 질문 자동 추천 (시맨틱 기반)
- ✅ **간단한 인증**: 사번/이름 기반 접근 제어
- ✅ **무료 & 로컬**: 외부 API 없이 완전 로컬 처리

## 기술 스택

- **Backend**: FastAPI (Python 3.11+), Uvicorn
- **Frontend**: HTML5, Tailwind CSS, Vanilla JavaScript
- **Database**: JSON (MVP) → Google Sheets → PostgreSQL (확장 시)
- **Search Engine**: 
  - Sentence Transformers (한국어 모델: `jhgan/ko-sroberta-multitask`)
  - FAISS (벡터 유사도 검색)
  - Fallback: 키워드 기반 검색
- **Integration**: Microsoft Teams API (예정)

## 🚀 빠른 시작

### 1. 기본 의존성 설치

```bash
pip install -r requirements.txt
```

### 2. 🧠 시맨틱 검색 설정 (v3.0 NEW!)

**방법 A: 배치 파일 (Windows, 권장)**
```bash
install_semantic.bat    # 패키지 설치
build_index.bat         # 인덱스 구축
```

**방법 B: 직접 실행**
```bash
pip install sentence-transformers faiss-cpu
python semantic_search.py
```

**⏱️ 소요 시간**: 최초 3-5분 (모델 다운로드 + 인덱스 구축)  
**⚠️ 참고**: 시맨틱 검색 없이도 실행 가능 (키워드 검색으로 동작)

### 3. 서버 실행

```bash
python run.py
```

또는

```bash
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

### 4. 브라우저 접속

- **메인**: http://localhost:8000
- **API 문서**: http://localhost:8000/docs

### 5. 로그인

테스트 계정:
- 사번: `2024001`
- 이름: `김철수`

자세한 내용은 [빠른 시작 가이드](QUICK_START.md) 및 [시맨틱 검색 가이드](SEMANTIC_SEARCH_GUIDE.md)를 참고하세요.

## 프로젝트 구조

```
encar-copilot/
├── main.py                   # FastAPI 메인 애플리케이션
├── models.py                # 데이터 모델
├── database.py              # 데이터베이스 관리
├── search_engine.py         # 키워드 기반 검색 (폴백)
├── semantic_search.py       # 🆕 시맨틱 검색 엔진 (v3.0)
├── auth.py                  # 인증 시스템
├── data/
│   ├── faq_data.json       # FAQ 데이터베이스
│   ├── users.json          # 사용자 데이터 (MVP)
│   └── semantic_index/     # 🆕 벡터 인덱스 (생성 후)
├── docs/
│   └── 엔카생활가이드.md   # 🆕 전체 문서 (PDF 변환)
├── static/
│   ├── css/
│   │   └── style.css       # 커스텀 스타일
│   └── js/
│       └── app.js          # 프론트엔드 로직
├── templates/
│   └── index.html          # 메인 UI
├── requirements.txt         # Python 의존성
├── install_semantic.bat     # 🆕 시맨틱 검색 설치
├── build_index.bat          # 🆕 인덱스 구축
└── README.md               # 프로젝트 문서
```

## API 엔드포인트

### 인증
- `POST /api/login` - 로그인
- `POST /api/logout` - 로그아웃

### 질문 응답
- `POST /api/ask` - 질문 제출 및 답변 받기
- `GET /api/questions` - 모든 FAQ 목록 조회
- `GET /api/categories` - 카테고리 목록 조회

### 피드백
- `POST /api/feedback` - 피드백 제출

## 성공 지표 (KPI)

- 평균 응답 시간: 3초 이하
- 답변 정확도(Top-1): 85% 이상
- 피드백 긍정률: 80% 이상
- 주간 이용자 수: 100명 이상
- HR/IT 문의 감소율: 30% 이상

## 로드맵

- **v1.0 (MVP)** — 2025 Q4: HR/IT/총무 주요 FAQ 통합, Teams 봇 배포
- **v1.5** — 2026 Q1: FAQ 관리 페이지 + 피드백 통계
- **v2.0** — 2026 Q2: OpenAI 기반 자연어 검색, 의미 유사도 기반 응답
- **v3.0** — 2026 Q3: Outlook Add-in 통합 및 다국어 지원

## 보안

- HTTPS 통신
- 인증된 사용자만 접근 가능
- 질문 로그 익명화
- 비밀번호 암호화 (bcrypt)

## 📖 문서

### 소개 & 시작하기
- [👋 엔디 소개](ABOUT_ENDY.md) - 엔디(Endy)가 누구인지 알아보세요
- [⚡ 빠른 시작 가이드](QUICK_START.md) - 5분 만에 시작하기
- [🔧 설치 가이드](INSTALLATION.md) - 상세 설치 방법
- [📚 사용 가이드](USAGE_GUIDE.md) - 기능별 사용법
- [🧠 **시맨틱 검색 가이드 (v3.0 NEW!)**](SEMANTIC_SEARCH_GUIDE.md) - GPT-like 자연어 이해 ⭐

### 개발 & 운영
- [🏗️ 프로젝트 구조](PROJECT_STRUCTURE.md) - 코드 구조 설명
- [📝 변경 이력](CHANGELOG.md) - 버전별 변경사항

### 기획 & 개선
- [📋 PRD 문서](PRD%20v3.0%20—%20Encar%20Copilot%20(엔카%20코파일럿).md) - 제품 요구사항
- [🔍 QA 리뷰](QA_REVIEW_AND_UX_IMPROVEMENTS.md) - 코드 리뷰 및 UX 개선 제안
- [🎨 UX 개선사항 v2.0](UX_IMPROVEMENTS_V2.md) - UX 개선 상세 (2025-10-14)
- [🚀 시맨틱 검색 개선 계획](SEMANTIC_SEARCH_PLAN.md) - FAQ vs GPT 비교 및 개선 전략

## 🎯 다음 단계

### 사용자
1. [빠른 시작 가이드](QUICK_START.md)로 시작하기
2. 다양한 질문 시도해보기
3. 피드백 제공하기

### 개발자
1. [프로젝트 구조](PROJECT_STRUCTURE.md) 이해하기
2. API 엔드포인트 확인하기
3. 새로운 FAQ 추가하기

### 관리자
1. 피드백 통계 확인하기
2. FAQ 데이터 업데이트하기
3. 사용자 계정 관리하기

## 🤝 기여

이 프로젝트는 Encar 내부 프로젝트입니다. 개선 아이디어나 버그 제보는:
- P&C팀 Ryan에게 연락
- 피드백 기능 활용

## 📝 라이선스

Internal Use Only - Encar Corporation

## 👥 작성자

- **Ryan (P&C팀)** - 프로젝트 리드 및 개발
- 작성일: 2025-10-14
- 검토자: BMAD Orchestrator

## 📞 문의

질문이나 지원이 필요하신가요?
- P&C팀 Ryan
- 이메일: ryan@encar.com (예시)
- 내선: 1234 (예시)

---

**Made with ❤️ by Encar P&C Team**

