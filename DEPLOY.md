# 部署指南 - 知识胶囊服务 V2.1

> 版本: 2.1
> 更新时间: 2026-02-26

## 环境要求

- Python 3.9+
- SQLite3
- 4GB+ RAM
- 端口: 8005

## 快速启动

```bash
# 1. 克隆仓库
git clone https://github.com/wanyview/kai-capsule-service-v2.git
cd kai-capsule-service-v2

# 2. 安装依赖
pip install -r requirements.txt

# 3. 启动服务
python main.py

# 4. 验证服务
curl http://localhost:8005/
```

## 生产环境部署

### 使用Systemd (Linux)

```bash
# 创建服务文件
sudo nano /etc/systemd/system/capsule.service

[Unit]
Description=Kai Capsule Service V2.1
After=network.target

[Service]
Type=simple
User=ubuntu
WorkingDirectory=/opt/kai-capsule-service-v2
ExecStart=/usr/bin/python3 main.py
Restart=always

[Install]
WantedBy=multi-user.target

# 启动服务
sudo systemctl enable capsule
sudo systemctl start capsule
```

### 使用Docker

```dockerfile
FROM python:3.9-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt
COPY . .
EXPOSE 8005
CMD ["python", "main.py"]
```

```bash
# 构建和运行
docker build -t kai-capsule-service .
docker run -d -p 8005:8005 -v $(pwd)/capsules.db:/app/capsules.db kai-capsule-service
```

## API端口配置

| 环境 | 端口 |
|------|------|
| 开发 | 8005 |
| 测试 | 8006 |
| 生产 | 8005 |

## 外部系统对接

### 附中矩阵对接配置

```yaml
# 附中矩阵配置
kaihub:
  base_url: http://<kaihub-host>:8005
  api_key: tok_matrix_xxx
  
  # 同步设置
  sync:
    interval: 3600  # 每小时同步
    batch_size: 50
    
  # 胶囊过滤
  filters:
    min_score: 70
    categories: [ai, education, technology]
```

## 监控

### 健康检查

```bash
curl http://localhost:8005/
```

### 日志

```bash
# 查看日志
tail -f /tmp/capsule.log

# 系统日志
journalctl -u capsule -f
```

## 备份

```bash
# 备份数据库
cp capsules.db capsules.db.backup.$(date +%Y%m%d)
```

## 故障排查

| 问题 | 解决方案 |
|------|----------|
| 服务启动失败 | 检查端口占用 `lsof -i :8005` |
| 数据库错误 | 重新初始化 `python main.py --init` |
| 内存不足 | 增加Swap或优化查询 |
