"""
配置管理模組
負責加載、驗證和管理系統配置
"""

import json
import os
from typing import Dict, Any, Optional
from pathlib import Path
import logging

logger = logging.getLogger(__name__)


class ConfigManager:
    """配置管理器"""
    
    _instance: Optional['ConfigManager'] = None
    _config: Dict[str, Any] = {}
    
    def __new__(cls, config_file: str = 'config.json'):
        """單例模式實現"""
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialized = False
        return cls._instance
    
    def __init__(self, config_file: str = 'config.json'):
        """初始化配置管理器"""
        if self._initialized:
            return
            
        self.config_file = config_file
        self._config = self._load_config()
        self._initialized = True
        
    def _load_config(self) -> Dict[str, Any]:
        """加載配置文件"""
        try:
            config_path = Path(self.config_file)
            if config_path.exists():
                with open(config_path, 'r', encoding='utf-8') as f:
                    config = json.load(f)
                logger.info(f"✅ 成功加載配置文件: {self.config_file}")
                return config
            else:
                logger.warning(f"⚠️ 配置文件 {self.config_file} 不存在，使用默認配置")
                return self._get_default_config()
        except Exception as e:
            logger.error(f"❌ 加載配置文件失敗: {e}")
            return self._get_default_config()
    
    def _get_default_config(self) -> Dict[str, Any]:
        """獲取默認配置"""
        return {
            "api_keys": {
                "openai": "",
                "anthropic": "",
                "zhipu": ""
            },
            "ai": {
                "model_preference": "openai",
                "models": {
                    "openai": "gpt-4-turbo-preview",
                    "anthropic": "claude-3-haiku-20240307",
                    "zhipu": "chatglm_turbo"
                },
                "max_tokens": 4000,
                "temperature": 0.7,
                "api_base_urls": {
                    "openai": "https://api.openai.com/v1"
                }
            },
            "analysis_weights": {
                "technical": 0.4,
                "fundamental": 0.4,
                "sentiment": 0.2
            },
            "cache": {
                "price_hours": 1,
                "fundamental_hours": 6,
                "news_hours": 2
            },
            "streaming": {
                "enabled": True,
                "show_thinking": False,
                "delay": 0.05
            },
            "analysis_params": {
                "max_news_count": 100,
                "technical_period_days": 365,
                "financial_indicators_count": 25
            },
            "web_auth": {
                "enabled": True,
                "password": "your_password_here",
                "session_timeout": 3600
            },
            "logging": {
                "level": "INFO",
                "file": "stock_analyzer.log"
            }
        }
    
    def get(self, key: str, default: Any = None) -> Any:
        """獲取配置值"""
        keys = key.split('.')
        value = self._config
        
        for k in keys:
            if isinstance(value, dict) and k in value:
                value = value[k]
            else:
                return default
                
        return value
    
    def set(self, key: str, value: Any) -> None:
        """設置配置值"""
        keys = key.split('.')
        config = self._config
        
        for k in keys[:-1]:
            if k not in config:
                config[k] = {}
            config = config[k]
            
        config[keys[-1]] = value
    
    def save(self) -> bool:
        """保存配置到文件"""
        try:
            with open(self.config_file, 'w', encoding='utf-8') as f:
                json.dump(self._config, f, indent=4, ensure_ascii=False)
            logger.info(f"✅ 配置已保存到 {self.config_file}")
            return True
        except Exception as e:
            logger.error(f"❌ 保存配置失敗: {e}")
            return False
    
    def reload(self) -> None:
        """重新加載配置"""
        self._config = self._load_config()
    
    @property
    def api_keys(self) -> Dict[str, str]:
        """獲取 API 密鑰配置"""
        return self.get('api_keys', {})
    
    @property
    def ai_config(self) -> Dict[str, Any]:
        """獲取 AI 配置"""
        return self.get('ai', {})
    
    @property
    def cache_config(self) -> Dict[str, Any]:
        """獲取緩存配置"""
        return self.get('cache', {})
    
    @property
    def analysis_weights(self) -> Dict[str, float]:
        """獲取分析權重配置"""
        return self.get('analysis_weights', {})
    
    @property
    def analysis_params(self) -> Dict[str, Any]:
        """獲取分析參數配置"""
        return self.get('analysis_params', {})
    
    @property
    def streaming_config(self) -> Dict[str, Any]:
        """獲取串流配置"""
        return self.get('streaming', {})
    
    @property
    def web_auth_config(self) -> Dict[str, Any]:
        """獲取 Web 認證配置"""
        return self.get('web_auth', {})


# 全局配置實例
config_manager = ConfigManager()