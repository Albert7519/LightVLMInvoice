# LocalllmOcrMK2 - 智能发票混合识别系统

基于 Qwen3.5 Vision Language Model 的企业级发票 OCR 识别系统。支持多格式发票、自动字段提取、Excel 导出。

![License](https://img.shields.io/badge/license-MIT-green)
![Python](https://img.shields.io/badge/python-3.11%2B-blue)
![Docker](https://img.shields.io/badge/docker-ready-blue)

---

## 🎯 核心特性

- **高精度识别**：基于 Qwen3.5 2B VLM，支持中英文混合发票
- **GPU 加速**：vLLM 推理引擎，支持 NVIDIA GPU 加速
- **异步处理**：Celery + Redis 任务队列，支持批量处理
- **灵活导出**：自动生成 Excel，包含完整发票信息
- **Docker 就绪**：一键 Docker Compose 部署

---

## 🚀 快速开始

### 前置要求

- Python 3.11+
- Node.js 18.0+
- Redis (可选，自动安装)
- NVIDIA GPU (可选，CPU 模式可用)

### 方案 A：一键本地装机（推荐）

```bash
cd /home/albert/CodeProjects/LocalllmOcrMK2

# 一键安装所有依赖
bash setup_local.sh

# 启动所有服务
make dev
```

**完成后访问**：
- 前端：http://localhost:5173
- API 文档：http://localhost:8080/docs

### 方案 B：Docker Compose（生产推荐）

```bash
# 构建镜像
docker-compose build

# 启动服务
docker-compose up -d

# 等待 30-60 秒，然后访问
open http://localhost
```

### 方案 C：手动配置

详见：[LOCAL_SETUP.md](LOCAL_SETUP.md)

---

## 📋 项目结构

```
LocalllmOcrMK2/
├── backend/                    # FastAPI 后端
│   ├── main.py                # API 入口
│   ├── tasks.py               # Celery 异步任务
│   ├── celery_app.py          # Celery 配置
│   ├── Dockerfile             # 后端容器定义
│   ├── requirements.txt        # Python 依赖
│   ├── .env.example           # 环境变量模板
│   ├── check_gpu.py           # GPU 检验脚本
│   ├── start_dev.sh           # 本地启动脚本
│   └── uploads/               # 上传文件存储
│
├── frontend/                   # React 前端
│   ├── src/App.tsx            # 主组件
│   ├── Dockerfile             # 前端容器定义
│   ├── nginx.conf             # Nginx 配置
│   ├── package.json           # Node 依赖
│   └── .env.example           # 环境变量
│
├── tests/                      # 测试套件
│   ├── run_tests.sh           # 测试运行脚本
│   └── performance_benchmark.py # 性能测试
│
├── docker-compose.yml          # Docker 编排
├── Makefile                    # 便捷命令
└── 文档
    ├── IMPLEMENTATION_GUIDE.md  # 详尽实施指南
    ├── LOCAL_SETUP.md           # 本地开发指南
    ├── PHASE1_COMPLETION_REPORT.md # Phase 1 完成报告
    └── DEPLOYMENT.md            # 部署指南（准备中）
```

---

## 🔧 环境配置

### 后端环境变量

```bash
cp backend/.env.example backend/.env
```

关键变量：
```
VLLM_API_BASE=http://localhost:8000/v1
VLLM_USE_MODELSCOPE=true              # 使用国内镜像
VLLM_GPU_MEMORY_UTILIZATION=0.9       # GPU 显存使用率
REDIS_URL=redis://localhost:6379/0    # Redis 连接
UVICORN_PORT=8080                     # FastAPI 端口
```

### 前端环境变量

```bash
cp frontend/.env.example frontend/.env
```

关键变量：
```
VITE_API_BASE=http://localhost:8000/api/v1/invoices
```

---

## 📖 常用命令

```bash
# 开发环境
make dev              # 启动所有本地服务
make gpu-check        # 检查 GPU 就绪状态
make test             # 运行所有测试

# Docker
make docker-build     # 构建 Docker 镜像
make docker-up        # Docker Compose 启动
make docker-down      # Docker Compose 停止
make docker-logs      # 查看 Docker 日志

# 清理
make clean            # 停止服务并清理
```

---

## 🧪 测试

```bash
# 后端测试
cd backend && pytest tests/ -v

# 前端测试（需 npm install）
cd frontend && npm run test

# 性能基准（需服务运行）
python tests/performance_benchmark.py

# 一键运行所有测试
make test
```

---

## 🌐 API 文档

启动后访问：**http://localhost:8080/docs**

### 主要端点

| 方法 | 端点 | 说明 |
|------|------|------|
| POST | `/api/v1/invoices/extract` | 上传发票并创建识别任务 |
| GET | `/api/v1/invoices/status/{task_id}` | 查询任务状态和进度 |
| POST | `/api/v1/invoices/export` | 导出识别结果为 Excel |

---

## 📊 架构

```
┌─────────────┐
│   Browser   │  
│  (React)    │
└──────┬──────┘
       │ http://localhost:5173
       ▼
┌──────────────────┐
│  Frontend (SPA)  │
│  Vite/Nginx      │
└────────┬─────────┘
         │ API call
         ▼
┌──────────────────┐
│  FastAPI (8080)  │  ◄── Upload PDF
├──────────────────┤
│ Redis (6379)     │  ◄── Task Queue
├──────────────────┤
│ Celery Worker    │  ◄── Process Task
└────────┬─────────┘
         │
         ▼
┌──────────────────┐
│  vLLM (8000)     │  ◄── Model Inference
│  + Qwen3.5 2B    │
│  + GPU (NVIDIA)  │
└──────────────────┘
```

---

## 🐳 Docker 部署

### 快速启动

```bash
docker-compose up -d
```

### 服务列表

| 服务 | 端口 | 用途 |
|------|------|------|
| frontend | 80 | React SPA (Nginx) |
| backend | 8080 | FastAPI 网关 |
| vllm | 8000 | 模型推理服务 |
| celery | - | 异步任务处理 |
| redis | 6379 | 消息队列 |

### 停止服务

```bash
docker-compose down
```

---

## 🔍 GPU 检查

```bash
# 检查 GPU 就绪状态
python backend/check_gpu.py
```

**输出示例**：
```
✓ GPU found: NVIDIA RTX 3060
  Available memory: 12 GB
✓ PyTorch CUDA available (CUDA 12.1)
✓ vLLM imported successfully
✓ ModelScope imported successfully
✓ GPU environment is ready for inference
```

---

## 📝 系统要求

### 最低配置（CPU 推理）
- CPU: 4 核
- 内存: 8GB
- 存储: 50GB (含模型缓存)
- 网络: 需要下载 2-3GB 模型文件

### 推荐配置（GPU 加速）
- GPU: NVIDIA RTX 3060 或更高 (≥6GB 显存)
- CPU: 8 核
- 内存: 16GB
- 存储: 200GB
- 网络: 10Mbps+

---

## 🛠️ 部署到生产环境

### Linux 5090 机器

1. **安装系统依赖**：
   ```bash
   bash setup_local.sh
   ```

2. **生成依赖锁**：
   ```bash
   cd backend && pip freeze > requirements.lock
   ```

3. **启动 Docker**：
   ```bash
   docker-compose up -d
   ```

详见：[DEPLOYMENT.md](DEPLOYMENT.md)（准备中）

---

## 📚 文档

| 文档 | 说明 |
|------|------|
| [IMPLEMENTATION_GUIDE.md](IMPLEMENTATION_GUIDE.md) | 详尽的 4 阶段实施指南 |
| [LOCAL_SETUP.md](LOCAL_SETUP.md) | 本地开发环境配置 |
| [PHASE1_COMPLETION_REPORT.md](PHASE1_COMPLETION_REPORT.md) | Phase 1 完成情况 |
| [PHASE1_LOCAL_VERIFICATION.md](PHASE1_LOCAL_VERIFICATION.md) | 本地验证指引 |

---

## 🐛 故障排查

### 常见问题

**Q: vLLM 启动缓慢**
> 第一次启动需下载 2-3GB 模型文件，耐心等待 10-20 分钟。

**Q: Port already in use**
> 修改 `backend/.env` 中的 `UVICORN_PORT`，或杀死占用进程。

**Q: Redis connection refused**
> 确保 Redis 正在运行：`redis-cli ping` 应返回 PONG。

**Q: API 无法访问**
> 检查 CORS 配置或防火墙设置。

详见：[LOCAL_SETUP.md#常见问题](LOCAL_SETUP.md#常见问题)

---

## 🤝 贡献

欢迎提交 Issue 和 PR！

---

## 📄 许可

MIT License - 详见 [LICENSE](LICENSE)

---

## 📞 支持

- 📖 文档：见上方 [文档](#-文档) 部分
- 🐛 问题：提交 GitHub Issue
- 💬 讨论：参考 [LOCAL_SETUP.md](LOCAL_SETUP.md)

---

## 🔄 项目状态

- ✅ Phase 1：依赖与环境完善 (2026-03-31)
- ⏳ Phase 2：Docker 容器化 (进行中)
- ⏳ Phase 3：测试与性能基准 (待进行)
- ⏳ Phase 4：生产部署文档 (待进行)

---

**最后更新**：2026年3月31日
