# 🚀 엔카 코파일럿 (엔디) 배포 가이드

**제작자**: Ryan (P&C팀)  
**버전**: v2.1 (Production Ready)  
**최종 업데이트**: 2025년 10월 17일

---

## ✅ 완료된 개선 사항

### 🔐 보안 (Security)
- [x] API 키 환경변수화 (하드코딩 제거)
- [x] 개인정보 로그 마스킹 (이메일, 사번, 전화번호)
- [x] RBAC 역할 기반 접근 제어 (admin/user)
- [x] CORS 정책 강화 (특정 도메인만 허용)
- [x] 보안 헤더 추가 (XSS, Clickjacking 방어)
- [x] Content Security Policy (CSP)

### 🛡️ 안정성 (Stability)
- [x] 전역 예외 처리 (일관된 에러 응답)
- [x] 레이트리밋 (분당 10회, 시간당 100회)
- [x] 입력 검증 (질문 길이 제한 500자)
- [x] PostgreSQL 마이그레이션 준비 (스키마, 마이그레이션 스크립트)

### 📊 관찰성 (Observability)
- [x] 구조화된 로깅 (JSON 포맷, 파일 로테이션)
- [x] 헬스체크 엔드포인트 (/health, /readiness, /liveness)
- [x] Prometheus 메트릭 수집 (/metrics)

---

## 📋 배포 전 체크리스트

### 1단계: 환경 설정 (10분)

#### 1.1 `.env` 파일 생성
프로젝트 루트에 `.env` 파일을 생성하세요:

```bash
# 🔑 OpenAI API 키 (필수!)
OPENAI_API_KEY=sk-proj-your-actual-api-key-here

# 🌐 서버 설정
HOST=0.0.0.0
PORT=8000
ENVIRONMENT=production  # 중요: production으로 설정!
LOG_LEVEL=info

# 🔐 보안 설정
SECRET_KEY=your-secret-key-min-32-characters-random-string
ALLOWED_ORIGINS=https://endy.encar.com,https://encar.com

# ⚡ 레이트리밋
RATE_LIMIT_PER_MINUTE=10
RATE_LIMIT_PER_HOUR=100

# 📊 관찰성
ENABLE_METRICS=true
ENABLE_HEALTH_CHECK=true
```

**⚠️ 중요**: `.env` 파일은 Git에 커밋하지 마세요! (이미 `.gitignore`에 등록됨)

#### 1.2 OpenAI API 키 발급
1. https://platform.openai.com/api-keys 접속
2. "Create new secret key" 클릭
3. 생성된 키를 `.env` 파일에 붙여넣기

#### 1.3 SECRET_KEY 생성
```python
# Python으로 랜덤 문자열 생성
import secrets
print(secrets.token_urlsafe(32))
```

### 2단계: 의존성 설치 (5분)

```bash
# 기본 패키지 설치
pip install -r requirements.txt

# Prometheus 클라이언트 추가
pip install prometheus-client

# (선택) PostgreSQL 사용 시
pip install psycopg2-binary
```

### 3단계: 서버 실행 및 확인 (5분)

```bash
# 서버 시작
python run.py

# 다른 터미널에서 헬스체크
curl http://localhost:8000/health

# 예상 결과:
# {
#   "status": "healthy",
#   "timestamp": "2025-01-17T...",
#   "version": "2.0.0",
#   "checks": {
#     "llm_service": true,
#     "database": true,
#     "disk_space": true
#   }
# }
```

---

## 🔍 주요 기능 확인

### API 키 환경변수 확인
```bash
# 서버 로그에서 확인
# ✅ "✅ LLM 서비스 활성화 (OpenAI API)" 메시지 확인
# ❌ "⚠️  LLM 서비스 비활성화" 메시지 나오면 .env 확인
```

### 레이트리밋 테스트
```bash
# 10번 연속 요청 (분당 10회 제한)
for i in {1..11}; do
  echo "요청 $i"
  curl -X POST http://localhost:8000/api/ask \
    -H "Content-Type: application/json" \
    -d '{"question": "테스트"}' \
    -w "\nStatus: %{http_code}\n\n"
  sleep 1
done

# 11번째 요청에서 429 Too Many Requests 예상
```

### 관리자 권한 테스트
```bash
# 일반 사용자(박민수)로 로그인 후 관리자 API 호출
curl http://localhost:8000/api/feedback/detailed \
  -H "Authorization: Bearer <박민수_토큰>"

# 예상 결과: 403 Forbidden
# {
#   "error": "insufficient_permissions",
#   "message": "관리자만 접근 가능합니다"
# }
```

### 메트릭 확인
```bash
curl http://localhost:8000/metrics

# 예상 결과 (Prometheus 포맷):
# api_requests_total{method="POST",endpoint="/api/ask",status="200"} 5.0
# llm_requests_total{status="success"} 3.0
# cache_operations_total{operation="hit"} 2.0
# ...
```

---

## 🎯 프로덕션 배포

### 환경변수 설정 (프로덕션)
```bash
# 프로덕션 환경
ENVIRONMENT=production
RELOAD=false  # auto-reload 비활성화
LOG_LEVEL=warning  # 경고 이상만 로그

# 보안
SECRET_KEY=<64자 이상 랜덤 문자열>
ALLOWED_ORIGINS=https://endy.encar.com  # 프로덕션 도메인만!

# 레이트리밋 (필요시 조정)
RATE_LIMIT_PER_MINUTE=20
RATE_LIMIT_PER_HOUR=200
```

### Docker 배포 (추천)
```dockerfile
# Dockerfile
FROM python:3.11-slim

WORKDIR /app

# 의존성 설치
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# 앱 복사
COPY . .

# 비-root 사용자
RUN useradd -m -u 1000 appuser && chown -R appuser /app
USER appuser

# 헬스체크
HEALTHCHECK --interval=30s --timeout=3s --start-period=5s --retries=3 \
  CMD python -c "import requests; requests.get('http://localhost:8000/health')"

EXPOSE 8000
CMD ["python", "run.py"]
```

### Kubernetes 배포
```yaml
# kubernetes/deployment.yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: encar-copilot
spec:
  replicas: 2
  selector:
    matchLabels:
      app: encar-copilot
  template:
    metadata:
      labels:
        app: encar-copilot
    spec:
      containers:
      - name: encar-copilot
        image: encar/copilot:latest
        ports:
        - containerPort: 8000
        env:
        - name: OPENAI_API_KEY
          valueFrom:
            secretKeyRef:
              name: encar-copilot-secrets
              key: openai-api-key
        - name: ENVIRONMENT
          value: "production"
        livenessProbe:
          httpGet:
            path: /liveness
            port: 8000
          initialDelaySeconds: 10
          periodSeconds: 30
        readinessProbe:
          httpGet:
            path: /readiness
            port: 8000
          initialDelaySeconds: 5
          periodSeconds: 10
        resources:
          requests:
            memory: "512Mi"
            cpu: "500m"
          limits:
            memory: "1Gi"
            cpu: "1000m"
```

---

## 📊 모니터링 설정

### Prometheus 설정
```yaml
# prometheus.yml
scrape_configs:
  - job_name: 'encar-copilot'
    scrape_interval: 15s
    static_configs:
      - targets: ['localhost:8000']
    metrics_path: '/metrics'
```

### Grafana 대시보드
주요 지표:
- `api_requests_total`: API 요청 수
- `api_response_seconds`: 응답 시간
- `llm_requests_total`: LLM 호출 수
- `cache_operations_total`: 캐시 히트율
- `errors_total`: 에러 발생 수

---

## 🚨 알람 설정

### 필수 알람
1. **헬스체크 실패**: 3회 연속 실패 시 알람
2. **에러율 급증**: 5분간 에러율 10% 초과 시
3. **응답 시간 지연**: P95 응답 시간 10초 초과 시
4. **디스크 용량**: 남은 용량 1GB 미만 시

---

## 🔄 롤백 계획

### 문제 발생 시
1. **즉시 롤백**: 이전 버전으로 복구
2. **로그 확인**: `logs/encar_copilot.log` 분석
3. **헬스체크**: `/health` 엔드포인트 확인
4. **메트릭 확인**: Prometheus/Grafana에서 이상 징후 확인

### 롤백 명령어
```bash
# Git으로 이전 버전 복구
git checkout <previous-commit-hash>

# 서버 재시작
python run.py
```

---

## 📞 문제 해결

### Q: "⚠️  LLM 서비스 비활성화" 메시지가 나와요
A: `.env` 파일에 `OPENAI_API_KEY`가 설정되었는지 확인하세요.

### Q: "403 Forbidden" 에러가 나와요
A: 관리자 권한이 필요한 API입니다. `data/users.json`에서 사용자의 `role`을 `admin`으로 변경하세요.

### Q: "429 Too Many Requests" 에러가 나와요
A: 레이트리밋을 초과했습니다. 잠시 후 다시 시도하거나, `.env`에서 `RATE_LIMIT_PER_MINUTE`을 높이세요.

### Q: 로그 파일이 너무 커져요
A: 로그 로테이션이 자동으로 됩니다. `config/settings.py`에서 `LOG_MAX_BYTES`, `LOG_BACKUP_COUNT` 조정 가능.

---

## 🎓 추가 문서

- `ENV_SETUP.md`: 환경변수 상세 설정 가이드
- `database_migration/README.md`: PostgreSQL 마이그레이션 가이드
- `documentation/`: 전체 프로젝트 문서

---

## ✅ 최종 체크리스트

배포 전에 다음을 확인하세요:

- [ ] `.env` 파일 생성 및 API 키 설정
- [ ] `ENVIRONMENT=production` 설정
- [ ] `SECRET_KEY` 랜덤 문자열로 변경
- [ ] `ALLOWED_ORIGINS` 프로덕션 도메인으로 설정
- [ ] 헬스체크 통과 (`/health` 200 OK)
- [ ] 레이트리밋 동작 확인
- [ ] 관리자 권한 테스트
- [ ] 로그 파일 확인 (`logs/encar_copilot.log`)
- [ ] 메트릭 수집 확인 (`/metrics`)
- [ ] 백업 계획 수립

---

**🎉 모든 준비가 완료되었습니다! 안전한 배포 되세요!**

