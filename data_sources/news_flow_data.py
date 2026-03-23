"""
新闻流量数据获取模块
用于获取各大平台的热点新闻和流量数据
支持22个平台，包含排名、K值计算等功能
"""
import requests
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
import time
from collections import Counter

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class NewsFlowDataFetcher:
    """新闻流量数据获取器"""
    
    def __init__(self):
        self.base_url = "https://newsapi.ws4.cn/api/v1/dailynews/"
        self.timeout = 10
        
        # 支持的平台配置 - 扩展到22个平台
        self.platforms = {
            # 社交媒体平台（核心流量指标）- 8个
            'weibo': {'name': '微博热搜', 'category': 'social', 'weight': 10, 'influence': 'high'},
            'douyin': {'name': '抖音热点', 'category': 'social', 'weight': 9, 'influence': 'high'},
            'zhihu': {'name': '知乎热榜', 'category': 'social', 'weight': 7, 'influence': 'medium'},
            'bilibili': {'name': '哔哩哔哩', 'category': 'social', 'weight': 6, 'influence': 'medium'},
            'xiaohongshu': {'name': '小红书', 'category': 'social', 'weight': 7, 'influence': 'medium'},
            'kuaishou': {'name': '快手', 'category': 'social', 'weight': 6, 'influence': 'medium'},
            'tieba': {'name': '百度贴吧', 'category': 'social', 'weight': 5, 'influence': 'low'},
            'weixin': {'name': '微信热点', 'category': 'social', 'weight': 8, 'influence': 'high'},
            
            # 新闻媒体平台 - 6个
            'baidu': {'name': '百度热搜', 'category': 'news', 'weight': 8, 'influence': 'high'},
            'jinritoutiao': {'name': '今日头条', 'category': 'news', 'weight': 7, 'influence': 'high'},
            'tenxunwang': {'name': '腾讯网', 'category': 'news', 'weight': 6, 'influence': 'medium'},
            'netease': {'name': '网易新闻', 'category': 'news', 'weight': 6, 'influence': 'medium'},
            'ifeng': {'name': '凤凰网', 'category': 'news', 'weight': 5, 'influence': 'medium'},
            'sina': {'name': '新浪新闻', 'category': 'news', 'weight': 6, 'influence': 'medium'},
            
            # 财经平台（股市相关）- 5个
            'sina_finance': {'name': '新浪财经', 'category': 'finance', 'weight': 9, 'influence': 'high'},
            'eastmoney': {'name': '东方财富', 'category': 'finance', 'weight': 9, 'influence': 'high'},
            'xueqiu': {'name': '雪球', 'category': 'finance', 'weight': 8, 'influence': 'high'},
            'cls': {'name': '财联社', 'category': 'finance', 'weight': 8, 'influence': 'high'},
            'wallstreetcn': {'name': '华尔街见闻', 'category': 'finance', 'weight': 7, 'influence': 'medium'},
            
            # 科技平台 - 3个
            'tskr': {'name': '36氪', 'category': 'tech', 'weight': 6, 'influence': 'medium'},
            'sspai': {'name': '少数派', 'category': 'tech', 'weight': 5, 'influence': 'low'},
            'juejin': {'name': '掘金', 'category': 'tech', 'weight': 5, 'influence': 'low'},
        }
        
        # 平台类别权重（用于转化率计算）
        self.category_weights = {
            'finance': 1.5,    # 财经平台转化率高
            'social': 1.2,     # 社交媒体传播快
            'news': 1.0,       # 新闻媒体正常
            'tech': 0.8,       # 科技平台相关性低
        }
        
        # 停用词（过滤无意义的词）
        self.stop_words = {
            '的', '是', '在', '了', '和', '与', '等', '为', '将', '被',
            '有', '一', '个', '上', '下', '中', '大', '新', '年', '月', '日',
            '这', '那', '其', '之', '也', '要', '就', '不', '我', '你', '他',
            '来', '去', '到', '说', '会', '能', '都', '对', '着', '让',
            '从', '以', '及', '或', '如', '还', '没', '很', '更', '最',
        }
    
    def get_platform_news(self, platform: str) -> Dict:
        """
        获取单个平台的新闻数据
        
        Args:
            platform: 平台代码（如 'weibo', 'baidu'等）
            
        Returns:
            {
                'success': bool,
                'platform': str,
                'platform_name': str,
                'category': str,
                'weight': int,
                'influence': str,
                'data': List[Dict],
                'count': int,
                'fetch_time': str,
                'error': str (如果失败)
            }
        """
        try:
            url = f"{self.base_url}?platform={platform}"
            
            logger.info(f"正在获取 {platform} 平台数据...")
            response = requests.get(url, timeout=self.timeout)
            response.raise_for_status()
            
            data = response.json()
            
            if data.get('status') == '200':
                news_list = data.get('data', [])
                platform_info = self.platforms.get(platform, {})
                
                # 为每条新闻添加排名信息
                for i, news in enumerate(news_list):
                    news['rank'] = i + 1
                    news['platform'] = platform
                
                return {
                    'success': True,
                    'platform': platform,
                    'platform_name': platform_info.get('name', platform),
                    'category': platform_info.get('category', 'other'),
                    'weight': platform_info.get('weight', 5),
                    'influence': platform_info.get('influence', 'medium'),
                    'data': news_list,
                    'count': len(news_list),
                    'fetch_time': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                }
            else:
                return {
                    'success': False,
                    'platform': platform,
                    'error': f"API返回错误: {data.get('msg', '未知错误')}"
                }
                
        except requests.exceptions.Timeout:
            return {
                'success': False,
                'platform': platform,
                'error': f"请求超时（{self.timeout}秒）"
            }
        except requests.exceptions.ConnectionError:
            return {
                'success': False,
                'platform': platform,
                'error': "网络连接失败"
            }
        except Exception as e:
            return {
                'success': False,
                'platform': platform,
                'error': f"获取数据失败: {str(e)}"
            }
    
    def get_multi_platform_news(self, platforms: List[str] = None, 
                                 category: str = None) -> Dict:
        """
        获取多个平台的新闻数据
        
        Args:
            platforms: 平台列表，None表示获取所有
            category: 按类别筛选（'social', 'news', 'finance', 'tech'）
            
        Returns:
            {
                'success': bool,
                'total_platforms': int,
                'success_count': int,
                'failed_count': int,
                'platforms_data': List[Dict],
                'fetch_time': str
            }
        """
        # 确定要获取的平台列表
        if platforms is None:
            if category:
                target_platforms = [
                    p for p, info in self.platforms.items() 
                    if info.get('category') == category
                ]
            else:
                target_platforms = list(self.platforms.keys())
        else:
            target_platforms = platforms
        
        results = []
        success_count = 0
        failed_count = 0
        
        for platform in target_platforms:
            result = self.get_platform_news(platform)
            results.append(result)
            
            if result['success']:
                success_count += 1
            else:
                failed_count += 1
            
            # 避免请求过快，休息0.3秒
            time.sleep(0.3)
        
        return {
            'success': success_count > 0,
            'total_platforms': len(target_platforms),
            'success_count': success_count,
            'failed_count': failed_count,
            'platforms_data': results,
            'fetch_time': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
        }
    
    def extract_stock_related_news(self, platforms_data: List[Dict], 
                                    keywords: List[str] = None) -> List[Dict]:
        """
        从新闻数据中提取股票相关的新闻
        
        Args:
            platforms_data: 平台数据列表
            keywords: 股票相关关键词列表
            
        Returns:
            List[Dict]: 股票相关新闻列表
        """
        if keywords is None:
            keywords = [
                # 股市基础词汇
                '股', '股市', '股票', 'A股', '港股', '美股', '创业板', '科创板', '北交所',
                '涨停', '跌停', '大涨', '暴涨', '飙升', '暴跌', '涨幅', '跌幅', '翻倍',
                '概念股', '龙头股', '妖股', '题材股', '白马股', '蓝筹股', '成长股',
                '上市', 'IPO', '重组', '并购', '收购', '增发', '回购', '减持', '增持',
                '业绩', '财报', '利好', '利空', '预增', '预减', '盈利', '亏损',
                '牛市', '熊市', '反弹', '回调', '震荡', '突破', '新高',
                '主力', '游资', '北向资金', '外资', '机构', '资金流入', '资金流出',
                '板块', '行业', '赛道', '题材', '轮动', '热点',
                
                # 热门板块关键词
                '芯片', '半导体', '光刻机', '封装', '存储',
                '新能源', '锂电', '光伏', '储能', '风电', '氢能',
                'AI', '人工智能', '大模型', 'ChatGPT', 'DeepSeek', '算力', 'GPU',
                '机器人', '人形机器人', '工业机器人', '减速器', '伺服电机',
                '低空经济', '无人机', 'eVTOL', '飞行汽车',
                '数据要素', '数字经济', '信创', '国产替代',
                '医药', '创新药', 'CXO', '医疗器械', '中药',
                '消费', '白酒', '食品', '旅游', '免税',
                '军工', '国防', '航空', '航天', '船舶',
                '汽车', '新能源车', '智能驾驶', '无人驾驶', '充电桩',
                '地产', '房地产', '楼市', '房价',
                '金融', '银行', '保险', '券商', '证券',
                
                # 政策相关
                '政策', '利率', '降息', '降准', '货币政策', '财政政策',
                '国常会', '证监会', '央行', '发改委', '工信部',
            ]
        
        stock_related = []
        
        for platform_data in platforms_data:
            if not platform_data.get('success'):
                continue
            
            platform = platform_data['platform']
            platform_name = platform_data['platform_name']
            category = platform_data['category']
            weight = platform_data['weight']
            influence = platform_data.get('influence', 'medium')
            
            for news in platform_data.get('data', []):
                title = news.get('title') or ''
                content = news.get('content') or ''
                rank = news.get('rank', 99)
                
                # 检查是否包含股票关键词
                text = f"{title} {content}"
                matched_keywords = [kw for kw in keywords if kw in text]
                
                if matched_keywords:
                    # 计算综合得分（排名越靠前、权重越高得分越高）
                    rank_score = max(0, 100 - rank * 2)  # 排名1得98分，排名50得0分
                    weight_score = weight * 10
                    keyword_score = len(matched_keywords) * 5
                    total_score = rank_score + weight_score + keyword_score
                    
                    stock_related.append({
                        'platform': platform,
                        'platform_name': platform_name,
                        'category': category,
                        'weight': weight,
                        'influence': influence,
                        'rank': rank,
                        'title': title,
                        'content': content,
                        'url': news.get('url') or '',
                        'source': news.get('source') or platform_name,
                        'publish_time': news.get('publish_time') or '',
                        'matched_keywords': matched_keywords,
                        'keyword_count': len(matched_keywords),
                        'score': total_score,
                    })
        
        # 按综合得分排序
        stock_related.sort(key=lambda x: x['score'], reverse=True)
        
        return stock_related
    
    def calculate_flow_score(self, platforms_data: List[Dict]) -> Dict:
        """
        计算流量得分
        
        根据"流量为王"理念，评估当前市场热度
        
        Returns:
            {
                'total_score': int,  # 总流量得分（0-1000）
                'social_score': int,  # 社交媒体流量得分
                'news_score': int,  # 新闻媒体流量得分
                'finance_score': int,  # 财经平台流量得分
                'tech_score': int,  # 科技平台流量得分
                'level': str,  # 流量等级（低/中/高/极高）
                'analysis': str,  # 流量分析
                'platform_details': List[Dict],  # 各平台详情
            }
        """
        scores = {
            'social': 0,
            'news': 0,
            'finance': 0,
            'tech': 0,
        }
        
        platform_details = []
        
        for platform_data in platforms_data:
            if not platform_data.get('success'):
                continue
            
            category = platform_data['category']
            weight = platform_data['weight']
            count = platform_data['count']
            platform_name = platform_data['platform_name']
            
            # 计算得分：权重 × 新闻数量
            score = weight * count
            scores[category] = scores.get(category, 0) + score
            
            platform_details.append({
                'platform': platform_data['platform'],
                'platform_name': platform_name,
                'category': category,
                'count': count,
                'score': score,
            })
        
        # 计算总分
        total_score = sum(scores.values())
        
        # 归一化到0-1000
        if total_score > 0:
            normalized_score = min(int(total_score / 50), 1000)
        else:
            normalized_score = 0
        
        # 确定流量等级
        if normalized_score >= 800:
            level = "极高"
            analysis = "流量爆发！市场情绪极度活跃，大量新闻热点，存在热点题材炒作机会。建议：密切关注龙头股，注意追高风险。"
        elif normalized_score >= 500:
            level = "高"
            analysis = "流量较高。市场有明确热点，资金活跃度较好。建议：关注热点板块，注意节奏把握。"
        elif normalized_score >= 200:
            level = "中"
            analysis = "流量正常。市场处于常态，有一定热点但不突出。建议：观望为主，等待明确信号。"
        else:
            level = "低"
            analysis = "流量较低。市场情绪低迷，缺乏热点。建议：控制仓位，等待市场转暖。"
        
        return {
            'total_score': normalized_score,
            'social_score': scores.get('social', 0),
            'news_score': scores.get('news', 0),
            'finance_score': scores.get('finance', 0),
            'tech_score': scores.get('tech', 0),
            'level': level,
            'analysis': analysis,
            'platform_details': platform_details,
        }
    
    def get_hot_topics(self, platforms_data: List[Dict], top_n: int = 20) -> List[Dict]:
        """
        获取热门话题（基于标题词频分析）
        
        Returns:
            List[Dict]: 热门话题列表
        """
        import jieba
        
        # 收集所有标题及其来源信息
        all_titles = []
        title_sources = {}  # 记录每个标题来自哪些平台
        
        for platform_data in platforms_data:
            if platform_data.get('success'):
                platform_name = platform_data['platform_name']
                for news in platform_data.get('data', []):
                    title = news.get('title') or ''
                    if title:
                        all_titles.append(title)
                        if title not in title_sources:
                            title_sources[title] = []
                        title_sources[title].append(platform_name)
        
        # 分词并统计
        word_counter = Counter()
        word_sources = {}  # 记录每个词出现在哪些平台
        
        for title in all_titles:
            if title:
                words = jieba.cut(title)
                for word in words:
                    if len(word) >= 2 and word not in self.stop_words:
                        word_counter[word] += 1
                        if word not in word_sources:
                            word_sources[word] = set()
                        for source in title_sources.get(title, []):
                            word_sources[word].add(source)
        
        # 获取TOP N
        hot_topics = []
        total_titles = len(all_titles) if all_titles else 1
        
        for word, count in word_counter.most_common(top_n):
            sources = list(word_sources.get(word, []))
            cross_platform = len(sources)  # 跨平台数
            heat = min(int(count / total_titles * 1000), 100)
            
            # 跨平台加成
            if cross_platform >= 5:
                heat = min(heat + 20, 100)
            elif cross_platform >= 3:
                heat = min(heat + 10, 100)
            
            hot_topics.append({
                'topic': word,
                'count': count,
                'heat': heat,
                'cross_platform': cross_platform,
                'sources': sources[:5],  # 最多显示5个来源
            })
        
        return hot_topics
    
    def get_platform_ranking(self, platforms_data: List[Dict]) -> List[Dict]:
        """
        获取跨平台热度排名
        
        合并所有平台的新闻，按热度排序
        
        Returns:
            List[Dict]: 排名列表
        """
        all_news = []
        
        for platform_data in platforms_data:
            if not platform_data.get('success'):
                continue
            
            platform = platform_data['platform']
            platform_name = platform_data['platform_name']
            weight = platform_data['weight']
            
            for news in platform_data.get('data', []):
                title = news.get('title') or ''
                rank = news.get('rank', 99)
                
                if not title:
                    continue
                
                # 计算综合热度分数
                # 排名越靠前分数越高，平台权重越高分数越高
                heat_score = (100 - rank) * weight
                
                all_news.append({
                    'title': title,
                    'platform': platform,
                    'platform_name': platform_name,
                    'original_rank': rank,
                    'heat_score': heat_score,
                    'url': news.get('url') or '',
                    'content': news.get('content') or '',
                })
        
        # 按热度分数排序
        all_news.sort(key=lambda x: x['heat_score'], reverse=True)
        
        # 添加全局排名
        for i, news in enumerate(all_news):
            news['global_rank'] = i + 1
        
        return all_news
    
    def calculate_viral_coefficient(self, current_data: Dict, 
                                     previous_data: Dict) -> Dict:
        """
        计算病毒系数K值
        
        K值 = 当前传播量 / 上期传播量
        
        Args:
            current_data: 当前数据
            previous_data: 上期数据
            
        Returns:
            {
                'k_value': float,  # K值
                'trend': str,  # 趋势（指数型/线性/衰减）
                'analysis': str,  # 分析
            }
        """
        current_score = current_data.get('total_score', 0)
        previous_score = previous_data.get('total_score', 0)
        
        if previous_score == 0:
            k_value = 1.0
            trend = "无历史数据"
            analysis = "首次采集，无法计算K值"
        else:
            k_value = round(current_score / previous_score, 2)
            
            if k_value > 1.5:
                trend = "指数型爆发"
                analysis = f"K值={k_value}，流量正在指数型增长！这是病毒式传播的特征，题材可能进入加速期。"
            elif k_value > 1.0:
                trend = "线性增长"
                analysis = f"K值={k_value}，流量稳步增长，题材正在发酵中。"
            elif k_value == 1.0:
                trend = "平稳"
                analysis = f"K值={k_value}，流量保持稳定，市场处于平衡状态。"
            else:
                trend = "衰减"
                analysis = f"K值={k_value}，流量正在衰减，题材热度下降，注意风险。"
        
        return {
            'k_value': k_value,
            'current_score': current_score,
            'previous_score': previous_score,
            'trend': trend,
            'analysis': analysis,
        }
    
    def detect_flow_type(self, history_scores: List[int], 
                          current_score: int) -> Dict:
        """
        识别流量类型（存量流量型 vs 增量流量型）
        
        存量流量型：出生自带顶流，流量快速到位（政策/大事件）
        增量流量型：初始流量小，具备病毒传播能力（话题发酵）
        
        Args:
            history_scores: 历史得分列表（从旧到新）
            current_score: 当前得分
            
        Returns:
            {
                'flow_type': str,  # 存量流量型/增量流量型/未知
                'characteristics': List[str],  # 特征
                'time_window': str,  # 时间窗口建议
                'operation': str,  # 操作建议
            }
        """
        if len(history_scores) < 2:
            return {
                'flow_type': '未知',
                'characteristics': ['历史数据不足'],
                'time_window': '无法判断',
                'operation': '继续观察',
            }
        
        # 计算初始得分和增长率
        initial_score = history_scores[0] if history_scores else 0
        avg_score = sum(history_scores) / len(history_scores)
        
        # 计算增长趋势
        growth_rates = []
        for i in range(1, len(history_scores)):
            if history_scores[i-1] > 0:
                rate = (history_scores[i] - history_scores[i-1]) / history_scores[i-1]
                growth_rates.append(rate)
        
        avg_growth = sum(growth_rates) / len(growth_rates) if growth_rates else 0
        
        # 判断流量类型
        if initial_score >= 500:
            # 初始热度高 -> 存量流量型
            flow_type = "存量流量型"
            characteristics = [
                "初始热度高",
                "流量快速到位",
                "可能与政策/大事件相关",
            ]
            time_window = "时间窗口短（2-3天）"
            operation = "快进快出，密切关注热度变化"
        elif avg_growth > 0.2 and len([r for r in growth_rates if r > 0]) >= 2:
            # 持续增长 -> 增量流量型
            flow_type = "增量流量型"
            characteristics = [
                "初始热度低",
                "逐步攀升",
                "具备病毒传播特征",
            ]
            time_window = "时间窗口长（5-10天）"
            operation = "可以埋伏，等待加速"
        else:
            flow_type = "常规流量"
            characteristics = [
                "热度波动正常",
                "无明显趋势",
            ]
            time_window = "无特定窗口"
            operation = "保持观望"
        
        return {
            'flow_type': flow_type,
            'characteristics': characteristics,
            'time_window': time_window,
            'operation': operation,
            'initial_score': initial_score,
            'current_score': current_score,
            'avg_growth': round(avg_growth * 100, 1),  # 百分比
        }
    
    def get_platform_list(self) -> List[Dict]:
        """
        获取所有支持的平台列表
        
        Returns:
            List[Dict]: 平台列表
        """
        result = []
        for code, info in self.platforms.items():
            result.append({
                'code': code,
                'name': info['name'],
                'category': info['category'],
                'weight': info['weight'],
                'influence': info.get('influence', 'medium'),
            })
        
        # 按权重排序
        result.sort(key=lambda x: x['weight'], reverse=True)
        return result
    
    def get_platforms_by_category(self) -> Dict[str, List[str]]:
        """
        按类别获取平台列表
        
        Returns:
            Dict[str, List[str]]: 类别 -> 平台代码列表
        """
        categories = {}
        for code, info in self.platforms.items():
            category = info['category']
            if category not in categories:
                categories[category] = []
            categories[category].append(code)
        return categories


# 测试代码
if __name__ == "__main__":
    fetcher = NewsFlowDataFetcher()
    
    # 测试获取平台列表
    print("=== 支持的平台列表 ===")
    platforms = fetcher.get_platform_list()
    print(f"共支持 {len(platforms)} 个平台：")
    for p in platforms[:5]:
        print(f"  - {p['name']} ({p['code']}) - 权重:{p['weight']}")
    
    # 测试获取单个平台
    print("\n=== 测试获取微博热搜 ===")
    result = fetcher.get_platform_news('weibo')
    if result['success']:
        print(f"✅ 成功获取 {result['count']} 条新闻")
        print(f"前3条标题：")
        for news in result['data'][:3]:
            print(f"  {news['rank']}. {news['title']}")
    else:
        print(f"❌ 失败: {result['error']}")
    
    print("\n=== 测试获取财经平台 ===")
    result = fetcher.get_multi_platform_news(category='finance')
    print(f"总共 {result['total_platforms']} 个平台")
    print(f"成功 {result['success_count']} 个")
    print(f"失败 {result['failed_count']} 个")
    
    # 提取股票相关新闻
    stock_news = fetcher.extract_stock_related_news(result['platforms_data'])
    print(f"\n✅ 提取到 {len(stock_news)} 条股票相关新闻")
    
    # 计算流量得分
    flow_score = fetcher.calculate_flow_score(result['platforms_data'])
    print(f"\n流量得分: {flow_score['total_score']}")
    print(f"流量等级: {flow_score['level']}")
    
    # 获取热门话题
    hot_topics = fetcher.get_hot_topics(result['platforms_data'])
    print(f"\n热门话题TOP5:")
    for i, topic in enumerate(hot_topics[:5], 1):
        print(f"  {i}. {topic['topic']} (热度:{topic['heat']}, 跨{topic['cross_platform']}平台)")
