"""启动 FastAPI 测试服务器"""
import sys
import os

# 添加 backend 目录到 Python 路径
sys.path.insert(0, os.path.dirname(__file__))

if __name__ == "__main__":
    import uvicorn
    
    print("\n" + "=" * 60)
    print("🚀 启动 Stock Analysis System API (测试服务器)")
    print("=" * 60)
    print(f"📍 API 地址: http://127.0.0.1:8001")
    print(f"📚 API 文档: http://127.0.0.1:8001/docs")
    print(f"📄 ReDoc: http://127.0.0.1:8001/redoc")
    print("=" * 60)
    print("⏸️  按 Ctrl+C 停止服务器\n")
    
    # 启动 uvicorn 服务器
    uvicorn.run(
        "app.simple_app:app",
        host="127.0.0.1",
        port=8001,
        reload=False,
        log_level="info"
    )
