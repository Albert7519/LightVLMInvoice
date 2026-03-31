# 智能发票混合识别系统 - 交付与验收指引

> [!TIP]
> 您的项目架构和主程序已经 100% 建设完毕！系统完全采纳了异步高并发设计，前后端代码全部部署于您的工作区 `LocalllmOcrMK2` 目录下。本文档将指引您在本地启动该整套服务系统并进行验收测试。

## 1. 系统模块总结

您当前环境已具备以下核心模块：
* **模型服务 (vLLM)**: 需要独立启动，提供 OpenAI API 兼容端口。
* **计算队列 (Redis)**: 用于消息分发与任务状态缓存。
* **后端 API网关 (FastAPI)**: 在 `backend/` 下，暴露 HTTP 终点接收文件提交与前端轮询。
* **异步工作者 (Celery Worker)**: 在 `backend/` 下，拉取文件，调用 `pypdfium2` 分拆 PDF 图片，再多线程发给模型提取。
* **前端 Web (React + Vite)**: 在 `frontend/` 下，极具科技感的毛玻璃效果界面，并支持 Excel 实时导出。

---

## 2. 环境配置与启动说明

请打开终端（推荐准备至少 4 个相互独立的控制台窗口）按照以下顺序依次启动。

### Step 1: 启动 Redis
请确保您的机器已经安装并启动了 Redis 数据库（监听于默认端口 `6379`）。
* Windows 可以通过 WSL 启动或下载原生绿色版启动 `redis-server.exe`。

### Step 2: 启动底层大脑 ModelScope Qwen vLLM 服务
准备一个搭载 GPU 的终端环境：
```bash
export VLLM_USE_MODELSCOPE=true
# 设置量化大模型推理引擎
python -m vllm.entrypoints.openai.api_server \
    --model "cyankiwi/Qwen3.5-2B-AWQ-BF16-INT8" \
    --host 0.0.0.0 \
    --port 8000 \
    --gpu-memory-utilization 0.9 \
    --max-model-len 32768
```
*(注意：首次启动会自动通过 ModelScope 连接 HuggingFace 镜像源拉取模型权重。)*

### Step 3: 启动 Backend API 与 Celery Worker
新开终端，切换到项目 backend 目录并安装依赖：
```bash
cd backend
pip install -r requirements.txt
```

**窗口 A - 启动 Celery Worker**:
```bash
# 启动处理发票图片与调用大模型的后台进程
python -m celery -A celery_app worker --loglevel=info --pool=solo
```

**窗口 B - 启动 FastAPI 网关**:
```bash
# 默认映射在 8080 端口（防止与上面 8000 的大模型冲突）
uvicorn main:app --host 0.0.0.0 --port 8080 --reload
```
*(如果您发现前端的调用接口改变，可以进入 frontend/src/App.tsx 修改 API_BASE )*

### Step 4: 启动 Frontend 视觉终端
新开终端，进入 frontend 文件夹：
```bash
cd frontend

# 若上一步 npm install 执行不完整导致依赖缺漏，可再运行一次：
npm install

# 启动 Vite 开发服务
npm run dev
```
前端默认将在 `http://localhost:5173/` 提供服务。

---

## 3. 验收指南 (Verification)

> [!IMPORTANT]
> **您重点需要测试的内容：**

1. **界面体验测试**: 打开 `http://localhost:5173/`。尝试拖拽一张复杂的多行明细发票图片（或多页PDF）至网页左侧的虚线框。
2. **状态轮询测试**: 点击 `开始 AI 智能识别` 后，观察界面的扫描雷达样式加载条是否跟随 Celery 后台的状态更新动态从 10% 推进至 100%。
3. **Qwen 非思考模式验证**: 结果渲染期间，VLM 会严格利用我们传入的 `temperature=0.7`, `top_k=20`, `repetition_penalty=1.0` 等参数直接抛出纯粹 JSON 数据。观察是否不再引发大段的多余闲聊，右侧面板能瞬间结构化渲染出各项明细。
4. **Excel 导出测试**: 数据渲染于右侧后，点击右上角的 `导出 Excel`。检查您的下载文件夹，核实一份包含了所有项目明细数组摊平的结构化报表是否按期生成。

至此，您的开源智能发票系统（支持 Excel 下载、支持 PDF 和多模态 Qwen API、支持纯真科技风 UI）正式交付！
