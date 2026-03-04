"""
知识胶囊 V2.1 搜索模块
兼容 V1 和 V2 数据结构
"""
import json
import sqlite3
from typing import List, Dict

# 尝试连接数据库，优先V2
DB_PATHS = [
    "/Users/wanyview/clawd/capsule_service_v2/capsules.db",  # V2 (优先)
    "/Users/wanyview/clawd/capsule_service/capsules.db"  # V1 (备用)
]

def get_db():
    """获取可用的数据库"""
    for db_path in DB_PATHS:
        try:
            conn = sqlite3.connect(db_path)
            cursor = conn.execute("SELECT COUNT(*) FROM capsules")
            cursor.fetchone()
            return conn, db_path
        except:
            continue
    raise Exception("No database available")

DB_PATH = get_db()[1]

# ===================== 工具函数 =====================

def parse_capsule(row) -> Dict:
    """解析胶囊数据 (兼容 V1 和 V2)"""
    if 'data' in row.keys():
        # V2: JSON in 'data' column
        return json.loads(row['data'])
    else:
        # V1: 扁平结构
        return {
            'id': row['id'],
            'title': row['title'],
            'content': row['content'],
            'domain': row['domain'],
            'tags': json.loads(row['tags']) if row['tags'] else [],
            'datm_score': row['datm_score'],
            'author': row['author']
        }

def get_all_capsules() -> List[Dict]:
    """获取所有胶囊"""
    conn, _ = get_db()
    conn.row_factory = sqlite3.Row
    cursor = conn.execute("SELECT * FROM capsules")
    capsules = [parse_capsule(dict(row)) for row in cursor.fetchall()]
    conn.close()
    return capsules

# ===================== 改进的搜索 =====================

def simple_semantic_search(query: str, limit: int = 10) -> List[Dict]:
    """简单但有效的语义搜索"""
    capsules = get_all_capsules()
    
    # 查询词处理
    query_lower = query.lower()
    query_words = set(query_lower.split())
    
    results = []
    
    for cap in capsules:
        title = cap.get('title', '')
        content = cap.get('content', '')
        domain = cap.get('domain', 'unknown')
        tags = cap.get('tags', [])
        
        # 组合所有文本
        all_text = f"{title} {content} {' '.join(tags)}".lower()
        
        # 计算得分
        score = 0
        
        # 标题精确匹配 (最高权重)
        if query_lower in title.lower():
            score += 10
        
        # 关键词匹配
        for word in query_words:
            if word in all_text:
                score += 1
            # 中文包含
            if len(word) >= 2 and word in all_text:
                score += 2
        
        # 标签匹配
        for tag in tags:
            if query_lower in str(tag).lower():
                score += 5
        
        if score > 0:
            results.append({
                "capsule_id": cap['id'],
                "title": title,
                "domain": domain,
                "score": score,
                "excerpt": content[:100] + "..." if len(content) > 100 else content,
                "tags": tags
            })
    
    # 排序返回
    results.sort(key=lambda x: x['score'], reverse=True)
    return results[:limit]

def get_domain_graph() -> Dict:
    """获取领域知识图谱"""
    capsules = get_all_capsules()
    
    # 领域统计
    domain_counts = {}
    for cap in capsules:
        domain = cap.get('domain', 'unknown')
        domain_counts[domain] = domain_counts.get(domain, 0) + 1
    
    # 跨域标签分析
    domain_tags = {}
    for cap in capsules:
        domain = cap.get('domain', 'unknown')
        tags = cap.get('tags', [])
        for tag in tags:
            if tag not in domain_tags:
                domain_tags[tag] = set()
            domain_tags[tag].add(domain)
    
    # 构建边 (跨域共享标签)
    edges = []
    for tag, domains in domain_tags.items():
        if len(domains) > 1:
            domains_list = list(domains)
            for i in range(len(domains_list) - 1):
                edges.append({
                    "source": domains_list[i],
                    "target": domains_list[i+1],
                    "label": tag,
                    "strength": len(domains)
                })
    
    return {
        "nodes": [{"id": d, "label": d, "count": c} for d, c in domain_counts.items()],
        "edges": edges[:20]
    }

def get_related_capsules(capsule_id: str, limit: int = 5) -> List[Dict]:
    """获取相关胶囊"""
    capsules = get_all_capsules()
    
    # 找目标胶囊
    target = None
    for c in capsules:
        if c['id'] == capsule_id:
            target = c
            break
    
    if not target:
        return []
    
    target_domain = target.get('domain', '')
    target_tags = target.get('tags', [])
    target_title = target.get('title', '')
    
    related = []
    for cap in capsules:
        if cap['id'] == capsule_id:
            continue
        
        domain = cap.get('domain', '')
        tags = cap.get('tags', [])
        title = cap.get('title', '')
        
        score = 0
        
        # 同领域
        if domain == target_domain:
            score += 3
        
        # 共享标签
        shared = set(tags) & set(target_tags)
        score += len(shared) * 2
        
        # 标题相似 (简单词匹配)
        title_words = set(title.lower().split())
        target_words = set(target_title.lower().split())
        title_overlap = len(title_words & target_words)
        score += title_overlap
        
        if score > 0:
            related.append({
                "capsule_id": cap['id'],
                "title": title,
                "domain": domain,
                "score": score,
                "reason": "领域相同" if domain == target_domain else "标签关联"
            })
    
    related.sort(key=lambda x: x['score'], reverse=True)
    return related[:limit]

# ===================== 测试 =====================

if __name__ == "__main__":
    print("🔍 知识胶囊搜索测试")
    print("=" * 40)
    print(f"使用数据库: {DB_PATH}")
    
    # 搜索测试
    tests = ["物理", "测试", "发明", "技术", "牛顿"]
    for query in tests:
        results = simple_semantic_search(query, limit=3)
        print(f"\n搜索 '{query}': {len(results)} 条")
        for r in results[:3]:
            print(f"  ✓ {r['title']} (score:{r['score']}, domain:{r['domain']})")
    
    # 知识图谱
    print("\n\n📊 知识图谱:")
    graph = get_domain_graph()
    print(f"  领域节点: {len(graph['nodes'])}")
    for node in graph['nodes']:
        print(f"    - {node['label']}: {node['count']} 个胶囊")
    
    print(f"  跨域边: {len(graph['edges'])}")
    
    # 相关胶囊测试
    print("\n\n🔗 相关胶囊推荐:")
    capsules = get_all_capsules()
    if capsules:
        first_id = capsules[0]['id']
        print(f"  基于 {first_id} 的推荐:")
        related = get_related_capsules(first_id, limit=3)
        for r in related:
            print(f"    - {r['title']} (score:{r['score']}, reason:{r['reason']})")
