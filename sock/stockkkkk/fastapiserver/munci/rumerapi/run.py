"""
루머 검증 API 서버 실행 스크립트
"""
import uvicorn

if __name__ == "__main__":
    uvicorn.run(
        "munci.rumerapi.app.main:app",
        host="0.0.0.0",
        port=8001,
        reload=True
    )
