import os
from dotenv import load_dotenv
from celery import Celery

# Load environment variables from .env file
load_dotenv()

# 从环境变量中读取 Redis 地址，默认本机
REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379/0")

# 创建 Celery 实例
celery_app = Celery(
    "invoice_ocr_worker",
    broker=REDIS_URL,
    backend=REDIS_URL,
    include=['tasks']  # 后续定义任务的模块名
)

# 配置 Celery
celery_app.conf.update(
    task_serializer='json',
    accept_content=['json'],  
    result_serializer='json',
    timezone='Asia/Shanghai',
    enable_utc=True,
    task_track_started=True, # 允许随时更新任务进度
)
