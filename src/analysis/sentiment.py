"""
情緒分析模組

提供新聞情緒分析和市場情緒評分功能
"""

from typing import Dict, Any, Optional, List, Tuple
from datetime import datetime, timedelta
from collections import defaultdict
import re
from ..utils.logger import get_logger
from ..core.config import Config

logger = get_logger(__name__)


class SentimentAnalyzer:
    """情緒分析器"""
    
    def __init__(self, config: Optional[Config] = None):
        """
        初始化情緒分析器
        
        Args:
            config: 配置管理器實例
        """
        self.config = config or Config()
        self.logger = logger
        
        # 初始化情緒詞典
        self._init_sentiment_dictionary()
        
        # 新聞類型權重
        self.news_type_weights = {
            '公司新聞': 1.0,
            '公司公告': 0.9,
            '研究報告': 0.8,
            '行業新聞': 0.6,
            '市場動態': 0.5
        }
        
    def analyze(self, news_data: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        執行完整的情緒分析
        
        Args:
            news_data: 新聞數據列表
            
        Returns:
            包含情緒分析結果和評分的字典
        """
        try:
            if not news_data:
                return self._get_default_result()
                
            # 執行高級情緒分析
            sentiment_analysis = self.calculate_advanced_sentiment(news_data)
            
            # 計算情緒得分
            score = self.calculate_score(sentiment_analysis)
            
            # 生成情緒報告
            report = self._generate_sentiment_report(sentiment_analysis)
            
            return {
                'analysis': sentiment_analysis,
                'score': score,
                'report': report,
                'status': 'success'
            }
            
        except Exception as e:
            self.logger.error(f"情緒分析失敗: {str(e)}")
            return self._get_default_result()
    
    def calculate_advanced_sentiment(self, news_data: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        計算高級情緒分析
        
        Args:
            news_data: 新聞數據列表
            
        Returns:
            情緒分析結果
        """
        try:
            # 初始化結果
            result = {
                'overall_sentiment': 0.0,
                'confidence_score': 0.0,
                'sentiment_distribution': {'positive': 0, 'neutral': 0, 'negative': 0},
                'category_sentiments': {},
                'sentiment_trend': [],
                'keyword_sentiments': {},
                'total_analyzed': 0,
                'analysis_details': []
            }
            
            if not news_data:
                return result
                
            # 按類型分組新聞
            news_by_type = self._group_news_by_type(news_data)
            
            # 分析每個類型的情緒
            category_scores = {}
            all_sentiments = []
            
            for news_type, news_list in news_by_type.items():
                type_sentiments = []
                
                for news in news_list:
                    # 分析單條新聞
                    sentiment = self._analyze_single_news(news)
                    type_sentiments.append(sentiment)
                    all_sentiments.append(sentiment)
                    
                    # 記錄詳細分析
                    result['analysis_details'].append({
                        'title': news.get('title', ''),
                        'type': news_type,
                        'sentiment': sentiment['score'],
                        'keywords': sentiment['keywords']
                    })
                    
                # 計算該類型的平均情緒
                if type_sentiments:
                    avg_sentiment = sum(s['score'] for s in type_sentiments) / len(type_sentiments)
                    category_scores[news_type] = avg_sentiment
                    
            result['category_sentiments'] = category_scores
            result['total_analyzed'] = len(all_sentiments)
            
            # 計算整體情緒（加權平均）
            if all_sentiments:
                result['overall_sentiment'] = self._calculate_weighted_sentiment(
                    news_by_type, category_scores
                )
                
                # 計算情緒分佈
                for sentiment in all_sentiments:
                    score = sentiment['score']
                    if score > 0.3:
                        result['sentiment_distribution']['positive'] += 1
                    elif score < -0.3:
                        result['sentiment_distribution']['negative'] += 1
                    else:
                        result['sentiment_distribution']['neutral'] += 1
                        
                # 計算置信度
                result['confidence_score'] = self._calculate_confidence(all_sentiments)
                
                # 分析情緒趨勢
                result['sentiment_trend'] = self._analyze_sentiment_trend(news_data)
                
                # 提取關鍵詞情緒
                result['keyword_sentiments'] = self._extract_keyword_sentiments(all_sentiments)
                
            return result
            
        except Exception as e:
            self.logger.error(f"高級情緒分析失敗: {str(e)}")
            return self._get_default_sentiment_analysis()
    
    def calculate_score(self, sentiment_analysis: Dict[str, Any]) -> float:
        """
        計算情緒分析得分
        
        Args:
            sentiment_analysis: 情緒分析結果
            
        Returns:
            情緒得分（0-100）
        """
        try:
            overall_sentiment = sentiment_analysis.get('overall_sentiment', 0.0)
            confidence_score = sentiment_analysis.get('confidence_score', 0.0)
            total_analyzed = sentiment_analysis.get('total_analyzed', 0)
            
            # 基礎得分：將情緒得分從[-1,1]映射到[0,100]
            base_score = (overall_sentiment + 1) * 50
            
            # 置信度調整（最多±10分）
            confidence_adjustment = confidence_score * 10
            
            # 新聞數量調整（最多+10分）
            news_adjustment = min(total_analyzed / 100, 1.0) * 10
            
            # 情緒分佈調整
            distribution = sentiment_analysis.get('sentiment_distribution', {})
            total_news = sum(distribution.values())
            if total_news > 0:
                positive_ratio = distribution.get('positive', 0) / total_news
                negative_ratio = distribution.get('negative', 0) / total_news
                
                # 正面新聞比例高加分，負面新聞比例高減分
                distribution_adjustment = (positive_ratio - negative_ratio) * 10
            else:
                distribution_adjustment = 0
                
            # 計算最終得分
            final_score = base_score + confidence_adjustment + news_adjustment + distribution_adjustment
            final_score = max(0, min(100, final_score))
            
            return round(final_score, 2)
            
        except Exception as e:
            self.logger.error(f"情緒得分計算失敗: {str(e)}")
            return 50.0
    
    def _init_sentiment_dictionary(self):
        """初始化情緒詞典"""
        # 正面詞彙（擴展版）
        self.positive_words = {
            # 業績相關
            '增長', '上漲', '提升', '改善', '優化', '創新高', '突破', '超預期',
            '盈利', '獲利', '賺錢', '營收增長', '利潤增長', '業績增長',
            # 技術突破
            '突破', '創新', '領先', '第一', '首創', '獨家', '革命性', '顛覆性',
            '技術優勢', '競爭優勢', '核心技術', '專利', '研發成功',
            # 市場地位
            '龍頭', '領導者', '市占率提升', '擴張', '佈局', '戰略合作', '強強聯合',
            '訂單增長', '中標', '簽約', '合作', '併購',
            # 財務健康
            '現金流充裕', '財務穩健', '低負債', '高股息', '分紅', '回購',
            '資產優質', '毛利率提升', '費用下降', '效率提升',
            # 市場情緒
            '看好', '推薦', '買入', '增持', '目標價上調', '評級上調',
            '機構看好', '資金流入', '主力買入', '北向資金'
        }
        
        # 負面詞彙（擴展版）
        self.negative_words = {
            # 業績相關
            '下降', '下跌', '減少', '虧損', '下滑', '衰退', '低於預期', '不及預期',
            '業績下滑', '利潤下降', '營收下降', '毛利率下降',
            # 經營問題
            '裁員', '關閉', '停產', '違約', '逾期', '訴訟', '處罰', '調查',
            '質量問題', '安全事故', '環保問題', '監管處罰',
            # 市場風險
            '競爭加劇', '市場萎縮', '需求下降', '訂單減少', '客戶流失',
            '市占率下降', '被超越', '技術落後', '產品滯銷',
            # 財務風險
            '資金緊張', '流動性風險', '高負債', '償債壓力', '現金流惡化',
            '壞賬', '減值', '計提', '財務造假', '審計問題',
            # 市場情緒
            '看跌', '賣出', '減持', '目標價下調', '評級下調', '不看好',
            '資金流出', '主力賣出', '拋售', '恐慌'
        }
        
        # 中性詞彙
        self.neutral_words = {
            '維持', '持平', '穩定', '正常', '一般', '預計', '可能',
            '觀望', '震盪', '盤整', '橫盤', '調整'
        }
        
        # 情緒強度修飾詞
        self.intensity_modifiers = {
            '大幅': 1.5, '顯著': 1.3, '明顯': 1.2, '較大': 1.1,
            '略微': 0.8, '小幅': 0.7, '輕微': 0.6, '稍微': 0.5
        }
        
    def _analyze_single_news(self, news: Dict[str, Any]) -> Dict[str, Any]:
        """分析單條新聞的情緒"""
        try:
            title = news.get('title', '')
            content = news.get('content', '')
            text = f"{title} {content}"
            
            # 統計情緒詞
            positive_count = 0
            negative_count = 0
            neutral_count = 0
            keywords = []
            
            # 查找情緒詞
            for word in self.positive_words:
                if word in text:
                    positive_count += text.count(word)
                    keywords.append(('正面', word))
                    
            for word in self.negative_words:
                if word in text:
                    negative_count += text.count(word)
                    keywords.append(('負面', word))
                    
            for word in self.neutral_words:
                if word in text:
                    neutral_count += text.count(word)
                    
            # 檢查強度修飾詞
            intensity = 1.0
            for modifier, factor in self.intensity_modifiers.items():
                if modifier in text:
                    intensity = max(intensity, factor)
                    
            # 計算情緒分數
            total_words = positive_count + negative_count + neutral_count
            if total_words > 0:
                # 基礎分數
                base_score = (positive_count - negative_count) / total_words
                # 應用強度修飾
                sentiment_score = base_score * intensity
                # 限制在[-1, 1]範圍
                sentiment_score = max(-1, min(1, sentiment_score))
            else:
                sentiment_score = 0
                
            return {
                'score': sentiment_score,
                'positive_count': positive_count,
                'negative_count': negative_count,
                'neutral_count': neutral_count,
                'keywords': keywords[:5],  # 只保留前5個關鍵詞
                'intensity': intensity
            }
            
        except Exception as e:
            self.logger.error(f"單條新聞分析失敗: {str(e)}")
            return {'score': 0, 'keywords': []}
    
    def _group_news_by_type(self, news_data: List[Dict[str, Any]]) -> Dict[str, List]:
        """按類型分組新聞"""
        grouped = defaultdict(list)
        
        for news in news_data:
            news_type = news.get('type', '其他')
            grouped[news_type].append(news)
            
        return dict(grouped)
    
    def _calculate_weighted_sentiment(self, news_by_type: Dict[str, List], 
                                    category_scores: Dict[str, float]) -> float:
        """計算加權平均情緒"""
        weighted_sum = 0
        weight_sum = 0
        
        for news_type, score in category_scores.items():
            weight = self.news_type_weights.get(news_type, 0.5)
            count = len(news_by_type.get(news_type, []))
            
            weighted_sum += score * weight * count
            weight_sum += weight * count
            
        if weight_sum > 0:
            return weighted_sum / weight_sum
        return 0
    
    def _calculate_confidence(self, sentiments: List[Dict[str, Any]]) -> float:
        """計算置信度分數"""
        if not sentiments:
            return 0
            
        # 基於情緒一致性計算置信度
        scores = [s['score'] for s in sentiments]
        
        # 計算標準差
        avg_score = sum(scores) / len(scores)
        variance = sum((s - avg_score) ** 2 for s in scores) / len(scores)
        std_dev = variance ** 0.5
        
        # 低標準差表示高一致性，高置信度
        # 將標準差映射到置信度（0-1）
        confidence = max(0, 1 - std_dev)
        
        # 考慮樣本數量
        sample_factor = min(len(sentiments) / 50, 1.0)  # 50條新聞達到最大置信度
        
        return confidence * sample_factor
    
    def _analyze_sentiment_trend(self, news_data: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """分析情緒趨勢"""
        try:
            # 按日期分組新聞
            news_by_date = defaultdict(list)
            
            for news in news_data:
                # 提取日期
                date_str = news.get('date', '')
                if date_str:
                    try:
                        date = datetime.strptime(date_str[:10], '%Y-%m-%d')
                        news_by_date[date.strftime('%Y-%m-%d')].append(news)
                    except:
                        continue
                        
            # 計算每日情緒
            trend = []
            for date in sorted(news_by_date.keys())[-7:]:  # 最近7天
                daily_news = news_by_date[date]
                daily_sentiments = [self._analyze_single_news(n)['score'] for n in daily_news]
                
                if daily_sentiments:
                    avg_sentiment = sum(daily_sentiments) / len(daily_sentiments)
                    trend.append({
                        'date': date,
                        'sentiment': round(avg_sentiment, 3),
                        'count': len(daily_sentiments)
                    })
                    
            return trend
            
        except Exception as e:
            self.logger.error(f"情緒趨勢分析失敗: {str(e)}")
            return []
    
    def _extract_keyword_sentiments(self, sentiments: List[Dict[str, Any]]) -> Dict[str, Dict]:
        """提取關鍵詞情緒"""
        keyword_stats = defaultdict(lambda: {'count': 0, 'sentiment': 0})
        
        for sentiment in sentiments:
            for sentiment_type, keyword in sentiment.get('keywords', []):
                keyword_stats[keyword]['count'] += 1
                keyword_stats[keyword]['sentiment'] += sentiment['score']
                keyword_stats[keyword]['type'] = sentiment_type
                
        # 計算平均情緒並排序
        result = {}
        for keyword, stats in keyword_stats.items():
            if stats['count'] > 0:
                avg_sentiment = stats['sentiment'] / stats['count']
                result[keyword] = {
                    'count': stats['count'],
                    'sentiment': round(avg_sentiment, 3),
                    'type': stats['type']
                }
                
        # 返回出現頻率最高的前10個關鍵詞
        sorted_keywords = sorted(result.items(), key=lambda x: x[1]['count'], reverse=True)
        return dict(sorted_keywords[:10])
    
    def _generate_sentiment_report(self, sentiment_analysis: Dict[str, Any]) -> Dict[str, Any]:
        """生成情緒分析報告"""
        try:
            report = {
                'summary': '',
                'highlights': [],
                'risks': [],
                'trend_analysis': ''
            }
            
            overall_sentiment = sentiment_analysis.get('overall_sentiment', 0)
            confidence = sentiment_analysis.get('confidence_score', 0)
            distribution = sentiment_analysis.get('sentiment_distribution', {})
            
            # 生成摘要
            if overall_sentiment > 0.5:
                sentiment_desc = '非常正面'
            elif overall_sentiment > 0.2:
                sentiment_desc = '偏正面'
            elif overall_sentiment > -0.2:
                sentiment_desc = '中性'
            elif overall_sentiment > -0.5:
                sentiment_desc = '偏負面'
            else:
                sentiment_desc = '非常負面'
                
            total_news = sum(distribution.values())
            if total_news > 0:
                positive_pct = distribution.get('positive', 0) / total_news * 100
                negative_pct = distribution.get('negative', 0) / total_news * 100
                
                report['summary'] = (
                    f"市場情緒{sentiment_desc}（得分：{overall_sentiment:.2f}），"
                    f"置信度：{confidence:.0%}。"
                    f"正面新聞佔{positive_pct:.0f}%，負面新聞佔{negative_pct:.0f}%"
                )
            else:
                report['summary'] = '暫無足夠新聞數據進行情緒分析'
                
            # 提取亮點和風險
            keyword_sentiments = sentiment_analysis.get('keyword_sentiments', {})
            for keyword, stats in keyword_sentiments.items():
                if stats['type'] == '正面' and stats['sentiment'] > 0.3:
                    report['highlights'].append(f"{keyword}（出現{stats['count']}次）")
                elif stats['type'] == '負面' and stats['sentiment'] < -0.3:
                    report['risks'].append(f"{keyword}（出現{stats['count']}次）")
                    
            # 趨勢分析
            trend = sentiment_analysis.get('sentiment_trend', [])
            if len(trend) >= 2:
                recent_sentiment = trend[-1]['sentiment']
                earlier_sentiment = trend[0]['sentiment']
                
                if recent_sentiment > earlier_sentiment + 0.1:
                    report['trend_analysis'] = '情緒趨勢向好，市場信心增強'
                elif recent_sentiment < earlier_sentiment - 0.1:
                    report['trend_analysis'] = '情緒趨勢轉弱，需關注風險'
                else:
                    report['trend_analysis'] = '情緒趨勢平穩'
            else:
                report['trend_analysis'] = '趨勢數據不足'
                
            return report
            
        except Exception as e:
            self.logger.error(f"生成情緒報告失敗: {str(e)}")
            return {'summary': '報告生成失敗', 'highlights': [], 'risks': []}
    
    def _get_default_sentiment_analysis(self) -> Dict[str, Any]:
        """獲取默認情緒分析結果"""
        return {
            'overall_sentiment': 0.0,
            'confidence_score': 0.0,
            'sentiment_distribution': {'positive': 0, 'neutral': 0, 'negative': 0},
            'category_sentiments': {},
            'sentiment_trend': [],
            'keyword_sentiments': {},
            'total_analyzed': 0,
            'analysis_details': []
        }
    
    def _get_default_result(self) -> Dict[str, Any]:
        """獲取默認分析結果"""
        return {
            'analysis': self._get_default_sentiment_analysis(),
            'score': 50.0,
            'report': {
                'summary': '無新聞數據',
                'highlights': [],
                'risks': [],
                'trend_analysis': '無趨勢數據'
            },
            'status': 'no_data'
        }