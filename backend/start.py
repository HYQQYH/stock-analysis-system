#!/usr/bin/env python
"""
启动 FastAPI 开发服务器
"""
import sys
import os

# 添加 backend 目录到 Python 路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

if __name__ == "__main__":
    import uvicorn
    
    print("\n" + "="*60)
    print("🚀 启动 Stock Analysis System API")
    print("="*60)
    print(f"Python: {sys.version.split()[0]}")
    print(f"Address: http://127.0.0.1:8000")
    print(f"Docs: http://127.0.0.1:8000/docs")
    print("="*60 + "\n")
    
    try:
        uvicorn.run(
            app="app.simple_app:app",
            host="127.0.0.1",
            port=8000,
            log_level="info",
            reload=False
        )
    except Exception as e:
        print(f"\n❌ Error: {e}", file=sys.stderr)
        sys.exit(1)
