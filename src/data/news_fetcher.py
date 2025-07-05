"""
新聞數據獲取模組

負責從 akshare 和其他來源獲取股票相關的新聞資訊，包括：
- 個股新聞
- 公司公告
- 研究報告
- 行業動態
- 市場情緒分析
"""

import akshare as ak
import pandas as pd
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple, Any
import hashlib
from collections import defaultdict
from ..utils.logger import get_logger
from ..core.config import ConfigManager as Config
from ..core.constants import CACHE_TYPE

logger = get_logger(__name__)


class NewsDataFetcher:
    """新聞數據獲取器"""
    
    def __init__(self, config: Optional[Config] = None):
        """
        初始化新聞數據獲取器
        
        Args:
            config: 配置對象，如果為 None 則使用默認配置
        """
        self.config = config or Config()
        self._init_cache()
        
    def _init_cache(self):
        """初始化緩存"""
        # 從配置中獲取緩存設置
        cache_config = self.config.get('cache', {})
        
        # 新聞數據緩存
        self.news_cache: Dict[str, Tuple[datetime, Dict]] = {}
        self.news_cache_duration = timedelta(
            hours=cache_config.get('news_hours', 2)
        )
        
        logger.info("新聞緩存系統初始化完成")
        
    def _get_from_cache(self, key: str) -> Optional[Dict]:
        """
        從緩存中獲取數據
        
        Args:
            key: 緩存鍵
            
        Returns:
            緩存的數據，如果不存在或已過期則返回 None
        """
        if key in self.news_cache:
            cache_time, data = self.news_cache[key]
            if datetime.now() - cache_time < self.news_cache_duration:
                logger.debug(f"從緩存獲取新聞數據: {key}")
                return data
                
        return None
        
    def _save_to_cache(self, key: str, data: Dict):
        """
        保存數據到緩存
        
        Args:
            key: 緩存鍵
            data: 要緩存的數據
        """
        self.news_cache[key] = (datetime.now(), data)
        logger.debug(f"新聞數據已緩存: {key}")
        
    def fetch_comprehensive_news(self, stock_code: str, days: int = 15) -> Optional[Dict]:
        """
        獲取綜合新聞數據
        
        Args:
            stock_code: 股票代碼
            days: 獲取最近幾天的新聞
            
        Returns:
            綜合新聞數據字典
        """
        # 檢查緩存
        cache_key = f"{stock_code}_{days}days"
        cached_data = self._get_from_cache(cache_key)
        if cached_data is not None:
            return cached_data
            
        try:
            logger.info(f"獲取綜合新聞數據: {stock_code}, 最近 {days} 天")
            
            news_data = {
                'stock_code': stock_code,
                'update_time': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                'days': days,
                'company_news': [],
                'announcements': [],
                'research_reports': [],
                'industry_news': [],
                'market_sentiment': {},
                'news_summary': {}
            }
            
            # 1. 獲取個股新聞
            company_news = self._fetch_company_news(stock_code, days)
            if company_news:
                news_data['company_news'] = company_news
                
            # 2. 獲取公司公告
            announcements = self._fetch_announcements(stock_code, days)
            if announcements:
                news_data['announcements'] = announcements
                
            # 3. 獲取研究報告
            research_reports = self._fetch_research_reports(stock_code)
            if research_reports:
                news_data['research_reports'] = research_reports
                
            # 4. 獲取行業新聞
            industry_news = self._fetch_industry_news(stock_code, days)
            if industry_news:
                news_data['industry_news'] = industry_news
                
            # 5. 分析市場情緒
            news_data['market_sentiment'] = self._analyze_market_sentiment(news_data)
            
            # 6. 生成新聞摘要
            news_data['news_summary'] = self._generate_news_summary(news_data)
            
            # 保存到緩存
            self._save_to_cache(cache_key, news_data)
            
            return news_data
            
        except Exception as e:
            logger.error(f"獲取綜合新聞失敗 {stock_code}: {str(e)}")
            return None
            
    def _fetch_company_news(self, stock_code: str, days: int) -> List[Dict]:
        """
        獲取個股新聞
        
        Args:
            stock_code: 股票代碼
            days: 天數
            
        Returns:
            新聞列表
        """
        try:
            logger.debug(f"獲取個股新聞: {stock_code}")
            
            # 獲取個股新聞
            news_df = ak.stock_news_em(symbol=stock_code)
            
            if news_df is None or news_df.empty:
                return []
                
            # 過濾最近N天的新聞
            news_df['發布時間'] = pd.to_datetime(news_df['發布時間'])
            cutoff_date = datetime.now() - timedelta(days=days)
            recent_news = news_df[news_df['發布時間'] >= cutoff_date]
            
            # 轉換為字典列表
            news_list = []
            for _, row in recent_news.iterrows():
                news_item = {
                    'title': row.get('新聞標題', ''),
                    'time': row.get('發布時間', '').strftime('%Y-%m-%d %H:%M:%S'),
                    'source': row.get('新聞來源', ''),
                    'content': row.get('新聞內容', ''),
                    'url': row.get('新聞鏈接', ''),
                    'type': 'company_news'
                }
                news_list.append(news_item)
                
            # 按時間倒序排序
            news_list.sort(key=lambda x: x['time'], reverse=True)
            
            # 限制返回數量
            return news_list[:50]
            
        except Exception as e:
            logger.warning(f"獲取個股新聞失敗: {e}")
            return []
            
    def _fetch_announcements(self, stock_code: str, days: int) -> List[Dict]:
        """
        獲取公司公告
        
        Args:
            stock_code: 股票代碼
            days: 天數
            
        Returns:
            公告列表
        """
        try:
            logger.debug(f"獲取公司公告: {stock_code}")
            
            # 獲取公司公告（使用東方財富接口）
            # 注意：這裡使用快訊作為公告的補充
            alerts_df = ak.stock_zh_a_alerts_cls()
            
            if alerts_df is None or alerts_df.empty:
                return []
                
            # 過濾包含股票代碼的公告
            stock_name = self._get_stock_name(stock_code)
            if not stock_name:
                return []
                
            # 過濾相關公告
            related_alerts = alerts_df[
                alerts_df['標題'].str.contains(stock_name, na=False) |
                alerts_df['內容'].str.contains(stock_code, na=False)
            ]
            
            # 過濾時間
            related_alerts['發布時間'] = pd.to_datetime(related_alerts['發布時間'])
            cutoff_date = datetime.now() - timedelta(days=days)
            recent_alerts = related_alerts[related_alerts['發布時間'] >= cutoff_date]
            
            # 轉換為字典列表
            announcement_list = []
            for _, row in recent_alerts.iterrows():
                announcement = {
                    'title': row.get('標題', ''),
                    'time': row.get('發布時間', '').strftime('%Y-%m-%d %H:%M:%S'),
                    'content': row.get('內容', ''),
                    'type': 'announcement',
                    'importance': self._judge_announcement_importance(row.get('標題', ''))
                }
                announcement_list.append(announcement)
                
            # 按時間倒序排序
            announcement_list.sort(key=lambda x: x['time'], reverse=True)
            
            return announcement_list[:30]
            
        except Exception as e:
            logger.warning(f"獲取公司公告失敗: {e}")
            return []
            
    def _fetch_research_reports(self, stock_code: str) -> List[Dict]:
        """
        獲取研究報告
        
        Args:
            stock_code: 股票代碼
            
        Returns:
            研究報告列表
        """
        try:
            logger.debug(f"獲取研究報告: {stock_code}")
            
            # 獲取研究報告
            reports_df = ak.stock_research_report_em(symbol=stock_code)
            
            if reports_df is None or reports_df.empty:
                return []
                
            # 轉換為字典列表
            report_list = []
            for _, row in reports_df.head(20).iterrows():
                report = {
                    'title': row.get('標題', ''),
                    'time': row.get('發布時間', ''),
                    'institution': row.get('機構', ''),
                    'analyst': row.get('分析師', ''),
                    'rating': row.get('評級', ''),
                    'target_price': row.get('目標價', ''),
                    'type': 'research_report'
                }
                report_list.append(report)
                
            return report_list
            
        except Exception as e:
            logger.warning(f"獲取研究報告失敗: {e}")
            return []
            
    def _fetch_industry_news(self, stock_code: str, days: int) -> List[Dict]:
        """
        獲取行業新聞
        
        Args:
            stock_code: 股票代碼
            days: 天數
            
        Returns:
            行業新聞列表
        """
        try:
            logger.debug(f"獲取行業新聞: {stock_code}")
            
            # 這裡簡化處理，實際可以通過行業分類獲取更精確的行業新聞
            # 暫時返回空列表，後續可以擴展
            return []
            
        except Exception as e:
            logger.warning(f"獲取行業新聞失敗: {e}")
            return []
            
    def _analyze_market_sentiment(self, news_data: Dict) -> Dict:
        """
        分析市場情緒
        
        Args:
            news_data: 新聞數據
            
        Returns:
            市場情緒分析結果
        """
        try:
            # 統計各類新聞數量
            sentiment_analysis = {
                'total_news': len(news_data.get('company_news', [])),
                'total_announcements': len(news_data.get('announcements', [])),
                'total_reports': len(news_data.get('research_reports', [])),
                'sentiment_keywords': {},
                'news_heat': 'normal',  # high, normal, low
                'sentiment_score': 50  # 0-100, 50為中性
            }
            
            # 分析新聞標題關鍵詞
            positive_keywords = ['漲', '增長', '突破', '新高', '利好', '超預期', '創新', '領先']
            negative_keywords = ['跌', '下降', '虧損', '風險', '利空', '低於預期', '處罰', '調查']
            
            positive_count = 0
            negative_count = 0
            
            # 統計所有新聞標題
            all_titles = []
            all_titles.extend([n['title'] for n in news_data.get('company_news', [])])
            all_titles.extend([n['title'] for n in news_data.get('announcements', [])])
            
            for title in all_titles:
                for keyword in positive_keywords:
                    if keyword in title:
                        positive_count += 1
                        sentiment_analysis['sentiment_keywords'][keyword] = \
                            sentiment_analysis['sentiment_keywords'].get(keyword, 0) + 1
                            
                for keyword in negative_keywords:
                    if keyword in title:
                        negative_count += 1
                        sentiment_analysis['sentiment_keywords'][keyword] = \
                            sentiment_analysis['sentiment_keywords'].get(keyword, 0) + 1
                            
            # 計算情緒分數
            total_sentiment = positive_count + negative_count
            if total_sentiment > 0:
                sentiment_score = int((positive_count / total_sentiment) * 100)
                sentiment_analysis['sentiment_score'] = sentiment_score
                
            # 判斷新聞熱度
            total_news = sentiment_analysis['total_news'] + sentiment_analysis['total_announcements']
            if total_news > 20:
                sentiment_analysis['news_heat'] = 'high'
            elif total_news > 10:
                sentiment_analysis['news_heat'] = 'normal'
            else:
                sentiment_analysis['news_heat'] = 'low'
                
            # 分析研究報告評級
            ratings = defaultdict(int)
            for report in news_data.get('research_reports', []):
                rating = report.get('rating', '')
                if rating:
                    ratings[rating] += 1
                    
            sentiment_analysis['research_ratings'] = dict(ratings)
            
            return sentiment_analysis
            
        except Exception as e:
            logger.error(f"分析市場情緒失敗: {e}")
            return {
                'sentiment_score': 50,
                'news_heat': 'normal',
                'sentiment_keywords': {}
            }
            
    def _generate_news_summary(self, news_data: Dict) -> Dict:
        """
        生成新聞摘要
        
        Args:
            news_data: 新聞數據
            
        Returns:
            新聞摘要
        """
        try:
            summary = {
                'latest_update': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                'key_events': [],
                'important_announcements': [],
                'analyst_consensus': None,
                'news_trend': 'neutral'  # positive, negative, neutral
            }
            
            # 提取最新的重要事件
            all_news = []
            
            # 添加新聞
            for news in news_data.get('company_news', [])[:5]:
                all_news.append({
                    'time': news['time'],
                    'title': news['title'],
                    'type': 'news'
                })
                
            # 添加重要公告
            for announcement in news_data.get('announcements', []):
                if announcement.get('importance', 'normal') == 'high':
                    summary['important_announcements'].append({
                        'time': announcement['time'],
                        'title': announcement['title']
                    })
                    
            # 分析師共識
            ratings = news_data.get('market_sentiment', {}).get('research_ratings', {})
            if ratings:
                # 找出最多的評級
                max_rating = max(ratings.items(), key=lambda x: x[1])
                summary['analyst_consensus'] = {
                    'rating': max_rating[0],
                    'count': max_rating[1],
                    'total': sum(ratings.values())
                }
                
            # 判斷新聞趨勢
            sentiment_score = news_data.get('market_sentiment', {}).get('sentiment_score', 50)
            if sentiment_score > 60:
                summary['news_trend'] = 'positive'
            elif sentiment_score < 40:
                summary['news_trend'] = 'negative'
            else:
                summary['news_trend'] = 'neutral'
                
            # 排序並取前5個關鍵事件
            all_news.sort(key=lambda x: x['time'], reverse=True)
            summary['key_events'] = all_news[:5]
            
            return summary
            
        except Exception as e:
            logger.error(f"生成新聞摘要失敗: {e}")
            return {
                'latest_update': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                'key_events': [],
                'news_trend': 'neutral'
            }
            
    def _get_stock_name(self, stock_code: str) -> Optional[str]:
        """
        獲取股票名稱
        
        Args:
            stock_code: 股票代碼
            
        Returns:
            股票名稱
        """
        try:
            # 使用個股信息接口獲取股票名稱
            info_df = ak.stock_individual_info_em(symbol=stock_code)
            if info_df is not None and not info_df.empty:
                # 查找股票名稱
                name_row = info_df[info_df['item'] == '股票簡稱']
                if not name_row.empty:
                    return name_row.iloc[0]['value']
            return None
        except:
            return None
            
    def _judge_announcement_importance(self, title: str) -> str:
        """
        判斷公告重要性
        
        Args:
            title: 公告標題
            
        Returns:
            重要性級別: high, normal, low
        """
        high_keywords = [
            '重大', '收購', '重組', '合併', '分拆', '退市',
            '停牌', '復牌', '業績預告', '利潤分配', '股權激勵'
        ]
        
        low_keywords = [
            '會議通知', '簡式', '摘要', '更正'
        ]
        
        # 檢查高重要性關鍵詞
        for keyword in high_keywords:
            if keyword in title:
                return 'high'
                
        # 檢查低重要性關鍵詞
        for keyword in low_keywords:
            if keyword in title:
                return 'low'
                
        return 'normal'