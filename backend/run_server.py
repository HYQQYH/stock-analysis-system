#!/usr/bin/env python
"""FastAPI Server Launcher"""

import os
import sys
import uvicorn

if __name__ == "__main__":
    os.chdir(os.path.dirname(__file__))
    
    print("=" * 50)
    print("🚀 启动 Stock Analysis System API 服务器")
    print("=" * 50)
    print(f"Python 版本: {sys.version}")
    print(f"工作目录: {os.getcwd()}")
    print(f"API 地址: http://127.0.0.1:8000")
    print(f"API 文档: http://127.0.0.1:8000/docs")
    print("=" * 50)
    
    uvicorn.run(
        "app.main_test:app",
        host="127.0.0.1",
        port=8000,
        reload=False,
        log_level="info"
    )
