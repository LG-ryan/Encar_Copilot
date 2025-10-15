# Encar Copilot - 엔디(Endy) 🚗💬

> 전사 구성원이 회사 관련 정보를 쉽고 빠르게 찾을 수 있도록 지원하는 사내 지식 어시스턴트

[![Python](https://img.shields.io/badge/Python-3.11+-blue.svg)](https://www.python.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.104+-green.svg)](https://fastapi.tiangolo.com/)
[![License](https://img.shields.io/badge/License-Internal-red.svg)](LICENSE)
[![Status](https://img.shields.io/badge/Status-v2.0-brightgreen.svg)](CHANGELOG.md)

---

## 📁 프로젝트 구조 (v2.0 리팩토링)

```
Encar Copilot/
├── 📂 config/              # 설정 관리 ⭐ NEW
│   ├── __init__.py
│   └── settings.py         # 중앙화된 설정
│
├── 📂 services/            # 비즈니스 로직 ⭐ NEW
│   ├── __init__.py
│   └── answer_service.py   # 답변 처리 서비스
│
├── 📂 data/                # 데이터 파일
│   ├── faq_data.json       # FAQ 데이터
│   ├── users.json          # 사용자 정보
│   ├── feedback.json       # 피드백 로그
│   └── semantic_index/     # 시맨틱 인덱스 (자동 생성)
│
├── 📂 docs/                # 문서 및 가이드
│   ├── images/             # 가이드 이미지
│   └── 엔카생활가이드.md    # 메인 가이드 (H3 단위 청킹)
│
├── 📂 static/              # 정적 파일
│   ├── css/style.css       # 스타일시트
│   └── js/app.js           # JavaScript
│
├── 📂 templates/           # HTML 템플릿
│   └── index.html          # 메인 페이지
│
├── 📂 archives/            # 백업 파일
│   ├── 엔카생활가이드_backup_final.md
│   └── 엔카생활가이드.pdf
│
├── 📂 documentation/       # 프로젝트 문서
│   ├── 🚀_START_HERE.md
│   ├── INSTALLATION.md
│   ├── QUICK_START.md
│   ├── USAGE_GUIDE.md
│   ├── SEMANTIC_SEARCH_GUIDE.md
│   ├── CHANGELOG.md
│   ├── DEPLOYMENT_CHECKLIST.md
│   └── PROJECT_STRUCTURE.md
│
├── 🐍 main.py              # FastAPI 메인 서버 (간소화)
├── 🔍 semantic_search.py   # 시맨틱 검색 엔진
├── 🗄️ database.py          # 데이터베이스 관리
├── 🔐 auth.py              # 인증 관리
├── 🔎 search_engine.py     # 키워드 검색 엔진
├── 📦 models.py            # 데이터 모델
├── 🚀 run.py               # 서버 실행 스크립트
├── 📋 requirements.txt     # 패키지 의존성 (정리됨)
├── 📋 requirements_semantic.txt  # 시맨틱 검색 의존성
├── .env.example            # 환경 변수 템플릿 ⭐ NEW
├── .gitignore              # Git 무시 파일
└── 📖 README.md            # 프로젝트 설명
```

---

## 🌟 특징 (v2.0 리팩토링 완료!)

### ⚡ v2.0 아키텍처 개선
- **📦 서비스 계층 도입**: 비즈니스 로직 분리로 테스트 가능성 ↑
- **⚙️ 중앙화된 설정**: `config/settings.py`로 환경 변수 관리
- **🎯 코드 간소화**: `main.py` 60% 감소 (653 → 264 라인)
- **🧹 불필요한 파일 정리**: 일회성 스크립트 제거
- **🔧 의존성 최적화**: 미사용 라이브러리 제거

### 🚀 v1.0 핵심 기능 (유지)
- **시맨틱 검색**: 자연어 이해 (GPT-like)
- **H3 단위 청킹**: 정확한 정보 검색
- **하이브리드 검색**: 시맨틱 + 키워드 결합
- **마인드맵 모드**: 여러 관련 섹션 제공
- **자동 인덱싱**: MD 파일 변경 시 자동 재생성

---

## 🚀 빠른 시작

### 1. 패키지 설치

```bash
# 기본 패키지
pip install -r requirements.txt

# 시맨틱 검색 (필수)
pip install -r requirements_semantic.txt
```

### 2. 환경 설정 (선택사항)

```bash
# .env 파일 생성
cp .env.example .env

# 필요 시 설정 수정
# PORT, SEMANTIC_THRESHOLD 등
```

### 3. 서버 실행

```bash
python run.py
```

또는

```bash
python main.py
```

### 4. 브라우저에서 접속

```
http://localhost:8000
```

---

## 🔍 시맨틱 검색 엔진

### 특징
- **100% 무료**: Sentence Transformers (오픈소스)
- **로컬 실행**: 개인정보 보호, API 비용 없음
- **한국어 최적화**: jhgan/ko-sroberta-multitask 모델

### 검색 방식
```
사용자 질문: "휴가는 언제 생겨?"
          ↓ 임베딩 변환
          ↓ 유사도 계산 (FAISS)
매칭: "연차는 언제 생기나요?" (0.85 유사도)
```

### 인덱스 관리
- **자동 생성**: 서버 시작 시 MD 파일 변경 감지
- **H3 청킹**: 194개 독립 섹션으로 분리
- **수동 재생성**: 불필요 (자동화됨)

---

## 📊 v2.0 개선 사항

### 코드 품질
| 항목 | Before | After | 개선율 |
|------|--------|-------|--------|
| `main.py` 라인 수 | 653 | 264 | **60% ↓** |
| 불필요한 파일 | 18개 | 0개 | **100% 제거** |
| 의존성 라이브러리 | 15개 | 10개 | **33% ↓** |
| 테스트 가능성 | ❌ | ✅ | **개선** |

### 아키텍처
```
Before (Monolithic):
main.py (653 lines)
├── 인증 로직
├── 검색 로직
├── 답변 구성 로직  ← 복잡하고 중복
├── FAQ 관리
└── 설정 (하드코딩)

After (Layered):
main.py (264 lines)  ← 간결!
├── 라우트만
└── 서비스 호출

services/answer_service.py
├── 시맨틱 검색
├── 답변 구성  ← 재사용 가능, 테스트 가능
└── 카테고리 매핑

config/settings.py
└── 중앙화된 설정  ← .env 지원
```

---

## 🛠️ 개발 가이드

### 설정 변경
```python
# config/settings.py 또는 .env 파일

# 검색 임계값 조정
SEMANTIC_THRESHOLD_MD=0.25
SEMANTIC_THRESHOLD_FAQ=0.15

# 서버 설정
PORT=8000
RELOAD=True
```

### 새로운 기능 추가
```python
# services/your_service.py 생성
class YourService:
    def process(self):
        pass

# main.py에서 사용
from services import YourService
your_service = YourService()
```

### MD 파일 업데이트
1. `docs/엔카생활가이드.md` 수정
2. 서버 재시작 → 자동 인덱스 재생성
3. 완료!

---

## 📚 문서

- [🚀 시작 가이드](documentation/🚀_START_HERE.md)
- [📦 설치 가이드](documentation/INSTALLATION.md)
- [📖 사용 가이드](documentation/USAGE_GUIDE.md)
- [🔍 시맨틱 검색 가이드](documentation/SEMANTIC_SEARCH_GUIDE.md)
- [📝 변경 이력](documentation/CHANGELOG.md)
- [🚀 배포 체크리스트](documentation/DEPLOYMENT_CHECKLIST.md)

---

## 🤝 기여 가이드

### 커밋 메시지 컨벤션
```
feat: 새로운 기능
fix: 버그 수정
refactor: 리팩토링
docs: 문서 수정
style: 코드 스타일 변경
test: 테스트 추가
chore: 빌드/설정 변경
```

### 브랜치 전략
```
master - 운영 버전
develop - 개발 버전
feature/* - 기능 개발
hotfix/* - 긴급 수정
```

---

## 📝 라이선스

Internal Use Only - Encar Corporation

---

## 👥 팀

- **Product Owner**: 엔카 HR팀
- **Developer**: AI Dev Team
- **Version**: 2.0 (Refactored)
- **Last Updated**: 2024-10-15

---

## 🔄 버전 히스토리

### v2.0 (2024-10-15) - 🎉 Major Refactoring
- ⚡ 서비스 계층 도입
- ⚙️ 설정 파일 분리
- 🧹 코드 정리 및 최적화
- 📦 의존성 정리

### v1.0 (2024-09) - Initial Release
- 🚀 시맨틱 검색 도입
- 🎨 UX/UI 개선
- 📄 MD 파일 구조화

---

**Made with ❤️ by Encar AI Team**
