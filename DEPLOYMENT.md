# 部署指南 - LocalllmOcrMK2

面向 Linux 5090 GPU 机器的部署与运维指南。支持 Docker Compose 一键启动。

---

## 1. 系统要求

### 最低要求（CPU 推理）
- OS: Ubuntu 22.04+
- CPU: 4 核
- RAM: 8 GB
- Disk: 50 GB

### 推荐要求（GPU 推理）
- OS: Ubuntu 22.04+
- GPU: NVIDIA GPU (>= 6 GB 显存)
- Driver: >= 520
- RAM: 16 GB
- Disk: 200 GB
- Docker: 20.10+
- Docker Compose: 2.0+

---

## 2. 环境准备

### 2.1 安装 NVIDIA 驱动与容器运行时

```bash
# 检查 GPU 驱动
nvidia-smi

# 检查 Docker GPU 支持
docker run --rm --gpus all nvidia/cuda:12.4.1-base nvidia-smi
```

如无法运行，请先安装 NVIDIA 驱动与 nvidia-container-toolkit。

---

## 3. Docker Compose 快速启动

### 3.1 启动服务

```bash
cd /path/to/LocalllmOcrMK2

docker-compose up -d
```

### 3.2 查看服务状态

```bash
docker-compose ps
```

### 3.3 查看日志

```bash
# 后端日志
docker-compose logs -f backend --tail=100

# vLLM 日志
docker-compose logs -f vllm --tail=100

# Celery 日志
docker-compose logs -f celery --tail=100
```

---

## 4. 服务验证

### 4.1 前端页面

浏览器访问：
```
http://localhost
```

### 4.2 API 文档

```bash
curl http://localhost:8080/docs
```

### 4.3 vLLM 运行状态

```bash
curl http://localhost:8000/v1/models
```

---

## 5. 业务验证

### 5.1 上传发票

```bash
curl -X POST http://localhost:8080/api/v1/invoices/extract \
  -F "files=@/path/to/invoice.pdf"
```

返回示例：
```json
{"code":200,"data":{"task_ids":["xxxx-xxxx"]}}
```

### 5.2 查询任务状态

```bash
curl http://localhost:8080/api/v1/invoices/status/<TASK_ID>
```

### 5.3 导出 Excel

```bash
curl -X POST http://localhost:8080/api/v1/invoices/export \
  -H "Content-Type: application/json" \
  -d '{"task_ids":["<TASK_ID>"]}' \
  --output invoice.xlsx
```

---

## 6. 常见问题排查

### 6.1 vLLM 启动慢或超时

原因：首次启动需要下载模型。

解决：等待 10-20 分钟或预下载模型。

```bash
# 在容器内下载模型
docker-compose exec vllm python -c "from modelscope import snapshot_download; snapshot_download('cyankiwi/Qwen3.5-2B-AWQ-BF16-INT8')"
```

### 6.2 GPU 显存不足 (CUDA OOM)

解决：降低显存占用。

编辑 [docker-compose.yml](docker-compose.yml)：
```
VLLM_GPU_MEMORY_UTILIZATION=0.7
```

或使用更小模型。

### 6.3 Celery 任务堆积

```bash
# 查看 Worker 状态
docker-compose logs -f celery

# 重启 Worker
docker-compose restart celery
```

### 6.4 Redis 连接失败

```bash
# 检查 redis 是否正常
docker-compose exec redis redis-cli ping
```

---

## 7. 性能调优建议

- 调整 `VLLM_GPU_MEMORY_UTILIZATION` (默认 0.9)
- 使用量化模型（INT8/INT4）
- 限制 Celery 并发（当前 `--concurrency=1`）

---

## 8. 安全建议（生产环境）

- 将 FastAPI CORS 改为指定域名
- 使用 Nginx 配置 HTTPS
- Redis 启用密码
- 限制上传文件大小

---

## 9. 停止与清理

```bash
# 停止服务
docker-compose down

# 删除容器与卷
docker-compose down -v
```

---

## 10. 版本说明

- vLLM 镜像：`vllm/vllm-openai:v0.18.1-cu130`
- CUDA 运行时：12.4

---

如需进一步的生产级优化（监控、日志集中、集群化），可继续扩展。
