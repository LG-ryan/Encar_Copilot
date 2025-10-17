# PostgreSQL 마이그레이션 가이드

## 개요

현재 JSON 파일 기반 데이터 저장에서 PostgreSQL로 마이그레이션하는 가이드입니다.

## 왜 필요한가?

### 현재 문제점 (JSON 파일)
- ❌ 동시성 제어 없음 (여러 사용자가 동시에 피드백 제출 시 데이터 손실 가능)
- ❌ 트랜잭션 없음 (중간에 실패 시 불완전한 데이터 저장)
- ❌ 인덱싱 불가 (데이터가 많아지면 검색 느림)
- ❌ 백업/복구 어려움
- ❌ 복잡한 쿼리 불가

### PostgreSQL 장점
- ✅ ACID 트랜잭션 보장
- ✅ 자동 동시성 제어
- ✅ 인덱싱으로 빠른 검색
- ✅ 자동 백업 및 복구
- ✅ SQL로 복잡한 통계 쿼리 가능

## 마이그레이션 단계

### Phase 1: 로컬 환경 설정 (30분)

1. **PostgreSQL 설치**
```bash
# Windows (Chocolatey)
choco install postgresql

# Mac (Homebrew)
brew install postgresql

# Ubuntu
sudo apt install postgresql
```

2. **데이터베이스 생성**
```sql
-- psql 접속
psql -U postgres

-- 데이터베이스 생성
CREATE DATABASE encar_copilot;

-- 사용자 생성 (선택)
CREATE USER encar_user WITH PASSWORD 'your_password';
GRANT ALL PRIVILEGES ON DATABASE encar_copilot TO encar_user;
```

3. **환경변수 설정** (`.env` 파일)
```bash
DATABASE_URL=postgresql://encar_user:your_password@localhost:5432/encar_copilot
```

### Phase 2: 스키마 생성 (10분)

`database_migration/schema.sql` 파일 실행:
```bash
psql -U encar_user -d encar_copilot -f database_migration/schema.sql
```

### Phase 3: 기존 데이터 마이그레이션 (10분)

Python 스크립트로 JSON → PostgreSQL:
```bash
python database_migration/migrate_data.py
```

### Phase 4: 코드 변경 (30분)

`database.py` 파일을 PostgreSQL 버전으로 교체:
```bash
# 기존 파일 백업
cp database.py database.py.json_backup

# PostgreSQL 버전 적용
cp database_migration/database_postgres.py database.py
```

### Phase 5: 테스트 및 검증 (20분)

```bash
# 서버 재시작
python run.py

# 테스트
curl http://localhost:8000/health
curl -X POST http://localhost:8000/api/ask -H "Content-Type: application/json" -d '{"question": "테스트"}'
```

## 롤백 계획

문제 발생 시 JSON 파일로 복귀:
```bash
# 서버 중지
# Ctrl+C

# 백업 파일 복원
cp database.py.json_backup database.py

# 서버 재시작
python run.py
```

## 체크리스트

- [ ] PostgreSQL 설치 완료
- [ ] 데이터베이스 생성 완료
- [ ] `.env` 파일에 DATABASE_URL 설정
- [ ] 스키마 생성 완료
- [ ] 기존 데이터 마이그레이션 완료
- [ ] 코드 변경 완료
- [ ] 테스트 통과
- [ ] 백업 확인

## 다음 단계 (Phase 3 이후)

- Redis 캐시 통합
- 실시간 분석 대시보드
- 자동 백업 스케줄링
- 데이터베이스 모니터링

