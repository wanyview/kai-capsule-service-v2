#!/usr/bin/env python3
"""
知识胶囊服务 API 测试用例
"""
import requests
import json
import time

BASE_URL = "http://localhost:8005"

def test_health():
    """测试服务健康"""
    r = requests.get(f"{BASE_URL}/")
    assert r.status_code == 200
    data = r.json()
    assert data["status"] == "running"
    print("✅ 健康检查通过")

def test_create_capsule():
    """测试创建胶囊"""
    data = {
        "title": f"测试胶囊 {int(time.time())}",
        "content": "这是测试内容",
        "domain": "test",
        "tags": ["测试", "自动化"]
    }
    r = requests.post(f"{BASE_URL}/capsules", json=data)
    assert r.status_code == 200
    result = r.json()
    assert "id" in result
    print(f"✅ 创建胶囊成功: {result['id']}")
    return result["id"]

def test_list_capsules():
    """测试列出胶囊"""
    r = requests.get(f"{BASE_URL}/capsules?limit=5")
    assert r.status_code == 200
    result = r.json()
    assert "capsules" in result
    print(f"✅ 列出胶囊: {result['total']} 个")
    return result

def test_pull_capsules():
    """测试拉取胶囊API"""
    data = {"limit": 3}
    r = requests.post(f"{BASE_URL}/api/v1/capsule/pull", json=data)
    assert r.status_code == 200
    result = r.json()
    assert "capsules" in result
    print(f"✅ 拉取胶囊: {result['count']} 个")
    return result

def test_sync_capsule():
    """测试同步胶囊API"""
    data = {
        "id": f"test_sync_{int(time.time())}",
        "title": "同步测试胶囊",
        "content": "这是通过同步API创建的",
        "category": "test",
        "tags": ["同步", "测试"],
        "author": {"id": "test", "name": "测试", "platform": "test"}
    }
    r = requests.post(f"{BASE_URL}/api/v1/capsule/sync", json=data)
    assert r.status_code == 200
    result = r.json()
    assert result["success"] == True
    print(f"✅ 同步胶囊成功: {result['capsule_id']}")
    return result["capsule_id"]

def test_batch_sync():
    """测试批量同步"""
    data = {
        "capsules": [
            {"id": f"batch_{int(time.time())}_1", "title": "批量1", "content": "内容1", "category": "test", "tags": ["批量"], "author": {"id": "test", "name": "测试"}},
            {"id": f"batch_{int(time.time())}_2", "title": "批量2", "content": "内容2", "category": "test", "tags": ["批量"], "author": {"id": "test", "name": "测试"}},
        ]
    }
    r = requests.post(f"{BASE_URL}/api/v1/capsule/batch-sync", json=data)
    assert r.status_code == 200
    result = r.json()
    assert result["success"] >= 1
    print(f"✅ 批量同步: {result['success']}/{result['total']}")
    return result

def test_domains():
    """测试获取领域列表"""
    r = requests.get(f"{BASE_URL}/api/v1/capsule/pull/domains")
    assert r.status_code == 200
    result = r.json()
    assert "domains" in result
    print(f"✅ 可用领域: {result['domains']}")
    return result

def test_tags():
    """测试获取标签列表"""
    r = requests.get(f"{BASE_URL}/api/v1/capsule/pull/tags")
    assert r.status_code == 200
    result = r.json()
    assert "tags" in result
    print(f"✅ 可用标签: {len(result['tags'])} 个")
    return result

def test_stats():
    """测试统计信息"""
    try:
        r = requests.get(f"{BASE_URL}/stats")
        if r.status_code == 200:
            print("✅ 统计接口正常")
        else:
            print("⚠️ 统计接口暂不可用")
    except Exception as e:
        print(f"⚠️ 统计接口错误: {e}")

def run_all_tests():
    """运行所有测试"""
    print("=" * 50)
    print("开始测试知识胶囊服务 API")
    print("=" * 50)
    
    try:
        test_health()
        test_stats()
        test_create_capsule()
        test_list_capsules()
        test_domains()
        test_tags()
        test_pull_capsules()
        test_sync_capsule()
        test_batch_sync()
        
        print("=" * 50)
        print("🎉 所有测试通过!")
        print("=" * 50)
    except Exception as e:
        print(f"❌ 测试失败: {e}")
        raise

if __name__ == "__main__":
    run_all_tests()
