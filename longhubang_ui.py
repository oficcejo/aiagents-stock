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
        analyze_button = st.button("🚀 开始分析", type="primary", use_container_width=True)
    
    with col2:
        if st.button("🔄 清除结果", use_container_width=True):
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
    tab1, tab2, tab3, tab4 = st.tabs([
        "🎯 推荐股票",
        "🤖 AI分析师报告",
        "📊 数据详情",
        "📈 可视化图表"
    ])
    
    with tab1:
        display_recommended_stocks(result)
    
    with tab2:
        display_agents_reports(result)
    
    with tab3:
        display_data_details(result)
    
    with tab4:
        display_visualizations(result)


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
        use_container_width=True
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
            use_container_width=True
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
            use_container_width=True
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
            use_container_width=True
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
        st.plotly_chart(fig, use_container_width=True)
    
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
        st.plotly_chart(fig, use_container_width=True)


def display_pdf_export_section(result):
    """显示PDF导出功能"""
    
    st.markdown("### 📄 导出PDF报告")
    
    col1, col2 = st.columns([3, 1])
    
    with col1:
        st.info("💡 点击按钮生成并下载专业的PDF分析报告")
    
    with col2:
        if st.button("📥 生成PDF", type="primary", use_container_width=True):
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
                        use_container_width=True
                    )
                    
                    st.success("✅ PDF报告生成成功！")
                
                except Exception as e:
                    st.error(f"❌ PDF生成失败: {str(e)}")


def display_history_tab():
    """显示历史报告标签页"""
    
    st.subheader("📚 历史分析报告")
    
    try:
        engine = LonghubangEngine()
        reports_df = engine.get_historical_reports(limit=20)
        
        if reports_df.empty:
            st.info("暂无历史报告")
            return
        
        st.dataframe(
            reports_df,
            column_config={
                "id": st.column_config.NumberColumn("ID", format="%d"),
                "analysis_date": st.column_config.TextColumn("分析时间"),
                "data_date_range": st.column_config.TextColumn("数据日期范围"),
                "summary": st.column_config.TextColumn("摘要")
            },
            hide_index=True,
            use_container_width=True
        )
        
    except Exception as e:
        st.error(f"❌ 加载历史报告失败: {str(e)}")


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
                use_container_width=True
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
                use_container_width=True
            )
        
    except Exception as e:
        st.error(f"❌ 加载统计数据失败: {str(e)}")


# 测试函数
if __name__ == "__main__":
    st.set_page_config(
        page_title="智瞰龙虎",
        page_icon="🎯",
        layout="wide"
    )
    
    display_longhubang()

