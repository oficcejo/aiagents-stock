"""
新闻流量情绪分析模块
实现情绪指数、情绪分类、流量阶段判断、情绪动量计算
"""
import logging
from datetime import datetime
from typing import Dict, List, Optional, Tuple
import statistics

import config

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class SentimentAnalyzer:
    """情绪分析器"""
    
    def __init__(self):
        # 情绪分类阈值
        self.sentiment_thresholds = {
            'extremely_pessimistic': 20,   # 极度悲观
            'pessimistic': 40,             # 悲观
            'neutral': 60,                 # 中性
            'optimistic': 80,              # 乐观
            'extremely_optimistic': 100,   # 极度乐观
        }
        
        # 流量阶段定义
        self.flow_stages = {
            'startup': '启动',      # 刚开始发酵
            'acceleration': '加速', # 增速加快
            'divergence': '分歧',   # 多空分歧
            'consensus': '一致',    # 流量高潮（危险！）
            'decline': '退潮',      # 热度下降
        }
        
        # 阶段判断阈值
        self.stage_thresholds = {
            'startup_growth': 0.20,      # 启动期增速阈值
            'acceleration_growth': 0.20, # 加速期增速阈值
            'divergence_volatility': 0.30, # 分歧期波动率阈值
            'consensus_k': 1.5,          # 一致期K值阈值
            'decline_growth': -0.20,     # 退潮期增速阈值
        }
        
        # 正面/负面关键词（用于情绪分析）
        self.positive_keywords = [
            '利好', '大涨', '暴涨', '涨停', '新高', '突破', '牛市',
            '反弹', '加仓', '买入', '增持', '推荐', '看好', '机遇',
            '政策支持', '业绩预增', '超预期', '景气度', '高增长',
        ]
        
        self.negative_keywords = [
            '利空', '大跌', '暴跌', '跌停', '新低', '破位', '熊市',
            '回调', '减仓', '卖出', '减持', '风险', '看空', '危机',
            '政策收紧', '业绩下滑', '不及预期', '亏损', '退市',
        ]

        # Jev 结构化情绪分类：懒加载客户端（未配置 TYPESAFE_API_KEY 时为 None）
        self._jev_initialized = False
        self._jev_client = None

    def _get_jev_client(self):
        """懒加载 Jev 决策客户端；未配置或初始化失败返回 None。"""
        if not self._jev_initialized:
            try:
                from llm_client import get_jev_client
                self._jev_client = get_jev_client()
            except Exception as e:
                logger.warning(f"Jev 客户端获取失败，新闻情绪分类将走文本/关键词链路: {e}")
                self._jev_client = None
            self._jev_initialized = True
        return self._jev_client

    def classify_news_stance(self, title: str, content: str = "",
                             stock_name: str = "") -> Optional[Dict]:
        """单条新闻立场分类（适配层：优先 Jev，失败降级 DeepSeek 文本+正则）。

        返回 {stance, urgency, relevant, confidence, decision_source}；完全不可用时返回 None。
        """
        jev = self._get_jev_client()
        if jev is not None:
            try:
                from typesafe_decision_client import build_news_state, stance_label
                state = build_news_state(title, content, stock_name)
                answers = jev.ask_news_stance(state)
                label = stance_label(answers)
                if label:
                    confidence = float((answers.get('stance') or {}).get('confidence', 0.0) or 0.0)
                    result = {
                        'stance': label,
                        'urgency': (answers.get('urgency') or {}).get('score'),
                        'relevant': bool((answers.get('relevant') or {}).get('noul', 0) >= 0.5),
                        'confidence': confidence,
                        'decision_source': 'jev',
                        'title': (title or '')[:80],
                    }
                    # 灰度双写：同时记录关键词启发式结果，供分歧分析（6.3）
                    logger.info(f"[双写] 新闻立场 jev={label}(conf={confidence:.2f}) "
                                f"keyword={self._keyword_stance(title, content)} | {title[:30]}")
                    return result
            except Exception as e:
                logger.warning(f"Jev 新闻分类失败，降级 DeepSeek 文本链路: {e}")
        # 降级：DeepSeek 文本 + 正则
        text_result = self._classify_via_text(title, content, stock_name)
        if text_result is not None:
            return text_result
        # 最终兜底：关键词启发式（不调用任何 LLM，永远可用）
        kw = self._keyword_stance(title, content)
        if kw is None:
            return None
        return {'stance': kw, 'urgency': None, 'relevant': None,
                'confidence': None, 'decision_source': 'keyword_fallback'}

    def _classify_via_text(self, title: str, content: str, stock_name: str) -> Optional[Dict]:
        """DeepSeek 文本分类降级链路：生成文本再用正则提取立场。"""
        try:
            import re
            from llm_client import get_llm_client
            client = get_llm_client()
            prompt = (
                f"判断以下新闻对{'股票' if not stock_name else stock_name}的整体立场，"
                f"只回答一个词：利好/中性/利空。\n"
                f"标题：{title}\n内容：{content[:500]}"
            )
            messages = [
                {"role": "system", "content": "你是新闻情绪分类器，只输出'利好'、'中性'或'利空'一个词。"},
                {"role": "user", "content": prompt},
            ]
            response = client.call_api(messages, temperature=0.2, max_tokens=16)
            text = str(response)
            stance = None
            if re.search(r'利空', text):
                stance = '利空'
            elif re.search(r'利好', text):
                stance = '利好'
            elif re.search(r'中性', text):
                stance = '中性'
            if stance:
                return {'stance': stance, 'urgency': None, 'relevant': None,
                        'confidence': None, 'decision_source': 'deepseek_fallback'}
            return None
        except Exception as e:
            logger.warning(f"DeepSeek 文本新闻分类失败: {e}")
            return None

    def _keyword_stance(self, title: str, content: str) -> Optional[str]:
        """关键词启发式立场（供双写对比与无网络兜底）。"""
        text = f"{title} {content}"
        pos = sum(1 for kw in self.positive_keywords if kw in text)
        neg = sum(1 for kw in self.negative_keywords if kw in text)
        if pos == 0 and neg == 0:
            return None
        if pos > neg:
            return '利好'
        if neg > pos:
            return '利空'
        return '中性'

    def classify_batch_stances(self, stock_news: List[Dict], max_items: int = 10) -> List[Dict]:
        """批量分类（限制条数避免逐条过多调用）。返回带 stance 的结果列表。"""
        results = []
        for news in (stock_news or [])[:max_items]:
            r = self.classify_news_stance(news.get('title', ''), news.get('content', ''))
            if r and r.get('stance'):
                results.append(r)
        return results
    
    def calculate_sentiment_index(self, platforms_data: List[Dict], 
                                   stock_news: List[Dict] = None) -> Dict:
        """
        计算情绪指数（0-100）
        
        基于以下因素：
        1. 流量规模（占40%）
        2. 财经平台活跃度（占30%）
        3. 正负面关键词比例（占30%）
        
        Returns:
            {
                'sentiment_index': int,
                'flow_factor': int,
                'finance_factor': int,
                'keyword_factor': int,
                'sentiment_class': str,
                'analysis': str,
            }
        """
        # 1. 流量规模因子（40%）
        total_news = 0
        finance_news = 0
        
        for platform_data in platforms_data:
            if not platform_data.get('success'):
                continue
            count = platform_data.get('count', 0)
            total_news += count
            if platform_data.get('category') == 'finance':
                finance_news += count
        
        # 流量分数：基于新闻数量
        if total_news >= 500:
            flow_factor = 90
        elif total_news >= 300:
            flow_factor = 70
        elif total_news >= 150:
            flow_factor = 50
        elif total_news >= 50:
            flow_factor = 30
        else:
            flow_factor = 10
        
        # 2. 财经平台活跃度因子（30%）
        if total_news > 0:
            finance_ratio = finance_news / total_news
            finance_factor = min(int(finance_ratio * 200), 100)
        else:
            finance_factor = 50
        
        # 3. 关键词情绪因子（30%）
        positive_count = 0
        negative_count = 0
        
        if stock_news:
            for news in stock_news:
                title = news.get('title', '')
                content = news.get('content', '')
                text = f"{title} {content}"
                
                for kw in self.positive_keywords:
                    if kw in text:
                        positive_count += 1
                        break
                
                for kw in self.negative_keywords:
                    if kw in text:
                        negative_count += 1
                        break
        
        total_sentiment_news = positive_count + negative_count
        if total_sentiment_news > 0:
            positive_ratio = positive_count / total_sentiment_news
            keyword_factor = int(positive_ratio * 100)
        else:
            keyword_factor = 50  # 中性

        # 3.5 Jev/文本分类层（仅当启用时）：用高置信度立场细化 keyword_factor
        stance_summary = self._apply_stance_refinement(stock_news)
        if stance_summary:
            sp, sn = stance_summary['positive'], stance_summary['negative']
            st = sp + sn
            if st > 0:
                keyword_factor = int(sp / st * 100)
        
        # 4. 综合计算情绪指数
        sentiment_index = int(
            flow_factor * 0.4 +
            finance_factor * 0.3 +
            keyword_factor * 0.3
        )
        
        # 限制范围
        sentiment_index = max(0, min(100, sentiment_index))
        
        # 5. 情绪分类
        sentiment_class = self.classify_sentiment(sentiment_index)
        
        # 6. 生成分析
        analysis = self._generate_sentiment_analysis(
            sentiment_index, sentiment_class,
            flow_factor, finance_factor, keyword_factor
        )
        
        return {
            'sentiment_index': sentiment_index,
            'flow_factor': flow_factor,
            'finance_factor': finance_factor,
            'keyword_factor': keyword_factor,
            'positive_count': positive_count,
            'negative_count': negative_count,
            'sentiment_class': sentiment_class,
            'analysis': analysis,
            'stance_summary': stance_summary,
        }

    def _apply_stance_refinement(self, stock_news: List[Dict]) -> Optional[Dict]:
        """仅当 Jev 启用时，对新闻做立场分类并汇总（降级链已在 classify_news_stance 内部）。

        返回 {positive, negative, neutral, sources}；未启用 Jev 时返回 None（保持原关键词链路）。
        """
        if self._get_jev_client() is None or not stock_news:
            return None
        stances = self.classify_batch_stances(stock_news, max_items=10)
        if not stances:
            return None
        pos = sum(1 for s in stances if s['stance'] == '利好')
        neg = sum(1 for s in stances if s['stance'] == '利空')
        neu = sum(1 for s in stances if s['stance'] == '中性')
        sources = {}
        for s in stances:
            sources[s.get('decision_source')] = sources.get(s.get('decision_source'), 0) + 1
        # 告警候选：仅高置信度的 Jev 利好/利空结论（门控阈值 config.JEV_ALERT_MIN_CONFIDENCE）
        alerts = [
            {'stance': s['stance'], 'confidence': s['confidence'], 'title': s.get('title', ''),
             'urgency': s.get('urgency')}
            for s in stances
            if s.get('decision_source') == 'jev' and s.get('stance') in ('利好', '利空')
            and (s.get('confidence') or 0) >= config.JEV_ALERT_MIN_CONFIDENCE
        ]
        return {'positive': pos, 'negative': neg, 'neutral': neu,
                'total': len(stances), 'sources': sources, 'alerts': alerts}
    
    def classify_sentiment(self, index: int) -> str:
        """
        情绪分类
        
        极度悲观(<20) / 悲观(20-40) / 中性(40-60) / 乐观(60-80) / 极度乐观(>80)
        """
        if index < 20:
            return "极度悲观"
        elif index < 40:
            return "悲观"
        elif index < 60:
            return "中性"
        elif index < 80:
            return "乐观"
        else:
            return "极度乐观"
    
    def _generate_sentiment_analysis(self, index: int, sentiment_class: str,
                                       flow: int, finance: int, keyword: int) -> str:
        """生成情绪分析文本"""
        if sentiment_class == "极度乐观":
            return f"情绪指数{index}，市场极度乐观！流量爆发({flow})，财经活跃({finance})。警告：可能是情绪顶部，注意获利了结。"
        elif sentiment_class == "乐观":
            return f"情绪指数{index}，市场情绪乐观。题材正在发酵，可关注龙头机会，但需注意节奏。"
        elif sentiment_class == "中性":
            return f"情绪指数{index}，市场情绪中性。缺乏明确方向，建议观望为主。"
        elif sentiment_class == "悲观":
            return f"情绪指数{index}，市场情绪偏悲观。负面因素较多，控制仓位，等待转机。"
        else:  # 极度悲观
            return f"情绪指数{index}，市场极度悲观！恐慌情绪蔓延。可能是超跌机会，但需谨慎左侧布局。"
    
    def determine_flow_stage(self, history_scores: List[int], 
                              current_score: int,
                              current_k: float = None) -> Dict:
        """
        判断流量阶段
        
        流量阶段：
        1. 启动 - 刚开始发酵，关注
        2. 加速 - 增速加快，参与
        3. 分歧 - 多空分歧，谨慎
        4. 一致 - 流量高潮，危险！准备跑路
        5. 退潮 - 热度下降，及时止盈止损
        
        Returns:
            {
                'stage': str,
                'stage_name': str,
                'confidence': int,
                'signal': str,  # 关注/参与/谨慎/危险/离场
                'analysis': str,
            }
        """
        if len(history_scores) < 3:
            return {
                'stage': 'unknown',
                'stage_name': '未知',
                'confidence': 0,
                'signal': '观察',
                'analysis': '历史数据不足，继续观察积累数据',
            }
        
        # 计算增长率序列
        all_scores = history_scores + [current_score]
        growth_rates = []
        for i in range(1, len(all_scores)):
            if all_scores[i-1] > 0:
                rate = (all_scores[i] - all_scores[i-1]) / all_scores[i-1]
                growth_rates.append(rate)
        
        # 计算关键指标
        recent_growth_rates = growth_rates[-3:] if len(growth_rates) >= 3 else growth_rates
        avg_growth = sum(recent_growth_rates) / len(recent_growth_rates) if recent_growth_rates else 0
        
        # 波动率（标准差）
        if len(recent_growth_rates) >= 2:
            volatility = statistics.stdev(recent_growth_rates)
        else:
            volatility = 0
        
        # 计算K值（如果没有提供）
        if current_k is None and len(all_scores) >= 2:
            previous_score = all_scores[-2]
            current_k = current_score / previous_score if previous_score > 0 else 1.0
        elif current_k is None:
            current_k = 1.0
        
        # 判断上升/下降趋势
        positive_count = sum(1 for r in recent_growth_rates if r > 0)
        negative_count = sum(1 for r in recent_growth_rates if r < 0)
        
        # 阶段判断逻辑
        stage = 'unknown'
        stage_name = '未知'
        confidence = 50
        signal = '观察'
        analysis = ''
        
        # 1. 一致阶段（最危险）- K值>1.5 且 高增速
        if current_k >= 1.5 and avg_growth > 0.3:
            stage = 'consensus'
            stage_name = '一致'
            confidence = 90
            signal = '危险'
            analysis = f"流量高潮！K值={current_k:.2f}，增速{avg_growth*100:.1f}%。市场一致看多，这往往是顶部信号。立即减仓或清仓！"
        
        # 2. 退潮阶段 - 连续下降
        elif negative_count >= 2 and avg_growth < -0.15:
            stage = 'decline'
            stage_name = '退潮'
            confidence = 85
            signal = '离场'
            analysis = f"流量退潮！连续下降，增速{avg_growth*100:.1f}%。题材热度消退，及时止盈止损，不要恋战。"
        
        # 3. 分歧阶段 - 高波动，涨跌交替
        elif volatility > 0.25 and positive_count > 0 and negative_count > 0:
            stage = 'divergence'
            stage_name = '分歧'
            confidence = 75
            signal = '谨慎'
            analysis = f"多空分歧！波动率{volatility*100:.1f}%，市场观点不一。高抛低吸，控制仓位，设好止损。"
        
        # 4. 加速阶段 - 持续上涨，增速加快
        elif avg_growth > 0.2 and current_k > 1.1 and positive_count >= 2:
            stage = 'acceleration'
            stage_name = '加速'
            confidence = 80
            signal = '参与'
            analysis = f"流量加速！增速{avg_growth*100:.1f}%，K值{current_k:.2f}。题材正在快速发酵，可参与龙头，但注意仓位。"
        
        # 5. 启动阶段 - 刚开始上涨
        elif avg_growth > 0.05 and positive_count >= 2:
            stage = 'startup'
            stage_name = '启动'
            confidence = 70
            signal = '关注'
            analysis = f"流量启动！增速{avg_growth*100:.1f}%，题材刚开始发酵。可以关注，等待确认后介入。"
        
        # 6. 其他情况
        else:
            stage = 'stable'
            stage_name = '平稳'
            confidence = 60
            signal = '观察'
            analysis = f"流量平稳。增速{avg_growth*100:.1f}%，无明显趋势。保持观望，等待方向明确。"
        
        return {
            'stage': stage,
            'stage_name': stage_name,
            'confidence': confidence,
            'signal': signal,
            'analysis': analysis,
            'avg_growth': round(avg_growth * 100, 1),
            'volatility': round(volatility * 100, 1),
            'current_k': round(current_k, 2),
        }
    
    def calculate_momentum(self, history_data: List[Dict]) -> Dict:
        """
        计算情绪动量
        
        情绪动量 = 当前变化速率 / 平均变化速率
        
        动量 > 1.5: 情绪加速
        动量 ≈ 1: 情绪稳定
        动量 < 0.5: 情绪减速
        
        Args:
            history_data: 历史数据列表，每项包含 'sentiment_index' 和 'timestamp'
            
        Returns:
            {
                'momentum': float,
                'momentum_level': str,
                'trend': str,
                'analysis': str,
            }
        """
        if len(history_data) < 3:
            return {
                'momentum': 1.0,
                'momentum_level': '正常',
                'trend': '数据不足',
                'analysis': '历史数据不足，无法计算动量',
            }
        
        # 提取情绪指数序列
        sentiment_values = [d.get('sentiment_index', 50) for d in history_data]
        
        # 计算变化率序列
        changes = []
        for i in range(1, len(sentiment_values)):
            change = sentiment_values[i] - sentiment_values[i-1]
            changes.append(abs(change))
        
        # 计算平均变化率
        avg_change = sum(changes) / len(changes) if changes else 1
        
        # 计算当前变化率（最近的变化）
        current_change = abs(changes[-1]) if changes else 0
        
        # 计算动量
        if avg_change > 0:
            momentum = round(current_change / avg_change, 2)
        else:
            momentum = 1.0
        
        # 确定动量级别和趋势
        if momentum >= 2.0:
            momentum_level = '极高'
            trend = '急剧变化'
            analysis = f"情绪动量{momentum}，情绪正在急剧变化！市场可能出现转折点，密切关注。"
        elif momentum >= 1.5:
            momentum_level = '高'
            trend = '加速变化'
            analysis = f"情绪动量{momentum}，情绪变化正在加速。趋势可能强化或反转。"
        elif momentum >= 0.8:
            momentum_level = '正常'
            trend = '稳定'
            analysis = f"情绪动量{momentum}，情绪变化平稳，市场处于正常状态。"
        elif momentum >= 0.3:
            momentum_level = '低'
            trend = '减速'
            analysis = f"情绪动量{momentum}，情绪变化正在减速，可能进入盘整期。"
        else:
            momentum_level = '极低'
            trend = '停滞'
            analysis = f"情绪动量{momentum}，情绪几乎没有变化，市场陷入僵局。"
        
        # 判断方向
        if len(sentiment_values) >= 2:
            direction = sentiment_values[-1] - sentiment_values[-2]
            if direction > 0:
                trend += "（向上）"
            elif direction < 0:
                trend += "（向下）"
        
        return {
            'momentum': momentum,
            'momentum_level': momentum_level,
            'trend': trend,
            'current_change': current_change,
            'avg_change': round(avg_change, 1),
            'analysis': analysis,
        }
    
    def run_full_sentiment_analysis(self, platforms_data: List[Dict],
                                      stock_news: List[Dict],
                                      history_scores: List[int],
                                      current_score: int,
                                      history_sentiments: List[Dict] = None) -> Dict:
        """
        运行完整的情绪分析
        
        Returns:
            {
                'sentiment': Dict,  # 情绪指数
                'flow_stage': Dict,  # 流量阶段
                'momentum': Dict,  # 情绪动量
                'summary': str,  # 总结
                'risk_level': str,  # 风险等级
                'advice': str,  # 操作建议
            }
        """
        # 1. 计算情绪指数
        sentiment = self.calculate_sentiment_index(platforms_data, stock_news)
        
        # 2. 判断流量阶段
        flow_stage = self.determine_flow_stage(history_scores, current_score)
        
        # 3. 计算情绪动量
        if history_sentiments and len(history_sentiments) >= 3:
            momentum = self.calculate_momentum(history_sentiments)
        else:
            momentum = {
                'momentum': 1.0,
                'momentum_level': '正常',
                'trend': '数据不足',
                'analysis': '历史情绪数据不足',
            }
        
        # 4. 综合风险评估
        risk_level, advice = self._assess_risk(sentiment, flow_stage, momentum)
        
        # 5. 生成总结
        summary = self._generate_summary(sentiment, flow_stage, momentum, risk_level)
        
        return {
            'sentiment': sentiment,
            'flow_stage': flow_stage,
            'momentum': momentum,
            'summary': summary,
            'risk_level': risk_level,
            'advice': advice,
            'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
        }
    
    def _assess_risk(self, sentiment: Dict, flow_stage: Dict, 
                     momentum: Dict) -> Tuple[str, str]:
        """综合风险评估"""
        risk_score = 0
        
        # 情绪因素
        sentiment_index = sentiment['sentiment_index']
        if sentiment_index > 85:
            risk_score += 3  # 过度乐观
        elif sentiment_index < 25:
            risk_score += 2  # 过度悲观
        
        # 流量阶段因素
        stage = flow_stage['stage']
        if stage == 'consensus':
            risk_score += 4  # 一致阶段最危险
        elif stage == 'decline':
            risk_score += 3
        elif stage == 'divergence':
            risk_score += 2
        
        # 动量因素
        momentum_value = momentum['momentum']
        if momentum_value > 2.0:
            risk_score += 2  # 变化过快
        
        # 确定风险等级和建议
        if risk_score >= 7:
            risk_level = "极高"
            advice = "立即减仓或清仓！市场处于极端状态，控制风险为第一要务。"
        elif risk_score >= 5:
            risk_level = "高"
            advice = "谨慎操作，建议减仓。不追高，设置严格止损。"
        elif risk_score >= 3:
            risk_level = "中等"
            advice = "正常操作，注意仓位控制。逢高减仓，逢低观察。"
        elif risk_score >= 1:
            risk_level = "低"
            advice = "可适度参与，关注龙头机会。"
        else:
            risk_level = "极低"
            advice = "风险较低，可积极参与，但仍需设置止损。"
        
        return risk_level, advice
    
    def _generate_summary(self, sentiment: Dict, flow_stage: Dict,
                          momentum: Dict, risk_level: str) -> str:
        """生成综合总结"""
        lines = [
            f"【情绪】{sentiment['sentiment_class']}（{sentiment['sentiment_index']}分）",
            f"【阶段】{flow_stage['stage_name']}期，信号：{flow_stage['signal']}",
            f"【动量】{momentum['momentum_level']}，趋势{momentum['trend']}",
            f"【风险】{risk_level}",
        ]
        
        return '\n'.join(lines)


# 全局实例
sentiment_analyzer = SentimentAnalyzer()


# 测试代码
if __name__ == "__main__":
    print("=== 测试情绪分析模块 ===")
    
    # 模拟数据
    platforms_data = [
        {'success': True, 'category': 'finance', 'count': 100},
        {'success': True, 'category': 'social', 'count': 200},
        {'success': True, 'category': 'news', 'count': 150},
    ]
    
    stock_news = [
        {'title': 'AI板块大涨，龙头股涨停', 'content': '利好政策推动'},
        {'title': '新能源概念股反弹', 'content': '业绩预增超预期'},
        {'title': '市场观望情绪浓厚', 'content': '回调风险加大'},
    ]
    
    history_scores = [300, 350, 420, 500, 580]
    current_score = 650
    
    history_sentiments = [
        {'sentiment_index': 55},
        {'sentiment_index': 60},
        {'sentiment_index': 68},
        {'sentiment_index': 72},
    ]
    
    # 运行完整分析
    result = sentiment_analyzer.run_full_sentiment_analysis(
        platforms_data, stock_news, history_scores, current_score, history_sentiments
    )
    
    print(f"\n情绪指数: {result['sentiment']['sentiment_index']} ({result['sentiment']['sentiment_class']})")
    print(f"流量阶段: {result['flow_stage']['stage_name']} - {result['flow_stage']['signal']}")
    print(f"情绪动量: {result['momentum']['momentum']} ({result['momentum']['momentum_level']})")
    print(f"风险等级: {result['risk_level']}")
    print(f"\n===总结===\n{result['summary']}")
    print(f"\n操作建议: {result['advice']}")
