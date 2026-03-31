# VLM 发票识别系统

这是一个基于本地视觉大模型（VLM）的发票识别提取系统。主要针对扫描件、多张发票合并的 PDF 等复杂的版式，通过 VLM 直接读取并结构化提取关键信息（金额、税号、时间等）。

## 架构

* **前端**: React + Vite + TailwindCSS (运行端口: 8002)
* **后端**: FastAPI + Celery + Redis (运行端口: 8005)
* **模型推理**: 基于 vLLM 引擎部署（当前推荐配置 Qwen 等小参数模型，兼顾显存和速度）

## 主要功能

* 支持上传多页 PDF 以及各种图片格式。
* 基于 Celery 的异步任务队列进行分页解析，并使用 `json_repair` 对大模型的输出结果做增强容错，基本不会丢数据。
* 提供极简的前后端分离界面，上传和预览无缝衔接。

## 部署与启动

环境要求：系统需要安装 Docker 和 Docker Compose。如果有显卡，请先装好 NVIDIA Container Toolkit。

1. **拉取代码**：
```bash
git clone https://github.com/your-username/your-repo-name.git
cd your-repo-name
```

2. **一键启动**：
```bash
docker-compose up -d --build
```

3. **访问系统**：
服务会在后台启动。打开浏览器访问: `http://localhost:8002`

## 二次开发

- 核心的大语言模型（VLM） Prompt 写在 `backend/tasks.py` 里。如果换了其他系列的模型，可以酌情修改以对齐它的识别逻辑。
- 要改前端界面直接在 `frontend/` 下面搞就可以了，`npm dev` 一键起开发服务器。

## 协议 (License)

待定 (TBD)
