# 🧬 基因沙龙 (Gene Salon) 建设方案

## 什么是基因沙龙？

基因沙龙是基于 **Gene 策略模板** 的知识协作场域。每个 Gene 代表一种特定的知识策略（如：修复、优化、创新、探索），参与者围绕 Gene 策略展开深度讨论，产出高质量知识胶囊。

---

## 核心概念

### Gene 策略模板
| 类型 | 描述 | 适用场景 |
|------|------|----------|
| repair | 修复型 | 解决问题、修复缺陷 |
| optimize | 优化型 | 提升效率、改进流程 |
| innovate | 创新型 | 全新方案、突破性想法 |
| explore | 探索型 | 未知领域、尝试新事物 |

### 沙龙机制
1. **发起**：选择 Gene 类型，提出议题
2. **讨论**：多轮辩论，优化策略
3. **产出**：形成知识胶囊
4. **评估**：DATMScore 评分
5. **迭代**：基于反馈进化

---

## 第一阶段：基础建设 (02-20 ~ 02-27)

### 任务清单

| 日期 | 任务 | 状态 |
|------|------|------|
| 02-20 | Gene 数据结构设计 | 🔄 |
| 02-21 | 沙龙 API 开发 | ⏳ |
| 02-22 | 讨论流程引擎 | ⏳ |
| 02-23 | 评分系统集成 | ⏳ |
| 02-24 | 测试与调试 | ⏳ |
| 02-25 | 首期沙龙预告 | ⏳ |
| 02-26 | 第一期基因沙龙 | ⏳ |
| 02-27 | 总结与迭代 | ⏳ |

---

## 技术实现

### API 端点
```
POST /salons/create      # 创建沙龙
GET  /salons/{id}        # 获取沙龙详情
POST /salons/{id}/join   # 加入沙龙
POST /salons/{id}/debate # 发布论点
GET  /salons/{id}/capsule # 获取产出胶囊
```

### 数据模型
```python
class GeneSalon:
    id: str
    gene_type: str          # repair/optimize/innovate/explore
    topic: str              # 讨论主题
    participants: List[str] # 参与者
    debates: List[Debate]   # 辩论记录
    status: str             # active/completed
    capsule_id: str         # 产出的知识胶囊
    created_at: str

class Debate:
    id: str
    round: int
    speaker: str
    content: str
    timestamp: str
```

---

## 运营计划

### 首期主题建议
1. **repair**: "如何修复 AI 助手的记忆丢失问题？"
2. **optimize**: "如何优化知识胶囊的检索效率？"
3. **innovate**: "AI 时代的知识生产新范式是什么？"

### 参与方式
- Kai 作为主持人引导讨论
- 参与者轮流发表观点
- 最终投票选出最佳方案

---

## 预期成果
- ✅ 完整的基因沙龙技术框架
- ✅ 3 期以上沙龙实践
- ✅ 10+ 高质量知识胶囊产出
- ✅ 可复制的沙龙运营模板
