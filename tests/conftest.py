"""
pytest 配置文件
提供測試固件和配置
"""

import pytest
import sys
import os
from pathlib import Path

# 將 src 目錄加入 Python 路徑
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))
sys.path.insert(0, str(project_root / "src"))


@pytest.fixture
def test_config_file(tmp_path):
    """創建測試用配置文件"""
    config_content = {
        "api_keys": {
            "openai": "test-key",
            "anthropic": "test-key",
            "zhipu": "test-key"
        },
        "ai": {
            "model_preference": "openai",
            "max_tokens": 1000,
            "temperature": 0.5
        },
        "cache": {
            "price_hours": 1,
            "fundamental_hours": 6,
            "news_hours": 2
        }
    }
    
    import json
    config_file = tmp_path / "test_config.json"
    with open(config_file, 'w') as f:
        json.dump(config_content, f)
    
    return str(config_file)


@pytest.fixture
def mock_logger(mocker):
    """模擬日誌器"""
    return mocker.MagicMock()


@pytest.fixture
def sample_stock_data():
    """提供樣本股票數據"""
    return {
        "code": "000001",
        "name": "平安銀行",
        "price": 12.34,
        "change": 0.56,
        "change_pct": 4.75,
        "volume": 1234567,
        "amount": 15234567.89
    }


@pytest.fixture
def sample_technical_data():
    """提供樣本技術分析數據"""
    return {
        "ma5": 12.20,
        "ma10": 12.15,
        "ma20": 12.05,
        "rsi": 65.5,
        "macd": {
            "dif": 0.15,
            "dea": 0.12,
            "macd": 0.06
        },
        "kdj": {
            "k": 75.5,
            "d": 70.2,
            "j": 86.1
        }
    }


@pytest.fixture(autouse=True)
def reset_singletons():
    """重置單例實例（用於測試隔離）"""
    # 在每個測試前後重置單例
    from src.core.config import ConfigManager
    ConfigManager._instance = None
    ConfigManager._config = {}
    yield
    ConfigManager._instance = None
    ConfigManager._config = {}