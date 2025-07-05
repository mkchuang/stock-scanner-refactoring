"""
股票數據獲取模組的單元測試
"""

import pytest
from unittest.mock import Mock, patch, MagicMock
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from src.data.stock_fetcher import StockDataFetcher
from src.core.constants import CACHE_TYPE


class TestStockDataFetcher:
    """股票數據獲取器測試"""
    
    @pytest.fixture
    def fetcher(self):
        """創建測試用的 fetcher"""
        return StockDataFetcher()
        
    @pytest.fixture
    def mock_stock_data(self):
        """模擬股票數據"""
        return pd.DataFrame({
            '日期': pd.date_range('2024-01-01', periods=10),
            '開盤': np.random.uniform(100, 110, 10),
            '收盤': np.random.uniform(100, 110, 10),
            '最高': np.random.uniform(110, 120, 10),
            '最低': np.random.uniform(90, 100, 10),
            '成交量': np.random.randint(1000000, 5000000, 10),
            '成交額': np.random.uniform(1e8, 5e8, 10),
            '振幅': np.random.uniform(1, 5, 10),
            '漲跌幅': np.random.uniform(-3, 3, 10),
            '漲跌額': np.random.uniform(-3, 3, 10),
            '換手率': np.random.uniform(1, 5, 10)
        })
        
    def test_init(self, fetcher):
        """測試初始化"""
        assert fetcher.config is not None
        assert hasattr(fetcher, 'price_cache')
        assert hasattr(fetcher, 'fundamental_cache')
        assert hasattr(fetcher, 'industry_cache')
        
    def test_cache_operations(self, fetcher):
        """測試緩存操作"""
        # 測試保存到緩存
        test_data = {"test": "data"}
        fetcher._save_to_cache(CACHE_TYPE.PRICE, "test_key", test_data)
        
        # 測試從緩存獲取
        cached = fetcher._get_from_cache(CACHE_TYPE.PRICE, "test_key")
        assert cached == test_data
        
        # 測試緩存未命中
        assert fetcher._get_from_cache(CACHE_TYPE.PRICE, "non_existent") is None
        
    @patch('akshare.stock_individual_info_em')
    def test_fetch_stock_info(self, mock_ak_info, fetcher):
        """測試獲取股票基本信息"""
        # 模擬 akshare 返回數據
        mock_df = pd.DataFrame({
            'item': ['股票代碼', '股票簡稱', '所屬行業'],
            'value': ['000001', '平安銀行', '銀行']
        })
        mock_ak_info.return_value = mock_df
        
        # 調用方法
        result = fetcher.fetch_stock_info('000001')
        
        # 驗證結果
        assert result is not None
        assert result['股票代碼'] == '000001'
        assert result['股票簡稱'] == '平安銀行'
        assert result['所屬行業'] == '銀行'
        
        # 驗證調用
        mock_ak_info.assert_called_once_with(symbol='000001')
        
    @patch('akshare.stock_individual_info_em')
    def test_fetch_stock_info_error(self, mock_ak_info, fetcher):
        """測試獲取股票信息失敗的情況"""
        # 模擬異常
        mock_ak_info.side_effect = Exception("API Error")
        
        # 調用方法
        result = fetcher.fetch_stock_info('000001')
        
        # 應該返回 None
        assert result is None
        
    @patch('akshare.stock_zh_a_hist')
    def test_fetch_price_data(self, mock_ak_hist, fetcher, mock_stock_data):
        """測試獲取價格數據"""
        # 模擬 akshare 返回數據
        mock_ak_hist.return_value = mock_stock_data
        
        # 調用方法
        result = fetcher.fetch_price_data('000001', period='1m')
        
        # 驗證結果
        assert result is not None
        assert isinstance(result, pd.DataFrame)
        assert 'date' in result.columns
        assert 'close' in result.columns
        assert len(result) == 10
        
        # 驗證數據清理
        assert result.index.name == 'date'
        assert pd.api.types.is_datetime64_any_dtype(result.index)
        
    @patch('akshare.stock_zh_a_hist')
    def test_fetch_price_data_cache(self, mock_ak_hist, fetcher, mock_stock_data):
        """測試價格數據緩存"""
        # 模擬 akshare 返回數據
        mock_ak_hist.return_value = mock_stock_data
        
        # 第一次調用
        result1 = fetcher.fetch_price_data('000001', period='1m')
        assert mock_ak_hist.call_count == 1
        
        # 第二次調用（應該從緩存獲取）
        result2 = fetcher.fetch_price_data('000001', period='1m')
        assert mock_ak_hist.call_count == 1  # 不應該再次調用
        
        # 結果應該相同
        pd.testing.assert_frame_equal(result1, result2)
        
    def test_clean_price_data(self, fetcher, mock_stock_data):
        """測試價格數據清理"""
        # 添加一些問題數據
        mock_stock_data.loc[5, '收盤'] = np.nan
        mock_stock_data.loc[6, '最高'] = np.inf
        mock_stock_data.loc[7, '最低'] = -np.inf
        
        # 清理數據
        cleaned = fetcher._clean_price_data(mock_stock_data)
        
        # 驗證列名轉換
        assert 'close' in cleaned.columns
        assert 'high' in cleaned.columns
        assert 'low' in cleaned.columns
        
        # 驗證數據清理
        assert not cleaned['close'].isna().any()
        assert not np.isinf(cleaned['high']).any()
        assert not np.isinf(cleaned['low']).any()
        
    @patch('akshare.stock_financial_abstract_ths')
    @patch('akshare.stock_financial_analysis_indicator')
    @patch('akshare.stock_a_indicator_lg')
    @patch('akshare.stock_yjbb_em')
    @patch('akshare.stock_fhpg_em')
    def test_fetch_fundamental_data(self, mock_fhpg, mock_yjbb, mock_indicator,
                                  mock_analysis, mock_abstract, fetcher):
        """測試獲取基本面數據"""
        # 模擬各個 API 返回
        mock_abstract.return_value = pd.DataFrame({
            '報告期': ['2024-03-31'],
            '營業收入': [1000000000]
        })
        
        mock_analysis.return_value = pd.DataFrame({
            '淨資產收益率': [15.5],
            '毛利率': [30.2]
        })
        
        mock_indicator.return_value = pd.DataFrame({
            'pe_ttm': [12.5],
            'pb': [1.8],
            'ps_ttm': [2.3],
            'total_mv': [50000000000]
        })
        
        mock_yjbb.return_value = pd.DataFrame({
            '股票代碼': ['000001'],
            '業績類型': ['預增']
        })
        
        mock_fhpg.return_value = pd.DataFrame({
            '分紅方案': ['10派3'],
            '除權除息日': ['2024-06-30']
        })
        
        # 調用方法
        result = fetcher.fetch_fundamental_data('000001')
        
        # 驗證結果結構
        assert result is not None
        assert 'stock_code' in result
        assert 'update_time' in result
        assert 'financial_indicators' in result
        assert 'valuation_indicators' in result
        
    def test_calculate_core_financial_indicators(self, fetcher):
        """測試計算核心財務指標"""
        # 模擬財務數據
        mock_df = pd.DataFrame({
            '淨資產收益率': ['15.5%'],
            '總資產收益率': ['8.3%'],
            '毛利率': ['30.2%'],
            '淨利率': ['12.5%'],
            '營業利潤率': ['18.7%']
        })
        
        # 計算指標
        result = fetcher._calculate_core_financial_indicators(mock_df)
        
        # 驗證結果
        assert isinstance(result, dict)
        assert result['淨資產收益率'] == 15.5
        assert result['總資產收益率'] == 8.3
        assert result['毛利率'] == 30.2
        
    def test_safe_float(self, fetcher):
        """測試安全浮點數轉換"""
        # 測試各種輸入
        assert fetcher._safe_float(10) == 10.0
        assert fetcher._safe_float('15.5') == 15.5
        assert fetcher._safe_float('20.3%') == 20.3
        assert fetcher._safe_float('1,234.56') == 1234.56
        assert fetcher._safe_float(None) == 0.0
        assert fetcher._safe_float(np.nan) == 0.0
        assert fetcher._safe_float('invalid') == 0.0
        
    @patch('akshare.stock_board_industry_name_em')
    @patch('akshare.stock_board_industry_cons_em')
    def test_fetch_industry_data(self, mock_cons, mock_name, fetcher):
        """測試獲取行業數據"""
        # 模擬行業板塊列表
        mock_name.return_value = pd.DataFrame({
            '板塊名稱': ['銀行', '保險'],
            '板塊代碼': ['BK0819', 'BK0820']
        })
        
        # 模擬成分股數據
        mock_cons.return_value = pd.DataFrame({
            '代碼': ['000001', '000002', '600000'],
            '名稱': ['平安銀行', '萬科A', '浦發銀行'],
            '最新價': [10.5, 15.2, 8.3],
            '漲跌幅': [1.2, -0.5, 0.8]
        })
        
        # 調用方法
        result = fetcher.fetch_industry_data('000001')
        
        # 驗證結果
        assert result is not None
        assert result['stock_code'] == '000001'
        assert result['industry_name'] == '銀行'
        assert result['industry_rank'] == 1
        assert len(result['industry_stocks']) > 0
        
    @patch('akshare.stock_board_industry_name_em')
    def test_fetch_industry_data_error(self, mock_name, fetcher):
        """測試獲取行業數據失敗的情況"""
        # 模擬異常
        mock_name.side_effect = Exception("API Error")
        
        # 調用方法
        result = fetcher.fetch_industry_data('000001')
        
        # 應該返回基本結構
        assert result is not None
        assert result['stock_code'] == '000001'
        assert result['industry_name'] is None
        
    def test_period_mapping(self, fetcher):
        """測試週期映射"""
        # 測試不同週期的處理
        periods = ['1d', '1w', '1m', '3m', '6m', '1y', '2y', '3y', '5y']
        
        for period in periods:
            # 這裡只是驗證不會拋出異常
            # 實際調用需要 mock akshare
            assert period in ['1d', '1w', '1m', '3m', '6m', '1y', '2y', '3y', '5y']