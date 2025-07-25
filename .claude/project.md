# 專案全貌 - Project Overview

## 🎯 專案簡介 (Project Brief)

### 專案目標
構建一個基於 AI 技術的智能股票分析平台，整合多維度數據源和多個 AI 模型，為投資者提供專業、即時、全面的股票分析報告。

### 核心功能
- **技術分析引擎**：整合 K線、MA、RSI、MACD、布林帶等多種技術指標，提供量化交易信號
- **基本面評估系統**：分析 25 項關鍵財務指標，支援行業對比和歷史趨勢分析
- **AI 智能報告**：整合 OpenAI GPT-4、Anthropic Claude、智譜 AI，生成專業投資建議
- **情緒分析模組**：即時分析市場新聞和輿情，評估市場情緒對股價的影響
- **串流即時更新**：採用 SSE 技術實現分析過程的即時推送，提升用戶體驗

### 目標用戶
- **個人投資者**：需要專業分析工具輔助投資決策的散戶
- **投資顧問**：為客戶提供投資建議的專業人士
- **量化交易者**：需要技術指標和 API 接口的程式化交易者
- **金融研究員**：進行市場研究和股票分析的專業人員

## 🏗️ 系統架構 (System Patterns)

### 整體架構
```
┌─────────────┐     ┌──────────────────┐     ┌─────────────────┐
│   前端界面   │────▶│  Flask Web Server │────▶│ WebStockAnalyzer │
│  (HTML/JS)  │◀────│   (SSE 推送)      │◀────│   (分析引擎)     │
└─────────────┘     └──────────────────┘     └────────┬────────┘
                            │                          │
                    ┌───────┴────────┐         ┌──────┴───────┐
                    │ Authentication │         │  Data Source │
                    │   (Session)    │         │  (AKShare)   │
                    └────────────────┘         └──────┬───────┘
                                                      │
                            ┌─────────────────────────┴─────────────┐
                            │            AI APIs                     │
                            ├──────────┬──────────┬────────────────┤
                            │ OpenAI   │ Claude   │   Zhipu AI     │
                            └──────────┴──────────┴────────────────┘
```

### 核心模組
- **WebStockAnalyzer**：核心分析引擎，整合技術分析、基本面分析、情緒分析
- **Flask Web Server**：提供 RESTful API 和 SSE 即時推送，處理並發請求
- **SSEManager**：管理 Server-Sent Events 連接池，實現即時數據推送
- **緩存管理器**：三層緩存（價格/基本面/新聞），提升響應速度
- **AI 整合層**：統一介面調用多個 AI 模型，支援串流輸出

### 設計模式
- **工廠模式**：AI 模型選擇器根據配置動態創建對應的 AI 客戶端
- **單例模式**：分析器實例全局唯一，避免重複初始化
- **觀察者模式**：SSE 實現事件推送，客戶端訂閱分析進度
- **策略模式**：不同維度的分析策略可獨立替換和擴展

### 執行緒模式
- **ThreadPoolExecutor**：最大 4 個工作線程處理並發分析請求
- **線程安全**：使用 threading.Lock 保護共享資源（任務狀態、SSE 客戶端）
- **非阻塞設計**：SSE 使用 Queue 實現非阻塞消息傳遞

### 通訊機制
- **RESTful API**：標準 HTTP 請求/響應模式
- **Server-Sent Events**：單向即時推送，適合分析進度更新
- **JSON 數據交換**：統一的數據序列化格式
- **異步回調**：AI 串流輸出通過回調函數即時處理

## 🔧 技術上下文 (Tech Context)

### 技術棧
- **後端語言**：Python 3.11
- **Web 框架**：Flask 2.x + Flask-CORS
- **數據來源**：AKShare（A股市場數據）
- **AI 服務**：OpenAI API、Anthropic API、Zhipu AI API
- **即時通訊**：Server-Sent Events (SSE)
- **數據處理**：Pandas、NumPy

### 開發環境
- **作業系統**：跨平台（Linux/Windows/macOS）
- **Python 版本**：3.9+（建議 3.11）
- **IDE/編輯器**：VS Code、PyCharm
- **版本控制**：Git

### 建置環境
- **依賴管理**：pip + requirements.txt
- **容器化**：Docker + Docker Compose
- **WSGI 服務器**：Gunicorn（生產環境）
- **反向代理**：Nginx（可選）

### 運行環境
- **目標平台**：x86_64 Linux/Windows
- **記憶體需求**：建議 2GB+（Docker 配置限制）
- **CPU 需求**：建議 2 核心+
- **網路需求**：需要訪問外部 API 服務

### 技術限制
- **API 速率限制**：依賴第三方 AI 服務的配額
- **數據源限制**：AKShare 免費接口有請求頻率限制
- **並發限制**：ThreadPoolExecutor 最大 4 線程
- **緩存策略**：內存緩存，重啟後失效

### 相依關係
- **核心依賴**：
  - Flask==2.x（Web 框架）
  - pandas>=1.3（數據分析）
  - akshare>=1.8（股票數據）
  - openai>=1.0（AI 接口）
- **開發依賴**：
  - python-dotenv（環境變量）
  - pytest（單元測試）
- **版本要求**：
  - Python >= 3.9
  - Docker >= 20.10
  - Docker Compose >= 1.29

---
*建立時間: 2025-01-27*
*最後更新: 2025-01-27*
