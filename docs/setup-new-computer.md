# 新電腦開發環境設置指南

## 🚀 快速開始

### 1. 克隆專案
```bash
git clone https://github.com/mkchuang/stock-scanner-refactoring.git
cd stock-scanner-refactoring
```

### 2. 設置 Python 環境
```bash
# 確認 Python 版本（需要 3.12+）
python3 --version

# 創建虛擬環境
python3 -m venv venv

# 激活虛擬環境（可選）
source venv/bin/activate  # Linux/Mac
# 或
venv\Scripts\activate  # Windows
```

### 3. 安裝依賴
```bash
# 安裝所有依賴
venv/bin/pip install -r requirements.txt

# 安裝測試框架
venv/bin/pip install pytest pytest-cov pytest-mock
```

### 4. 驗證環境
```bash
# 執行測試
venv/bin/python -m pytest

# 查看測試覆蓋率
venv/bin/python -m pytest --cov=src --cov-report=term-missing
```

## 📊 當前專案狀態

### 重構進度
- ✅ 第一階段：基礎架構（完成）
- ✅ 第二階段：數據層（完成）
- ⏳ 第三階段：分析層（進行中）
- ⏳ 第四階段：AI 層（待開始）
- ⏳ 第五階段：Web 層（待開始）

### 測試覆蓋率
- 整體：41%
- 核心模組：90%+
- 數據層：測試中
- 分析層：0%（待實現）

## 🔧 開發環境檢查

### 必要工具
- Python 3.12+
- Git
- pip
- 文本編輯器（VSCode/PyCharm 推薦）

### 可選工具
- Docker（用於部署測試）
- Postman（用於 API 測試）

## 📚 重要文件位置

### 記憶文件
- `.claude/memory.md` - 專案總覽
- `.claude/workspace.md` - 當前工作狀態
- `.claude/project.md` - 專案架構
- `.claude/CLAUDE.md` - 開發規範

### 文檔
- `docs/testing-guide.md` - 測試指南
- `docs/setup-new-computer.md` - 本文件

### 配置
- `requirements.txt` - Python 依賴
- `pytest.ini` - 測試配置
- `.gitignore` - Git 忽略規則

## 🎯 下一步開發任務

1. **修復數據層測試**
   - 更新 akshare API 調用
   - 修復失敗的測試案例

2. **實現分析層模組**
   - 技術分析（technical.py）
   - 基本面分析（fundamental.py）
   - 情緒分析（sentiment.py）

3. **編寫分析層測試**
   - 目標覆蓋率 > 80%
   - 使用 TDD 開發模式

## 💡 開發提示

### Git 分支策略
```bash
# 目前在 master 分支
git checkout -b feature/analysis-layer  # 創建功能分支
```

### 常用命令
```bash
# 載入記憶
/load-memory

# 進入執行模式
/act-mode

# 更新記憶總覽
/update-memory
```

### 測試驅動開發
1. 先寫測試
2. 運行測試（應該失敗）
3. 實現功能
4. 運行測試（應該通過）
5. 重構代碼

## 🔗 相關資源

- GitHub 倉庫：https://github.com/mkchuang/stock-scanner-refactoring
- 原始需求：AI 智能股票分析系統
- 技術棧：Flask + AKShare + AI APIs

---
*最後更新：2025-07-06*
*準備人：Claude Assistant*