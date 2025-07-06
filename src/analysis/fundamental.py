"""
基本面分析模組

提供財務指標分析和基本面評分功能
"""

from typing import Dict, Any, Optional, List
from ..utils.logger import get_logger
from ..core.config import Config

logger = get_logger(__name__)


class FundamentalAnalyzer:
    """基本面分析器"""
    
    def __init__(self, config: Optional[Config] = None):
        """
        初始化基本面分析器
        
        Args:
            config: 配置管理器實例
        """
        self.config = config or Config()
        self.logger = logger
        
        # 財務指標權重配置
        self.indicator_weights = {
            'profitability': 0.3,    # 盈利能力
            'solvency': 0.2,         # 償債能力
            'operation': 0.2,        # 營運能力
            'growth': 0.2,           # 成長能力
            'valuation': 0.1         # 估值水平
        }
        
    def analyze(self, fundamental_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        執行完整的基本面分析
        
        Args:
            fundamental_data: 包含財務數據的字典
            
        Returns:
            包含分析結果和評分的字典
        """
        try:
            if not fundamental_data:
                return self._get_default_result()
                
            # 分析財務指標
            analysis = self._analyze_financial_indicators(fundamental_data)
            
            # 計算各維度得分
            scores = self._calculate_dimension_scores(analysis)
            
            # 計算綜合得分
            total_score = self.calculate_score(fundamental_data, scores)
            
            return {
                'analysis': analysis,
                'dimension_scores': scores,
                'score': total_score,
                'status': 'success'
            }
            
        except Exception as e:
            self.logger.error(f"基本面分析失敗: {str(e)}")
            return self._get_default_result()
    
    def calculate_score(self, fundamental_data: Dict[str, Any], 
                       dimension_scores: Optional[Dict[str, float]] = None) -> float:
        """
        計算基本面得分
        
        Args:
            fundamental_data: 財務數據
            dimension_scores: 各維度得分（可選）
            
        Returns:
            基本面得分（0-100）
        """
        try:
            base_score = 50.0
            
            # 如果提供了維度得分，使用加權計算
            if dimension_scores:
                weighted_score = sum(
                    dimension_scores.get(dim, 50) * weight 
                    for dim, weight in self.indicator_weights.items()
                )
                return round(weighted_score, 2)
            
            # 否則使用簡單評分邏輯
            financial_indicators = fundamental_data.get('financial_indicators', {})
            
            # 財務指標完整性
            if len(financial_indicators) >= 15:
                base_score += 20
                
                # 盈利能力評分
                roe = financial_indicators.get('淨資產收益率', 0)
                if roe > 15:
                    base_score += 10
                elif roe > 10:
                    base_score += 5
                elif roe < 5:
                    base_score -= 5
                    
                # 償債能力評分
                debt_ratio = financial_indicators.get('資產負債率', 50)
                if debt_ratio < 30:
                    base_score += 5
                elif debt_ratio > 70:
                    base_score -= 10
                    
                # 成長性評分
                revenue_growth = financial_indicators.get('營收同比增長率', 0)
                if revenue_growth > 20:
                    base_score += 10
                elif revenue_growth > 10:
                    base_score += 5
                elif revenue_growth < -10:
                    base_score -= 10
                    
            # 估值評分
            valuation = fundamental_data.get('valuation', {})
            if valuation:
                base_score += 10
                
            # 業績預告評分
            performance_forecast = fundamental_data.get('performance_forecast', [])
            if performance_forecast:
                base_score += 10
                
            # 確保分數在0-100範圍內
            return round(max(0, min(100, base_score)), 2)
            
        except Exception as e:
            self.logger.error(f"基本面評分計算失敗: {str(e)}")
            return 50.0
    
    def _analyze_financial_indicators(self, fundamental_data: Dict[str, Any]) -> Dict[str, Any]:
        """分析財務指標"""
        try:
            financial_indicators = fundamental_data.get('financial_indicators', {})
            
            analysis = {
                'profitability': self._analyze_profitability(financial_indicators),
                'solvency': self._analyze_solvency(financial_indicators),
                'operation': self._analyze_operation(financial_indicators),
                'growth': self._analyze_growth(financial_indicators),
                'valuation': self._analyze_valuation(fundamental_data.get('valuation', {})),
                'summary': {}
            }
            
            # 生成綜合評價
            analysis['summary'] = self._generate_summary(analysis)
            
            return analysis
            
        except Exception as e:
            self.logger.error(f"財務指標分析失敗: {str(e)}")
            return {}
    
    def _analyze_profitability(self, indicators: Dict[str, Any]) -> Dict[str, Any]:
        """分析盈利能力"""
        try:
            result = {
                'indicators': {},
                'evaluation': '',
                'score': 50.0
            }
            
            # 提取盈利指標
            roe = indicators.get('淨資產收益率', 0)
            roa = indicators.get('總資產收益率', 0)
            gross_margin = indicators.get('毛利率', 0)
            net_margin = indicators.get('淨利率', 0)
            operating_margin = indicators.get('營業利潤率', 0)
            
            result['indicators'] = {
                'ROE': roe,
                'ROA': roa,
                '毛利率': gross_margin,
                '淨利率': net_margin,
                '營業利潤率': operating_margin
            }
            
            # 評分邏輯
            score = 50.0
            
            # ROE評分（權重最高）
            if roe > 20:
                score += 20
                roe_eval = '優秀'
            elif roe > 15:
                score += 15
                roe_eval = '良好'
            elif roe > 10:
                score += 10
                roe_eval = '正常'
            elif roe > 5:
                score += 5
                roe_eval = '偏低'
            else:
                score -= 10
                roe_eval = '較差'
                
            # 毛利率評分
            if gross_margin > 40:
                score += 10
                margin_eval = '高毛利'
            elif gross_margin > 25:
                score += 5
                margin_eval = '中等毛利'
            else:
                margin_eval = '低毛利'
                
            # 淨利率評分
            if net_margin > 15:
                score += 10
            elif net_margin > 10:
                score += 5
            elif net_margin < 5:
                score -= 5
                
            # 生成評價
            result['evaluation'] = f"ROE {roe_eval}（{roe:.1f}%），{margin_eval}（{gross_margin:.1f}%）"
            result['score'] = max(0, min(100, score))
            
            return result
            
        except Exception as e:
            self.logger.error(f"盈利能力分析失敗: {str(e)}")
            return {'indicators': {}, 'evaluation': '分析失敗', 'score': 50.0}
    
    def _analyze_solvency(self, indicators: Dict[str, Any]) -> Dict[str, Any]:
        """分析償債能力"""
        try:
            result = {
                'indicators': {},
                'evaluation': '',
                'score': 50.0
            }
            
            # 提取償債指標
            debt_ratio = indicators.get('資產負債率', 50)
            current_ratio = indicators.get('流動比率', 1)
            quick_ratio = indicators.get('速動比率', 0.8)
            interest_coverage = indicators.get('利息保障倍數', 2)
            cash_ratio = indicators.get('現金比率', 0.2)
            
            result['indicators'] = {
                '資產負債率': debt_ratio,
                '流動比率': current_ratio,
                '速動比率': quick_ratio,
                '利息保障倍數': interest_coverage,
                '現金比率': cash_ratio
            }
            
            # 評分邏輯
            score = 50.0
            
            # 資產負債率評分
            if debt_ratio < 30:
                score += 15
                debt_eval = '低負債'
            elif debt_ratio < 50:
                score += 10
                debt_eval = '適中負債'
            elif debt_ratio < 70:
                score += 5
                debt_eval = '較高負債'
            else:
                score -= 10
                debt_eval = '高負債'
                
            # 流動比率評分
            if current_ratio > 2:
                score += 10
                liquidity_eval = '流動性充足'
            elif current_ratio > 1.5:
                score += 5
                liquidity_eval = '流動性良好'
            elif current_ratio > 1:
                liquidity_eval = '流動性一般'
            else:
                score -= 10
                liquidity_eval = '流動性不足'
                
            # 速動比率評分
            if quick_ratio > 1:
                score += 10
            elif quick_ratio > 0.7:
                score += 5
            else:
                score -= 5
                
            # 生成評價
            result['evaluation'] = f"{debt_eval}（{debt_ratio:.1f}%），{liquidity_eval}（{current_ratio:.2f}）"
            result['score'] = max(0, min(100, score))
            
            return result
            
        except Exception as e:
            self.logger.error(f"償債能力分析失敗: {str(e)}")
            return {'indicators': {}, 'evaluation': '分析失敗', 'score': 50.0}
    
    def _analyze_operation(self, indicators: Dict[str, Any]) -> Dict[str, Any]:
        """分析營運能力"""
        try:
            result = {
                'indicators': {},
                'evaluation': '',
                'score': 50.0
            }
            
            # 提取營運指標
            inventory_turnover = indicators.get('存貨週轉率', 0)
            receivable_turnover = indicators.get('應收帳款週轉率', 0)
            asset_turnover = indicators.get('總資產週轉率', 0)
            fixed_asset_turnover = indicators.get('固定資產週轉率', 0)
            working_capital_turnover = indicators.get('營運資金週轉率', 0)
            
            result['indicators'] = {
                '存貨週轉率': inventory_turnover,
                '應收帳款週轉率': receivable_turnover,
                '總資產週轉率': asset_turnover,
                '固定資產週轉率': fixed_asset_turnover,
                '營運資金週轉率': working_capital_turnover
            }
            
            # 評分邏輯
            score = 50.0
            
            # 存貨週轉率評分
            if inventory_turnover > 6:
                score += 10
                inventory_eval = '快速'
            elif inventory_turnover > 4:
                score += 5
                inventory_eval = '正常'
            elif inventory_turnover > 2:
                inventory_eval = '偏慢'
            else:
                score -= 5
                inventory_eval = '緩慢'
                
            # 應收帳款週轉率評分
            if receivable_turnover > 12:
                score += 10
                receivable_eval = '回款快'
            elif receivable_turnover > 6:
                score += 5
                receivable_eval = '回款正常'
            else:
                receivable_eval = '回款慢'
                
            # 總資產週轉率評分
            if asset_turnover > 1:
                score += 10
            elif asset_turnover > 0.5:
                score += 5
            else:
                score -= 5
                
            # 生成評價
            result['evaluation'] = f"存貨週轉{inventory_eval}（{inventory_turnover:.1f}次/年），{receivable_eval}（{receivable_turnover:.1f}次/年）"
            result['score'] = max(0, min(100, score))
            
            return result
            
        except Exception as e:
            self.logger.error(f"營運能力分析失敗: {str(e)}")
            return {'indicators': {}, 'evaluation': '分析失敗', 'score': 50.0}
    
    def _analyze_growth(self, indicators: Dict[str, Any]) -> Dict[str, Any]:
        """分析成長能力"""
        try:
            result = {
                'indicators': {},
                'evaluation': '',
                'score': 50.0
            }
            
            # 提取成長指標
            revenue_growth = indicators.get('營收同比增長率', 0)
            profit_growth = indicators.get('淨利潤同比增長率', 0)
            asset_growth = indicators.get('總資產增長率', 0)
            equity_growth = indicators.get('淨資產增長率', 0)
            eps_growth = indicators.get('每股收益增長率', 0)
            
            result['indicators'] = {
                '營收增長率': revenue_growth,
                '淨利潤增長率': profit_growth,
                '總資產增長率': asset_growth,
                '淨資產增長率': equity_growth,
                '每股收益增長率': eps_growth
            }
            
            # 評分邏輯
            score = 50.0
            
            # 營收增長評分
            if revenue_growth > 30:
                score += 20
                revenue_eval = '高速增長'
            elif revenue_growth > 20:
                score += 15
                revenue_eval = '快速增長'
            elif revenue_growth > 10:
                score += 10
                revenue_eval = '穩定增長'
            elif revenue_growth > 0:
                score += 5
                revenue_eval = '緩慢增長'
            else:
                score -= 10
                revenue_eval = '負增長'
                
            # 利潤增長評分
            if profit_growth > revenue_growth + 10:
                score += 15
                profit_eval = '利潤增速超營收'
            elif profit_growth > revenue_growth:
                score += 10
                profit_eval = '利潤同步增長'
            elif profit_growth > 0:
                score += 5
                profit_eval = '利潤正增長'
            else:
                score -= 5
                profit_eval = '利潤下滑'
                
            # 生成評價
            result['evaluation'] = f"營收{revenue_eval}（{revenue_growth:.1f}%），{profit_eval}（{profit_growth:.1f}%）"
            result['score'] = max(0, min(100, score))
            
            return result
            
        except Exception as e:
            self.logger.error(f"成長能力分析失敗: {str(e)}")
            return {'indicators': {}, 'evaluation': '分析失敗', 'score': 50.0}
    
    def _analyze_valuation(self, valuation_data: Dict[str, Any]) -> Dict[str, Any]:
        """分析估值水平"""
        try:
            result = {
                'indicators': {},
                'evaluation': '',
                'score': 50.0
            }
            
            if not valuation_data:
                return result
                
            # 提取估值指標
            pe_ratio = valuation_data.get('市盈率', 0)
            pb_ratio = valuation_data.get('市淨率', 0)
            ps_ratio = valuation_data.get('市銷率', 0)
            peg_ratio = valuation_data.get('PEG', 0)
            
            result['indicators'] = {
                '市盈率(PE)': pe_ratio,
                '市淨率(PB)': pb_ratio,
                '市銷率(PS)': ps_ratio,
                'PEG': peg_ratio
            }
            
            # 評分邏輯
            score = 50.0
            
            # PE評分
            if 0 < pe_ratio < 15:
                score += 15
                pe_eval = '低估'
            elif 15 <= pe_ratio < 25:
                score += 10
                pe_eval = '合理'
            elif 25 <= pe_ratio < 40:
                score += 5
                pe_eval = '偏高'
            else:
                score -= 5
                pe_eval = '高估'
                
            # PB評分
            if 0 < pb_ratio < 1:
                score += 10
                pb_eval = '破淨'
            elif 1 <= pb_ratio < 3:
                score += 5
                pb_eval = '正常'
            else:
                pb_eval = '偏高'
                
            # PEG評分
            if 0 < peg_ratio < 1:
                score += 10
            elif 1 <= peg_ratio < 2:
                score += 5
                
            # 生成評價
            result['evaluation'] = f"PE{pe_eval}（{pe_ratio:.1f}），PB{pb_eval}（{pb_ratio:.2f}）"
            result['score'] = max(0, min(100, score))
            
            return result
            
        except Exception as e:
            self.logger.error(f"估值分析失敗: {str(e)}")
            return {'indicators': {}, 'evaluation': '分析失敗', 'score': 50.0}
    
    def _calculate_dimension_scores(self, analysis: Dict[str, Any]) -> Dict[str, float]:
        """計算各維度得分"""
        try:
            scores = {}
            
            for dimension in ['profitability', 'solvency', 'operation', 'growth', 'valuation']:
                if dimension in analysis and 'score' in analysis[dimension]:
                    scores[dimension] = analysis[dimension]['score']
                else:
                    scores[dimension] = 50.0
                    
            return scores
            
        except Exception as e:
            self.logger.error(f"維度得分計算失敗: {str(e)}")
            return {dim: 50.0 for dim in self.indicator_weights.keys()}
    
    def _generate_summary(self, analysis: Dict[str, Any]) -> Dict[str, Any]:
        """生成綜合評價摘要"""
        try:
            summary = {
                'strengths': [],
                'weaknesses': [],
                'overall': ''
            }
            
            # 分析優勢和劣勢
            for dimension, data in analysis.items():
                if isinstance(data, dict) and 'score' in data:
                    if data['score'] >= 70:
                        summary['strengths'].append(self._get_dimension_name(dimension))
                    elif data['score'] <= 30:
                        summary['weaknesses'].append(self._get_dimension_name(dimension))
                        
            # 生成總體評價
            avg_score = sum(
                analysis.get(dim, {}).get('score', 50) 
                for dim in ['profitability', 'solvency', 'operation', 'growth', 'valuation']
            ) / 5
            
            if avg_score >= 70:
                summary['overall'] = '基本面優秀，財務狀況健康'
            elif avg_score >= 60:
                summary['overall'] = '基本面良好，具有投資價值'
            elif avg_score >= 50:
                summary['overall'] = '基本面一般，需關注風險'
            else:
                summary['overall'] = '基本面較差，謹慎投資'
                
            return summary
            
        except Exception as e:
            self.logger.error(f"生成綜合評價失敗: {str(e)}")
            return {'strengths': [], 'weaknesses': [], 'overall': '評價失敗'}
    
    def _get_dimension_name(self, dimension: str) -> str:
        """獲取維度中文名稱"""
        names = {
            'profitability': '盈利能力',
            'solvency': '償債能力',
            'operation': '營運能力',
            'growth': '成長能力',
            'valuation': '估值水平'
        }
        return names.get(dimension, dimension)
    
    def _get_default_result(self) -> Dict[str, Any]:
        """獲取默認分析結果"""
        return {
            'analysis': {},
            'dimension_scores': {dim: 50.0 for dim in self.indicator_weights.keys()},
            'score': 50.0,
            'status': 'no_data'
        }