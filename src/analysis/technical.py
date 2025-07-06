"""
技術分析模組

提供股票技術指標計算和技術面評分功能
"""

import math
import pandas as pd
import numpy as np
from typing import Dict, Any, Optional
from ..utils.logger import get_logger
from ..core.config import Config

logger = get_logger(__name__)


class TechnicalAnalyzer:
    """技術分析器"""
    
    def __init__(self, config: Optional[Config] = None):
        """
        初始化技術分析器
        
        Args:
            config: 配置管理器實例
        """
        self.config = config or Config()
        self.logger = logger
        
    def analyze(self, price_data: pd.DataFrame) -> Dict[str, Any]:
        """
        執行完整的技術分析
        
        Args:
            price_data: 包含OHLCV數據的DataFrame
            
        Returns:
            包含技術指標和評分的字典
        """
        try:
            if price_data.empty:
                return self._get_default_result()
                
            # 計算技術指標
            indicators = self.calculate_indicators(price_data)
            
            # 計算技術評分
            score = self.calculate_score(indicators)
            
            return {
                'indicators': indicators,
                'score': score,
                'status': 'success'
            }
            
        except Exception as e:
            self.logger.error(f"技術分析失敗: {str(e)}")
            return self._get_default_result()
    
    def calculate_indicators(self, price_data: pd.DataFrame) -> Dict[str, Any]:
        """
        計算技術指標
        
        Args:
            price_data: 價格數據
            
        Returns:
            技術指標字典
        """
        try:
            if price_data.empty:
                return self._get_default_indicators()
                
            indicators = {}
            
            # 移動平均線
            indicators['ma'] = self._calculate_moving_averages(price_data)
            
            # RSI指標
            indicators['rsi'] = self._calculate_rsi(price_data)
            
            # MACD指標
            indicators['macd'] = self._calculate_macd(price_data)
            
            # 布林帶
            indicators['bollinger'] = self._calculate_bollinger_bands(price_data)
            
            # 成交量分析
            indicators['volume'] = self._analyze_volume(price_data)
            
            # KDJ指標
            indicators['kdj'] = self._calculate_kdj(price_data)
            
            # 波動率
            indicators['volatility'] = self._calculate_volatility(price_data)
            
            return indicators
            
        except Exception as e:
            self.logger.error(f"技術指標計算失敗: {str(e)}")
            return self._get_default_indicators()
    
    def calculate_score(self, indicators: Dict[str, Any]) -> float:
        """
        計算技術分析得分
        
        Args:
            indicators: 技術指標字典
            
        Returns:
            技術分析得分（0-100）
        """
        try:
            score = 50.0  # 基礎分數
            
            # 移動平均線趨勢評分
            ma_trend = indicators.get('ma', {}).get('trend', '震盪整理')
            if ma_trend == '多頭排列':
                score += 20
            elif ma_trend == '空頭排列':
                score -= 20
                
            # RSI評分
            rsi_value = indicators.get('rsi', {}).get('value', 50)
            rsi_signal = indicators.get('rsi', {}).get('signal', '中性')
            if rsi_signal == '超賣':
                score += 10
            elif rsi_signal == '超買':
                score -= 5
            elif 40 <= rsi_value <= 60:
                score += 5
                
            # MACD評分
            macd_signal = indicators.get('macd', {}).get('signal', '橫盤整理')
            if macd_signal == '金叉向上':
                score += 15
            elif macd_signal == '死叉向下':
                score -= 15
                
            # 布林帶評分
            bb_position = indicators.get('bollinger', {}).get('position', 0.5)
            bb_signal = indicators.get('bollinger', {}).get('signal', '中性')
            if bb_signal == '超賣區':
                score += 10
            elif bb_signal == '超買區':
                score -= 5
            elif 0.3 <= bb_position <= 0.7:
                score += 5
                
            # 成交量評分
            volume_status = indicators.get('volume', {}).get('status', '正常')
            if volume_status == '放量上漲':
                score += 10
            elif volume_status == '放量下跌':
                score -= 10
            elif volume_status == '縮量調整':
                score += 5
                
            # KDJ評分
            kdj_signal = indicators.get('kdj', {}).get('signal', '中性')
            if kdj_signal == '金叉':
                score += 5
            elif kdj_signal == '死叉':
                score -= 5
                
            # 波動率評分
            volatility = indicators.get('volatility', {}).get('current', 0.02)
            if volatility < 0.02:  # 低波動
                score += 5
            elif volatility > 0.05:  # 高波動
                score -= 5
                
            # 確保分數在0-100範圍內
            score = max(0, min(100, score))
            
            return round(score, 2)
            
        except Exception as e:
            self.logger.error(f"技術評分計算失敗: {str(e)}")
            return 50.0
    
    def _calculate_moving_averages(self, price_data: pd.DataFrame) -> Dict[str, Any]:
        """計算移動平均線"""
        try:
            result = {}
            
            # 計算各期移動平均線
            price_data['ma5'] = price_data['close'].rolling(window=5, min_periods=1).mean()
            price_data['ma10'] = price_data['close'].rolling(window=10, min_periods=1).mean()
            price_data['ma20'] = price_data['close'].rolling(window=20, min_periods=1).mean()
            price_data['ma60'] = price_data['close'].rolling(window=60, min_periods=1).mean()
            
            # 獲取最新值
            latest_price = self._safe_float(price_data['close'].iloc[-1])
            ma5 = self._safe_float(price_data['ma5'].iloc[-1], latest_price)
            ma10 = self._safe_float(price_data['ma10'].iloc[-1], latest_price)
            ma20 = self._safe_float(price_data['ma20'].iloc[-1], latest_price)
            ma60 = self._safe_float(price_data['ma60'].iloc[-1], latest_price)
            
            result['values'] = {
                'current': latest_price,
                'ma5': ma5,
                'ma10': ma10,
                'ma20': ma20,
                'ma60': ma60
            }
            
            # 判斷趨勢
            if latest_price > ma5 > ma10 > ma20:
                result['trend'] = '多頭排列'
            elif latest_price < ma5 < ma10 < ma20:
                result['trend'] = '空頭排列'
            else:
                result['trend'] = '震盪整理'
                
            # 計算均線支撐/壓力
            if latest_price > ma20:
                result['support'] = ma20
                result['resistance'] = None
            else:
                result['support'] = None
                result['resistance'] = ma20
                
            return result
            
        except Exception as e:
            self.logger.error(f"移動平均線計算失敗: {str(e)}")
            return {'trend': '計算失敗', 'values': {}}
    
    def _calculate_rsi(self, price_data: pd.DataFrame, window: int = 14) -> Dict[str, Any]:
        """計算RSI指標"""
        try:
            result = {}
            
            # 計算價格變化
            delta = price_data['close'].diff()
            
            # 計算漲跌幅
            gain = delta.where(delta > 0, 0).rolling(window=window, min_periods=1).mean()
            loss = (-delta.where(delta < 0, 0)).rolling(window=window, min_periods=1).mean()
            
            # 計算RS和RSI
            rs = gain / loss.replace(0, 1e-10)  # 避免除零
            rsi = 100 - (100 / (1 + rs))
            
            # 獲取最新RSI值
            current_rsi = self._safe_float(rsi.iloc[-1], 50.0)
            result['value'] = round(current_rsi, 2)
            
            # 判斷信號
            if current_rsi > 70:
                result['signal'] = '超買'
            elif current_rsi < 30:
                result['signal'] = '超賣'
            else:
                result['signal'] = '中性'
                
            # RSI趨勢
            if len(rsi) >= 2:
                prev_rsi = self._safe_float(rsi.iloc[-2], 50.0)
                result['trend'] = '上升' if current_rsi > prev_rsi else '下降'
            else:
                result['trend'] = '未知'
                
            return result
            
        except Exception as e:
            self.logger.error(f"RSI計算失敗: {str(e)}")
            return {'value': 50.0, 'signal': '計算失敗'}
    
    def _calculate_macd(self, price_data: pd.DataFrame) -> Dict[str, Any]:
        """計算MACD指標"""
        try:
            result = {}
            
            # 計算指數移動平均線
            ema12 = price_data['close'].ewm(span=12, min_periods=1, adjust=False).mean()
            ema26 = price_data['close'].ewm(span=26, min_periods=1, adjust=False).mean()
            
            # 計算MACD線和信號線
            macd_line = ema12 - ema26
            signal_line = macd_line.ewm(span=9, min_periods=1, adjust=False).mean()
            histogram = macd_line - signal_line
            
            # 獲取最新值
            current_macd = self._safe_float(macd_line.iloc[-1])
            current_signal = self._safe_float(signal_line.iloc[-1])
            current_hist = self._safe_float(histogram.iloc[-1])
            
            result['values'] = {
                'macd': round(current_macd, 4),
                'signal': round(current_signal, 4),
                'histogram': round(current_hist, 4)
            }
            
            # 判斷信號
            if len(histogram) >= 2:
                prev_hist = self._safe_float(histogram.iloc[-2])
                
                if current_hist > 0 and prev_hist <= 0:
                    result['signal'] = '金叉向上'
                elif current_hist < 0 and prev_hist >= 0:
                    result['signal'] = '死叉向下'
                elif current_hist > prev_hist:
                    result['signal'] = '向上發散'
                elif current_hist < prev_hist:
                    result['signal'] = '向下收斂'
                else:
                    result['signal'] = '橫盤整理'
            else:
                result['signal'] = '數據不足'
                
            return result
            
        except Exception as e:
            self.logger.error(f"MACD計算失敗: {str(e)}")
            return {'signal': '計算失敗', 'values': {}}
    
    def _calculate_bollinger_bands(self, price_data: pd.DataFrame, window: int = 20) -> Dict[str, Any]:
        """計算布林帶"""
        try:
            result = {}
            
            # 計算中軌（移動平均線）
            bb_middle = price_data['close'].rolling(window=window, min_periods=1).mean()
            
            # 計算標準差
            bb_std = price_data['close'].rolling(window=window, min_periods=1).std()
            
            # 計算上下軌
            bb_upper = bb_middle + 2 * bb_std
            bb_lower = bb_middle - 2 * bb_std
            
            # 獲取最新值
            latest_close = self._safe_float(price_data['close'].iloc[-1])
            upper_val = self._safe_float(bb_upper.iloc[-1])
            middle_val = self._safe_float(bb_middle.iloc[-1])
            lower_val = self._safe_float(bb_lower.iloc[-1])
            
            result['values'] = {
                'upper': round(upper_val, 2),
                'middle': round(middle_val, 2),
                'lower': round(lower_val, 2),
                'current': latest_close
            }
            
            # 計算相對位置（0-1）
            if upper_val > lower_val:
                position = (latest_close - lower_val) / (upper_val - lower_val)
                result['position'] = round(max(0, min(1, position)), 3)
            else:
                result['position'] = 0.5
                
            # 判斷信號
            if result['position'] > 0.9:
                result['signal'] = '超買區'
            elif result['position'] < 0.1:
                result['signal'] = '超賣區'
            elif result['position'] > 0.7:
                result['signal'] = '偏高'
            elif result['position'] < 0.3:
                result['signal'] = '偏低'
            else:
                result['signal'] = '中性'
                
            # 帶寬指標
            bandwidth = (upper_val - lower_val) / middle_val if middle_val > 0 else 0
            result['bandwidth'] = round(bandwidth, 4)
            
            return result
            
        except Exception as e:
            self.logger.error(f"布林帶計算失敗: {str(e)}")
            return {'position': 0.5, 'signal': '計算失敗', 'values': {}}
    
    def _analyze_volume(self, price_data: pd.DataFrame) -> Dict[str, Any]:
        """分析成交量"""
        try:
            result = {}
            
            # 計算平均成交量
            volume_window = min(20, len(price_data))
            avg_volume = price_data['volume'].rolling(window=volume_window, min_periods=1).mean()
            
            # 獲取最新成交量
            recent_volume = self._safe_float(price_data['volume'].iloc[-1])
            avg_volume_val = self._safe_float(avg_volume.iloc[-1], recent_volume)
            
            result['values'] = {
                'current': recent_volume,
                'average': avg_volume_val,
                'ratio': round(recent_volume / avg_volume_val, 2) if avg_volume_val > 0 else 1.0
            }
            
            # 計算價格變化
            if len(price_data) >= 2:
                price_change = self._calculate_price_change(price_data)
            else:
                price_change = 0
                
            # 判斷成交量狀態
            volume_ratio = result['values']['ratio']
            
            if volume_ratio > 2.0:
                result['status'] = '巨量' + ('上漲' if price_change > 0 else '下跌')
            elif volume_ratio > 1.5:
                result['status'] = '放量' + ('上漲' if price_change > 0 else '下跌')
            elif volume_ratio < 0.5:
                result['status'] = '縮量調整'
            elif volume_ratio < 0.7:
                result['status'] = '成交清淡'
            else:
                result['status'] = '正常'
                
            # 量價關係
            if price_change > 1 and volume_ratio > 1.2:
                result['relationship'] = '量價齊升'
            elif price_change < -1 and volume_ratio > 1.2:
                result['relationship'] = '放量下跌'
            elif abs(price_change) < 0.5 and volume_ratio < 0.7:
                result['relationship'] = '縮量橫盤'
            else:
                result['relationship'] = '正常'
                
            return result
            
        except Exception as e:
            self.logger.error(f"成交量分析失敗: {str(e)}")
            return {'status': '數據不足', 'values': {}}
    
    def _calculate_kdj(self, price_data: pd.DataFrame, window: int = 9) -> Dict[str, Any]:
        """計算KDJ指標"""
        try:
            result = {}
            
            # 計算RSV
            low_min = price_data['low'].rolling(window=window, min_periods=1).min()
            high_max = price_data['high'].rolling(window=window, min_periods=1).max()
            
            rsv = 100 * (price_data['close'] - low_min) / (high_max - low_min)
            rsv = rsv.fillna(50)
            
            # 計算K、D、J值
            k = rsv.ewm(com=2, min_periods=1, adjust=False).mean()
            d = k.ewm(com=2, min_periods=1, adjust=False).mean()
            j = 3 * k - 2 * d
            
            # 獲取最新值
            k_val = self._safe_float(k.iloc[-1], 50)
            d_val = self._safe_float(d.iloc[-1], 50)
            j_val = self._safe_float(j.iloc[-1], 50)
            
            result['values'] = {
                'k': round(k_val, 2),
                'd': round(d_val, 2),
                'j': round(j_val, 2)
            }
            
            # 判斷信號
            if k_val > d_val and len(k) >= 2:
                prev_k = self._safe_float(k.iloc[-2], 50)
                prev_d = self._safe_float(d.iloc[-2], 50)
                if prev_k <= prev_d:
                    result['signal'] = '金叉'
                else:
                    result['signal'] = '多頭'
            elif k_val < d_val and len(k) >= 2:
                prev_k = self._safe_float(k.iloc[-2], 50)
                prev_d = self._safe_float(d.iloc[-2], 50)
                if prev_k >= prev_d:
                    result['signal'] = '死叉'
                else:
                    result['signal'] = '空頭'
            else:
                result['signal'] = '中性'
                
            # 超買超賣判斷
            if k_val > 80 and d_val > 80:
                result['condition'] = '超買'
            elif k_val < 20 and d_val < 20:
                result['condition'] = '超賣'
            else:
                result['condition'] = '正常'
                
            return result
            
        except Exception as e:
            self.logger.error(f"KDJ計算失敗: {str(e)}")
            return {'signal': '計算失敗', 'values': {}}
    
    def _calculate_volatility(self, price_data: pd.DataFrame, window: int = 20) -> Dict[str, Any]:
        """計算波動率"""
        try:
            result = {}
            
            # 計算日收益率
            returns = price_data['close'].pct_change().dropna()
            
            if len(returns) < 2:
                return {'current': 0.02, 'level': '正常'}
                
            # 計算標準差（波動率）
            volatility = returns.rolling(window=min(window, len(returns)), min_periods=1).std()
            current_vol = self._safe_float(volatility.iloc[-1], 0.02)
            
            # 計算平均波動率
            avg_vol = self._safe_float(volatility.mean(), current_vol)
            
            result['values'] = {
                'current': round(current_vol, 4),
                'average': round(avg_vol, 4),
                'ratio': round(current_vol / avg_vol, 2) if avg_vol > 0 else 1.0
            }
            
            # 判斷波動水平
            if current_vol < 0.01:
                result['level'] = '極低'
            elif current_vol < 0.02:
                result['level'] = '低'
            elif current_vol < 0.04:
                result['level'] = '正常'
            elif current_vol < 0.06:
                result['level'] = '高'
            else:
                result['level'] = '極高'
                
            # 波動趨勢
            if len(volatility) >= 5:
                recent_vol = volatility.iloc[-5:].mean()
                earlier_vol = volatility.iloc[-10:-5].mean() if len(volatility) >= 10 else avg_vol
                
                if recent_vol > earlier_vol * 1.2:
                    result['trend'] = '上升'
                elif recent_vol < earlier_vol * 0.8:
                    result['trend'] = '下降'
                else:
                    result['trend'] = '穩定'
            else:
                result['trend'] = '未知'
                
            return result
            
        except Exception as e:
            self.logger.error(f"波動率計算失敗: {str(e)}")
            return {'current': 0.02, 'level': '計算失敗'}
    
    def _calculate_price_change(self, price_data: pd.DataFrame) -> float:
        """計算價格變化百分比"""
        try:
            if 'change_pct' in price_data.columns:
                return self._safe_float(price_data['change_pct'].iloc[-1])
            elif len(price_data) >= 2:
                current_price = self._safe_float(price_data['close'].iloc[-1])
                prev_price = self._safe_float(price_data['close'].iloc[-2])
                if prev_price > 0:
                    return ((current_price - prev_price) / prev_price) * 100
            return 0
        except:
            return 0
    
    def _safe_float(self, value: Any, default: float = 0.0) -> float:
        """安全的浮點數轉換"""
        try:
            if pd.isna(value):
                return default
            num_value = float(value)
            if math.isnan(num_value) or math.isinf(num_value):
                return default
            return num_value
        except (ValueError, TypeError):
            return default
    
    def _get_default_indicators(self) -> Dict[str, Any]:
        """獲取默認技術指標"""
        return {
            'ma': {'trend': '數據不足', 'values': {}},
            'rsi': {'value': 50.0, 'signal': '數據不足'},
            'macd': {'signal': '數據不足', 'values': {}},
            'bollinger': {'position': 0.5, 'signal': '數據不足', 'values': {}},
            'volume': {'status': '數據不足', 'values': {}},
            'kdj': {'signal': '數據不足', 'values': {}},
            'volatility': {'current': 0.02, 'level': '數據不足'}
        }
    
    def _get_default_result(self) -> Dict[str, Any]:
        """獲取默認分析結果"""
        return {
            'indicators': self._get_default_indicators(),
            'score': 50.0,
            'status': 'no_data'
        }