# 🚀 快速启动指南

## 激活虚拟环境并开发

### Windows (PowerShell)

#### 方式 1：激活虚拟环境后使用
```powershell
# 切换到后端目录
cd backend

# 激活虚拟环境
.\aistock_env\Scripts\Activate.ps1

# 现在可以直接使用 python 和 pip 命令
python --version
pip list

# 启动 FastAPI 开发服务器
python -m uvicorn app.main:app --reload --port 8000

# 或使用 uvicorn 直接命令（虚拟环境已激活）
uvicorn app.main:app --reload
```

#### 方式 2：不激活虚拟环境，直接使用
```powershell
# 进入后端目录
cd backend

# 直接使用虚拟环境中的 Python
$python = ".\aistock_env\Scripts\python.exe"
& $python -m uvicorn app.main:app --reload --port 8000

# 或在后续命令中使用
& $python tests/
```

### Windows (CMD)

```cmd
cd backend

# 激活虚拟环境
aistock_env\Scripts\activate.bat

# 启动 FastAPI 服务器
python -m uvicorn app.main:app --reload --port 8000
```

### Linux/Mac

```bash
cd backend

# 激活虚拟环境
source aistock_env/bin/activate

# 启动 FastAPI 服务器
python -m uvicorn app.main:app --reload --port 8000
```

---

## 前端开发

```bash
cd frontend

# 安装依赖（首次）
npm install

# 启动开发服务器
npm run dev

# 构建生产版本
npm run build

# 代码检查
npm run lint

# 代码格式化
npm run format
```

---

## 常用命令

### 运行测试
```bash
cd backend

# 激活虚拟环境
.\aistock_env\Scripts\Activate.ps1

# 运行所有测试
pytest

# 运行特定测试文件
pytest tests/test_api.py

# 显示覆盖率
pytest --cov=app tests/
```

### 数据库初始化
```bash
# 使用虚拟环境 Python
$python = ".\aistock_env\Scripts\python.exe"

# 初始化数据库表
& $python -c "from app.db.database import init_db; init_db()"

# 清空数据库
& $python -c "from app.db.database import drop_db; drop_db()"
```

### 安装新依赖
```bash
# 激活虚拟环境
.\aistock_env\Scripts\Activate.ps1

# 安装新包
pip install <package-name>

# 更新 requirements.txt
pip freeze > requirements.txt
```

### 代码格式化和检查
```bash
# 激活虚拟环境
.\aistock_env\Scripts\Activate.ps1

# 使用 black 格式化代码
black app/

# 使用 flake8 检查代码
flake8 app/

# 使用 mypy 进行类型检查
mypy app/
```

---

## 访问应用

- **FastAPI 文档**: http://localhost:8000/docs
- **FastAPI ReDoc**: http://localhost:8000/redoc
- **健康检查**: http://localhost:8000/health
- **前端应用**: http://localhost:5173

---

## Docker 容器化部署

```bash
# 在项目根目录

# 启动所有容器
docker-compose up -d

# 停止所有容器
docker-compose down

# 查看容器状态
docker-compose ps

# 查看日志
docker-compose logs -f backend
docker-compose logs -f frontend

# 重启服务
docker-compose restart
```

---

## 常见问题

**Q: 虚拟环境在哪里?**  
A: `backend/aistock_env/`

**Q: 如何重新安装依赖?**  
A: 删除 `backend/aistock_env/` 目录，然后运行 `python -m venv aistock_env` 和 `pip install -r requirements.txt`

**Q: 如何在多个终端中使用虚拟环境?**  
A: 每个终端都需要独立激活虚拟环境，或使用第二种方式直接指定 Python 可执行文件

**Q: 依赖安装失败怎么办?**  
A: 检查 `requirements.txt` 中是否有版本冲突，参考 [SETUP_COMPLETE.md](./SETUP_COMPLETE.md) 了解已知的版本问题

---

## 下一步

1. ✅ 虚拟环境已设置
2. 🔄 测试 FastAPI 服务器（运行 `python -m uvicorn app.main:app --reload`）
3. 🔄 测试前端（进入 `frontend` 目录，运行 `npm install` 和 `npm run dev`）
4. 🔄 初始化数据库
5. 🔄 运行完整测试套件

---

**最后更新**: 2026-01-25  
**环境**: Python 3.12.9, Node.js v22.14.0+
