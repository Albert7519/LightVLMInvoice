# 生产部署检查清单 - LocalllmOcrMK2

用于上线前最终验收与安全检查。

---

## 1. 基础设施

- [ ] GPU 驱动已安装 (`nvidia-smi` 正常)
- [ ] Docker 已安装 (>= 20.10)
- [ ] Docker Compose 已安装 (>= 2.0)
- [ ] 磁盘空间 >= 200 GB
- [ ] 网络可访问 ModelScope 镜像源

---

## 2. 应用配置

- [ ] `.env` 已生成并配置
- [ ] `docker-compose.yml` 中 vLLM 镜像为固定版本
- [ ] Redis 持久化已启用
- [ ] `uploads` 目录权限正常

---

## 3. 安全加固

- [ ] FastAPI CORS 已限制为指定域名
- [ ] Redis 已设置密码
- [ ] HTTPS 已启用 (Nginx 或负载均衡)
- [ ] 防火墙已限制外部端口访问

---

## 4. 服务健康

- [ ] `docker-compose ps` 全部服务为 healthy
- [ ] 前端可访问 (`http://<host>`)
- [ ] API 文档可访问 (`http://<host>:8080/docs`)
- [ ] vLLM 端点可访问 (`http://<host>:8000/v1/models`)

---

## 5. 功能验证

- [ ] 上传 PDF 发票 → 返回 task_id
- [ ] 状态轮询 → 任务完成
- [ ] 导出 Excel → 文件可用

---

## 6. 性能与稳定性

- [ ] 单张发票识别 < 30 秒
- [ ] 并发 3 张任务处理无异常
- [ ] GPU 显存占用无异常增长

---

## 7. 日志与监控

- [ ] backend/celery/vllm 日志可查看
- [ ] 日志目录定期轮转或清理
- [ ] （可选）Flower 监控已启用

---

## 8. 灾备与回滚

- [ ] 镜像版本固定
- [ ] 支持 `docker-compose down` 快速回滚
- [ ] 关键配置有备份

---

完成以上清单即可进入生产环境。
