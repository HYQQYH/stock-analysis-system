@echo off
REM 激活虚拟环境并安装依赖的脚本

cd /d D:\projects\work\code\gitee\stock-analysis-system\backend

REM 激活虚拟环境
call .\aistock_env\Scripts\activate.bat

REM 升级 pip
echo ===== Upgrading pip =====
python -m pip install --upgrade pip setuptools wheel

REM 安装依赖
echo ===== Installing requirements =====
pip install -r requirements.txt

REM 显示安装结果
echo ===== Installation complete =====
pip list | findstr /E "fastapi pandas sqlalchemy redis"

REM 验证关键包
echo ===== Verifying imports =====
python -c "import fastapi; print('FastAPI:', fastapi.__version__)"
python -c "import pandas; print('Pandas:', pandas.__version__)"
python -c "import sqlalchemy; print('SQLAlchemy:', sqlalchemy.__version__)"
python -c "import redis; print('Redis client loaded successfully')"

echo ===== Setup completed =====
