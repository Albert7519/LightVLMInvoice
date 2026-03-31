import os
import json
import base64
import time
from dotenv import load_dotenv
from celery_app import celery_app
from PIL import Image
from openai import OpenAI
import pypdfium2 as pdfium

# Load environment variables from .env file
load_dotenv()

# vLLM ModelScope 本地/局域网服务调用配置
VLLM_API_BASE = os.getenv("VLLM_API_BASE", "http://localhost:8000/v1")
VLLM_API_KEY = os.getenv("VLLM_API_KEY", "EMPTY")
MODEL_NAME = "cyankiwi/Qwen3.5-2B-AWQ-BF16-INT8"

client = OpenAI(base_url=VLLM_API_BASE, api_key=VLLM_API_KEY)

SYSTEM_PROMPT = """你是一个极其专业的全球多语种发票OCR解析专家。
请严格按照以下JSON格式返回结果，不包含任何外部 markdown 标签或自然语言回复：
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
如果某个特定字段在图片内部找不到，请赋值为 null。"""

def encode_image_base64(image_path):
    with open(image_path, "rb") as f:
        return base64.b64encode(f.read()).decode('utf-8')

@celery_app.task(bind=True)
def process_invoice_task(self, file_path: str, filename: str):
    self.update_state(state='PROCESSING', meta={'progress': 10, 'message': f'开始处理 {filename}'})
    
    ext = os.path.splitext(file_path)[1].lower()
    image_paths = []
    
    # === 阶段 1：解析文件 (PDF -> Images) ===
    if ext == '.pdf':
        self.update_state(state='PROCESSING', meta={'progress': 20, 'message': '检测到PDF，正在并行分页渲染并转换为高精度图片...'})
        pdf = pdfium.PdfDocument(file_path)
        for i in range(len(pdf)):
            page = pdf.get_page(i)
            # scale=2 提供 2x 的图片清晰度，控制尺寸在多模态上限下
            bitmap = page.render(scale=2, rotation=0, crop=(0, 0, 0, 0))
            pil_image = bitmap.to_pil()
            img_path = f"{file_path}_page_{i}.jpg"
            pil_image.save(img_path, "JPEG")
            image_paths.append(img_path)
            page.close()
        pdf.close()
    elif ext in ['.jpg', '.jpeg', '.png', '.webp']:
        image_paths.append(file_path)
    else:
        raise ValueError(f"不受支持的文件类型: {ext}")
        
    self.update_state(state='PROCESSING', meta={'progress': 30, 'message': f'文件拆分为 {len(image_paths)} 张独立图像。即将移交 VLM (Qwen3.5)'})

    # === 阶段 2：大模型并发推理与提取 ===
    aggregated_data = {
        "invoice_number": None,
        "invoice_date": None,
        "currency": None,
        "total_amount": None,
        "vendor_name": None,
        "purchaser_name": None,
        "items": []
    }
    
    for idx, img_path in enumerate(image_paths):
        # 计算进度条平滑滑动比例
        base_prog = 30
        curr_prog = base_prog + int(60 * (idx+1)/len(image_paths))
        self.update_state(state='PROCESSING', meta={'progress': curr_prog, 'message': f'底层 GPU 模型识别第 {idx+1}/{len(image_paths)} 页...'})
        
        base64_img = encode_image_base64(img_path)
        
        try:
            # 向 vLLM Qwen 发送带指定严控参数（Non-thinking mode）的任务
            response = client.chat.completions.create(
                model=MODEL_NAME,
                messages=[
                    {
                        "role": "user",
                        "content": [
                            {"type": "text", "text": SYSTEM_PROMPT},
                            {"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{base64_img}"}}
                        ]
                    }
                ],
                max_tokens=4096,
                temperature=0.7,        
                top_p=0.8,              
                presence_penalty=1.5,
                frequency_penalty=0.0,
                extra_body={
                    "top_k": 20,        
                    "repetition_penalty": 1.0  
                }
            )
            
            content = response.choices[0].message.content
            # NLP 后处理：清洗可能残留的 ```json markdown 包裹符号
            if "```json" in content:
                content = content.split("```json")[-1].split("```")[0]
            elif "```" in content:
                content = content.split("```")[-1].split("```")[0]
                
            page_data = json.loads(content.strip())
            
            # 跨页合并聚合逻辑
            for k in ["invoice_number", "invoice_date", "currency", "total_amount", "vendor_name", "purchaser_name"]:
                if not aggregated_data[k] and page_data.get(k):
                    aggregated_data[k] = page_data[k]
                    
            if page_data.get("items"):
                aggregated_data["items"].extend(page_data["items"])
                
        except Exception as e:
            # 兼容：如果遇到一页损坏，可以抛出错误但在合并中选择性允许单页缺省
            print(f"执行多模态推理失败 [页码 {idx+1}]: {str(e)}")

    self.update_state(state='PROCESSING', meta={'progress': 95, 'message': '全部拆切页结构化合并完成。'})
    
    # 若有清理需求可释放临时盘
    # for p in image_paths:
    #     if p != file_path and os.path.exists(p):
    #         os.remove(p)
            
    return {
        "file_name": filename,
        "page_count": len(image_paths),
        "invoice_data": aggregated_data
    }
