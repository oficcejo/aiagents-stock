"""
智瞰龙虎AI分析师集群
专注于龙虎榜数据的多维度分析
"""

from deepseek_client import DeepSeekClient
from typing import Dict, Any, List
import time


class LonghubangAgents:
    """龙虎榜AI分析师集合"""
    
    def __init__(self, model="deepseek-chat"):
        self.model = model
        self.deepseek_client = DeepSeekClient(model=model)
        print(f"[智瞰龙虎] AI分析师系统初始化 (模型: {model})")
    
    def youzi_behavior_analyst(self, longhubang_data: str, summary: Dict) -> Dict[str, Any]:
        """
        游资行为分析师 - 分析游资操作特征和意图
        
        职责：
        - 识别活跃游资及其操作风格
        - 分析游资席位的进出特征
        - 研判游资对个股的态度
        """
        print("🎯 游资行为分析师正在分析...")
        time.sleep(1)
        
        # 构建游资统计信息
        youzi_info = ""
        if summary.get('top_youzi'):
            youzi_info = "\n【活跃游资统计】\n"
            for idx, (name, amount) in enumerate(list(summary['top_youzi'].items())[:15], 1):
                youzi_info += f"{idx}. {name}: 净流入 {amount:,.2f} 元\n"
        
        prompt = f"""
你是一名资深的游资研究专家，拥有10年以上的龙虎榜数据分析经验，深谙各路游资的操作风格和盈利模式。

【龙虎榜数据概况】
记录总数: {summary.get('total_records', 0)}
涉及股票: {summary.get('total_stocks', 0)} 只
涉及游资: {summary.get('total_youzi', 0)} 个
总买入金额: {summary.get('total_buy_amount', 0):,.2f} 元
总卖出金额: {summary.get('total_sell_amount', 0):,.2f} 元
净流入金额: {summary.get('total_net_inflow', 0):,.2f} 元

{youzi_info}

{longhubang_data[:8000]}

请基于以上龙虎榜数据，进行深入的游资行为分析：

1. **活跃游资识别与画像** ⭐ 核心
   - 识别当前最活跃的5-8个游资席位
   - 分析每个游资的操作风格（激进型/稳健型/超短型/波段型）
   - 评估游资的胜率和成功案例
   - 识别知名"牛散"和"游资大佬"

2. **游资操作特征分析**
   - 分析游资的买入特征（追高/低吸/打板/潜伏）
   - 分析游资的卖出特征（一日游/持有周期/止盈止损）
   - 识别游资的联合操作和接力特征
   - 判断游资是否存在抱团现象

3. **游资目标股票分析**
   - 分析游资重点关注的股票（前10只）
   - 识别游资集体看好的股票（多席位介入）
   - 分析游资选股的共性特征（题材/概念/技术形态）
   - 评估游资介入股票的后续爆发力

4. **游资进出节奏**
   - 判断游资整体是进攻还是防守状态
   - 分析游资对热点的跟随速度
   - 识别游资撤退的信号和板块
   - 评估游资的持续作战能力

5. **游资与题材的匹配**
   - 分析游资偏好的题材和概念
   - 识别游资正在炒作的热点
   - 判断题材的炒作周期位置
   - 预判下一个游资可能关注的题材

6. **风险与机会提示**
   - 识别游资可能设置的"陷阱"股票
   - 提示游资一致性过高的风险（容易崩盘）
   - 发现游资刚开始介入的潜力股
   - 评估跟随游资的风险收益比

7. **投资策略建议**
   - 推荐3-5只游资看好的潜力股票
   - 提示2-3只游资可能出货的风险股票
   - 给出跟随游资的操作建议
   - 提供仓位和止损建议

请给出专业、实战性强的游资行为分析报告。
"""
        
        messages = [
            {"role": "system", "content": "你是一名资深的游资研究专家，擅长从龙虎榜数据中洞察游资意图和操作手法。"},
            {"role": "user", "content": prompt}
        ]
        
        analysis = self.deepseek_client.call_api(messages, max_tokens=4000)
        
        print("  ✓ 游资行为分析师分析完成")
        
        return {
            "agent_name": "游资行为分析师",
            "agent_role": "分析游资操作特征、意图和目标股票",
            "analysis": analysis,
            "focus_areas": ["游资画像", "操作风格", "目标股票", "进出节奏", "题材偏好"],
            "timestamp": time.strftime("%Y-%m-%d %H:%M:%S")
        }
    
    def stock_potential_analyst(self, longhubang_data: str, summary: Dict) -> Dict[str, Any]:
        """
        个股潜力分析师 - 从龙虎榜数据挖掘潜力股
        
        职责：
        - 分析上榜股票的资金动向
        - 评估股票的上涨潜力
        - 识别次日大概率上涨的股票
        """
        print("📈 个股潜力分析师正在分析...")
        time.sleep(1)
        
        # 构建股票统计信息
        stock_info = ""
        if summary.get('top_stocks'):
            stock_info = "\n【热门股票统计】\n"
            for idx, stock in enumerate(summary['top_stocks'][:20], 1):
                stock_info += f"{idx}. {stock['name']}({stock['code']}): 净流入 {stock['net_inflow']:,.2f} 元\n"
        
        prompt = f"""
你是一名资深的个股研究专家和短线交易高手，精通技术分析和资金分析，擅长从龙虎榜中挖掘短期爆发股。

【龙虎榜数据概况】
记录总数: {summary.get('total_records', 0)}
涉及股票: {summary.get('total_stocks', 0)} 只
涉及游资: {summary.get('total_youzi', 0)} 个

{stock_info}

{longhubang_data[:8000]}

请基于以上龙虎榜数据，进行深入的个股潜力分析：

1. **次日大概率上涨股票挖掘** ⭐⭐⭐ 最核心
   - 识别5-8只次日大概率上涨的股票
   - 详细分析每只股票的上涨逻辑（资金面、技术面、题材面）
   - 评估每只股票的上涨空间和确定性（高/中/低）
   - 给出具体的买入价位和止损位

2. **资金流向强度分析**
   - 识别主力资金大幅流入的股票（净买入前10）
   - 分析资金流入的集中度和持续性
   - 识别多席位联合买入的股票（强烈看好信号）
   - 判断资金流入是真实买入还是诱多

3. **技术形态评估**
   - 分析上榜股票的技术位置（突破/回调/整理）
   - 识别处于启动阶段的股票
   - 评估股票的技术支撑和阻力
   - 判断股票的短期走势方向

4. **题材与概念分析**
   - 识别当前最热门的题材和概念
   - 分析题材的持续性和爆发力
   - 找出题材龙头和低位补涨股
   - 预判题材的炒作周期

5. **游资持仓分析**
   - 识别游资重仓持有的股票
   - 分析游资的一致性程度
   - 判断游资是建仓、加仓还是出货
   - 评估游资持仓的稳定性

6. **上榜类型分析**
   - 分析日榜和三日榜的差异
   - 识别连续上榜的股票（关注度高）
   - 判断上榜的性质（放量突破/涨停板/异常波动）
   - 评估不同上榜类型的后续表现概率

7. **风险股票识别**
   - 识别3-5只高风险股票（游资可能出货）
   - 分析卖出金额大于买入金额的股票
   - 提示游资一日游后撤离的股票
   - 警示技术面走坏的股票

8. **操作策略建议**
   - 推荐5-8只次日重点关注的股票（按优先级排序）
   - 给出每只股票的买入逻辑、买入价位、目标价位、止损价位
   - 提供仓位分配建议
   - 给出持有周期建议（超短/短线/波段）

请给出专业、实战、具有可操作性的个股潜力分析报告。务必重点分析次日大概率上涨的股票！
"""
        
        messages = [
            {"role": "system", "content": "你是一名资深的个股研究专家和短线交易高手，擅长从龙虎榜中挖掘短期爆发股。"},
            {"role": "user", "content": prompt}
        ]
        
        analysis = self.deepseek_client.call_api(messages, max_tokens=4000)
        
        print("  ✓ 个股潜力分析师分析完成")
        
        return {
            "agent_name": "个股潜力分析师",
            "agent_role": "挖掘次日大概率上涨的潜力股票",
            "analysis": analysis,
            "focus_areas": ["潜力股挖掘", "资金流向", "技术形态", "题材概念", "操作策略"],
            "timestamp": time.strftime("%Y-%m-%d %H:%M:%S")
        }
    
    def theme_tracker_analyst(self, longhubang_data: str, summary: Dict) -> Dict[str, Any]:
        """
        题材追踪分析师 - 分析龙虎榜中的热点题材
        
        职责：
        - 识别当前热点题材和概念
        - 分析题材的炒作周期
        - 预判题材的持续性
        """
        print("🔥 题材追踪分析师正在分析...")
        time.sleep(1)
        
        # 构建概念统计信息
        concept_info = ""
        if summary.get('hot_concepts'):
            concept_info = "\n【热门概念统计】\n"
            for idx, (concept, count) in enumerate(list(summary['hot_concepts'].items())[:20], 1):
                concept_info += f"{idx}. {concept}: 出现 {count} 次\n"
        
        prompt = f"""
你是一名资深的题材研究专家，拥有敏锐的市场嗅觉，擅长从龙虎榜数据中捕捉题材热点和板块轮动机会。

【龙虎榜数据概况】
记录总数: {summary.get('total_records', 0)}
涉及股票: {summary.get('total_stocks', 0)} 只

{concept_info}

{longhubang_data[:8000]}

请基于以上龙虎榜数据，进行深入的题材追踪分析：

1. **热点题材识别** ⭐ 核心
   - 识别当前最热门的5-8个题材/概念
   - 分析每个题材的核心逻辑和催化剂
   - 评估题材的市场关注度和参与度
   - 判断题材是主流还是伪题材

2. **题材炒作周期分析**
   - 判断每个题材所处的炒作周期（萌芽期/爆发期/高潮期/退潮期）
   - 分析题材的爆发力和持续性
   - 识别即将启动的新题材（萌芽期）
   - 提示即将退潮的老题材（高潮期）

3. **题材龙头与梯队**
   - 识别每个题材的龙头股（1-2只）
   - 找出题材的跟风股和补涨股
   - 分析龙头的地位是否稳固
   - 判断是否存在龙头切换

4. **游资对题材的态度**
   - 分析游资重点炒作的题材
   - 判断游资对题材的认同度（一致/分歧）
   - 识别游资集体进攻的题材（强势题材）
   - 发现游资开始撤离的题材（弱势题材）

5. **题材轮动特征**
   - 分析题材之间的轮动关系
   - 识别强势题材和弱势题材
   - 判断资金从哪个题材流向哪个题材
   - 预判下一个可能启动的题材

6. **题材与市场环境匹配度**
   - 分析题材是否符合当前市场风格
   - 评估题材的政策支持度
   - 判断题材的基本面支撑
   - 识别纯粹炒作的题材

7. **题材风险评估**
   - 识别过度炒作的题材（泡沫风险）
   - 提示游资分歧加大的题材
   - 警示题材逻辑破裂的风险
   - 评估题材的回调风险

8. **投资策略建议**
   - 推荐3-5个值得关注的强势题材
   - 每个题材推荐1-2只最优标的
   - 提供题材投资的时机选择
   - 给出题材仓位和持有周期建议

请给出专业、前瞻性强的题材追踪分析报告。
"""
        
        messages = [
            {"role": "system", "content": "你是一名资深的题材研究专家，擅长从龙虎榜数据中捕捉题材热点和投资机会。"},
            {"role": "user", "content": prompt}
        ]
        
        analysis = self.deepseek_client.call_api(messages, max_tokens=4000)
        
        print("  ✓ 题材追踪分析师分析完成")
        
        return {
            "agent_name": "题材追踪分析师",
            "agent_role": "识别热点题材，分析炒作周期，预判轮动方向",
            "analysis": analysis,
            "focus_areas": ["热点题材", "炒作周期", "龙头梯队", "题材轮动", "风险评估"],
            "timestamp": time.strftime("%Y-%m-%d %H:%M:%S")
        }
    
    def risk_control_specialist(self, longhubang_data: str, summary: Dict) -> Dict[str, Any]:
        """
        风险控制专家 - 识别龙虎榜中的风险信号
        
        职责：
        - 识别高风险股票和陷阱
        - 分析游资出货信号
        - 提供风险管理建议
        """
        print("⚠️ 风险控制专家正在分析...")
        time.sleep(1)
        
        prompt = f"""
你是一名资深的风险控制专家和反向思维大师，拥有20年的市场风险管理经验，擅长识别龙虎榜中的风险信号和资金陷阱。

【龙虎榜数据概况】
记录总数: {summary.get('total_records', 0)}
涉及股票: {summary.get('total_stocks', 0)} 只
涉及游资: {summary.get('total_youzi', 0)} 个
总买入金额: {summary.get('total_buy_amount', 0):,.2f} 元
总卖出金额: {summary.get('total_sell_amount', 0):,.2f} 元
净流入金额: {summary.get('total_net_inflow', 0):,.2f} 元

{longhubang_data[:8000]}

请基于以上龙虎榜数据，进行全面的风险分析：

1. **高风险股票识别** ⭐ 核心
   - 识别5-8只高风险股票（次日大概率下跌）
   - 分析每只股票的风险点（游资出货/技术破位/题材退潮）
   - 评估每只股票的风险等级（高/中/低）
   - 给出规避建议和止损位

2. **游资出货信号识别**
   - 识别卖出金额远大于买入金额的股票
   - 分析游资"一日游"后撤离的股票
   - 识别游资集体出货的股票（多席位卖出）
   - 判断游资出货是正常获利了结还是预期恶化

3. **资金陷阱识别**
   - 识别"虚假放量"的股票（实为对倒出货）
   - 分析"高位放量滞涨"的股票
   - 识别"拉高出货"的经典手法
   - 提示"击鼓传花"的末期信号

4. **题材风险评估**
   - 识别过度炒作的题材（泡沫严重）
   - 分析题材逻辑破裂的风险
   - 提示题材退潮的信号
   - 评估题材的持续性风险

5. **技术面风险提示**
   - 识别技术面走坏的股票（破位/跌破支撑）
   - 分析高位震荡的股票（出货迹象）
   - 提示连续上涨后的回调风险
   - 评估短期超买的股票

6. **情绪风险评估**
   - 识别市场情绪过热的信号
   - 分析游资一致性过高的风险（易崩盘）
   - 提示跟风盘过多的股票（接盘侠风险）
   - 评估短期投机氛围的风险

7. **系统性风险提示**
   - 分析整体龙虎榜数据反映的市场风险
   - 评估游资整体是进攻还是防守
   - 判断市场风险偏好的变化
   - 提示可能的系统性调整风险

8. **风险管理建议**
   - 提供仓位控制建议（重仓/轻仓/空仓）
   - 给出止损止盈的纪律要求
   - 建议规避的板块和题材
   - 提供风险对冲策略

请给出专业、严谨、保守的风险控制报告，宁可错过，不可做错。
"""
        
        messages = [
            {"role": "system", "content": "你是一名资深的风险控制专家，擅长识别龙虎榜中的风险信号和资金陷阱。"},
            {"role": "user", "content": prompt}
        ]
        
        analysis = self.deepseek_client.call_api(messages, max_tokens=4000)
        
        print("  ✓ 风险控制专家分析完成")
        
        return {
            "agent_name": "风险控制专家",
            "agent_role": "识别高风险股票、游资出货信号和市场陷阱",
            "analysis": analysis,
            "focus_areas": ["高风险股票", "出货信号", "资金陷阱", "题材风险", "风险管理"],
            "timestamp": time.strftime("%Y-%m-%d %H:%M:%S")
        }
    
    def chief_strategist(self, all_analyses: List[Dict]) -> Dict[str, Any]:
        """
        首席策略师 - 综合所有分析师的意见，给出最终投资建议
        
        职责：
        - 整合多维度分析结果
        - 给出最终推荐股票清单
        - 提供具体操作策略
        """
        print("👔 首席策略师正在综合分析...")
        time.sleep(1)
        
        # 整合所有分析师的分析结果
        analyses_text = ""
        for analysis in all_analyses:
            analyses_text += f"\n{'='*60}\n"
            analyses_text += f"【{analysis['agent_name']}】分析报告\n"
            analyses_text += f"职责: {analysis['agent_role']}\n"
            analyses_text += f"{'='*60}\n"
            analyses_text += analysis['analysis'] + "\n"
        
        prompt = f"""
你是一名资深的首席投资策略师，拥有CFA、FRM等专业资格，具有25年的市场实战经验和卓越的综合分析能力。

你的团队包含4位专业分析师，他们已经从不同维度完成了龙虎榜数据分析：
1. 游资行为分析师 - 分析游资操作特征和意图
2. 个股潜力分析师 - 挖掘次日大概率上涨的股票
3. 题材追踪分析师 - 识别热点题材和轮动机会
4. 风险控制专家 - 识别高风险股票和市场陷阱

以下是各位分析师的详细分析报告：

{analyses_text[:15000]}

请作为首席策略师，综合以上所有分析，给出最终的投资策略报告：

1. **市场总体研判**
   - 综合评估当前龙虎榜反映的市场状态
   - 判断游资整体的进攻或防守态度
   - 评估短期市场的机会和风险
   - 给出市场情绪和热度评分（0-100分）

2. **次日重点推荐股票（TOP5-8）** ⭐⭐⭐ 最核心
   - 综合4位分析师的意见，筛选出5-8只次日最有潜力的股票
   - 每只股票必须包含：
     * 股票名称和代码
     * 推荐理由（多维度综合）
     * 确定性评级（高/中/低）
     * 买入价位区间
     * 目标价位（预期涨幅）
     * 止损价位
     * 持有周期建议
   - 按推荐优先级排序（第一只为最看好）

3. **高风险警示股票（TOP3-5）**
   - 综合识别3-5只高风险股票
   - 说明风险原因
   - 给出规避建议

4. **热点题材总结**
   - 总结当前2-3个最强势题材
   - 每个题材推荐1-2只最优标的
   - 分析题材的持续性

5. **操作策略建议**
   - 仓位管理建议（进攻/平衡/防守）
   - 选股思路和方向
   - 买卖时机选择
   - 风险控制要求

6. **注意事项**
   - 提示关键风险点
   - 强调纪律执行
   - 给出应对预案

请给出专业、全面、可执行的首席策略师综合报告。报告要有明确的结论和可操作性！
"""
        
        messages = [
            {"role": "system", "content": "你是一名资深的首席投资策略师，擅长综合多维度分析，给出最优投资决策。"},
            {"role": "user", "content": prompt}
        ]
        
        analysis = self.deepseek_client.call_api(messages, max_tokens=5000)
        
        print("  ✓ 首席策略师分析完成")
        
        return {
            "agent_name": "首席策略师",
            "agent_role": "综合多维度分析，给出最终投资建议和推荐股票清单",
            "analysis": analysis,
            "focus_areas": ["综合研判", "推荐股票", "风险警示", "热点题材", "操作策略"],
            "timestamp": time.strftime("%Y-%m-%d %H:%M:%S")
        }


# 测试函数
if __name__ == "__main__":
    print("=" * 60)
    print("测试智瞰龙虎AI分析师系统")
    print("=" * 60)
    
    # 创建模拟数据
    test_summary = {
        'total_records': 150,
        'total_stocks': 50,
        'total_youzi': 30,
        'total_buy_amount': 500000000,
        'total_sell_amount': 200000000,
        'total_net_inflow': 300000000,
        'top_youzi': {
            '92科比': 14455321,
            '赵老哥': 12000000,
            '章盟主': 10000000
        },
        'top_stocks': [
            {'code': '001337', 'name': '四川黄金', 'net_inflow': 14455321}
        ],
        'hot_concepts': {
            '黄金概念': 10,
            '新能源': 8,
            'ChatGPT': 7
        }
    }
    
    test_data = """
【详细交易记录 TOP50】
92科比 | 四川黄金(001337) | 买入:14,470,401 卖出:15,080 净流入:14,455,321 | 日期:2023-03-22
"""
    
    agents = LonghubangAgents()
    
    # 测试游资行为分析师
    print("\n测试游资行为分析师...")
    result = agents.youzi_behavior_analyst(test_data, test_summary)
    print(f"分析师: {result['agent_name']}")
    print(f"分析内容长度: {len(result['analysis'])} 字符")

