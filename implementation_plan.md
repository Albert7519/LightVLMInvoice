# 智能发票混合识别系统 (AI Invoice OCR System) - 开发文档

> [!NOTE]
> 本文档定义了一个基于大型视觉语言模型（VLM）的开源发票识别系统的完整架构。系统专门针对多页PDF、复杂混合图像以及多国不同语种版式设计，并通过异步架构支持高并发场景。

## 1. 项目概述

构建一个企业级的、开源的Web发票数据自动提取系统。系统利用最前沿的量化多模态大模型 `cyankiwi/Qwen3.5-2B-AWQ-BF16-INT8` 直接理解发票图像和文档规律，替代传统繁杂的版面分析（Layout Analysis）和OCR规则适配模式，从根本上解决“多国”、“多版式”、“多页”的痛点。

### 1.1 核心能力
* **多格式兼容**：支持 `PDF`（单页/多页）、`JPG`、`PNG`、`WebP` 等主流格式。
* **多语言与跨国发票**：模型原生支持多语种跨文化理解，支持中、英、日、韩及欧洲等多国发票混合识别。
* **高并发处理**：采用 `FastAPI + Celery + Redis` 架构，支持多文件打包上传与并发排队识别。
* **极简私有化部署**：模型小巧（2B参数量，经过AWQ INT8量化与BF16激活），单张中端显卡（如 RTX 3060/4060 8GB）即可流畅进行推理。
* **在线实时预览**：内置文档渲染器（前端集成 PDF.js 或原生的图片渲染工具），支持原生发票画面与右侧提取结果的同屏双向校对。
* **Excel 一键导出**：支持将单张提取结果或批量多发票数据汇总后，一键生成结构化的 Excel (`.xlsx`) 文件进行本地归档与财务做账。

## 2. 系统架构设计

本系统采用经典的前后端分离+异步任务调度的微服务架构。

```mermaid
graph TD
    subgraph Frontend [前端 Web UI]
        UI[Vue3 / React 界面]
        Upload[文件拖拽与预处理组件]
        Preview[PDF/图片预览引擎]
    end

    subgraph Backend [后端 API 核心层]
        API[FastAPI 网关]
        Storage[(文件系统/S3)]
        Redis[(Redis 消息中间件)]
    end

    subgraph Worker [异步计算集群]
        Celery[Celery Worker 集群]
        PDFium[pypdfium2 PDF分页渲染]
    end

    subgraph ModelServing [vLLM 模型推理服务]
        vLLM[vLLM OpenAI Compatible Server]
        Qwen[Qwen3.5-2B-AWQ-BF16-INT8 (ModelScope)]
    end

    UI -- HTTP POST / 多文件 --> API
    API --> Storage
    API -- 分发任务ID --> Redis
    Redis <-- 拉取排队任务 --> Celery
    Celery -- 拆解多页PDF转Image --> PDFium
    Celery -- 多模态Prompt --> vLLM
    vLLM --> Qwen
    Celery -- 写入解析结果 (JSON) --> Storage/Redis
    UI -- 轮询拉取状态 --> API
```

### 2.1 技术栈选型
* **前端 (Frontend)**: Vue 3 / React + TailwindCSS + Vite (强调极致、动态的交互体验)。
* **后端 (Backend)**: Python 3.11+, FastAPI (高性能异步网关)。
* **中间件 (Middleware)**: Celery (分布式任务队列), Redis (消息代理与状态缓存)。
* **文档处理工具**: `pypdfium2` (目前生态中速度极快且依赖最干净的PDF转图方案)。
* **模型服务引擎**: vLLM (支持 AWQ 极致加速，原生适配 OpenAI API 标准格式)。
* **模型来源**: ModelScope (魔搭社区，国内网络下极速下载体验)。

## 3. 模型部署方案 (ModelScope + vLLM)

> [!IMPORTANT]
> 系统强制要求使用 `vLLM` 部署多模态大模型。相较于原生 HuggingFace 部署，vLLM 能提供 PagedAttention 显存优化和极高的吞吐量。

### 3.1 环境准备与安装
首先配置支持 vLLM 的 Python 虚拟环境：
```bash
# 推荐使用 uv 或者 pip 安装最新版 vllm
pip install vllm --torch-backend=auto
# 安装 modelscope 库以便按需下载
pip install modelscope
```

### 3.2 启动 vLLM 推理服务 (使用 ModelScope)
为了直接从 ModelScope 下载该 AWQ 量化模型，需要配置环境变量 `VLLM_USE_MODELSCOPE`。

创建一个启动脚本 `start_vllm.sh`：
```bash
#!/bin/bash
# 声明使用 ModelScope 源替代 HuggingFace
export VLLM_USE_MODELSCOPE=true

# 启动兼容 OpenAI 格式的 API Server
# cyankiwi/Qwen3.5-2B-AWQ-BF16-INT8 会被 vLLM 自动识别为 AWQ 并正确加载
python -m vllm.entrypoints.openai.api_server \
    --model "cyankiwi/Qwen3.5-2B-AWQ-BF16-INT8" \
    --host 0.0.0.0 \
    --port 8000 \
    --gpu-memory-utilization 0.9 \
    --max-model-len 32768
```
*提示：该模型在 ModelScope 上的生态若未完全同步 cyankiwi 仓库，可自行通过 MS 提供的接口上传或拉取，一般情况下镜像均完整匹配。*

## 4. 核心业务流程：文档解析策略

### 4.1 多页 PDF 处理策略
由于大语言模型的多图输入对显存占用巨大且容易引起“幻觉”遗忘，本系统采用 **按页切割渲染 + 独立/合并处理** 的策略。

1. 用户上传 `invoice.pdf` (例如 3 页)。
2. 后端接收并存放至 `/tmp/files/`，将文件路径加入 Celery 队列。
3. Celery Worker 拾取任务后，使用 `pypdfium2` 单页循环渲染：
```python
import pypdfium2 as pdfium

def process_pdf(pdf_path, output_dir):
    pdf = pdfium.PdfDocument(pdf_path)
    image_paths = []
    for i in range(len(pdf)):
        page = pdf.get_page(i)
        # 推荐使用 2-3 的 scale (大约 144-216 DPI)，权衡 OCR 清晰度与大模型输入 token 成本
        image = page.render_topil(scale=2, rotation=0, crop=(0, 0, 0, 0))
        path = f"{output_dir}/page_{i}.jpg"
        image.save(path, "JPEG")
        image_paths.append(path)
    return image_paths
```

### 4.2 基于 Qwen3.5 的 Prompt 工程 (Prompt Engineering)

利用 vLLM 提供的 OpenAI Schema 接口发起请求。为实现精准识别，系统定义了如下 System Prompt，要求其必须返回 JSON。

```python
from openai import OpenAI

# 连接已部署的本地 vLLM 服务
client = OpenAI(base_url="http://localhost:8000/v1", api_key="EMPTY")

prompt = """
你是一个极其专业的全球多语种发票OCR解析专家。
请识别我提供的发票图像，并严格按照以下JSON格式返回结果，禁止输出任何其他解释性文本：
{
  "invoice_number": "发票号码",
  "invoice_date": "YYYY-MM-DD",
  "currency": "货币符号或代码",
  "total_amount": "含税总金额(纯数字)",
  "vendor_name": "收款方/商家名称",
  "purchaser_name": "付款方/购买人名称",
  "items": [
      {
         "description": "商品描述",
         "quantity": "数量",
         "unit_price": "单价",
         "amount": "总价"
      }
  ]
}
如果某个字段在发票中找不到，请赋值为 null。
"""

# 请求构建 (以单页图片为例进行 Base64 编码传入)
# 重要：关闭 Qwen3.5 的思考模式，确保原生稳定的 JSON 输出
# 官方针对 VL (视觉任务) 的非思考模式（Non-thinking mode）参数推荐如下：
response = client.chat.completions.create(
    model="cyankiwi/Qwen3.5-2B-AWQ-BF16-INT8",
    messages=[
        {
            "role": "user",
            "content": [
                {"type": "text", "text": prompt},
                {"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{base64_image}"}}
            ]
        }
    ],
    max_tokens=4096,
    temperature=0.7,        # Non-thinking 模式建议的 VL 任务温度
    top_p=0.8,              # Non-thinking 模式建议的 VL 任务 top_p
    presence_penalty=1.5,   # Non-thinking 模式建议的 presence_penalty
    frequency_penalty=0.0,
    extra_body={
        "top_k": 20,         # Non-thinking 模式建议的 top_k
        "repetition_penalty": 1.0  # 确保不增加无端的重复惩罚
    }
)
# 注意：实际生产中应当使用 AsyncOpenAI 的异步调用方法避免阻塞 Celery Worker
```

> [!TIP]
> **多页关联聚合**: 对于分页的发票图像，分别对每页发起推理。后端在获取所有页的 JSON 数组后，进行数据拍平（Flatten），例如对长列表的 `items` 进行跨页合并，最后输出一份最终聚合版 JSON 给前端。

## 5. RESTful API 接口设计

### 5.1 提交解析任务
**POST** `/api/v1/invoices/extract`
* **Content-Type**: `multipart/form-data`
* **参数**:
  * `files`: List[File] (支持多选文件)
* **响应** (202 Accepted):
```json
{
  "code": 200,
  "message": "任务已提交队列",
  "data": {
    "task_ids": ["uuid-1", "uuid-2"]
  }
}
```

### 5.2 轮询/Webhook 查询识别结果
**GET** `/api/v1/invoices/status/{task_id}`
* **响应**:
```json
{
  "code": 200,
  "status": "COMPLETED",  // PENDING, PROCESSING, COMPLETED, FAILED
  "progress": 100,
  "result": {
    "file_name": "apple_receipt_2026.pdf",
    "page_count": 2,
    "invoice_data": { 
       // 聚合后的结构化 JSON 
    }
  }
}
```

### 5.3 批量导出 Excel
**POST** `/api/v1/invoices/export`
* **Content-Type**: `application/json`
* **说明**: 前端将核对无误的一张或多张发票的 JSON 数据体发到此接口，后端使用 `pandas` 根据财务需要的表头映射迅速生成二进制的 `.xlsx` 文件流，允许用户直接点击下载。

## 6. 用户体验设计(UX/UI 规范)

前文要求我们建立一套非常高端（Wow!）的前端界面。
* **色彩系统**: 倾向暗黑科技风（Sleek Dark Mode），或带有柔和毛玻璃（Glassmorphism）质感的现代蓝紫色调。
* **微交互**: 上传区需具备粒子吸附动画，PDF解析时呈现逐级进度条或类似雷达扫描的动画效果。
* **数据展示**: VLM 提取后的结果不应只是一段生硬的 JSON，而应该呈现为可编辑、高亮对应原图位置的「双屏对校」界面。左侧为可缩放滚动的发票图，右侧为优雅的 Form 表单结构。

## 7. 后续规划评估

### 需要您确认 (User Review Required)
> [!CAUTION]
> 1. **ModelScope 源确认**: 系统已配置通过 `VLLM_USE_MODELSCOPE=true` 利用 ModelScope 拉取 `Qwen3.5-2B-AWQ-BF16-INT8`。您是否已经配置好了相关的网络及硬件（至少显存需 6-8 GB）？
> 2. **前端选型**: 本文档默认优先考虑采用 **React** 构建具有强烈动态视觉的交互界面。是否符合您的技术栈偏好？
> 3. **结果保存**: 提取的 JSON 是否需要持久化到关系型数据库（如 PostgreSQL/MySQL）？当前设计为仅作展示，不长久存储。

如果以上架构和方案满足要求，请给予确认。我将可以进一步协助您生成骨架代码（包括 FastAPI API 结构和 Celery 任务代码）。
