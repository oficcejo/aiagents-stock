from deepseek_client import DeepSeekClient
from typing import Dict, Any
import time

class StockAnalysisAgents:
    """股票分析AI智能体集合"""
    
    def __init__(self, model="deepseek-chat"):
        self.model = model
        self.deepseek_client = DeepSeekClient(model=model)
        
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
    
    def fundamental_analyst_agent(self, stock_info: Dict, financial_data: Dict = None) -> Dict[str, Any]:
        """基本面分析智能体"""
        print("📊 基本面分析师正在分析中...")
        time.sleep(1)
        
        analysis = self.deepseek_client.fundamental_analysis(stock_info, financial_data)
        
        return {
            "agent_name": "基本面分析师", 
            "agent_role": "负责公司财务分析、行业研究、估值分析",
            "analysis": analysis,
            "focus_areas": ["财务指标", "行业分析", "公司价值", "成长性"],
            "timestamp": time.strftime("%Y-%m-%d %H:%M:%S")
        }
    
    def fund_flow_analyst_agent(self, stock_info: Dict, indicators: Dict) -> Dict[str, Any]:
        """资金面分析智能体"""
        print("💰 资金面分析师正在分析中...")
        time.sleep(1)
        
        analysis = self.deepseek_client.fund_flow_analysis(stock_info, indicators)
        
        return {
            "agent_name": "资金面分析师",
            "agent_role": "负责资金流向分析、主力行为研究、市场情绪判断", 
            "analysis": analysis,
            "focus_areas": ["资金流向", "主力动向", "市场情绪", "流动性"],
            "timestamp": time.strftime("%Y-%m-%d %H:%M:%S")
        }
    
    def risk_management_agent(self, stock_info: Dict, indicators: Dict) -> Dict[str, Any]:
        """风险管理智能体"""
        print("⚠️ 风险管理师正在评估中...")
        time.sleep(1)
        
        risk_prompt = f"""
作为风险管理专家，请基于以下信息进行风险评估：

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

请从以下角度进行风险评估：
1. 市场风险（系统性风险）
2. 个股风险（非系统性风险）
3. 流动性风险
4. 波动性风险
5. 估值风险
6. 行业风险
7. 风险等级评定（低/中/高）
8. 风险控制建议

给出专业的风险评估报告。
"""
        
        messages = [
            {"role": "system", "content": "你是一名专业的风险管理专家，具有丰富的风险识别和控制经验。"},
            {"role": "user", "content": risk_prompt}
        ]
        
        analysis = self.deepseek_client.call_api(messages)
        
        return {
            "agent_name": "风险管理师",
            "agent_role": "负责风险识别、风险评估、风险控制策略制定",
            "analysis": analysis,
            "focus_areas": ["风险识别", "风险量化", "风险控制", "资产配置"],
            "timestamp": time.strftime("%Y-%m-%d %H:%M:%S")
        }
    
    def market_sentiment_agent(self, stock_info: Dict) -> Dict[str, Any]:
        """市场情绪分析智能体"""
        print("📈 市场情绪分析师正在分析中...")
        time.sleep(1)
        
        sentiment_prompt = f"""
作为市场情绪分析专家，请基于当前市场环境对以下股票进行情绪分析：

股票信息：
- 股票代码：{stock_info.get('symbol', 'N/A')}
- 股票名称：{stock_info.get('name', 'N/A')}
- 行业：{stock_info.get('sector', 'N/A')}
- 细分行业：{stock_info.get('industry', 'N/A')}

请从以下角度分析市场情绪：
1. 整体市场情绪（牛市/熊市/震荡市）
2. 行业板块情绪和热度
3. 个股关注度和讨论热度
4. 投资者情绪指标
5. 市场预期和共识
6. 消息面和事件驱动因素
7. 情绪对股价的影响评估
8. 情绪反转的可能性

结合当前宏观环境和市场热点，给出专业的市场情绪分析。
"""
        
        messages = [
            {"role": "system", "content": "你是一名专业的市场情绪分析师，擅长解读市场心理和投资者行为。"},
            {"role": "user", "content": sentiment_prompt}
        ]
        
        analysis = self.deepseek_client.call_api(messages)
        
        return {
            "agent_name": "市场情绪分析师",
            "agent_role": "负责市场情绪研究、投资者心理分析、热点追踪",
            "analysis": analysis,
            "focus_areas": ["市场情绪", "投资者心理", "热点板块", "消息面"],
            "timestamp": time.strftime("%Y-%m-%d %H:%M:%S")
        }
    
    def run_multi_agent_analysis(self, stock_info: Dict, stock_data: Any, indicators: Dict, financial_data: Dict = None) -> Dict[str, Any]:
        """运行多智能体分析"""
        print("🚀 启动多智能体股票分析系统...")
        print("=" * 50)
        
        # 并行运行各个分析师
        agents_results = {}
        
        # 技术面分析
        agents_results["technical"] = self.technical_analyst_agent(stock_info, stock_data, indicators)
        
        # 基本面分析
        agents_results["fundamental"] = self.fundamental_analyst_agent(stock_info, financial_data)
        
        # 资金面分析
        agents_results["fund_flow"] = self.fund_flow_analyst_agent(stock_info, indicators)
        
        # 风险管理分析
        agents_results["risk_management"] = self.risk_management_agent(stock_info, indicators)
        
        # 市场情绪分析
        agents_results["market_sentiment"] = self.market_sentiment_agent(stock_info)
        
        print("✅ 所有分析师完成分析")
        print("=" * 50)
        
        return agents_results
    
    def conduct_team_discussion(self, agents_results: Dict[str, Any], stock_info: Dict) -> str:
        """进行团队讨论"""
        print("🤝 分析团队正在进行综合讨论...")
        time.sleep(2)
        
        # 提取各分析师的报告
        technical_report = agents_results.get("technical", {}).get("analysis", "")
        fundamental_report = agents_results.get("fundamental", {}).get("analysis", "")
        fund_flow_report = agents_results.get("fund_flow", {}).get("analysis", "")
        risk_report = agents_results.get("risk_management", {}).get("analysis", "")
        sentiment_report = agents_results.get("market_sentiment", {}).get("analysis", "")
        
        discussion_prompt = f"""
现在进行投资决策团队会议，参会人员包括：技术分析师、基本面分析师、资金面分析师、风险管理师、市场情绪分析师。

股票：{stock_info.get('name', 'N/A')} ({stock_info.get('symbol', 'N/A')})

各分析师报告：

【技术分析师报告】
{technical_report}

【基本面分析师报告】 
{fundamental_report}

【资金面分析师报告】
{fund_flow_report}

【风险管理师报告】
{risk_report}

【市场情绪分析师报告】
{sentiment_report}

请模拟一场真实的投资决策会议讨论：
1. 各分析师观点的一致性和分歧
2. 不同维度分析的权重考量
3. 风险收益评估
4. 投资时机判断
5. 策略制定思路
6. 达成初步共识

请以对话形式展现讨论过程，体现专业团队的思辨过程。
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
