"""
知识胶囊服务 V2.0 - 整合 EvoMap 优点增强版
- 内容寻址机制 (SHA256 asset_id)
- 验证评分体系 (outcome.score ≥ 0.7)
- EvolutionEvent 进化事件追踪
- Gene策略关联
- 活胶囊版本控制
"""
import hashlib
import json
import sqlite3
import os
import asyncio
from datetime import datetime
from typing import Optional, List, Dict, Any
from dataclasses import dataclass, field, asdict
from enum import Enum
from fastapi import FastAPI, HTTPException, Query
from pydantic import BaseModel
import uuid

# ===================== 配置 =====================
DB_PATH = "/Users/wanyview/clawd/capsule_service_v2/capsules.db"
app = FastAPI(title="Kai Capsule Service V2.0 (EvoMap Enhanced)", version="2.1.0")

# ===================== 数据模型 =====================

class CapsuleLevel(str, Enum):
    STANDARD = "standard"
    ADVANCED = "advanced"
    LEGENDARY = "legendary"

class CapsuleStatus(str, Enum):
    DRAFT = "draft"
    CANDIDATE = "candidate"
    PROMOTED = "promoted"
    REJECTED = "rejected"
    ARCHIVED = "archived"

class EvolutionIntent(str, Enum):
    EXPLORE = "explore"       # 探索型
    REPAIR = "repair"         # 修复型
    OPTIMIZE = "optimize"     # 优化型
    INNOVATE = "innovate"     # 创新型

@dataclass
class DATMScore:
    """DATM 四维评分"""
    truth: float              # 真理性
    goodness: float           # 价值性  
    beauty: float            # 美感
    intelligence: float      # 智慧性
    
    @property
    def overall(self) -> float:
        return round((self.truth + self.goodness + self.beauty + self.intelligence) / 4, 2)

@dataclass
class EnvironmentFingerprint:
    """环境指纹"""
    platform: str = "unknown"
    arch: str = "unknown"
    version: str = "1.0.0"
    additional_info: Dict[str, str] = field(default_factory=dict)

@dataclass
class BlastRadius:
    """影响范围"""
    files: int = 1
    lines: int = 100
    domains: List[str] = field(default_factory=list)

@dataclass
class Gene:
    """Gene 策略模板 (借鉴 EvoMap)"""
    id: str
    category: str                    # repair/optimize/innovate/explore
    signals_match: List[str]         # 触发信号
    summary: str                      # 策略描述
    intent: EvolutionIntent
    validation_commands: List[str] = field(default_factory=list)
    author: str = "Kai"
    created_at: str = ""

@dataclass
class EvolutionEvent:
    """进化事件 (借鉴 EvoMap EvolutionEvent)"""
    id: str
    intent: EvolutionIntent
    capsule_id: str
    genes_used: List[str]
    outcome: Dict[str, Any]          # {status: success/failure, score: 0-1}
    mutations_tried: int
    total_cycles: int
    created_at: str = ""

@dataclass
class KnowledgeCapsule:
    """知识胶囊 (借鉴 EvoMap Capsule + 增强)"""
    id: str                          # SHA256 content-addressable ID
    title: str
    content: str
    level: CapsuleLevel
    domain: str
    tags: List[str]
    
    # EvoMap 增强字段
    gene_id: Optional[str] = None     # 关联的 Gene
    trigger_signals: List[str] = field(default_factory=list)  # 触发信号
    confidence: float = 0.5          # 置信度 0-1
    blast_radius: BlastRadius = None  # 影响范围
    outcome: Dict[str, Any] = None   # 验证结果 {status, score}
    success_streak: int = 0          # 连续成功次数
    env_fingerprint: EnvironmentFingerprint = None
    
    # DATM 评分
    datm_score: DATMScore = None
    
    # 元数据
    author: str = "Kai"
    collaborators: List[str] = field(default_factory=list)
    status: CapsuleStatus = CapsuleStatus.DRAFT
    version: int = 1
    parent_id: Optional[str] = None   # 父胶囊ID (活胶囊迭代)
    created_at: str = ""
    updated_at: str = ""
    
    def to_dict(self) -> Dict:
        return {
            "id": self.id,
            "title": self.title,
            "content": self.content,
            "level": self.level.value,
            "domain": self.domain,
            "tags": self.tags,
            "gene_id": self.gene_id,
            "trigger_signals": self.trigger_signals,
            "confidence": self.confidence,
            "blast_radius": asdict(self.blast_radius) if self.blast_radius else None,
            "outcome": self.outcome,
            "success_streak": self.success_streak,
            "env_fingerprint": asdict(self.env_fingerprint) if self.env_fingerprint else None,
            "datm_score": asdict(self.datm_score) if self.datm_score else None,
            "author": self.author,
            "collaborators": self.collaborators,
            "status": self.status.value,
            "version": self.version,
            "parent_id": self.parent_id,
            "created_at": self.created_at,
            "updated_at": self.updated_at
        }

# ===================== 数据库 =====================
_db_conn = None

def get_db():
    global _db_conn
    if _db_conn is None:
        _db_conn = sqlite3.connect(DB_PATH, check_same_thread=False)
        _db_conn.row_factory = sqlite3.Row
    return _db_conn

def init_db():
    """初始化数据库"""
    conn = get_db()
    cursor = conn.cursor()
    
    # 知识胶囊表 (V2 增强版)
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS capsules (
            id TEXT PRIMARY KEY,
            data TEXT NOT NULL,
            level TEXT,
            domain TEXT,
            status TEXT,
            datm_score REAL,
            confidence REAL,
            version INTEGER DEFAULT 1,
            created_at TEXT,
            updated_at TEXT
        )
    ''')
    
    # Gene 策略表
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS genes (
            id TEXT PRIMARY KEY,
            data TEXT NOT NULL,
            category TEXT,
            intent TEXT,
            usage_count INTEGER DEFAULT 0,
            created_at TEXT
        )
    ''')
    
    # 进化事件表
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS evolution_events (
            id TEXT PRIMARY KEY,
            capsule_id TEXT,
            intent TEXT,
            genes_used TEXT,
            outcome TEXT,
            mutations_tried INTEGER,
            total_cycles INTEGER,
            created_at TEXT
        )
    ''')
    
    # 胶囊碰撞表
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS collisions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            capsule_a_id TEXT,
            capsule_b_id TEXT,
            collision_type TEXT,
            score REAL,
            created_at TEXT
        )
    ''')
    
    conn.commit()

init_db()

# ===================== 内容寻址工具 =====================

def canonical_json(obj: Dict) -> str:
    """生成规范JSON (EvoMap标准)"""
    return json.dumps(obj, sort_keys=True, separators=(',', ':'))

def compute_asset_id(data: Dict, exclude_field: str = None) -> str:
    """计算内容寻址ID (SHA256)"""
    if exclude_field:
        data = {k: v for k, v in data.items() if k != exclude_field}
    json_str = canonical_json(data)
    hash_val = hashlib.sha256(json_str.encode()).hexdigest()
    return f"sha256:{hash_val}"

def generate_id(prefix: str = "obj") -> str:
    """生成ID"""
    timestamp = datetime.utcnow().strftime("%Y%m%d%H%M%S")
    short_uuid = str(uuid.uuid4())[:8]
    return f"{prefix}_{timestamp}_{short_uuid}"

# ===================== 胶囊操作 =====================

def create_capsule(data: Dict) -> KnowledgeCapsule:
    """创建知识胶囊 (带内容寻址)"""
    conn = get_db()
    cursor = conn.cursor()
    
    now = datetime.utcnow().isoformat()
    
    # 构建胶囊对象
    capsule = KnowledgeCapsule(
        id="",  # 稍后计算
        title=data['title'],
        content=data['content'],
        level=CapsuleLevel(data.get('level', 'standard')),
        domain=data.get('domain', 'general'),
        tags=data.get('tags', []),
        
        # EvoMap 增强字段
        gene_id=data.get('gene_id'),
        trigger_signals=data.get('trigger_signals', []),
        confidence=data.get('confidence', 0.5),
        blast_radius=BlastRadius(**data.get('blast_radius', {'files': 1, 'lines': 100})),
        outcome=data.get('outcome', {'status': 'pending', 'score': 0}),
        success_streak=data.get('success_streak', 0),
        env_fingerprint=EnvironmentFingerprint(**data.get('env_fingerprint', {})),
        
        # DATM 评分
        datm_score=DATMScore(
            truth=data.get('truth', 70),
            goodness=data.get('goodness', 70),
            beauty=data.get('beauty', 70),
            intelligence=data.get('intelligence', 70)
        ),
        
        # 元数据
        author=data.get('author', 'Kai'),
        collaborators=data.get('collaborators', []),
        status=CapsuleStatus(data.get('status', 'candidate')),
        version=data.get('version', 1),
        parent_id=data.get('parent_id'),
        created_at=now,
        updated_at=now
    )
    
    # 计算内容寻址ID
    capsule.id = compute_asset_id(capsule.to_dict(), 'id')
    
    # 自动验证 (借鉴 EvoMap: outcome.score >= 0.7)
    if capsule.outcome and capsule.outcome.get('score', 0) >= 0.7:
        capsule.status = CapsuleStatus.PROMOTED
    elif capsule.datm_score and capsule.datm_score.overall >= 70:
        capsule.status = CapsuleStatus.CANDIDATE
    
    # 存储
    cursor.execute('''
        INSERT INTO capsules (id, data, level, domain, status, datm_score, confidence, version, created_at, updated_at)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    ''', (
        capsule.id,
        json.dumps(capsule.to_dict()),
        capsule.level.value,
        capsule.domain,
        capsule.status.value,
        capsule.datm_score.overall if capsule.datm_score else None,
        capsule.confidence,
        capsule.version,
        now,
        now
    ))
    
    conn.commit()
    return capsule

def get_capsule(capsule_id: str) -> Optional[KnowledgeCapsule]:
    """获取胶囊"""
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("SELECT data FROM capsules WHERE id = ?", (capsule_id,))
    row = cursor.fetchone()
    
    if row is None:
        return None
    
    data = json.loads(row['data'])
    return KnowledgeCapsule(**data)

def list_capsules(domain: str = None, status: str = None, 
                  min_score: float = None, limit: int = 50) -> List[KnowledgeCapsule]:
    """列出胶囊"""
    conn = get_db()
    cursor = conn.cursor()
    
    query = "SELECT data FROM capsules WHERE 1=1"
    params = []
    
    if domain:
        query += " AND domain = ?"
        params.append(domain)
    
    if status:
        query += " AND status = ?"
        params.append(status)
    
    if min_score:
        query += " AND datm_score >= ?"
        params.append(min_score)
    
    query += " ORDER BY created_at DESC LIMIT ?"
    params.append(min(limit, 200))
    
    cursor.execute(query, params)
    
    capsules = []
    for row in cursor.fetchall():
        data = json.loads(row['data'])
        capsules.append(KnowledgeCapsule(**data))
    
    return capsules

def update_capsule(capsule_id: str, updates: Dict) -> Optional[KnowledgeCapsule]:
    """更新胶囊 (活胶囊机制)"""
    conn = get_db()
    cursor = conn.cursor()
    
    cursor.execute("SELECT data FROM capsules WHERE id = ?", (capsule_id,))
    row = cursor.fetchone()
    
    if row is None:
        return None
    
    capsule = KnowledgeCapsule(**json.loads(row['data']))
    
    # 应用更新
    for key, value in updates.items():
        if hasattr(capsule, key):
            setattr(capsule, key, value)
    
    capsule.version += 1
    capsule.updated_at = datetime.utcnow().isoformat()
    
    # 重新计算ID (内容寻址)
    new_data = capsule.to_dict()
    new_data['id'] = ""
    new_id = compute_asset_id(new_data, 'id')
    
    # 更新时保留旧ID引用
    old_id = capsule.id
    capsule.id = new_id
    capsule.parent_id = old_id
    
    cursor.execute('''
        INSERT INTO capsules (id, data, level, domain, status, datm_score, confidence, version, parent_id, created_at, updated_at)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    ''', (
        capsule.id,
        json.dumps(capsule.to_dict()),
        capsule.level.value,
        capsule.domain,
        capsule.status.value,
        capsule.datm_score.overall if capsule.datm_score else None,
        capsule.confidence,
        capsule.version,
        capsule.parent_id,
        old_id,  # 保留原始创建时间
        capsule.updated_at
    ))
    
    conn.commit()
    return capsule

# ===================== Gene 操作 =====================

def create_gene(data: Dict) -> Gene:
    """创建 Gene 策略模板"""
    conn = get_db()
    cursor = conn.cursor()
    
    now = datetime.utcnow().isoformat()
    
    gene = Gene(
        id=generate_id("gene"),
        category=data['category'],
        signals_match=data['signals_match'],
        summary=data['summary'],
        intent=EvolutionIntent(data.get('intent', 'explore')),
        validation_commands=data.get('validation_commands', []),
        author=data.get('author', 'Kai'),
        created_at=now
    )
    
    cursor.execute('''
        INSERT INTO genes (id, data, category, intent, created_at)
        VALUES (?, ?, ?, ?, ?)
    ''', (gene.id, json.dumps(asdict(gene)), gene.category, gene.intent.value, now))
    
    conn.commit()
    return gene

# ===================== 碰撞检测 =====================

def detect_collisions(capsule_id: str, threshold: float = 0.5) -> List[Dict]:
    """检测胶囊碰撞"""
    conn = get_db()
    cursor = conn.cursor()
    
    target = get_capsule(capsule_id)
    if not target:
        return []
    
    all_capsules = list_capsules(limit=500)
    
    collisions = []
    for capsule in all_capsules:
        if capsule.id == capsule_id:
            continue
        
        # 标签重叠计算
        if target.tags and capsule.tags:
            overlap = len(set(target.tags) & set(capsule.tags))
            similarity = overlap / max(len(target.tags), len(capsule.tags))
        else:
            similarity = 0
        
        # 领域加成
        domain_bonus = 1.3 if capsule.domain == target.domain else 1.0
        final_score = round(similarity * domain_bonus, 3)
        
        if final_score >= threshold:
            collisions.append({
                "capsule_id": capsule.id,
                "title": capsule.title,
                "domain": capsule.domain,
                "score": final_score
            })
    
    collisions.sort(key=lambda x: x['score'], reverse=True)
    return collisions[:20]

# ===================== 统计 =====================

def get_stats() -> Dict:
    """获取统计信息"""
    conn = get_db()
    cursor = conn.cursor()
    
    cursor.execute("SELECT COUNT(*) FROM capsules")
    total = cursor.fetchone()[0]
    
    cursor.execute("SELECT AVG(datm_score) FROM capsules WHERE datm_score IS NOT NULL")
    avg_score = cursor.fetchone()[0] or 0
    
    cursor.execute("SELECT domain, COUNT(*) FROM capsules GROUP BY domain")
    domain_dist = {row[0]: row[1] for row in cursor.fetchall() if row[0]}
    
    cursor.execute("SELECT author, COUNT(*) FROM capsules GROUP BY author")
    author_dist = {row[0]: row[1] for row in cursor.fetchall() if row[0]}
    
    return {
        "total_capsules": total,
        "avg_datm_score": round(avg_score, 2),
        "domain_distribution": domain_dist,
        "author_distribution": author_dist
    }

# ===================== API 路由 =====================

@app.get("/")
async def root():
    return {
        "service": "Kai Capsule Service V2.0",
        "version": "2.1.0",
        "status": "running",
        "features": [
            "content_addressable_id",
            "gene_capsule_bundle",
            "evolution_events",
            "datm_scoring",
            "collision_detection",
            "version_control"
        ]
    }

@app.post("/capsules")
async def create_capsule(data: dict):
    """创建知识胶囊"""
    # 直接创建并保存到数据库
    import json
    from datetime import datetime
    
    now = datetime.utcnow().isoformat()
    
    # 生成ID
    timestamp = datetime.now().strftime('%Y%m%d%H%M%S')
    import uuid
    capsule_id = f"capsule_{timestamp}_{uuid.uuid4().hex[:8]}"
    
    # 保存到数据库
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    tags = data.get('tags', [])
    if isinstance(tags, list):
        tags = json.dumps(tags)
    
    cursor.execute("""
        INSERT INTO capsules (id, title, content, source, domain, tags, datm_score, author, created_at, updated_at)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        capsule_id,
        data.get('title', 'Untitled'),
        data.get('content', ''),
        'api',
        data.get('domain', 'general'),
        tags,
        data.get('datm_score', 0),
        data.get('author', 'Kai'),
        now,
        now
    ))
    
    conn.commit()
    conn.close()
    
    return {"id": capsule_id, "status": "created", "created_at": now}

@app.get("/capsules")
async def list_capsules(
    domain: str = None,
    status: str = None,
    min_score: float = Query(None, ge=0, le=100),
    limit: int = Query(50, ge=1, le=200)
):
    """列出胶囊"""
    # 直接查询数据库
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    
    query = "SELECT * FROM capsules WHERE 1=1"
    params = []
    
    if domain:
        query += " AND domain = ?"
        params.append(domain)
    
    if min_score:
        query += " AND datm_score >= ?"
        params.append(min_score)
    
    query += " ORDER BY created_at DESC LIMIT ?"
    params.append(min(limit, 200))
    
    cursor.execute(query, params)
    
    capsules = []
    for row in cursor.fetchall():
        # 直接返回字典格式
        import json
        tags = json.loads(row['tags']) if row['tags'] else []
        capsule_dict = {
            'id': row['id'],
            'title': row['title'],
            'content': row['content'],
            'level': 'standard',
            'domain': row['domain'] or "general",
            'tags': tags,
            'author': row['author'] or "Kai",
            'datm_score': row['datm_score'] or 0,
            'created_at': row['created_at'],
            'updated_at': row['updated_at']
        }
        capsules.append(capsule_dict)
    
    conn.close()
    return {"capsules": capsules, "total": len(capsules)}

@app.get("/capsules/{capsule_id}")
async def get_capsule(capsule_id: str):
    """获取胶囊"""
    capsule = get_capsule(capsule_id)
    if not capsule:
        raise HTTPException(status_code=404, detail="胶囊不存在")
    return capsule.to_dict()

@app.put("/capsules/{capsule_id}")
async def update_capsule(capsule_id: str, updates: dict):
    """更新胶囊 (活胶囊)"""
    capsule = update_capsule(capsule_id, updates)
    if not capsule:
        raise HTTPException(status_code=404, detail="胶囊不存在")
    return capsule.to_dict()

@app.post("/capsules/{capsule_id}/collisions")
async def get_collisions(capsule_id: str, threshold: float = Query(0.5, ge=0, le=1)):
    """检测碰撞"""
    collisions = detect_collisions(capsule_id, threshold)
    return {"collisions": collisions}

@app.post("/genes")
async def create_gene(data: dict):
    """创建 Gene 策略"""
    gene = create_gene(data)
    return asdict(gene)

@app.get("/stats")
def stats():
    """统计信息"""
    try:
        conn = get_db()
        cursor = conn.cursor()
        
        cursor.execute("SELECT COUNT(*) FROM capsules")
        total = cursor.fetchone()[0]
        
        cursor.execute("SELECT AVG(datm_score) FROM capsules WHERE datm_score IS NOT NULL")
        avg_score = cursor.fetchone()[0] or 0
        
        return {
            "total_capsules": total,
            "avg_datm_score": round(avg_score, 2)
        }
    except Exception as e:
        return {"error": str(e)}

# ===================== V2.1 增强 API =====================

@app.post("/capsules/embed/{capsule_id}")
async def create_embedding(capsule_id: str):
    """为胶囊创建向量嵌入"""
    if not ENHANCEMENTS_ENABLED or not SEMANTIC_ENABLED:
        raise HTTPException(status_code=501, detail="语义搜索未启用")
    
    capsule = get_capsule(capsule_id)
    if not capsule:
        raise HTTPException(status_code=404, detail="胶囊不存在")
    
    # 组合文本
    text = f"{capsule.title} {capsule.content}"
    embedding = compute_embedding(text)
    
    if embedding:
        store_embedding(capsule_id, embedding)
        return {"success": True, "capsule_id": capsule_id, "dimensions": len(embedding)}
    
    raise HTTPException(status_code=500, detail="嵌入生成失败")

@app.post("/capsules/semantic-search")
async def semantic_search_endpoint(request: dict):
    """语义搜索"""
    query = request.get("query", "")
    limit = request.get("limit", 10)
    
    # 使用轻量级搜索 (跳过高级语义搜索以避免网络问题)
    try:
        from search_v2 import simple_semantic_search
        results = simple_semantic_search(query, limit)
        print(f"DEBUG: search('{query}') returned {len(results)} results")
        return {"query": query, "results": results, "total": len(results), "mode": "keyword"}
    except Exception as e:
        import traceback
        print(f"ERROR: search failed - {e}")
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"搜索失败: {str(e)}")

@app.get("/domains/graph")
async def get_knowledge_graph():
    """获取知识图谱"""
    # 使用轻量级版本
    try:
        from search_v2 import get_domain_graph as _get_graph
        graph = _get_graph()
        return graph
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"图谱获取失败: {str(e)}")

@app.post("/domains/analyze")
async def analyze_cross_domain():
    """分析跨域关联"""
    if not ENHANCEMENTS_ENABLED:
        raise HTTPException(status_code=501, detail="跨域分析未启用")
    
    links = analyze_cross_domain_links()
    return {"links": [asdict(l) for l in links], "total": len(links)}

@app.get("/capsules/{capsule_id}/related")
async def get_related_capsules(capsule_id: str, limit: int = Query(5, ge=1, le=20)):
    """获取相关胶囊"""
    try:
        from search_v2 import get_related_capsules as _get_related
        recs = _get_related(capsule_id, limit)
        return {"recommendations": recs}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"推荐失败: {str(e)}")

@app.get("/capsules/{capsule_id}/timeline")
async def get_timeline(capsule_id: str):
    """获取版本时间线"""
    if not ENHANCEMENTS_ENABLED:
        raise HTTPException(status_code=501, detail="时间线功能未启用")
    
    timeline = get_capsule_timeline(capsule_id)
    return {"capsule_id": capsule_id, "timeline": timeline}

@app.get("/capsules/{capsule_id}/multimedia")
async def get_multimedia(capsule_id: str):
    """获取多媒体资源"""
    if not ENHANCEMENTS_ENABLED:
        raise HTTPException(status_code=501, detail="多模态功能未启用")
    
    assets = get_capsule_multimedia(capsule_id)
    return {"capsule_id": capsule_id, "assets": assets}

@app.post("/capsules/{capsule_id}/multimedia")
async def add_capsule_multimedia(
    capsule_id: str,
    request: dict
):
    """添加多媒体资源"""
    if not ENHANCEMENTS_ENABLED:
        raise HTTPException(status_code=501, detail="多模态功能未启用")
    
    capsule = get_capsule(capsule_id)
    if not capsule:
        raise HTTPException(status_code=404, detail="胶囊不存在")
    
    file_type = request.get("file_type", "document")
    filename = request.get("filename", "")
    url = request.get("url", "")
    
    asset = add_multimedia(capsule_id, file_type, filename, url)
    return asset.to_dict()

@app.get("/recommend")
async def recommend(domain: str = None, limit: int = Query(5, ge=1, le=20)):
    """智能推荐"""
    if not ENHANCEMENTS_ENABLED:
        raise HTTPException(status_code=501, detail="推荐功能未启用")
    
    recs = recommend_capsules(domain=domain, limit=limit)
    return {"recommendations": [asdict(r) for r in recs]}

# ===================== 外部系统拉取API (附中矩阵对接) =====================

class CapsulePullRequest(BaseModel):
    """拉取请求"""
    domain: Optional[str] = None
    tags: Optional[List[str]] = None
    status: Optional[str] = "promoted"  # 默认只拉取已推广的
    min_score: Optional[float] = Query(None, ge=0, le=100)
    limit: int = Query(50, ge=1, le=200)
    offset: int = Query(0, ge=0)
    since: Optional[str] = None  # 更新时间筛选 (ISO格式)

class UnifiedCapsuleResponse(BaseModel):
    """统一胶囊格式响应 (用于跨平台对接)"""
    id: str
    source: str = "kaihub"
    title: str
    content: str
    summary: str
    category: str
    tags: List[str]
    keywords: List[str]
    author: dict
    created_at: str
    updated_at: str
    metrics: dict
    visibility: str = "public"
    sync_status: str = "synced"

@app.post("/api/v1/capsule/pull")
async def pull_capsules(request: CapsulePullRequest):
    """
    外部系统拉取知识胶囊API
    用于附中矩阵等外部系统从KaiHub拉取胶囊
    """
    # 直接查询数据库
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    
    query = "SELECT * FROM capsules WHERE 1=1"
    params = []
    
    if request.domain:
        query += " AND domain = ?"
        params.append(request.domain)
    
    if request.min_score:
        query += " AND datm_score >= ?"
        params.append(request.min_score)
    
    query += f" ORDER BY updated_at DESC LIMIT {request.limit} OFFSET {request.offset}"
    
    cursor.execute(query, params)
    rows = cursor.fetchall()
    conn.close()
    
    # 转换为统一格式
    unified_capsules = []
    for row in rows:
        # 直接使用列数据
        import json
        tags = json.loads(row['tags']) if row['tags'] else []
        
        # 过滤更新时间
        if request.since:
            since_dt = datetime.fromisoformat(request.since.replace('Z', '+00:00'))
            updated_at = datetime.fromisoformat(row['updated_at'].replace('Z', '+00:00'))
            if updated_at <= since_dt:
                continue
        
        # 过滤标签
        if request.tags:
            if not any(tag in tags for tag in request.tags):
                continue
        
        unified = UnifiedCapsuleResponse(
            id=row['id'],
            source="kaihub",
            title=row['title'],
            content=row['content'][:5000] if row['content'] else "",
            summary=row['content'][:500] if row['content'] else "",
            category=row['domain'] or "general",
            tags=tags,
            keywords=tags[:5],  # 使用标签作为关键词
            author={
                "id": row['author'] or "unknown",
                "name": row['author'] or "Kai",
                "platform": "kaihub"
            },
            created_at=row['created_at'],
            updated_at=row['updated_at'],
            metrics={
                "views": 0,
                "likes": 0,
                "citations": 0,
                "rating": 0,
                "datm_score": row['datm_score'] or 0
            },
            visibility="public",
            sync_status="synced"
        )
        unified_capsules.append(unified)
    
    return {
        "count": len(unified_capsules),
        "capsules": [uc.dict() for uc in unified_capsules],
        "pagination": {
            "limit": request.limit,
            "offset": request.offset,
            "has_more": len(unified_capsules) == request.limit
        }
    }

@app.get("/api/v1/capsule/pull/domains")
async def get_available_domains():
    """获取可用的领域列表"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("SELECT DISTINCT domain FROM capsules WHERE domain IS NOT NULL")
    domains = [row[0] for row in cursor.fetchall()]
    conn.close()
    return {"domains": domains}

@app.get("/api/v1/capsule/pull/tags")
async def get_available_tags():
    """获取可用的标签列表"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("SELECT DISTINCT tags FROM capsules WHERE tags IS NOT NULL")
    all_tags = set()
    for row in cursor.fetchall():
        if row[0]:
            import json
            try:
                tags = json.loads(row[0])
                all_tags.update(tags)
            except:
                pass
    conn.close()
    return {"tags": list(all_tags)}

# ===================== 同步API (外部系统推送) =====================

class CapsuleSyncRequest(BaseModel):
    """同步请求 (从外部系统接收胶囊)"""
    id: str
    title: str
    content: str
    summary: Optional[str] = ""
    category: str = "general"
    tags: List[str] = []
    keywords: List[str] = []
    author: dict
    visibility: str = "public"

@app.post("/api/v1/capsule/sync")
async def sync_capsule(request: CapsuleSyncRequest):
    """
    外部系统同步知识胶囊到KaiHub
    用于附中矩阵等外部系统推送胶囊到KaiHub
    """
    import json
    from datetime import datetime
    
    # 生成ID (如果未提供)
    capsule_id = request.id or f"capsule_{datetime.now().strftime('%Y%m%d%H%M%S')}"
    
    # 创建时间戳
    now = datetime.now().isoformat()
    
    # 保存到数据库
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    # 检查是否已存在
    cursor.execute("SELECT id FROM capsules WHERE id = ?", (capsule_id,))
    exists = cursor.fetchone()
    
    if exists:
        # 更新
        cursor.execute("""
            UPDATE capsules SET 
                title = ?, content = ?, domain = ?, tags = ?, 
                updated_at = ?, metadata = ?
            WHERE id = ?
        """, (
            request.title,
            request.content,
            request.category,
            json.dumps(request.tags),
            now,
            json.dumps({"source": "external_sync", "author": request.author}),
            capsule_id
        ))
        action = "updated"
    else:
        # 插入
        cursor.execute("""
            INSERT INTO capsules (id, title, content, source, domain, tags, datm_score, author, created_at, updated_at, metadata)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            capsule_id,
            request.title,
            request.content,
            "external_sync",
            request.category,
            json.dumps(request.tags),
            0,  # 初始评分
            request.author.get("name", "Unknown"),
            now,
            now,
            json.dumps({"source": "external_sync", "author": request.author, "visibility": request.visibility})
        ))
        action = "created"
    
    conn.commit()
    conn.close()
    
    return {
        "success": True,
        "action": action,
        "capsule_id": capsule_id,
        "message": f"胶囊已{action}"
    }

@app.post("/api/v1/capsule/batch-sync")
async def batch_sync_capsules(request: dict):
    """批量同步胶囊"""
    capsules = request.get("capsules", [])
    results = []
    
    for capsule_data in capsules:
        try:
            req = CapsuleSyncRequest(**capsule_data)
            # 简化处理 - 直接调用上面的逻辑
            import json
            from datetime import datetime
            
            capsule_id = req.id or f"capsule_{datetime.now().strftime('%Y%m%d%H%M%S')}"
            now = datetime.now().isoformat()
            
            conn = sqlite3.connect(DB_PATH)
            cursor = conn.cursor()
            
            cursor.execute("SELECT id FROM capsules WHERE id = ?", (capsule_id,))
            exists = cursor.fetchone()
            
            if exists:
                cursor.execute("""
                    UPDATE capsules SET title = ?, content = ?, domain = ?, tags = ?, updated_at = ?
                    WHERE id = ?
                """, (req.title, req.content, req.category, json.dumps(req.tags), now, capsule_id))
                action = "updated"
            else:
                cursor.execute("""
                    INSERT INTO capsules (id, title, content, source, domain, tags, datm_score, author, created_at, updated_at)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (capsule_id, req.title, req.content, "external_sync", req.category, json.dumps(req.tags), 0, req.author.get("name", "Unknown"), now, now))
                action = "created"
            
            conn.commit()
            conn.close()
            
            results.append({"capsule_id": capsule_id, "action": action, "success": True})
        except Exception as e:
            results.append({"error": str(e), "success": False})
    
    success_count = sum(1 for r in results if r.get("success"))
    return {
        "total": len(capsules),
        "success": success_count,
        "failed": len(capsules) - success_count,
        "results": results
    }

# ===================== V2.1 增强功能导入 =====================
try:
    from enhancements import (
        init_db_enhancements,
        compute_embedding,
        store_embedding,
        semantic_search,
        analyze_cross_domain_links,
        get_domain_graph,
        add_multimedia,
        get_capsule_multimedia,
        recommend_capsules,
        get_capsule_timeline,
        SEMANTIC_ENABLED
    )
    ENHANCEMENTS_ENABLED = True
except ImportError as e:
    print(f"⚠️ 增强模块加载失败: {e}")
    ENHANCEMENTS_ENABLED = False
    SEMANTIC_ENABLED = False

# ===================== 辩论引擎模块 =====================
from debate_engine import router as debate_router
from feedback_system import router as feedback_router
app.include_router(debate_router)
app.include_router(feedback_router)

# 初始化增强数据库
if ENHANCEMENTS_ENABLED:
    init_db_enhancements()

# ===================== 启动 =====================
if __name__ == "__main__":
    import uvicorn
    print(f"""
╔════════════════════════════════════════════════════════════╗
║       知识胶囊服务 V2.1 (EvoMap Enhanced)                   ║
╠════════════════════════════════════════════════════════════╣
║  版本: 2.1.0                                               ║
║  端口: 8005                                                ║
╠════════════════════════════════════════════════════════════╣
║  核心功能:                                                  ║
║  ✓ 内容寻址 (SHA256)                                       ║
║  ✓ DATM 四维评分                                           ║
║  ✓ Gene 策略模板                                           ║
║  ✓ 进化事件追踪                                            ║
║  ✓ 活胶囊版本控制                                          ║
╠════════════════════════════════════════════════════════════╣
║  V2.1 增强功能:                                            ║
║  {'✓ 语义向量搜索' if SEMANTIC_ENABLED else '✗ 语义向量搜索 (需安装依赖)'}       ║
║  {'✓ 跨域关联引擎' if ENHANCEMENTS_ENABLED else '✗ 跨域关联引擎'}              ║
║  {'✓ 多模态支持' if ENHANCEMENTS_ENABLED else '✗ 多模态支持'}                  ║
║  {'✓ 智能推荐' if ENHANCEMENTS_ENABLED else '✗ 智能推荐'}                      ║
╚════════════════════════════════════════════════════════════╝
    """)
    uvicorn.run(app, host="0.0.0.0", port=8005)
