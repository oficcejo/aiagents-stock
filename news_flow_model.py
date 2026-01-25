"""
新闻流量模型计算模块
核心公式：接盘总量 = 流量 × 转化率 × 客单价
实现流量为王理念的量化分析
"""
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class NewsFlowModel:
    """新闻流量模型计算器"""
    
    def __init__(self):
        # 平台类别权重（用于转化率计算）
        self.category_weights = {
            'finance': 1.5,    # 财经平台转化率高
            'social': 1.2,     # 社交媒体传播快
            'news': 1.0,       # 新闻媒体正常
            'tech': 0.8,       # 科技平台相关性低
        }
        
        # 话题类型转化率系数
        self.topic_weights = {
            # 高转化话题
            '政策': 2.0,
            '利好': 1.8,
            '涨停': 1.8,
            '龙头': 1.7,
            '机构': 1.6,
            '外资': 1.6,
            '北向': 1.6,
            '重组': 1.5,
            '并购': 1.5,
            'IPO': 1.5,
            
            # 中转化话题
            '业绩': 1.3,
            '财报': 1.3,
            '板块': 1.2,
            '概念': 1.2,
            '题材': 1.2,
            
            # 一般话题
            '股票': 1.0,
            '股市': 1.0,
            'A股': 1.0,
        }
        
        # 基础转化率（万分之一）
        self.base_conversion_rate = 0.0001
        
        # 平均客单价（元）- 散户平均投资金额
        self.avg_investment = 50000
        
        # 时效因子衰减系数（每小时衰减）
        self.time_decay_rate = 0.95
    
    def calculate_traffic_score(self, platforms_data: List[Dict]) -> Dict:
        """
        计算流量分数
        
        流量分数 = Σ(平台权重 × 热度 × 时效因子)
        
        Args:
            platforms_data: 平台数据列表
            
        Returns:
            {
                'total_score': int,
                'category_scores': Dict[str, int],
                'platform_details': List[Dict],
                'normalized_score': int,  # 归一化到0-1000
            }
        """
        category_scores = {
            'social': 0,
            'news': 0,
            'finance': 0,
            'tech': 0,
        }
        
        platform_details = []
        total_raw_score = 0
        
        for platform_data in platforms_data:
            if not platform_data.get('success'):
                continue
            
            category = platform_data.get('category', 'other')
            weight = platform_data.get('weight', 5)
            count = platform_data.get('count', 0)
            platform_name = platform_data.get('platform_name', '')
            
            # 计算平台得分：权重 × 新闻数量 × 类别权重
            category_weight = self.category_weights.get(category, 1.0)
            platform_score = weight * count * category_weight
            
            category_scores[category] = category_scores.get(category, 0) + platform_score
            total_raw_score += platform_score
            
            platform_details.append({
                'platform': platform_data.get('platform', ''),
                'platform_name': platform_name,
                'category': category,
                'count': count,
                'weight': weight,
                'score': int(platform_score),
            })
        
        # 归一化到0-1000
        normalized_score = min(int(total_raw_score / 50), 1000)
        
        return {
            'total_score': int(total_raw_score),
            'normalized_score': normalized_score,
            'category_scores': {k: int(v) for k, v in category_scores.items()},
            'platform_details': platform_details,
        }
    
    def estimate_conversion_rate(self, hot_topics: List[Dict], 
                                  category_distribution: Dict[str, int]) -> Dict:
        """
        估算转化率
        
        转化率 = 基础转化率 × 话题系数 × 平台系数
        
        Args:
            hot_topics: 热门话题列表
            category_distribution: 类别得分分布
            
        Returns:
            {
                'conversion_rate': float,
                'topic_factor': float,
                'platform_factor': float,
                'analysis': str,
            }
        """
        # 1. 计算话题系数（基于热门话题的类型）
        topic_factor = 1.0
        matched_topics = []
        
        for topic in hot_topics[:10]:  # 只看TOP10热门话题
            topic_text = topic.get('topic', '')
            topic_heat = topic.get('heat', 0)
            
            for keyword, weight in self.topic_weights.items():
                if keyword in topic_text:
                    # 热度加权
                    heat_bonus = 1 + (topic_heat / 100) * 0.5
                    topic_factor = max(topic_factor, weight * heat_bonus)
                    matched_topics.append({
                        'topic': topic_text,
                        'keyword': keyword,
                        'factor': weight,
                    })
                    break
        
        # 2. 计算平台系数（基于类别分布）
        total_score = sum(category_distribution.values())
        if total_score > 0:
            platform_factor = sum(
                (score / total_score) * self.category_weights.get(cat, 1.0)
                for cat, score in category_distribution.items()
            )
        else:
            platform_factor = 1.0
        
        # 3. 计算最终转化率
        conversion_rate = self.base_conversion_rate * topic_factor * platform_factor
        
        # 4. 生成分析
        if conversion_rate >= 0.0003:
            analysis = f"转化率极高({conversion_rate:.4%})！话题与股市高度相关，投资者关注度极高。"
        elif conversion_rate >= 0.0002:
            analysis = f"转化率较高({conversion_rate:.4%})。话题具有较强的股市联动性。"
        elif conversion_rate >= 0.0001:
            analysis = f"转化率正常({conversion_rate:.4%})。话题与股市有一定关联。"
        else:
            analysis = f"转化率较低({conversion_rate:.4%})。话题与股市关联度不高。"
        
        return {
            'conversion_rate': conversion_rate,
            'topic_factor': round(topic_factor, 2),
            'platform_factor': round(platform_factor, 2),
            'matched_topics': matched_topics,
            'analysis': analysis,
        }
    
    def calculate_potential(self, flow_score: int, conversion_rate: float,
                            avg_investment: float = None) -> Dict:
        """
        计算接盘潜力
        
        核心公式：接盘总量 = 流量 × 转化率 × 客单价
        
        Args:
            flow_score: 流量分数（代表潜在触达人数，按比例换算）
            conversion_rate: 转化率
            avg_investment: 平均客单价（元）
            
        Returns:
            {
                'potential_volume': float,  # 接盘总量（亿元）
                'potential_level': str,  # 潜力等级
                'estimated_participants': int,  # 预估参与人数
                'analysis': str,
            }
        """
        if avg_investment is None:
            avg_investment = self.avg_investment
        
        # 流量分数换算为潜在触达人数（假设满分1000对应1000万人）
        potential_reach = flow_score * 10000  # 分数 × 10000 = 潜在触达人数
        
        # 预估参与人数
        estimated_participants = int(potential_reach * conversion_rate)
        
        # 接盘总量 = 参与人数 × 平均投资额（转换为亿元）
        potential_volume = (estimated_participants * avg_investment) / 100000000
        
        # 确定潜力等级
        if potential_volume >= 100:
            potential_level = "超大"
            analysis = f"预估接盘资金{potential_volume:.1f}亿元，市场资金充裕，热点题材可能持续发酵。"
        elif potential_volume >= 50:
            potential_level = "大"
            analysis = f"预估接盘资金{potential_volume:.1f}亿元，资金量较大，可支撑短期行情。"
        elif potential_volume >= 20:
            potential_level = "中"
            analysis = f"预估接盘资金{potential_volume:.1f}亿元，资金量适中，行情可能分化。"
        elif potential_volume >= 5:
            potential_level = "小"
            analysis = f"预估接盘资金{potential_volume:.1f}亿元，资金量较小，注意风险。"
        else:
            potential_level = "极小"
            analysis = f"预估接盘资金{potential_volume:.1f}亿元，资金量不足，不建议追高。"
        
        return {
            'potential_volume': round(potential_volume, 2),
            'potential_level': potential_level,
            'potential_reach': potential_reach,
            'estimated_participants': estimated_participants,
            'avg_investment': avg_investment,
            'analysis': analysis,
        }
    
    def classify_flow_type(self, history_scores: List[int], 
                           current_score: int) -> Dict:
        """
        判断流量类型
        
        存量流量型：出生自带顶流，流量快速到位（政策/大事件）
        增量流量型：初始流量小，具备病毒传播能力（话题发酵）
        
        Args:
            history_scores: 历史得分列表（从旧到新）
            current_score: 当前得分
            
        Returns:
            {
                'flow_type': str,
                'characteristics': List[str],
                'time_window': str,
                'operation': str,
                'confidence': int,
            }
        """
        if len(history_scores) < 2:
            return {
                'flow_type': '未知',
                'characteristics': ['历史数据不足，无法判断'],
                'time_window': '无法判断',
                'operation': '继续观察，积累数据',
                'confidence': 0,
            }
        
        # 计算关键指标
        initial_score = history_scores[0]
        avg_score = sum(history_scores) / len(history_scores)
        max_score = max(history_scores)
        
        # 计算增长率序列
        growth_rates = []
        for i in range(1, len(history_scores)):
            if history_scores[i-1] > 0:
                rate = (history_scores[i] - history_scores[i-1]) / history_scores[i-1]
                growth_rates.append(rate)
        
        avg_growth = sum(growth_rates) / len(growth_rates) if growth_rates else 0
        positive_growth_count = len([r for r in growth_rates if r > 0])
        
        # 判断流量类型
        if initial_score >= 500 and (current_score - initial_score) / (initial_score + 1) < 0.3:
            # 初始热度高，增长有限 -> 存量流量型
            flow_type = "存量流量型"
            characteristics = [
                f"初始热度高（{initial_score}分）",
                "流量快速到位",
                "可能与政策/大事件相关",
                "来得快去得也快",
            ]
            time_window = "时间窗口短（2-3天）"
            operation = "快进快出，首日参与最佳，及时止盈"
            confidence = 80
            
        elif avg_growth > 0.15 and positive_growth_count >= len(growth_rates) * 0.6:
            # 持续增长 -> 增量流量型
            flow_type = "增量流量型"
            characteristics = [
                f"初始热度较低（{initial_score}分）",
                f"增长率{avg_growth*100:.1f}%",
                "逐步攀升，病毒式传播",
                "有埋伏机会",
            ]
            time_window = "时间窗口长（5-10天）"
            operation = "可以埋伏，等待加速，分批建仓"
            confidence = 75
            
        elif avg_growth < -0.1:
            # 持续下降 -> 衰退期
            flow_type = "流量衰退"
            characteristics = [
                "热度持续下降",
                f"平均跌幅{abs(avg_growth)*100:.1f}%",
                "题材热度消退",
            ]
            time_window = "窗口已关闭"
            operation = "及时止盈止损，不宜追入"
            confidence = 70
            
        else:
            # 波动 -> 常规流量
            flow_type = "常规流量"
            characteristics = [
                "热度波动正常",
                "无明显趋势",
            ]
            time_window = "无特定窗口"
            operation = "保持观望，等待方向明确"
            confidence = 50
        
        return {
            'flow_type': flow_type,
            'characteristics': characteristics,
            'time_window': time_window,
            'operation': operation,
            'confidence': confidence,
            'initial_score': initial_score,
            'current_score': current_score,
            'avg_growth': round(avg_growth * 100, 1),
            'history_length': len(history_scores),
        }
    
    def calculate_viral_k(self, current_score: int, previous_score: int) -> Dict:
        """
        计算病毒系数K值
        
        K值 = 当前传播量 / 上期传播量
        
        K > 1.5: 指数型爆发
        K ≈ 1: 线性增长
        K < 1: 自然死亡
        
        Returns:
            {
                'k_value': float,
                'trend': str,
                'risk_level': str,
                'analysis': str,
            }
        """
        if previous_score == 0:
            return {
                'k_value': 1.0,
                'trend': '无历史数据',
                'risk_level': '未知',
                'analysis': '首次采集，无法计算K值',
            }
        
        k_value = round(current_score / previous_score, 2)
        
        if k_value > 2.0:
            trend = "爆发式增长"
            risk_level = "高风险"
            analysis = f"K值={k_value}，流量正在爆发式增长！这是极端情况，可能接近顶部，注意风险。"
        elif k_value > 1.5:
            trend = "指数型爆发"
            risk_level = "中高风险"
            analysis = f"K值={k_value}，流量指数型增长！题材正在加速发酵，关注龙头但注意追高风险。"
        elif k_value > 1.2:
            trend = "快速增长"
            risk_level = "中风险"
            analysis = f"K值={k_value}，流量快速增长，题材正在升温，可适度参与。"
        elif k_value > 1.0:
            trend = "稳步增长"
            risk_level = "低风险"
            analysis = f"K值={k_value}，流量稳步增长，题材处于发酵期。"
        elif k_value == 1.0:
            trend = "平稳"
            risk_level = "低风险"
            analysis = f"K值={k_value}，流量保持稳定，市场平衡状态。"
        elif k_value > 0.8:
            trend = "轻微下降"
            risk_level = "中风险"
            analysis = f"K值={k_value}，流量轻微下降，题材热度开始消退。"
        else:
            trend = "快速衰减"
            risk_level = "高风险"
            analysis = f"K值={k_value}，流量快速衰减！题材进入退潮期，注意及时止盈止损。"
        
        return {
            'k_value': k_value,
            'current_score': current_score,
            'previous_score': previous_score,
            'trend': trend,
            'risk_level': risk_level,
            'analysis': analysis,
        }
    
    def run_full_model(self, platforms_data: List[Dict], 
                       hot_topics: List[Dict],
                       history_scores: List[int] = None) -> Dict:
        """
        运行完整的流量模型分析
        
        Returns:
            {
                'traffic': Dict,  # 流量分析
                'conversion': Dict,  # 转化率分析
                'potential': Dict,  # 接盘潜力
                'flow_type': Dict,  # 流量类型
                'viral_k': Dict,  # K值分析
                'summary': str,  # 总结
            }
        """
        # 1. 计算流量分数
        traffic = self.calculate_traffic_score(platforms_data)
        current_score = traffic['normalized_score']
        
        # 2. 估算转化率
        conversion = self.estimate_conversion_rate(
            hot_topics, 
            traffic['category_scores']
        )
        
        # 3. 计算接盘潜力
        potential = self.calculate_potential(
            current_score,
            conversion['conversion_rate']
        )
        
        # 4. 判断流量类型
        if history_scores and len(history_scores) >= 2:
            flow_type = self.classify_flow_type(history_scores, current_score)
            # 计算K值（与上一次对比）
            viral_k = self.calculate_viral_k(current_score, history_scores[-1])
        else:
            flow_type = {
                'flow_type': '未知',
                'characteristics': ['历史数据不足'],
                'time_window': '无法判断',
                'operation': '继续观察',
                'confidence': 0,
            }
            viral_k = {
                'k_value': 1.0,
                'trend': '无历史数据',
                'risk_level': '未知',
                'analysis': '首次分析，无法计算K值',
            }
        
        # 5. 生成总结
        summary = self._generate_summary(traffic, conversion, potential, flow_type, viral_k)
        
        return {
            'traffic': traffic,
            'conversion': conversion,
            'potential': potential,
            'flow_type': flow_type,
            'viral_k': viral_k,
            'summary': summary,
            'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
        }
    
    def _generate_summary(self, traffic: Dict, conversion: Dict, 
                          potential: Dict, flow_type: Dict, viral_k: Dict) -> str:
        """生成分析总结"""
        lines = []
        
        # 流量概况
        score = traffic['normalized_score']
        if score >= 800:
            lines.append(f"【流量】当前流量分数{score}，处于极高水平")
        elif score >= 500:
            lines.append(f"【流量】当前流量分数{score}，处于较高水平")
        elif score >= 200:
            lines.append(f"【流量】当前流量分数{score}，处于正常水平")
        else:
            lines.append(f"【流量】当前流量分数{score}，处于低位")
        
        # 转化率
        lines.append(f"【转化】{conversion['analysis']}")
        
        # 接盘潜力
        lines.append(f"【潜力】{potential['analysis']}")
        
        # 流量类型
        if flow_type['flow_type'] != '未知':
            lines.append(f"【类型】{flow_type['flow_type']}，{flow_type['operation']}")
        
        # K值
        if viral_k['k_value'] != 1.0 or viral_k['trend'] != '无历史数据':
            lines.append(f"【趋势】K值={viral_k['k_value']}，{viral_k['trend']}")
        
        return '\n'.join(lines)


# 全局实例
news_flow_model = NewsFlowModel()


# 测试代码
if __name__ == "__main__":
    print("=== 测试新闻流量模型 ===")
    
    # 模拟数据
    platforms_data = [
        {'success': True, 'platform': 'weibo', 'platform_name': '微博',
         'category': 'social', 'weight': 10, 'count': 50},
        {'success': True, 'platform': 'eastmoney', 'platform_name': '东方财富',
         'category': 'finance', 'weight': 9, 'count': 30},
        {'success': True, 'platform': 'baidu', 'platform_name': '百度',
         'category': 'news', 'weight': 8, 'count': 40},
    ]
    
    hot_topics = [
        {'topic': 'AI芯片', 'heat': 95, 'count': 50},
        {'topic': '新能源政策', 'heat': 80, 'count': 30},
        {'topic': '涨停板', 'heat': 75, 'count': 25},
    ]
    
    history_scores = [300, 350, 420, 500]
    
    # 运行完整分析
    result = news_flow_model.run_full_model(platforms_data, hot_topics, history_scores)
    
    print(f"\n流量分数: {result['traffic']['normalized_score']}")
    print(f"转化率: {result['conversion']['conversion_rate']:.4%}")
    print(f"接盘潜力: {result['potential']['potential_volume']:.1f}亿元 ({result['potential']['potential_level']})")
    print(f"流量类型: {result['flow_type']['flow_type']}")
    print(f"K值: {result['viral_k']['k_value']} ({result['viral_k']['trend']})")
    print(f"\n===总结===\n{result['summary']}")
