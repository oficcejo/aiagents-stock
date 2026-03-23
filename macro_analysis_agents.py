"""
宏观分析板块 - AI智能体
"""

from __future__ import annotations

import json
import re
import time
from typing import Any, Dict, List

import config
from deepseek_client import DeepSeekClient


class MacroAnalysisAgents:
    """宏观分析多智能体"""

    def __init__(self, model: str | None = None) -> None:
        self.model = model or config.DEFAULT_MODEL_NAME
        self.client = DeepSeekClient(model=self.model)

    def macro_analyst_agent(self, context_text: str) -> Dict[str, Any]:
        prompt = f"""
你是一位资深中国宏观经济研究员。请严格基于下面的数据，分析当前国内宏观经济形势。

{context_text}

请重点回答：
1. 当前中国经济处于什么阶段，增长、通胀、就业、地产、信用各自是什么状态。
2. 当前宏观环境的核心矛盾是什么。
3. 未来1-2个季度最关键的跟踪变量有哪些。
4. 输出必须紧扣中国A股投资，不要空泛。
"""
        return self._call_text(
            "你是中国宏观经济分析师，擅长从官方数据中提炼当前经济主线。",
            prompt,
            agent_name="宏观总量分析师",
            focus_areas=["增长", "通胀", "就业", "地产", "信用"],
        )

    def policy_analyst_agent(self, context_text: str) -> Dict[str, Any]:
        prompt = f"""
你是一位资深的政策与流动性分析师。请基于下面的数据和新闻，评估当前中国政策环境与流动性状态。

{context_text}

请重点回答：
1. 当前政策组合更偏稳增长、稳地产、稳信用还是防风险。
2. 流动性是否对A股估值形成支撑。
3. 哪些方向更可能获得政策支持，哪些方向政策弹性偏弱。
4. 必须写出对A股风格和板块轮动的含义。
"""
        return self._call_text(
            "你是中国政策与流动性分析师，擅长把政策信号映射到A股行业风格。",
            prompt,
            agent_name="政策流动性分析师",
            focus_areas=["货币", "财政", "产业政策", "估值", "风格"],
        )

    def sector_mapper_agent(self, context_text: str, rule_view: Dict[str, Any], sector_pool: List[str]) -> Dict[str, Any]:
        prompt = f"""
你是一位A股行业配置分析师。请严格从给定行业板块池中选择，结合宏观数据、政策环境与A股指数状态，输出未来1-2个季度更可能受益和承压的行业板块。

可选板块池：
{", ".join(sector_pool)}

规则基线（可修正，但不能完全脱离）：
{json.dumps(rule_view, ensure_ascii=False, indent=2)}

宏观与市场上下文：
{context_text}

请只返回 JSON，不要写任何额外解释。格式如下：
{{
  "market_view": "震荡偏多/结构性机会/震荡偏谨慎",
  "bullish_sectors": [
    {{"sector": "银行", "logic": "逻辑", "confidence": 0.78}},
    {{"sector": "公用事业", "logic": "逻辑", "confidence": 0.72}}
  ],
  "bearish_sectors": [
    {{"sector": "房地产", "logic": "逻辑", "confidence": 0.81}}
  ],
  "watch_signals": ["一句话监控点1", "一句话监控点2"]
}}

要求：
1. `bullish_sectors` 输出 4-6 个；
2. `bearish_sectors` 输出 2-4 个；
3. 行业名称必须从板块池中选择；
4. `confidence` 用 0-1 之间小数；
5. 逻辑必须结合宏观数据，不要泛化成“政策支持”四个字。
"""
        structured = self._call_json(
            "你是A股行业配置分析师，只输出合法JSON。",
            prompt,
            fallback=rule_view,
        )
        analysis_prompt = f"""
请基于以下结构化结论，写一份可读性强的中文行业配置报告：
{json.dumps(structured, ensure_ascii=False, indent=2)}

要求：
1. 先说市场主线；
2. 再解释看多板块和看空板块；
3. 每个板块都要写出宏观传导链；
4. 结尾补一段风格偏好与风险提示。
"""
        analysis = self.client.call_api(
            [
                {"role": "system", "content": "你是A股行业配置分析师，擅长把结构化结论写成可执行策略。"},
                {"role": "user", "content": analysis_prompt},
            ],
            max_tokens=2600,
            temperature=0.5,
        )
        return {
            "agent_name": "行业映射分析师",
            "agent_role": "将宏观变量映射为A股行业利好与利空方向",
            "analysis": analysis,
            "structured": structured,
            "focus_areas": ["行业轮动", "顺周期", "红利", "科技成长"],
            "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
        }

    def stock_selector_agent(
        self,
        context_text: str,
        sector_view: Dict[str, Any],
        stock_candidates: List[Dict[str, Any]],
    ) -> Dict[str, Any]:
        candidate_text = json.dumps(stock_candidates, ensure_ascii=False, indent=2)
        prompt = f"""
你是一位A股选股分析师。请从候选股票中挑选更适合当前宏观环境的优质标的。

宏观与行业上下文：
{context_text}

行业配置结论：
{json.dumps(sector_view, ensure_ascii=False, indent=2)}

候选股票池：
{candidate_text}

请只返回 JSON，格式如下：
{{
  "recommended_stocks": [
    {{
      "code": "600036",
      "name": "招商银行",
      "sector": "银行",
      "reason": "推荐逻辑",
      "risk": "主要风险",
      "style": "稳健/进攻/均衡",
      "confidence": 0.82
    }}
  ],
  "watchlist": [
    {{"code": "002371", "name": "北方华创", "sector": "半导体", "reason": "观察逻辑"}}
  ]
}}

要求：
1. `recommended_stocks` 输出 4-8 只；
2. 优先选择与当前宏观主线匹配、质量相对更高、回撤承受度更可控的标的；
3. 推荐逻辑要结合行业、估值/质量、走势位置三个维度；
4. 不要推荐候选池外的股票。
"""
        fallback = {
            "recommended_stocks": stock_candidates[:6],
            "watchlist": stock_candidates[6:10],
        }
        structured = self._call_json(
            "你是A股选股分析师，只输出合法JSON。",
            prompt,
            fallback=fallback,
        )
        analysis_prompt = f"""
请基于以下结构化选股结果，输出一份中文选股说明：
{json.dumps(structured, ensure_ascii=False, indent=2)}

要求：
1. 解释为什么这些股票适配当前宏观环境；
2. 每只股票都要写一句核心催化与一句核心风险；
3. 明确区分“优先关注”和“观察名单”。
"""
        analysis = self.client.call_api(
            [
                {"role": "system", "content": "你是A股选股分析师，输出简洁、专业、可执行。"},
                {"role": "user", "content": analysis_prompt},
            ],
            max_tokens=2600,
            temperature=0.5,
        )
        return {
            "agent_name": "优质标的分析师",
            "agent_role": "从宏观受益方向中筛选更适合当前环境的A股标的",
            "analysis": analysis,
            "structured": structured,
            "focus_areas": ["候选股筛选", "风险收益比", "风格适配"],
            "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
        }

    def chief_strategist_agent(
        self,
        context_text: str,
        macro_report: str,
        policy_report: str,
        sector_view: Dict[str, Any],
        stock_view: Dict[str, Any],
    ) -> Dict[str, Any]:
        prompt = f"""
你是一位首席策略官，需要给出当前A股后市的综合结论。

宏观与市场上下文：
{context_text}

【宏观总量分析师】
{macro_report}

【政策流动性分析师】
{policy_report}

【行业映射结论】
{json.dumps(sector_view, ensure_ascii=False, indent=2)}

【优质标的结论】
{json.dumps(stock_view, ensure_ascii=False, indent=2)}

请输出一份结构清晰的综合报告，至少包含：
1. 当前宏观判断
2. A股后市展望
3. 利好板块与逻辑
4. 利空板块与逻辑
5. 优质标的与关注理由
6. 风险提示与需要跟踪的数据点
"""
        return self._call_text(
            "你是首席策略官，擅长把宏观、行业和选股结论整合成完整投资框架。",
            prompt,
            agent_name="首席策略官",
            focus_areas=["总策略", "行业配置", "选股落地", "风险提示"],
            max_tokens=4200,
            temperature=0.45,
        )

    def _call_text(
        self,
        system_prompt: str,
        user_prompt: str,
        agent_name: str,
        focus_areas: List[str],
        max_tokens: int = 3200,
        temperature: float = 0.45,
    ) -> Dict[str, Any]:
        analysis = self.client.call_api(
            [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
            max_tokens=max_tokens,
            temperature=temperature,
        )
        return {
            "agent_name": agent_name,
            "analysis": analysis,
            "focus_areas": focus_areas,
            "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
        }

    def _call_json(
        self,
        system_prompt: str,
        user_prompt: str,
        fallback: Dict[str, Any],
        max_tokens: int = 2800,
    ) -> Dict[str, Any]:
        response = self.client.call_api(
            [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
            max_tokens=max_tokens,
            temperature=0.2,
        )
        parsed = self._extract_json(response)
        if isinstance(parsed, dict):
            return parsed
        return fallback

    @staticmethod
    def _extract_json(text: str) -> Dict[str, Any] | None:
        if not text:
            return None
        text = text.strip()
        candidates = [text]

        fenced = re.findall(r"```(?:json)?\s*(\{.*?\})\s*```", text, re.S)
        candidates.extend(fenced)

        brace_match = re.search(r"(\{.*\})", text, re.S)
        if brace_match:
            candidates.append(brace_match.group(1))

        for candidate in candidates:
            try:
                return json.loads(candidate)
            except Exception:
                continue
        return None
