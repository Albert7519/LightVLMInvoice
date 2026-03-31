# GPU 调优指南 - LocalllmOcrMK2

面向 vLLM 推理服务的 GPU 配置与性能优化指南。

---

## 1. 核心参数

### 1.1 显存利用率

`VLLM_GPU_MEMORY_UTILIZATION` 控制 vLLM 可用显存比例。

- 默认：`0.9`
- 推荐范围：`0.7 ~ 0.9`

**示例**：
```
VLLM_GPU_MEMORY_UTILIZATION=0.8
```

### 1.2 最大上下文长度

`--max-model-len` 控制最大上下文长度。

- 默认：`32768`
- 如果显存不足，可降到 `8192` 或 `16384`

**示例**：
```
--max-model-len 16384
```

---

## 2. 常见场景调优

### 2.1 显存不足（OOM）

**症状**：日志出现 `CUDA out of memory`。

**处理建议**：
- 下调显存占用
- 降低最大上下文长度
- 使用更小模型

**配置示例**：
```
VLLM_GPU_MEMORY_UTILIZATION=0.7
--max-model-len 8192
```

### 2.2 启动慢或模型下载慢

**原因**：首次运行需下载模型（2-3GB）。

**解决方案**：
- 预下载模型
- 配置 ModelScope 镜像源

**手动下载**：
```bash
docker-compose exec vllm python -c "from modelscope import snapshot_download; snapshot_download('cyankiwi/Qwen3.5-2B-AWQ-BF16-INT8')"
```

---

## 3. 多 GPU 配置

若机器有多张 GPU，可启用 tensor parallel：

```
--tensor-parallel-size 2
```

**注意**：
- 需要模型支持分片
- 需显式指定 GPU 数量

---

## 4. 监控建议

### 4.1 GPU 使用率

```bash
watch -n 1 nvidia-smi
```

### 4.2 容器内 GPU 情况

```bash
docker-compose exec vllm nvidia-smi
```

---

## 5. 推荐配置模板

### 生产推荐（平衡性能与稳定）

```
VLLM_GPU_MEMORY_UTILIZATION=0.85
--max-model-len 16384
```

### 稳定优先（低显存机器）

```
VLLM_GPU_MEMORY_UTILIZATION=0.7
--max-model-len 8192
```

---

## 6. 版本说明

- vLLM 镜像：`vllm/vllm-openai:v0.18.1-cu130`
- CUDA 运行时：12.4

---

如需更深度的性能调优（量化/多模型/调度优化），可继续扩展。
