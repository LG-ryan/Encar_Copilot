# Encar Copilot - 엔디(Endy) 설치 가이드

> "Encar의 든든한 Buddy"로서 여러분을 도와드릴 준비를 해볼까요?

## 사전 요구사항

- Python 3.11 이상
- pip (Python 패키지 관리자)

## 설치 단계

### 1. Python 버전 확인

```bash
python --version
```

Python 3.11 이상이 설치되어 있어야 합니다.

### 2. 가상 환경 생성 (권장)

```bash
# Windows
python -m venv venv
venv\Scripts\activate

# macOS/Linux
python3 -m venv venv
source venv/bin/activate
```

### 3. 의존성 설치

```bash
pip install -r requirements.txt
```

### 4. 데이터 확인

`data/` 폴더에 다음 파일들이 있는지 확인:
- `faq_data.json` - FAQ 데이터
- `users.json` - 사용자 데이터
- `feedback.json` - 피드백 데이터

### 5. 서버 실행

#### 방법 1: run.py 사용 (권장)

```bash
python run.py
```

#### 방법 2: uvicorn 직접 실행

```bash
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

### 6. 브라우저 접속

서버가 실행되면 다음 주소로 접속:

- **메인 페이지**: http://localhost:8000
- **API 문서**: http://localhost:8000/docs
- **대체 API 문서**: http://localhost:8000/redoc

## 테스트 계정

```
사번: 2024001
이름: 김철수
```

```
사번: 2024002
이름: 이영희
```

```
사번: 2024003
이름: 박민수
```

## 문제 해결

### 1. 포트가 이미 사용 중인 경우

다른 포트로 실행:

```bash
uvicorn main:app --reload --host 0.0.0.0 --port 8080
```

### 2. 의존성 설치 오류

pip 업그레이드 후 재시도:

```bash
python -m pip install --upgrade pip
pip install -r requirements.txt
```

### 3. KoNLPy 설치 오류 (Windows)

KoNLPy는 선택사항입니다. 설치가 어려운 경우 `requirements.txt`에서 주석 처리:

```txt
# konlpy==0.6.0
```

현재 MVP는 KoNLPy 없이도 작동합니다.

## 개발 모드

개발 중에는 코드 변경 시 자동으로 서버가 재시작됩니다 (`--reload` 옵션).

## 배포 준비

실제 배포 시에는:

1. `.env` 파일 생성 (`.env.example` 참고)
2. `SECRET_KEY` 변경
3. CORS 설정 수정 (`main.py`)
4. HTTPS 설정
5. 프로덕션 ASGI 서버 사용 (Gunicorn + Uvicorn)

```bash
gunicorn main:app -w 4 -k uvicorn.workers.UvicornWorker
```

## 추가 도구

### API 테스트

FastAPI는 자동으로 Swagger UI를 제공합니다:
- http://localhost:8000/docs

여기서 모든 API를 직접 테스트할 수 있습니다.

### 로그 확인

서버 실행 시 콘솔에 로그가 출력됩니다.

## 지원

문제가 발생하면 P&C팀의 Ryan에게 문의하세요.

