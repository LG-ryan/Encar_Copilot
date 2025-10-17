-- Encar Copilot PostgreSQL 스키마
-- 버전: 1.0
-- 생성일: 2025-01-17

-- 사용자 테이블
CREATE TABLE IF NOT EXISTS users (
    id SERIAL PRIMARY KEY,
    employee_id VARCHAR(50) UNIQUE NOT NULL,
    name VARCHAR(100) NOT NULL,
    department VARCHAR(100),
    email VARCHAR(255) UNIQUE,
    role VARCHAR(20) DEFAULT 'user' CHECK (role IN ('admin', 'user')),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 사용자 인덱스
CREATE INDEX idx_users_employee_id ON users(employee_id);
CREATE INDEX idx_users_email ON users(email);
CREATE INDEX idx_users_role ON users(role);

-- 세션 테이블
CREATE TABLE IF NOT EXISTS sessions (
    id SERIAL PRIMARY KEY,
    user_id INTEGER REFERENCES users(id) ON DELETE CASCADE,
    token VARCHAR(255) UNIQUE NOT NULL,
    expires_at TIMESTAMP NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 세션 인덱스
CREATE INDEX idx_sessions_token ON sessions(token);
CREATE INDEX idx_sessions_expires_at ON sessions(expires_at);

-- FAQ 테이블
CREATE TABLE IF NOT EXISTS faqs (
    id SERIAL PRIMARY KEY,
    category VARCHAR(100) NOT NULL,
    question TEXT NOT NULL,
    main_answer TEXT NOT NULL,
    keywords TEXT[],  -- 배열 타입
    department VARCHAR(100),
    link TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- FAQ 인덱스
CREATE INDEX idx_faqs_category ON faqs(category);
CREATE INDEX idx_faqs_keywords ON faqs USING GIN(keywords);  -- 배열 검색용

-- 피드백 테이블
CREATE TABLE IF NOT EXISTS feedbacks (
    id SERIAL PRIMARY KEY,
    user_id INTEGER REFERENCES users(id) ON DELETE SET NULL,
    question_id INTEGER,
    user_question TEXT NOT NULL,
    is_helpful BOOLEAN NOT NULL,
    comment TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 피드백 인덱스
CREATE INDEX idx_feedbacks_user_id ON feedbacks(user_id);
CREATE INDEX idx_feedbacks_is_helpful ON feedbacks(is_helpful);
CREATE INDEX idx_feedbacks_created_at ON feedbacks(created_at DESC);

-- 상세 피드백 테이블
CREATE TABLE IF NOT EXISTS detailed_feedbacks (
    id SERIAL PRIMARY KEY,
    user_id INTEGER REFERENCES users(id) ON DELETE SET NULL,
    question_id INTEGER,
    user_question TEXT NOT NULL,
    is_helpful BOOLEAN DEFAULT FALSE,
    reasons TEXT[],  -- 배열: ["정확하지 않음", "도움이 안됨"]
    comment TEXT,
    matched_section VARCHAR(255),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 상세 피드백 인덱스
CREATE INDEX idx_detailed_feedbacks_user_id ON detailed_feedbacks(user_id);
CREATE INDEX idx_detailed_feedbacks_created_at ON detailed_feedbacks(created_at DESC);
CREATE INDEX idx_detailed_feedbacks_reasons ON detailed_feedbacks USING GIN(reasons);

-- API 요청 로그 테이블 (선택 사항)
CREATE TABLE IF NOT EXISTS api_logs (
    id SERIAL PRIMARY KEY,
    user_id INTEGER REFERENCES users(id) ON DELETE SET NULL,
    method VARCHAR(10) NOT NULL,
    path VARCHAR(255) NOT NULL,
    status_code INTEGER,
    duration_ms FLOAT,
    ip_address INET,
    user_agent TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- API 로그 인덱스
CREATE INDEX idx_api_logs_created_at ON api_logs(created_at DESC);
CREATE INDEX idx_api_logs_user_id ON api_logs(user_id);
CREATE INDEX idx_api_logs_status_code ON api_logs(status_code);

-- 통계 뷰 (자주 사용하는 집계 쿼리)
CREATE OR REPLACE VIEW feedback_stats AS
SELECT
    COUNT(*) as total_feedbacks,
    SUM(CASE WHEN is_helpful THEN 1 ELSE 0 END) as helpful_count,
    SUM(CASE WHEN NOT is_helpful THEN 1 ELSE 0 END) as not_helpful_count,
    ROUND(
        100.0 * SUM(CASE WHEN is_helpful THEN 1 ELSE 0 END) / COUNT(*),
        2
    ) as helpful_percentage
FROM feedbacks;

-- 일별 사용 통계 뷰
CREATE OR REPLACE VIEW daily_usage_stats AS
SELECT
    DATE(created_at) as date,
    COUNT(*) as question_count,
    COUNT(DISTINCT user_id) as unique_users
FROM api_logs
WHERE path = '/api/ask'
GROUP BY DATE(created_at)
ORDER BY date DESC;

-- 초기 데이터: 테스트 사용자
INSERT INTO users (employee_id, name, department, email, role) VALUES
('2024001', '김철수', '개발팀', 'kim@encar.com', 'admin'),
('2024002', '이영희', 'P&C팀', 'lee@encar.com', 'admin'),
('2024003', '박민수', 'IT팀', 'park@encar.com', 'user')
ON CONFLICT (employee_id) DO NOTHING;

-- 업데이트 트리거 (updated_at 자동 갱신)
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER update_users_updated_at
BEFORE UPDATE ON users
FOR EACH ROW
EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_faqs_updated_at
BEFORE UPDATE ON faqs
FOR EACH ROW
EXECUTE FUNCTION update_updated_at_column();

-- 완료 메시지
DO $$
BEGIN
    RAISE NOTICE '✅ Encar Copilot 데이터베이스 스키마 생성 완료!';
    RAISE NOTICE '📊 테이블: users, sessions, faqs, feedbacks, detailed_feedbacks, api_logs';
    RAISE NOTICE '👤 테스트 사용자 3명 생성됨';
END $$;

