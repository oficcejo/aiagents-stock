"""
宏观周期分析 - 综合研判引擎
协调数据采集与AI分析，生成完整的宏观周期分析报告
"""

from macro_cycle_agents import MacroCycleAgents
from macro_cycle_data import MacroCycleDataFetcher
from typing import Dict, Any
import time
import json
import logging
import config


class MacroCycleEngine:
    """宏观周期综合研判引擎"""

    def __init__(self, model=None):
        self.model = model or config.DEFAULT_MODEL_NAME
        self.agents = MacroCycleAgents(model=self.model)
        self.data_fetcher = MacroCycleDataFetcher()
        self.logger = logging.getLogger(__name__)
        if not self.logger.handlers:
            logging.basicConfig(level=logging.INFO, format='[%(asctime)s] %(levelname)s %(name)s: %(message)s')
        print(f"[宏观周期引擎] 初始化完成 (模型: {self.model})")

    def run_full_analysis(self, progress_callback=None) -> Dict[str, Any]:
        """
        运行完整的宏观周期分析流程

        Args:
            progress_callback: 进度回调函数 (progress_pct, status_text)

        Returns:
            完整的分析结果
        """
        print("\n" + "=" * 60)
        print("🧭 宏观周期分析系统启动")
        print("=" * 60)

        results = {
            "success": False,
            "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
            "raw_data": {},
            "formatted_data": "",
            "agents_analysis": {},
            "data_errors": []
        }

        try:
            # 阶段1：数据采集
            if progress_callback:
                progress_callback(5, "📊 正在采集宏观经济数据...")
            print("\n[阶段1] 宏观经济数据采集...")
            print("-" * 60)

            raw_data = self.data_fetcher.get_all_macro_data()
            results["raw_data"] = raw_data
            results["data_errors"] = raw_data.get("errors", [])

            if not raw_data.get("success"):
                print("⚠ 数据采集未完全成功，尝试继续分析...")

            # 格式化数据
            formatted_text = self.data_fetcher.format_data_for_ai(raw_data)
            results["formatted_data"] = formatted_text

            if progress_callback:
                progress_callback(15, "✓ 数据采集完成")
            print("✓ 数据采集和格式化完成")
            print(f"  数据文本长度: {len(formatted_text)} 字符")

            # 阶段2：AI智能体分析
            print("\n[阶段2] AI智能体分析集群工作中...")
            print("-" * 60)

            agents_results = {}

            # 2.1 康波周期分析师
            if progress_callback:
                progress_callback(20, "🌊 康波周期分析师正在分析...")
            print("1/4 康波周期分析师...")
            kondratieff_result = self.agents.kondratieff_wave_agent(formatted_text)
            agents_results["kondratieff"] = kondratieff_result

            if progress_callback:
                progress_callback(35, "✓ 康波分析完成")

            # 2.2 美林时钟分析师
            if progress_callback:
                progress_callback(40, "⏰ 美林时钟分析师正在分析...")
            print("2/4 美林时钟分析师...")
            merrill_result = self.agents.merrill_lynch_clock_agent(formatted_text)
            agents_results["merrill"] = merrill_result

            if progress_callback:
                progress_callback(55, "✓ 美林时钟分析完成")

            # 2.3 中国政策分析师
            if progress_callback:
                progress_callback(60, "🏛️ 中国政策分析师正在分析...")
            print("3/4 中国政策分析师...")
            policy_result = self.agents.china_policy_agent(formatted_text)
            agents_results["policy"] = policy_result

            if progress_callback:
                progress_callback(75, "✓ 政策分析完成")

            # 2.4 首席宏观策略师（综合三位分析师的报告）
            if progress_callback:
                progress_callback(80, "👔 首席宏观策略师正在综合研判...")
            print("4/4 首席宏观策略师综合研判...")
            chief_result = self.agents.chief_macro_strategist_agent(
                kondratieff_report=kondratieff_result.get("analysis", ""),
                merrill_report=merrill_result.get("analysis", ""),
                policy_report=policy_result.get("analysis", ""),
                macro_data_text=formatted_text
            )
            agents_results["chief"] = chief_result

            if progress_callback:
                progress_callback(95, "✓ 综合研判完成")

            results["agents_analysis"] = agents_results
            results["success"] = True

            print("\n" + "=" * 60)
            print("✓ 宏观周期分析完成！")
            print("=" * 60)

            if progress_callback:
                progress_callback(100, "✅ 分析完成！")

        except Exception as e:
            print(f"\n✗ 分析过程出错: {e}")
            import traceback
            traceback.print_exc()
            results["error"] = str(e)

        return results


# 测试
if __name__ == "__main__":
    print("=" * 60)
    print("测试宏观周期分析引擎")
    print("=" * 60)
    engine = MacroCycleEngine()
    print("引擎初始化完成")
