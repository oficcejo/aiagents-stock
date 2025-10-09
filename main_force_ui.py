#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
主力选股UI模块
"""

import streamlit as st
from datetime import datetime, timedelta
from main_force_analysis import MainForceAnalyzer
from main_force_pdf_generator import display_report_download_section
import pandas as pd

def display_main_force_selector():
    """显示主力选股界面"""
    
    st.markdown("## 🎯 主力选股 - 智能筛选优质标的")
    st.markdown("---")
    
    st.markdown("""
    ### 功能说明
    
    本功能通过以下步骤筛选优质股票：
    
    1. **数据获取**: 使用问财获取指定日期以来主力资金净流入前100名股票
    2. **智能筛选**: 过滤掉涨幅过高、市值不符的股票
    3. **AI分析**: 调用资金流向、行业板块、财务基本面三大分析师团队
    4. **综合决策**: 资深研究员综合评估，精选3-5只优质标的
    
    **筛选标准**:
    - ✅ 主力资金净流入较多
    - ✅ 区间涨跌幅适中（避免追高）
    - ✅ 财务基本面良好
    - ✅ 行业前景明朗
    - ✅ 综合素质优秀
    """)
    
    st.markdown("---")
    
    # 参数设置
    col1, col2, col3 = st.columns(3)
    
    with col1:
        date_option = st.selectbox(
            "选择时间区间",
            ["最近3个月", "最近6个月", "最近1年", "自定义日期"]
        )
        
        if date_option == "最近3个月":
            days_ago = 90
            start_date = None
        elif date_option == "最近6个月":
            days_ago = 180
            start_date = None
        elif date_option == "最近1年":
            days_ago = 365
            start_date = None
        else:
            custom_date = st.date_input(
                "选择开始日期",
                value=datetime.now() - timedelta(days=90)
            )
            start_date = f"{custom_date.year}年{custom_date.month}月{custom_date.day}日"
            days_ago = None
    
    with col2:
        final_n = st.slider(
            "最终精选数量",
            min_value=3,
            max_value=10,
            value=5,
            step=1,
            help="最终推荐的股票数量"
        )
    
    with col3:
        st.info("💡 系统将获取前100名股票，进行整体分析后精选优质标的")
    
    # 高级选项
    with st.expander("⚙️ 高级筛选参数"):
        col1, col2, col3 = st.columns(3)
        
        with col1:
            max_change = st.number_input(
                "最大涨跌幅(%)",
                min_value=10.0,
                max_value=100.0,
                value=30.0,
                step=5.0,
                help="过滤掉涨幅过高的股票，避免追高"
            )
        
        with col2:
            min_cap = st.number_input(
                "最小市值(亿)",
                min_value=10.0,
                max_value=500.0,
                value=50.0,
                step=10.0
            )
        
        with col3:
            max_cap = st.number_input(
                "最大市值(亿)",
                min_value=100.0,
                max_value=50000.0,
                value=5000.0,
                step=100.0
            )
    
    # 模型选择
    model = st.selectbox(
        "选择AI模型",
        ["deepseek-chat", "deepseek-reasoner"],
        help="deepseek-chat速度快，deepseek-reasoner推理能力强"
    )
    
    st.markdown("---")
    
    # 开始分析按钮
    if st.button("🚀 开始主力选股", type="primary", use_container_width=True):
        
        with st.spinner("正在获取数据并分析，这可能需要几分钟..."):
            
            # 创建分析器
            analyzer = MainForceAnalyzer(model=model)
            
            # 运行分析
            result = analyzer.run_full_analysis(
                start_date=start_date,
                days_ago=days_ago,
                final_n=final_n
            )
            
            # 保存结果到session_state
            st.session_state.main_force_result = result
            st.session_state.main_force_analyzer = analyzer
        
        # 显示结果
        if result['success']:
            st.success(f"✅ 分析完成！共筛选出 {len(result['final_recommendations'])} 只优质标的")
            st.rerun()
        else:
            st.error(f"❌ 分析失败: {result.get('error', '未知错误')}")
    
    # 显示分析结果
    if 'main_force_result' in st.session_state:
        result = st.session_state.main_force_result
        
        if result['success']:
            display_analysis_results(result, st.session_state.get('main_force_analyzer'))

def display_analysis_results(result: dict, analyzer):
    """显示分析结果"""
    
    st.markdown("---")
    st.markdown("## 📊 分析结果")
    
    # 统计信息
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.metric("获取股票数", result['total_stocks'])
    
    with col2:
        st.metric("筛选后", result['filtered_stocks'])
    
    with col3:
        st.metric("最终推荐", len(result['final_recommendations']))
    
    st.markdown("---")
    
    # 显示AI分析师完整报告
    if analyzer and hasattr(analyzer, 'fund_flow_analysis'):
        display_analyst_reports(analyzer)
    
    st.markdown("---")
    
    # 显示推荐股票
    if result['final_recommendations']:
        st.markdown("### ⭐ 精选推荐")
        
        for rec in result['final_recommendations']:
            with st.expander(
                f"【第{rec['rank']}名】{rec['symbol']} - {rec['name']}", 
                expanded=(rec['rank'] <= 3)
            ):
                display_recommendation_detail(rec)
    
    # 显示候选股票列表
    if analyzer and analyzer.raw_stocks is not None and not analyzer.raw_stocks.empty:
        st.markdown("---")
        st.markdown("### 📋 候选股票列表（筛选后）")
        
        # 选择关键列显示
        display_cols = ['股票代码', '股票简称']
        
        # 添加行业列
        industry_cols = [col for col in analyzer.raw_stocks.columns if '行业' in col]
        if industry_cols:
            display_cols.append(industry_cols[0])
        
        # 添加区间主力资金净流入（智能匹配）
        main_fund_col = None
        main_fund_patterns = [
            '区间主力资金流向',      # 实际列名
            '区间主力资金净流入', 
            '主力资金流向',
            '主力资金净流入', 
            '主力净流入', 
            '主力资金'
        ]
        for pattern in main_fund_patterns:
            matching = [col for col in analyzer.raw_stocks.columns if pattern in col]
            if matching:
                main_fund_col = matching[0]
                break
        if main_fund_col:
            display_cols.append(main_fund_col)
        
        # 添加区间涨跌幅（前复权）（智能匹配）
        interval_pct_col = None
        interval_pct_patterns = [
            '区间涨跌幅:前复权', '区间涨跌幅:前复权(%)', '区间涨跌幅(%)', 
            '区间涨跌幅', '涨跌幅:前复权', '涨跌幅:前复权(%)', '涨跌幅(%)', '涨跌幅'
        ]
        for pattern in interval_pct_patterns:
            matching = [col for col in analyzer.raw_stocks.columns if pattern in col]
            if matching:
                interval_pct_col = matching[0]
                break
        if interval_pct_col:
            display_cols.append(interval_pct_col)
        
        # 添加市值、市盈率、市净率
        for col_name in ['总市值', '市盈率', '市净率']:
            matching_cols = [col for col in analyzer.raw_stocks.columns if col_name in col]
            if matching_cols:
                display_cols.append(matching_cols[0])
        
        # 选择存在的列
        final_cols = [col for col in display_cols if col in analyzer.raw_stocks.columns]
        
        # 调试信息：显示找到的列名
        with st.expander("🔍 调试信息 - 查看数据列", expanded=False):
            st.caption("所有可用列:")
            cols_list = list(analyzer.raw_stocks.columns)
            st.write(cols_list)
            st.caption(f"\n已选择显示的列: {final_cols}")
            if main_fund_col:
                st.success(f"✅ 找到主力资金列: {main_fund_col}")
            else:
                st.warning("⚠️ 未找到主力资金列")
            if interval_pct_col:
                st.success(f"✅ 找到涨跌幅列: {interval_pct_col}")
            else:
                st.warning("⚠️ 未找到涨跌幅列")
        
        # 显示DataFrame
        display_df = analyzer.raw_stocks[final_cols].copy()
        st.dataframe(display_df, use_container_width=True, height=400)
        
        # 显示统计
        st.caption(f"共 {len(display_df)} 只候选股票，显示 {len(final_cols)} 个字段")
        
        # 下载按钮
        csv = display_df.to_csv(index=False, encoding='utf-8-sig')
        st.download_button(
            label="📥 下载候选列表CSV",
            data=csv,
            file_name=f"main_force_stocks_{datetime.now().strftime('%Y%m%d')}.csv",
            mime="text/csv"
        )
    
    # 显示PDF报告下载区域
    if analyzer and result:
        display_report_download_section(analyzer, result)

def display_recommendation_detail(rec: dict):
    """显示单个推荐股票的详细信息"""
    
    col1, col2 = st.columns([1, 1])
    
    with col1:
        st.markdown("#### 📌 推荐理由")
        for reason in rec.get('reasons', []):
            st.markdown(f"- {reason}")
        
        st.markdown("#### 💡 投资亮点")
        st.info(rec.get('highlights', 'N/A'))
    
    with col2:
        st.markdown("#### 📊 投资建议")
        st.markdown(f"**建议仓位**: {rec.get('position', 'N/A')}")
        st.markdown(f"**投资周期**: {rec.get('investment_period', 'N/A')}")
        
        st.markdown("#### ⚠️ 风险提示")
        st.warning(rec.get('risks', 'N/A'))
    
    # 显示股票详细数据
    if 'stock_data' in rec:
        st.markdown("---")
        st.markdown("#### 📊 股票详细数据")
        
        stock_data = rec['stock_data']
        
        # 创建数据展示
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.metric("股票代码", stock_data.get('股票代码', 'N/A'))
            
            # 显示行业
            industry_keys = [k for k in stock_data.keys() if '行业' in k]
            if industry_keys:
                st.metric("所属行业", stock_data.get(industry_keys[0], 'N/A'))
        
        with col2:
            # 显示主力资金
            fund_keys = [k for k in stock_data.keys() if '主力' in k and '净流入' in k]
            if fund_keys:
                fund_value = stock_data.get(fund_keys[0], 'N/A')
                if isinstance(fund_value, (int, float)):
                    st.metric("主力资金净流入", f"{fund_value/100000000:.2f}亿")
                else:
                    st.metric("主力资金净流入", str(fund_value))
        
        with col3:
            # 显示涨跌幅
            change_keys = [k for k in stock_data.keys() if '涨跌幅' in k]
            if change_keys:
                change_value = stock_data.get(change_keys[0], 'N/A')
                if isinstance(change_value, (int, float)):
                    st.metric("区间涨跌幅", f"{change_value:.2f}%")
                else:
                    st.metric("区间涨跌幅", str(change_value))
        
        # 显示其他关键指标
        st.markdown("**其他关键指标：**")
        metrics_col1, metrics_col2, metrics_col3 = st.columns(3)
        
        with metrics_col1:
            if '市盈率' in stock_data or any('市盈率' in k for k in stock_data.keys()):
                pe_keys = [k for k in stock_data.keys() if '市盈率' in k]
                if pe_keys:
                    st.caption(f"市盈率: {stock_data.get(pe_keys[0], 'N/A')}")
        
        with metrics_col2:
            if '市净率' in stock_data or any('市净率' in k for k in stock_data.keys()):
                pb_keys = [k for k in stock_data.keys() if '市净率' in k]
                if pb_keys:
                    st.caption(f"市净率: {stock_data.get(pb_keys[0], 'N/A')}")
        
        with metrics_col3:
            if '总市值' in stock_data or any('总市值' in k for k in stock_data.keys()):
                cap_keys = [k for k in stock_data.keys() if '总市值' in k]
                if cap_keys:
                    st.caption(f"总市值: {stock_data.get(cap_keys[0], 'N/A')}")

def display_analyst_reports(analyzer):
    """显示AI分析师完整报告"""
    
    st.markdown("### 🤖 AI分析师团队完整报告")
    
    # 创建三个标签页
    tab1, tab2, tab3 = st.tabs(["💰 资金流向分析", "📊 行业板块分析", "📈 财务基本面分析"])
    
    with tab1:
        st.markdown("#### 💰 资金流向分析师报告")
        st.markdown("---")
        if hasattr(analyzer, 'fund_flow_analysis') and analyzer.fund_flow_analysis:
            st.markdown(analyzer.fund_flow_analysis)
        else:
            st.info("暂无资金流向分析报告")
    
    with tab2:
        st.markdown("#### 📊 行业板块及市场热点分析师报告")
        st.markdown("---")
        if hasattr(analyzer, 'industry_analysis') and analyzer.industry_analysis:
            st.markdown(analyzer.industry_analysis)
        else:
            st.info("暂无行业板块分析报告")
    
    with tab3:
        st.markdown("#### 📈 财务基本面分析师报告")
        st.markdown("---")
        if hasattr(analyzer, 'fundamental_analysis') and analyzer.fundamental_analysis:
            st.markdown(analyzer.fundamental_analysis)
        else:
            st.info("暂无财务基本面分析报告")

def format_number(value, unit='', suffix=''):
    """格式化数字显示"""
    if value is None or value == 'N/A':
        return 'N/A'
    
    try:
        num = float(value)
        
        # 如果单位是亿，需要转换
        if unit == '亿':
            if abs(num) >= 100000000:  # 大于1亿（以元为单位）
                num = num / 100000000
            elif abs(num) < 100:  # 小于100，可能已经是亿
                pass
            else:  # 100-100000000之间，可能是万
                num = num / 10000
        
        # 格式化显示
        if abs(num) >= 1000:
            formatted = f"{num:,.2f}"
        elif abs(num) >= 1:
            formatted = f"{num:.2f}"
        else:
            formatted = f"{num:.4f}"
        
        return f"{formatted}{suffix}"
    except (ValueError, TypeError):
        return str(value)

