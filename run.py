"""
Encar Copilot 서버 실행 스크립트
"""
import uvicorn

if __name__ == "__main__":
    print("=" * 60)
    print("🚀 Encar Copilot (엔디) 서버를 시작합니다...")
    print("=" * 60)
    print()
    print("📍 서버 주소: http://localhost:8000")
    print("📚 API 문서: http://localhost:8000/docs")
    print("💡 중지하려면 Ctrl+C를 누르세요")
    print()
    print("=" * 60)
    
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )


