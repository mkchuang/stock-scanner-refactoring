"""
緩存管理模組的單元測試
"""

import pytest
import time
from datetime import datetime, timedelta
from pathlib import Path
import tempfile
import shutil
from src.core.cache import (
    CacheManager, MemoryCacheBackend, FileCacheBackend,
    get_cache_manager
)
from src.core.constants import CACHE_TYPE


class TestMemoryCacheBackend:
    """內存緩存後端測試"""
    
    def test_basic_operations(self):
        """測試基本操作"""
        cache = MemoryCacheBackend()
        
        # 測試 set 和 get
        cache.set("test_key", "test_value")
        assert cache.get("test_key") == "test_value"
        
        # 測試 exists
        assert cache.exists("test_key") is True
        assert cache.exists("non_existent") is False
        
        # 測試 delete
        assert cache.delete("test_key") is True
        assert cache.get("test_key") is None
        assert cache.delete("non_existent") is False
        
    def test_ttl(self):
        """測試過期時間"""
        cache = MemoryCacheBackend()
        
        # 設置 1 秒過期
        cache.set("ttl_key", "ttl_value", ttl=1)
        assert cache.get("ttl_key") == "ttl_value"
        
        # 等待過期
        time.sleep(1.1)
        assert cache.get("ttl_key") is None
        
    def test_no_ttl(self):
        """測試無過期時間"""
        cache = MemoryCacheBackend()
        
        # 不設置過期時間
        cache.set("no_ttl_key", "no_ttl_value")
        
        # 等待一段時間後仍然存在
        time.sleep(0.5)
        assert cache.get("no_ttl_key") == "no_ttl_value"
        
    def test_clear(self):
        """測試清空緩存"""
        cache = MemoryCacheBackend()
        
        # 設置多個值
        cache.set("key1", "value1")
        cache.set("key2", "value2")
        cache.set("key3", "value3")
        
        # 清空
        cache.clear()
        
        # 驗證全部清空
        assert cache.get("key1") is None
        assert cache.get("key2") is None
        assert cache.get("key3") is None
        
    def test_stats(self):
        """測試統計信息"""
        cache = MemoryCacheBackend()
        
        # 初始狀態
        stats = cache.get_stats()
        assert stats['hits'] == 0
        assert stats['misses'] == 0
        
        # 執行一些操作
        cache.set("key1", "value1")
        cache.get("key1")  # hit
        cache.get("key2")  # miss
        cache.delete("key1")
        
        stats = cache.get_stats()
        assert stats['hits'] == 1
        assert stats['misses'] == 1
        assert stats['sets'] == 1
        assert stats['deletes'] == 1
        
    def test_thread_safety(self):
        """測試線程安全性"""
        import threading
        
        cache = MemoryCacheBackend()
        results = []
        
        def worker(thread_id):
            for i in range(100):
                key = f"thread_{thread_id}_key_{i}"
                cache.set(key, f"value_{i}")
                value = cache.get(key)
                if value == f"value_{i}":
                    results.append(True)
                else:
                    results.append(False)
                    
        threads = []
        for i in range(5):
            t = threading.Thread(target=worker, args=(i,))
            threads.append(t)
            t.start()
            
        for t in threads:
            t.join()
            
        # 所有操作都應該成功
        assert all(results)
        assert len(results) == 500
        
    def test_clean_expired(self):
        """測試清理過期項"""
        cache = MemoryCacheBackend()
        
        # 設置不同過期時間的項
        cache.set("expire_1", "value1", ttl=1)
        cache.set("expire_2", "value2", ttl=2)
        cache.set("no_expire", "value3")
        
        # 等待第一個過期
        time.sleep(1.1)
        
        # 清理過期項
        cache.clean_expired()
        
        # 驗證結果
        assert cache.get("expire_1") is None
        assert cache.get("expire_2") == "value2"
        assert cache.get("no_expire") == "value3"


class TestFileCacheBackend:
    """文件緩存後端測試"""
    
    def setup_method(self):
        """測試前準備"""
        self.temp_dir = tempfile.mkdtemp()
        
    def teardown_method(self):
        """測試後清理"""
        shutil.rmtree(self.temp_dir)
        
    def test_basic_operations(self):
        """測試基本操作"""
        cache = FileCacheBackend(self.temp_dir)
        
        # 測試 set 和 get
        cache.set("test_key", {"data": "test_value"})
        assert cache.get("test_key") == {"data": "test_value"}
        
        # 測試 exists
        assert cache.exists("test_key") is True
        assert cache.exists("non_existent") is False
        
        # 測試 delete
        assert cache.delete("test_key") is True
        assert cache.get("test_key") is None
        
    def test_ttl(self):
        """測試過期時間"""
        cache = FileCacheBackend(self.temp_dir)
        
        # 設置 1 秒過期
        cache.set("ttl_key", "ttl_value", ttl=1)
        assert cache.get("ttl_key") == "ttl_value"
        
        # 等待過期
        time.sleep(1.1)
        assert cache.get("ttl_key") is None
        
        # 驗證文件已被刪除
        cache_files = list(Path(self.temp_dir).glob("*.cache"))
        assert len(cache_files) == 0
        
    def test_clear(self):
        """測試清空緩存"""
        cache = FileCacheBackend(self.temp_dir)
        
        # 設置多個值
        cache.set("key1", "value1")
        cache.set("key2", "value2")
        cache.set("key3", "value3")
        
        # 驗證文件創建
        cache_files = list(Path(self.temp_dir).glob("*.cache"))
        assert len(cache_files) == 3
        
        # 清空
        cache.clear()
        
        # 驗證文件刪除
        cache_files = list(Path(self.temp_dir).glob("*.cache"))
        assert len(cache_files) == 0
        
    def test_stats(self):
        """測試統計信息"""
        cache = FileCacheBackend(self.temp_dir)
        
        # 設置一些數據
        cache.set("key1", "x" * 1000)  # 1KB 數據
        cache.set("key2", "y" * 2000)  # 2KB 數據
        
        stats = cache.get_stats()
        assert stats['total_keys'] == 2
        assert stats['total_size_mb'] > 0
        
    def test_complex_data_types(self):
        """測試複雜數據類型"""
        cache = FileCacheBackend(self.temp_dir)
        
        # 測試各種數據類型
        test_data = {
            "list": [1, 2, 3, "test"],
            "dict": {"a": 1, "b": 2},
            "tuple": (1, 2, 3),
            "nested": {
                "list": [{"a": 1}, {"b": 2}],
                "data": "test"
            }
        }
        
        cache.set("complex", test_data)
        retrieved = cache.get("complex")
        
        assert retrieved == test_data


class TestCacheManager:
    """緩存管理器測試"""
    
    def test_memory_backend(self):
        """測試使用內存後端"""
        manager = CacheManager()
        
        # 基本操作
        manager.set(CACHE_TYPE.PRICE, "stock_001", {"price": 100})
        assert manager.get(CACHE_TYPE.PRICE, "stock_001") == {"price": 100}
        
        # 不同類型的緩存
        manager.set(CACHE_TYPE.NEWS, "news_001", {"title": "test news"})
        assert manager.get(CACHE_TYPE.NEWS, "news_001") == {"title": "test news"}
        
    def test_file_backend(self):
        """測試使用文件後端"""
        with tempfile.TemporaryDirectory() as temp_dir:
            # 創建配置
            config = {
                "cache": {
                    "backend": "file",
                    "file_cache_dir": temp_dir
                }
            }
            
            from src.core.config import ConfigManager
            test_config = ConfigManager()
            test_config._config = config
            
            manager = CacheManager(config=test_config)
            
            # 基本操作
            manager.set(CACHE_TYPE.FUNDAMENTAL, "fund_001", {"pe": 15.5})
            assert manager.get(CACHE_TYPE.FUNDAMENTAL, "fund_001") == {"pe": 15.5}
            
    def test_default_ttl(self):
        """測試默認 TTL"""
        manager = CacheManager()
        
        # 使用默認 TTL
        manager.set(CACHE_TYPE.PRICE, "ttl_test", "value")
        assert manager.exists(CACHE_TYPE.PRICE, "ttl_test") is True
        
    def test_custom_ttl(self):
        """測試自定義 TTL"""
        manager = CacheManager()
        
        # 使用自定義 TTL
        manager.set(CACHE_TYPE.ANALYSIS, "custom_ttl", "value", ttl=1)
        assert manager.get(CACHE_TYPE.ANALYSIS, "custom_ttl") == "value"
        
        # 等待過期
        time.sleep(1.1)
        assert manager.get(CACHE_TYPE.ANALYSIS, "custom_ttl") is None
        
    def test_batch_operations(self):
        """測試批量操作"""
        manager = CacheManager()
        
        # 批量設置
        items = {
            "key1": "value1",
            "key2": "value2",
            "key3": "value3"
        }
        manager.batch_set(CACHE_TYPE.PRICE, items)
        
        # 批量獲取
        keys = ["key1", "key2", "key3", "key4"]
        result = manager.batch_get(CACHE_TYPE.PRICE, keys)
        
        assert len(result) == 3
        assert result["key1"] == "value1"
        assert result["key2"] == "value2"
        assert result["key3"] == "value3"
        assert "key4" not in result
        
    def test_get_or_set(self):
        """測試 get_or_set"""
        manager = CacheManager()
        
        call_count = 0
        
        def factory():
            nonlocal call_count
            call_count += 1
            return {"computed": "value"}
            
        # 第一次調用，應該執行 factory
        result1 = manager.get_or_set(CACHE_TYPE.ANALYSIS, "compute_key", factory)
        assert result1 == {"computed": "value"}
        assert call_count == 1
        
        # 第二次調用，應該從緩存獲取
        result2 = manager.get_or_set(CACHE_TYPE.ANALYSIS, "compute_key", factory)
        assert result2 == {"computed": "value"}
        assert call_count == 1  # factory 不應該再次被調用
        
    def test_clear_operations(self):
        """測試清空操作"""
        manager = CacheManager()
        
        # 設置多個緩存
        manager.set(CACHE_TYPE.PRICE, "price_1", "value1")
        manager.set(CACHE_TYPE.NEWS, "news_1", "value2")
        
        # 清空所有
        manager.clear_all()
        
        assert manager.get(CACHE_TYPE.PRICE, "price_1") is None
        assert manager.get(CACHE_TYPE.NEWS, "news_1") is None
        
    def test_stats(self):
        """測試統計信息"""
        manager = CacheManager()
        
        # 執行一些操作
        manager.set(CACHE_TYPE.PRICE, "key1", "value1")
        manager.get(CACHE_TYPE.PRICE, "key1")  # hit
        manager.get(CACHE_TYPE.PRICE, "key2")  # miss
        
        stats = manager.get_stats()
        assert stats['hits'] > 0
        assert stats['misses'] > 0
        assert stats['hit_rate'] >= 0
        
    def test_singleton_get_cache_manager(self):
        """測試獲取全局緩存管理器單例"""
        manager1 = get_cache_manager()
        manager2 = get_cache_manager()
        
        # 應該是同一個實例
        assert manager1 is manager2
        
        # 測試功能
        manager1.set(CACHE_TYPE.PRICE, "singleton_test", "value")
        assert manager2.get(CACHE_TYPE.PRICE, "singleton_test") == "value"