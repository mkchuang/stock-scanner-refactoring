"""
股票數據獲取模組

負責從 akshare 獲取股票相關的各類數據，包括：
- 股票基本信息
- 歷史價格數據
- 財務指標數據
- 行業分析數據
"""

import akshare as ak
import pandas as pd
from datetime import datetime, timedelta
from typing import Dict, Optional, Tuple, Any
import numpy as np
from ..utils.logger import get_logger
from ..core.config import ConfigManager as Config
from ..core.constants import CACHE_TYPE

logger = get_logger(__name__)


class StockDataFetcher:
    """股票數據獲取器"""
    
    def __init__(self, config: Optional[Config] = None):
        """
        初始化股票數據獲取器
        
        Args:
            config: 配置對象，如果為 None 則使用默認配置
        """
        self.config = config or Config()
        self._init_cache()
        
    def _init_cache(self):
        """初始化緩存"""
        # 從配置中獲取緩存設置
        cache_config = self.config.get('cache', {})
        
        # 價格數據緩存
        self.price_cache: Dict[str, Tuple[datetime, pd.DataFrame]] = {}
        self.price_cache_duration = timedelta(
            hours=cache_config.get('price_hours', 1)
        )
        
        # 基本面數據緩存
        self.fundamental_cache: Dict[str, Tuple[datetime, Dict]] = {}
        self.fundamental_cache_duration = timedelta(
            hours=cache_config.get('fundamental_hours', 6)
        )
        
        # 行業數據緩存
        self.industry_cache: Dict[str, Tuple[datetime, Dict]] = {}
        self.industry_cache_duration = timedelta(
            hours=cache_config.get('industry_hours', 12)
        )
        
        logger.info("緩存系統初始化完成")
        
    def _get_from_cache(self, cache_type: str, key: str) -> Optional[Any]:
        """
        從緩存中獲取數據
        
        Args:
            cache_type: 緩存類型
            key: 緩存鍵
            
        Returns:
            緩存的數據，如果不存在或已過期則返回 None
        """
        cache_map = {
            CACHE_TYPE.PRICE: (self.price_cache, self.price_cache_duration),
            CACHE_TYPE.FUNDAMENTAL: (self.fundamental_cache, self.fundamental_cache_duration),
            CACHE_TYPE.INDUSTRY: (self.industry_cache, self.industry_cache_duration),
        }
        
        if cache_type not in cache_map:
            return None
            
        cache, duration = cache_map[cache_type]
        
        if key in cache:
            cache_time, data = cache[key]
            if datetime.now() - cache_time < duration:
                logger.debug(f"從緩存獲取數據: {cache_type}/{key}")
                return data
                
        return None
        
    def _save_to_cache(self, cache_type: str, key: str, data: Any):
        """
        保存數據到緩存
        
        Args:
            cache_type: 緩存類型
            key: 緩存鍵
            data: 要緩存的數據
        """
        cache_map = {
            CACHE_TYPE.PRICE: self.price_cache,
            CACHE_TYPE.FUNDAMENTAL: self.fundamental_cache,
            CACHE_TYPE.INDUSTRY: self.industry_cache,
        }
        
        if cache_type in cache_map:
            cache_map[cache_type][key] = (datetime.now(), data)
            logger.debug(f"數據已緩存: {cache_type}/{key}")
            
    def fetch_stock_info(self, stock_code: str) -> Optional[Dict]:
        """
        獲取股票基本信息
        
        Args:
            stock_code: 股票代碼
            
        Returns:
            股票基本信息字典
        """
        try:
            logger.info(f"獲取股票基本信息: {stock_code}")
            
            # 使用東方財富接口獲取個股信息
            df = ak.stock_individual_info_em(symbol=stock_code)
            
            if df is None or df.empty:
                logger.warning(f"無法獲取股票信息: {stock_code}")
                return None
                
            # 轉換為字典格式
            info_dict = {}
            for _, row in df.iterrows():
                key = row['item']
                value = row['value']
                info_dict[key] = value
                
            return info_dict
            
        except Exception as e:
            logger.error(f"獲取股票信息失敗 {stock_code}: {str(e)}")
            return None
            
    def fetch_price_data(self, stock_code: str, period: str = '1y') -> Optional[pd.DataFrame]:
        """
        獲取股票歷史價格數據
        
        Args:
            stock_code: 股票代碼
            period: 時間週期 (1d, 1w, 1m, 3m, 6m, 1y, 2y, 3y, 5y)
            
        Returns:
            包含歷史價格的 DataFrame
        """
        # 檢查緩存
        cache_key = f"{stock_code}_{period}"
        cached_data = self._get_from_cache(CACHE_TYPE.PRICE, cache_key)
        if cached_data is not None:
            return cached_data
            
        try:
            logger.info(f"獲取股票價格數據: {stock_code}, 週期: {period}")
            
            # 計算開始日期
            end_date = datetime.now().strftime('%Y%m%d')
            period_map = {
                '1d': 1, '1w': 7, '1m': 30, '3m': 90,
                '6m': 180, '1y': 365, '2y': 730, '3y': 1095, '5y': 1825
            }
            
            days = period_map.get(period, 365)
            start_date = (datetime.now() - timedelta(days=days)).strftime('%Y%m%d')
            
            # 獲取歷史數據
            df = ak.stock_zh_a_hist(
                symbol=stock_code,
                period="daily",
                start_date=start_date,
                end_date=end_date,
                adjust="qfq"
            )
            
            if df is None or df.empty:
                logger.warning(f"無法獲取價格數據: {stock_code}")
                return None
                
            # 清理數據
            df = self._clean_price_data(df)
            
            # 保存到緩存
            self._save_to_cache(CACHE_TYPE.PRICE, cache_key, df)
            
            return df
            
        except Exception as e:
            logger.error(f"獲取價格數據失敗 {stock_code}: {str(e)}")
            return None
            
    def _clean_price_data(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        清理價格數據
        
        Args:
            df: 原始價格數據
            
        Returns:
            清理後的數據
        """
        # 重命名列名為英文
        column_map = {
            '日期': 'date',
            '開盤': 'open',
            '收盤': 'close',
            '最高': 'high',
            '最低': 'low',
            '成交量': 'volume',
            '成交額': 'amount',
            '振幅': 'amplitude',
            '漲跌幅': 'pct_change',
            '漲跌額': 'change',
            '換手率': 'turnover'
        }
        
        df = df.rename(columns=column_map)
        
        # 確保日期列為 datetime 類型
        if 'date' in df.columns:
            df['date'] = pd.to_datetime(df['date'])
            df = df.set_index('date')
            
        # 處理缺失值
        df = df.fillna(method='ffill').fillna(method='bfill')
        
        # 處理無窮大值
        df = df.replace([np.inf, -np.inf], np.nan).fillna(0)
        
        return df
        
    def fetch_fundamental_data(self, stock_code: str) -> Optional[Dict]:
        """
        獲取股票基本面數據（財務指標）
        
        Args:
            stock_code: 股票代碼
            
        Returns:
            基本面數據字典
        """
        # 檢查緩存
        cached_data = self._get_from_cache(CACHE_TYPE.FUNDAMENTAL, stock_code)
        if cached_data is not None:
            return cached_data
            
        try:
            logger.info(f"獲取基本面數據: {stock_code}")
            
            fundamental_data = {
                'stock_code': stock_code,
                'update_time': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                'financial_indicators': {},
                'valuation_indicators': {},
                'profit_forecast': {},
                'dividend_info': {}
            }
            
            # 1. 獲取財務摘要
            try:
                financial_summary = ak.stock_financial_abstract_ths(
                    symbol=stock_code,
                    indicator="按報告期"
                )
                if financial_summary is not None and not financial_summary.empty:
                    fundamental_data['financial_summary'] = financial_summary.to_dict('records')
            except Exception as e:
                logger.warning(f"獲取財務摘要失敗: {e}")
                
            # 2. 獲取財務分析指標
            try:
                financial_indicators = ak.stock_financial_analysis_indicator(
                    symbol=stock_code,
                    indicator="按年度"
                )
                if financial_indicators is not None and not financial_indicators.empty:
                    # 計算核心財務指標
                    core_indicators = self._calculate_core_financial_indicators(financial_indicators)
                    fundamental_data['financial_indicators'] = core_indicators
            except Exception as e:
                logger.warning(f"獲取財務指標失敗: {e}")
                
            # 3. 獲取估值指標
            try:
                valuation = ak.stock_a_indicator_lg(symbol=stock_code)
                if valuation is not None and not valuation.empty:
                    latest_valuation = valuation.iloc[-1].to_dict()
                    fundamental_data['valuation_indicators'] = {
                        'pe_ttm': latest_valuation.get('pe_ttm', None),
                        'pb': latest_valuation.get('pb', None),
                        'ps_ttm': latest_valuation.get('ps_ttm', None),
                        'total_mv': latest_valuation.get('total_mv', None)
                    }
            except Exception as e:
                logger.warning(f"獲取估值指標失敗: {e}")
                
            # 4. 獲取業績預告
            try:
                profit_forecast = ak.stock_yjbb_em(date="最新")
                if profit_forecast is not None and not profit_forecast.empty:
                    stock_forecast = profit_forecast[
                        profit_forecast['股票代碼'] == stock_code
                    ]
                    if not stock_forecast.empty:
                        fundamental_data['profit_forecast'] = stock_forecast.iloc[0].to_dict()
            except Exception as e:
                logger.warning(f"獲取業績預告失敗: {e}")
                
            # 5. 獲取分紅配股信息
            try:
                dividend_info = ak.stock_fhpg_em(symbol=stock_code)
                if dividend_info is not None and not dividend_info.empty:
                    fundamental_data['dividend_info'] = dividend_info.head(5).to_dict('records')
            except Exception as e:
                logger.warning(f"獲取分紅信息失敗: {e}")
                
            # 保存到緩存
            self._save_to_cache(CACHE_TYPE.FUNDAMENTAL, stock_code, fundamental_data)
            
            return fundamental_data
            
        except Exception as e:
            logger.error(f"獲取基本面數據失敗 {stock_code}: {str(e)}")
            return None
            
    def _calculate_core_financial_indicators(self, df: pd.DataFrame) -> Dict:
        """
        計算核心財務指標
        
        Args:
            df: 財務數據 DataFrame
            
        Returns:
            核心財務指標字典
        """
        try:
            # 獲取最新一期數據
            if df.empty:
                return {}
                
            latest = df.iloc[0].to_dict()
            
            # 定義25個核心財務指標
            core_indicators = {
                # 盈利能力指標
                '淨資產收益率': self._safe_float(latest.get('淨資產收益率', 0)),
                '總資產收益率': self._safe_float(latest.get('總資產收益率', 0)),
                '毛利率': self._safe_float(latest.get('毛利率', 0)),
                '淨利率': self._safe_float(latest.get('淨利率', 0)),
                '營業利潤率': self._safe_float(latest.get('營業利潤率', 0)),
                
                # 成長能力指標
                '營收增長率': self._safe_float(latest.get('營收增長率', 0)),
                '淨利潤增長率': self._safe_float(latest.get('淨利潤增長率', 0)),
                '總資產增長率': self._safe_float(latest.get('總資產增長率', 0)),
                '淨資產增長率': self._safe_float(latest.get('淨資產增長率', 0)),
                '每股收益增長率': self._safe_float(latest.get('每股收益增長率', 0)),
                
                # 營運能力指標
                '總資產周轉率': self._safe_float(latest.get('總資產周轉率', 0)),
                '應收賬款周轉率': self._safe_float(latest.get('應收賬款周轉率', 0)),
                '存貨周轉率': self._safe_float(latest.get('存貨周轉率', 0)),
                '流動資產周轉率': self._safe_float(latest.get('流動資產周轉率', 0)),
                
                # 償債能力指標
                '資產負債率': self._safe_float(latest.get('資產負債率', 0)),
                '流動比率': self._safe_float(latest.get('流動比率', 0)),
                '速動比率': self._safe_float(latest.get('速動比率', 0)),
                '利息保障倍數': self._safe_float(latest.get('利息保障倍數', 0)),
                
                # 現金流指標
                '經營現金流量比率': self._safe_float(latest.get('經營現金流量比率', 0)),
                '現金流量淨額比率': self._safe_float(latest.get('現金流量淨額比率', 0)),
                
                # 每股指標
                '每股收益': self._safe_float(latest.get('每股收益', 0)),
                '每股淨資產': self._safe_float(latest.get('每股淨資產', 0)),
                '每股經營現金流': self._safe_float(latest.get('每股經營現金流', 0)),
                '每股公積金': self._safe_float(latest.get('每股公積金', 0)),
                '每股未分配利潤': self._safe_float(latest.get('每股未分配利潤', 0))
            }
            
            return core_indicators
            
        except Exception as e:
            logger.error(f"計算財務指標失敗: {str(e)}")
            return {}
            
    def _safe_float(self, value: Any) -> float:
        """
        安全地轉換為浮點數
        
        Args:
            value: 要轉換的值
            
        Returns:
            浮點數，如果轉換失敗返回 0.0
        """
        try:
            if pd.isna(value) or value is None:
                return 0.0
            if isinstance(value, str):
                # 處理百分號
                value = value.replace('%', '').replace(',', '')
            return float(value)
        except:
            return 0.0
            
    def fetch_industry_data(self, stock_code: str) -> Optional[Dict]:
        """
        獲取股票行業數據
        
        Args:
            stock_code: 股票代碼
            
        Returns:
            行業數據字典
        """
        # 檢查緩存
        cached_data = self._get_from_cache(CACHE_TYPE.INDUSTRY, stock_code)
        if cached_data is not None:
            return cached_data
            
        try:
            logger.info(f"獲取行業數據: {stock_code}")
            
            industry_data = {
                'stock_code': stock_code,
                'update_time': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                'industry_name': None,
                'industry_rank': None,
                'industry_stocks': []
            }
            
            # 獲取行業板塊信息
            try:
                # 獲取所有行業板塊
                industry_df = ak.stock_board_industry_name_em()
                
                # 查找股票所屬行業
                for _, industry in industry_df.iterrows():
                    industry_name = industry['板塊名稱']
                    industry_code = industry['板塊代碼']
                    
                    # 獲取板塊成分股
                    try:
                        constituents = ak.stock_board_industry_cons_em(symbol=industry_name)
                        if stock_code in constituents['代碼'].values:
                            industry_data['industry_name'] = industry_name
                            industry_data['industry_code'] = industry_code
                            
                            # 獲取行業內排名
                            constituents['排名'] = range(1, len(constituents) + 1)
                            stock_rank = constituents[constituents['代碼'] == stock_code]['排名'].values
                            if len(stock_rank) > 0:
                                industry_data['industry_rank'] = int(stock_rank[0])
                                industry_data['industry_total'] = len(constituents)
                                
                            # 獲取行業內前10股票
                            top_stocks = constituents.head(10)[['代碼', '名稱', '最新價', '漲跌幅']]
                            industry_data['industry_stocks'] = top_stocks.to_dict('records')
                            
                            break
                    except:
                        continue
                        
            except Exception as e:
                logger.warning(f"獲取行業信息失敗: {e}")
                
            # 保存到緩存
            self._save_to_cache(CACHE_TYPE.INDUSTRY, stock_code, industry_data)
            
            return industry_data
            
        except Exception as e:
            logger.error(f"獲取行業數據失敗 {stock_code}: {str(e)}")
            return None