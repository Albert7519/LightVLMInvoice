import os
import io
import uuid
import pandas as pd
from typing import List
from dotenv import load_dotenv
from fastapi import FastAPI, UploadFile, File, HTTPException, Request
from fastapi.responses import StreamingResponse
from fastapi.middleware.cors import CORSMiddleware
from celery.result import AsyncResult
from celery_app import celery_app
from tasks import process_invoice_task

# Load environment variables from .env file
load_dotenv()

app = FastAPI(
    title="智能发票混合识别系统 API",
    description="基于 Qwen3.5 VLM 的发票 OCR 识别",
    version="1.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 确保文件上传目录存在
UPLOAD_DIR = os.path.join(os.path.dirname(__file__), "uploads")
os.makedirs(UPLOAD_DIR, exist_ok=True)

@app.post("/api/v1/invoices/extract")
async def extract_invoices(files: List[UploadFile] = File(...)):
    """接收并落盘上传的发票，调度给 Celery 队列异步处理"""
    task_ids = []
    for file in files:
        file_id = str(uuid.uuid4())
        file_ext = os.path.splitext(file.filename)[1]
        file_path = os.path.join(UPLOAD_DIR, f"{file_id}{file_ext}")
        
        with open(file_path, "wb") as f:
            content = await file.read()
            f.write(content)
            
        # delay() 异步发起Celery任务
        task = process_invoice_task.delay(file_path, file.filename)
        task_ids.append(task.id)
        
    return {
        "code": 200,
        "message": "Tasks queued successfully",
        "data": {
            "task_ids": task_ids
        }
    }

@app.get("/api/v1/invoices/status/{task_id}")
async def get_task_status(task_id: str):
    """轮询任务进度，返回最终结果或当前执行比例"""
    res = AsyncResult(task_id, app=celery_app)
    
    if res.state == 'PENDING':
        return {"code": 200, "status": "PENDING", "progress": 0, "result": None}
    elif res.state == 'PROCESSING':
        info = res.info or {}
        return {
            "code": 200, 
            "status": "PROCESSING", 
            "progress": info.get('progress', 0), 
            "message": info.get('message', ''), 
            "result": None
        }
    elif res.state == 'SUCCESS':
        return {"code": 200, "status": "COMPLETED", "progress": 100, "result": res.result}
    else:
        # 抛出具体的异常信息追踪
        return {"code": 500, "status": "FAILED", "progress": 0, "result": str(res.info)}

@app.post("/api/v1/invoices/export")
async def export_invoices(request: Request):
    """接收前端核实后的发票 JSON，生成结构化 Excel 表格(Excel 流) 下载"""
    invoice_data = await request.json()
    try:
        rows = []
        for task_res in invoice_data:
            invoices = task_res.get("invoices", [])
            for data in invoices:
                base_row = {
                    "原文件名称": task_res.get("file_name", ""),
                    "发票号码": data.get("invoice_number", ""),
                    "发票日期": data.get("invoice_date", ""),
                    "销售方(收款)": data.get("vendor_name", ""),
                    "购买方(付款)": data.get("purchaser_name", ""),
                    "货币": data.get("currency", ""),
                    "总含税金额": data.get("total_amount", ""),
                }
                items = data.get("items", [])
                if not items:
                    rows.append(base_row)
                else:
                    for item in items:
                        row = base_row.copy()
                        row.update({
                            "商品名称": item.get("description", ""),
                            "数量": item.get("quantity", ""),
                            "单价": item.get("unit_price", ""),
                            "金额": item.get("amount", "")
                        })
                        rows.append(row)
                    
        df = pd.DataFrame(rows)
        stream = io.BytesIO()
        with pd.ExcelWriter(stream, engine='openpyxl') as writer:
            df.to_excel(writer, index=False, sheet_name='发票提取明细')
            
        stream.seek(0)
        headers = {
            'Content-Disposition': 'attachment; filename="invoices_export.xlsx"'
        }
        return StreamingResponse(stream, headers=headers, media_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
