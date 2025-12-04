#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
一进二策略UI界面模块
"""

import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, timedelta
from momentum_filter_data import MomentumFilterData
from momentum_filter_engine import MomentumFilterEngine


def display_momentum_filter():
    """显示一进二策略界面"""

    # 页面标题
    st.markdown("## 🚀 一进二策略 - 智能选股")
    st.markdown("---")

    # 策略说明
    with st.expander("📖 什么是一进二策略？", expanded=False):
        st.markdown("""
        ### 策略概述

        **一进二策略**是一种捕捉个股在首个涨停板（首板）后，于第二个交易日继续涨停（二板）的短线交易方法。

        ### 核心原理

        - **首板筛选**: 从当日所有涨停股票中，筛选出具有连板潜力的优质标的
        - **技术特征**: 关注涨停时间、封单强度、炸板次数、换手率等关键指标
        - **基本面**: 优选低价、小市值、深市股票，避免ST、科创板

        ### 选股标准

        1. ✅ **股价**: 优选30元以下（最好20元以下）
        2. ✅ **市值**: 流通市值100亿以下（最好80亿以下）
        3. ✅ **市场**: 深市股票（排除60开头）
        4. ✅ **板块**: 排除创业板300开头、科创板688开头
        5. ✅ **涨停质量**: 涨停时间早、封单强、无炸板或少炸板
        6. ✅ **换手率**: 5-15%为最佳（充分换手）
        7. ✅ **排除**: ST股票、一字板

        ### 评分维度

        本系统对首板股票进行综合评分（满分100分）：

        - **涨停时间** (30分): 越早越好，9:30-10:00最佳
        - **封单强度** (25分): 封单金额/流通市值比例越高越好
        - **炸板次数** (20分): 0次最佳，次数越多越差
        - **换手率** (15分): 5-15%最佳，过低或过高都不好
        - **市值大小** (10分): 市值越小越好

        ### 风险提示

        ⚠️ 一进二策略属于高风险短线策略，需要：
        - 严格的仓位管理（单票不超过三成）
        - 及时止损（-5%到-7%）
        - 关注市场整体情绪
        - 避免在市场情绪低迷时操作
        """)

    st.markdown("---")

    # 参数设置
    st.subheader("📋 筛选参数设置")

    col1, col2, col3 = st.columns(3)

    with col1:
        # 日期选择
        trade_date_option = st.selectbox(
            "选择交易日期",
            ["今天", "昨天", "自定义日期"]
        )

        if trade_date_option == "今天":
            trade_date = datetime.now().strftime("%Y%m%d")
        elif trade_date_option == "昨天":
            trade_date = (datetime.now() - timedelta(days=1)).strftime("%Y%m%d")
        else:
            custom_date = st.date_input(
                "选择日期",
                value=datetime.now() - timedelta(days=1)
            )
            trade_date = custom_date.strftime("%Y%m%d")

        st.info(f"📅 交易日期: {trade_date[:4]}-{trade_date[4:6]}-{trade_date[6:]}")

    with col2:
        max_price = st.slider(
            "最大股价（元）",
            min_value=10,
            max_value=100,
            value=30,
            step=5,
            help="建议30元以下"
        )

    with col3:
        max_market_cap = st.slider(
            "最大流通市值（亿）",
            min_value=20,
            max_value=500,
            value=100,
            step=10,
            help="建议100亿以下"
        )

    # 高级筛选选项
    with st.expander("⚙️ 高级筛选选项"):
        col1, col2, col3 = st.columns(3)

        with col1:
            exclude_sh = st.checkbox("排除沪市（60开头）", value=True,
                                    help="沪市监管更严格，摸不着头脑")

        with col2:
            exclude_cyb = st.checkbox("排除创业板（300开头）", value=True,
                                     help="300首板20cm相当于2板，连板概率小")

        with col3:
            exclude_one_word = st.checkbox("排除一字板", value=True,
                                          help="一字板缺乏充分换手，后续动力不足")

        top_n = st.slider(
            "显示前N只股票",
            min_value=5,
            max_value=50,
            value=20,
            step=5,
            help="按综合评分从高到低显示"
        )

    st.markdown("---")

    # 开始筛选按钮
    if st.button("🔍 开始筛选", type="primary", use_container_width=True):

        with st.spinner("正在获取涨停板数据..."):

            # 创建数据获取器和引擎
            data_fetcher = MomentumFilterData()
            engine = MomentumFilterEngine()

            # 获取涨停板数据
            success, df, message = data_fetcher.get_limit_up_stocks(trade_date)

            if not success or df is None or df.empty:
                st.error(f"❌ {message}")
                st.info("💡 提示: 请检查日期是否为交易日，或稍后重试")
                return

            st.success(f"✅ {message}")

            # 显示原始数据
            with st.expander("📊 原始涨停板数据", expanded=False):
                st.dataframe(df, use_container_width=True)

        with st.spinner("正在筛选优质首板..."):

            # 筛选首板股票
            filtered_df = engine.filter_first_board_stocks(
                df,
                max_price=max_price,
                max_market_cap=max_market_cap,
                exclude_sh=exclude_sh,
                exclude_cyb=exclude_cyb,
                exclude_one_word=exclude_one_word
            )

            if filtered_df.empty:
                st.warning("⚠️ 没有符合条件的股票，请放宽筛选条件")
                return

        with st.spinner("正在评分排序..."):

            # 对股票进行评分
            scored_df = engine.score_stocks(filtered_df)

            # 获取前N只股票
            top_stocks = engine.get_top_stocks(top_n)

        st.success(f"✅ 筛选完成！共找到 {len(filtered_df)} 只符合条件的股票")

        # 显示结果
        display_results(top_stocks, scored_df)

        # 保存到session state供后续使用
        st.session_state['momentum_filter_results'] = top_stocks
        st.session_state['momentum_filter_all'] = scored_df


def display_results(top_stocks: pd.DataFrame, all_stocks: pd.DataFrame):
    """显示筛选结果"""

    st.markdown("---")
    st.subheader("📈 筛选结果")

    # 统计信息
    col1, col2, col3, col4 = st.columns(4)

    with col1:
        st.metric("符合条件股票数", len(all_stocks))

    with col2:
        avg_score = all_stocks['total_score'].mean()
        st.metric("平均得分", f"{avg_score:.1f}")

    with col3:
        max_score = all_stocks['total_score'].max()
        st.metric("最高得分", f"{max_score:.1f}")

    with col4:
        min_score = all_stocks['total_score'].min()
        st.metric("最低得分", f"{min_score:.1f}")

    # Top N 股票详细信息
    st.markdown("### 🏆 Top股票详情")

    for idx, row in top_stocks.iterrows():
        display_stock_card(row)

    # 评分分布图
    st.markdown("---")
    st.subheader("📊 评分分布分析")

    col1, col2 = st.columns(2)

    with col1:
        # 总分分布直方图
        fig = px.histogram(
            all_stocks,
            x='total_score',
            nbins=20,
            title="总分分布",
            labels={'total_score': '综合评分', 'count': '股票数量'}
        )
        fig.update_layout(showlegend=False)
        st.plotly_chart(fig, use_container_width=True)

    with col2:
        # Top股票评分对比
        if len(top_stocks) > 0:
            top_10 = top_stocks.head(10)
            fig = px.bar(
                top_10,
                x='name',
                y='total_score',
                title="Top10股票评分对比",
                labels={'name': '股票名称', 'total_score': '综合评分'},
                text='total_score'
            )
            fig.update_traces(texttemplate='%{text:.1f}', textposition='outside')
            st.plotly_chart(fig, use_container_width=True)

    # 各维度评分雷达图
    st.markdown("### 🎯 评分维度分析")

    display_score_radar(top_stocks)

    # 完整数据表格
    st.markdown("---")
    st.subheader("📋 完整数据表格")

    # 选择要显示的列
    display_columns = [
        'code', 'name', 'price', 'total_score',
        'circulation_market_cap', 'turnover_rate',
        'limit_time', 'broken_times', 'sector'
    ]

    # 过滤存在的列
    available_columns = [col for col in display_columns if col in all_stocks.columns]

    # 重命名列名（中文）
    column_rename = {
        'code': '代码',
        'name': '名称',
        'price': '股价',
        'total_score': '综合评分',
        'circulation_market_cap': '流通市值(亿)',
        'turnover_rate': '换手率(%)',
        'limit_time': '涨停时间',
        'broken_times': '炸板次数',
        'sector': '所属板块'
    }

    display_df = all_stocks[available_columns].copy()
    display_df = display_df.rename(columns=column_rename)

    # 格式化数值
    if '股价' in display_df.columns:
        display_df['股价'] = display_df['股价'].apply(lambda x: f"{x:.2f}" if pd.notna(x) else "N/A")

    if '综合评分' in display_df.columns:
        display_df['综合评分'] = display_df['综合评分'].apply(lambda x: f"{x:.1f}" if pd.notna(x) else "N/A")

    if '流通市值(亿)' in display_df.columns:
        display_df['流通市值(亿)'] = display_df['流通市值(亿)'].apply(lambda x: f"{x:.2f}" if pd.notna(x) else "N/A")

    if '换手率(%)' in display_df.columns:
        display_df['换手率(%)'] = display_df['换手率(%)'].apply(lambda x: f"{x:.2f}" if pd.notna(x) else "N/A")

    st.dataframe(display_df, use_container_width=True, height=400)

    # 下载按钮
    csv = all_stocks.to_csv(index=False, encoding='utf-8-sig')
    st.download_button(
        label="📥 下载完整数据（CSV）",
        data=csv,
        file_name=f"momentum_filter_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
        mime="text/csv"
    )


def display_stock_card(row: pd.Series):
    """显示单个股票卡片"""

    code = row.get('code', 'N/A')
    name = row.get('name', 'N/A')
    price = row.get('price', 0)
    total_score = row.get('total_score', 0)

    # 创建卡片
    with st.container():
        col1, col2, col3, col4 = st.columns([2, 2, 3, 3])

        with col1:
            st.markdown(f"### 【{name}】")
            st.markdown(f"**代码**: {code}")

        with col2:
            st.metric("股价", f"{price:.2f}元")
            if 'circulation_market_cap' in row:
                cap = row['circulation_market_cap']
                if pd.notna(cap):
                    st.metric("流通市值", f"{cap:.2f}亿")

        with col3:
            st.metric("综合评分", f"{total_score:.1f}/100")

            # 评分等级
            if total_score >= 80:
                grade = "🌟🌟🌟 优秀"
                color = "green"
            elif total_score >= 70:
                grade = "⭐⭐ 良好"
                color = "blue"
            elif total_score >= 60:
                grade = "⭐ 中等"
                color = "orange"
            else:
                grade = "💫 一般"
                color = "gray"

            st.markdown(f"**等级**: :{color}[{grade}]")

        with col4:
            # 关键指标
            if 'limit_time' in row and pd.notna(row['limit_time']):
                st.write(f"⏰ 涨停时间: {row['limit_time']}")

            if 'turnover_rate' in row and pd.notna(row['turnover_rate']):
                st.write(f"🔄 换手率: {row['turnover_rate']:.2f}%")

            if 'broken_times' in row and pd.notna(row['broken_times']):
                times = int(row['broken_times'])
                st.write(f"💥 炸板次数: {times}次")

            if 'sector' in row and pd.notna(row['sector']):
                st.write(f"📊 板块: {row['sector']}")

        # 评分详情
        with st.expander("📋 评分详情"):
            score_cols = st.columns(5)

            score_items = [
                ('时间', 'time_score', 30),
                ('封单', 'seal_score', 25),
                ('炸板', 'broken_score', 20),
                ('换手', 'turnover_score', 15),
                ('市值', 'cap_score', 10)
            ]

            for i, (label, key, max_score) in enumerate(score_items):
                with score_cols[i]:
                    score = row.get(key, 0)
                    if pd.notna(score):
                        percentage = (score / max_score) * 100
                        st.metric(label, f"{score:.1f}/{max_score}")
                        st.progress(percentage / 100)

        st.markdown("---")


def display_score_radar(stocks_df: pd.DataFrame):
    """显示评分雷达图"""

    if stocks_df.empty:
        return

    # 选择前5只股票
    top_5 = stocks_df.head(5)

    # 准备雷达图数据
    categories = ['涨停时间', '封单强度', '炸板次数', '换手率', '市值']
    score_columns = ['time_score', 'seal_score', 'broken_score', 'turnover_score', 'cap_score']
    max_scores = [30, 25, 20, 15, 10]

    fig = go.Figure()

    for idx, row in top_5.iterrows():
        name = row.get('name', 'N/A')

        # 计算百分比分数
        scores = []
        for col, max_score in zip(score_columns, max_scores):
            score = row.get(col, 0)
            if pd.notna(score):
                percentage = (score / max_score) * 100
                scores.append(percentage)
            else:
                scores.append(0)

        fig.add_trace(go.Scatterpolar(
            r=scores,
            theta=categories,
            fill='toself',
            name=name
        ))

    fig.update_layout(
        polar=dict(
            radialaxis=dict(
                visible=True,
                range=[0, 100]
            )
        ),
        showlegend=True,
        title="Top5股票评分维度对比（百分比）"
    )

    st.plotly_chart(fig, use_container_width=True)
