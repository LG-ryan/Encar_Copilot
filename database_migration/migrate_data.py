"""
JSON 파일 데이터를 PostgreSQL로 마이그레이션
"""
import json
import psycopg2
from psycopg2.extras import execute_values
from pathlib import Path
from datetime import datetime


def load_json(file_path: str) -> dict:
    """JSON 파일 로드"""
    path = Path(file_path)
    if not path.exists():
        print(f"⚠️  파일 없음: {file_path}")
        return {}
    
    with open(path, 'r', encoding='utf-8') as f:
        return json.load(f)


def migrate_users(conn, users_data: list):
    """사용자 데이터 마이그레이션"""
    if not users_data:
        print("⚠️  사용자 데이터 없음")
        return
    
    cursor = conn.cursor()
    
    # 기존 사용자 삭제 (초기화)
    cursor.execute("DELETE FROM users WHERE employee_id NOT IN ('2024001', '2024002', '2024003')")
    
    # 사용자 삽입
    values = [
        (
            user.get('employee_id'),
            user.get('name'),
            user.get('department'),
            user.get('email'),
            user.get('role', 'user'),
            user.get('created_at', datetime.now().isoformat())
        )
        for user in users_data
    ]
    
    execute_values(
        cursor,
        """
        INSERT INTO users (employee_id, name, department, email, role, created_at)
        VALUES %s
        ON CONFLICT (employee_id) DO UPDATE SET
            name = EXCLUDED.name,
            department = EXCLUDED.department,
            email = EXCLUDED.email,
            role = EXCLUDED.role
        """,
        values
    )
    
    conn.commit()
    print(f"✅ 사용자 {len(values)}명 마이그레이션 완료")


def migrate_faqs(conn, faqs_data: list):
    """FAQ 데이터 마이그레이션"""
    if not faqs_data:
        print("⚠️  FAQ 데이터 없음")
        return
    
    cursor = conn.cursor()
    
    # 기존 FAQ 삭제
    cursor.execute("DELETE FROM faqs")
    
    # FAQ 삽입
    values = [
        (
            faq.get('category'),
            faq.get('question'),
            faq.get('main_answer'),
            faq.get('keywords', []),
            faq.get('department'),
            faq.get('link'),
            faq.get('created_at', datetime.now().isoformat())
        )
        for faq in faqs_data
    ]
    
    execute_values(
        cursor,
        """
        INSERT INTO faqs (category, question, main_answer, keywords, department, link, created_at)
        VALUES %s
        """,
        values
    )
    
    conn.commit()
    print(f"✅ FAQ {len(values)}개 마이그레이션 완료")


def migrate_feedbacks(conn, feedback_data: dict):
    """피드백 데이터 마이그레이션"""
    feedbacks = feedback_data.get('feedbacks', [])
    detailed_feedbacks = feedback_data.get('detailed_feedbacks', [])
    
    cursor = conn.cursor()
    
    # 일반 피드백
    if feedbacks:
        cursor.execute("DELETE FROM feedbacks")
        
        values = [
            (
                None,  # user_id는 나중에 연결
                fb.get('question_id'),
                fb.get('user_question'),
                fb.get('is_helpful'),
                fb.get('comment'),
                fb.get('timestamp', datetime.now().isoformat())
            )
            for fb in feedbacks
        ]
        
        execute_values(
            cursor,
            """
            INSERT INTO feedbacks (user_id, question_id, user_question, is_helpful, comment, created_at)
            VALUES %s
            """,
            values
        )
        
        print(f"✅ 일반 피드백 {len(values)}개 마이그레이션 완료")
    
    # 상세 피드백
    if detailed_feedbacks:
        cursor.execute("DELETE FROM detailed_feedbacks")
        
        values = [
            (
                None,  # user_id는 나중에 연결
                fb.get('question_id'),
                fb.get('user_question'),
                fb.get('is_helpful', False),
                fb.get('reasons', []),
                fb.get('comment'),
                fb.get('matched_section'),
                fb.get('timestamp', datetime.now().isoformat())
            )
            for fb in detailed_feedbacks
        ]
        
        execute_values(
            cursor,
            """
            INSERT INTO detailed_feedbacks (user_id, question_id, user_question, is_helpful, reasons, comment, matched_section, created_at)
            VALUES %s
            """,
            values
        )
        
        print(f"✅ 상세 피드백 {len(values)}개 마이그레이션 완료")
    
    conn.commit()


def main():
    """메인 마이그레이션 함수"""
    print("=" * 60)
    print("🔄 Encar Copilot 데이터 마이그레이션 시작")
    print("=" * 60)
    
    # 환경변수에서 DATABASE_URL 로드
    import os
    database_url = os.getenv('DATABASE_URL')
    
    if not database_url:
        print("❌ DATABASE_URL 환경변수가 설정되지 않았습니다")
        print("   .env 파일에 다음을 추가하세요:")
        print("   DATABASE_URL=postgresql://user:password@localhost:5432/encar_copilot")
        return
    
    try:
        # PostgreSQL 연결
        print(f"\n📡 PostgreSQL 연결 중...")
        conn = psycopg2.connect(database_url)
        print("✅ 연결 성공")
        
        # 데이터 로드
        print("\n📂 JSON 파일 로드 중...")
        users_data = load_json('data/users.json').get('users', [])
        faqs_data = load_json('data/faq_data.json').get('faqs', [])
        feedback_data = load_json('data/feedback.json')
        
        # 마이그레이션 실행
        print("\n🔄 마이그레이션 실행...")
        migrate_users(conn, users_data)
        migrate_faqs(conn, faqs_data)
        migrate_feedbacks(conn, feedback_data)
        
        # 결과 확인
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM users")
        user_count = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(*) FROM faqs")
        faq_count = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(*) FROM feedbacks")
        feedback_count = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(*) FROM detailed_feedbacks")
        detailed_feedback_count = cursor.fetchone()[0]
        
        print("\n" + "=" * 60)
        print("✅ 마이그레이션 완료!")
        print("=" * 60)
        print(f"👥 사용자: {user_count}명")
        print(f"📚 FAQ: {faq_count}개")
        print(f"👍 피드백: {feedback_count}개")
        print(f"📝 상세 피드백: {detailed_feedback_count}개")
        print("=" * 60)
        
        conn.close()
        
    except psycopg2.OperationalError as e:
        print(f"\n❌ 데이터베이스 연결 실패: {e}")
        print("\n💡 해결 방법:")
        print("   1. PostgreSQL이 실행 중인지 확인")
        print("   2. DATABASE_URL이 올바른지 확인")
        print("   3. 데이터베이스가 생성되었는지 확인")
    except Exception as e:
        print(f"\n❌ 마이그레이션 실패: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()

