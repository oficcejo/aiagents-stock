"""
智瞰龙虎UI界面模块
展示龙虎榜分析结果和推荐股票
"""

import streamlit as st
import plotly.graph_objects as go
import plotly.express as px
import pandas as pd
from datetime import datetime, timedelta
import time
import base64

from longhubang_engine import LonghubangEngine
from longhubang_pdf import LonghubangPDFGenerator


def display_longhubang():
    """显示智瞰龙虎主界面"""
    
    st.markdown("""
    <div class="top-nav">
        <h1 class="nav-title">🎯 智瞰龙虎 - AI驱动的龙虎榜分析</h1>
        <p class="nav-subtitle">Multi-Agent Dragon Tiger Analysis | 游资·个股·题材·风险多维分析</p>
    </div>
    """, unsafe_allow_html=True)
    
    st.markdown("---")
    
    # 功能说明
    with st.expander("💡 智瞰龙虎系统介绍", expanded=False):
        st.markdown("""
        ### 🌟 系统特色
        
        **智瞰龙虎**是基于多AI智能体的龙虎榜深度分析系统，通过5位专业分析师的协同工作，
        为您挖掘次日大概率上涨的潜力股票。
        
        ### 🤖 AI分析师团队
        
        1. **🎯 游资行为分析师**
           - 识别活跃游资及其操作风格
           - 分析游资席位的进出特征
           - 研判游资对个股的态度
        
        2. **📈 个股潜力分析师**
           - 从龙虎榜数据挖掘潜力股
           - 识别次日大概率上涨的股票
           - 分析资金动向和技术形态
        
        3. **🔥 题材追踪分析师**
           - 识别当前热点题材和概念
           - 分析题材的炒作周期
           - 预判题材的持续性
        
        4. **⚠️ 风险控制专家**
           - 识别高风险股票和陷阱
           - 分析游资出货信号
           - 提供风险管理建议
        
        5. **👔 首席策略师**
           - 综合所有分析师意见
           - 给出最终推荐股票清单
           - 提供具体操作策略
        
        ### 📊 数据来源
        
        数据来自**StockAPI龙虎榜接口**，包括：
        - 游资上榜交割单历史数据
        - 股票买卖金额和净流入
        - 热门概念和题材
        - 更新时间：交易日下午5点40
        
        ### 🎯 核心功能
        
        - ✅ **潜力股挖掘** - AI识别次日大概率上涨股票
        - ✅ **游资追踪** - 跟踪活跃游资的操作
        - ✅ **题材识别** - 发现热点题材和龙头股
        - ✅ **风险提示** - 识别高风险股票和陷阱
        - ✅ **历史记录** - 存储所有龙虎榜数据
        - ✅ **PDF报告** - 生成专业分析报告
        """)
    
    st.markdown("---")
    
    # 创建标签页
    tab1, tab2, tab3 = st.tabs([
        "📊 龙虎榜分析",
        "📚 历史报告",
        "📈 数据统计"
    ])
    
    with tab1:
        display_analysis_tab()
    
    with tab2:
        display_history_tab()
    
    with tab3:
        display_statistics_tab()


def display_analysis_tab():
    """显示分析标签页"""
    
    # 检查是否触发批量分析（不立即删除标志）
    if st.session_state.get('longhubang_batch_trigger'):
        run_longhubang_batch_analysis()
        return
    
    st.subheader("🔍 龙虎榜综合分析")
    
    # 参数设置
    col1, col2, col3 = st.columns([2, 2, 2])
    
    with col1:
        analysis_mode = st.selectbox(
            "分析模式",
            ["指定日期", "最近N天"],
            help="选择分析特定日期还是最近几天的数据"
        )
    
    with col2:
        if analysis_mode == "指定日期":
            selected_date = st.date_input(
                "选择日期",
                value=datetime.now() - timedelta(days=1),
                help="选择要分析的龙虎榜日期"
            )
        else:
            days = st.number_input(
                "最近天数",
                min_value=1,
                max_value=10,
                value=1,
                help="分析最近N天的龙虎榜数据"
            )
    
    with col3:
        selected_model = st.selectbox(
            "AI模型",
            ["deepseek-chat", "deepseek-reasoner"],
            help="Reasoner模型提供更强的推理能力"
        )
    
    # 分析按钮
    col1, col2, col3 = st.columns([2, 2, 2])
    
    with col1:
        analyze_button = st.button("🚀 开始分析", type="primary", width='stretch')
    
    with col2:
        if st.button("🔄 清除结果", width='stretch'):
            if 'longhubang_result' in st.session_state:
                del st.session_state.longhubang_result
            st.success("已清除分析结果")
            st.rerun()
    
    st.markdown("---")
    
    # 开始分析
    if analyze_button:
        # 清除之前的结果
        if 'longhubang_result' in st.session_state:
            del st.session_state.longhubang_result
        
        # 准备参数
        if analysis_mode == "指定日期":
            date_str = selected_date.strftime('%Y-%m-%d')
            run_longhubang_analysis(model=selected_model, date=date_str)
        else:
            run_longhubang_analysis(model=selected_model, days=days)
    
    # 显示分析结果
    if 'longhubang_result' in st.session_state:
        result = st.session_state.longhubang_result
        
        if result.get("success"):
            display_analysis_results(result)
        else:
            st.error(f"❌ 分析失败: {result.get('error', '未知错误')}")


def run_longhubang_analysis(model="deepseek-chat", date=None, days=1):
    """运行龙虎榜分析"""
    
    # 进度显示
    progress_bar = st.progress(0)
    status_text = st.empty()
    
    try:
        status_text.text("🚀 初始化分析引擎...")
        progress_bar.progress(5)
        
        engine = LonghubangEngine(model=model)
        
        status_text.text("📊 正在获取龙虎榜数据...")
        progress_bar.progress(15)
        
        # 运行分析
        result = engine.run_comprehensive_analysis(date=date, days=days)
        
        progress_bar.progress(90)
        
        if result.get("success"):
            # 保存结果
            st.session_state.longhubang_result = result
            
            progress_bar.progress(100)
            status_text.text("✅ 分析完成！")
            
            time.sleep(1)
            status_text.empty()
            progress_bar.empty()
            
            # 自动刷新显示结果
            st.rerun()
        else:
            st.error(f"❌ 分析失败: {result.get('error', '未知错误')}")
    
    except Exception as e:
        st.error(f"❌ 分析过程出错: {str(e)}")
        import traceback
        st.code(traceback.format_exc())
    finally:
        progress_bar.empty()
        status_text.empty()


def display_analysis_results(result):
    """显示分析结果"""
    
    st.success("✅ 龙虎榜分析完成！")
    st.info(f"📅 分析时间: {result.get('timestamp', 'N/A')}")
    
    # 数据概况
    data_info = result.get('data_info', {})
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("龙虎榜记录", f"{data_info.get('total_records', 0)} 条")
    
    with col2:
        st.metric("涉及股票", f"{data_info.get('total_stocks', 0)} 只")
    
    with col3:
        st.metric("涉及游资", f"{data_info.get('total_youzi', 0)} 个")
    
    with col4:
        recommended = result.get('recommended_stocks', [])
        st.metric("推荐股票", f"{len(recommended)} 只", delta="AI筛选")
    
    # PDF导出功能
    display_pdf_export_section(result)
    
    st.markdown("---")
    
    # 创建子标签页
    tab1, tab2, tab3, tab4, tab5 = st.tabs([
        "🏆 AI评分排名",
        "🎯 推荐股票",
        "🤖 AI分析师报告",
        "📊 数据详情",
        "📈 可视化图表"
    ])
    
    with tab1:
        display_scoring_ranking(result)
    
    with tab2:
        display_recommended_stocks(result)
    
    with tab3:
        display_agents_reports(result)
    
    with tab4:
        display_data_details(result)
    
    with tab5:
        display_visualizations(result)


def display_scoring_ranking(result):
    """显示AI智能评分排名"""
    
    st.subheader("🏆 AI智能评分排名")
    
    scoring_df = result.get('scoring_ranking')
    
    if scoring_df is None or (hasattr(scoring_df, 'empty') and scoring_df.empty):
        st.warning("暂无评分数据")
        return
    
    # 评分说明
    with st.expander("📖 评分维度说明", expanded=False):
        st.markdown("""
        ### 📊 AI智能评分体系 (总分100分)
        
        #### 1️⃣ 买入资金含金量 (0-30分)
        - **顶级游资**（赵老哥、章盟主、92科比等）：每个 +10分
        - **知名游资**（深股通、中信证券等）：每个 +5分
        - **普通游资**：每个 +1.5分
        
        #### 2️⃣ 净买入额评分 (0-25分)
        - 净流入 < 1000万：0-10分
        - 净流入 1000-5000万：10-18分
        - 净流入 5000万-1亿：18-22分
        - 净流入 > 1亿：22-25分
        
        #### 3️⃣ 卖出压力评分 (0-20分)
        - 卖出比例 0-10%：20分 ✨（压力极小）
        - 卖出比例 10-30%：15-20分（压力较小）
        - 卖出比例 30-50%：10-15分（压力中等）
        - 卖出比例 50-80%：5-10分（压力较大）
        - 卖出比例 > 80%：0-5分（压力极大）
        
        #### 4️⃣ 机构共振评分 (0-15分)
        - **机构+游资共振**：15分 ⭐（最强信号）
        - 仅机构买入：8-12分
        - 仅游资买入：5-10分
        
        #### 5️⃣ 其他加分项 (0-10分)
        - **主力集中度**：席位越少越集中 (+1-3分)
        - **热门概念**：AI、新能源、芯片等 (+0-3分)
        - **连续上榜**：连续多日上榜 (+0-2分)
        - **买卖比例优秀**：买入远大于卖出 (+0-2分)
        
        ---
        
        💡 **评分越高，表示该股票受到资金青睐程度越高！**  
        ⚠️ **但仍需结合市场环境、技术面等因素综合判断！**
        """)
    
    st.markdown("---")
    
    # 显示TOP10评分表格
    st.markdown("### 🥇 TOP10 综合评分排名")
    
    # 兼容历史数据与类型统一，避免 Arrow 序列化错误
    if isinstance(scoring_df, list):
        scoring_df = pd.DataFrame(scoring_df)

    numeric_cols = ['排名','综合评分','资金含金量','净买入额','卖出压力','机构共振','加分项','顶级游资','买方数','净流入']
    for col in numeric_cols:
        if col in scoring_df.columns:
            scoring_df[col] = pd.to_numeric(scoring_df[col], errors='coerce')

    text_cols = ['股票名称','股票代码','机构参与']
    for col in text_cols:
        if col in scoring_df.columns:
            scoring_df[col] = scoring_df[col].astype(str)

    top10_df = scoring_df.head(10).copy()
    if '排名' in top10_df.columns:
        top10_df['排名'] = pd.to_numeric(top10_df['排名'], errors='coerce').fillna(0).astype(int)
    
    # 格式化显示
    st.dataframe(
        top10_df,
        column_config={
            "排名": st.column_config.NumberColumn("排名", format="%d", width="small"),
            "股票名称": st.column_config.TextColumn("股票名称", width="medium"),
            "股票代码": st.column_config.TextColumn("代码", width="small"),
            "综合评分": st.column_config.NumberColumn(
                "综合评分",
                format="%.1f",
                help="总分100分"
            ),
            "资金含金量": st.column_config.ProgressColumn(
                "资金含金量",
                format="%d分",
                min_value=0,
                max_value=30
            ),
            "净买入额": st.column_config.ProgressColumn(
                "净买入额",
                format="%d分",
                min_value=0,
                max_value=25
            ),
            "卖出压力": st.column_config.ProgressColumn(
                "卖出压力",
                format="%d分",
                min_value=0,
                max_value=20
            ),
            "机构共振": st.column_config.ProgressColumn(
                "机构共振",
                format="%d分",
                min_value=0,
                max_value=15
            ),
            "加分项": st.column_config.ProgressColumn(
                "加分项",
                format="%d分",
                min_value=0,
                max_value=10
            ),
            "顶级游资": st.column_config.NumberColumn("顶级游资", format="%d家"),
            "买方数": st.column_config.NumberColumn("买方数", format="%d家"),
            "机构参与": st.column_config.TextColumn("机构参与"),
            "净流入": st.column_config.NumberColumn("净流入(元)", format="%.2f")
        },
        hide_index=True,
        width='stretch'
    )
    
    # 一键批量分析功能
    st.markdown("---")
    
    col_batch1, col_batch2, col_batch3 = st.columns([2, 1, 1])
    with col_batch1:
        st.markdown("#### 🚀 批量深度分析")
        st.caption("对TOP10股票进行完整的AI团队分析，获取投资评级和关键价位")
    
    with col_batch2:
        batch_count = st.selectbox(
            "分析数量",
            options=[3, 5, 10],
            index=0,
            help="选择分析前N只股票",
            key="batch_count_selector"
        )
        # 同步更新session_state中的batch_count
        st.session_state.batch_count = batch_count
    
    with col_batch3:
        st.write("")  # 占位
        if st.button("🚀 开始批量分析", type="primary", width='stretch'):
            # 提取股票代码
            stock_codes = top10_df.head(batch_count)['股票代码'].tolist()
            
            # 存储到session_state，触发批量分析
            st.session_state.longhubang_batch_codes = stock_codes
            st.session_state.longhubang_batch_trigger = True
            st.rerun()
    
    st.markdown("---")
    
    # 评分分布图表
    st.markdown("### 📊 评分分布可视化")
    
    col1, col2 = st.columns(2)
    
    with col1:
        # 综合评分柱状图
        fig1 = px.bar(
            top10_df,
            x='股票名称',
            y='综合评分',
            title='TOP10 综合评分对比',
            text='综合评分',
            color='综合评分',
            color_continuous_scale='RdYlGn'
        )
        fig1.update_traces(texttemplate='%{text:.1f}分', textposition='outside')
        fig1.update_layout(
            xaxis_tickangle=-45,
            showlegend=False,
            height=400
        )
        st.plotly_chart(fig1, config={'displayModeBar': False}, use_container_width=True)
    
    with col2:
        # 五维评分雷达图（显示批量分析数量的股票）
        if len(top10_df) > 0:
            display_count = min(5, len(top10_df))
            
            fig2 = go.Figure()
            
            # 为每只股票添加雷达图
            colors = ['#FF6B6B', '#4ECDC4', '#45B7D1', '#96CEB4', '#FFEAA7']
            for i in range(display_count):
                stock = top10_df.iloc[i]
                
                fig2.add_trace(go.Scatterpolar(
                    r=[
                        stock['资金含金量'] / 30 * 100,
                        stock['净买入额'] / 25 * 100,
                        stock['卖出压力'] / 20 * 100,
                        stock['机构共振'] / 15 * 100,
                        stock['加分项'] / 10 * 100
                    ],
                    theta=['资金含金量', '净买入额', '卖出压力', '机构共振', '加分项'],
                    fill='toself',
                    name=f"{stock['股票名称']}",
                    line_color=colors[i % len(colors)],
                    fillcolor=colors[i % len(colors)],
                    opacity=0.6
                ))
            
            fig2.update_layout(
                polar=dict(
                    radialaxis=dict(
                        visible=True,
                        range=[0, 100]
                    )
                ),
                showlegend=True,
                title=f"🏆 TOP{display_count} 五维评分对比",
                height=400,
                legend=dict(
                    orientation="h",
                    yanchor="auto",
                    y=-0.2,
                    xanchor="center",
                    x=0.5
                )
            )
            st.plotly_chart(fig2, config={'displayModeBar': False}, use_container_width=True)
    
    st.markdown("---")
    
    # 完整排名表格
    st.markdown("### 📋 完整评分排名")
    
    st.dataframe(
        scoring_df,
        column_config={
            "排名": st.column_config.NumberColumn("排名", format="%d", width="small"),
            "股票名称": st.column_config.TextColumn("股票名称"),
            "股票代码": st.column_config.TextColumn("代码"),
            "综合评分": st.column_config.NumberColumn("综合评分", format="%.1f"),
            "顶级游资": st.column_config.NumberColumn("顶级游资", format="%d家"),
            "买方数": st.column_config.NumberColumn("买方数", format="%d家"),
            "机构参与": st.column_config.TextColumn("机构"),
            "净流入": st.column_config.NumberColumn("净流入(元)", format="%.2f")
        },
        hide_index=True,
        width='stretch'
    )


def display_recommended_stocks(result):
    """显示推荐股票"""
    
    st.subheader("🎯 AI推荐股票")
    
    recommended = result.get('recommended_stocks', [])
    
    if not recommended:
        st.warning("暂无推荐股票")
        return
    
    st.info(f"💡 基于5位AI分析师的综合分析，系统识别出以下 **{len(recommended)}** 只潜力股票")
    
    # 创建DataFrame
    df_recommended = pd.DataFrame(recommended)
    
    # 显示表格
    st.dataframe(
        df_recommended,
        column_config={
            "rank": st.column_config.NumberColumn("排名", format="%d"),
            "code": st.column_config.TextColumn("股票代码"),
            "name": st.column_config.TextColumn("股票名称"),
            "net_inflow": st.column_config.NumberColumn("净流入金额", format="%.2f"),
            "confidence": st.column_config.TextColumn("确定性"),
            "hold_period": st.column_config.TextColumn("持有周期"),
            "reason": st.column_config.TextColumn("推荐理由")
        },
        hide_index=True,
        width='stretch'
    )
    
    # 详细推荐理由
    st.markdown("### 📝 详细推荐理由")
    
    for stock in recommended[:5]:  # 只显示前5只
        with st.expander(f"**{stock.get('rank', '-')}. {stock.get('name', '-')} ({stock.get('code', '-')})**"):
            col1, col2 = st.columns([2, 1])
            
            with col1:
                st.markdown(f"**推荐理由:** {stock.get('reason', '暂无')}")
                st.markdown(f"**净流入:** {stock.get('net_inflow', 0):,.2f} 元")
            
            with col2:
                st.markdown(f"**确定性:** {stock.get('confidence', '-')}")
                st.markdown(f"**持有周期:** {stock.get('hold_period', '-')}")


def display_agents_reports(result):
    """显示AI分析师报告"""
    
    st.subheader("🤖 AI分析师团队报告")
    
    agents_analysis = result.get('agents_analysis', {})
    
    if not agents_analysis:
        st.warning("暂无分析报告")
        return
    
    # 各分析师报告
    agent_info = {
        'youzi': {'title': '🎯 游资行为分析师', 'icon': '🎯'},
        'stock': {'title': '📈 个股潜力分析师', 'icon': '📈'},
        'theme': {'title': '🔥 题材追踪分析师', 'icon': '🔥'},
        'risk': {'title': '⚠️ 风险控制专家', 'icon': '⚠️'},
        'chief': {'title': '👔 首席策略师综合研判', 'icon': '👔'}
    }
    
    for agent_key, info in agent_info.items():
        agent_data = agents_analysis.get(agent_key, {})
        if agent_data:
            with st.expander(f"{info['icon']} {info['title']}", expanded=(agent_key == 'chief')):
                analysis = agent_data.get('analysis', '暂无分析')
                st.markdown(analysis)
                
                st.markdown(f"*{agent_data.get('agent_role', '')}*")
                st.caption(f"分析时间: {agent_data.get('timestamp', 'N/A')}")


def display_data_details(result):
    """显示数据详情"""
    
    st.subheader("📊 龙虎榜数据详情")
    
    data_info = result.get('data_info', {})
    summary = data_info.get('summary', {})
    
    # TOP游资
    if summary.get('top_youzi'):
        st.markdown("### 🏆 活跃游资 TOP10")
        
        youzi_data = [
            {'排名': idx, '游资名称': name, '净流入金额': amount}
            for idx, (name, amount) in enumerate(list(summary['top_youzi'].items())[:10], 1)
        ]
        df_youzi = pd.DataFrame(youzi_data)
        
        st.dataframe(
            df_youzi,
            column_config={
                "排名": st.column_config.NumberColumn("排名", format="%d"),
                "游资名称": st.column_config.TextColumn("游资名称"),
                "净流入金额": st.column_config.NumberColumn("净流入金额(元)", format="%.2f")
            },
            hide_index=True,
            width='stretch'
        )
    
    # TOP股票
    if summary.get('top_stocks'):
        st.markdown("### 📈 资金净流入 TOP20 股票")
        
        df_stocks = pd.DataFrame(summary['top_stocks'][:20])
        
        st.dataframe(
            df_stocks,
            column_config={
                "code": st.column_config.TextColumn("股票代码"),
                "name": st.column_config.TextColumn("股票名称"),
                "net_inflow": st.column_config.NumberColumn("净流入金额(元)", format="%.2f")
            },
            hide_index=True,
            width='stretch'
        )
    
    # 热门概念
    if summary.get('hot_concepts'):
        st.markdown("### 🔥 热门概念 TOP20")
        
        concepts_data = [
            {'排名': idx, '概念名称': concept, '出现次数': count}
            for idx, (concept, count) in enumerate(list(summary['hot_concepts'].items())[:20], 1)
        ]
        df_concepts = pd.DataFrame(concepts_data)
        
        st.dataframe(
            df_concepts,
            column_config={
                "排名": st.column_config.NumberColumn("排名", format="%d"),
                "概念名称": st.column_config.TextColumn("概念名称"),
                "出现次数": st.column_config.NumberColumn("出现次数", format="%d")
            },
            hide_index=True,
            width='stretch'
        )


def display_visualizations(result):
    """显示可视化图表"""
    
    st.subheader("📈 数据可视化")
    
    data_info = result.get('data_info', {})
    summary = data_info.get('summary', {})
    
    # 资金流向图表
    if summary.get('top_stocks'):
        st.markdown("### 💰 TOP20 股票资金净流入")
        
        stocks = summary['top_stocks'][:20]
        df_chart = pd.DataFrame(stocks)
        
        fig = px.bar(
            df_chart,
            x='name',
            y='net_inflow',
            title='TOP20 股票资金净流入金额',
            labels={'name': '股票名称', 'net_inflow': '净流入金额(元)'}
        )
        fig.update_layout(xaxis_tickangle=-45)
        st.plotly_chart(fig, config={'displayModeBar': False}, use_container_width=True)
    
    # 热门概念图表
    if summary.get('hot_concepts'):
        st.markdown("### 🔥 热门概念分布")
        
        concepts = list(summary['hot_concepts'].items())[:15]
        df_concepts = pd.DataFrame(concepts, columns=['概念', '次数'])
        
        fig = px.pie(
            df_concepts,
            values='次数',
            names='概念',
            title='热门概念出现次数分布'
        )
        st.plotly_chart(fig, config={'displayModeBar': False}, use_container_width=True)


def display_pdf_export_section(result):
    """显示PDF导出功能"""
    
    st.markdown("### 📄 导出PDF报告")
    
    col1, col2 = st.columns([3, 1])
    
    with col1:
        st.info("💡 点击按钮生成并下载专业的PDF分析报告")
    
    with col2:
        if st.button("📥 生成PDF", type="primary", width='stretch'):
            with st.spinner("正在生成PDF报告..."):
                try:
                    generator = LonghubangPDFGenerator()
                    pdf_path = generator.generate_pdf(result)
                    
                    # 读取PDF文件
                    with open(pdf_path, "rb") as f:
                        pdf_bytes = f.read()
                    
                    # 提供下载
                    st.download_button(
                        label="📥 下载PDF报告",
                        data=pdf_bytes,
                        file_name=f"智瞰龙虎报告_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf",
                        mime="application/pdf",
                        width='stretch'
                    )
                    
                    st.success("✅ PDF报告生成成功！")
                
                except Exception as e:
                    st.error(f"❌ PDF生成失败: {str(e)}")


def display_history_tab():
    """显示历史报告标签页（增强版）"""
    
    st.subheader("📚 历史分析报告")
    
    try:
        engine = LonghubangEngine()
        reports_df = engine.get_historical_reports(limit=50)
        
        if reports_df.empty:
            st.info("暂无历史报告")
            return
        
        st.info(f"💾 共有 {len(reports_df)} 条历史报告")
        
        # 显示报告列表
        st.markdown("### 📋 报告列表")
        
        # 为每条报告创建展开面板
        for idx, row in reports_df.iterrows():
            report_id = row['id']
            analysis_date = row['analysis_date']
            data_date_range = row['data_date_range']
            summary = row['summary']
            
            # 创建展开面板
            with st.expander(
                f"📄 报告 #{report_id} | {analysis_date} | 数据范围: {data_date_range}",
                expanded=False
            ):
                # 获取完整报告详情
                report_detail = engine.get_report_detail(report_id)
                
                if not report_detail:
                    st.warning("无法加载报告详情")
                    continue
                
                # 显示摘要
                st.markdown("#### 📝 报告摘要")
                st.info(summary)
                
                st.markdown("---")
                
                # 显示推荐股票
                recommended_stocks = report_detail.get('recommended_stocks', [])
                if recommended_stocks:
                    st.markdown(f"#### 🎯 推荐股票 ({len(recommended_stocks)}只)")
                    
                    # 创建DataFrame显示
                    df_stocks = pd.DataFrame(recommended_stocks)
                    st.dataframe(
                        df_stocks,
                        column_config={
                            "rank": st.column_config.NumberColumn("排名", format="%d"),
                            "code": st.column_config.TextColumn("代码"),
                            "name": st.column_config.TextColumn("名称"),
                            "net_inflow": st.column_config.NumberColumn("净流入", format="%.2f"),
                            "reason": st.column_config.TextColumn("推荐理由"),
                            "confidence": st.column_config.TextColumn("确定性"),
                            "hold_period": st.column_config.TextColumn("持有周期")
                        },
                        hide_index=True,
                        width='stretch'
                    )
                
                st.markdown("---")
                
                # 尝试解析完整分析内容
                analysis_content_parsed = report_detail.get('analysis_content_parsed')
                
                if analysis_content_parsed and isinstance(analysis_content_parsed, dict):
                    # 显示AI分析师团队报告
                    agents_analysis = analysis_content_parsed.get('agents_analysis', {})
                    
                    if agents_analysis:
                        st.markdown("#### 🤖 AI分析师团队报告")
                        
                        agent_info = {
                            'youzi': {'title': '🎯 游资行为分析师', 'icon': '🎯'},
                            'stock': {'title': '📈 个股潜力分析师', 'icon': '📈'},
                            'theme': {'title': '🔥 题材追踪分析师', 'icon': '🔥'},
                            'risk': {'title': '⚠️ 风险控制专家', 'icon': '⚠️'},
                            'chief': {'title': '👔 首席策略师', 'icon': '👔'}
                        }
                        
                        for agent_key, info in agent_info.items():
                            agent_data = agents_analysis.get(agent_key, {})
                            if agent_data:
                                with st.expander(f"{info['icon']} {info['title']}", expanded=False):
                                    analysis = agent_data.get('analysis', '暂无分析')
                                    st.markdown(analysis)
                                    st.caption(f"分析时间: {agent_data.get('timestamp', 'N/A')}")
                    
                    # 显示AI评分排名
                    scoring_ranking = analysis_content_parsed.get('scoring_ranking', [])
                    if scoring_ranking:
                        st.markdown("---")
                        st.markdown("#### 🏆 AI智能评分排名 (TOP10)")
                        
                        df_scoring = pd.DataFrame(scoring_ranking[:10])
                        # 类型统一，避免Arrow序列化错误
                        numeric_cols = ['排名','综合评分','资金含金量','净买入额','卖出压力','机构共振','加分项','顶级游资','买方数','净流入']
                        for col in numeric_cols:
                            if col in df_scoring.columns:
                                df_scoring[col] = pd.to_numeric(df_scoring[col], errors='coerce')
                        text_cols = ['股票名称','股票代码','机构参与']
                        for col in text_cols:
                            if col in df_scoring.columns:
                                df_scoring[col] = df_scoring[col].astype(str)
                        if '排名' in df_scoring.columns:
                            df_scoring['排名'] = pd.to_numeric(df_scoring['排名'], errors='coerce').fillna(0).astype(int)
                        
                        # 显示完整的评分表格
                        st.dataframe(
                            df_scoring,
                            column_config={
                                "排名": st.column_config.NumberColumn("排名", format="%d"),
                                "股票名称": st.column_config.TextColumn("股票名称", width="medium"),
                                "股票代码": st.column_config.TextColumn("代码", width="small"),
                                "综合评分": st.column_config.NumberColumn(
                                    "综合评分",
                                    format="%.1f",
                                    help="总分100分"
                                ),
                                "资金含金量": st.column_config.ProgressColumn(
                                    "资金含金量",
                                    format="%d分",
                                    min_value=0,
                                    max_value=30
                                ),
                                "净买入额": st.column_config.ProgressColumn(
                                    "净买入额",
                                    format="%d分",
                                    min_value=0,
                                    max_value=25
                                ),
                                "卖出压力": st.column_config.ProgressColumn(
                                    "卖出压力",
                                    format="%d分",
                                    min_value=0,
                                    max_value=20
                                ),
                                "机构共振": st.column_config.ProgressColumn(
                                    "机构共振",
                                    format="%d分",
                                    min_value=0,
                                    max_value=15
                                ),
                                "加分项": st.column_config.ProgressColumn(
                                    "加分项",
                                    format="%d分",
                                    min_value=0,
                                    max_value=10
                                ),
                                "顶级游资": st.column_config.NumberColumn("顶级游资", format="%d家"),
                                "买方数": st.column_config.NumberColumn("买方数", format="%d家"),
                                "机构参与": st.column_config.TextColumn("机构参与"),
                                "净流入": st.column_config.NumberColumn("净流入(元)", format="%.2f")
                            },
                            hide_index=True,
                            width='stretch'
                        )
                        
                        # 显示评分说明
                        with st.expander("📖 评分维度说明", expanded=False):
                            st.markdown("""
                            **AI智能评分体系 (总分100分)**
                            
                            - **资金含金量** (0-30分)：顶级游资+10分，知名游资+5分，普通游资+1.5分
                            - **净买入额** (0-25分)：根据净流入金额大小评分
                            - **卖出压力** (0-20分)：卖出比例越低得分越高
                            - **机构共振** (0-15分)：机构+游资共振15分最高
                            - **加分项** (0-10分)：主力集中度、热门概念、连续上榜等
                            
                            💡 评分越高，表示该股票受到资金青睐程度越高！
                            """)
                    
                    # 显示数据概况
                    data_info = analysis_content_parsed.get('data_info', {})
                    if data_info:
                        st.markdown("---")
                        st.markdown("#### 📊 数据概况")
                        
                        col1, col2, col3 = st.columns(3)
                        with col1:
                            st.metric("龙虎榜记录", f"{data_info.get('total_records', 0)} 条")
                        with col2:
                            st.metric("涉及股票", f"{data_info.get('total_stocks', 0)} 只")
                        with col3:
                            st.metric("涉及游资", f"{data_info.get('total_youzi', 0)} 个")
                
                else:
                    # 如果无法解析，显示原始内容
                    st.markdown("#### 📄 原始分析内容")
                    analysis_content = report_detail.get('analysis_content', '')
                    if analysis_content:
                        st.text_area("原始分析内容", value=analysis_content[:2000], height=200, disabled=True)
                        if len(analysis_content) > 2000:
                            st.caption("(内容过长，仅显示前2000字符)")
                
                # 操作按钮
                st.markdown("---")
                col_export1, col_export2, col_export3 = st.columns(3)
                
                with col_export1:
                    if st.button(f"📥 导出为PDF", key=f"export_pdf_{report_id}"):
                        st.info("PDF导出功能开发中...")
                
                with col_export2:
                    # 使用session_state来管理按钮状态，避免需要点击两次的问题
                    load_key = f"load_report_{report_id}"
                    if st.button(f"📋 加载到分析页", key=load_key):
                        # 将历史报告加载到当前分析结果中
                        if analysis_content_parsed:
                            # 重建完整的result结构
                            scoring_data = analysis_content_parsed.get('scoring_ranking', [])
                            if scoring_data:
                                df_scoring = pd.DataFrame(scoring_data)
                                # 类型统一，避免Arrow序列化错误
                                numeric_cols = ['排名','综合评分','资金含金量','净买入额','卖出压力','机构共振','加分项','顶级游资','买方数','净流入']
                                for col in numeric_cols:
                                    if col in df_scoring.columns:
                                        df_scoring[col] = pd.to_numeric(df_scoring[col], errors='coerce')
                                text_cols = ['股票名称','股票代码','机构参与']
                                for col in text_cols:
                                    if col in df_scoring.columns:
                                        df_scoring[col] = df_scoring[col].astype(str)
                                if '排名' in df_scoring.columns:
                                    df_scoring['排名'] = pd.to_numeric(df_scoring['排名'], errors='coerce').fillna(0).astype(int)
                            else:
                                df_scoring = None
                                
                            loaded_result = {
                                "success": True,
                                "timestamp": report_detail.get('analysis_date', ''),
                                "data_info": analysis_content_parsed.get('data_info', {}),
                                "agents_analysis": analysis_content_parsed.get('agents_analysis', {}),
                                "scoring_ranking": df_scoring,
                                "final_report": analysis_content_parsed.get('final_report', {}),
                                "recommended_stocks": report_detail.get('recommended_stocks', [])
                            }
                            st.session_state.longhubang_result = loaded_result
                            # 使用rerun来立即刷新页面状态
                            st.success('✅ 报告已加载到分析页面，请切换到"龙虎榜分析"标签查看')
                            st.rerun()
                
                with col_export3:
                    # 删除按钮
                    delete_key = f"delete_report_{report_id}"
                    if st.button(f"🗑️ 删除报告", key=delete_key, type="secondary"):
                        # 使用session_state来管理删除确认状态
                        st.session_state[f"confirm_delete_{report_id}"] = True
                        st.rerun()
                
                # 删除确认对话框
                if st.session_state.get(f"confirm_delete_{report_id}", False):
                    st.warning(f"⚠️ 确认删除报告 #{report_id}？此操作不可撤销！")
                    col_confirm1, col_confirm2 = st.columns(2)
                    
                    with col_confirm1:
                        if st.button(f"✅ 确认删除", key=f"confirm_delete_yes_{report_id}", type="primary"):
                            try:
                                # 调用数据库删除方法 - 修复属性名
                                engine.database.delete_analysis_report(report_id)
                                st.success(f"✅ 报告 #{report_id} 已成功删除")
                                # 清除确认状态并刷新页面
                                if f"confirm_delete_{report_id}" in st.session_state:
                                    del st.session_state[f"confirm_delete_{report_id}"]
                                st.rerun()
                            except Exception as e:
                                st.error(f"❌ 删除失败: {str(e)}")
                    
                    with col_confirm2:
                        if st.button(f"❌ 取消", key=f"confirm_delete_no_{report_id}"):
                            # 清除确认状态
                            if f"confirm_delete_{report_id}" in st.session_state:
                                del st.session_state[f"confirm_delete_{report_id}"]
                            st.rerun()
        
    except Exception as e:
        st.error(f"❌ 加载历史报告失败: {str(e)}")
        import traceback
        st.code(traceback.format_exc())


def display_statistics_tab():
    """显示数据统计标签页"""
    
    st.subheader("📈 数据统计")
    
    try:
        engine = LonghubangEngine()
        stats = engine.get_statistics()
        
        # 基本统计
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.metric("总记录数", f"{stats.get('total_records', 0):,}")
        
        with col2:
            st.metric("股票总数", f"{stats.get('total_stocks', 0):,}")
        
        with col3:
            st.metric("游资总数", f"{stats.get('total_youzi', 0):,}")
        
        with col4:
            st.metric("分析报告", f"{stats.get('total_reports', 0):,}")
        
        # 日期范围
        date_range = stats.get('date_range', {})
        if date_range:
            st.info(f"📅 数据日期范围: {date_range.get('start', 'N/A')} 至 {date_range.get('end', 'N/A')}")
        
        st.markdown("---")
        
        # 活跃游资排名
        st.markdown("### 🏆 历史活跃游资排名 (近30天)")
        
        end_date = datetime.now().strftime('%Y-%m-%d')
        start_date = (datetime.now() - timedelta(days=30)).strftime('%Y-%m-%d')
        
        top_youzi_df = engine.get_top_youzi(start_date, end_date, limit=20)
        
        if not top_youzi_df.empty:
            st.dataframe(
                top_youzi_df,
                column_config={
                    "youzi_name": st.column_config.TextColumn("游资名称"),
                    "trade_count": st.column_config.NumberColumn("交易次数", format="%d"),
                    "total_net_inflow": st.column_config.NumberColumn("总净流入(元)", format="%.2f")
                },
                hide_index=True,
                width='stretch'
            )
        
        st.markdown("---")
        
        # 热门股票排名
        st.markdown("### 📈 历史热门股票排名 (近30天)")
        
        top_stocks_df = engine.get_top_stocks(start_date, end_date, limit=20)
        
        if not top_stocks_df.empty:
            st.dataframe(
                top_stocks_df,
                column_config={
                    "stock_code": st.column_config.TextColumn("股票代码"),
                    "stock_name": st.column_config.TextColumn("股票名称"),
                    "youzi_count": st.column_config.NumberColumn("游资数量", format="%d"),
                    "total_net_inflow": st.column_config.NumberColumn("总净流入(元)", format="%.2f")
                },
                hide_index=True,
                width='stretch'
            )
        
    except Exception as e:
        st.error(f"❌ 加载统计数据失败: {str(e)}")


def run_longhubang_batch_analysis():
    """执行龙虎榜TOP股票批量分析（遵循统一调用规范）"""
    
    st.markdown("## 🚀 龙虎榜TOP股票批量分析")
    st.markdown("---")
    
    # 检查是否已有分析结果
    if st.session_state.get('longhubang_batch_results'):
        display_longhubang_batch_results(st.session_state.longhubang_batch_results)
        
        # 返回按钮
        col_back, col_clear = st.columns(2)
        with col_back:
            if st.button("🔙 返回龙虎榜分析", width='stretch'):
                # 清除所有批量分析相关状态
                if 'longhubang_batch_trigger' in st.session_state:
                    del st.session_state.longhubang_batch_trigger
                if 'longhubang_batch_codes' in st.session_state:
                    del st.session_state.longhubang_batch_codes
                if 'longhubang_batch_results' in st.session_state:
                    del st.session_state.longhubang_batch_results
                st.rerun()
        
        with col_clear:
            if st.button("🔄 重新分析", width='stretch'):
                # 清除结果，保留触发标志和代码
                if 'longhubang_batch_results' in st.session_state:
                    del st.session_state.longhubang_batch_results
                st.rerun()
        
        return
    
    # 获取股票代码列表
    stock_codes = st.session_state.get('longhubang_batch_codes', [])
    
    if not stock_codes:
        st.error("未找到股票代码列表")
        # 清除触发标志
        if 'longhubang_batch_trigger' in st.session_state:
            del st.session_state.longhubang_batch_trigger
        return
    
    st.info(f"即将分析 {len(stock_codes)} 只股票：{', '.join(stock_codes)}")
    
    # 返回按钮
    if st.button("🔙 取消返回", type="secondary"):
        # 清除所有批量分析相关状态
        if 'longhubang_batch_trigger' in st.session_state:
            del st.session_state.longhubang_batch_trigger
        if 'longhubang_batch_codes' in st.session_state:
            del st.session_state.longhubang_batch_codes
        st.rerun()
    
    st.markdown("---")
    
    # 分析选项
    col1, col2 = st.columns(2)
    
    with col1:
        analysis_mode = st.selectbox(
            "分析模式",
            options=["sequential", "parallel"],
            format_func=lambda x: "顺序分析（稳定）" if x == "sequential" else "并行分析（快速）",
            help="顺序分析较慢但稳定，并行分析更快但消耗更多资源"
        )
    
    with col2:
        if analysis_mode == "parallel":
            max_workers = st.number_input(
                "并行线程数",
                min_value=2,
                max_value=5,
                value=3,
                help="同时分析的股票数量"
            )
        else:
            max_workers = 1
    
    st.markdown("---")
    
    # 开始分析按钮
    col_confirm, col_cancel = st.columns(2)
    
    start_analysis = False
    with col_confirm:
        if st.button("🚀 确认开始分析", type="primary", width='stretch'):
            start_analysis = True
    
    with col_cancel:
        if st.button("❌ 取消", type="secondary", width='stretch'):
            # 清除所有批量分析相关状态
            if 'longhubang_batch_trigger' in st.session_state:
                del st.session_state.longhubang_batch_trigger
            if 'longhubang_batch_codes' in st.session_state:
                del st.session_state.longhubang_batch_codes
            st.rerun()
    
    if start_analysis:
        # 导入统一分析函数（遵循统一规范）
        from app import analyze_single_stock_for_batch
        import concurrent.futures
        import time
        
        st.markdown("---")
        st.info("⏳ 正在执行批量分析，请稍候...")
        
        # 进度显示
        progress_bar = st.progress(0)
        status_text = st.empty()
        
        results = []
        start_time = time.time()
        
        if analysis_mode == "sequential":
            # 顺序分析
            for i, code in enumerate(stock_codes):
                status_text.text(f"正在分析 {code} ({i+1}/{len(stock_codes)})")
                progress_bar.progress((i + 1) / len(stock_codes))
                
                try:
                    # 调用统一分析函数
                    result = analyze_single_stock_for_batch(
                        symbol=code,
                        period="1y",
                        enabled_analysts_config={
                            'technical': True,
                            'fundamental': True,
                            'fund_flow': True,
                            'risk': True,
                            'sentiment': False,
                            'news': False
                        },
                        selected_model='deepseek-chat'
                    )
                    
                    results.append({
                        "code": code,
                        "result": result
                    })
                    
                except Exception as e:
                    results.append({
                        "code": code,
                        "result": {"success": False, "error": str(e)}
                    })
        
        else:
            # 并行分析
            status_text.text(f"并行分析 {len(stock_codes)} 只股票...")
            
            def analyze_one(code):
                try:
                    result = analyze_single_stock_for_batch(
                        symbol=code,
                        period="1y",
                        enabled_analysts_config={
                            'technical': True,
                            'fundamental': True,
                            'fund_flow': True,
                            'risk': True,
                            'sentiment': False,
                            'news': False
                        },
                        selected_model='deepseek-chat'
                    )
                    return {"code": code, "result": result}
                except Exception as e:
                    return {"code": code, "result": {"success": False, "error": str(e)}}
            
            with concurrent.futures.ThreadPoolExecutor(max_workers=max_workers) as executor:
                futures = {executor.submit(analyze_one, code): code for code in stock_codes}
                
                completed = 0
                for future in concurrent.futures.as_completed(futures):
                    completed += 1
                    progress_bar.progress(completed / len(stock_codes))
                    status_text.text(f"已完成 {completed}/{len(stock_codes)}")
                    results.append(future.result())
        
        # 清除进度
        progress_bar.empty()
        status_text.empty()
        
        # 计算统计
        elapsed_time = time.time() - start_time
        success_count = sum(1 for r in results if r.get("result", {}).get("success"))
        failed_count = len(results) - success_count
        
        st.success(f"✅ 批量分析完成！成功 {success_count} 只，失败 {failed_count} 只，耗时 {elapsed_time:.1f}秒")
        
        # 保存结果到session_state
        st.session_state.longhubang_batch_results = {
            "results": results,
            "total": len(results),
            "success": success_count,
            "failed": failed_count,
            "elapsed_time": elapsed_time
        }
        
        time.sleep(0.5)
        st.rerun()


def display_longhubang_batch_results(batch_results: dict):
    """显示龙虎榜批量分析结果"""
    
    st.markdown("### 📊 批量分析结果")
    
    results = batch_results.get("results", [])
    total = batch_results.get("total", 0)
    success = batch_results.get("success", 0)
    failed = batch_results.get("failed", 0)
    elapsed_time = batch_results.get("elapsed_time", 0)
    
    # 统计信息
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("总计", total)
    with col2:
        st.metric("成功", success)
    with col3:
        st.metric("失败", failed)
    with col4:
        st.metric("耗时", f"{elapsed_time:.1f}秒")
    
    st.markdown("---")
    
    # 失败的股票
    failed_results = [r for r in results if not r.get("result", {}).get("success")]
    if failed_results:
        with st.expander(f"❌ 失败股票 ({len(failed_results)}只)", expanded=False):
            for item in failed_results:
                code = item.get("code", "")
                error = item.get("result", {}).get("error", "未知错误")
                st.error(f"**{code}**: {error}")
    
    # 成功的股票
    success_results = [r for r in results if r.get("result", {}).get("success")]
    
    if not success_results:
        st.warning("⚠️ 没有成功分析的股票")
        return
    
    st.markdown("### 🎯 分析结果详情")
    
    # 显示每只股票的分析结果（使用统一字段名）
    for item in success_results:
        code = item.get("code", "")
        result = item.get("result", {})
        final_decision = result.get("final_decision", {})
        stock_info = result.get("stock_info", {})
        
        # 使用统一字段名
        rating = final_decision.get("rating", "未知")
        confidence = final_decision.get("confidence_level", "N/A")
        entry_range = final_decision.get("entry_range", "N/A")
        take_profit = final_decision.get("take_profit", "N/A")
        stop_loss = final_decision.get("stop_loss", "N/A")
        target_price = final_decision.get("target_price", "N/A")
        advice = final_decision.get("advice", "")
        
        # 评级颜色
        if "强烈买入" in rating or "买入" in rating:
            rating_color = "🟢"
        elif "卖出" in rating:
            rating_color = "🔴"
        else:
            rating_color = "🟡"
        
        with st.expander(f"{rating_color} {code} {stock_info.get('name', '')} - {rating} (信心度: {confidence})", expanded=False):
            col1, col2, col3 = st.columns(3)
            
            with col1:
                st.markdown("**基本信息**")
                st.write(f"当前价: {stock_info.get('current_price', 'N/A')}")
                st.write(f"目标价: {target_price}")
            
            with col2:
                st.markdown("**进出场位置**")
                st.write(f"进场区间: {entry_range}")
                st.write(f"止盈位: {take_profit}")
            
            with col3:
                st.markdown("**风控**")
                st.write(f"止损位: {stop_loss}")
                st.write(f"评级: {rating}")
            
            if advice:
                st.markdown("**投资建议**")
                st.info(advice)
            
            # 添加到监测按钮
            if st.button(f"➕ 加入监测", key=f"add_monitor_{code}"):
                add_to_monitor_from_longhubang(code, stock_info.get('name', ''), final_decision)


def add_to_monitor_from_longhubang(code: str, name: str, final_decision: dict):
    """从龙虎榜分析结果添加到监测列表"""
    try:
        from monitor_db import monitor_db
        import re
        
        # 提取数据（使用统一字段名和解析逻辑）
        rating = final_decision.get("rating", "持有")
        entry_range = final_decision.get("entry_range", "")
        take_profit_str = final_decision.get("take_profit", "")
        stop_loss_str = final_decision.get("stop_loss", "")
        
        # 解析进场区间
        entry_min, entry_max = None, None
        if entry_range and isinstance(entry_range, str) and "-" in entry_range:
            try:
                parts = entry_range.split("-")
                entry_min = float(parts[0].strip())
                entry_max = float(parts[1].strip())
            except:
                pass
        
        # 解析止盈止损
        take_profit, stop_loss = None, None
        if take_profit_str:
            try:
                numbers = re.findall(r'\d+\.?\d*', str(take_profit_str))
                if numbers:
                    take_profit = float(numbers[0])
            except:
                pass
        
        if stop_loss_str:
            try:
                numbers = re.findall(r'\d+\.?\d*', str(stop_loss_str))
                if numbers:
                    stop_loss = float(numbers[0])
            except:
                pass
        
        # 验证必需参数
        if not all([entry_min, entry_max, take_profit, stop_loss]):
            st.error("❌ 分析结果缺少完整的进场区间和止盈止损信息")
            return
        
        # 添加到监测
        monitor_db.add_monitored_stock(
            symbol=code,
            name=name,
            rating=rating,
            entry_range={"min": entry_min, "max": entry_max},
            take_profit=take_profit,
            stop_loss=stop_loss,
            check_interval=60,
            notification_enabled=True
        )
        
        st.success(f"✅ {code} 已成功加入监测列表！")
        
    except Exception as e:
        st.error(f"❌ 添加监测失败: {str(e)}")


# 测试函数
if __name__ == "__main__":
    st.set_page_config(
        page_title="智瞰龙虎",
        page_icon="🎯",
        layout="wide"
    )
    
    display_longhubang()

