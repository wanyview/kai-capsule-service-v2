# 知识胶囊：辩论引擎API使用指南

## 胶囊信息

| 字段 | 内容 |
|------|------|
| ID | capsule_002 |
| 标题 | 辩论引擎API使用指南 |
| 类型 | 技术胶囊 |
| 标签 | API, 辩论, 教程, 技术 |
| DATM评分 | 88 |
| 等级 | L3-钻石 |

## 内容

### 1. 概述

辩论引擎API是TIER咖啡知识沙龙的核心能力，支持自动生成论点、反驳和评分。

### 2. API列表

| 接口 | 方法 | 功能 |
|------|------|------|
| /api/v1/debate/start | POST | 发起辩论 |
| /api/v1/debate/argument | POST | 生成论点 |
| /api/v1/debate/counter | POST | 生成反驳 |
| /api/v1/debate/judge | POST | 裁判评分 |
| /api/v1/debate/history | GET | 历史记录 |

### 3. 快速开始

```python
import requests

# 1. 发起辩论
response = requests.post("http://localhost:8005/api/v1/debate/start", json={
    "topic": "AI是否会取代老师",
    "pro_team": "正方",
    "con_team": "反方"
})
debate_id = response.json()["debate_id"]

# 2. 生成论点
response = requests.post("http://localhost:8005/api/v1/debate/argument", json={
    "debate_id": debate_id,
    "side": "pro",
    "topic": "AI是否会取代老师"
})
argument = response.json()["argument"]

# 3. 生成反驳
response = requests.post("http://localhost:8005/api/v1/debate/counter", json={
    "debate_id": debate_id,
    "argument_id": argument["id"]
})
counter = response.json()["counter"]

# 4. 裁判评分
response = requests.post("http://localhost:8005/api/v1/debate/judge", json={
    "debate_id": debate_id
})
result = response.json()
```

### 4. 响应示例

```json
{
  "debate_id": "deb_123456",
  "status": "active",
  "topic": "AI是否会取代老师",
  "arguments": [
    {
      "id": "arg_001",
      "side": "pro",
      "content": "AI可以个性化教学",
      "strength": 8.5
    }
  ]
}
```

### 5. 应用场景

- 课堂教学模拟辩论
- 学术论文正反论证
- 商业决策利弊分析
- 个人思考多方视角

---

**创建时间**: 2026-02-28
**作者**: KAI数字主理人
