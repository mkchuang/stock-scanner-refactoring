"""
新聞數據獲取模組的單元測試
"""

import pytest
from unittest.mock import Mock, patch, MagicMock
import pandas as pd
from datetime import datetime, timedelta
from src.data.news_fetcher import NewsDataFetcher
from src.core.constants import CACHE_TYPE


class TestNewsDataFetcher:
    """新聞數據獲取器測試"""
    
    @pytest.fixture
    def fetcher(self):
        """創建測試用的 fetcher"""
        return NewsDataFetcher()
        
    @pytest.fixture
    def mock_news_data(self):
        """模擬新聞數據"""
        base_time = datetime.now()
        return pd.DataFrame({
            '新聞標題': [
                '公司業績增長超預期',
                '新產品發布會成功舉行',
                '獲得重要訂單',
                '市場份額持續提升',
                '技術創新獲得突破'
            ],
            '發布時間': [
                base_time - timedelta(hours=i) for i in range(5)
            ],
            '新聞來源': ['財經網', '證券時報', '新浪財經', '東方財富', '騰訊財經'],
            '新聞內容': ['內容' + str(i) for i in range(5)],
            '新聞鏈接': ['http://example.com/' + str(i) for i in range(5)]
        })
        
    def test_init(self, fetcher):
        """測試初始化"""
        assert fetcher.config is not None
        assert hasattr(fetcher, 'news_cache')
        assert hasattr(fetcher, 'news_cache_duration')
        
    def test_cache_operations(self, fetcher):
        """測試緩存操作"""
        # 測試保存到緩存
        test_data = {"news": "test data"}
        fetcher._save_to_cache("test_key", test_data)
        
        # 測試從緩存獲取
        cached = fetcher._get_from_cache("test_key")
        assert cached == test_data
        
        # 測試緩存未命中
        assert fetcher._get_from_cache("non_existent") is None
        
    @patch('akshare.stock_news_em')
    @patch('akshare.stock_zh_a_alerts_cls')
    @patch('akshare.stock_research_report_em')
    @patch('akshare.stock_individual_info_em')
    def test_fetch_comprehensive_news(self, mock_info, mock_report, 
                                    mock_alerts, mock_news, fetcher, mock_news_data):
        """測試獲取綜合新聞數據"""
        # 模擬股票名稱
        mock_info.return_value = pd.DataFrame({
            'item': ['股票簡稱'],
            'value': ['測試股票']
        })
        
        # 模擬新聞數據
        mock_news.return_value = mock_news_data
        
        # 模擬快訊數據
        mock_alerts.return_value = pd.DataFrame({
            '標題': ['測試股票發布重要公告', '行業利好消息'],
            '發布時間': [datetime.now(), datetime.now() - timedelta(hours=1)],
            '內容': ['公告內容1', '公告內容2']
        })
        
        # 模擬研究報告
        mock_report.return_value = pd.DataFrame({
            '標題': ['深度研究報告', '行業分析報告'],
            '發布時間': ['2024-01-01', '2024-01-02'],
            '機構': ['中信證券', '海通證券'],
            '分析師': ['張三', '李四'],
            '評級': ['買入', '增持'],
            '目標價': ['15.5', '16.0']
        })
        
        # 調用方法
        result = fetcher.fetch_comprehensive_news('000001', days=7)
        
        # 驗證結果結構
        assert result is not None
        assert 'stock_code' in result
        assert 'update_time' in result
        assert 'company_news' in result
        assert 'announcements' in result
        assert 'research_reports' in result
        assert 'market_sentiment' in result
        assert 'news_summary' in result
        
        # 驗證數據內容
        assert len(result['company_news']) > 0
        assert len(result['research_reports']) > 0
        
    def test_fetch_company_news(self, fetcher, mock_news_data):
        """測試獲取個股新聞"""
        with patch('akshare.stock_news_em') as mock_news:
            mock_news.return_value = mock_news_data
            
            # 調用方法
            result = fetcher._fetch_company_news('000001', days=7)
            
            # 驗證結果
            assert isinstance(result, list)
            assert len(result) == 5
            assert all('title' in item for item in result)
            assert all('time' in item for item in result)
            assert all('type' in item for item in result)
            
    def test_fetch_company_news_empty(self, fetcher):
        """測試獲取新聞無數據的情況"""
        with patch('akshare.stock_news_em') as mock_news:
            mock_news.return_value = pd.DataFrame()
            
            # 調用方法
            result = fetcher._fetch_company_news('000001', days=7)
            
            # 應該返回空列表
            assert result == []
            
    def test_fetch_announcements(self, fetcher):
        """測試獲取公司公告"""
        with patch('akshare.stock_zh_a_alerts_cls') as mock_alerts:
            with patch.object(fetcher, '_get_stock_name', return_value='測試股票'):
                # 模擬公告數據
                mock_alerts.return_value = pd.DataFrame({
                    '標題': [
                        '測試股票：重大資產重組公告',
                        '測試股票：季度報告',
                        '其他公司公告'
                    ],
                    '發布時間': [
                        datetime.now(),
                        datetime.now() - timedelta(hours=1),
                        datetime.now() - timedelta(hours=2)
                    ],
                    '內容': ['重組內容', '報告內容', '其他內容']
                })
                
                # 調用方法
                result = fetcher._fetch_announcements('000001', days=7)
                
                # 驗證結果
                assert isinstance(result, list)
                assert len(result) == 2  # 只有包含股票名稱的公告
                assert result[0]['importance'] == 'high'  # 重組公告為高重要性
                
    def test_fetch_research_reports(self, fetcher):
        """測試獲取研究報告"""
        with patch('akshare.stock_research_report_em') as mock_report:
            # 模擬研究報告數據
            mock_report.return_value = pd.DataFrame({
                '標題': ['深度研究：強烈推薦', '行業分析報告'],
                '發布時間': ['2024-01-01', '2024-01-02'],
                '機構': ['中信證券', '海通證券'],
                '分析師': ['張三', '李四'],
                '評級': ['買入', '增持'],
                '目標價': ['15.5', '16.0']
            })
            
            # 調用方法
            result = fetcher._fetch_research_reports('000001')
            
            # 驗證結果
            assert isinstance(result, list)
            assert len(result) == 2
            assert all('title' in item for item in result)
            assert all('rating' in item for item in result)
            
    def test_analyze_market_sentiment(self, fetcher):
        """測試市場情緒分析"""
        # 構建測試數據
        news_data = {
            'company_news': [
                {'title': '公司業績大幅增長，利潤創新高'},
                {'title': '獲得重要訂單，市場前景看好'},
                {'title': '面臨市場競爭加劇的風險'}
            ],
            'announcements': [
                {'title': '股權激勵計劃公告'},
                {'title': '重大合同簽署公告'}
            ],
            'research_reports': [
                {'rating': '買入'},
                {'rating': '買入'},
                {'rating': '增持'}
            ]
        }
        
        # 分析情緒
        result = fetcher._analyze_market_sentiment(news_data)
        
        # 驗證結果
        assert 'sentiment_score' in result
        assert 'news_heat' in result
        assert 'sentiment_keywords' in result
        assert 'research_ratings' in result
        
        # 情緒分數應該偏正面
        assert result['sentiment_score'] > 50
        
    def test_generate_news_summary(self, fetcher):
        """測試生成新聞摘要"""
        # 構建測試數據
        news_data = {
            'company_news': [
                {'title': '重要新聞1', 'time': '2024-01-01 10:00:00'},
                {'title': '重要新聞2', 'time': '2024-01-01 09:00:00'}
            ],
            'announcements': [
                {'title': '重大資產重組', 'time': '2024-01-01 08:00:00', 
                 'importance': 'high'}
            ],
            'market_sentiment': {
                'sentiment_score': 75,
                'research_ratings': {
                    '買入': 3,
                    '增持': 2
                }
            }
        }
        
        # 生成摘要
        result = fetcher._generate_news_summary(news_data)
        
        # 驗證結果
        assert 'latest_update' in result
        assert 'key_events' in result
        assert 'important_announcements' in result
        assert 'analyst_consensus' in result
        assert 'news_trend' in result
        
        # 驗證趨勢判斷
        assert result['news_trend'] == 'positive'
        
    def test_get_stock_name(self, fetcher):
        """測試獲取股票名稱"""
        with patch('akshare.stock_individual_info_em') as mock_info:
            # 模擬返回數據
            mock_info.return_value = pd.DataFrame({
                'item': ['股票簡稱', '股票代碼'],
                'value': ['平安銀行', '000001']
            })
            
            # 調用方法
            result = fetcher._get_stock_name('000001')
            
            # 驗證結果
            assert result == '平安銀行'
            
    def test_judge_announcement_importance(self, fetcher):
        """測試判斷公告重要性"""
        # 測試高重要性
        assert fetcher._judge_announcement_importance('關於重大資產重組的公告') == 'high'
        assert fetcher._judge_announcement_importance('業績預告') == 'high'
        assert fetcher._judge_announcement_importance('股權激勵計劃') == 'high'
        
        # 測試低重要性
        assert fetcher._judge_announcement_importance('股東大會會議通知') == 'low'
        assert fetcher._judge_announcement_importance('簡式權益變動報告') == 'low'
        
        # 測試普通重要性
        assert fetcher._judge_announcement_importance('普通公告') == 'normal'
        
    def test_news_cache_functionality(self, fetcher):
        """測試新聞緩存功能"""
        with patch('akshare.stock_news_em') as mock_news:
            with patch('akshare.stock_individual_info_em') as mock_info:
                # 模擬數據
                mock_news.return_value = pd.DataFrame({
                    '新聞標題': ['測試新聞'],
                    '發布時間': [datetime.now()],
                    '新聞來源': ['測試來源'],
                    '新聞內容': ['測試內容'],
                    '新聞鏈接': ['http://test.com']
                })
                
                mock_info.return_value = pd.DataFrame({
                    'item': ['股票簡稱'],
                    'value': ['測試股票']
                })
                
                # 第一次調用
                result1 = fetcher.fetch_comprehensive_news('000001', days=1)
                assert mock_news.call_count == 1
                
                # 第二次調用（應該從緩存獲取）
                result2 = fetcher.fetch_comprehensive_news('000001', days=1)
                assert mock_news.call_count == 1  # 不應該再次調用
                
                # 結果應該相同
                assert result1['company_news'] == result2['company_news']
                
    def test_error_handling(self, fetcher):
        """測試錯誤處理"""
        with patch('akshare.stock_news_em') as mock_news:
            # 模擬異常
            mock_news.side_effect = Exception("API Error")
            
            # 調用方法不應該拋出異常
            result = fetcher.fetch_comprehensive_news('000001', days=7)
            
            # 應該返回基本結構
            assert result is None or (result is not None and 'stock_code' in result)