# 測試指南 - Testing Guide

## 🔧 測試環境設置

### 1. 虛擬環境要求
本專案使用 Python 虛擬環境來管理依賴，確保測試環境的一致性。

```bash
# 檢查虛擬環境
ls -la venv/

# 激活虛擬環境（非必須，可直接使用 venv/bin/python）
source venv/bin/activate

# 使用虛擬環境的 Python
venv/bin/python --version  # Python 3.12.3
```

### 2. 必要依賴安裝
```bash
# 安裝測試框架
venv/bin/pip install pytest pytest-cov pytest-mock

# 安裝專案依賴
venv/bin/pip install -r requirements.txt

# 關鍵依賴清單
# - pytest 8.4.1：測試框架
# - pytest-cov 6.2.1：覆蓋率工具
# - pytest-mock 3.14.1：Mock 工具
# - pandas：數據處理
# - numpy：數值計算
# - akshare：股票數據
```

## 📊 測試執行指令

### 基本測試指令
```bash
# 執行所有測試
venv/bin/python -m pytest

# 執行特定目錄的測試
venv/bin/python -m pytest tests/unit/

# 執行特定文件的測試
venv/bin/python -m pytest tests/unit/test_cache.py

# 顯示詳細輸出
venv/bin/python -m pytest -v

# 顯示測試中的 print 輸出
venv/bin/python -m pytest -s
```

### 覆蓋率測試指令
```bash
# 執行測試並生成覆蓋率報告（終端顯示）
venv/bin/python -m pytest --cov=src --cov-report=term

# 顯示未覆蓋的程式碼行號
venv/bin/python -m pytest --cov=src --cov-report=term-missing

# 生成 HTML 覆蓋率報告
venv/bin/python -m pytest --cov=src --cov-report=html

# 指定 HTML 報告輸出目錄
venv/bin/python -m pytest --cov=src --cov-report=html:htmlcov_summary

# 同時生成終端和 HTML 報告
venv/bin/python -m pytest --cov=src --cov-report=term --cov-report=html

# 只顯示覆蓋率摘要（快速模式）
venv/bin/python -m pytest --cov=src --cov-report=term --no-cov-on-fail -q
```

### 部分測試執行（避免超時）
```bash
# 執行核心模組測試（快速）
venv/bin/python -m pytest tests/unit/test_cache.py tests/unit/test_config.py tests/unit/test_logger.py --cov=src --cov-report=term-missing

# 執行數據層測試
venv/bin/python -m pytest tests/unit/test_stock_fetcher.py tests/unit/test_news_fetcher.py --cov=src/data --cov-report=term-missing

# 執行分析層測試（當實現後）
venv/bin/python -m pytest tests/unit/test_technical.py tests/unit/test_fundamental.py tests/unit/test_sentiment.py --cov=src/analysis --cov-report=term-missing
```

### 除錯和問題排查
```bash
# 只收集測試，不執行（檢查測試發現問題）
venv/bin/python -m pytest --collect-only

# 執行失敗時立即停止
venv/bin/python -m pytest -x

# 顯示最慢的 N 個測試
venv/bin/python -m pytest --durations=10

# 執行上次失敗的測試
venv/bin/python -m pytest --lf

# 設定超時時間（防止測試卡住）
venv/bin/python -m pytest --timeout=300
```

## 📈 覆蓋率目標

### 當前覆蓋率狀態（2025-07-06）
```
整體覆蓋率：41%
- 核心模組：90%+ ✅
- 數據層：測試中
- 分析層：0%（待實現）
- AI 層：0%（待實現）
- Web 層：0%（待實現）
```

### 覆蓋率標準
- **優秀**：> 90%（核心模組要求）
- **良好**：> 80%（業務邏輯要求）
- **及格**：> 70%（一般模組要求）
- **警告**：< 70%（需要改進）

## 🛠️ 常見問題解決

### 1. 模組導入錯誤
```bash
# 確保在專案根目錄執行
cd /mnt/c/Users/V000149/Project/stock-scanner

# 檢查 PYTHONPATH
echo $PYTHONPATH

# 使用正確的 pytest 配置（pytest.ini 已配置）
cat pytest.ini
```

### 2. 依賴缺失錯誤
```bash
# 檢查已安裝的包
venv/bin/pip list

# 重新安裝依賴
venv/bin/pip install -r requirements.txt

# 安裝特定缺失的包
venv/bin/pip install pandas numpy akshare
```

### 3. 測試超時問題
```bash
# 分批執行測試
venv/bin/python -m pytest tests/unit/test_cache.py
venv/bin/python -m pytest tests/unit/test_config.py
venv/bin/python -m pytest tests/unit/test_logger.py

# 跳過慢速測試
venv/bin/python -m pytest -m "not slow"
```

## 📝 測試編寫規範

### 測試文件命名
- 單元測試：`test_<module_name>.py`
- 集成測試：`test_integration_<feature>.py`
- 測試類：`Test<ClassName>`
- 測試方法：`test_<method_name>_<scenario>`

### 測試結構範例
```python
import pytest
from unittest.mock import Mock, patch

class TestModuleName:
    """模組測試類"""
    
    def setup_method(self):
        """每個測試方法前執行"""
        pass
    
    def teardown_method(self):
        """每個測試方法後執行"""
        pass
    
    def test_normal_case(self):
        """測試正常情況"""
        pass
    
    def test_edge_case(self):
        """測試邊界情況"""
        pass
    
    def test_error_handling(self):
        """測試錯誤處理"""
        pass
```

## 🔄 持續整合建議

### GitHub Actions 配置（未來實現）
```yaml
name: Tests
on: [push, pull_request]
jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v2
      - uses: actions/setup-python@v2
        with:
          python-version: '3.12'
      - run: |
          python -m venv venv
          venv/bin/pip install -r requirements.txt
          venv/bin/python -m pytest --cov=src
```

## 📊 測試報告查看

### 終端報告
直接在命令執行後查看

### HTML 報告
```bash
# 生成報告後
ls -la htmlcov/

# 在 WSL 中打開報告（使用 Windows 瀏覽器）
explorer.exe htmlcov/index.html

# 或複製路徑在 Windows 瀏覽器中打開
# file:///mnt/c/Users/V000149/Project/stock-scanner/htmlcov/index.html
```

---
*最後更新：2025-07-06*
*記錄人：Claude Assistant*