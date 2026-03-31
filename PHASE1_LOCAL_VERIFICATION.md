# 📋 Phase 1 本地验证与启动指南

**日期**：2026年3月31日
**状态**：✅ Phase 1 完成，准备本地验证

---

## 🎯 当前状态

✅ **已完成**：
- 所有 Phase 1 代码、脚本已编写
- 环境变量模板已创建
- 测试框架已就位
- GPU 检验脚本已准备

⚠️ **需要**：
- 系统依赖安装（pip3、Redis）
- Python 依赖安装
- 环境配置

---

## 🚀 快速启动（3 个步骤）

### 步骤 1️⃣：自动一键装机（推荐）

在项目根目录运行：

```bash
cd /home/albert/CodeProjects/LocalllmOcrMK2
bash setup_local.sh
```

**这个脚本会自动**：
1. ✅ 安装 pip3
2. ✅ 安装 Redis
3. ✅ 创建 Python 虚拟环境
4. ✅ 安装 Python 依赖
5. ✅ 安装 Node.js 依赖
6. ✅ 初始化 .env 配置文件
7. ✅ 启动 Redis 服务

**需要输入密码**（sudo 安装系统软件包）

---

### 步骤 2️⃣：检查 GPU 环境（可选）

```bash
python backend/check_gpu.py
```

**预期输出**：
- ✅ 有 GPU：`✓ GPU ready`
- ⚠️ 无 GPU：`⚠ GPU not available, falling back to CPU mode`（功能完整，仅速度慢）

---

### 步骤 3️⃣：启动本地服务

```bash
make dev
```

**预期输出**（2-3 分钟）：

```
🚀 LocalllmOcrMK2 Development Startup
======================================

[1/5] Checking GPU environment...
✓ GPU check passed (CPU mode available)

[2/5] Setting up Python environment...
✓ Python environment ready

[3/5] Installing backend dependencies...
✓ Dependencies installed

[4/5] Preparing directories...
✓ Directories ready

[5/5] Starting services...
Starting Redis on port 6379...
  ✓ Redis started

Starting vLLM model server on port 8000...
  Waiting for vLLM to initialize...
  ✓ vLLM ready

Starting Celery worker...
  ✓ Celery worker started

Starting FastAPI backend on port 8080...
  ✓ FastAPI ready

Starting Frontend dev server on port 5173...
  ✓ Frontend running

======================================
✅ All services started successfully!

Service URLs:
  Backend API:    http://localhost:8080
  API Docs:       http://localhost:8080/docs
  Frontend:       http://localhost:5173
  Redis:          localhost:6379

Press Ctrl+C to stop all services
======================================
```

---

## 📖 详细步骤说明

### 如果 `setup_local.sh` 失败或您想手动配置

详见：[LOCAL_SETUP.md](LOCAL_SETUP.md)

---

## 🧪 完成后的验证

### 验证 1：API 是否可达

在新终端运行：

```bash
curl http://localhost:8080/docs
```

**预期**：返回 FastAPI Swagger UI 文档（HTML）

### 验证 2：前端是否可達

在浏览器打开：

```
http://localhost:5173
```

**预期**：看到发票上传界面（拖拽 PDF 区域）

### 验证 3：Redis 是否连接

```bash
redis-cli ping
```

**预期**：输出 `PONG`

### 验证 4：测试完整流程（可选）

1. 访问 http://localhost:5173
2. 拖拽或选择 PDF 文件（或创建简单测试 PDF）
3. 点击上传
4. 观察进度
5. 等待识别完成
6. 下载 Excel 结果

---

## ⏹️ 停止服务

**方式 1**：在运行 `make dev` 的终端按 `Ctrl+C`

**方式 2**：手动清理

```bash
make clean
# 或
bash backend/cleanup.sh
```

---

## 🐳 下一步：Phase 2 Docker 化

一旦本地验证成功，我们会立即开启 **Phase 2：Docker 容器化**

### Phase 2 包含：
1. **后端 Dockerfile** - 基于 nvidia/cuda:12.4.1-runtime
2. **前端 Dockerfile** - Nginx SPA 静态服务
3. **nginx.conf** - 反向代理配置
4. **docker-compose.yml** - 5 个 services 的完整编排
5. 完整的 Docker 一键启动

### 时间预估
- 编写 Dockerfile：1 天
- docker-compose + 测试：1-2 天
- 文档 + 文档调整：1 天

---

## 💡 文件清单

### 本地验证相关文件

| 文件 | 说明 |
|------|------|
| `setup_local.sh` | 🆕 一键自动装机脚本 |
| `LOCAL_SETUP.md` | 🆕 本地开发详细指南 |
| `Makefile` | 便捷命令 (`make dev`, `make test` 等) |
| `backend/start_dev.sh` | 本地完整启动脚本 |
| `backend/check_gpu.py` | GPU 环境检验 |
| `backend/.env.example` | 环境变量模板 |
| `frontend/.env.example` | 前端环境变量 |

---

## 🆘 常见问题

### Q1：运行 setup_local.sh 时卡住
**A**：通常是在安装系统包时等待。提示输入密码时，输入你的用户密码即可。

### Q2：make dev 启动后，vLLM 一直在 "Waiting for initialization"
**A**：这是正常的。第一次运行时需下载 2-3GB 模型文件。等待 10-20 分钟（取决于网速）。

### Q3：前端显示 "Cannot connect to API"
**A**：检查：
1. FastAPI 是否启动 (`curl http://localhost:8080/docs`)
2. .env 文件中 `VITE_API_BASE` 是否正确
3. 防火墙是否阻止 8080 端口

### Q4：Redis connection refused
**A**：
```bash
redis-cli ping
# 如果返回错误，启动 Redis：
redis-server --daemonize yes
```

### Q5：Port already in use
**A**：
```bash
# 查找占用该端口的进程
lsof -i :8080

# 杀死进程
kill -9 <PID>

# 或在 backend/.env 改端口
UVICORN_PORT=8081
```

详见：[LOCAL_SETUP.md](LOCAL_SETUP.md#常见问题)

---

## ✅ 验证完成标志

当你看到以下情况时，本地验证完成 ✅

### 终端输出
```
✅ All services started successfully!

Service URLs:
  Backend API:    http://localhost:8080
  API Docs:       http://localhost:8080/docs
  Frontend:       http://localhost:5173
```

### 浏览器访问
- [ ] http://localhost:5173 - 显示发票上传界面
- [ ] http://localhost:8080/docs - 显示 API 文档

### 命令验证
- [ ] `redis-cli ping` - 返回 PONG
- [ ] `curl http://localhost:8080/api/v1/invoices/extract` - 返回 API 响应
- [ ] `make test` - 所有测试通过

---

## 🚀 开启 Phase 2 的条件

本地验证完成后，满足以下条件即可启动 Phase 2：

1. ✅ 所有服务可正常启动
2. ✅ API 可访问
3. ✅ 前端可加载
4. ✅ 无明显错误日志

**然后** → 我会立即创建 3 个 Dockerfile + docker-compose.yml

---

## 📝 建议流程

### 今天（预计 30-60 分钟）
1. 运行 `bash setup_local.sh`
2. 等待系统依赖和 Python/Node 依赖安装
3. 运行 `make dev`
4. 验证所有服务启动成功

### 明天或之后
1. 确认本地验证无问题
2. 通知启动 Phase 2（Docker 化）
3. 我会在 2-3 天内完成 Docker 容器化、测试、文档

---

## 📞 需要帮助？

如果运行过程中遇到问题，请：

1. 收集完整的错误信息
2. 告诉我操作系统和 Python/Node 版本
3. 附上失败时的日志输出

---

**现在准备好了吗？** 

👉 运行：

```bash
cd /home/albert/CodeProjects/LocalllmOcrMK2
bash setup_local.sh
```

🚀 然后：

```bash
make dev
```

验证完成后，告诉我，我将启动 **Phase 2：Docker 容器化**！
