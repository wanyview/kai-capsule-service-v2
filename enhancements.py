"""
知识胶囊 V2.1 增强模块
- 语义向量搜索
- 跨域关联引擎
- 多模态支持
- 智能推荐
"""
import hashlib
import json
import sqlite3
import os
from datetime import datetime
from typing import Optional, List, Dict, Any
from dataclasses import dataclass, asdict
from enum import Enum

# ===================== 配置 =====================
DB_PATH = "/Users/wanyview/clawd/capsule_service_v2/capsules.db"

# ===================== 尝试导入向量化 =====================
try:
    from sentence_transformers import SentenceTransformer
    SEMANTIC_ENABLED = True
    _embedding_model = None
except ImportError:
    SEMANTIC_ENABLED = False
    print("⚠️ sentence-transformers 未安装，语义搜索不可用")

# ===================== 数据模型 =====================

class MultimediaType(str, Enum):
    IMAGE = "image"
    AUDIO = "audio"
    VIDEO = "video"
    DOCUMENT = "document"

@dataclass
class MultimediaAsset:
    """多媒体资源"""
    id: str
    capsule_id: str
    type: MultimediaType
    filename: str
    url: str
    thumbnail: Optional[str] = None
    size: int = 0
    mime_type: str = ""
    metadata: Dict[str, Any] = None
    
    def to_dict(self) -> Dict:
        return {
            "id": self.id,
            "capsule_id": self.capsule_id,
            "type": self.type.value,
            "filename": self.filename,
            "url": self.url,
            "thumbnail": self.thumbnail,
            "size": self.size,
            "mime_type": self.mime_type,
            "metadata": self.metadata or {}
        }

@dataclass
class CrossDomainLink:
    """跨域知识链接"""
    id: str
    source_id: str
    target_id: str
    source_domain: str
    target_domain: str
    strength: float  # 0-1 连接强度
    reason: str      # 连接原因
    created_at: str

@dataclass
class Recommendation:
    """推荐结果"""
    capsule_id: str
    title: str
    reason: str
    score: float
    domain: str

# ===================== 数据库增强 =====================

def init_db_enhancements():
    """初始化增强功能数据库表"""
    conn = sqlite3.connect(DB_PATH, check_same_thread=False)
    cursor = conn.cursor()
    
    # 向量表
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS capsule_vectors (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            capsule_id TEXT UNIQUE NOT NULL,
            embedding BLOB NOT NULL,
            model TEXT NOT NULL,
            created_at TEXT NOT NULL
        )
    ''')
    
    # 多媒体资源表
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS multimedia_assets (
            id TEXT PRIMARY KEY,
            capsule_id TEXT NOT NULL,
            type TEXT NOT NULL,
            filename TEXT NOT NULL,
            url TEXT NOT NULL,
            thumbnail TEXT,
            size INTEGER DEFAULT 0,
            mime_type TEXT,
            metadata TEXT,
            created_at TEXT NOT NULL,
            FOREIGN KEY (capsule_id) REFERENCES capsules(id)
        )
    ''')
    
    # 跨域链接表
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS cross_domain_links (
            id TEXT PRIMARY KEY,
            source_id TEXT NOT NULL,
            target_id TEXT NOT NULL,
            source_domain TEXT NOT NULL,
            target_domain TEXT NOT NULL,
            strength REAL NOT NULL,
            reason TEXT,
            created_at TEXT NOT NULL,
            FOREIGN KEY (source_id) REFERENCES capsules(id),
            FOREIGN KEY (target_id) REFERENCES capsules(id)
        )
    ''')
    
    # 知识图谱节点
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS knowledge_graph_nodes (
            id TEXT PRIMARY KEY,
            domain TEXT NOT NULL,
            label TEXT NOT NULL,
            capsule_count INTEGER DEFAULT 0,
            created_at TEXT NOT NULL
        )
    ''')
    
    conn.commit()
    conn.close()

# ===================== 语义向量 =====================

def get_embedding_model():
    """获取嵌入模型"""
    global _embedding_model
    if not SEMANTIC_ENABLED:
        return None
    
    if _embedding_model is None:
        _embedding_model = SentenceTransformer('all-MiniLM-L6-v2')
    return _embedding_model

def compute_embedding(text: str) -> Optional[List[float]]:
    """计算文本嵌入向量"""
    if not SEMANTIC_ENABLED:
        return None
    
    model = get_embedding_model()
    if model:
        embedding = model.encode(text, convert_to_numpy=True)
        return embedding.tolist()
    return None

def store_embedding(capsule_id: str, embedding: List[float], model: str = "all-MiniLM-L6-v2"):
    """存储胶囊向量"""
    import numpy as np
    
    conn = sqlite3.connect(DB_PATH, check_same_thread=False)
    cursor = conn.cursor()
    
    # 转换为bytes存储
    embedding_bytes = np.array(embedding).tobytes()
    
    now = datetime.utcnow().isoformat()
    
    cursor.execute('''
        INSERT OR REPLACE INTO capsule_vectors (capsule_id, embedding, model, created_at)
        VALUES (?, ?, ?, ?)
    ''', (capsule_id, embedding_bytes, model, now))
    
    conn.commit()
    conn.close()

def semantic_search(query: str, limit: int = 10, min_score: float = 0.3) -> List[Dict]:
    """语义搜索胶囊"""
    if not SEMANTIC_ENABLED:
        return []
    
    import numpy as np
    
    # 计算查询向量
    query_embedding = compute_embedding(query)
    if query_embedding is None:
        return []
    
    conn = sqlite3.connect(DB_PATH, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    
    # 获取所有向量
    cursor.execute("SELECT capsule_id, embedding FROM capsule_vectors")
    rows = cursor.fetchall()
    
    results = []
    query_vec = np.array(query_embedding)
    
    for row in rows:
        capsule_id = row['capsule_id']
        emb = np.frombuffer(row['embedding'], dtype=np.float32)
        
        # 余弦相似度
        similarity = np.dot(query_vec, emb) / (np.linalg.norm(query_vec) * np.linalg.norm(emb) + 1e-8)
        
        if similarity >= min_score:
            # 获取胶囊信息
            cursor.execute("SELECT data FROM capsules WHERE id = ?", (capsule_id,))
            cap_row = cursor.fetchone()
            if cap_row:
                data = json.loads(cap_row['data'])
                results.append({
                    "capsule_id": capsule_id,
                    "title": data.get('title'),
                    "domain": data.get('domain'),
                    "score": round(float(similarity), 4),
                    "excerpt": data.get('content', '')[:200]
                })
    
    conn.close()
    
    results.sort(key=lambda x: x['score'], reverse=True)
    return results[:limit]

# ===================== 跨域关联 =====================

def analyze_cross_domain_links() -> List[CrossDomainLink]:
    """分析跨域知识链接"""
    conn = sqlite3.connect(DB_PATH, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    
    # 获取所有胶囊
    cursor.execute("SELECT id, title, content, domain, tags FROM capsules")
    capsules = cursor.fetchall()
    
    links = []
    now = datetime.utcnow().isoformat()
    
    # 简单的跨域关联算法
    for i, cap1 in enumerate(capsules):
        for cap2 in capsules[i+1:]:
            # 不同领域
            if cap1['domain'] == cap2['domain']:
                continue
            
            # 检查标签重叠
            tags1 = set(json.loads(cap1['tags']) if isinstance(cap1['tags'], str) else cap1['tags']) if cap1['tags'] else set()
            tags2 = set(json.loads(cap2['tags']) if isinstance(cap2['tags'], str) else cap2['tags']) if cap2['tags'] else set()
            
            overlap = len(tags1 & tags2)
            
            # 标题相似度 (简单词匹配)
            words1 = set(cap1['title'].lower().split())
            words2 = set(cap2['title'].lower().split())
            title_overlap = len(words1 & words2)
            
            # 计算连接强度
            strength = min(1.0, (overlap * 0.3 + title_overlap * 0.2))
            
            if strength > 0.3:
                link_id = hashlib.md5(f"{cap1['id']}{cap2['id']}".encode()).hexdigest()[:16]
                reason = f"共享标签: {tags1 & tags2}" if overlap > 0 else "跨域知识关联"
                
                links.append(CrossDomainLink(
                    id=link_id,
                    source_id=cap1['id'],
                    target_id=cap2['id'],
                    source_domain=cap1['domain'],
                    target_domain=cap2['domain'],
                    strength=strength,
                    reason=reason,
                    created_at=now
                ))
    
    conn.close()
    
    # 存储链接
    store_cross_domain_links(links)
    
    return links[:50]  # 返回前50个最强链接

def store_cross_domain_links(links: List[CrossDomainLink]):
    """存储跨域链接"""
    conn = sqlite3.connect(DB_PATH, check_same_thread=False)
    cursor = conn.cursor()
    
    for link in links:
        cursor.execute('''
            INSERT OR REPLACE INTO cross_domain_links 
            (id, source_id, target_id, source_domain, target_domain, strength, reason, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        ''', (link.id, link.source_id, link.target_id, link.source_domain, 
              link.target_domain, link.strength, link.reason, link.created_at))
    
    conn.commit()
    conn.close()

def get_domain_graph() -> Dict:
    """获取知识图谱"""
    conn = sqlite3.connect(DB_PATH, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    
    # 获取领域统计
    cursor.execute("SELECT domain, COUNT(*) as count FROM capsules GROUP BY domain")
    domains = {row['domain']: row['count'] for row in cursor.fetchall()}
    
    # 获取跨域链接
    cursor.execute("""
        SELECT source_domain, target_domain, COUNT(*) as link_count, AVG(strength) as avg_strength
        FROM cross_domain_links
        GROUP BY source_domain, target_domain
    """)
    edges = []
    for row in cursor.fetchall():
        edges.append({
            "source": row['source_domain'],
            "target": row['target_domain'],
            "count": row['link_count'],
            "strength": round(row['avg_strength'], 3)
        })
    
    conn.close()
    
    return {
        "nodes": [{"id": d, "label": d, "count": c} for d, c in domains.items()],
        "edges": edges
    }

# ===================== 多模态支持 =====================

def add_multimedia(capsule_id: str, file_type: str, filename: str, url: str, 
                   size: int = 0, mime_type: str = "", metadata: Dict = None) -> MultimediaAsset:
    """添加多媒体资源"""
    conn = sqlite3.connect(DB_PATH, check_same_thread=False)
    cursor = conn.cursor()
    
    asset_id = f"media_{hashlib.md5(f'{capsule_id}{filename}'.encode()).hexdigest()[:12]}"
    now = datetime.utcnow().isoformat()
    
    asset = MultimediaAsset(
        id=asset_id,
        capsule_id=capsule_id,
        type=MultimediaType(file_type),
        filename=filename,
        url=url,
        size=size,
        mime_type=mime_type,
        metadata=metadata or {}
    )
    
    cursor.execute('''
        INSERT INTO multimedia_assets (id, capsule_id, type, filename, url, size, mime_type, metadata, created_at)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
    ''', (asset.id, asset.capsule_id, asset.type.value, asset.filename, asset.url,
          asset.size, asset.mime_type, json.dumps(asset.metadata), now))
    
    conn.commit()
    conn.close()
    
    return asset

def get_capsule_multimedia(capsule_id: str) -> List[Dict]:
    """获取胶囊的所有多媒体资源"""
    conn = sqlite3.connect(DB_PATH, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    
    cursor.execute("SELECT * FROM multimedia_assets WHERE capsule_id = ?", (capsule_id,))
    assets = []
    for row in cursor.fetchall():
        asset = dict(row)
        asset['metadata'] = json.loads(asset['metadata']) if asset['metadata'] else {}
        assets.append(asset)
    
    conn.close()
    return assets

# ===================== 智能推荐 =====================

def recommend_capsules(capsule_id: str = None, domain: str = None, limit: int = 5) -> List[Recommendation]:
    """智能推荐胶囊"""
    conn = sqlite3.connect(DB_PATH, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    
    recommendations = []
    
    if capsule_id:
        # 基于胶囊的推荐
        cursor.execute("SELECT domain, tags, datm_score FROM capsules WHERE id = ?", (capsule_id,))
        row = cursor.fetchone()
        if row:
            target_domain = row['domain']
            target_tags = json.loads(row['tags']) if row['tags'] else []
            target_score = row['datm_score'] or 0
            
            # 找相似胶囊
            cursor.execute("""
                SELECT id, title, domain, tags, datm_score 
                FROM capsules 
                WHERE id != ? AND status = 'promoted'
                ORDER BY ABS(datm_score - ?) + 
                    CASE WHEN domain = ? THEN 0.3 ELSE 0 END
                LIMIT ?
            """, (capsule_id, target_score, target_domain, limit))
            
            for row in cursor.fetchall():
                tags = json.loads(row['tags']) if row['tags'] else []
                reason = "相似评分" if row['domain'] == target_domain else "跨域关联"
                recommendations.append(Recommendation(
                    capsule_id=row['id'],
                    title=row['title'],
                    reason=reason,
                    score=row['datm_score'] or 0,
                    domain=row['domain']
                ))
    
    elif domain:
        # 基于领域的推荐
        cursor.execute("""
            SELECT id, title, domain, datm_score 
            FROM capsules 
            WHERE domain = ? AND status = 'promoted'
            ORDER BY datm_score DESC
            LIMIT ?
        """, (domain, limit))
        
        for row in cursor.fetchall():
            recommendations.append(Recommendation(
                capsule_id=row['id'],
                title=row['title'],
                reason="高分" + domain + "胶囊",
                score=row['datm_score'] or 0,
                domain=row['domain']
            ))
    
    conn.close()
    return recommendations

# ===================== 版本时间线 =====================

def get_capsule_timeline(capsule_id: str) -> List[Dict]:
    """获取胶囊版本时间线"""
    conn = sqlite3.connect(DB_PATH, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    
    timeline = []
    
    # 查找所有版本
    cursor.execute("""
        SELECT id, version, updated_at, datm_score, status 
        FROM capsules 
        WHERE id = ? OR parent_id = ? OR parent_id = (
            SELECT parent_id FROM capsules WHERE id = ?
        )
        ORDER BY version DESC
    """, (capsule_id, capsule_id, capsule_id))
    
    for row in cursor.fetchall():
        timeline.append({
            "id": row['id'],
            "version": row['version'],
            "updated_at": row['updated_at'],
            "datm_score": row['datm_score'],
            "status": row['status']
        })
    
    conn.close()
    return timeline

# ===================== 初始化 =====================

if __name__ == "__main__":
    init_db_enhancements()
    print("✅ 知识胶囊 V2.1 增强模块初始化完成")
    print(f"✅ 语义搜索: {'可用' if SEMANTIC_ENABLED else '不可用 (需要安装 sentence-transformers)'}")
