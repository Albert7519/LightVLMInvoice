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
    """接收前端核实后的发票 JSON，生成结构化双表 Excel 表格(Excel 流) 下载"""
    invoice_data = await request.json()
    try:
        summary_rows = []
        detail_rows = []
        
        for task_res in invoice_data:
            invoices = task_res.get("invoices", [])
            for data in invoices:
                inv_no = data.get("invoice_number", "")
                # 主表数据 (每一张发票一条主表记录)
                summary_rows.append({
                    "原文件名称": task_res.get("file_name", ""),
                    "发票号码": inv_no,
                    "发票日期": data.get("invoice_date", ""),
                    "销售方(收款)": data.get("vendor_name", ""),
                    "购买方(付款)": data.get("purchaser_name", ""),
                    "货币": data.get("currency", ""),
                    "总含税金额": data.get("total_amount", ""),
                })
                
                # 明细表数据 (发票内包含的各种明细内容)
                items = data.get("items", [])
                if items:
                    for item in items:
                        detail_rows.append({
                            "归属发票号码": inv_no,
                            "原文件名称": task_res.get("file_name", ""),
                            "商品名称": item.get("description", ""),
                            "数量": item.get("quantity", ""),
                            "单价(不含/含税)": item.get("unit_price", ""),
                            "明细总金额": item.get("amount", "")
                        })

        df_summary = pd.DataFrame(summary_rows)
        # 如果没有明细数据，依然提供具有正确表头的空白明细表
        if not detail_rows:
            df_details = pd.DataFrame(columns=["归属发票号码", "原文件名称", "商品名称", "数量", "单价(不含/含税)", "明细总金额"])
        else:
            df_details = pd.DataFrame(detail_rows)

        stream = io.BytesIO()
        with pd.ExcelWriter(stream, engine='openpyxl') as writer:
            df_summary.to_excel(writer, index=False, sheet_name='发票汇总表')
            df_details.to_excel(writer, index=False, sheet_name='商品明细表')
            
            # 简单的列宽自适应
            workbook = writer.book
            
            # 调整发票汇总表列宽
            ws_summary = writer.sheets['发票汇总表']
            for col in ws_summary.columns:
                max_length = 0
                column = col[0].column_letter
                for cell in col:
                    try:
                        # 对于由于包含中文字符导致计算有些偏差的情况，乘以 1.5 缓冲一下
                        cell_len = len(str(cell.value).encode('gbk')) if cell.value else 0
                        if cell_len > max_length:
                            max_length = cell_len
                    except:
                        pass
                adjusted_width = min(max_length + 2, 60) # 设置一个最大宽度60，防止无限拉长
                ws_summary.column_dimensions[column].width = adjusted_width
                
            # 调整商品明细表列宽
            ws_details = writer.sheets['商品明细表']
            for col in ws_details.columns:
                max_length = 0
                column = col[0].column_letter
                for cell in col:
                    try:
                        cell_len = len(str(cell.value).encode('gbk')) if cell.value else 0
                        if cell_len > max_length:
                            max_length = cell_len
                    except:
                        pass
                adjusted_width = min(max_length + 2, 80)
                ws_details.column_dimensions[column].width = adjusted_width

        stream.seek(0)
        headers = {
            'Content-Disposition': 'attachment; filename="invoices_export.xlsx"'
        }
        return StreamingResponse(stream, headers=headers, media_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
