"""
宏观分析板块 - Streamlit UI
"""

from __future__ import annotations

import time
from typing import Any, Dict, List

import pandas as pd
import streamlit as st

import config
from macro_analysis_engine import MacroAnalysisEngine


def display_macro_analysis() -> None:
    st.markdown(
        """
        <div style="background: linear-gradient(135deg, #09203f 0%, #537895 100%);
                    padding: 2rem; border-radius: 16px; margin-bottom: 1.2rem;
                    box-shadow: 0 8px 30px rgba(9,32,63,0.25);">
            <h1 style="color: white; margin: 0;">🌏 宏观分析</h1>
            <p style="color: rgba(255,255,255,0.86); margin: 0.6rem 0 0 0; font-size: 1.02rem;">
                国家统计局官方数据 × AI多智能体 × A股行业映射 × 优质标的筛选
            </p>
        </div>
        """,
        unsafe_allow_html=True,
    )

    st.info(
        "本板块优先通过国家统计局官方接口抓取宏观数据，再结合A股指数与模型分析输出行业利好/利空和优质标的。"
    )

    col1, col2 = st.columns([2, 1])
    with col1:
        analyze = st.button("🚀 开始宏观分析", type="primary", key="macro_analysis_run")
    with col2:
        if st.button("🧹 清除结果", key="macro_analysis_clear"):
            st.session_state.pop("macro_analysis_result", None)
            st.rerun()

    st.markdown("---")

    if analyze:
        st.session_state.pop("macro_analysis_result", None)
        run_macro_analysis()

    if "macro_analysis_result" in st.session_state:
        result = st.session_state["macro_analysis_result"]
        if result.get("success"):
            display_macro_analysis_result(result)
        else:
            st.error(f"分析失败: {result.get('error', '未知错误')}")


def run_macro_analysis() -> None:
    progress_bar = st.progress(0)
    status = st.empty()

    def callback(pct: int, text: str) -> None:
        progress_bar.progress(pct)
        status.text(text)

    try:
        engine = MacroAnalysisEngine(model=config.DEFAULT_MODEL_NAME)
        result = engine.run_full_analysis(progress_callback=callback)
        st.session_state["macro_analysis_result"] = result
        time.sleep(0.8)
        st.rerun()
    except Exception as exc:
        st.error(f"运行失败: {exc}")
    finally:
        progress_bar.empty()
        status.empty()


def display_macro_analysis_result(result: Dict[str, Any]) -> None:
    raw_data = result.get("raw_data", {})
    snapshot = raw_data.get("macro_snapshot", {})
    agents = result.get("agents_analysis", {})
    sector_view = result.get("sector_view", {})
    stock_view = result.get("stock_view", {})

    st.success(f"分析完成时间：{result.get('timestamp', '-')}")

    if result.get("errors"):
        with st.expander("部分数据获取告警"):
            for item in result["errors"]:
                st.warning(item)

    display_macro_cards(snapshot)
    st.markdown("---")

    tab1, tab2, tab3, tab4, tab5 = st.tabs(
        ["📌 综合结论", "📊 宏观数据", "🏭 行业映射", "🎯 优质标的", "🧠 分析过程"]
    )

    with tab1:
        chief = agents.get("chief", {})
        st.subheader("首席策略官")
        st.markdown(chief.get("analysis", "暂无综合结论"))

    with tab2:
        display_macro_tables(raw_data)

    with tab3:
        display_sector_view(sector_view, agents.get("sector", {}))

    with tab4:
        display_stock_view(stock_view, result.get("candidate_stocks", []), agents.get("stock", {}))

    with tab5:
        st.subheader("宏观总量分析师")
        st.markdown(agents.get("macro", {}).get("analysis", "暂无"))
        st.markdown("---")
        st.subheader("政策流动性分析师")
        st.markdown(agents.get("policy", {}).get("analysis", "暂无"))
        st.markdown("---")
        st.subheader("行业映射分析师")
        st.markdown(agents.get("sector", {}).get("analysis", "暂无"))


def display_macro_cards(snapshot: Dict[str, Any]) -> None:
    keys = [
        "gdp_yoy",
        "manufacturing_pmi",
        "cpi_yoy",
        "m2_yoy",
        "retail_sales_yoy",
        "urban_unemployment",
    ]
    cols = st.columns(6)
    for col, key in zip(cols, keys):
        item = snapshot.get(key)
        if not item:
            col.metric(label=key, value="N/A")
            continue
        delta = None
        if item.get("change") is not None:
            delta = f"{item['change']:+.2f}{item['unit']}"
        col.metric(
            label=item["label"],
            value=f"{item['value']}{item['unit']}",
            delta=delta,
            help=item.get("period_label", ""),
        )


def display_macro_tables(raw_data: Dict[str, Any]) -> None:
    st.subheader("国家统计局核心指标")
    tables = raw_data.get("macro_tables", {})
    snapshot = raw_data.get("macro_snapshot", {})

    overview_rows = []
    for key, item in snapshot.items():
        overview_rows.append(
            {
                "指标": item["label"],
                "最新值": f"{item['value']}{item['unit']}",
                "最新期间": item["period_label"],
                "前值": f"{item['previous_value']}{item['unit']}" if item.get("previous_value") is not None else "-",
                "变动": f"{item['change']:+.2f}{item['unit']}" if item.get("change") is not None else "-",
            }
        )
    if overview_rows:
        st.dataframe(pd.DataFrame(overview_rows), width="stretch", hide_index=True)

    table_names = {
        "gdp_yoy": "GDP同比",
        "gdp_qoq": "GDP环比",
        "industrial_yoy": "规上工业同比",
        "cpi_yoy": "CPI同比",
        "ppi_yoy": "PPI同比",
        "manufacturing_pmi": "制造业PMI",
        "non_manufacturing_pmi": "非制造业PMI",
        "composite_pmi": "综合PMI",
        "m2_yoy": "M2同比",
        "retail_sales_yoy": "社零同比",
        "fixed_asset_yoy": "固投累计同比",
        "real_estate_invest_yoy": "地产投资累计同比",
        "urban_unemployment": "城镇调查失业率",
    }

    for key, title in table_names.items():
        if key not in tables:
            continue
        with st.expander(title):
            st.dataframe(tables[key], width="stretch", hide_index=True)

    if raw_data.get("market_indices"):
        st.subheader("A股指数快照")
        st.dataframe(
            pd.DataFrame(
                [
                    {
                        "指数": name,
                        "日期": item["date"],
                        "收盘": item["close"],
                        "日涨跌": f"{item['daily_change_pct']:+.2f}%",
                        "20日": f"{item['pct_20d']:+.2f}%",
                        "60日": f"{item['pct_60d']:+.2f}%",
                    }
                    for name, item in raw_data["market_indices"].items()
                ]
            ),
            width="stretch",
            hide_index=True,
        )

    if raw_data.get("news"):
        st.subheader("宏观新闻样本")
        for item in raw_data["news"]:
            st.markdown(f"- `{item['publish_time']}` {item['title']}")


def display_sector_view(sector_view: Dict[str, Any], sector_agent: Dict[str, Any]) -> None:
    st.subheader(f"市场判断：{sector_view.get('market_view', '暂无')}")

    col1, col2 = st.columns(2)
    with col1:
        st.markdown("#### 利好行业")
        bullish = sector_view.get("bullish_sectors", [])
        if bullish:
            st.dataframe(
                pd.DataFrame(
                    [
                        {
                            "行业": item.get("sector", ""),
                            "置信度": item.get("confidence", item.get("score", "")),
                            "逻辑": item.get("logic", ""),
                        }
                        for item in bullish
                    ]
                ),
                width="stretch",
                hide_index=True,
            )
        else:
            st.info("暂无利好行业")

    with col2:
        st.markdown("#### 利空行业")
        bearish = sector_view.get("bearish_sectors", [])
        if bearish:
            st.dataframe(
                pd.DataFrame(
                    [
                        {
                            "行业": item.get("sector", ""),
                            "置信度": item.get("confidence", item.get("score", "")),
                            "逻辑": item.get("logic", ""),
                        }
                        for item in bearish
                    ]
                ),
                width="stretch",
                hide_index=True,
            )
        else:
            st.info("暂无利空行业")

    if sector_view.get("watch_signals"):
        st.markdown("#### 重点跟踪")
        for signal in sector_view["watch_signals"]:
            st.markdown(f"- {signal}")

    st.markdown("---")
    st.markdown(sector_agent.get("analysis", "暂无行业映射分析"))


def display_stock_view(
    stock_view: Dict[str, Any], candidate_stocks: List[Dict[str, Any]], stock_agent: Dict[str, Any]
) -> None:
    recommended = stock_view.get("recommended_stocks", [])
    watchlist = stock_view.get("watchlist", [])

    st.subheader("优先关注")
    if recommended:
        st.dataframe(
            pd.DataFrame(
                [
                    {
                        "代码": item.get("code", ""),
                        "名称": item.get("name", ""),
                        "方向": item.get("sector", ""),
                        "现价": item.get("price", ""),
                        "PE": item.get("pe_ratio", ""),
                        "PB": item.get("pb_ratio", ""),
                        "20日": _format_pct(item.get("recent_20d_return")),
                        "60日": _format_pct(item.get("recent_60d_return")),
                        "理由": item.get("reason", ""),
                        "风险": item.get("risk", ""),
                    }
                    for item in recommended
                ]
            ),
            width="stretch",
            hide_index=True,
        )
    else:
        st.info("暂无推荐标的")

    st.subheader("观察名单")
    if watchlist:
        st.dataframe(
            pd.DataFrame(watchlist),
            width="stretch",
            hide_index=True,
        )
    else:
        st.info("暂无观察名单")

    with st.expander("候选股票池原始快照"):
        if candidate_stocks:
            st.dataframe(pd.DataFrame(candidate_stocks), width="stretch", hide_index=True)
        else:
            st.info("暂无候选股票池")

    st.markdown("---")
    st.markdown(stock_agent.get("analysis", "暂无选股分析"))


def _format_pct(value: Any) -> str:
    if value in (None, "", "-"):
        return "-"
    try:
        return f"{float(value):+.2f}%"
    except Exception:
        return str(value)
