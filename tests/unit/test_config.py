"""
配置管理模組單元測試
"""

import pytest
import json
from pathlib import Path
from src.core.config import ConfigManager


class TestConfigManager:
    """ConfigManager 測試類"""
    
    def test_singleton_pattern(self):
        """測試單例模式"""
        config1 = ConfigManager()
        config2 = ConfigManager()
        assert config1 is config2
    
    def test_load_config_file(self, test_config_file):
        """測試加載配置文件"""
        config = ConfigManager(test_config_file)
        
        # 驗證配置已加載
        assert config.get('api_keys.openai') == 'test-key'
        assert config.get('ai.max_tokens') == 1000
        assert config.get('cache.price_hours') == 1
    
    def test_load_default_config(self):
        """測試加載默認配置"""
        config = ConfigManager('non_existent_file.json')
        
        # 應該加載默認配置
        assert config.get('ai.model_preference') == 'openai'
        assert config.get('analysis_weights.technical') == 0.4
    
    def test_get_nested_config(self):
        """測試獲取嵌套配置值"""
        config = ConfigManager()
        
        # 測試多層嵌套
        config.set('test.nested.value', 123)
        assert config.get('test.nested.value') == 123
        
        # 測試默認值
        assert config.get('non.existent.key', 'default') == 'default'
    
    def test_set_config(self):
        """測試設置配置值"""
        config = ConfigManager()
        
        # 設置簡單值
        config.set('simple_key', 'simple_value')
        assert config.get('simple_key') == 'simple_value'
        
        # 設置嵌套值
        config.set('nested.key.value', {'data': 123})
        assert config.get('nested.key.value.data') == 123
    
    def test_save_config(self, tmp_path):
        """測試保存配置"""
        config_file = tmp_path / "save_test.json"
        config = ConfigManager(str(config_file))
        
        # 修改配置
        config.set('test_key', 'test_value')
        config.set('nested.test', 123)
        
        # 保存配置
        assert config.save() is True
        
        # 驗證文件已保存
        assert config_file.exists()
        
        # 驗證內容正確
        with open(config_file, 'r') as f:
            saved_data = json.load(f)
            assert saved_data['test_key'] == 'test_value'
            assert saved_data['nested']['test'] == 123
    
    def test_reload_config(self, tmp_path):
        """測試重新加載配置"""
        config_file = tmp_path / "reload_test.json"
        
        # 創建初始配置
        initial_config = {'key': 'initial_value'}
        with open(config_file, 'w') as f:
            json.dump(initial_config, f)
        
        config = ConfigManager(str(config_file))
        assert config.get('key') == 'initial_value'
        
        # 外部修改配置文件
        updated_config = {'key': 'updated_value'}
        with open(config_file, 'w') as f:
            json.dump(updated_config, f)
        
        # 重新加載
        config.reload()
        assert config.get('key') == 'updated_value'
    
    def test_property_accessors(self, test_config_file):
        """測試屬性訪問器"""
        config = ConfigManager(test_config_file)
        
        # 測試各種屬性
        assert config.api_keys['openai'] == 'test-key'
        assert config.ai_config['model_preference'] == 'openai'
        assert config.cache_config['price_hours'] == 1
        
        # 測試默認值
        assert isinstance(config.analysis_weights, dict)
        assert isinstance(config.streaming_config, dict)


class TestConfigValidation:
    """配置驗證測試"""
    
    def test_invalid_json_handling(self, tmp_path):
        """測試處理無效 JSON"""
        config_file = tmp_path / "invalid.json"
        with open(config_file, 'w') as f:
            f.write("invalid json content")
        
        # 應該加載默認配置而不是崩潰
        config = ConfigManager(str(config_file))
        assert config.get('ai.model_preference') == 'openai'
    
    def test_partial_config(self, tmp_path):
        """測試部分配置"""
        config_file = tmp_path / "partial.json"
        partial_config = {
            "api_keys": {
                "openai": "my-key"
            }
            # 缺少其他配置項
        }
        
        with open(config_file, 'w') as f:
            json.dump(partial_config, f)
        
        config = ConfigManager(str(config_file))
        
        # 應該能獲取存在的配置
        assert config.get('api_keys.openai') == 'my-key'
        
        # 缺失的配置應返回默認值或 None
        assert config.get('ai.model_preference') is None