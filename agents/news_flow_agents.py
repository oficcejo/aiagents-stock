"""
新闻流量智能分析代理模块
使用DeepSeek进行AI驱动的分析
包含：板块影响分析、股票推荐、风险评估、投资建议
"""
import json
import logging
import time
from datetime import datetime
from typing import Dict, List, Optional

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class NewsFlowAgents:
    """新闻流量智能分析代理"""
    
    def __init__(self, model: str = None):
        """
        初始化代理
        
        Args:
            model: 使用的模型，默认从 .env 的 DEFAULT_MODEL_NAME 读取
        """
        from core import config
        self.model = model or config.DEFAULT_MODEL_NAME
        self.deepseek_client = None
        self._init_client()
    
    def _init_client(self):
        """初始化DeepSeek客户端"""
        try:
            from core.deepseek_client import DeepSeekClient
            self.deepseek_client = DeepSeekClient(model=self.model)
            logger.info(f"✅ DeepSeek客户端初始化成功，模型: {self.model}")
        except Exception as e:
            logger.error(f"❌ DeepSeek客户端初始化失败: {e}")
            self.deepseek_client = None
    
    def is_available(self) -> bool:
        """检查AI是否可用"""
        return self.deepseek_client is not None
    
    def sector_impact_agent(self, hot_topics: List[Dict], 
                            stock_news: List[Dict],
                            flow_data: Dict = None) -> Dict:
        """
        板块影响分析代理
        
        分析热点可能影响的板块
        
        Returns:
            {
                'affected_sectors': List[Dict],
                'analysis': str,
                'success': bool,
            }
        """
        if not self.is_available():
            return self._fallback_sector_analysis(hot_topics, stock_news)
        
        # 准备数据
        topics_text = '\n'.join([
            f"- {t['topic']} (热度:{t.get('heat', 0)}, 跨{t.get('cross_platform', 0)}平台)"
            for t in hot_topics[:20]
        ])
        
        news_text = '\n'.join([
            f"- [{n.get('platform_name', '')}] {n.get('title', '')}"
            for n in stock_news[:15]
        ])
        
        flow_info = ""
        if flow_data:
            flow_info = f"""
当前流量状态:
- 流量得分: {flow_data.get('total_score', 'N/A')}/1000
- 流量等级: {flow_data.get('level', 'N/A')}
- 社交媒体热度: {flow_data.get('social_score', 'N/A')}
- 财经平台热度: {flow_data.get('finance_score', 'N/A')}
"""
        
        prompt = f"""你是一名资深的A股短线投资分析师，专注于热点题材挖掘和板块轮动分析。

【重要】请根据以下全网热点数据，进行深度的A股题材分析：

=== 全网热门话题TOP20 ===
{topics_text}

=== 股票相关新闻TOP15 ===
{news_text}
{flow_info}

请完成以下分析任务：

1. **题材挖掘**：从以上热点中挖掘出可能引爆A股的核心题材概念
2. **板块分析**：分析最可能受益的A股板块（要具体到申万行业或同花顺概念板块）
3. **热度评估**：评估每个板块的潜在炒作热度和持续性
4. **龙头预判**：推测可能的龙头股特征

请以JSON格式输出：
{{
    "hot_themes": [
        {{"theme": "题材名称", "source": "来源热点", "heat_level": "极高/高/中", "sustainability": "持续性评估"}}
    ],
    "benefited_sectors": [
        {{
            "name": "板块名称（要具体如：AI算力、低空经济、机器人等）",
            "impact": "利好",
            "confidence": 85,
            "reason": "详细分析原因",
            "related_concepts": ["相关概念1", "相关概念2"],
            "leader_characteristics": "龙头股特征描述"
        }}
    ],
    "damaged_sectors": [
        {{"name": "板块名称", "impact": "利空", "confidence": 60, "reason": "原因"}}
    ],
    "opportunity_assessment": "今日A股投资机会综合评估（100字以内）",
    "trading_suggestion": "短线操作建议",
    "key_points": ["核心要点1", "核心要点2", "核心要点3"]
}}

只输出JSON，不要其他文字。"""

        try:
            messages = [
                {"role": "system", "content": "你是专业的A股市场分析师，输出必须是纯JSON格式。"},
                {"role": "user", "content": prompt}
            ]
            
            response = self.deepseek_client.call_api(messages, temperature=0.5, max_tokens=2000)
            
            # 解析JSON
            result = self._parse_json_response(response)
            
            if result:
                return {
                    'hot_themes': result.get('hot_themes', []),
                    'affected_sectors': result.get('benefited_sectors', []) + result.get('damaged_sectors', []),
                    'benefited_sectors': result.get('benefited_sectors', []),
                    'damaged_sectors': result.get('damaged_sectors', []),
                    'opportunity_assessment': result.get('opportunity_assessment', ''),
                    'trading_suggestion': result.get('trading_suggestion', ''),
                    'key_points': result.get('key_points', []),
                    'success': True,
                    'raw_response': response,
                }
            else:
                return self._fallback_sector_analysis(hot_topics, stock_news)
                
        except Exception as e:
            logger.error(f"板块分析失败: {e}")
            return self._fallback_sector_analysis(hot_topics, stock_news)
    
    def stock_recommend_agent(self, hot_sectors: List[Dict],
                               flow_stage: str,
                               sentiment_class: str) -> Dict:
        """
        股票推荐代理
        
        基于热门板块和市场状态推荐股票
        
        Returns:
            {
                'recommended_stocks': List[Dict],
                'strategy': str,
                'success': bool,
            }
        """
        if not self.is_available():
            return self._fallback_stock_recommend(hot_sectors)
        
        sectors_text = '\n'.join([
            f"- {s.get('name', '')}：{s.get('impact', '利好')}，置信度{s.get('confidence', 50)}%\n  原因：{s.get('reason', '')}\n  龙头特征：{s.get('leader_characteristics', 'N/A')}"
            for s in hot_sectors[:5]
        ])
        
        related_concepts = []
        for s in hot_sectors[:5]:
            related_concepts.extend(s.get('related_concepts', []))
        concepts_text = ', '.join(list(set(related_concepts))[:10]) if related_concepts else '无'
        
        prompt = f"""你是一名资深的A股短线游资操盘手，专注于热点题材龙头股挖掘。

=== 当前市场状态 ===
- 流量阶段: {flow_stage} 
- 情绪状态: {sentiment_class}
- 相关概念: {concepts_text}

=== 热门受益板块分析 ===
{sectors_text}

=== 选股要求 ===
请根据"流量为王"理念，推荐5-8只A股短线标的：

选股法则（必须遵循）：
1. **先涨为王**：优先选择已经启动、走势强势的股票
2. **名字为王**：股票名称与热点高度相关（如AI概念选"智"字头）
3. **龙头优先**：选择板块内最强势的龙头或人气股
4. **题材纯正**：主业与热点题材高度相关
5. **流通盘适中**：30-150亿市值为佳，便于资金操作

请以JSON格式输出：
{{
    "recommended_stocks": [
        {{
            "code": "股票代码（6位数字，如000001或600001）",
            "name": "股票名称",
            "sector": "所属板块",
            "market": "沪市/深市/创业板/科创板",
            "market_cap": "市值（亿）",
            "reason": "推荐理由（与热点的关联性）",
            "catalyst": "催化剂/驱动因素",
            "strategy": "操作策略（进场/加仓/止损建议）",
            "target_space": "目标空间（如15-20%）",
            "risk_level": "低/中/高",
            "attention_points": ["注意事项1", "注意事项2"]
        }}
    ],
    "overall_strategy": "整体操作策略和仓位建议",
    "timing_advice": "最佳介入时机判断",
    "risk_warning": "风险提示（必须包含投资风险提醒）"
}}

【重要】只推荐真实存在的A股股票，代码必须正确。只输出JSON。"""

        try:
            messages = [
                {"role": "system", "content": "你是专业的A股投资顾问，只输出纯JSON格式。"},
                {"role": "user", "content": prompt}
            ]
            
            response = self.deepseek_client.call_api(messages, temperature=0.6, max_tokens=2000)
            result = self._parse_json_response(response)
            
            if result:
                return {
                    'recommended_stocks': result.get('recommended_stocks', []),
                    'overall_strategy': result.get('overall_strategy', ''),
                    'timing_advice': result.get('timing_advice', ''),
                    'risk_warning': result.get('risk_warning', ''),
                    'success': True,
                    'raw_response': response,
                }
            else:
                return self._fallback_stock_recommend(hot_sectors)
                
        except Exception as e:
            logger.error(f"股票推荐失败: {e}")
            return self._fallback_stock_recommend(hot_sectors)
    
    def risk_assess_agent(self, flow_stage: str, 
                          sentiment_data: Dict,
                          viral_k: float,
                          flow_type: str) -> Dict:
        """
        风险评估代理
        
        评估当前市场风险
        
        Returns:
            {
                'risk_level': str,
                'risk_factors': List[str],
                'risk_score': int,
                'analysis': str,
                'success': bool,
            }
        """
        if not self.is_available():
            return self._fallback_risk_assess(flow_stage, sentiment_data, viral_k)
        
        prompt = f"""你是一名专业的风险管理分析师。

请根据以下市场数据评估当前投资风险：

市场状态：
- 流量阶段: {flow_stage}
- 情绪指数: {sentiment_data.get('sentiment_index', 50)}
- 情绪分类: {sentiment_data.get('sentiment_class', '中性')}
- K值(病毒系数): {viral_k}
- 流量类型: {flow_type}

核心理念：
- 流量高潮 = 价格高潮 = 逃命时刻
- K值>1.5表示指数型爆发，风险上升
- 情绪极端（>85或<20）都意味着风险

请分析：
1. 当前风险等级（极低/低/中等/高/极高）
2. 主要风险因素
3. 风险分数（0-100）
4. 详细分析

以JSON格式输出：
{{
    "risk_level": "高",
    "risk_score": 75,
    "risk_factors": ["风险因素1", "风险因素2", ...],
    "opportunities": ["机会1", "机会2", ...],
    "analysis": "详细分析文字",
    "key_warning": "最重要的警告"
}}

只输出JSON。"""

        try:
            messages = [
                {"role": "system", "content": "你是专业的风险管理分析师，只输出纯JSON格式。"},
                {"role": "user", "content": prompt}
            ]
            
            response = self.deepseek_client.call_api(messages, temperature=0.4, max_tokens=1500)
            result = self._parse_json_response(response)
            
            if result:
                return {
                    'risk_level': result.get('risk_level', '中等'),
                    'risk_score': result.get('risk_score', 50),
                    'risk_factors': result.get('risk_factors', []),
                    'opportunities': result.get('opportunities', []),
                    'analysis': result.get('analysis', ''),
                    'key_warning': result.get('key_warning', ''),
                    'success': True,
                    'raw_response': response,
                }
            else:
                return self._fallback_risk_assess(flow_stage, sentiment_data, viral_k)
                
        except Exception as e:
            logger.error(f"风险评估失败: {e}")
            return self._fallback_risk_assess(flow_stage, sentiment_data, viral_k)
    
    def investment_advisor_agent(self, sector_analysis: Dict,
                                   stock_recommend: Dict,
                                   risk_assess: Dict,
                                   flow_data: Dict,
                                   sentiment_data: Dict) -> Dict:
        """
        投资建议代理（综合）
        
        综合所有分析给出最终投资建议
        
        Returns:
            {
                'advice': str,  # 买入/持有/观望/回避
                'confidence': int,
                'summary': str,
                'action_plan': List[str],
                'success': bool,
            }
        """
        if not self.is_available():
            return self._fallback_investment_advice(risk_assess, flow_data)
        
        # 构建综合信息
        sectors_text = ', '.join([s.get('name', '') for s in sector_analysis.get('benefited_sectors', [])[:3]])
        stocks_text = ', '.join([f"{s.get('name', '')}({s.get('code', '')})" 
                                 for s in stock_recommend.get('recommended_stocks', [])[:3]])
        
        prompt = f"""你是一名首席投资策略师，需要给出最终的投资建议。

综合分析数据：

【流量分析】
- 流量得分: {flow_data.get('total_score', 'N/A')}
- 流量等级: {flow_data.get('level', 'N/A')}

【情绪分析】
- 情绪指数: {sentiment_data.get('sentiment_index', 50)}
- 情绪分类: {sentiment_data.get('sentiment_class', '中性')}
- 流量阶段: {sentiment_data.get('flow_stage', '未知')}

【板块分析】
- 受益板块: {sectors_text}
- 机会评估: {sector_analysis.get('opportunity_assessment', 'N/A')}

【股票推荐】
- 推荐股票: {stocks_text}

【风险评估】
- 风险等级: {risk_assess.get('risk_level', '中等')}
- 风险分数: {risk_assess.get('risk_score', 50)}
- 主要风险: {', '.join(risk_assess.get('risk_factors', [])[:3])}

核心原则（流量为王）：
- 流量高潮 = 价格高潮 = 逃命时刻
- 当热搜、媒体报道、KOL转发同时达到高潮时，就是出货时机
- 短线操作：快进快出，紧跟龙头

请给出最终投资建议：
1. 操作建议（买入/持有/观望/回避）
2. 置信度（0-100）
3. 综合总结
4. 具体行动计划

以JSON格式输出：
{{
    "advice": "观望",
    "confidence": 75,
    "summary": "综合总结文字",
    "action_plan": [
        "行动1",
        "行动2",
        ...
    ],
    "position_suggestion": "仓位建议",
    "timing": "时机判断",
    "key_message": "最重要的一句话"
}}

只输出JSON。"""

        try:
            start_time = time.time()
            
            messages = [
                {"role": "system", "content": "你是首席投资策略师，必须给出明确的投资建议，只输出纯JSON格式。"},
                {"role": "user", "content": prompt}
            ]
            
            response = self.deepseek_client.call_api(messages, temperature=0.5, max_tokens=2000)
            result = self._parse_json_response(response)
            
            analysis_time = time.time() - start_time
            
            if result:
                return {
                    'advice': result.get('advice', '观望'),
                    'confidence': result.get('confidence', 50),
                    'summary': result.get('summary', ''),
                    'action_plan': result.get('action_plan', []),
                    'position_suggestion': result.get('position_suggestion', ''),
                    'timing': result.get('timing', ''),
                    'key_message': result.get('key_message', ''),
                    'success': True,
                    'analysis_time': round(analysis_time, 2),
                    'raw_response': response,
                }
            else:
                return self._fallback_investment_advice(risk_assess, flow_data)
                
        except Exception as e:
            logger.error(f"投资建议生成失败: {e}")
            return self._fallback_investment_advice(risk_assess, flow_data)
    
    def run_full_analysis(self, hot_topics: List[Dict],
                           stock_news: List[Dict],
                           flow_data: Dict,
                           sentiment_data: Dict,
                           viral_k: float = 1.0,
                           flow_type: str = "未知") -> Dict:
        """
        运行完整的AI分析
        
        Returns:
            {
                'sector_analysis': Dict,
                'stock_recommend': Dict,
                'risk_assess': Dict,
                'investment_advice': Dict,
                'success': bool,
                'analysis_time': float,
            }
        """
        start_time = time.time()
        
        logger.info("🤖 开始AI分析...")
        
        # 1. 板块影响分析
        logger.info("  📊 分析板块影响...")
        sector_analysis = self.sector_impact_agent(hot_topics, stock_news, flow_data)
        
        # 2. 股票推荐
        logger.info("  📈 生成股票推荐...")
        flow_stage = sentiment_data.get('flow_stage', {}).get('stage_name', '未知')
        sentiment_class = sentiment_data.get('sentiment', {}).get('sentiment_class', '中性')
        stock_recommend = self.stock_recommend_agent(
            sector_analysis.get('benefited_sectors', []),
            flow_stage,
            sentiment_class
        )
        
        # 3. 风险评估
        logger.info("  ⚠️ 评估风险...")
        risk_assess = self.risk_assess_agent(
            flow_stage,
            sentiment_data.get('sentiment', {}),
            viral_k,
            flow_type
        )
        
        # 4. 综合投资建议
        logger.info("  💡 生成投资建议...")
        investment_advice = self.investment_advisor_agent(
            sector_analysis,
            stock_recommend,
            risk_assess,
            flow_data,
            sentiment_data.get('sentiment', {})
        )
        
        total_time = time.time() - start_time
        logger.info(f"✅ AI分析完成，耗时 {total_time:.2f} 秒")
        
        # 汇总结果
        return {
            'sector_analysis': sector_analysis,
            'stock_recommend': stock_recommend,
            'risk_assess': risk_assess,
            'investment_advice': investment_advice,
            'success': all([
                sector_analysis.get('success', False),
                stock_recommend.get('success', False),
                risk_assess.get('success', False),
                investment_advice.get('success', False),
            ]),
            'analysis_time': round(total_time, 2),
            'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
        }
    
    def analyze_sector_deep(self, sector_name: str, related_news: List[Dict], 
                            hot_topics: List[Dict]) -> Dict:
        """
        深度分析单个板块
        
        为每个热门板块单独调用DeepSeek进行深度分析
        """
        if not self.is_available():
            return {'success': False, 'error': 'AI不可用'}
        
        news_text = '\n'.join([
            f"- [{n.get('platform_name', '')}] {n.get('title', '')}"
            for n in related_news[:20]
        ])
        
        topics_text = '\n'.join([
            f"- {t['topic']} (热度:{t.get('heat', 0)})"
            for t in hot_topics[:10]
        ])
        
        prompt = f"""你是{sector_name}板块的专业分析师。

请对以下与{sector_name}相关的新闻进行深度分析：

【相关新闻】
{news_text}

【相关热点话题】
{topics_text}

请分析：
1. {sector_name}板块当前的市场热度和关注度
2. 驱动因素分析（政策/技术/资金/事件）
3. 短期（1-3天）走势预判
4. 核心龙头股分析（至少3只）
5. 投资建议和风险提示

以JSON格式输出：
{{
    "sector_name": "{sector_name}",
    "heat_level": "极高/高/中/低",
    "heat_score": 85,
    "drivers": [
        {{"type": "政策", "content": "具体驱动因素", "impact": "正面/负面"}}
    ],
    "short_term_outlook": "看涨/震荡/看跌",
    "outlook_reason": "预判理由",
    "leader_stocks": [
        {{
            "code": "600000",
            "name": "股票名称",
            "reason": "龙头理由",
            "strategy": "操作策略"
        }}
    ],
    "investment_advice": "具体投资建议",
    "risk_warning": "风险提示",
    "key_indicators": {{
        "关注度": "高",
        "资金流向": "净流入",
        "情绪指数": 75
    }}
}}

只输出JSON。"""

        try:
            messages = [
                {"role": "system", "content": f"你是{sector_name}板块专业分析师，只输出JSON格式。"},
                {"role": "user", "content": prompt}
            ]
            
            response = self.deepseek_client.call_api(messages, temperature=0.5, max_tokens=2000)
            result = self._parse_json_response(response)
            
            if result:
                result['success'] = True
                return result
            else:
                return {'success': False, 'sector_name': sector_name}
                
        except Exception as e:
            logger.error(f"{sector_name}板块分析失败: {e}")
            return {'success': False, 'sector_name': sector_name, 'error': str(e)}
    
    def run_multi_sector_analysis(self, hot_topics: List[Dict], 
                                   stock_news: List[Dict],
                                   target_sectors: List[str] = None) -> Dict:
        """
        多板块并行分析
        
        对多个热门板块分别调用DeepSeek进行深度分析
        
        Args:
            hot_topics: 热门话题列表
            stock_news: 股票相关新闻
            target_sectors: 指定分析的板块列表，为None则自动识别
            
        Returns:
            {
                'sector_analyses': List[Dict],  # 各板块分析结果
                'summary': str,  # 综合总结
                'top_sectors': List[str],  # 最热门板块
                'success': bool
            }
        """
        if not self.is_available():
            return {'success': False, 'error': 'AI不可用', 'sector_analyses': []}
        
        start_time = time.time()
        
        # 如果没有指定板块，先识别热门板块
        if not target_sectors:
            target_sectors = self._identify_hot_sectors(hot_topics, stock_news)
        
        logger.info(f"🔍 开始分析 {len(target_sectors)} 个热门板块: {target_sectors}")
        
        # 对每个板块进行深度分析
        sector_analyses = []
        for sector in target_sectors[:5]:  # 最多分析5个板块
            logger.info(f"  📊 分析板块: {sector}")
            
            # 筛选与该板块相关的新闻
            related_news = self._filter_news_by_sector(stock_news, sector)
            related_topics = self._filter_topics_by_sector(hot_topics, sector)
            
            analysis = self.analyze_sector_deep(sector, related_news, related_topics)
            if analysis.get('success'):
                sector_analyses.append(analysis)
        
        # 生成综合总结
        summary = self._generate_multi_sector_summary(sector_analyses)
        
        total_time = time.time() - start_time
        logger.info(f"✅ 多板块分析完成，耗时 {total_time:.2f} 秒")
        
        return {
            'sector_analyses': sector_analyses,
            'summary': summary,
            'top_sectors': target_sectors[:5],
            'analysis_count': len(sector_analyses),
            'analysis_time': round(total_time, 2),
            'success': len(sector_analyses) > 0
        }
    
    def _identify_hot_sectors(self, hot_topics: List[Dict], stock_news: List[Dict]) -> List[str]:
        """识别热门板块"""
        # 板块关键词映射
        sector_keywords = {
            'AI人工智能': ['AI', '人工智能', '大模型', 'ChatGPT', '算力', '智能', 'DeepSeek', '机器人'],
            '新能源': ['新能源', '光伏', '锂电', '储能', '电池', '充电桩', '风电'],
            '半导体芯片': ['芯片', '半导体', '光刻', '封装', '晶圆', '国产替代'],
            '医药生物': ['医药', '生物', '疫苗', '创新药', '医疗', 'CXO'],
            '消费': ['消费', '白酒', '食品', '零售', '餐饮', '旅游'],
            '金融': ['银行', '保险', '券商', '证券', '金融'],
            '房地产': ['房地产', '地产', '楼市', '房价'],
            '军工': ['军工', '国防', '航空', '航天', '武器'],
            '汽车': ['汽车', '新能源车', '智能驾驶', '无人驾驶'],
            '低空经济': ['低空', '无人机', '飞行汽车', 'eVTOL'],
            '机器人': ['机器人', '人形机器人', '工业机器人', '减速器'],
            '数据要素': ['数据', '数据要素', '数据交易', '数字经济'],
        }
        
        # 统计各板块的热度
        sector_scores = {}
        
        # 从话题中统计
        for topic in hot_topics:
            topic_text = topic.get('topic', '')
            for sector, keywords in sector_keywords.items():
                for kw in keywords:
                    if kw in topic_text:
                        sector_scores[sector] = sector_scores.get(sector, 0) + topic.get('heat', 1)
                        break
        
        # 从新闻中统计
        for news in stock_news:
            news_text = (news.get('title') or '') + (news.get('content') or '')
            for sector, keywords in sector_keywords.items():
                for kw in keywords:
                    if kw in news_text:
                        sector_scores[sector] = sector_scores.get(sector, 0) + news.get('weight', 1)
                        break
        
        # 按热度排序
        sorted_sectors = sorted(sector_scores.items(), key=lambda x: x[1], reverse=True)
        return [s[0] for s in sorted_sectors[:5]]
    
    def _filter_news_by_sector(self, news_list: List[Dict], sector: str) -> List[Dict]:
        """筛选与板块相关的新闻"""
        sector_keywords = {
            'AI人工智能': ['AI', '人工智能', '大模型', 'ChatGPT', '算力', '智能', 'DeepSeek', '机器人'],
            '新能源': ['新能源', '光伏', '锂电', '储能', '电池', '充电桩', '风电'],
            '半导体芯片': ['芯片', '半导体', '光刻', '封装', '晶圆'],
            '医药生物': ['医药', '生物', '疫苗', '创新药', '医疗'],
            '消费': ['消费', '白酒', '食品', '零售', '餐饮'],
            '金融': ['银行', '保险', '券商', '证券', '金融'],
            '房地产': ['房地产', '地产', '楼市'],
            '军工': ['军工', '国防', '航空', '航天'],
            '汽车': ['汽车', '新能源车', '智能驾驶'],
            '低空经济': ['低空', '无人机', '飞行汽车'],
            '机器人': ['机器人', '人形机器人', '减速器'],
            '数据要素': ['数据', '数据要素', '数字经济'],
        }
        
        keywords = sector_keywords.get(sector, [sector])
        related = []
        
        for news in news_list:
            text = (news.get('title') or '') + (news.get('content') or '')
            for kw in keywords:
                if kw in text:
                    related.append(news)
                    break
        
        return related[:20]
    
    def _filter_topics_by_sector(self, topics: List[Dict], sector: str) -> List[Dict]:
        """筛选与板块相关的话题"""
        sector_keywords = {
            'AI人工智能': ['AI', '人工智能', '大模型', 'ChatGPT', '算力', '智能'],
            '新能源': ['新能源', '光伏', '锂电', '储能', '电池'],
            '半导体芯片': ['芯片', '半导体', '光刻'],
            '医药生物': ['医药', '生物', '疫苗', '医疗'],
            '消费': ['消费', '白酒', '食品', '餐饮'],
        }
        
        keywords = sector_keywords.get(sector, [sector])
        related = []
        
        for topic in topics:
            text = topic.get('topic', '')
            for kw in keywords:
                if kw in text:
                    related.append(topic)
                    break
        
        return related[:10]
    
    def _generate_multi_sector_summary(self, sector_analyses: List[Dict]) -> str:
        """生成多板块分析总结"""
        if not sector_analyses:
            return "暂无板块分析数据"
        
        # 按热度排序
        sorted_analyses = sorted(
            sector_analyses, 
            key=lambda x: x.get('heat_score', 0), 
            reverse=True
        )
        
        summary_parts = []
        summary_parts.append(f"共分析{len(sector_analyses)}个热门板块：")
        
        for i, analysis in enumerate(sorted_analyses[:3], 1):
            sector = analysis.get('sector_name', '未知')
            heat = analysis.get('heat_level', '中')
            outlook = analysis.get('short_term_outlook', '震荡')
            summary_parts.append(f"{i}. {sector}（热度{heat}，{outlook}）")
        
        return ' '.join(summary_parts)
    
    def _parse_json_response(self, response: str) -> Optional[Dict]:
        """解析JSON响应"""
        try:
            # 清理响应文本
            text = response.strip()
            
            # 处理markdown代码块
            if '```json' in text:
                text = text.split('```json')[1].split('```')[0]
            elif '```' in text:
                text = text.split('```')[1].split('```')[0]
            
            # 移除可能的推理过程
            if '【推理过程】' in text:
                parts = text.split('【推理过程】')
                text = parts[-1] if len(parts) > 1 else parts[0]
            
            # 查找JSON部分
            start = text.find('{')
            end = text.rfind('}') + 1
            
            if start >= 0 and end > start:
                json_text = text[start:end]
                return json.loads(json_text)
            
            return None
            
        except json.JSONDecodeError as e:
            logger.error(f"JSON解析失败: {e}")
            return None
    
    # ==================== 降级方法 ====================
    
    def _fallback_sector_analysis(self, hot_topics: List[Dict], 
                                   stock_news: List[Dict]) -> Dict:
        """板块分析降级方法"""
        # 基于关键词的简单分析
        sector_keywords = {
            'AI人工智能': ['AI', '人工智能', 'ChatGPT', '大模型', '算力', 'GPT'],
            '新能源': ['新能源', '锂电', '光伏', '风电', '储能', '充电桩'],
            '半导体': ['芯片', '半导体', '光刻机', '集成电路', '封测'],
            '医药生物': ['医药', '疫苗', '创新药', '医疗', '生物'],
            '消费': ['消费', '白酒', '食品', '零售', '餐饮'],
            '金融': ['银行', '保险', '券商', '金融', '信托'],
        }
        
        sector_hits = {}
        for topic in hot_topics:
            topic_text = topic.get('topic', '')
            heat = topic.get('heat', 0)
            for sector, keywords in sector_keywords.items():
                if any(kw in topic_text for kw in keywords):
                    if sector not in sector_hits:
                        sector_hits[sector] = 0
                    sector_hits[sector] += heat
        
        # 排序获取TOP板块
        sorted_sectors = sorted(sector_hits.items(), key=lambda x: x[1], reverse=True)
        
        benefited_sectors = [
            {
                'name': sector,
                'impact': '利好',
                'confidence': min(60, score // 2),
                'reason': f'热点话题关联度较高，热度得分{score}'
            }
            for sector, score in sorted_sectors[:5]
        ]
        
        return {
            'affected_sectors': benefited_sectors,
            'benefited_sectors': benefited_sectors,
            'damaged_sectors': [],
            'opportunity_assessment': '基于关键词匹配的简单分析，建议参考AI深度分析结果。',
            'key_points': ['AI分析不可用，使用降级方法'],
            'success': True,
            'fallback': True,
        }
    
    def _fallback_stock_recommend(self, hot_sectors: List[Dict]) -> Dict:
        """股票推荐降级方法"""
        return {
            'recommended_stocks': [],
            'overall_strategy': 'AI分析不可用，建议自行研究热门板块龙头股。',
            'risk_warning': '此为降级结果，请谨慎参考。',
            'success': True,
            'fallback': True,
        }
    
    def _fallback_risk_assess(self, flow_stage: str, 
                               sentiment_data: Dict, 
                               viral_k: float) -> Dict:
        """风险评估降级方法"""
        risk_score = 50
        risk_factors = []
        
        # 基于规则的简单风险评估
        if flow_stage in ['一致', 'consensus']:
            risk_score += 30
            risk_factors.append('流量处于一致阶段，可能是顶部')
        elif flow_stage in ['退潮', 'decline']:
            risk_score += 20
            risk_factors.append('流量正在退潮')
        
        sentiment_index = sentiment_data.get('sentiment_index', 50)
        if sentiment_index > 85:
            risk_score += 15
            risk_factors.append('情绪过度乐观')
        elif sentiment_index < 20:
            risk_score += 10
            risk_factors.append('情绪过度悲观')
        
        if viral_k > 1.5:
            risk_score += 15
            risk_factors.append(f'K值={viral_k}，流量指数型增长')
        
        risk_score = min(100, risk_score)
        
        if risk_score >= 80:
            risk_level = '极高'
        elif risk_score >= 60:
            risk_level = '高'
        elif risk_score >= 40:
            risk_level = '中等'
        elif risk_score >= 20:
            risk_level = '低'
        else:
            risk_level = '极低'
        
        return {
            'risk_level': risk_level,
            'risk_score': risk_score,
            'risk_factors': risk_factors,
            'opportunities': [],
            'analysis': '基于规则的简单风险评估，AI分析不可用。',
            'key_warning': '请谨慎参考，建议开启AI分析获取更准确的评估。',
            'success': True,
            'fallback': True,
        }
    
    def _fallback_investment_advice(self, risk_assess: Dict, 
                                     flow_data: Dict) -> Dict:
        """投资建议降级方法"""
        risk_level = risk_assess.get('risk_level', '中等')
        
        if risk_level in ['极高', '高']:
            advice = '回避'
            confidence = 70
            summary = '当前风险较高，建议保持观望或减仓。'
        elif risk_level == '中等':
            advice = '观望'
            confidence = 60
            summary = '市场状态中性，建议观望等待更明确的信号。'
        else:
            advice = '关注'
            confidence = 55
            summary = '风险较低，可关注热点板块机会。'
        
        return {
            'advice': advice,
            'confidence': confidence,
            'summary': summary,
            'action_plan': ['AI分析不可用，请自行判断'],
            'position_suggestion': '建议仓位不超过30%',
            'timing': '等待确认信号',
            'key_message': '此为降级结果，请谨慎参考。',
            'success': True,
            'fallback': True,
        }


# 全局实例
news_flow_agents = NewsFlowAgents()


# 测试代码
if __name__ == "__main__":
    print("=== 测试新闻流量智能分析代理 ===")
    
    # 检查AI是否可用
    if news_flow_agents.is_available():
        print("✅ AI客户端可用")
    else:
        print("⚠️ AI客户端不可用，将使用降级方法")
    
    # 模拟数据
    hot_topics = [
        {'topic': 'AI芯片', 'heat': 95, 'cross_platform': 5},
        {'topic': '新能源汽车', 'heat': 80, 'cross_platform': 4},
        {'topic': '涨停板', 'heat': 75, 'cross_platform': 3},
    ]
    
    stock_news = [
        {'platform_name': '东方财富', 'title': 'AI概念股集体大涨，龙头股涨停'},
        {'platform_name': '雪球', 'title': '新能源板块反弹，锂电池领涨'},
    ]
    
    flow_data = {
        'total_score': 650,
        'level': '高',
    }
    
    sentiment_data = {
        'sentiment': {'sentiment_index': 72, 'sentiment_class': '乐观'},
        'flow_stage': {'stage_name': '加速'},
    }
    
    # 运行板块分析
    print("\n--- 板块影响分析 ---")
    sector_result = news_flow_agents.sector_impact_agent(hot_topics, stock_news, flow_data)
    print(f"受益板块: {[s.get('name', '') for s in sector_result.get('benefited_sectors', [])]}")
    print(f"是否降级: {sector_result.get('fallback', False)}")
