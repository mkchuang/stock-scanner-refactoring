"""
系統常量定義
集中管理所有系統級常量，提高可維護性
"""

from enum import Enum, IntEnum


# API 相關常量
class APIProvider(Enum):
    """API 提供商枚舉"""
    OPENAI = "openai"
    ANTHROPIC = "anthropic"
    ZHIPU = "zhipu"


# 分析類型
class AnalysisType(Enum):
    """分析類型枚舉"""
    TECHNICAL = "technical"
    FUNDAMENTAL = "fundamental"
    SENTIMENT = "sentiment"


# 任務狀態
class TaskStatus(Enum):
    """任務狀態枚舉"""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


# HTTP 狀態碼
class HTTPStatus(IntEnum):
    """HTTP 狀態碼"""
    OK = 200
    CREATED = 201
    ACCEPTED = 202
    NO_CONTENT = 204
    BAD_REQUEST = 400
    UNAUTHORIZED = 401
    FORBIDDEN = 403
    NOT_FOUND = 404
    INTERNAL_SERVER_ERROR = 500
    SERVICE_UNAVAILABLE = 503


# 技術指標相關常量
TECHNICAL_INDICATORS = {
    "MA": {
        "periods": [5, 10, 20, 60, 120, 250],
        "description": "移動平均線"
    },
    "RSI": {
        "period": 14,
        "overbought": 70,
        "oversold": 30,
        "description": "相對強弱指數"
    },
    "MACD": {
        "fast_period": 12,
        "slow_period": 26,
        "signal_period": 9,
        "description": "平滑異同移動平均線"
    },
    "BOLLINGER": {
        "period": 20,
        "std_dev": 2,
        "description": "布林帶"
    },
    "KDJ": {
        "k_period": 9,
        "d_period": 3,
        "j_period": 3,
        "description": "隨機指標"
    }
}


# 評分權重
DEFAULT_WEIGHTS = {
    "technical": 0.4,
    "fundamental": 0.4,
    "sentiment": 0.2
}


# 評分等級
class ScoreLevel(Enum):
    """評分等級"""
    STRONG_BUY = (80, 100, "強烈買入", "🟢🟢🟢")
    BUY = (60, 80, "買入", "🟢🟢")
    HOLD = (40, 60, "持有", "🟡")
    SELL = (20, 40, "賣出", "🔴")
    STRONG_SELL = (0, 20, "強烈賣出", "🔴🔴")
    
    def __init__(self, min_score: float, max_score: float, description: str, emoji: str):
        self.min_score = min_score
        self.max_score = max_score
        self.description = description
        self.emoji = emoji
    
    @classmethod
    def from_score(cls, score: float) -> 'ScoreLevel':
        """根據評分獲取等級"""
        for level in cls:
            if level.min_score <= score < level.max_score:
                return level
        return cls.HOLD


# 緩存相關常量
CACHE_DURATION = {
    "price": 3600,        # 1 小時
    "fundamental": 21600, # 6 小時
    "news": 7200,         # 2 小時
    "analysis": 1800      # 30 分鐘
}


# 緩存類型
class CACHE_TYPE:
    """緩存類型常量"""
    PRICE = "price"
    FUNDAMENTAL = "fundamental"
    NEWS = "news"
    INDUSTRY = "industry"
    ANALYSIS = "analysis"


# API 限制
API_LIMITS = {
    "max_concurrent_requests": 10,
    "max_retries": 3,
    "retry_delay": 1.0,
    "timeout": 30
}


# 財務指標
FINANCIAL_INDICATORS = [
    "總市值", "流通市值", "總股本", "流通股本",
    "市盈率(TTM)", "市盈率(靜)", "市盈率(動)", "市淨率",
    "市銷率", "市現率", "股息率", "總營收",
    "淨利潤", "淨資產", "總資產", "總負債",
    "資產負債率", "流動比率", "速動比率", "毛利率",
    "淨利率", "ROE", "ROA", "每股收益",
    "每股淨資產"
]


# 市場情緒關鍵詞
SENTIMENT_KEYWORDS = {
    "positive": [
        "突破", "創新高", "利好", "增長", "上漲", "買入", "增持",
        "業績超預期", "訂單增加", "擴張", "合作", "簽約", "中標"
    ],
    "negative": [
        "下跌", "虧損", "減持", "利空", "下調", "風險", "調查",
        "處罰", "訴訟", "裁員", "關閉", "取消", "延期"
    ],
    "neutral": [
        "公告", "披露", "變動", "調整", "會議", "報告", "統計"
    ]
}


# 日期格式
DATE_FORMATS = {
    "default": "%Y-%m-%d",
    "datetime": "%Y-%m-%d %H:%M:%S",
    "time": "%H:%M:%S",
    "chinese": "%Y年%m月%d日"
}


# 錯誤碼
class ErrorCode(IntEnum):
    """系統錯誤碼"""
    SUCCESS = 0
    INVALID_PARAM = 1001
    STOCK_NOT_FOUND = 1002
    API_ERROR = 2001
    API_KEY_MISSING = 2002
    API_LIMIT_EXCEEDED = 2003
    DATA_FETCH_ERROR = 3001
    ANALYSIS_ERROR = 4001
    AUTH_FAILED = 5001
    SESSION_EXPIRED = 5002
    INTERNAL_ERROR = 9999


# SSE 事件類型
class SSEEventType(Enum):
    """Server-Sent Events 事件類型"""
    PROGRESS = "progress"
    CONTENT = "content"
    ERROR = "error"
    COMPLETE = "complete"
    HEARTBEAT = "heartbeat"


# 並發設置
CONCURRENCY_SETTINGS = {
    "max_workers": 4,
    "queue_size": 100,
    "task_timeout": 300  # 5 分鐘
}


# 股票市場代碼前綴
MARKET_PREFIX = {
    "SH": "滬市",  # 上海證券交易所
    "SZ": "深市",  # 深圳證券交易所
    "BJ": "北交所", # 北京證券交易所
    "HK": "港股",  # 香港交易所
}


# 交易時間（北京時間）
TRADING_HOURS = {
    "morning_open": "09:30",
    "morning_close": "11:30",
    "afternoon_open": "13:00",
    "afternoon_close": "15:00"
}