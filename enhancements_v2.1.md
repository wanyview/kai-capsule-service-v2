# 知识胶囊 V2.1 增强版

## 新增能力

### 1. 语义向量搜索
- 集成 sentence-transformers 嵌入
- 支持语义相似度查询
- 向量存储与索引

### 2. 跨域关联引擎
- 自动发现跨领域知识连接
- 图谱可视化
- 知识路径推荐

### 3. 多模态支持
- 图片胶囊
- 音频胶囊
- 视频胶囊
- 附件管理

### 4. 时间线视图
- 胶囊版本历史
- 演进过程追踪
- 分支与合并

### 5. 智能推荐
- 基于阅读历史的推荐
- 相似胶囊推荐
- 趋势发现

---

## API 增强

### 新增端点

```
POST /capsules/semantic-search    # 语义搜索
POST /capsules/embed              # 生成向量嵌入
GET  /capsules/related/{id}       # 相关胶囊
GET  /capsules/timeline/{id}      # 版本时间线
POST /capsules/multimodal         # 创建多模态胶囊
GET  /capsules/recommend          # 智能推荐
GET  /domains/graph               # 知识图谱
```

---

## 数据模型增强

```python
@dataclass
class CapsuleVector:
    """胶囊向量"""
    capsule_id: str
    embedding: List[float]
    model: str
    created_at: str

@dataclass
class CrossDomainLink:
    """跨域链接"""
    source_id: str
    target_id: str
    strength: float
    reason: str

@dataclass
class MultimediaAsset:
    """多媒体资源"""
    id: str
    type: str  # image/audio/video
    url: str
    thumbnail: str
    metadata: Dict
