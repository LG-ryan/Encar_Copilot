# 환경변수 설정 가이드

## 1. `.env` 파일 생성

프로젝트 루트 디렉토리에 `.env` 파일을 생성하고 아래 내용을 복사하세요.

```bash
# 🔑 OpenAI API 키 (필수)
OPENAI_API_KEY=sk-proj-your-actual-api-key-here

# 🌐 서버 설정
HOST=0.0.0.0
PORT=8000
ENVIRONMENT=development
LOG_LEVEL=info

# 🔐 보안 설정
SECRET_KEY=encar-copilot-secret-key-change-in-production
ALLOWED_ORIGINS=http://localhost:8000,https://encar.com

# ⚡ 레이트리밋 설정
RATE_LIMIT_PER_MINUTE=10
RATE_LIMIT_PER_HOUR=100

# 📊 관찰성 설정
ENABLE_METRICS=true
ENABLE_HEALTH_CHECK=true
```

## 2. OpenAI API 키 발급

1. https://platform.openai.com/api-keys 접속
2. "Create new secret key" 클릭
3. 키 이름 입력 (예: `Encar Copilot`)
4. 생성된 키를 복사하여 `.env` 파일의 `OPENAI_API_KEY`에 붙여넣기

⚠️ **주의**: API 키는 절대 Git에 커밋하지 마세요! `.gitignore`에 이미 `.env`가 등록되어 있습니다.

## 3. 환경별 설정

### Development (개발)
```bash
ENVIRONMENT=development
RELOAD=true
LOG_LEVEL=debug
```

### Production (운영)
```bash
ENVIRONMENT=production
RELOAD=false
LOG_LEVEL=info
SECRET_KEY=complex-random-string-min-32-characters
ALLOWED_ORIGINS=https://endy.encar.com
```

## 4. 서버 실행

```bash
python run.py
```

## 5. 확인

서버 시작 시 다음 메시지가 표시되어야 합니다:
```
✅ LLM 서비스 활성화 (OpenAI API)
```

만약 다음 메시지가 표시되면 `.env` 파일을 확인하세요:
```
⚠️  LLM 서비스 비활성화 (OPENAI_API_KEY 미설정)
```

