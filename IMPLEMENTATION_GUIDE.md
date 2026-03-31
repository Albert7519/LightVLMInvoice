# 🎯 LocalllmOcrMK2 Docker 化完整实施指南

**项目目标**：将发票 OCR 系统从开发状态升级到生产就绪（Docker 容器化、自动化测试、完整部署）

**交付环境**：Linux 5090 机器（NVIDIA GPU + 国内网络）

**最终成果**：一句命令启动完整系统 → `docker-compose up -d`

---

## 📋 核心需求确认

| 需求 | 状态 |
|------|------|
| 交付形式 | ✅ Docker 镜像 + docker-compose.yml |
| GPU 支持 | ✅ NVIDIA GPU + vLLM 加速 |
| 模型源 | ✅ ModelScope（国内镜像） |
| 测试范围 | ✅ 基本功能 + 端到端 + 性能基准 |
| 工期 | ✅ 15 个工作日 |

---

## 🏗️ 四阶段实施计划

### **Phase 1：依赖与环境完善** 
*目标：修复缺失依赖、规范化配置、实现本地一键启动*

#### P1a：补齐依赖并生成 requirements.lock

**文件**：`backend/requirements.lock`

**操作步骤**：
1. 在 `backend/requirements.txt` 追加缺失依赖：
   - `vllm>=0.6.0`
   - `modelscope>=1.14.0`
   
2. 添加 Python 版本标记注释

3. 生成 lock 文件（在 backend 目录）：
   ```bash
   pip freeze > requirements.lock
   ```

**验证**：
```bash
pip install -r requirements.lock
python -c "import vllm; import modelscope; print('✓ 依赖就绪')"
```

---

#### P1b：编写 GPU 环境检验脚本

**文件**：`backend/check_gpu.py`

**功能**：
- 检查 nvidia-smi 可用性
- 验证 CUDA 版本 ≥ 11.8
- 检查可用显存 ≥ 6GB
- 测试 vLLM 初始化
- 验证 ModelScope 可达性

**输出**：
- 返回码 0：GPU 就绪
- 返回码 1：降级到 CPU
- 返回码 2：失败/禁用

---

#### P1c：环境变量标准化

**文件**：
- `backend/.env.example` - 后端环境变量模板
- `frontend/.env.example` - 前端环境变量模板

**后端 .env 内容**：
```bash
# vLLM 推理服务配置
VLLM_API_BASE=http://localhost:8000/v1
VLLM_API_KEY=EMPTY
VLLM_USE_MODELSCOPE=true
VLLM_GPU_MEMORY_UTILIZATION=0.9

# Redis 消息队列
REDIS_URL=redis://localhost:6379/0

# FastAPI 服务
UVICORN_HOST=0.0.0.0
UVICORN_PORT=8080
UVICORN_RELOAD=true
```

**前端 .env 内容**：
```bash
# API 服务地址
VITE_API_BASE=http://localhost:8000/api/v1/invoices
```

**代码修改**：
- `backend/main.py` - 改为从 os.getenv() 读取配置
- `backend/celery_app.py` - 改为从 .env 读取 REDIS_URL
- `backend/tasks.py` - 改为从 .env 读取 vLLM 配置
- `frontend/src/App.tsx` - 改为从环境变量读取 API_BASE

---

#### P1d：一键本地启动脚本

**文件**：
- `backend/start_dev.sh` - 完整启动脚本
- `Makefile` - 便捷命令入口
- `backend/cleanup.sh` - 清理脚本

**使用**：
```bash
# 启动所有服务
make dev

# 运行测试
make test

# 清理进程
make clean
```

---

### **Phase 2：Docker 容器化**
*目标：三个 Dockerfile + docker-compose.yml，GPU 支持*

#### P2a：后端 Dockerfile（多阶段构建）

**文件**：`backend/Dockerfile`

**特点**：
- Base：`nvidia/cuda:12.4.1-runtime-ubuntu22.04`
- 包含 PDF 库依赖（libpdfium, libpoppler）
- vLLM 编译环境
- 多阶段构建优化大小
- 暴露端口 8080，包含 healthcheck

---

#### P2b：前端 Dockerfile（多阶段构建）

**文件**：
- `frontend/Dockerfile` - 前端容器定义
- `frontend/nginx.conf` - Nginx 配置（关键！）

**Nginx 配置要点**：
- SPA fallback：`try_files $uri $uri/ /index.html`
- API 代理：`location /api/` → `proxy_pass http://backend:8080`
- 大文件支持：`client_max_body_size 100M`
- 缓存策略：静态文件 1 小时缓存

---

#### P2c：vLLM 容器配置

**方案**：使用官方 `vllm/vllm-openai:v0.6.x-gpu` 镜像

**环境变量**：
- `VLLM_USE_MODELSCOPE=true`（国内镜像）
- `VLLM_GPU_MEMORY_UTILIZATION=0.9`

---

#### P2d：docker-compose.yml 完整编排

**文件**：`docker-compose.yml` (根目录)

**5 个 Services**：
1. **redis** - 消息队列 + AOF 持久化
2. **vllm** - GPU 推理服务（官方镜像）
3. **backend** - FastAPI 网关
4. **celery** - 异步任务处理
5. **frontend** - Nginx SPA 服务

**关键配置**：
- GPU 驱动支持：`deploy.resources.reservations.devices`
- 卷挂载：uploads（持久化）、缓存目录
- 健康检查：所有服务都包含
- 依赖顺序：`depends_on` 字段
- 网络：容器内部通过 Docker DNS 通信

---

### **Phase 3：自动化测试**
*目标：覆盖核心业务链路*

#### P3a：后端集成测试

**文件**：`backend/tests/test_e2e.py`

**框架**：pytest

**测试案例**：
- 有效 PDF 上传 → 返回 task_id
- 任务状态查询
- 使用 mock vLLM 的端到端流程
- 导出边界条件

---

#### P3b：前端 UI 测试

**文件**：`frontend/src/__tests__/App.test.tsx`

**框架**：Vitest + @testing-library/react

**测试案例**：
- 组件渲染
- 文件拖拽处理
- 状态轮询流程
- 导出功能

---

#### P3c：性能基准测试

**文件**：`tests/performance_benchmark.py`

**指标**：
- 单张发票识别时间：** < 30s **
- 并发 10 张发票处理：** < 60s **

---

#### P3d：测试运行脚本

**文件**：`tests/run_tests.sh`

**执行**：
```bash
# 本地运行（需要服务启动）
bash tests/run_tests.sh

# Docker 运行
docker-compose run --rm backend pytest tests/ -v
```

---

### **Phase 4：交付与文档**
*目标：完整部署手册、故障排查、生产检查清单*

#### P4a：DEPLOYMENT.md（部署手册 - 关键！）

**内容**：
1. 系统要求 & 硬件检查
2. 快速启动（Docker Compose）
3. 验证部署（API 端点测试）
4. **详尽故障排查**
   - vLLM 模型下载超时
   - GPU 显存溢出 (OOM)
   - Celery 任务堆积
   - Redis 连接失败
5. 性能调优指南
6. 日志与监控
7. Flower 监控面板集成
8. 备选方案（无 GPU、本地部署）
9. **生产安全建议**（CORS、HTTPS、Redis 密码）
10. 清理与卸载

---

#### P4b：GPU_TUNING.md

**内容**：
- vLLM 显存优化参数详解
- ModelScope 镜像源配置
- 多 GPU 分布式推理方案
- 显存监控工具

---

#### P4c：PRODUCTION_CHECKLIST.md

**内容**：
- 基础设施检查
- 应用配置检查
- 安全加固清单
- 验证步骤

---

#### P4d：更新 README + 新增 LOCAL_SETUP.md

**README 更新**：
- Docker 快速启动章节
- 文档链接区

**LOCAL_SETUP.md**：
- 本地开发完整指南
- `make dev` 启动流程
- 依赖安装步骤

---

## 📊 文件变更完整清单

### 新增文件（24 个）

#### 核心容器化（5 个）
```
backend/Dockerfile
frontend/Dockerfile
frontend/nginx.conf
docker-compose.yml
Makefile
```

#### 依赖与配置（6 个）
```
backend/requirements.lock
backend/.env.example
backend/check_gpu.py
backend/start_dev.sh
backend/cleanup.sh
frontend/.env.example
```

#### 测试套件（5 个）
```
backend/tests/__init__.py
backend/tests/test_e2e.py
frontend/src/__tests__/App.test.tsx
tests/run_tests.sh
tests/performance_benchmark.py
tests/fixtures/sample_invoice.pdf
```

#### 部署文档（5 个）
```
DEPLOYMENT.md
GPU_TUNING.md
PRODUCTION_CHECKLIST.md
LOCAL_SETUP.md
IMPLEMENTATION_GUIDE.md (本文件)
```

### 修改现有文件（5 个）

```
backend/main.py              # 改为从 .env 读取配置
backend/celery_app.py        # 改为从 .env 读取 REDIS_URL
backend/tasks.py             # 改为从 .env 读取 vLLM 配置
frontend/src/App.tsx         # 改为从环境变量读取 API_BASE
frontend/package.json        # 添加 test 命令脚本
README.md                    # 添加 Docker 快速开始
```

---

## ✅ 阶段性验证标准

### Phase 1 验证
```bash
# 1. 依赖安装成功
pip install -r backend/requirements.lock

# 2. GPU 检验脚本运行
python backend/check_gpu.py
# 预期：返回 0（GPU 就绪）或 1（降级 CPU）

# 3. 环境变量加载正常
cd backend && python -c "import os; from dotenv import load_dotenv; load_dotenv('.env.example'); print(os.getenv('VLLM_API_BASE'))"

# 4. 本地启动成功
make dev
# 预期：Redis、vLLM、Celery、FastAPI、前端依次启动，无错误
```

### Phase 2 验证
```bash
# 1. 镜像构建成功
docker-compose build

# 2. 容器启动成功
docker-compose up -d

# 3. 等待 30-60 秒，所有服务就绪
docker-compose ps
# 预期：所有服务 STATUS 为 "Up (healthy)"

# 4. API 可达
curl http://localhost:8080/docs        # FastAPI 文档
curl http://localhost                  # 前端页面
curl http://localhost:8000/v1/models   # vLLM 模型列表
```

### Phase 3 验证
```bash
# 1. 后端测试
docker-compose run --rm backend pytest tests/ -v

# 2. 前端测试
docker-compose run --rm frontend npm run test

# 3. 性能基准
python tests/performance_benchmark.py
# 预期：单张 < 30s，并发 < 60s
```

### Phase 4 验证
```bash
# 1. 文档完整性检查
ls -la *.md   # 应包含：DEPLOYMENT.md, GPU_TUNING.md 等

# 2. 生产检查清单
cat PRODUCTION_CHECKLIST.md | grep -c "\\[ \\]"  # 应有多个检查项

# 3. 功能端到端验证
curl -X POST http://localhost:8080/api/v1/invoices/extract \
  -F "files=@tests/fixtures/sample_invoice.pdf"
# 预期：返回 task_id，可查询状态，最终导出 Excel
```

---

## 🔄 执行顺序指南

### **Day 1-2：Phase 1**
- [ ] P1a：补齐依赖 → requirements.lock
- [ ] P1b：编写 GPU 检验脚本
- [ ] P1c：环境变量标准化 + 代码修改
- [ ] P1d：启动脚本 + Makefile
- [ ] 本地验证：`make dev` 成功启动

### **Day 3-5：Phase 2**
- [ ] P2a：后端 Dockerfile
- [ ] P2b：前端 Dockerfile + nginx.conf
- [ ] P2c/P2d：docker-compose.yml
- [ ] 本地 Docker 测试与调试：`docker-compose up`
- [ ] 验证 GPU、API、前端可达

### **Day 6-10：Phase 3**
- [ ] P3a：后端集成测试
- [ ] P3b：前端 UI 测试
- [ ] P3c/P3d：性能基准 + 测试脚本
- [ ] 完整测试运行：`docker-compose run --rm backend pytest`
- [ ] 性能验收

### **Day 11-15：Phase 4 + 交付**
- [ ] P4a：DEPLOYMENT.md（详细部署手册）
- [ ] P4b：GPU_TUNING.md
- [ ] P4c：PRODUCTION_CHECKLIST.md
- [ ] P4d：README 更新 + LOCAL_SETUP.md
- [ ] 端到端验证 + 性能测试
- [ ] 最终交付物检查清单

---

## 📝 实施中的关键注意事项

### Docker & 容器化
- ✅ 使用多阶段构建减小镜像大小
- ✅ GPU 支持需要 `--runtime=nvidia` 或 `deploy.resources`
- ✅ 容器间通信通过 Docker 内部 DNS（使用 service name）
- ✅ 卷挂载用于保存 uploads 和模型缓存
- ✅ 健康检查确保服务启动顺序

### 环境变量标准化
- ✅ `.env.example` 作为模板，用户复制为 `.env`
- ✅ 代码中用 `os.getenv()` 读取，设置合理默认值
- ✅ 前端使用 `VITE_` 前缀的环境变量（Vite 约定）
- ✅ 容器中通过 `docker-compose.yml` 的 `environment` 字段传入

### 模型与 GPU
- ✅ vLLM 基础镜像：`vllm/vllm-openai:v0.6.x-gpu`
- ✅ ModelScope：设置 `VLLM_USE_MODELSCOPE=true`
- ✅ 显存管理：`VLLM_GPU_MEMORY_UTILIZATION=0.9`（可根据情况调整）
- ✅ 模型缓存卷：`modelscope_cache:/root/.modelscope`

### 测试覆盖
- ✅ 后端测试使用 pytest + mock
- ✅ 前端测试使用 Vitest + @testing-library
- ✅ 性能测试在真实环境（Docker）中运行
- ✅ 测试脚本可在 Docker 容器内执行

### 部署文档
- ✅ DEPLOYMENT.md 重点：故障排查章节详尽
- ✅ 清晰的命令示例 + 预期输出
- ✅ GPU 显存溢出、模型超时等常见问题
- ✅ 生产部署前的完整检查清单

---

## 🎯 最终交付物

### 给用户的命令
```bash
# 1. 克隆仓库
git clone <repo_url>
cd LocalllmOcrMK2

# 2. 启动系统（一句 docker-compose）
docker-compose up -d

# 3. 等待 30-60 秒，所有服务就绪

# 4. 访问应用
# 前端：http://localhost
# API 文档：http://localhost:8080/docs
# Flower 监控（可选）：http://localhost:5555
```

### 最终目录结构
```
LocalllmOcrMK2/
├── IMPLEMENTATION_GUIDE.md      # 本文件
├── DEPLOYMENT.md                # 部署手册
├── GPU_TUNING.md                # GPU 调优指南
├── PRODUCTION_CHECKLIST.md      # 生产检查清单
├── LOCAL_SETUP.md               # 本地开发指南
├── docker-compose.yml           # Docker 编排
├── Makefile                     # 便捷命令
├── README.md                    # 更新
│
├── backend/
│   ├── Dockerfile
│   ├── requirements.txt          # (原有)
│   ├── requirements.lock         # 新增
│   ├── .env.example              # 新增
│   ├── check_gpu.py              # 新增
│   ├── start_dev.sh              # 新增
│   ├── cleanup.sh                # 新增
│   ├── main.py                   # 修改（读 .env）
│   ├── celery_app.py             # 修改（读 .env）
│   ├── tasks.py                  # 修改（读 .env）
│   ├── uploads/                  # (运行时创建)
│   └── tests/
│       ├── __init__.py           # 新增
│       └── test_e2e.py           # 新增
│
├── frontend/
│   ├── Dockerfile
│   ├── nginx.conf                # 新增
│   ├── .env.example              # 新增
│   ├── package.json              # 修改（添加 test）
│   ├── src/
│   │   ├── App.tsx               # 修改（读环境变量）
│   │   └── __tests__/
│   │       └── App.test.tsx      # 新增
│   └── dist/                     # (构建时生成)
│
└── tests/
    ├── run_tests.sh              # 新增
    ├── performance_benchmark.py  # 新增
    └── fixtures/
        └── sample_invoice.pdf    # 新增（测试用）
```

---

## 💡 关键成功因素 (CSF)

1. **环境变量管理** - 没有硬编码，所有配置都可通过 .env 灵活调整
2. **Docker 多阶段构建** - 优化镜像大小，加快 CI/CD
3. **完整健康检查** - 容器就绪校验，自动启动顺序
4. **详尽部署文档** - 特别是故障排查，降低用户部署难度
5. **自动化测试** - 确保核心功能稳定，性能基准可重复
6. **GPU 支持配置** - 正确使用 NVIDIA 容器运行时，显存合理管理

---

## ⏭️ 后续优化空间

- [ ] Kubernetes 部署配置
- [ ] Flower 监控仪表板可视化
- [ ] 多 GPU 分布式推理
- [ ] 更激进的模型量化（INT4）
- [ ] 模型热更新机制
- [ ] 自动扩缩容（基于队列深度）
- [ ] Prometheus + Grafana 监控

---

**此文档为完整实施参考。请逐 Phase 按步骤执行，每个 Phase 完成后进行验证。**

