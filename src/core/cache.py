"""
統一緩存管理模組

提供統一的緩存管理功能，支援：
- 多種緩存後端（內存、文件、Redis等）
- 過期時間管理
- 緩存統計
- 批量操作
"""

import json
import pickle
import os
from datetime import datetime, timedelta
from typing import Any, Dict, Optional, Tuple, List, Union
from abc import ABC, abstractmethod
import threading
import hashlib
from pathlib import Path
from ..utils.logger import get_logger
from .config import ConfigManager as Config
from .constants import CACHE_DURATION, CACHE_TYPE

logger = get_logger(__name__)


class CacheBackend(ABC):
    """緩存後端抽象基類"""
    
    @abstractmethod
    def get(self, key: str) -> Optional[Any]:
        """獲取緩存值"""
        pass
        
    @abstractmethod
    def set(self, key: str, value: Any, ttl: Optional[int] = None):
        """設置緩存值"""
        pass
        
    @abstractmethod
    def delete(self, key: str) -> bool:
        """刪除緩存值"""
        pass
        
    @abstractmethod
    def exists(self, key: str) -> bool:
        """檢查緩存是否存在"""
        pass
        
    @abstractmethod
    def clear(self):
        """清空所有緩存"""
        pass
        
    @abstractmethod
    def get_stats(self) -> Dict:
        """獲取緩存統計信息"""
        pass


class MemoryCacheBackend(CacheBackend):
    """內存緩存後端"""
    
    def __init__(self):
        self._cache: Dict[str, Tuple[Any, Optional[datetime]]] = {}
        self._lock = threading.RLock()
        self._stats = {
            'hits': 0,
            'misses': 0,
            'sets': 0,
            'deletes': 0
        }
        
    def get(self, key: str) -> Optional[Any]:
        """獲取緩存值"""
        with self._lock:
            if key in self._cache:
                value, expire_time = self._cache[key]
                
                # 檢查是否過期
                if expire_time is None or datetime.now() < expire_time:
                    self._stats['hits'] += 1
                    return value
                else:
                    # 過期則刪除
                    del self._cache[key]
                    
            self._stats['misses'] += 1
            return None
            
    def set(self, key: str, value: Any, ttl: Optional[int] = None):
        """設置緩存值"""
        with self._lock:
            expire_time = None
            if ttl is not None:
                expire_time = datetime.now() + timedelta(seconds=ttl)
                
            self._cache[key] = (value, expire_time)
            self._stats['sets'] += 1
            
    def delete(self, key: str) -> bool:
        """刪除緩存值"""
        with self._lock:
            if key in self._cache:
                del self._cache[key]
                self._stats['deletes'] += 1
                return True
            return False
            
    def exists(self, key: str) -> bool:
        """檢查緩存是否存在"""
        with self._lock:
            if key in self._cache:
                _, expire_time = self._cache[key]
                if expire_time is None or datetime.now() < expire_time:
                    return True
                else:
                    # 過期則刪除
                    del self._cache[key]
            return False
            
    def clear(self):
        """清空所有緩存"""
        with self._lock:
            self._cache.clear()
            
    def get_stats(self) -> Dict:
        """獲取緩存統計信息"""
        with self._lock:
            total_requests = self._stats['hits'] + self._stats['misses']
            hit_rate = self._stats['hits'] / total_requests if total_requests > 0 else 0
            
            return {
                **self._stats,
                'total_keys': len(self._cache),
                'hit_rate': hit_rate
            }
            
    def clean_expired(self):
        """清理過期的緩存項"""
        with self._lock:
            expired_keys = []
            now = datetime.now()
            
            for key, (_, expire_time) in self._cache.items():
                if expire_time is not None and now >= expire_time:
                    expired_keys.append(key)
                    
            for key in expired_keys:
                del self._cache[key]
                
            if expired_keys:
                logger.debug(f"清理了 {len(expired_keys)} 個過期緩存項")


class FileCacheBackend(CacheBackend):
    """文件緩存後端"""
    
    def __init__(self, cache_dir: str = ".cache"):
        self.cache_dir = Path(cache_dir)
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        self._lock = threading.RLock()
        self._stats = {
            'hits': 0,
            'misses': 0,
            'sets': 0,
            'deletes': 0
        }
        
    def _get_cache_path(self, key: str) -> Path:
        """獲取緩存文件路徑"""
        # 使用 MD5 避免文件名過長或包含特殊字符
        key_hash = hashlib.md5(key.encode()).hexdigest()
        return self.cache_dir / f"{key_hash}.cache"
        
    def get(self, key: str) -> Optional[Any]:
        """獲取緩存值"""
        with self._lock:
            cache_path = self._get_cache_path(key)
            
            if cache_path.exists():
                try:
                    with open(cache_path, 'rb') as f:
                        data = pickle.load(f)
                        
                    expire_time = data.get('expire_time')
                    if expire_time is None or datetime.now() < expire_time:
                        self._stats['hits'] += 1
                        return data['value']
                    else:
                        # 過期則刪除
                        cache_path.unlink()
                        
                except Exception as e:
                    logger.error(f"讀取緩存文件失敗 {key}: {e}")
                    
            self._stats['misses'] += 1
            return None
            
    def set(self, key: str, value: Any, ttl: Optional[int] = None):
        """設置緩存值"""
        with self._lock:
            cache_path = self._get_cache_path(key)
            
            expire_time = None
            if ttl is not None:
                expire_time = datetime.now() + timedelta(seconds=ttl)
                
            data = {
                'value': value,
                'expire_time': expire_time,
                'created_time': datetime.now()
            }
            
            try:
                with open(cache_path, 'wb') as f:
                    pickle.dump(data, f)
                self._stats['sets'] += 1
            except Exception as e:
                logger.error(f"寫入緩存文件失敗 {key}: {e}")
                
    def delete(self, key: str) -> bool:
        """刪除緩存值"""
        with self._lock:
            cache_path = self._get_cache_path(key)
            
            if cache_path.exists():
                try:
                    cache_path.unlink()
                    self._stats['deletes'] += 1
                    return True
                except Exception as e:
                    logger.error(f"刪除緩存文件失敗 {key}: {e}")
                    
            return False
            
    def exists(self, key: str) -> bool:
        """檢查緩存是否存在"""
        return self.get(key) is not None
        
    def clear(self):
        """清空所有緩存"""
        with self._lock:
            for cache_file in self.cache_dir.glob("*.cache"):
                try:
                    cache_file.unlink()
                except Exception as e:
                    logger.error(f"刪除緩存文件失敗: {e}")
                    
    def get_stats(self) -> Dict:
        """獲取緩存統計信息"""
        with self._lock:
            total_requests = self._stats['hits'] + self._stats['misses']
            hit_rate = self._stats['hits'] / total_requests if total_requests > 0 else 0
            
            # 統計緩存文件數量和大小
            cache_files = list(self.cache_dir.glob("*.cache"))
            total_size = sum(f.stat().st_size for f in cache_files)
            
            return {
                **self._stats,
                'total_keys': len(cache_files),
                'hit_rate': hit_rate,
                'total_size_mb': total_size / (1024 * 1024)
            }


class CacheManager:
    """統一緩存管理器"""
    
    def __init__(self, config: Optional[Config] = None, backend: Optional[CacheBackend] = None):
        """
        初始化緩存管理器
        
        Args:
            config: 配置對象
            backend: 緩存後端，如果為 None 則使用默認的內存後端
        """
        self.config = config or Config()
        self.backend = backend or self._create_backend()
        
        # 從配置獲取默認 TTL
        cache_config = self.config.get('cache', {})
        self.default_ttl = {
            CACHE_TYPE.PRICE: cache_config.get('price_hours', 1) * 3600,
            CACHE_TYPE.FUNDAMENTAL: cache_config.get('fundamental_hours', 6) * 3600,
            CACHE_TYPE.NEWS: cache_config.get('news_hours', 2) * 3600,
            CACHE_TYPE.INDUSTRY: cache_config.get('industry_hours', 12) * 3600,
            CACHE_TYPE.ANALYSIS: cache_config.get('analysis_minutes', 30) * 60
        }
        
        logger.info(f"緩存管理器初始化完成，使用後端: {type(self.backend).__name__}")
        
    def _create_backend(self) -> CacheBackend:
        """根據配置創建緩存後端"""
        cache_config = self.config.get('cache', {})
        backend_type = cache_config.get('backend', 'memory')
        
        if backend_type == 'memory':
            return MemoryCacheBackend()
        elif backend_type == 'file':
            cache_dir = cache_config.get('file_cache_dir', '.cache')
            return FileCacheBackend(cache_dir)
        else:
            logger.warning(f"未知的緩存後端類型: {backend_type}，使用內存緩存")
            return MemoryCacheBackend()
            
    def _make_key(self, cache_type: str, key: str) -> str:
        """生成緩存鍵"""
        return f"{cache_type}:{key}"
        
    def get(self, cache_type: str, key: str) -> Optional[Any]:
        """
        獲取緩存值
        
        Args:
            cache_type: 緩存類型
            key: 緩存鍵
            
        Returns:
            緩存的值，如果不存在返回 None
        """
        full_key = self._make_key(cache_type, key)
        value = self.backend.get(full_key)
        
        if value is not None:
            logger.debug(f"緩存命中: {full_key}")
        else:
            logger.debug(f"緩存未命中: {full_key}")
            
        return value
        
    def set(self, cache_type: str, key: str, value: Any, ttl: Optional[int] = None):
        """
        設置緩存值
        
        Args:
            cache_type: 緩存類型
            key: 緩存鍵
            value: 要緩存的值
            ttl: 過期時間（秒），如果為 None 則使用默認值
        """
        if ttl is None:
            ttl = self.default_ttl.get(cache_type, 3600)
            
        full_key = self._make_key(cache_type, key)
        self.backend.set(full_key, value, ttl)
        logger.debug(f"緩存設置: {full_key}, TTL: {ttl}秒")
        
    def delete(self, cache_type: str, key: str) -> bool:
        """
        刪除緩存值
        
        Args:
            cache_type: 緩存類型
            key: 緩存鍵
            
        Returns:
            是否刪除成功
        """
        full_key = self._make_key(cache_type, key)
        result = self.backend.delete(full_key)
        
        if result:
            logger.debug(f"緩存刪除: {full_key}")
            
        return result
        
    def exists(self, cache_type: str, key: str) -> bool:
        """
        檢查緩存是否存在
        
        Args:
            cache_type: 緩存類型
            key: 緩存鍵
            
        Returns:
            是否存在
        """
        full_key = self._make_key(cache_type, key)
        return self.backend.exists(full_key)
        
    def clear_type(self, cache_type: str):
        """
        清空指定類型的所有緩存
        
        Args:
            cache_type: 緩存類型
        """
        # 這裡簡化處理，實際使用時可能需要更精確的實現
        logger.warning(f"清空緩存類型: {cache_type}")
        # 注意：這會清空所有緩存，不只是指定類型
        self.backend.clear()
        
    def clear_all(self):
        """清空所有緩存"""
        self.backend.clear()
        logger.info("已清空所有緩存")
        
    def get_stats(self) -> Dict:
        """獲取緩存統計信息"""
        return self.backend.get_stats()
        
    def batch_get(self, cache_type: str, keys: List[str]) -> Dict[str, Any]:
        """
        批量獲取緩存值
        
        Args:
            cache_type: 緩存類型
            keys: 緩存鍵列表
            
        Returns:
            鍵值對字典
        """
        result = {}
        for key in keys:
            value = self.get(cache_type, key)
            if value is not None:
                result[key] = value
        return result
        
    def batch_set(self, cache_type: str, items: Dict[str, Any], ttl: Optional[int] = None):
        """
        批量設置緩存值
        
        Args:
            cache_type: 緩存類型
            items: 鍵值對字典
            ttl: 過期時間（秒）
        """
        for key, value in items.items():
            self.set(cache_type, key, value, ttl)
            
    def get_or_set(self, cache_type: str, key: str, factory_func, ttl: Optional[int] = None) -> Any:
        """
        獲取緩存值，如果不存在則使用工廠函數生成並緩存
        
        Args:
            cache_type: 緩存類型
            key: 緩存鍵
            factory_func: 生成值的函數
            ttl: 過期時間（秒）
            
        Returns:
            緩存的值或新生成的值
        """
        value = self.get(cache_type, key)
        
        if value is None:
            logger.debug(f"緩存未命中，調用工廠函數: {cache_type}:{key}")
            value = factory_func()
            if value is not None:
                self.set(cache_type, key, value, ttl)
                
        return value


# 全局緩存管理器實例
_cache_manager = None


def get_cache_manager() -> CacheManager:
    """獲取全局緩存管理器實例"""
    global _cache_manager
    if _cache_manager is None:
        _cache_manager = CacheManager()
    return _cache_manager