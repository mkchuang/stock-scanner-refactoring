#!/usr/bin/env python3
"""
股票分析系統主程序入口
"""

import sys
import os
from pathlib import Path

# 添加 src 到 Python 路徑
sys.path.insert(0, str(Path(__file__).parent / "src"))

from src.core.config import config_manager
from src.utils.logger import LoggerManager, get_logger


def setup_application():
    """初始化應用程序"""
    # 設置日誌
    log_config = config_manager.get('logging', {})
    LoggerManager.setup_logging(
        level=log_config.get('level', 'INFO'),
        log_file=log_config.get('file', 'logs/stock_analyzer.log'),
        console_output=True,
        file_output=True
    )
    
    logger = get_logger(__name__)
    logger.info("🚀 股票分析系統啟動中...")
    
    # 顯示配置狀態
    logger.info(f"配置文件: {config_manager.config_file}")
    logger.info(f"AI 模型偏好: {config_manager.ai_config.get('model_preference')}")
    logger.info(f"日誌級別: {log_config.get('level', 'INFO')}")
    
    return logger


def main():
    """主函數"""
    logger = setup_application()
    
    try:
        # TODO: 這裡將整合重構後的 Flask 應用
        logger.info("✅ 系統初始化完成")
        logger.info("⚠️  Web 服務器模組正在重構中...")
        
        # 臨時代碼：顯示重構進度
        from src.core.constants import ErrorCode, ScoreLevel
        logger.info(f"已加載常量模組，錯誤碼示例: {ErrorCode.SUCCESS.name}")
        logger.info(f"評分等級示例: {ScoreLevel.BUY.description}")
        
    except Exception as e:
        logger.error(f"❌ 系統啟動失敗: {e}", exc_info=True)
        sys.exit(1)


if __name__ == "__main__":
    main()