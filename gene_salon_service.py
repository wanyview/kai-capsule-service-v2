"""
基因沙龙 (Gene Salon) 服务模块
知识策略讨论场域
"""
import hashlib
import json
import sqlite3
from datetime import datetime
from typing import List, Dict, Optional
from dataclasses import dataclass, asdict
from enum import Enum

# ===================== 配置 =====================
DB_PATH = "/Users/wanyview/clawd/capsule_service_v2/capsules.db"

# ===================== 数据模型 =====================

class GeneType(str, Enum):
    REPAIR = "repair"       # 修复型
    OPTIMIZE = "optimize"   # 优化型
    INNOVATE = "innovate"   # 创新型
    EXPLORE = "explore"     # 探索型

class SalonStatus(str, Enum):
    PREPARING = "preparing"   # 准备中
    ACTIVE = "active"         # 进行中
    COMPLETED = "completed"   # 已完成
    ARCHIVED = "archived"     # 已归档

@dataclass
class Debate:
    """辩论发言"""
    id: str
    round: int
    speaker: str
    content: str
    gene_type: str
    upvotes: int = 0
    timestamp: str = ""

@dataclass
class GeneSalon:
    """基因沙龙"""
    id: str
    gene_type: GeneType
    topic: str
    description: str
    host: str
    participants: List[str]
    debates: List[Debate]
    status: SalonStatus
    capsule_id: Optional[str] = None
    created_at: str = ""
    updated_at: str = ""

# ===================== 数据库 =====================

def init_salon_db():
    """初始化沙龙数据库"""
    conn = sqlite3.connect(DB_PATH, check_same_thread=False)
    cursor = conn.cursor()
    
    # 沙龙表
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS gene_salons (
            id TEXT PRIMARY KEY,
            data TEXT NOT NULL,
            gene_type TEXT,
            topic TEXT,
            host TEXT,
            status TEXT,
            capsule_id TEXT,
            created_at TEXT,
            updated_at TEXT
        )
    ''')
    
    # 辩论记录表
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS salon_debates (
            id TEXT PRIMARY KEY,
            salon_id TEXT NOT NULL,
            round INTEGER,
            speaker TEXT,
            content TEXT,
            gene_type TEXT,
            upvotes INTEGER DEFAULT 0,
            timestamp TEXT,
            FOREIGN KEY (salon_id) REFERENCES gene_salons(id)
        )
    ''')
    
    conn.commit()
    conn.close()

# ===================== 沙龙操作 =====================

def generate_salon_id(topic: str) -> str:
    """生成沙龙ID"""
    timestamp = datetime.utcnow().strftime("%Y%m%d")
    raw = f"{timestamp}{topic}"
    return f"salon_{timestamp}_{hashlib.md5(raw.encode()).hexdigest()[:8]}"

def create_salon(gene_type: str, topic: str, description: str, host: str = "Kai") -> GeneSalon:
    """创建基因沙龙"""
    conn = sqlite3.connect(DB_PATH, check_same_thread=False)
    cursor = conn.cursor()
    
    now = datetime.utcnow().isoformat()
    salon_id = generate_salon_id(topic)
    
    salon = GeneSalon(
        id=salon_id,
        gene_type=GeneType(gene_type),
        topic=topic,
        description=description,
        host=host,
        participants=[host],
        debates=[],
        status=SalonStatus.PREPARING,
        created_at=now,
        updated_at=now
    )
    
    cursor.execute('''
        INSERT INTO gene_salons (id, data, gene_type, topic, host, status, created_at, updated_at)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
    ''', (salon_id, json.dumps(asdict(salon)), gene_type, topic, host, 
          SalonStatus.PREPARING.value, now, now))
    
    conn.commit()
    conn.close()
    
    return salon

def get_salon(salon_id: str) -> Optional[GeneSalon]:
    """获取沙龙详情"""
    conn = sqlite3.connect(DB_PATH, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    
    cursor.execute("SELECT data FROM gene_salons WHERE id = ?", (salon_id,))
    row = cursor.fetchone()
    conn.close()
    
    if row:
        data = json.loads(row['data'])
        return GeneSalon(**data)
    return None

def list_salons(status: str = None, limit: int = 20) -> List[GeneSalon]:
    """列出沙龙"""
    conn = sqlite3.connect(DB_PATH, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    
    if status:
        cursor.execute("SELECT data FROM gene_salons WHERE status = ? ORDER BY created_at DESC LIMIT ?", 
                      (status, limit))
    else:
        cursor.execute("SELECT data FROM gene_salons ORDER BY created_at DESC LIMIT ?", (limit,))
    
    salons = []
    for row in cursor.fetchall():
        data = json.loads(row['data'])
        salons.append(GeneSalon(**data))
    
    conn.close()
    return salons

def add_debate(salon_id: str, speaker: str, content: str) -> Debate:
    """添加辩论发言"""
    conn = sqlite3.connect(DB_PATH, check_same_thread=False)
    cursor = conn.cursor()
    
    # 获取当前沙龙信息
    salon = get_salon(salon_id)
    if not salon:
        raise ValueError("沙龙不存在")
    
    now = datetime.utcnow().isoformat()
    debate_id = f"debate_{hashlib.md5(f'{salon_id}{speaker}{now}'.encode()).hexdigest()[:12]}"
    
    # 确定轮次
    round_num = len(salon.debates) // len(salon.participants) + 1 if salon.participants else 1
    
    debate = Debate(
        id=debate_id,
        round=round_num,
        speaker=speaker,
        content=content,
        gene_type=salon.gene_type.value if hasattr(salon.gene_type, 'value') else salon.gene_type,
        timestamp=now
    )
    
    # 存储辩论
    cursor.execute('''
        INSERT INTO salon_debates (id, salon_id, round, speaker, content, gene_type, timestamp)
        VALUES (?, ?, ?, ?, ?, ?, ?)
    ''', (debate_id, salon_id, round_num, speaker, content, 
          salon.gene_type.value if hasattr(salon.gene_type, 'value') else salon.gene_type, now))
    
    # 更新沙龙状态
    cursor.execute('''
        UPDATE gene_salons SET status = ?, updated_at = ? WHERE id = ?
    ''', (SalonStatus.ACTIVE.value, now, salon_id))
    
    conn.commit()
    conn.close()
    
    return debate

def start_salon(salon_id: str) -> GeneSalon:
    """开始沙龙（从准备转为进行）"""
    conn = sqlite3.connect(DB_PATH, check_same_thread=False)
    cursor = conn.cursor()
    
    now = datetime.utcnow().isoformat()
    cursor.execute('''
        UPDATE gene_salons SET status = ?, updated_at = ? WHERE id = ?
    ''', (SalonStatus.ACTIVE.value, now, salon_id))
    
    conn.commit()
    conn.close()
    
    return get_salon(salon_id)

def complete_salon(salon_id: str, capsule_id: str) -> GeneSalon:
    """完成沙龙（产出知识胶囊）"""
    conn = sqlite3.connect(DB_PATH, check_same_thread=False)
    cursor = conn.cursor()
    
    now = datetime.utcnow().isoformat()
    cursor.execute('''
        UPDATE gene_salons SET status = ?, capsule_id = ?, updated_at = ? WHERE id = ?
    ''', (SalonStatus.COMPLETED.value, capsule_id, now, salon_id))
    
    conn.commit()
    conn.close()
    
    return get_salon(salon_id)

def get_salon_debates(salon_id: str) -> List[Debate]:
    """获取沙龙的所有辩论"""
    conn = sqlite3.connect(DB_PATH, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    
    cursor.execute('''
        SELECT * FROM salon_debates WHERE salon_id = ? ORDER BY round, timestamp
    ''', (salon_id,))
    
    debates = []
    for row in cursor.fetchall():
        debates.append(Debate(
            id=row['id'],
            round=row['round'],
            speaker=row['speaker'],
            content=row['content'],
            gene_type=row['gene_type'],
            upvotes=row['upvotes'],
            timestamp=row['timestamp']
        ))
    
    conn.close()
    return debates

# ===================== 预设 Gene 模板 =====================

DEFAULT_GENES = {
    "repair": {
        "signals_match": ["bug", "错误", "修复", "问题", "故障", "缺陷"],
        "summary": "修复型策略 - 识别并解决特定问题",
        "intent": "repair"
    },
    "optimize": {
        "signals_match": ["优化", "改进", "提升", "效率", "性能"],
        "summary": "优化型策略 - 改进现有方案",
        "intent": "optimize"
    },
    "innovate": {
        "signals_match": ["创新", "突破", "新方案", "颠覆", "革命"],
        "summary": "创新型策略 - 探索全新可能性",
        "intent": "innovate"
    },
    "explore": {
        "signals_match": ["探索", "尝试", "研究", "实验", "未知"],
        "summary": "探索型策略 - 探索未知领域",
        "intent": "explore"
    }
}

# ===================== 测试 =====================

if __name__ == "__main__":
    init_salon_db()
    
    # 创建测试沙龙
    salon = create_salon(
        gene_type="optimize",
        topic="如何优化知识胶囊的检索效率？",
        description="讨论提升知识胶囊搜索性能的方案",
        host="Kai"
    )
    print(f"✅ 创建沙龙: {salon.id}")
    print(f"   主题: {salon.topic}")
    print(f"   类型: {salon.gene_type.value}")
    
    # 添加发言
    debate1 = add_debate(salon.id, "Kai", "我认为可以引入向量索引来提升搜索效率。")
    print(f"\n✅ 添加发言: {debate1.content[:30]}...")
    
    # 获取列表
    salons = list_salons()
    print(f"\n📋 沙龙列表: {len(salons)} 个")
    
    # 开始沙龙
    active_salon = start_salon(salon.id)
    print(f"\n▶️ 沙龙状态: {active_salon.status.value}")
