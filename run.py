"""
Encar Copilot 서버 실행 스크립트
"""
import uvicorn
from config.settings import settings

if __name__ == "__main__":
    print("=" * 60)
    print("🚀 Encar Copilot (엔디) v2.0 서버를 시작합니다...")
    print("=" * 60)
    print()
    print(f"📍 서버 주소: http://localhost:{settings.PORT}")
    print(f"📚 API 문서: http://localhost:{settings.PORT}/docs")
    print("💡 중지하려면 Ctrl+C를 누르세요")
    print()
    print("=" * 60)
    
    uvicorn.run(
        "main:app",
        host=settings.HOST,
        port=settings.PORT,
        reload=settings.RELOAD,
        log_level=settings.LOG_LEVEL
    )
