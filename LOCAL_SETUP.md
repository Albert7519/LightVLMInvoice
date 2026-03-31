# 🧪 Phase 1 本地验证报告

**验证时间**：2026年3月31日
**进行人员**：自动化检查
**状态**：⚠️ 需要系统配置

---

## 📋 系统环境检查结果

### ✅ 已就绪
| 组件 | 版本 | 状态 |
|------|------|------|
| Python | 3.12.3 | ✅ 满足 (≥3.11) |
| Node.js | 24.13.1 | ✅ 满足 (≥18.0) |

### ❌ 缺失或不可用
| 组件 | 当前状态 | 需求 | 影响 |
|------|---------|------|------|
| pip/pip3 | ❌ 未安装 | pip 3.0+ | **阻塞** - 无法安装 Python 依赖 |
| Redis | ❌ 未安装 | redis-server | **阻塞** - Celery/消息队列必需 |
| NVIDIA GPU | ❌ 不可用 | GPU + 驱动 | **可降级** - 改用 CPU 推理 |

---

## ⚠️ 阻塞项及解决方案

### 1. 安装 pip3

```bash
# Ubuntu/Debian
sudo apt-get update && sudo apt-get install -y python3-pip

# 验证
pip3 --version

# 建议设置别名（可选）
echo "alias pip=pip3" >> ~/.bashrc
source ~/.bashrc
```

### 2. 安装 Redis

```bash
# Ubuntu/Debian
sudo apt-get install -y redis-server

# 启动 Redis（一次性）
sudo systemctl start redis-server

# 验证
redis-cli ping
# 应输出：PONG
```

### 3. GPU（可选但推荐）

如果需要 GPU 加速（vLLM 推理）：

```bash
# 检查 NVIDIA 驱动
nvidia-smi

# 如果无驱动，需要安装
# 参考：https://docs.nvidia.com/cuda/cuda-installation-guide-linux/

# 安装后验证
python3 backend/check_gpu.py
```

**如果无 GPU**：系统会自动降级到 CPU 推理（速度会慢 10-20 倍，但功能完整）

---

## 🛠️ 快速一键修复脚本

创建文件 `setup_local.sh`：

```bash
#!/bin/bash

echo "🔧 LocalllmOcrMK2 本地环境设置"
echo "=================================="

# 1. 安装系统依赖
echo "[1/3] 安装系统依赖..."
sudo apt-get update -qq
sudo apt-get install -y -qq python3-pip redis-server

# 2. 验证安装
echo "[2/3] 验证安装..."
pip3 --version
redis-cli --version

# 3. 启动 Redis
echo "[3/3] 启动 Redis..."
sudo systemctl start redis-server
redis-cli ping

echo ""
echo "✅ 环境设置完成！"
echo ""
echo "下一步："
echo "  cd /home/albert/CodeProjects/LocalllmOcrMK2"
echo "  make dev"
```

**运行**：
```bash
bash setup_local.sh
```

---

## 📝 手动设置步骤

如果不能或不想使用上面的脚本，按以下步骤手动操作：

### 步骤 1：安装 pip3
```bash
sudo apt-get update
sudo apt-get install -y python3-pip
pip3 --version  # 验证
```

### 步骤 2：安装 Redis
```bash
sudo apt-get install -y redis-server
sudo systemctl start redis-server
redis-cli ping  # 验证 (应输出 PONG)
```

### 步骤 3：安装 Python 依赖
```bash
cd /home/albert/CodeProjects/LocalllmOcrMK2/backend

# 创建虚拟环境
python3 -m venv venv
source venv/bin/activate

# 安装依赖
pip install -r requirements.txt

# 生成 lock 文件（可选但推荐）
pip freeze > requirements.lock
```

### 步骤 4：安装前端依赖
```bash
cd /home/albert/CodeProjects/LocalllmOcrMK2/frontend
npm install
```

### 步骤 5：初始化环境变量
```bash
# 后端
cd /home/albert/CodeProjects/LocalllmOcrMK2
cp backend/.env.example backend/.env

# 前端
cp frontend/.env.example frontend/.env
```

---

## 🚀 完成以上步骤后的启动

```bash
# 方式 1：使用 Makefile（推荐）
cd /home/albert/CodeProjects/LocalllmOcrMK2
make dev

# 方式 2：直接运行脚本
bash backend/start_dev.sh
```

**预期输出**：
```
✅ All services started successfully!

Service URLs:
  Backend API:    http://localhost:8080
  API Docs:       http://localhost:8080/docs
  Frontend:       http://localhost:5173
  Redis:          localhost:6379

Press Ctrl+C to stop all services
```

---

## 📊 验证检查清单

完成以上设置后，逐项验证：

```bash
# 1. Redis 运行
redis-cli ping
# 期望：PONG

# 2. GPU 检查（可选）
python backend/check_gpu.py
# 期望：EXIT_CODE 0 或 1

# 3. 依赖安装
python -c "import vllm; import modelscope; print('✓')"
# 期望：不报错

# 4. 前端依赖
cd frontend && npm list
# 期望：无错误的依赖树

# 5. 启动测试
make gpu-check  # 快速测试
```

---

## 🎯 完整验证流程（推荐顺序）

### 第 1 阶段：系统检查
```bash
# 确保 pip3 和 Redis 已安装
pip3 --version
redis-cli ping  # 应输出 PONG
```

### 第 2 阶段：生成依赖锁
```bash
cd backend
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
pip freeze > requirements.lock
```

### 第 3 阶段：初始化配置
```bash
# 回到项目根
cd ..
cp backend/.env.example backend/.env
cp frontend/.env.example frontend/.env
```

### 第 4 阶段：启动验证
```bash
# 快速 GPU 检查
python backend/check_gpu.py

# 启动所有服务
make dev

# 在新终端验证 API
curl http://localhost:8080/docs        # 应返回 200
curl http://localhost                  # 应返回 HTML（前端）
```

---

## 💡 常见问题

### ❓ "Redis connection refused"
**解决**：
```bash
# 检查 Redis 运行状态
redis-cli ping

# 如果不响应，启动 Redis
sudo systemctl start redis-server

# 或后台运行
redis-server --daemonize yes
```

### ❓ "ModuleNotFoundError: No module named 'vllm'"
**解决**：
```bash
# 确保在虚拟环境中
source backend/venv/bin/activate

# 重新安装
pip install -r requirements.txt
```

### ❓ "Port 8080 already in use"
**解决**：
```bash
# 查找占用 8080 的进程
lsof -i :8080

# 杀死进程
kill -9 <PID>

# 或在 .env 中改端口
UVICORN_PORT=8081
```

### ❓ "npm: command not found"
**解决**：Node.js 已装，尝试：
```bash
# 使用 nvm 重新加载
nvm use node

# 或使用 npx
npx npm install  # 前端目录
```

### ❓ vLLM 首次启动超级慢（模型下载）
**原因**：第一次运行时需下载 2-3GB 模型文件
**解决**：
- 等待 5-10 分钟，取决于网速
- 或预先手动下载：
  ```bash
  python -c "from modelscope import snapshot_download; snapshot_download('cyankiwi/Qwen3.5-2B-AWQ-BF16-INT8')"
  ```

---

## ✅ 本地验证完成标志

当你看到以下输出时，Phase 1 本地验证完成：

```
✅ All services started successfully!

Service URLs:
  Backend API:    http://localhost:8080
  API Docs:       http://localhost:8080/docs
  Frontend:       http://localhost:5173
  Redis:          localhost:6379

Press Ctrl+C to stop all services
```

访问 http://localhost:5173，应该看到发票上传界面。

---

## 🔄 下一步

### ✅ 验证成功后
1. 上传测试 PDF 到前端
2. 观察任务处理流程
3. 确认识别结果输出
4. 验证 Excel 导出功能

### 然后启动 Phase 2
所有本地验证完成后，我们会立即启动 **Phase 2：Docker 容器化**
- Dockerfile 编写
- nginx 配置
- docker-compose 编排
- 完整的一键 Docker 启动

---

## 📞 支持

如果本地验证遇到问题，请提供：
1. 错误信息（完整输出）
2. 系统环境（OS、Python 版本、Node 版本）
3. 已执行的步骤

---

**生成时间**：2026年3月31日
**下一步**：完成上述系统配置后，运行 `make dev` 启动本地服务
