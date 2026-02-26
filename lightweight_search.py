"""
知识胶囊 V2.1 轻量级语义搜索
不依赖外部模型的本地实现
"""
import re
import hashlib
import json
import sqlite3
from datetime import datetime
from typing import Optional, List, Dict
from dataclasses import dataclass, asdict

DB_PATH = "/Users/wanyview/clawd/capsule_service_v2/capsules.db"

# ===================== 轻量级文本处理 =====================

def tokenize(text: str) -> set:
    """中文分词 (简单实现)"""
    # 移除标点，转小写
    text = re.sub(r'[^\w\u4e00-\u9fff]', ' ', text.lower())
    # 提取词
    words = set()
    # 英文词
    words.update(re.findall(r'[a-z]+', text))
    # 尝试简单中文词分割 (2-4字)
    cn_chars = re.findall(r'[\u4e00-\u9fff]+', text)
    for chars in cn_chars:
        if len(chars) >= 2:
            # 滑动窗口提取
            for i in range(len(chars) - 1):
                words.add(chars[i:i+2])  # 2-gram
                if i < len(chars) - 2:
                    words.add(chars[i:i+3])  # 3-gram
    return words

def compute_text_similarity(text1: str, text2: str) -> float:
    """计算文本相似度 (Jaccard + TF-IDF 简化)"""
    tokens1 = tokenize(text1)
    tokens2 = tokenize(text2)
    
    if not tokens1 or not tokens2:
        return 0.0
    
    # Jaccard 相似度
    intersection = len(tokens1 & tokens2)
    union = len(tokens1 | tokens2)
    
    return intersection / union if union > 0 else 0.0

# ===================== 语义搜索 (轻量版) =====================

def lightweight_semantic_search(query: str, limit: int = 10, min_score: float = 0.1) -> List[Dict]:
    """轻量级语义搜索"""
    conn = sqlite3.connect(DB_PATH, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    
    # 获取所有胶囊 (data 是 JSON)
    cursor.execute("SELECT id, data FROM capsules")
    capsules = cursor.fetchall()
    
    results = []
    
    for cap in capsules:
        try:
            data = json.loads(cap['data'])
            title = data.get('title', '')
            content = data.get('content', '')
            domain = data.get('domain', 'unknown')
        except:
            continue
        
        # 组合文本
        full_text = f"{title} {content}"
        
        # 计算相似度
        score = compute_text_similarity(query, full_text)
        
        if score >= min_score:
            results.append({
                "capsule_id": cap['id'],
                "title": title,
                "domain": domain,
                "score": round(score, 4),
                "excerpt": content[:150] + "..." if len(content) > 150 else content
            })
    
    conn.close()
    
    # 排序返回
    results.sort(key=lambda x: x['score'], reverse=True)
    return results[:limit]

def analyze_cross_domain_light() -> List[Dict]:
    """轻量级跨域分析"""
    conn = sqlite3.connect(DB_PATH, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    
    cursor.execute("SELECT id, data FROM capsules")
    capsules = cursor.fetchall()
    
    links = []
    
    # 解析数据
    capsule_data = []
    for cap in capsules:
        try:
            data = json.loads(cap['data'])
            capsule_data.append({
                'id': cap['id'],
                'title': data.get('title', ''),
                'domain': data.get('domain', 'unknown')
            })
        except:
            continue
    
    for i, cap1 in enumerate(capsule_data):
        for cap2 in capsule_data[i+1:]:
            if cap1['domain'] == cap2['domain']:
                continue
            
            # 文本相似度
            score = compute_text_similarity(cap1['title'], cap2['title'])
            
            if score > 0.15:  # 阈值
                links.append({
                    "source_id": cap1['id'],
                    "target_id": cap2['id'],
                    "source_domain": cap1['domain'],
                    "target_domain": cap2['domain'],
                    "strength": round(score, 3),
                    "reason": f"内容关联"
                })
    
    conn.close()
    links.sort(key=lambda x: x['strength'], reverse=True)
    return links[:30]

# ===================== 快速测试 =====================

if __name__ == "__main__":
    print("🧪 轻量级语义搜索测试")
    print("-" * 40)
    
    # 测试分词
    text = "知识胶囊是AI时代的知识管理新范式"
    tokens = tokenize(text)
    print(f"分词结果: {tokens}")
    
    # 测试搜索
    results = lightweight_semantic_search("知识管理", limit=5)
    print(f"\n搜索 '知识管理' 返回 {len(results)} 条:")
    for r in results:
        print(f"  - {r['title']} (score: {r['score']}, domain: {r['domain']})")
    
    # 跨域分析
    print("\n🔗 跨域关联:")
    links = analyze_cross_domain_light()
    print(f"  发现 {len(links)} 个跨域连接")
    for link in links[:5]:
        print(f"  {link['source_domain']} ↔ {link['target_domain']} (strength: {link['strength']})")
