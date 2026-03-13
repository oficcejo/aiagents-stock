#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
低估值策略UI模块
"""

import streamlit as st
import pandas as pd
from datetime import datetime
from strategies.value_stock_selector import ValueStockSelector
from strategies.value_stock_strategy import ValueStockStrategy


def display_value_stock():
    """显示低估值选股界面"""

    st.markdown("""
    <div style="background: linear-gradient(135deg, #1a5276 0%, #2e86c1 50%, #1a5276 100%); 
                padding: 2rem; border-radius: 15px; margin-bottom: 1.5rem;
                box-shadow: 0 8px 32px rgba(0,0,0,0.3);">
        <h1 style="color: #fff; margin: 0; font-size: 2rem;">
            💎 低估值策略 - 价值投资选股
        </h1>
        <p style="color: rgba(255,255,255,0.7); margin: 0.5rem 0 0 0; font-size: 0.9rem;">
            基于视频 <a href="https://www.bilibili.com/video/BV1eJfxBrEjZ" target="_blank" style="color: #7ec8e3; text-decoration: underline;">头号投资法则</a>
        </p>
        <p style="color: rgba(255,255,255,0.8); margin: 0.3rem 0 0 0; font-size: 1.1rem;">
            低PE + 低PB + 高股息 + 低负债 — 寻找被市场低估的优质标的
        </p>
    </div>
    """, unsafe_allow_html=True)

    st.markdown("---")

    st.markdown("""
    ### 📋 选股策略说明

    **筛选条件**：
    - ✅ 市盈率（PE）≤ 20
    - ✅ 市净率（PB）≤ 1.5
    - ✅ 股息率 ≥ 1%
    - ✅ 资产负债率 ≤ 30%
    - ✅ 非ST股票
    - ✅ 非科创板
    - ✅ 非创业板
    - ✅ 按流通市值由小到大排名

    **量化交易策略**：
    - 💰 资金量：100万元
    - 📈 买入时机：开盘买入
    - 💼 单股最大仓位：30%
    - 🎯 最大持股数：4只
    - 🛒 每日最多买入：2只
    - 📉 卖出条件①：持股满30天到期卖出
    - 📉 卖出条件②：RSI超买（>70）卖出
    """)

    st.markdown("---")

    # 参数设置
    col1, col2 = st.columns([2, 1])

    with col1:
        top_n = st.slider(
            "筛选数量",
            min_value=5,
            max_value=20,
            value=10,
            step=1,
            help="选择展示的股票数量",
            key="value_stock_top_n"
        )

    with col2:
        st.info(f"💡 将筛选流通市值最小的前{top_n}只低估值股票")

    st.markdown("---")

    # 开始选股按钮
    if st.button("🚀 开始低估值选股", type="primary", width='content', key="value_stock_start"):

        with st.spinner("正在获取数据，请稍候..."):
            selector = ValueStockSelector()
            success, stocks_df, message = selector.get_value_stocks(top_n=top_n)

            if success and stocks_df is not None:
                st.session_state.value_stocks = stocks_df
                st.session_state.value_stock_selector = selector
                st.success(f"✅ {message}")
                st.rerun()
            else:
                st.error(f"❌ {message}")

    # 显示选股结果
    if 'value_stocks' in st.session_state:
        display_stock_results(
            st.session_state.value_stocks,
            st.session_state.get('value_stock_selector')
        )


def display_stock_results(stocks_df: pd.DataFrame, selector):
    """显示选股结果"""

    st.markdown("---")
    st.markdown("## 📊 选股结果")

    # 统计信息
    col1, col2, col3, col4 = st.columns(4)

    with col1:
        st.metric("筛选数量", f"{len(stocks_df)} 只")

    with col2:
        pe_col = None
        for pattern in ['市盈率', '市盈率(动态)']:
            matching = [col for col in stocks_df.columns if pattern in col]
            if matching:
                pe_col = matching[0]
                break
        if pe_col:
            valid = pd.to_numeric(stocks_df[pe_col], errors='coerce').dropna()
            if len(valid) > 0:
                st.metric("平均PE", f"{valid.mean():.1f}")
            else:
                st.metric("平均PE", "-")
        else:
            st.metric("平均PE", "-")

    with col3:
        pb_col = None
        matching = [col for col in stocks_df.columns if '市净率' in col]
        if matching:
            pb_col = matching[0]
            valid = pd.to_numeric(stocks_df[pb_col], errors='coerce').dropna()
            if len(valid) > 0:
                st.metric("平均PB", f"{valid.mean():.2f}")
            else:
                st.metric("平均PB", "-")
        else:
            st.metric("平均PB", "-")

    with col4:
        div_col = None
        matching = [col for col in stocks_df.columns if '股息率' in col]
        if matching:
            div_col = matching[0]
            valid = pd.to_numeric(stocks_df[div_col], errors='coerce').dropna()
            if len(valid) > 0:
                st.metric("平均股息率", f"{valid.mean():.2f}%")
            else:
                st.metric("平均股息率", "-")
        else:
            st.metric("平均股息率", "-")

    st.markdown("---")

    # 显示股票列表
    st.markdown("### 📋 精选低估值股票")

    for idx, row in stocks_df.iterrows():
        code = row.get('股票代码', 'N/A')
        name = row.get('股票简称', 'N/A')

        # 获取关键指标用于标题
        pe_val = ''
        for pattern in ['市盈率', '市盈率(动态)']:
            matching = [col for col in stocks_df.columns if pattern in col]
            if matching:
                v = row.get(matching[0])
                if v is not None and not pd.isna(v):
                    try:
                        pe_val = f" PE:{float(v):.1f}"
                    except:
                        pass
                break

        pb_val = ''
        matching = [col for col in stocks_df.columns if '市净率' in col]
        if matching:
            v = row.get(matching[0])
            if v is not None and not pd.isna(v):
                try:
                    pb_val = f" PB:{float(v):.2f}"
                except:
                    pass

        with st.expander(
            f"【第{idx+1}名】{code} - {name}{pe_val}{pb_val}",
            expanded=(idx < 3)
        ):
            display_stock_detail(row, stocks_df)

    # 完整数据表格
    st.markdown("---")
    st.markdown("### 📊 完整数据表格")

    # 选择关键列
    display_cols = ['股票代码', '股票简称']
    for pattern in ['最新价', '股价']:
        matching = [col for col in stocks_df.columns if pattern in col]
        if matching:
            display_cols.append(matching[0])
            break
    for pattern in ['市盈率', '市净率', '股息率', '资产负债率', '流通市值', '所属行业']:
        matching = [col for col in stocks_df.columns if pattern in col]
        if matching:
            display_cols.append(matching[0])

    final_cols = [col for col in display_cols if col in stocks_df.columns]

    if final_cols:
        st.dataframe(stocks_df[final_cols], width='content', height=400)

        csv = stocks_df[final_cols].to_csv(index=False, encoding='utf-8-sig')
        st.download_button(
            label="📥 下载股票列表CSV",
            data=csv,
            file_name=f"value_stock_{datetime.now().strftime('%Y%m%d')}.csv",
            mime="text/csv",
            key="value_csv_download"
        )

    # 量化交易模拟
    st.markdown("---")
    display_strategy_simulation(stocks_df, selector)


def display_stock_detail(row: pd.Series, df: pd.DataFrame):
    """显示单个股票详情"""

    def is_valid(value):
        if value is None:
            return False
        if isinstance(value, float) and pd.isna(value):
            return False
        if isinstance(value, str) and value.strip() in ('', 'N/A', 'nan', 'None'):
            return False
        return True

    def fmt(value, suffix=''):
        if not is_valid(value):
            return "-"
        try:
            return f"{float(value):.2f}{suffix}"
        except:
            return str(value) + suffix

    # 基本估值数据
    col1, col2, col3, col4 = st.columns(4)

    with col1:
        for p in ['市盈率', '市盈率(动态)']:
            m = [c for c in df.columns if p in c]
            if m:
                st.metric("📊 市盈率(PE)", fmt(row.get(m[0])))
                break

    with col2:
        m = [c for c in df.columns if '市净率' in c]
        if m:
            st.metric("📊 市净率(PB)", fmt(row.get(m[0])))

    with col3:
        m = [c for c in df.columns if '股息率' in c]
        if m:
            st.metric("💰 股息率", fmt(row.get(m[0]), '%'))

    with col4:
        m = [c for c in df.columns if '资产负债率' in c]
        if m:
            st.metric("📉 资产负债率", fmt(row.get(m[0]), '%'))

    # 补充信息
    st.markdown("**其他指标**：")
    info_parts = []
    for pattern in ['最新价', '股价', '流通市值', '总市值', '所属行业', '涨跌幅']:
        m = [c for c in df.columns if pattern in c]
        if m:
            val = row.get(m[0])
            if is_valid(val):
                info_parts.append(f"**{pattern}**: {val}")
    if info_parts:
        st.markdown(" | ".join(info_parts))


def display_strategy_simulation(stocks_df: pd.DataFrame, selector):
    """显示量化交易策略模拟"""

    st.markdown("## 🎯 策略模拟")

    st.info("""
    **策略规则**：
    - 📈 **买入**：开盘价买入，单股最大仓位30%，每日最多买2只
    - 📉 **卖出条件①**：持股满30天，到期自动卖出
    - 📉 **卖出条件②**：RSI(14) > 70 超买，触发卖出
    - 🎯 **最大持股**：4只
    - 💰 **初始资金**：100万元
    """)

    col1, col2 = st.columns(2)

    with col1:
        if st.button("🎮 开始策略模拟", type="primary", width='content', key="value_sim_start"):
            st.session_state.show_value_strategy_sim = True

    with col2:
        pass

    if st.session_state.get('show_value_strategy_sim'):
        run_strategy_simulation(stocks_df)


def run_strategy_simulation(stocks_df: pd.DataFrame):
    """运行策略模拟"""

    st.markdown("---")
    st.markdown("### 📈 策略模拟执行")

    strategy = ValueStockStrategy(initial_capital=1000000.0)

    # 模拟买入
    st.markdown("#### 1️⃣ 模拟买入信号")

    buy_results = []
    current_date = datetime.now().strftime("%Y-%m-%d")

    for idx, row in stocks_df.head(strategy.max_daily_buy).iterrows():
        code = str(row.get('股票代码', '')).split('.')[0]
        name = row.get('股票简称', 'N/A')

        # 尝试获取价格
        price = 0
        for p in ['最新价', '股价']:
            m = [c for c in stocks_df.columns if p in c]
            if m:
                try:
                    price = float(row.get(m[0], 0))
                except:
                    pass
                if price > 0:
                    break

        if price > 0:
            success, message, trade = strategy.buy(code, name, price, current_date)
            buy_results.append({
                'success': success,
                'message': message,
                'trade': trade
            })

    for result in buy_results:
        if result['success']:
            st.success(result['message'])
        else:
            st.warning(f"⚠️ {result['message']}")

    # RSI检查
    st.markdown("---")
    st.markdown("#### 2️⃣ RSI卖出信号检测")

    with st.spinner("正在计算RSI指标..."):
        for code, pos in list(strategy.positions.items()):
            rsi = strategy.calculate_rsi(code)
            if rsi is not None:
                if rsi > strategy.rsi_overbought:
                    st.warning(f"⚠️ {code} {pos['name']} RSI={rsi} > {strategy.rsi_overbought}，触发超买卖出信号！")
                else:
                    st.info(f"ℹ️ {code} {pos['name']} RSI={rsi}，正常范围")
            else:
                st.info(f"ℹ️ {code} {pos['name']} RSI计算中...")

    # 显示持仓
    st.markdown("---")
    st.markdown("#### 3️⃣ 当前持仓")

    positions = strategy.get_positions()
    if positions:
        positions_df = pd.DataFrame(positions)
        st.dataframe(positions_df, width='content')
    else:
        st.info("暂无持仓")

    # 显示账户摘要
    st.markdown("---")
    st.markdown("#### 4️⃣ 账户摘要")

    summary = strategy.get_portfolio_summary()

    col1, col2, col3, col4 = st.columns(4)

    with col1:
        st.metric("初始资金", f"{summary['initial_capital']:,.0f} 元")
    with col2:
        st.metric("可用资金", f"{summary['available_cash']:,.0f} 元")
    with col3:
        st.metric("持仓市值", f"{summary['position_value']:,.0f} 元")
    with col4:
        st.metric("总资产", f"{summary['total_assets']:,.0f} 元")

    st.markdown("---")
    st.markdown("#### 📝 策略说明")
    st.markdown("""
    **后续操作**：
    1. **持有期管理**：系统跟踪每只股票的持有天数（30天到期）
    2. **RSI监测**：每日收盘后计算RSI(14)
       - RSI > 70：超买信号，提示卖出
       - RSI < 30：超卖信号（可作为加仓参考）
    3. **轮动买入**：卖出后释放资金，继续买入新的低估值股票

    **风险提示**：
    - ⚠️ 本策略为模拟演示，实际交易存在滑点、手续费等成本
    - ⚠️ 低估值不代表没有风险，价值陷阱需警惕
    - ⚠️ 请谨慎评估风险，理性投资
    """)


# 主入口
if __name__ == "__main__":
    display_value_stock()
