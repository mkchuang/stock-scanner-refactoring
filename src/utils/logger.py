"""
日誌管理模組
提供統一的日誌配置和管理功能
"""

import logging
import logging.handlers
import os
from datetime import datetime
from pathlib import Path
from typing import Optional


class LoggerManager:
    """日誌管理器"""
    
    _loggers = {}
    _initialized = False
    
    @classmethod
    def setup_logging(cls, 
                     level: str = "INFO",
                     log_file: Optional[str] = None,
                     console_output: bool = True,
                     file_output: bool = True) -> None:
        """設置全局日誌配置"""
        if cls._initialized:
            return
            
        # 設置日誌級別
        log_level = getattr(logging, level.upper(), logging.INFO)
        
        # 設置日誌格式
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
        
        # 獲取根日誌器
        root_logger = logging.getLogger()
        root_logger.setLevel(log_level)
        
        # 清除現有的處理器
        root_logger.handlers.clear()
        
        # 控制台輸出
        if console_output:
            console_handler = logging.StreamHandler()
            console_handler.setFormatter(formatter)
            root_logger.addHandler(console_handler)
        
        # 文件輸出
        if file_output and log_file:
            # 確保日誌目錄存在
            log_path = Path(log_file)
            log_path.parent.mkdir(parents=True, exist_ok=True)
            
            # 使用 RotatingFileHandler 實現日誌輪轉
            file_handler = logging.handlers.RotatingFileHandler(
                log_file,
                maxBytes=10 * 1024 * 1024,  # 10MB
                backupCount=5,
                encoding='utf-8'
            )
            file_handler.setFormatter(formatter)
            root_logger.addHandler(file_handler)
        
        cls._initialized = True
    
    @classmethod
    def get_logger(cls, name: str) -> logging.Logger:
        """獲取日誌器實例"""
        if name not in cls._loggers:
            cls._loggers[name] = logging.getLogger(name)
        return cls._loggers[name]
    
    @classmethod
    def set_level(cls, name: str, level: str) -> None:
        """設置特定日誌器的級別"""
        logger = cls.get_logger(name)
        logger.setLevel(getattr(logging, level.upper(), logging.INFO))


class ColoredFormatter(logging.Formatter):
    """彩色日誌格式化器（用於控制台輸出）"""
    
    # ANSI 顏色碼
    COLORS = {
        'DEBUG': '\033[36m',    # 青色
        'INFO': '\033[32m',     # 綠色
        'WARNING': '\033[33m',  # 黃色
        'ERROR': '\033[31m',    # 紅色
        'CRITICAL': '\033[35m', # 紫色
    }
    RESET = '\033[0m'
    
    def format(self, record):
        # 獲取日誌級別對應的顏色
        levelname = record.levelname
        if levelname in self.COLORS:
            levelname_color = f"{self.COLORS[levelname]}{levelname}{self.RESET}"
            record.levelname = levelname_color
        
        # 調用父類的 format 方法
        return super().format(record)


def setup_colored_logging(level: str = "INFO") -> None:
    """設置彩色日誌輸出（僅用於開發環境）"""
    log_level = getattr(logging, level.upper(), logging.INFO)
    
    # 創建彩色格式化器
    colored_formatter = ColoredFormatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    
    # 設置控制台處理器
    console_handler = logging.StreamHandler()
    console_handler.setFormatter(colored_formatter)
    
    # 配置根日誌器
    root_logger = logging.getLogger()
    root_logger.setLevel(log_level)
    root_logger.handlers.clear()
    root_logger.addHandler(console_handler)


def get_logger(name: str) -> logging.Logger:
    """快捷方法：獲取日誌器"""
    return LoggerManager.get_logger(name)


# 日誌級別常量
LOG_LEVELS = {
    'DEBUG': logging.DEBUG,
    'INFO': logging.INFO,
    'WARNING': logging.WARNING,
    'ERROR': logging.ERROR,
    'CRITICAL': logging.CRITICAL
}


# 實用函數
def log_function_call(logger: logging.Logger):
    """裝飾器：記錄函數調用"""
    def decorator(func):
        def wrapper(*args, **kwargs):
            func_name = func.__name__
            logger.debug(f"調用函數 {func_name}")
            try:
                result = func(*args, **kwargs)
                logger.debug(f"函數 {func_name} 執行成功")
                return result
            except Exception as e:
                logger.error(f"函數 {func_name} 執行失敗: {e}")
                raise
        return wrapper
    return decorator


def log_execution_time(logger: logging.Logger):
    """裝飾器：記錄函數執行時間"""
    import time
    def decorator(func):
        def wrapper(*args, **kwargs):
            start_time = time.time()
            result = func(*args, **kwargs)
            elapsed_time = time.time() - start_time
            logger.info(f"{func.__name__} 執行時間: {elapsed_time:.2f} 秒")
            return result
        return wrapper
    return decorator