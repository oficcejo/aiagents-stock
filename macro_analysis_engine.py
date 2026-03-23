"""
宏观分析板块 - 综合引擎
"""

from __future__ import annotations

import time
from typing import Any, Dict, List

import config
from macro_analysis_agents import MacroAnalysisAgents
from macro_analysis_data import MacroAnalysisDataFetcher


class MacroAnalysisEngine:
    """统筹宏观数据抓取、多智能体分析和结果组织"""

    def __init__(self, model: str | None = None) -> None:
        self.model = model or config.DEFAULT_MODEL_NAME
        self.data_fetcher = MacroAnalysisDataFetcher()
        self.agents = MacroAnalysisAgents(model=self.model)

    def run_full_analysis(self, progress_callback=None) -> Dict[str, Any]:
        results: Dict[str, Any] = {
            "success": False,
            "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
            "raw_data": {},
            "agents_analysis": {},
            "sector_view": {},
            "stock_view": {},
            "candidate_stocks": [],
            "errors": [],
        }

        try:
            if progress_callback:
                progress_callback(5, "正在获取国家统计局宏观数据...")

            raw_data = self.data_fetcher.fetch_all_data()
            results["raw_data"] = raw_data
            results["errors"] = raw_data.get("errors", [])
            context_text = self.data_fetcher.build_prompt_context(raw_data)

            if progress_callback:
                progress_callback(22, "宏观总量分析师正在研判...")
            macro_result = self.agents.macro_analyst_agent(context_text)

            if progress_callback:
                progress_callback(38, "政策流动性分析师正在研判...")
            policy_result = self.agents.policy_analyst_agent(context_text)

            if progress_callback:
                progress_callback(55, "行业映射分析师正在生成板块多空视图...")
            sector_result = self.agents.sector_mapper_agent(
                context_text=context_text,
                rule_view=raw_data.get("rule_based_sector_view", {}),
                sector_pool=list(self.data_fetcher.SECTOR_STOCK_POOLS.keys()),
            )
            sector_view = self._normalize_sector_view(
                sector_result.get("structured", {}),
                raw_data.get("rule_based_sector_view", {}),
            )

            bullish_sector_names = [
                item.get("sector", "") for item in sector_view.get("bullish_sectors", [])
            ]
            candidate_stocks = self.data_fetcher.build_stock_candidates_for_sectors(
                bullish_sector_names
            )
            results["candidate_stocks"] = candidate_stocks

            if progress_callback:
                progress_callback(72, "优质标的分析师正在筛选候选股票...")
            stock_result = self.agents.stock_selector_agent(
                context_text=context_text,
                sector_view=sector_view,
                stock_candidates=candidate_stocks,
            )
            stock_view = self._normalize_stock_view(
                stock_result.get("structured", {}),
                candidate_stocks,
            )

            if progress_callback:
                progress_callback(88, "首席策略官正在综合输出...")
            chief_result = self.agents.chief_strategist_agent(
                context_text=context_text,
                macro_report=macro_result.get("analysis", ""),
                policy_report=policy_result.get("analysis", ""),
                sector_view=sector_view,
                stock_view=stock_view,
            )

            results["agents_analysis"] = {
                "macro": macro_result,
                "policy": policy_result,
                "sector": sector_result,
                "stock": stock_result,
                "chief": chief_result,
            }
            results["sector_view"] = sector_view
            results["stock_view"] = stock_view
            results["success"] = True

            if progress_callback:
                progress_callback(100, "分析完成")

        except Exception as exc:
            results["error"] = str(exc)

        return results

    @staticmethod
    def _normalize_sector_view(
        ai_view: Dict[str, Any], fallback_view: Dict[str, Any]
    ) -> Dict[str, Any]:
        view = ai_view if isinstance(ai_view, dict) and ai_view else fallback_view
        return {
            "market_view": view.get("market_view", fallback_view.get("market_view", "结构性机会为主")),
            "bullish_sectors": view.get("bullish_sectors", fallback_view.get("bullish_sectors", [])),
            "bearish_sectors": view.get("bearish_sectors", fallback_view.get("bearish_sectors", [])),
            "watch_signals": view.get("watch_signals", fallback_view.get("watch_signals", [])),
        }

    @staticmethod
    def _normalize_stock_view(
        ai_view: Dict[str, Any], candidate_stocks: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        if not isinstance(ai_view, dict) or not ai_view:
            return {
                "recommended_stocks": candidate_stocks[:6],
                "watchlist": candidate_stocks[6:10],
            }

        recommended = ai_view.get("recommended_stocks", [])
        watchlist = ai_view.get("watchlist", [])
        candidate_map = {item["code"]: item for item in candidate_stocks}

        def merge_item(item: Dict[str, Any]) -> Dict[str, Any]:
            base = candidate_map.get(item.get("code"), {}).copy()
            base.update(item)
            return base

        return {
            "recommended_stocks": [merge_item(item) for item in recommended],
            "watchlist": [merge_item(item) for item in watchlist],
        }
