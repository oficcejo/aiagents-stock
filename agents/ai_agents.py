from core.deepseek_client import DeepSeekClient
from typing import Dict, Any
import time
from core import config

class StockAnalysisAgents:
    """股票分析AI智能体集合"""
    
    def __init__(self, model=None):
        self.model = model or config.DEFAULT_MODEL_NAME
        self.deepseek_client = DeepSeekClient(model=self.model)
        
    def technical_analyst_agent(self, stock_info: Dict, stock_data: Any, indicators: Dict) -> Dict[str, Any]:
        """技术面分析智能体"""
        print("🔍 技术分析师正在分析中...")
        time.sleep(1)  # 模拟分析时间
        
        analysis = self.deepseek_client.technical_analysis(stock_info, stock_data, indicators)
        
        return {
            "agent_name": "技术分析师",
            "agent_role": "负责技术指标分析、图表形态识别、趋势判断",
            "analysis": analysis,
            "focus_areas": ["技术指标", "趋势分析", "支撑阻力", "交易信号"],
            "timestamp": time.strftime("%Y-%m-%d %H:%M:%S")
        }
    
    def fundamental_analyst_agent(self, stock_info: Dict, financial_data: Dict = None, quarterly_data: Dict = None) -> Dict[str, Any]:
        """基本面分析智能体"""
        print("📊 基本面分析师正在分析中...")
        
        # 如果有季报数据，显示数据来源
        if quarterly_data and quarterly_data.get('data_success'):
            income_count = quarterly_data.get('income_statement', {}).get('periods', 0) if quarterly_data.get('income_statement') else 0
            balance_count = quarterly_data.get('balance_sheet', {}).get('periods', 0) if quarterly_data.get('balance_sheet') else 0
            cash_flow_count = quarterly_data.get('cash_flow', {}).get('periods', 0) if quarterly_data.get('cash_flow') else 0
            print(f"   ✓ 已获取季报数据：利润表{income_count}期，资产负债表{balance_count}期，现金流量表{cash_flow_count}期")
        else:
            print("   ⚠ 未获取到季报数据，将基于基本财务数据分析")
        
        time.sleep(1)
        
        analysis = self.deepseek_client.fundamental_analysis(stock_info, financial_data, quarterly_data)
        
        return {
            "agent_name": "基本面分析师", 
            "agent_role": "负责公司财务分析、行业研究、估值分析",
            "analysis": analysis,
            "focus_areas": ["财务指标", "行业分析", "公司价值", "成长性", "季报趋势"],
            "quarterly_data": quarterly_data,  # 保存季报数据以供后续使用
            "timestamp": time.strftime("%Y-%m-%d %H:%M:%S")
        }
    
    def fund_flow_analyst_agent(self, stock_info: Dict, indicators: Dict, fund_flow_data: Dict = None) -> Dict[str, Any]:
        """资金面分析智能体"""
        print("💰 资金面分析师正在分析中...")
        
        # 如果有资金流向数据，显示数据来源
        if fund_flow_data and fund_flow_data.get('data_success'):
            print("   ✓ 已获取资金流向数据（akshare数据源）")
        else:
            print("   ⚠ 未获取到资金流向数据，将基于技术指标分析")
        
        time.sleep(1)
        
        analysis = self.deepseek_client.fund_flow_analysis(stock_info, indicators, fund_flow_data)
        
        return {
            "agent_name": "资金面分析师",
            "agent_role": "负责资金流向分析、主力行为研究、市场情绪判断", 
            "analysis": analysis,
            "focus_areas": ["资金流向", "主力动向", "市场情绪", "流动性"],
            "fund_flow_data": fund_flow_data,  # 保存资金流向数据以供后续使用
            "timestamp": time.strftime("%Y-%m-%d %H:%M:%S")
        }
    
    def risk_management_agent(self, stock_info: Dict, indicators: Dict, risk_data: Dict = None) -> Dict[str, Any]:
        """风险管理智能体（增强版）"""
        print("⚠️ 风险管理师正在评估中...")
        
        # 如果有风险数据，显示数据来源
        if risk_data and risk_data.get('data_success'):
            print("   ✓ 已获取问财风险数据（限售解禁、大股东减持、重要事件）")
        else:
            print("   ⚠ 未获取到风险数据，将基于基本信息分析")
        
        time.sleep(1)
        
        # 构建风险数据文本
        risk_data_text = ""
        if risk_data and risk_data.get('data_success'):
            # 使用格式化的风险数据
            from data_sources.risk_data_fetcher import RiskDataFetcher
            fetcher = RiskDataFetcher()
            risk_data_text = f"""

【实际风险数据】（来自问财）
{fetcher.format_risk_data_for_ai(risk_data)}

以上是通过问财（pywencai）获取的实际风险数据，请重点关注这些数据进行深度风险分析。
"""
        
        risk_prompt = f"""
作为资深风险管理专家，请基于以下信息进行全面深度的风险评估：

股票信息：
- 股票代码：{stock_info.get('symbol', 'N/A')}
- 股票名称：{stock_info.get('name', 'N/A')}
- 当前价格：{stock_info.get('current_price', 'N/A')}
- Beta系数：{stock_info.get('beta', 'N/A')}
- 52周最高：{stock_info.get('52_week_high', 'N/A')}
- 52周最低：{stock_info.get('52_week_low', 'N/A')}

技术指标：
- RSI：{indicators.get('rsi', 'N/A')}
- 布林带位置：当前价格相对于上下轨的位置
- 波动率指标等
{risk_data_text}

⚠️ 重要提示：以上风险数据是从问财（pywencai）实时查询的完整原始数据，请你：
1. 仔细解析每一条记录的所有字段信息
2. 识别数据中的关键风险点（时间、规模、频率、股东身份等）
3. 对数据进行深度分析，不要遗漏任何重要信息
4. 如果数据中有日期字段，要特别关注最近的记录和即将发生的事件
5. 如果数据中有金额/比例字段，要评估其规模和影响力
6. 基于实际数据给出量化的风险评估，而不是空泛的描述

请从以下角度进行全面的风险评估：

1. **限售解禁风险分析** ⭐ 重点
   - 解禁时间和规模评估
   - 解禁对股价的潜在冲击
   - 解禁股东类型分析（创始人/投资机构/其他）
   - 历史解禁后股价走势参考
   - 风险等级评定和应对建议

2. **股东减持风险分析** ⭐ 重点
   - 减持频率和力度评估
   - 减持股东身份和意图分析
   - 减持对市场信心的影响
   - 是否存在连续减持或集中减持
   - 风险警示和投资建议

3. **重要事件风险分析** ⭐ 重点
   - 识别可能影响股价的重大事件
   - 事件性质判断（利好/利空/中性）
   - 事件影响的时间维度（短期/中期/长期）
   - 事件的确定性和不确定性
   - 风险提示和关注要点

4. **市场风险（系统性风险）**
   - 宏观经济环境风险
   - 市场整体走势风险
   - Beta系数反映的市场敏感度
   - 系统性风险应对策略

5. **个股风险（非系统性风险）**
   - 公司基本面风险
   - 经营管理风险
   - 竞争力风险
   - 行业地位风险

6. **流动性风险**
   - 成交量和换手率分析
   - 买卖盘深度评估
   - 流动性枯竭风险
   - 大额交易影响评估

7. **波动性风险**
   - 价格波动幅度分析
   - 52周最高最低位分析
   - RSI等技术指标的风险提示
   - 波动率对投资的影响

8. **估值风险**
   - 当前估值水平评估
   - 市场预期和估值偏差
   - 估值过高风险警示

9. **行业风险**
   - 行业周期阶段
   - 行业竞争格局
   - 行业政策风险
   - 行业技术变革风险

10. **综合风险评定**
    - 风险等级评定（低/中/高）
    - 主要风险因素排序
    - 风险暴露时间窗口
    - 风险演变趋势判断

11. **风险控制建议** ⭐ 核心
    - 仓位控制建议（具体比例）
    - 止损位设置建议（具体价位）
    - 风险规避策略（什么情况下不建议投资）
    - 风险对冲方案（如果适用）
    - 持仓时间建议
    - 重点关注指标和信号

请基于实际数据进行客观、专业、严谨的风险评估，给出可操作的风险控制建议。
如果某些风险数据缺失，也要指出数据缺失本身可能带来的风险。
"""
        
        messages = [
            {"role": "system", "content": "你是一名资深的风险管理专家，具有20年以上的风险识别和控制经验，擅长全面评估各类投资风险，特别关注限售解禁、股东减持、重要事件等可能影响股价的风险因素。你擅长从海量原始数据中提取关键信息，进行深度解析和量化评估。"},
            {"role": "user", "content": risk_prompt}
        ]
        
        analysis = self.deepseek_client.call_api(messages, max_tokens=6000)
        
        return {
            "agent_name": "风险管理师",
            "agent_role": "负责风险识别、风险评估、风险控制策略制定",
            "analysis": analysis,
            "focus_areas": ["限售解禁风险", "股东减持风险", "重要事件风险", "风险识别", "风险量化", "风险控制", "资产配置"],
            "risk_data": risk_data,  # 保存风险数据以供后续使用
            "timestamp": time.strftime("%Y-%m-%d %H:%M:%S")
        }
    
    def market_sentiment_agent(self, stock_info: Dict, sentiment_data: Dict = None) -> Dict[str, Any]:
        """市场情绪分析智能体"""
        print("📈 市场情绪分析师正在分析中...")
        
        # 如果有市场情绪数据，显示数据来源
        if sentiment_data and sentiment_data.get('data_success'):
            print("   ✓ 已获取市场情绪数据（ARBR、换手率、涨跌停等）")
        else:
            print("   ⚠ 未获取到详细情绪数据，将基于基本信息分析")
        
        time.sleep(1)
        
        # 构建带有市场情绪数据的prompt
        sentiment_data_text = ""
        if sentiment_data and sentiment_data.get('data_success'):
            # 使用格式化的市场情绪数据
            from data_sources.market_sentiment_data import MarketSentimentDataFetcher
            fetcher = MarketSentimentDataFetcher()
            sentiment_data_text = f"""

【市场情绪实际数据】
{fetcher.format_sentiment_data_for_ai(sentiment_data)}

以上是通过akshare获取的实际市场情绪数据，请重点基于这些数据进行分析。
"""
        
        sentiment_prompt = f"""
作为市场情绪分析专家，请基于当前市场环境和实际数据对以下股票进行情绪分析：

股票信息：
- 股票代码：{stock_info.get('symbol', 'N/A')}
- 股票名称：{stock_info.get('name', 'N/A')}
- 行业：{stock_info.get('sector', 'N/A')}
- 细分行业：{stock_info.get('industry', 'N/A')}
{sentiment_data_text}

请从以下角度进行深度分析：

1. **ARBR情绪指标分析**
   - 详细解读AR和BR数值的含义
   - 分析当前市场人气和投机意愿
   - 判断是否存在超买超卖情况
   - 基于ARBR历史统计数据评估当前位置

2. **个股活跃度分析**
   - 换手率反映的资金活跃程度
   - 个股关注度和讨论热度
   - 与历史水平对比

3. **整体市场情绪**
   - 大盘涨跌情况对个股的影响
   - 市场涨跌家数反映的整体情绪
   - 涨跌停数量反映的市场热度
   - 恐慌贪婪指数的启示

4. **资金情绪**
   - 融资融券数据反映的看多看空情绪
   - 主力资金动向
   - 市场流动性状况

5. **情绪对股价影响**
   - 当前情绪对股价的支撑或压制作用
   - 情绪反转的可能性和信号
   - 短期情绪波动风险

6. **投资建议**
   - 基于市场情绪的操作建议
   - 情绪面的机会和风险提示

请确保分析基于实际数据，给出客观专业的市场情绪评估。
"""
        
        messages = [
            {"role": "system", "content": "你是一名专业的市场情绪分析师，擅长解读市场心理和投资者行为，善于利用ARBR等情绪指标进行分析。"},
            {"role": "user", "content": sentiment_prompt}
        ]
        
        analysis = self.deepseek_client.call_api(messages, max_tokens=4000)
        
        return {
            "agent_name": "市场情绪分析师",
            "agent_role": "负责市场情绪研究、投资者心理分析、热点追踪",
            "analysis": analysis,
            "focus_areas": ["ARBR指标", "市场情绪", "投资者心理", "资金活跃度", "恐慌贪婪指数"],
            "sentiment_data": sentiment_data,  # 保存市场情绪数据以供后续使用
            "timestamp": time.strftime("%Y-%m-%d %H:%M:%S")
        }
    
    def news_analyst_agent(self, stock_info: Dict, news_data: Dict = None) -> Dict[str, Any]:
        """新闻分析智能体"""
        print("📰 新闻分析师正在分析中...")
        
        # 如果有新闻数据，显示数据来源
        if news_data and news_data.get('data_success'):
            news_count = news_data.get('news_data', {}).get('count', 0) if news_data.get('news_data') else 0
            source = news_data.get('source', 'unknown')
            print(f"   ✓ 已从 {source} 获取 {news_count} 条新闻")
        else:
            print("   ⚠ 未获取到新闻数据，将基于基本信息分析")
        
        time.sleep(1)
        
        # 构建带有新闻数据的prompt
        news_text = ""
        if news_data and news_data.get('data_success'):
            # 使用格式化的新闻数据
            from data_sources.qstock_news_data import QStockNewsDataFetcher
            fetcher = QStockNewsDataFetcher()
            news_text = f"""

【最新新闻数据】
{fetcher.format_news_for_ai(news_data)}

以上是通过qstock获取的实际新闻数据，请重点基于这些数据进行分析。
"""
        
        news_prompt = f"""
作为专业的新闻分析师，请基于最新的新闻对以下股票进行深度分析：

股票信息：
- 股票代码：{stock_info.get('symbol', 'N/A')}
- 股票名称：{stock_info.get('name', 'N/A')}
- 行业：{stock_info.get('sector', 'N/A')}
- 细分行业：{stock_info.get('industry', 'N/A')}
{news_text}

请从以下角度进行深度分析：

1. **新闻概要**
   - 梳理最新的重要新闻
   - 总结核心要点和关键信息
   - 按重要性排序新闻

2. **新闻性质分析**
   - 分析新闻的性质（利好/利空/中性）
   - 评估新闻的可信度和权威性
   - 识别新闻来源和传播范围

3. **影响评估**
   - 评估新闻对股价的短期影响
   - 分析新闻对公司长期发展的影响
   - 判断新闻对行业的影响范围

4. **热点识别**
   - 识别市场关注的热点和焦点
   - 分析该股票在市场中的关注度
   - 评估舆论导向和市场情绪

5. **重大事件识别**
   - 识别可能影响股价的重大事件
   - 评估事件的紧迫性和重要性
   - 预判后续可能的发展和连锁反应

6. **市场反应预判**
   - 预测市场对新闻的可能反应
   - 判断是否存在预期差
   - 识别可能的交易机会窗口

7. **风险提示**
   - 识别新闻中的风险信号
   - 评估潜在的负面影响
   - 提示需要警惕的风险点

8. **投资建议**
   - 基于新闻的操作建议
   - 关键时间节点和观察点
   - 需要持续关注的事项

请确保分析客观、专业，重点关注对投资决策有实质性影响的内容。
如果某些新闻的重要性较低，可以简要提及或略过。
"""
        
        messages = [
            {"role": "system", "content": "你是一名专业的新闻分析师，擅长解读新闻事件、舆情分析，评估新闻对股价的影响。你具有敏锐的洞察力和丰富的市场经验。"},
            {"role": "user", "content": news_prompt}
        ]
        
        analysis = self.deepseek_client.call_api(messages, max_tokens=4000)
        
        return {
            "agent_name": "新闻分析师",
            "agent_role": "负责新闻事件分析、舆情研究、重大事件影响评估",
            "analysis": analysis,
            "focus_areas": ["新闻解读", "舆情分析", "事件影响", "市场反应", "投资机会"],
            "news_data": news_data,  # 保存新闻数据以供后续使用
            "timestamp": time.strftime("%Y-%m-%d %H:%M:%S")
        }
    
    def run_multi_agent_analysis(self, stock_info: Dict, stock_data: Any, indicators: Dict, 
                                 financial_data: Dict = None, fund_flow_data: Dict = None, 
                                 sentiment_data: Dict = None, news_data: Dict = None,
                                 quarterly_data: Dict = None, risk_data: Dict = None,
                                 enabled_analysts: Dict = None) -> Dict[str, Any]:
        """运行多智能体分析
        
        Args:
            enabled_analysts: 字典，指定哪些分析师参与分析
                例如: {'technical': True, 'fundamental': True, ...}
                如果为None，则运行所有分析师
        """
        # 如果未指定，默认所有分析师都参与
        if enabled_analysts is None:
            enabled_analysts = {
                'technical': True,
                'fundamental': True,
                'fund_flow': True,
                'risk': True,
                'sentiment': True,
                'news': True
            }
        
        print("🚀 启动多智能体股票分析系统...")
        print("=" * 50)
        
        # 显示参与分析的分析师
        active_analysts = [name for name, enabled in enabled_analysts.items() if enabled]
        print(f"📋 参与分析的分析师: {', '.join(active_analysts)}")
        print("=" * 50)
        
        # 并行运行各个分析师
        agents_results = {}
        
        # 技术面分析
        if enabled_analysts.get('technical', True):
            agents_results["technical"] = self.technical_analyst_agent(stock_info, stock_data, indicators)
        
        # 基本面分析
        if enabled_analysts.get('fundamental', True):
            agents_results["fundamental"] = self.fundamental_analyst_agent(stock_info, financial_data, quarterly_data)
        
        # 资金面分析（传入资金流向数据）
        if enabled_analysts.get('fund_flow', True):
            agents_results["fund_flow"] = self.fund_flow_analyst_agent(stock_info, indicators, fund_flow_data)
        
        # 风险管理分析（传入风险数据）
        if enabled_analysts.get('risk', True):
            agents_results["risk_management"] = self.risk_management_agent(stock_info, indicators, risk_data)
        
        # 市场情绪分析（传入市场情绪数据）
        if enabled_analysts.get('sentiment', False):
            agents_results["market_sentiment"] = self.market_sentiment_agent(stock_info, sentiment_data)
        
        # 新闻分析（传入新闻数据）
        if enabled_analysts.get('news', False):
            agents_results["news"] = self.news_analyst_agent(stock_info, news_data)
        
        print("✅ 所有已选择的分析师完成分析")
        print("=" * 50)
        
        return agents_results
    
    def conduct_team_discussion(self, agents_results: Dict[str, Any], stock_info: Dict) -> str:
        """进行团队讨论"""
        print("🤝 分析团队正在进行综合讨论...")
        time.sleep(2)
        
        # 收集参与分析的分析师名单和报告
        participants = []
        reports = []
        
        if "technical" in agents_results:
            participants.append("技术分析师")
            reports.append(f"【技术分析师报告】\n{agents_results['technical'].get('analysis', '')}")
        
        if "fundamental" in agents_results:
            participants.append("基本面分析师")
            reports.append(f"【基本面分析师报告】\n{agents_results['fundamental'].get('analysis', '')}")
        
        if "fund_flow" in agents_results:
            participants.append("资金面分析师")
            reports.append(f"【资金面分析师报告】\n{agents_results['fund_flow'].get('analysis', '')}")
        
        if "risk_management" in agents_results:
            participants.append("风险管理师")
            reports.append(f"【风险管理师报告】\n{agents_results['risk_management'].get('analysis', '')}")
        
        if "market_sentiment" in agents_results:
            participants.append("市场情绪分析师")
            reports.append(f"【市场情绪分析师报告】\n{agents_results['market_sentiment'].get('analysis', '')}")
        
        if "news" in agents_results:
            participants.append("新闻分析师")
            reports.append(f"【新闻分析师报告】\n{agents_results['news'].get('analysis', '')}")
        
        # 组合所有报告
        all_reports = "\n\n".join(reports)
        
        discussion_prompt = f"""
现在进行投资决策团队会议，参会人员包括：{', '.join(participants)}。

股票：{stock_info.get('name', 'N/A')} ({stock_info.get('symbol', 'N/A')})

各分析师报告：

{all_reports}

请模拟一场真实的投资决策会议讨论：
1. 各分析师观点的一致性和分歧
2. 不同维度分析的权重考量
3. 风险收益评估
4. 投资时机判断
5. 策略制定思路
6. 达成初步共识

请以对话形式展现讨论过程，体现专业团队的思辨过程。
注意：只讨论参与分析的分析师的观点。
"""
        
        messages = [
            {"role": "system", "content": "你需要模拟一场专业的投资团队讨论会议，体现不同角色的观点碰撞和最终共识形成。"},
            {"role": "user", "content": discussion_prompt}
        ]
        
        discussion_result = self.deepseek_client.call_api(messages, max_tokens=6000)
        
        print("✅ 团队讨论完成")
        return discussion_result
    
    def make_final_decision(self, discussion_result: str, stock_info: Dict, indicators: Dict) -> Dict[str, Any]:
        """制定最终投资决策"""
        print("📋 正在制定最终投资决策...")
        time.sleep(1)
        
        decision = self.deepseek_client.final_decision(discussion_result, stock_info, indicators)
        
        print("✅ 最终投资决策完成")
        return decision
