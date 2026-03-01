"""
capsule_service_v2 实时搜索增强模块
功能: 高速搜索 + 智能补全 + 热度排序
来源: 搜索优化算法
"""

import json
import time
from typing import List, Dict, Optional
from collections import defaultdict

class RealTimeSearch:
    """实时搜索增强引擎"""
    
    def __init__(self):
        self.capsules = []
        self.search_cache = {}
        self.hot_scores = defaultdict(float)
        self.cache_ttl = 300  # 5分钟缓存
        
    def index_capsules(self, capsules: List[Dict]):
        """索引胶囊"""
        self.capsules = capsules
        print(f"已索引 {len(capsules)} 个胶囊")
        
    def search(self, query: str, limit: int = 10) -> List[Dict]:
        """实时搜索"""
        # 检查缓存
        cache_key = f"{query}:{limit}"
        if cache_key in self.search_cache:
            cached_time, result = self.search_cache[cache_key]
            if time.time() - cached_time < self.cache_ttl:
                print(f"缓存命中: {query}")
                return result
        
        # 执行搜索
        results = self._execute_search(query)
        
        # 热度排序
        results = self._sort_by_hotness(results)
        
        # 缓存结果
        self.search_cache[cache_key] = (time.time(), results[:limit])
        
        return results[:limit]
    
    def _execute_search(self, query: str) -> List[Dict]:
        """执行搜索"""
        query_lower = query.lower()
        results = []
        
        for capsule in self.capsules:
            # 简单匹配
            title_match = query_lower in capsule.get("title", "").lower()
            content_match = query_lower in capsule.get("content", "").lower()
            tag_match = any(query_lower in tag.lower() for tag in capsule.get("tags", []))
            
            if title_match or content_match or tag_match:
                score = 0
                if title_match:
                    score += 10
                if content_match:
                    score += 5
                if tag_match:
                    score += 3
                results.append({**capsule, "score": score})
        
        return sorted(results, key=lambda x: x["score"], reverse=True)
    
    def _sort_by_hotness(self, results: List[Dict]) -> List[Dict]:
        """热度排序"""
        for result in results:
            capsule_id = result.get("id", "")
            hot_score = self.hot_scores.get(capsule_id, 0)
            result["score"] = result.get("score", 0) + hot_score
        return sorted(results, key=lambda x: x["score"], reverse=True)
    
    def update_hotness(self, capsule_id: str, increment: float = 1.0):
        """更新热度"""
        self.hot_scores[capsule_id] += increment
        # 清除相关缓存
        self.search_cache.clear()
        
    def get_suggestions(self, prefix: str, limit: int = 5) -> List[str]:
        """智能补全"""
        prefix_lower = prefix.lower()
        suggestions = set()
        
        for capsule in self.capsules:
            title = capsule.get("title", "")
            if title.lower().startswith(prefix_lower):
                suggestions.add(title)
            for tag in capsule.get("tags", []):
                if tag.lower().startswith(prefix_lower):
                    suggestions.add(tag)
        
        return list(suggestions)[:limit]

# 测试
if __name__ == "__main__":
    search = RealTimeSearch()
    
    # 模拟胶囊数据
    capsules = [
        {"id": "1", "title": "AI知识胶囊", "content": "关于人工智能的知识", "tags": ["AI", "机器学习"]},
        {"id": "2", "title": "物理知识胶囊", "content": "物理学基础知识", "tags": ["物理", "科学"]},
        {"id": "3", "title": "GPT-5研究", "content": "最新GPT模型研究", "tags": ["AI", "LLM", "GPT"]},
    ]
    
    search.index_capsules(capsules)
    
    # 测试搜索
    results = search.search("AI")
    print(json.dumps(results, ensure_ascii=False, indent=2))
    
    # 测试补全
    suggestions = search.get_suggestions("G")
    print(f"补全建议: {suggestions}")
