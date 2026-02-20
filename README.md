# Kai Capsule Service V2.0

## 概述

**Kai Capsule Service V2.0** 是整合 EvoMap 优点的知识胶囊服务增强版。

### 核心特性

- 🧠 **DATM 四维评分** - Truth/Goodness/Beauty/Intelligence 综合评估
- 🔗 **内容寻址机制** - SHA256 asset_id 确保内容不可篡改
- ⚡ **Gene + Capsule 组合** - 策略模板与知识胶囊绑定
- 📈 **EvolutionEvent 追踪** - 记录胶囊创作进化过程
- 🎯 **验证评分体系** - outcome.score ≥ 0.7 自动推广
- 🔄 **活胶囊机制** - 支持版本迭代和父级追溯
- 🤝 **碰撞检测** - 智能发现知识重叠

### 与 V1 对比

| 特性 | V1.0 | V2.0 (EvoMap Enhanced) |
|------|------|----------------------|
| ID 生成 | MD5 时间戳 | SHA256 内容寻址 |
| 评分 | 单一 DATM | DATM + outcome.score |
| 策略 | 无 | Gene 模板关联 |
| 版本 | 无 | 活胶囊迭代 |
| 验证 | 人工 | 自动阈值 (≥0.7) |
| 环境 | 无 | env_fingerprint |

## 快速开始

```bash
# 克隆
git clone https://github.com/wanyview/kai-capsule-service-v2.git
cd kai-capsule-service-v2

# 安装依赖
pip install -r requirements.txt

# 启动服务
python main.py
# 或
uvicorn main:app --host 0.0.0.0 --port 8005 --reload
```

## API 文档

### 创建胶囊

```bash
curl -X POST http://localhost:8005/capsules \
  -H "Content-Type: application/json" \
  -d '{
    "title": "AI时代的第二大脑",
    "content": "知识胶囊是AI时代的第二大脑...",
    "level": "advanced",
    "domain": "technology",
    "tags": ["AI", "知识管理", "第二大脑"],
    "truth": 85,
    "goodness": 80,
    "beauty": 75,
    "intelligence": 90,
    "outcome": {"status": "success", "score": 0.85}
  }'
```

### 查询胶囊

```bash
# 列表
curl http://localhost:8005/capsules

# 按领域筛选
curl "http://localhost:8005/capsules?domain=technology&min_score=70"

# 获取单个
curl http://localhost:8005/capsules/{id}
```

### 碰撞检测

```bash
curl -X POST http://localhost:8005/capsules/{id}/collisions?threshold=0.5
```

## 数据模型

### KnowledgeCapsule

```python
{
  "id": "sha256:abc123...",  # 内容寻址ID
  "title": "胶囊标题",
  "content": "胶囊内容",
  "level": "standard/advanced/legendary",
  "domain": "技术领域",
  "tags": ["标签1", "标签2"],
  
  # EvoMap 增强
  "gene_id": "gene_xxx",      # 关联策略
  "trigger_signals": ["AI", "知识"],  # 触发信号
  "confidence": 0.85,          # 置信度
  "blast_radius": {"files": 1, "lines": 100},  # 影响范围
  "outcome": {"status": "success", "score": 0.85},  # 验证结果
  "success_streak": 3,        # 连续成功
  
  # DATM 评分
  "datm_score": {
    "truth": 85,
    "goodness": 80,
    "beauty": 75,
    "intelligence": 90,
    "overall": 82.5
  },
  
  # 元数据
  "author": "作者名",
  "collaborators": ["协作者1"],
  "status": "draft/candidate/promoted",
  "version": 1,
  "parent_id": "sha256:parent..."  # 活胶囊父级
}
```

## 项目结构

```
capsule_service_v2/
├── main.py           # 主服务 (FastAPI)
├── requirements.txt  # 依赖
├── README.md         # 文档
└── capsules.db       # SQLite 数据库
```

## EvoMap 集成

本服务借鉴了 EvoMap 的以下特性：

1. **内容寻址** - SHA256 确保内容一致性
2. **验证阈值** - outcome.score ≥ 0.7 自动推广
3. **EvolutionEvent** - 记录进化过程
4. **Gene 策略** - 策略模板复用
5. **环境指纹** - env_fingerprint 追踪

## 许可证

MIT License
