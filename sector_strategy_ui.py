"""
智策UI界面模块
展示板块分析结果和预测
"""

import streamlit as st
import plotly.graph_objects as go
import plotly.express as px
import pandas as pd
from datetime import datetime, time as dt_time
import time
import base64

from sector_strategy_data import SectorStrategyDataFetcher
from sector_strategy_engine import SectorStrategyEngine
from sector_strategy_pdf import SectorStrategyPDFGenerator
from sector_strategy_scheduler import sector_strategy_scheduler


def display_sector_strategy():
    """显示智策板块分析主界面"""
    
    st.markdown("""
    <div class="top-nav">
        <h1 class="nav-title">🎯 智策 - AI驱动的板块策略分析</h1>
        <p class="nav-subtitle">Multi-Agent Sector Strategy Analysis | 板块多空·轮动·热度预测</p>
    </div>
    """, unsafe_allow_html=True)
    
    st.markdown("---")
    
    # 定时任务设置区域
    display_scheduler_settings()
    
    # 功能说明
    with st.expander("💡 智策系统介绍", expanded=False):
        st.markdown("""
        ### 🌟 系统特色
        
        **智策**是基于多AI智能体的板块策略分析系统，通过四位专业分析师的协同工作，为您提供全方位的板块投资决策支持。
        
        ### 🤖 AI智能体团队
        
        1. **🌐 宏观策略师**
           - 分析宏观经济形势和政策导向
           - 解读财经新闻对市场的影响
           - 识别行业发展趋势
        
        2. **📊 板块诊断师**
           - 深入分析板块走势和估值
           - 评估板块基本面和成长性
           - 预判板块轮动方向
        
        3. **💰 资金流向分析师**
           - 跟踪主力资金的板块流向
           - 分析北向资金的偏好
           - 识别资金轮动信号
        
        4. **📈 市场情绪解码员**
           - 量化市场情绪指标
           - 识别恐慌贪婪信号
           - 评估板块热度
        
        ### 📊 核心预测
        
        - **板块多空**: 看多/看空板块推荐
        - **板块轮动**: 强势/潜力/衰退板块识别
        - **板块热度**: 热度排行和升降温趋势
        
        ### 📈 数据来源
        
        所有数据来自**AKShare**开源库，包括：
        - 行业板块和概念板块行情
        - 板块资金流向数据
        - 北向资金数据
        - 市场统计数据
        - 财经新闻数据
        """)
    
    st.markdown("---")
    
    # 模型选择
    col1, col2, col3 = st.columns([2, 2, 2])
    
    with col1:
        selected_model = st.selectbox(
            "选择AI模型",
            ["deepseek-chat", "deepseek-reasoner"],
            help="Reasoner模型提供更强的推理能力"
        )
    
    with col2:
        st.write("")
        st.write("")
        analyze_button = st.button("🚀 开始智策分析", type="primary", use_container_width=True)
    
    with col3:
        st.write("")
        st.write("")
        if st.button("🔄 清除结果", use_container_width=True):
            if 'sector_strategy_result' in st.session_state:
                del st.session_state.sector_strategy_result
            st.success("已清除分析结果")
            st.rerun()
    
    st.markdown("---")
    
    # 开始分析
    if analyze_button:
        # 清除之前的结果
        if 'sector_strategy_result' in st.session_state:
            del st.session_state.sector_strategy_result
        
        run_sector_strategy_analysis(selected_model)
    
    # 显示分析结果
    if 'sector_strategy_result' in st.session_state:
        result = st.session_state.sector_strategy_result
        
        if result.get("success"):
            display_analysis_results(result)
        else:
            st.error(f"❌ 分析失败: {result.get('error', '未知错误')}")


def run_sector_strategy_analysis(model="deepseek-chat"):
    """运行智策分析"""
    
    # 进度显示
    progress_bar = st.progress(0)
    status_text = st.empty()
    
    try:
        # 1. 获取数据
        status_text.text("📊 正在获取市场数据...")
        progress_bar.progress(10)
        
        fetcher = SectorStrategyDataFetcher()
        data = fetcher.get_all_sector_data()
        
        if not data.get("success"):
            st.error("❌ 数据获取失败")
            return
        
        progress_bar.progress(30)
        status_text.text("✓ 数据获取完成")
        
        # 显示数据摘要
        display_data_summary(data)
        
        # 2. 运行AI分析
        status_text.text("🤖 AI智能体团队正在分析，预计需要10分钟...")
        progress_bar.progress(40)
        
        engine = SectorStrategyEngine(model=model)
        result = engine.run_comprehensive_analysis(data)
        
        progress_bar.progress(90)
        
        if result.get("success"):
            # 保存结果
            st.session_state.sector_strategy_result = result
            
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


def display_data_summary(data):
    """显示数据摘要"""
    st.subheader("📊 市场数据概览")
    
    col1, col2, col3, col4 = st.columns(4)
    
    market = data.get("market_overview", {})
    
    with col1:
        if market.get("sh_index"):
            sh = market["sh_index"]
            st.metric(
                "上证指数",
                f"{sh['close']:.2f}",
                f"{sh['change_pct']:+.2f}%"
            )
    
    with col2:
        if market.get("up_count"):
            st.metric(
                "上涨股票",
                market['up_count'],
                f"{market['up_ratio']:.1f}%"
            )
    
    with col3:
        sectors_count = len(data.get("sectors", {}))
        st.metric("行业板块", sectors_count)
    
    with col4:
        concepts_count = len(data.get("concepts", {}))
        st.metric("概念板块", concepts_count)


def display_analysis_results(result):
    """显示分析结果"""
    
    st.success("✅ 智策分析完成！")
    st.info(f"📅 分析时间: {result.get('timestamp', 'N/A')}")
    
    # PDF导出功能
    display_pdf_export_section(result)
    
    st.markdown("---")
    
    # 创建标签页
    tab1, tab2, tab3, tab4 = st.tabs([
        "📋 核心预测", 
        "🤖 智能体分析", 
        "📊 综合研判",
        "📈 数据可视化"
    ])
    
    # Tab 1: 核心预测
    with tab1:
        display_predictions(result.get("final_predictions", {}))
    
    # Tab 2: 智能体分析
    with tab2:
        display_agents_reports(result.get("agents_analysis", {}))
    
    # Tab 3: 综合研判
    with tab3:
        display_comprehensive_report(result.get("comprehensive_report", ""))
    
    # Tab 4: 数据可视化
    with tab4:
        display_visualizations(result.get("final_predictions", {}))


def display_predictions(predictions):
    """显示核心预测"""
    
    st.subheader("🎯 智策核心预测")
    
    if not predictions or predictions.get("prediction_text"):
        # 文本格式
        st.markdown("### 预测报告")
        st.write(predictions.get("prediction_text", "暂无预测"))
        return
    
    # JSON格式预测
    
    # 1. 板块多空
    st.markdown("### 📊 板块多空预测")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("#### 🟢 看多板块")
        bullish = predictions.get("long_short", {}).get("bullish", [])
        if bullish:
            for item in bullish:
                st.markdown(f"""
                <div class="agent-card" style="border-left-color: #4caf50;">
                    <h4>{item.get('sector', 'N/A')} <span style="color: #4caf50;">↑</span></h4>
                    <p><strong>信心度:</strong> {item.get('confidence', 0)}/10</p>
                    <p><strong>理由:</strong> {item.get('reason', '')}</p>
                    <p><strong>风险:</strong> {item.get('risk', '')}</p>
                </div>
                """, unsafe_allow_html=True)
        else:
            st.info("暂无看多板块")
    
    with col2:
        st.markdown("#### 🔴 看空板块")
        bearish = predictions.get("long_short", {}).get("bearish", [])
        if bearish:
            for item in bearish:
                st.markdown(f"""
                <div class="agent-card" style="border-left-color: #f44336;">
                    <h4>{item.get('sector', 'N/A')} <span style="color: #f44336;">↓</span></h4>
                    <p><strong>信心度:</strong> {item.get('confidence', 0)}/10</p>
                    <p><strong>理由:</strong> {item.get('reason', '')}</p>
                    <p><strong>风险:</strong> {item.get('risk', '')}</p>
                </div>
                """, unsafe_allow_html=True)
        else:
            st.info("暂无看空板块")
    
    st.markdown("---")
    
    # 2. 板块轮动
    st.markdown("### 🔄 板块轮动预测")
    
    rotation = predictions.get("rotation", {})
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.markdown("#### 💪 当前强势")
        current_strong = rotation.get("current_strong", [])
        for item in current_strong:
            st.markdown(f"""
            **{item.get('sector', 'N/A')}**
            - 时间窗口: {item.get('time_window', 'N/A')}
            - 逻辑: {item.get('logic', '')[:50]}...
            - 建议: {item.get('advice', '')}
            """)
    
    with col2:
        st.markdown("#### 🌱 潜力接力")
        potential = rotation.get("potential", [])
        for item in potential:
            st.markdown(f"""
            **{item.get('sector', 'N/A')}**
            - 时间窗口: {item.get('time_window', 'N/A')}
            - 逻辑: {item.get('logic', '')[:50]}...
            - 建议: {item.get('advice', '')}
            """)
    
    with col3:
        st.markdown("#### 📉 衰退板块")
        declining = rotation.get("declining", [])
        for item in declining:
            st.markdown(f"""
            **{item.get('sector', 'N/A')}**
            - 时间窗口: {item.get('time_window', 'N/A')}
            - 逻辑: {item.get('logic', '')[:50]}...
            - 建议: {item.get('advice', '')}
            """)
    
    st.markdown("---")
    
    # 3. 板块热度
    st.markdown("### 🔥 板块热度排行")
    
    heat = predictions.get("heat", {})
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.markdown("#### 🔥 最热板块")
        hottest = heat.get("hottest", [])
        for idx, item in enumerate(hottest, 1):
            st.metric(
                f"{idx}. {item.get('sector', 'N/A')}",
                f"{item.get('score', 0)}分",
                f"{item.get('trend', 'N/A')}"
            )
    
    with col2:
        st.markdown("#### 📈 升温板块")
        heating = heat.get("heating", [])
        for idx, item in enumerate(heating, 1):
            st.metric(
                f"{idx}. {item.get('sector', 'N/A')}",
                f"{item.get('score', 0)}分",
                "↗️ 升温"
            )
    
    with col3:
        st.markdown("#### 📉 降温板块")
        cooling = heat.get("cooling", [])
        for idx, item in enumerate(cooling, 1):
            st.metric(
                f"{idx}. {item.get('sector', 'N/A')}",
                f"{item.get('score', 0)}分",
                "↘️ 降温"
            )
    
    st.markdown("---")
    
    # 4. 总结建议
    summary = predictions.get("summary", {})
    if summary:
        st.markdown("### 📝 策略总结")
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown(f"""
            <div class="decision-card">
                <h4>💡 市场观点</h4>
                <p>{summary.get('market_view', 'N/A')}</p>
            </div>
            """, unsafe_allow_html=True)
            
            st.markdown(f"""
            <div class="agent-card" style="border-left-color: #2196f3;">
                <h4>🎯 核心机会</h4>
                <p>{summary.get('key_opportunity', 'N/A')}</p>
            </div>
            """, unsafe_allow_html=True)
        
        with col2:
            st.markdown(f"""
            <div class="warning-card">
                <h4>⚠️ 主要风险</h4>
                <p>{summary.get('major_risk', 'N/A')}</p>
            </div>
            """, unsafe_allow_html=True)
            
            st.markdown(f"""
            <div class="agent-card" style="border-left-color: #ff9800;">
                <h4>📋 整体策略</h4>
                <p>{summary.get('strategy', 'N/A')}</p>
            </div>
            """, unsafe_allow_html=True)


def display_agents_reports(agents_analysis):
    """显示智能体分析报告"""
    
    st.subheader("🤖 AI智能体分析报告")
    
    if not agents_analysis:
        st.info("暂无智能体分析数据")
        return
    
    # 创建子标签页
    agent_names = []
    agent_data = []
    
    for key, value in agents_analysis.items():
        agent_names.append(value.get("agent_name", "未知分析师"))
        agent_data.append(value)
    
    tabs = st.tabs(agent_names)
    
    for idx, tab in enumerate(tabs):
        with tab:
            agent = agent_data[idx]
            
            st.markdown(f"""
            <div class="agent-card">
                <h3>👨‍💼 {agent.get('agent_name', '未知')}</h3>
                <p><strong>职责:</strong> {agent.get('agent_role', '未知')}</p>
                <p><strong>关注领域:</strong> {', '.join(agent.get('focus_areas', []))}</p>
                <p><strong>分析时间:</strong> {agent.get('timestamp', '未知')}</p>
            </div>
            """, unsafe_allow_html=True)
            
            st.markdown("---")
            
            st.markdown("### 📄 分析报告")
            st.write(agent.get("analysis", "暂无分析"))


def display_comprehensive_report(report):
    """显示综合研判报告"""
    
    st.subheader("📊 综合研判报告")
    
    if not report:
        st.info("暂无综合研判数据")
        return
    
    st.markdown("""
    <div class="decision-card">
        <h4>🎯 智策综合研判</h4>
        <p>基于四位专业分析师的深度分析，形成的全面市场和板块研判</p>
    </div>
    """, unsafe_allow_html=True)
    
    st.markdown("---")
    
    st.write(report)


def display_visualizations(predictions):
    """显示数据可视化"""
    
    st.subheader("📈 数据可视化")
    
    if not predictions or predictions.get("prediction_text"):
        st.info("暂无可视化数据")
        return
    
    # 1. 板块多空雷达图
    st.markdown("### 📊 板块多空信心度对比")
    
    bullish = predictions.get("long_short", {}).get("bullish", [])
    bearish = predictions.get("long_short", {}).get("bearish", [])
    
    if bullish or bearish:
        # 准备数据
        sectors = []
        confidence = []
        types = []
        
        for item in bullish[:5]:
            sectors.append(item.get('sector', 'N/A'))
            confidence.append(item.get('confidence', 0))
            types.append('看多')
        
        for item in bearish[:5]:
            sectors.append(item.get('sector', 'N/A'))
            confidence.append(-item.get('confidence', 0))  # 负值表示看空
            types.append('看空')
        
        # 创建条形图
        df = pd.DataFrame({
            '板块': sectors,
            '信心度': confidence,
            '类型': types
        })
        
        fig = px.bar(df, x='板块', y='信心度', color='类型',
                     color_discrete_map={'看多': '#4caf50', '看空': '#f44336'},
                     title='板块多空信心度对比')
        
        fig.update_layout(height=400)
        st.plotly_chart(fig, use_container_width=True, key="sector_confidence")
    
    st.markdown("---")
    
    # 2. 板块热度分布
    st.markdown("### 🔥 板块热度分布")
    
    heat = predictions.get("heat", {})
    hottest = heat.get("hottest", [])
    heating = heat.get("heating", [])
    
    if hottest or heating:
        sectors = []
        scores = []
        trends = []
        
        for item in hottest:
            sectors.append(item.get('sector', 'N/A'))
            scores.append(item.get('score', 0))
            trends.append('最热')
        
        for item in heating:
            sectors.append(item.get('sector', 'N/A'))
            scores.append(item.get('score', 0))
            trends.append('升温')
        
        df = pd.DataFrame({
            '板块': sectors,
            '热度': scores,
            '趋势': trends
        })
        
        fig = px.scatter(df, x='板块', y='热度', size='热度', color='趋势',
                        color_discrete_map={'最热': '#ff5722', '升温': '#ff9800'},
                        title='板块热度分布图')
        
        fig.update_layout(height=400)
        st.plotly_chart(fig, use_container_width=True, key="sector_heat")


def display_pdf_export_section(result):
    """显示PDF导出部分"""
    st.subheader("📄 导出报告")
    
    col1, col2, col3 = st.columns([2, 1, 1])
    
    with col1:
        st.write("将分析报告导出为PDF文件，方便保存和分享")
    
    with col2:
        if st.button("📥 生成PDF报告", type="primary", use_container_width=True):
            with st.spinner("正在生成PDF报告..."):
                try:
                    # 生成PDF
                    generator = SectorStrategyPDFGenerator()
                    pdf_path = generator.generate_pdf(result)
                    
                    # 读取PDF文件
                    with open(pdf_path, "rb") as f:
                        pdf_bytes = f.read()
                    
                    # 保存到session_state
                    st.session_state.sector_pdf_data = pdf_bytes
                    st.session_state.sector_pdf_filename = f"智策报告_{result.get('timestamp', datetime.now().strftime('%Y%m%d_%H%M%S')).replace(':', '').replace(' ', '_')}.pdf"
                    
                    st.success("✅ PDF报告生成成功！")
                    st.rerun()
                    
                except Exception as e:
                    st.error(f"❌ PDF生成失败: {str(e)}")
    
    with col3:
        # 如果已经生成了PDF，显示下载按钮
        if 'sector_pdf_data' in st.session_state:
            st.download_button(
                label="💾 下载PDF",
                data=st.session_state.sector_pdf_data,
                file_name=st.session_state.sector_pdf_filename,
                mime="application/pdf",
                use_container_width=True
            )


def display_scheduler_settings():
    """显示定时任务设置"""
    with st.expander("⏰ 定时分析设置", expanded=False):
        st.markdown("""
        **定时分析功能**
        
        开启后，系统将在每天指定时间自动运行智策分析，并将核心结果通过邮件发送。
        
        **前提条件：**
        - 需要在 `.env` 文件中配置邮件设置
        - 配置项：`EMAIL_ENABLED`, `SMTP_SERVER`, `EMAIL_FROM`, `EMAIL_PASSWORD`, `EMAIL_TO`
        """)
        
        # 获取当前状态
        status = sector_strategy_scheduler.get_status()
        
        col1, col2 = st.columns([1, 1])
        
        with col1:
            # 显示当前状态
            if status['running']:
                st.success(f"✅ 定时任务运行中")
                st.info(f"⏰ 定时时间: {status['schedule_time']}")
                if status['next_run_time']:
                    st.info(f"📅 下次运行: {status['next_run_time']}")
                if status['last_run_time']:
                    st.info(f"📊 上次运行: {status['last_run_time']}")
            else:
                st.warning("⏸️ 定时任务未运行")
        
        with col2:
            # 时间设置
            schedule_time = st.time_input(
                "设置定时时间",
                value=dt_time(9, 0),  # 默认9:00
                help="系统将在每天此时间自动运行分析"
            )
            
            schedule_time_str = schedule_time.strftime("%H:%M")
            
            # 控制按钮
            col_a, col_b, col_c = st.columns(3)
            
            with col_a:
                if not status['running']:
                    if st.button("▶️ 启动", use_container_width=True, type="primary"):
                        if sector_strategy_scheduler.start(schedule_time_str):
                            st.success(f"✅ 定时任务已启动！每天 {schedule_time_str} 运行")
                            time.sleep(1)
                            st.rerun()
                        else:
                            st.error("❌ 启动失败")
                else:
                    if st.button("⏹️ 停止", use_container_width=True):
                        if sector_strategy_scheduler.stop():
                            st.success("✅ 定时任务已停止")
                            time.sleep(1)
                            st.rerun()
                        else:
                            st.error("❌ 停止失败")
            
            with col_b:
                if st.button("🔄 立即运行", use_container_width=True):
                    with st.spinner("正在运行分析..."):
                        sector_strategy_scheduler.manual_run()
                    st.success("✅ 手动分析完成！")
            
            with col_c:
                if st.button("📧 测试邮件", use_container_width=True):
                    test_email_notification()
        
        # 邮件配置检查
        st.markdown("---")
        check_email_config()


def check_email_config():
    """检查邮件配置"""
    st.markdown("**📧 邮件配置检查**")
    
    import os
    from dotenv import load_dotenv
    load_dotenv()
    
    email_enabled = os.getenv('EMAIL_ENABLED', 'false').lower() == 'true'
    smtp_server = os.getenv('SMTP_SERVER', '')
    email_from = os.getenv('EMAIL_FROM', '')
    email_password = os.getenv('EMAIL_PASSWORD', '')
    email_to = os.getenv('EMAIL_TO', '')
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.write("**配置项**")
        st.write(f"✅ 邮件功能: {'已启用' if email_enabled else '❌ 未启用'}")
        st.write(f"{'✅' if smtp_server else '❌'} SMTP服务器: {smtp_server or '未配置'}")
        st.write(f"{'✅' if email_from else '❌'} 发件邮箱: {email_from or '未配置'}")
    
    with col2:
        st.write("**状态**")
        st.write(f"{'✅' if email_password else '❌'} 邮箱密码: {'已配置' if email_password else '未配置'}")
        st.write(f"{'✅' if email_to else '❌'} 收件邮箱: {email_to or '未配置'}")
        
        config_complete = all([email_enabled, smtp_server, email_from, email_password, email_to])
        if config_complete:
            st.success("✅ 邮件配置完整")
        else:
            st.warning("⚠️ 邮件配置不完整，请在 .env 文件中配置")


def test_email_notification():
    """测试邮件通知"""
    try:
        from notification_service import notification_service
        
        # 使用notification_service的send_test_email方法
        success, message = notification_service.send_test_email()
        
        if success:
            st.success(f"✅ {message}")
            st.balloons()
        else:
            st.error(f"❌ {message}")
    
    except Exception as e:
        st.error(f"❌ 发送测试邮件时出错: {str(e)}")
        import traceback
        st.code(traceback.format_exc())


# 主入口
if __name__ == "__main__":
    display_sector_strategy()

