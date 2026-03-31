# VLM 发票识别系统 (VLM Invoice OCR System)

基于本地视觉大语言模型 (Vision Large Language Model) 的文档/发票结构化信息提取系统。本项目旨在通过本地部署的 VLM 直接对复杂版式（包含多页复合 PDF 或单张图片）进行解析，无需依赖外部 API，保障业务数据的隐私与资产安全。

## 🚀 架构与技术栈

系统采用前后端分离架构，核心处理流程结合了异步任务队列以应对大模型高耗时推理的特性。

- **前端 (Frontend)**: React + Vite + TypeScript + TailwindCSS。生产环境通过 Nginx 运行代理。
- **后端 (Backend)**: FastAPI (高并发 HTTP 框架)。
- **任务调度**: Celery + Redis（用于隔离长耗时的页面切割和 VLM 推理任务）。
- **推理引擎**: 基于 vLLM 部署的本地大模型（默认兼容 Qwen-VL 等具备视觉理解能力的小参数/量化模型，保障显存可控）。
- **容错增强**: 使用 `json_repair` 防止因模型输出偶发的 JSON 语法错误（如缺少引号、截断等）导致的数据丢弃。

## 📂 项目结构

```text
.
├── backend/                  # 后端及模型调度相关的核心代码
│   ├── main.py               # FastAPI 接口定义（上传、结果查询等 API）
│   ├── tasks.py              # Celery 异步任务：PDF分页、VLM 调用与信息提取核心逻辑
│   ├── celery_app.py         # 队列与 Redis 配置
│   └── requirements.txt      # Python 依赖清单
├── frontend/                 # 交互界面前端代码
│   ├── src/                  # React 组件及样式 
│   ├── vite.config.ts        # Vite 构建与开发端口代理配置
│   ├── nginx.conf            # 生产环境前端容器内的反向代理配置
│   └── package.json          # Node 依赖清单
└── docker-compose.yml        # 全局容器编排文件
```

## ✨ 核心特性

1. **复杂文件支持**: 全自动解析多页 PDF 文档（例如扫描的连页发票），后台自动分割为图片进行批处理。
2. **异步非阻塞**: 提交文件后前端不会处于死锁等待，通过轮询查询 Celery 状态实现进度条与实时反馈。
3. **强鲁棒性**: 对大模型偶尔输出的“不完美” JSON 数据进行自动修复（如 `{"amount": .040}` -> `{"amount": 0.04}`），保障数据有效回收。
4. **纯本地离线计算**: 所有推理与数据解析均在本地环境完成。

## 🛠️ 部署指南

### 环境依赖
- [Docker](https://docs.docker.com/get-docker/) & [Docker Compose](https://docs.docker.com/compose/install/)
- NVIDIA GPU 及对应的 [NVIDIA Container Toolkit](https://docs.nvidia.com/datacenter/cloud-native/container-toolkit/latest/install-guide.html)（用于支持 vLLM 容器使用宿主显卡做推理加速）

### 快速启动

1. **克隆项目**
   ```bash
   git clone <your-repository-url>
   cd LocalllmOcrMK2
   ```

2. **构建并启动所有服务**
   此命令将一次性启动 `vllm`, `redis`, `celery`, `backend`, 以及 `frontend` 五个容器。
   ```bash
   docker-compose up -d --build
   ```

3. **访问服务**
   - **前端交互界面**: `http://localhost:8002`
   - **后端 API 文档**: `http://localhost:8005/docs`

### 端口映射说明
- 前端 Web 界面服务映射在宿主机的 `8002` 端口。
- 后端 FastAPI 服务映射在宿主机的 `8005` 端口。
若遇到端口冲突，可直接在 `docker-compose.yml` 中修改。

## 👨‍💻 二次开发指南

- **更换 VLM 模型**: 如果需要使用如 LLaVA，Qwen-VL-Chat等其他模型，请在 `docker-compose.yml` 的 `vllm` 启动参数中修改模型路径，并视情况在 `backend/tasks.py` 中更新系统 Prompt（大模型提示词）以适配该模型的指令微调特性。
- **本地调试前端**:
  ```bash
  cd frontend
  npm install
  npm run dev
  ```

## 📄 开源协议 (License)

TBD
