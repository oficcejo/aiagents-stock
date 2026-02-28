"""
智策AI智能体分析集群
包含四个专业分析师智能体
"""

from deepseek_client import DeepSeekClient
from typing import Dict, Any
import time
import config


class SectorStrategyAgents:
    """板块策略AI智能体集合"""
    
    def __init__(self, model=None):
        self.model = model or config.DEFAULT_MODEL_NAME
        self.deepseek_client = DeepSeekClient(model=self.model)
        print(f"[智策] AI智能体系统初始化 (模型: {self.model})")
    
    def macro_strategist_agent(self, market_data: Dict, news_data: list) -> Dict[str, Any]:
        """
        宏观策略师 - 分析宏观经济和新闻对板块的影响
        
        职责：
        - 分析国际国内新闻和宏观经济数据
        - 判断对整体市场和不同板块的潜在影响
        - 识别政策导向和宏观趋势
        """
        print("🌐 宏观策略师正在分析...")
        time.sleep(1)
        
        # 构建新闻摘要
        news_summary = ""
        if news_data:
            news_summary = "\n【重要财经新闻】\n"
            for idx, news in enumerate(news_data[:30], 1):
                news_summary += f"{idx}. [{news.get('publish_time', '')}] {news.get('title', '')}\n"
                if news.get('content'):
                    news_summary += f"   摘要: {news['content'][:200]}...\n"
        
        # 构建市场概况
        market_summary = ""
        if market_data:
            market_summary = f"""
【市场概况】
大盘指数:
"""
            if market_data.get("sh_index"):
                sh = market_data["sh_index"]
                market_summary += f"  上证指数: {sh['close']} ({sh['change_pct']:+.2f}%)\n"
            if market_data.get("sz_index"):
                sz = market_data["sz_index"]
                market_summary += f"  深证成指: {sz['close']} ({sz['change_pct']:+.2f}%)\n"
            if market_data.get("cyb_index"):
                cyb = market_data["cyb_index"]
                market_summary += f"  创业板指: {cyb['close']} ({cyb['change_pct']:+.2f}%)\n"
            
            if market_data.get("total_stocks"):
                market_summary += f"""
市场涨跌统计:
  上涨: {market_data['up_count']} ({market_data['up_ratio']:.1f}%)
  下跌: {market_data['down_count']}
  涨停: {market_data['limit_up']} | 跌停: {market_data['limit_down']}
"""
        
        prompt = f"""
你是一名资深的宏观策略分析师，拥有10年以上的市场研究经验，擅长从宏观经济和政策新闻中洞察市场趋势。

{market_summary}
{news_summary}

请基于以上信息，从宏观角度进行深度分析：

1. **宏观环境评估**
   - 当前宏观经济形势判断（经济周期位置）
   - 政策环境分析（货币政策、财政政策倾向）
   - 国际环境影响（地缘政治、全球经济）
   - 市场整体风险偏好评估

2. **新闻事件影响分析**
   - 识别对市场影响最大的3-5条重要新闻
   - 分析新闻的性质（利好/利空/中性）和影响范围
   - 判断新闻对不同板块的差异化影响
   - 识别政策导向和行业扶持重点

3. **行业板块影响预判**
   - 分析哪些板块受宏观环境影响最积极（看多）
   - 分析哪些板块面临宏观压力（看空）
   - 识别政策支持的重点行业
   - 预判资金可能流向的板块

4. **市场情绪和节奏**
   - 当前市场情绪状态（恐慌/谨慎/乐观/亢奋）
   - 大盘趋势判断（上涨/震荡/下跌）
   - 市场参与热情（活跃度、成交量）
   - 风险偏好变化趋势

5. **投资策略建议**
   - 当前宏观环境下的配置思路
   - 建议重点关注的板块（3-5个）
   - 建议规避的板块（2-3个）
   - 仓位管理建议

请给出专业、深入的宏观策略分析报告。
"""
        
        messages = [
            {"role": "system", "content": "你是一名资深的宏观策略分析师，擅长从宏观经济、政策和新闻事件中把握市场脉搏。"},
            {"role": "user", "content": prompt}
        ]
        
        analysis = self.deepseek_client.call_api(messages, max_tokens=4000)
        
        print("  ✓ 宏观策略师分析完成")
        
        return {
            "agent_name": "宏观策略师",
            "agent_role": "分析宏观经济、政策导向、新闻事件对市场和板块的影响",
            "analysis": analysis,
            "focus_areas": ["宏观经济", "政策解读", "新闻事件", "市场情绪", "行业轮动"],
            "timestamp": time.strftime("%Y-%m-%d %H:%M:%S")
        }
    
    def sector_diagnostician_agent(self, sectors_data: Dict, concepts_data: Dict, market_data: Dict) -> Dict[str, Any]:
        """
        板块诊断师 - 分析板块的走势、估值和基本面
        
        职责：
        - 深入分析特定板块的历史走势
        - 评估板块的估值水平
        - 分析板块的成长性和基本面因素
        """
        print("📊 板块诊断师正在分析...")
        time.sleep(1)
        
        # 构建行业板块数据
        sector_summary = ""
        if sectors_data:
            sorted_sectors = sorted(sectors_data.items(), key=lambda x: x[1]["change_pct"], reverse=True)
            
            sector_summary = f"""
【行业板块表现】(共 {len(sectors_data)} 个板块)

涨幅榜 TOP15:
"""
            for idx, (name, info) in enumerate(sorted_sectors[:15], 1):
                sector_summary += f"{idx}. {name}: {info['change_pct']:+.2f}% | 换手率: {info['turnover']:.2f}% | 领涨股: {info['top_stock']} ({info['top_stock_change']:+.2f}%) | 涨跌家数: {info['up_count']}/{info['down_count']}\n"
            
            sector_summary += f"""
跌幅榜 TOP10:
"""
            for idx, (name, info) in enumerate(sorted_sectors[-10:], 1):
                sector_summary += f"{idx}. {name}: {info['change_pct']:+.2f}% | 换手率: {info['turnover']:.2f}% | 领跌股: {info['top_stock']} ({info['top_stock_change']:+.2f}%) | 涨跌家数: {info['up_count']}/{info['down_count']}\n"
        
        # 构建概念板块数据
        concept_summary = ""
        if concepts_data:
            sorted_concepts = sorted(concepts_data.items(), key=lambda x: x[1]["change_pct"], reverse=True)
            
            concept_summary = f"""
【概念板块表现】(共 {len(concepts_data)} 个板块)

热门概念 TOP15:
"""
            for idx, (name, info) in enumerate(sorted_concepts[:15], 1):
                concept_summary += f"{idx}. {name}: {info['change_pct']:+.2f}% | 换手率: {info['turnover']:.2f}% | 领涨股: {info['top_stock']} ({info['top_stock_change']:+.2f}%)\n"
        
        prompt = f"""
你是一名资深的板块分析师，具有CFA资格和深厚的行业研究背景，擅长板块诊断和趋势判断。

【市场环境】
{self._format_market_overview(market_data)}

{sector_summary}

{concept_summary}

请基于以上数据，进行专业的板块诊断分析：

1. **板块强弱分析**
   - 识别当前最强势的5个板块（涨幅、换手率、领涨股表现综合考虑）
   - 识别当前最弱势的3个板块
   - 分析板块强弱的内在逻辑（基本面、资金面、情绪面）
   - 判断强势板块的持续性

2. **板块估值与位置**
   - 评估热门板块的估值合理性
   - 判断板块所处的位置（启动期/加速期/高位/调整期）
   - 识别估值洼地（低估且有潜力的板块）
   - 提示估值泡沫风险

3. **板块轮动特征**
   - 分析当前的板块轮动特征
   - 识别资金轮动的方向和节奏
   - 判断是否存在明显的板块切换信号
   - 预判下一个可能轮动的板块

4. **成长性与基本面**
   - 分析强势板块的成长驱动因素
   - 评估板块的中长期发展前景
   - 识别具有持续成长潜力的板块
   - 提示基本面恶化的风险板块

5. **技术形态分析**
   - 分析板块的技术走势特征
   - 识别突破、整理、调整等形态
   - 判断技术面的支撑和阻力
   - 提供技术性买卖点参考

6. **投资建议**
   - 推荐3-5个值得关注的板块（多头方向）
   - 提示2-3个需要规避的板块（空头方向）
   - 给出每个板块的投资逻辑和风险提示
   - 建议配置比例和持有周期

请给出专业、详细的板块诊断报告。
"""
        
        messages = [
            {"role": "system", "content": "你是一名资深的板块分析师，擅长板块趋势判断和投资价值评估。"},
            {"role": "user", "content": prompt}
        ]
        
        analysis = self.deepseek_client.call_api(messages, max_tokens=4000)
        
        print("  ✓ 板块诊断师分析完成")
        
        return {
            "agent_name": "板块诊断师",
            "agent_role": "深入分析板块走势、估值水平、基本面因素和成长性",
            "analysis": analysis,
            "focus_areas": ["板块走势", "估值分析", "基本面", "技术形态", "板块轮动"],
            "timestamp": time.strftime("%Y-%m-%d %H:%M:%S")
        }
    
    def fund_flow_analyst_agent(self, fund_flow_data: Dict, north_flow_data: Dict, sectors_data: Dict) -> Dict[str, Any]:
        """
        资金流向分析师 - 分析板块资金流向和主力行为
        
        职责：
        - 实时跟踪主力资金在板块间的流动
        - 分析北向资金的板块偏好
        - 判断资金进攻或撤离的方向
        """
        print("💰 资金流向分析师正在分析...")
        time.sleep(1)
        
        # 构建资金流向数据
        fund_flow_summary = ""
        if fund_flow_data and fund_flow_data.get("today"):
            flow_list = fund_flow_data["today"]
            
            # 净流入前15
            sorted_inflow = sorted(flow_list, key=lambda x: x["main_net_inflow"], reverse=True)
            fund_flow_summary = f"""
【板块资金流向】(更新时间: {fund_flow_data.get('update_time', 'N/A')})

主力资金净流入 TOP15:
"""
            for idx, item in enumerate(sorted_inflow[:15], 1):
                fund_flow_summary += f"{idx}. {item['sector']}: {item['main_net_inflow']:.2f}万 ({item['main_net_inflow_pct']:+.2f}%) | 涨跌: {item['change_pct']:+.2f}% | 超大单: {item['super_large_net_inflow']:.2f}万\n"
            
            # 净流出前10
            sorted_outflow = sorted(flow_list, key=lambda x: x["main_net_inflow"])
            fund_flow_summary += f"""
主力资金净流出 TOP10:
"""
            for idx, item in enumerate(sorted_outflow[:10], 1):
                fund_flow_summary += f"{idx}. {item['sector']}: {item['main_net_inflow']:.2f}万 ({item['main_net_inflow_pct']:+.2f}%) | 涨跌: {item['change_pct']:+.2f}%\n"
        
        # 构建北向资金数据
        north_summary = ""
        if north_flow_data:
            north_summary = f"""
【北向资金】
日期: {north_flow_data.get('date', 'N/A')}
今日北向资金净流入: {north_flow_data.get('north_net_inflow', 0):.2f} 万元
  沪股通净流入: {north_flow_data.get('hgt_net_inflow', 0):.2f} 万元
  深股通净流入: {north_flow_data.get('sgt_net_inflow', 0):.2f} 万元
"""
            if north_flow_data.get('history'):
                north_summary += "\n近10日北向资金流向:\n"
                for item in north_flow_data['history'][:10]:
                    north_summary += f"  {item['date']}: {item['net_inflow']:.2f}万\n"
        
        prompt = f"""
你是一名资深的资金流向分析师，拥有15年的市场资金研究经验，擅长从资金流向中洞察主力意图和市场趋势。

{fund_flow_summary}

{north_summary}

请基于以上资金流向数据，进行深入的板块资金分析：

1. **主力资金流向分析** ⭐ 核心
   - 识别主力资金重点流入的板块（TOP5）
   - 分析主力资金大幅流出的板块（TOP3）
   - 判断资金流向的集中度（集中/分散）
   - 评估资金流向的持续性和强度

2. **资金类型分析**
   - 超大单资金的流向特征（机构大资金）
   - 大单资金的流向特征（主力资金）
   - 中小单资金的流向（散户资金）
   - 主力与散户的博弈特征

3. **量价配合分析**
   - 分析资金流入与板块涨幅的匹配度
   - 识别"资金流入+板块上涨"的强势板块
   - 识别"资金流入+板块下跌"的低吸信号
   - 识别"资金流出+板块上涨"的出货警示
   - 识别"资金流出+板块下跌"的弱势板块

4. **北向资金偏好**
   - 分析北向资金的流向趋势
   - 判断外资对A股的态度（积极/观望/撤离）
   - 识别北向资金偏好的板块
   - 评估北向资金的指示意义

5. **板块资金轮动**
   - 识别资金从哪些板块流出
   - 识别资金流向哪些板块
   - 分析板块资金轮动的节奏和方向
   - 预判下一个资金可能流入的板块

6. **主力操作意图研判**
   - 判断主力是否在积极建仓某些板块
   - 识别主力可能在出货的板块
   - 分析主力的操作风格（激进/稳健）
   - 评估主力对后市的态度

7. **投资策略建议**
   - 基于资金流向，推荐3-5个强势板块
   - 提示2-3个资金流出的风险板块
   - 给出板块配置的优先级
   - 提供跟随主力的操作建议

8. **风险提示**
   - 识别资金面的潜在风险
   - 提示可能的资金陷阱
   - 评估市场流动性状况

请给出专业、深度的资金流向分析报告。
"""
        
        messages = [
            {"role": "system", "content": "你是一名资深的资金流向分析师，擅长从资金数据中洞察主力意图和市场趋势。"},
            {"role": "user", "content": prompt}
        ]
        
        analysis = self.deepseek_client.call_api(messages, max_tokens=4000)
        
        print("  ✓ 资金流向分析师分析完成")
        
        return {
            "agent_name": "资金流向分析师",
            "agent_role": "跟踪板块资金流向，分析主力行为和资金轮动",
            "analysis": analysis,
            "focus_areas": ["资金流向", "主力行为", "北向资金", "板块轮动", "量价配合"],
            "timestamp": time.strftime("%Y-%m-%d %H:%M:%S")
        }
    
    def market_sentiment_decoder_agent(self, market_data: Dict, sectors_data: Dict, concepts_data: Dict) -> Dict[str, Any]:
        """
        市场情绪解码员 - 从多维度解读市场情绪
        
        职责：
        - 量化市场情绪指标
        - 识别过度乐观或恐慌信号
        - 评估板块热度和市场关注度
        """
        print("📈 市场情绪解码员正在分析...")
        time.sleep(1)
        
        # 构建市场情绪指标
        sentiment_summary = ""
        if market_data:
            sentiment_summary = f"""
【市场情绪指标】

涨跌统计:
  总股票数: {market_data.get('total_stocks', 0)}
  上涨股票: {market_data.get('up_count', 0)} ({market_data.get('up_ratio', 0):.1f}%)
  下跌股票: {market_data.get('down_count', 0)}
  涨停数: {market_data.get('limit_up', 0)}
  跌停数: {market_data.get('limit_down', 0)}

大盘表现:
"""
            if market_data.get("sh_index"):
                sh = market_data["sh_index"]
                sentiment_summary += f"  上证指数: {sh['close']} ({sh['change_pct']:+.2f}%)\n"
            if market_data.get("sz_index"):
                sz = market_data["sz_index"]
                sentiment_summary += f"  深证成指: {sz['close']} ({sz['change_pct']:+.2f}%)\n"
            if market_data.get("cyb_index"):
                cyb = market_data["cyb_index"]
                sentiment_summary += f"  创业板指: {cyb['close']} ({cyb['change_pct']:+.2f}%)\n"
        
        # 板块热度分析
        hot_sectors = ""
        if sectors_data:
            sorted_sectors = sorted(sectors_data.items(), key=lambda x: abs(x[1]["change_pct"]), reverse=True)
            hot_sectors = f"""
【板块热度排行】(按涨跌幅绝对值排序)

最活跃板块 TOP10:
"""
            for idx, (name, info) in enumerate(sorted_sectors[:10], 1):
                hot_sectors += f"{idx}. {name}: {info['change_pct']:+.2f}% | 换手率: {info['turnover']:.2f}% | 涨跌家数: {info['up_count']}/{info['down_count']}\n"
        
        # 概念热度
        hot_concepts = ""
        if concepts_data:
            sorted_concepts = sorted(concepts_data.items(), key=lambda x: abs(x[1]["change_pct"]), reverse=True)
            hot_concepts = f"""
【概念热度排行】

最热概念 TOP10:
"""
            for idx, (name, info) in enumerate(sorted_concepts[:10], 1):
                hot_concepts += f"{idx}. {name}: {info['change_pct']:+.2f}% | 换手率: {info['turnover']:.2f}%\n"
        
        prompt = f"""
你是一名资深的市场情绪分析师，拥有心理学和金融学双重背景，擅长从市场数据中解读投资者情绪和市场心理。

{sentiment_summary}

{hot_sectors}

{hot_concepts}

请基于以上数据，进行深入的市场情绪分析：

1. **整体市场情绪评估**
   - 量化当前市场情绪（0-100分，0=极度恐慌，50=中性，100=极度亢奋）
   - 判断市场情绪状态（恐慌/谨慎/中性/乐观/亢奋）
   - 分析情绪的强度和持续性
   - 对比历史情绪水平

2. **赚钱效应分析**
   - 评估市场的赚钱效应（强/中/弱）
   - 分析上涨股票占比和涨停数量
   - 判断是否存在明显的板块效应
   - 评估散户参与热情

3. **市场热点分析**
   - 识别当前最热门的3-5个板块/概念
   - 分析热点的形成原因和逻辑
   - 评估热点的持续性和扩散性
   - 判断是否存在炒作泡沫

4. **恐慌贪婪指数**
   - 综合判断市场的贪婪或恐慌程度
   - 分析涨跌停数量反映的情绪极端
   - 识别情绪拐点信号
   - 提示过度贪婪或过度恐慌的风险

5. **板块情绪分化**
   - 分析不同板块的情绪差异
   - 识别高情绪板块和低情绪板块
   - 判断情绪分化是否合理
   - 预判情绪可能扩散的方向

6. **换手率与活跃度**
   - 分析整体市场和板块的换手率
   - 评估市场活跃度（活跃/一般/低迷）
   - 判断资金参与意愿
   - 识别异常活跃的板块

7. **情绪对市场的影响**
   - 分析当前情绪对大盘的支撑或压制
   - 判断情绪反转的可能性和时机
   - 评估情绪驱动的交易机会
   - 提示情绪面的风险

8. **投资策略建议**
   - 基于市场情绪给出操作建议
   - 推荐情绪支持的板块（2-3个）
   - 提示情绪透支的风险板块（1-2个）
   - 给出仓位管理建议

请给出专业、客观的市场情绪分析报告，避免主观臆测。
"""
        
        messages = [
            {"role": "system", "content": "你是一名资深的市场情绪分析师，擅长从市场数据中解读投资者情绪和市场心理。"},
            {"role": "user", "content": prompt}
        ]
        
        analysis = self.deepseek_client.call_api(messages, max_tokens=4000)
        
        print("  ✓ 市场情绪解码员分析完成")
        
        return {
            "agent_name": "市场情绪解码员",
            "agent_role": "量化市场情绪，识别恐慌贪婪信号，评估板块热度",
            "analysis": analysis,
            "focus_areas": ["市场情绪", "赚钱效应", "热点识别", "恐慌贪婪", "活跃度"],
            "timestamp": time.strftime("%Y-%m-%d %H:%M:%S")
        }
    
    def _format_market_overview(self, market_data):
        """格式化市场概况"""
        if not market_data:
            return "暂无市场数据"
        
        text = ""
        if market_data.get("sh_index"):
            sh = market_data["sh_index"]
            text += f"上证指数: {sh['close']} ({sh['change_pct']:+.2f}%)\n"
        if market_data.get("sz_index"):
            sz = market_data["sz_index"]
            text += f"深证成指: {sz['close']} ({sz['change_pct']:+.2f}%)\n"
        if market_data.get("total_stocks"):
            text += f"涨跌统计: 上涨{market_data['up_count']}只({market_data['up_ratio']:.1f}%)，下跌{market_data['down_count']}只\n"
        
        return text


# 测试函数
if __name__ == "__main__":
    print("=" * 60)
    print("测试智策AI智能体系统")
    print("=" * 60)
    
    # 创建模拟数据
    test_market_data = {
        "sh_index": {"close": 3200, "change_pct": 0.5},
        "sz_index": {"close": 10500, "change_pct": 0.8},
        "total_stocks": 5000,
        "up_count": 3000,
        "up_ratio": 60.0,
        "down_count": 2000
    }
    
    test_news = [
        {"title": "央行宣布降准0.5个百分点", "content": "为支持实体经济发展...", "publish_time": "2024-01-15 10:00"}
    ]
    
    agents = SectorStrategyAgents()
    
    # 测试宏观策略师
    print("\n测试宏观策略师...")
    result = agents.macro_strategist_agent(test_market_data, test_news)
    print(f"分析师: {result['agent_name']}")
    print(f"分析内容长度: {len(result['analysis'])} 字符")

