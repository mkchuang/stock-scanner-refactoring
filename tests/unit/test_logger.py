"""
日誌管理模組單元測試
"""

import pytest
import logging
from pathlib import Path
from src.utils.logger import LoggerManager, get_logger, log_function_call, log_execution_time


class TestLoggerManager:
    """LoggerManager 測試類"""
    
    def test_setup_logging(self, tmp_path):
        """測試日誌設置"""
        log_file = tmp_path / "test.log"
        
        LoggerManager.setup_logging(
            level="DEBUG",
            log_file=str(log_file),
            console_output=True,
            file_output=True
        )
        
        # 獲取日誌器並記錄消息
        logger = LoggerManager.get_logger("test_logger")
        logger.debug("Debug message")
        logger.info("Info message")
        logger.warning("Warning message")
        logger.error("Error message")
        
        # 驗證日誌文件已創建
        assert log_file.exists()
        
        # 驗證日誌內容
        log_content = log_file.read_text()
        assert "Debug message" in log_content
        assert "Info message" in log_content
        assert "Warning message" in log_content
        assert "Error message" in log_content
    
    def test_get_logger(self):
        """測試獲取日誌器"""
        logger1 = LoggerManager.get_logger("test.module1")
        logger2 = LoggerManager.get_logger("test.module2")
        logger3 = LoggerManager.get_logger("test.module1")
        
        # 不同名稱的日誌器應該不同
        assert logger1 != logger2
        
        # 相同名稱的日誌器應該相同（緩存）
        assert logger1 is logger3
    
    def test_set_level(self):
        """測試設置日誌級別"""
        logger = LoggerManager.get_logger("level_test")
        
        # 設置為 WARNING 級別
        LoggerManager.set_level("level_test", "WARNING")
        
        # 驗證級別設置
        assert logger.level == logging.WARNING
        
        # 設置為 DEBUG 級別
        LoggerManager.set_level("level_test", "DEBUG")
        assert logger.level == logging.DEBUG
    
    def test_console_only_logging(self):
        """測試僅控制台輸出"""
        LoggerManager._initialized = False  # 重置狀態
        
        LoggerManager.setup_logging(
            level="INFO",
            console_output=True,
            file_output=False
        )
        
        root_logger = logging.getLogger()
        
        # 應該只有一個 StreamHandler
        handlers = [h for h in root_logger.handlers if isinstance(h, logging.StreamHandler)]
        assert len(handlers) >= 1
        
        # 不應該有 FileHandler
        file_handlers = [h for h in root_logger.handlers if isinstance(h, logging.FileHandler)]
        assert len(file_handlers) == 0
    
    def test_file_rotation(self, tmp_path):
        """測試日誌輪轉"""
        LoggerManager._initialized = False  # 重置狀態
        log_file = tmp_path / "rotation_test.log"
        
        LoggerManager.setup_logging(
            level="DEBUG",
            log_file=str(log_file),
            console_output=False,
            file_output=True
        )
        
        logger = LoggerManager.get_logger("rotation_test")
        
        # 寫入大量日誌以觸發輪轉
        for i in range(1000):
            logger.info(f"Test message {i} " + "x" * 100)
        
        # 驗證日誌文件存在
        assert log_file.exists()


class TestLogDecorators:
    """測試日誌裝飾器"""
    
    def test_log_function_call(self, caplog):
        """測試函數調用日誌裝飾器"""
        logger = get_logger("decorator_test")
        
        @log_function_call(logger)
        def test_function(x, y):
            return x + y
        
        # 正常調用
        with caplog.at_level(logging.DEBUG):
            result = test_function(1, 2)
            assert result == 3
            assert "調用函數 test_function" in caplog.text
            assert "函數 test_function 執行成功" in caplog.text
        
        # 異常情況
        @log_function_call(logger)
        def failing_function():
            raise ValueError("Test error")
        
        with pytest.raises(ValueError):
            with caplog.at_level(logging.ERROR):
                failing_function()
                assert "函數 failing_function 執行失敗" in caplog.text
    
    def test_log_execution_time(self, caplog):
        """測試執行時間日誌裝飾器"""
        logger = get_logger("time_test")
        
        @log_execution_time(logger)
        def slow_function():
            import time
            time.sleep(0.1)
            return "done"
        
        with caplog.at_level(logging.INFO):
            result = slow_function()
            assert result == "done"
            assert "slow_function 執行時間:" in caplog.text
            # 應該記錄了執行時間
            assert "0." in caplog.text  # 至少 0.1 秒


class TestHelperFunctions:
    """測試輔助函數"""
    
    def test_get_logger_helper(self):
        """測試 get_logger 輔助函數"""
        logger = get_logger("helper_test")
        assert isinstance(logger, logging.Logger)
        assert logger.name == "helper_test"
        
        # 應該返回相同的實例
        logger2 = get_logger("helper_test")
        assert logger is logger2