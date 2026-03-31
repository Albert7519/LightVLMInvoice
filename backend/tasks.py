import os
import json
import base64
import time
import uuid
from concurrent.futures import ThreadPoolExecutor, as_completed
from dotenv import load_dotenv
from celery_app import celery_app
from PIL import Image
from openai import OpenAI
import pypdfium2 as pdfium

load_dotenv()

VLLM_API_BASE = os.getenv("VLLM_API_BASE", "http://localhost:8000/v1")
VLLM_API_KEY = os.getenv("VLLM_API_KEY", "EMPTY")
MODEL_NAME = "cyankiwi/Qwen3.5-2B-AWQ-BF16-INT8"

client = OpenAI(base_url=VLLM_API_BASE, api_key=VLLM_API_KEY)

SYSTEM_PROMPT = """你是一个严谨的发票与单据数据提取专家。
请仔细提取图中所有的发票信息，返回严格的JSON格式（不要包含任何Markdown标记和自然语言回复）：
{
  "invoices": [
    {
      "invoice_number": "发票号码(必需，如Y26A0035，若无则为null)",
      "invoice_date": "YYYY-MM-DD (若无或者是1970-01-01这种幻觉日期，则必须返回null)",
      "currency": "货币符号(如USD, RMB等)",
      "total_amount": "含税最终总金额(纯数字，如果是分页发票的小计Subtotal则请返回null，只要全发票最终的Total)",
      "vendor_name": "销方/收款方名称",
      "purchaser_name": "购买方/付款方名称",
      "items": [
        {
           "description": "商品描述表述(务必尽量包含完整料号和品名)",
           "quantity": "数量(纯数字即可)",
           "unit_price": "单价(纯数字)",
           "amount": "该行总价(纯数字)"
        }
      ]
    }
  ]
}
如果图片不是发票或没有任何有效发票信息，请返回 {"invoices": []}。
【极其重要的规则，违反将导致系统严重错误】：
1. 绝对严禁把发票底部的“TOTAL”、“PACKAGE(S)”、“总计”、“运费”等汇总统计行当做商品明细(items)提取！
2. 【禁止伪造数据】只有当图片上某一行【同时明确印有】物料品名、数量、以及【单价】时，才能算作一个合法明细放入items。如果某行（如合计行）本身在图片上【并没有印着单价】，绝对禁止你擅自拷贝上一行的单价强行补齐！直接跳过该行，不加入items！
3. 请仔细对齐每一行的列，不要错位。
4. 你当前看到的可能只是多页发票的一页片段。只有在页面末尾明确标记最终合计时，才提取到 total_amount 中，否则为 null。"""

def encode_image_base64(image_path):
    with open(image_path, "rb") as f:
        return base64.b64encode(f.read()).decode('utf-8')

@celery_app.task(bind=True)
def process_invoice_task(self, file_path: str, filename: str):
    self.update_state(state='PROCESSING', meta={'progress': 10, 'message': f'开始处理 {filename}'})
    
    ext = os.path.splitext(file_path)[1].lower()
    image_paths = []
    
    if ext == '.pdf':
        self.update_state(state='PROCESSING', meta={'progress': 20, 'message': '检测到PDF，正在分页渲染...'})
        pdf = pdfium.PdfDocument(file_path)
        for i in range(len(pdf)):
            page = pdf.get_page(i)
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
        
    self.update_state(state='PROCESSING', meta={'progress': 30, 'message': f'文件拆分为 {len(image_paths)} 张图像，即将启动多线程并发提取（Qwen3.5)'})

    def fetch_page(idx, path):
        base64_img = encode_image_base64(path)
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
            extra_body={"top_k": 20, "repetition_penalty": 1.0}
        )
        content = response.choices[0].message.content
        if "```json" in content:
            content = content.split("```json")[-1].split("```")[0]
        elif "```" in content:
            content = content.split("```")[-1].split("```")[0]
        return idx, json.loads(content.strip())

    page_results = []
    completed = 0
    # 我们有vLLM高并发加持，可以直接开多个Worker同时发起请求
    with ThreadPoolExecutor(max_workers=5) as executor:
        futures = {executor.submit(fetch_page, i, p): i for i, p in enumerate(image_paths)}
        for future in as_completed(futures):
            completed += 1
            curr_prog = 30 + int(60 * completed / len(image_paths))
            self.update_state(state='PROCESSING', meta={'progress': curr_prog, 'message': f'底层并发推理中... ({completed}/{len(image_paths)})'})
            try:
                page_results.append(future.result())
            except Exception as e:
                print(f"执行推理失败: {str(e)}")

    page_results.sort(key=lambda x: x[0])

    # 跨页合并聚合逻辑（按发票号智能分组）
    merged_invoices = {}
    for _, page_data in page_results:
        for inv in page_data.get("invoices", []):
            inv_no = inv.get("invoice_number")
            if not inv_no or str(inv_no).lower() == 'null':
                inv_no = f"未命名片段_{str(uuid.uuid4())[:6]}"
                
            if inv_no not in merged_invoices:
                merged_invoices[inv_no] = inv
                if not merged_invoices[inv_no].get("items"):
                    merged_invoices[inv_no]["items"] = []
                # 初始过滤 1970-01-01
                if str(merged_invoices[inv_no].get("invoice_date")).strip() == "1970-01-01":
                    merged_invoices[inv_no]["invoice_date"] = None
            else:
                if inv.get("items"):
                    merged_invoices[inv_no]["items"].extend(inv["items"])
                for k in ["invoice_date", "currency", "vendor_name", "purchaser_name"]:
                    if str(inv.get(k, "")).strip() == "1970-01-01":
                        continue
                    if not merged_invoices[inv_no].get(k) and inv.get(k):
                        merged_invoices[inv_no][k] = inv[k]

                # 特殊处理总金额：如果后续页面的总金额更大（考虑到小计<总计），则覆盖
                if inv.get("total_amount"):
                    old_amt_str = str(merged_invoices[inv_no].get("total_amount") or "0")
                    new_amt_str = str(inv.get("total_amount") or "0")
                    import re
                    def parse_amt(s):
                        d = re.sub(r'[^\d\.]', '', s)
                        try: return float(d) if d else 0.0
                        except: return 0.0
                    if parse_amt(new_amt_str) > parse_amt(old_amt_str):
                        merged_invoices[inv_no]["total_amount"] = inv["total_amount"]

    self.update_state(state='PROCESSING', meta={'progress': 95, 'message': '结构化分析完成，数据聚合完毕。'})
    
    return {
        "file_name": filename,
        "page_count": len(image_paths),
        "invoices": list(merged_invoices.values())
    }
