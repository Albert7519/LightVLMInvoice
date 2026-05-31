# VLM 发票识别系统 (LightVLMInvoice)

[English](README.md) | [中文](README.zh-CN.md)

基于本地视觉大语言模型 (Vision Large Language Model) 的文档/发票结构化信息提取系统。本项目旨在通过本地部署的 VLM 直接对复杂版式（包含多页复合 PDF 或单张图片）进行解析，无需依赖外部 API，保障业务数据的隐私与资产安全。

## 项目价值

许多小团队、学生和个人开发者都需要发票或文档 OCR，但托管 OCR API 往往成本较高、不易定制，或者不适合处理敏感财务文档。LightVLMInvoice 提供了一套完全本地化、Docker 化的 VLM 文档抽取流程，包含异步处理、JSON 修复、可配置并发，以及清晰的全栈项目结构。

本项目希望成为一个可复现的开源参考：用户可以在本地运行抽取流程，按需调整提示词和模型，并完整检查后端、任务队列、前端和部署栈。

## 架构与技术栈

系统采用前后端分离架构，核心处理流程结合了异步任务队列以应对大模型高耗时推理的特性。

- **前端 (Frontend)**: React + Vite + TypeScript + TailwindCSS。生产环境通过 Nginx 运行代理。
- **后端 (Backend)**: FastAPI (高并发 HTTP 框架)。
- **任务调度**: Celery + Redis（用于隔离长耗时的页面切割和 VLM 推理任务）。
- **推理引擎**: 基于 vLLM 部署的本地视觉大模型，系统当前默认内置使用 `cyankiwi/Qwen3.5-2B-AWQ-BF16-INT8` 量化模型，兼具较低的显存占用与较强的版式识别能力。
- **容错增强**: 使用 `json_repair` 防止因模型输出偶发的 JSON 语法错误（如缺少引号、截断等）导致的数据丢弃。

## 项目结构

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
├── docker/                   # 容器化部署与统筹目录
│   ├── docker-compose.yml    # 全局容器编排文件
│   ├── backend.Dockerfile    # 后端环境构建镜像打包配置
│   └── frontend.Dockerfile   # 前端环境构建镜像打包配置
└── .env.example              # 环境变量配置模板
```

## 核心特性

1. **复杂文件支持**: 全自动解析多页 PDF 文档（例如扫描的连页发票），后台自动分割为图片进行批处理。
2. **异步非阻塞**: 提交文件后前端不会处于死锁等待，通过轮询查询 Celery 状态实现进度条与实时反馈。
3. **强鲁棒性**: 对大模型偶尔输出的“不完美” JSON 数据进行自动修复（如 `{"amount": .040}` -> `{"amount": 0.04}`），保障数据有效回收。
4. **纯本地离线计算**: 所有推理与数据解析均在本地环境完成。

## 部署指南

### 环境依赖

- [Docker](https://docs.docker.com/get-docker/) & [Docker Compose](https://docs.docker.com/compose/install/)
- NVIDIA GPU 及对应的 [NVIDIA Container Toolkit](https://docs.nvidia.com/datacenter/cloud-native/container-toolkit/latest/install-guide.html)（用于支持 vLLM 容器使用宿主显卡做推理加速）

### 快速启动

1. **克隆项目**

   ```bash
   git clone https://github.com/Albert7519/LightVLMInvoice.git
   cd LightVLMInvoice
   ```

2. **构建并启动所有服务**

   此命令将一次性启动 `vllm`, `redis`, `celery`, `backend`, 以及 `frontend` 五个容器。

   ```bash
   cd docker
   docker-compose up -d --build
   ```

3. **访问服务**

   - **前端交互界面**: `http://localhost:8002`
   - **后端 API 文档**: `http://localhost:8005/docs`

### 端口映射说明

- 前端 Web 界面服务映射在宿主机的 `${FRONTEND_PORT:-8002}` 端口。
- 后端 FastAPI 服务映射在宿主机的 `${BACKEND_PORT:-8005}` 端口。

若遇到端口冲突，可直接通过根目录的 `.env` 文件设定新端口隔离。

### 高级配置与并发调优

本项目将影响性能与环境的参数统一抽离为 `.env` 环境变量：

```bash
cp .env.example .env
```

核心配置：

- `CELERY_CONCURRENCY=2`：多文件并发处理数。默认值为 `1`，显存大于 16 GB 时可尝试设为 `2` 或更高。
- `MAX_CONCURRENT_PAGES=10`：单份发票文件内部最大解拆并发线程，例如同时并行处理 10 页 PDF。
- `VLLM_MODEL=cyankiwi/Qwen3.5-2B-AWQ...`：vLLM 服务加载的模型，可换用 LLaVA 等兼容 VLM。
- `VLLM_GPU_MEMORY_UTILIZATION=0.8`：调节 GPU 显存占用比例。
- `VLLM_MAX_MODEL_LEN=8192`：最大上下文处理长度，降低此值可换取更多并发可用显存。

## 二次开发指南

- **更换 VLM 模型**: 如果需要使用如 LLaVA 等其他模型，除了通过 `.env` 修改模型名称外，可能需要视情况在 `backend/tasks.py` 中更新系统 Prompt（大模型提示词）以适配该模型的指令微调格式。
- **本地调试前端**:

  ```bash
  cd frontend
  npm install
  npm run dev
  ```

## OSS 维护流程

本仓库按开源项目方式维护，计划覆盖以下维护流程：

- 针对部署、解析、模型输出和前端问题进行 issue triage；
- 使用脱敏或合成样例文件复现 bug；
- 对 FastAPI 后端、Celery worker、Docker 配置和 React 前端代码进行 PR review；
- 为用户可见行为、部署变化、模型或提示词变化编写 release notes；
- 持续完善本地部署、隐私约束和模型替换相关文档。

## Roadmap

- 添加合成发票样例和对应结构化输出。
- 为 PDF 拆分、图片转换、JSON 修复和 API 响应添加自动化测试。
- 添加更严格的输出 schema 校验。
- 改进前端错误展示和批处理状态显示。
- 文档化不同 GPU 显存下推荐的 vLLM 设置。
- 持续发布带 changelog 的 tagged releases。

## 开源协议

本项目使用 MIT License。详情见 [LICENSE](LICENSE)。
