"""
智策UI界面模块
展示板块分析结果和预测
"""

import streamlit as st
import time
import plotly.graph_objects as go
import plotly.express as px
import pandas as pd
from datetime import datetime, time as dt_time
import time
import base64
import json

from sector_strategy_data import SectorStrategyDataFetcher
from sector_strategy_engine import SectorStrategyEngine
from sector_strategy_pdf import SectorStrategyPDFGenerator
from sector_strategy_db import SectorStrategyDatabase
from sector_strategy_scheduler import sector_strategy_scheduler


def _parse_json_field(value, default):
    """将可能的JSON字符串安全转换为Python对象"""
    try:
        if isinstance(value, (dict, list)):
            return value
        if value is None:
            return default
        if isinstance(value, str):
            v = value.strip()
            if not v:
                return default
            return json.loads(v)
        return default
    except Exception:
        return default


def display_sector_strategy():
    """显示智策板块分析主界面"""
    
    st.markdown("""
    <div class="top-nav">
        <h1 class="nav-title">🎯 智策 - AI驱动的板块策略分析</h1>
        <p class="nav-subtitle">Multi-Agent Sector Strategy Analysis | 板块多空·轮动·热度预测</p>
    </div>
    """, unsafe_allow_html=True)
    
    st.markdown("---")
    
    # 创建标签页
    tab1, tab2 = st.tabs(["📊 智策分析", "📋 历史报告"])
    
    with tab1:
        display_analysis_tab()
    
    with tab2:
        display_history_tab()


def display_analysis_tab():
    """显示分析标签页"""
    
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
        # 导入model_config.py中定义的model_options
        from model_config import model_options as app_model_options
        selected_model = st.selectbox(
            "AI模型",
            list(app_model_options.keys()),
            format_func=lambda x: app_model_options[x],
            help="Reasoner模型提供更强的推理能力"
        )
    
    with col2:
        st.write("")
        st.write("")
        analyze_button = st.button("🚀 开始智策分析", type="primary", width='content')
    
    with col3:
        st.write("")
        st.write("")
        if st.button("🔄 清除结果", width='content'):
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


def display_history_tab():
    """显示历史报告标签页"""
    
    st.markdown("### 📋 智策历史报告")
    st.markdown("查看和管理历史分析报告")
    
    try:
        # 初始化引擎以获取历史报告
        engine = SectorStrategyEngine()
        
        # 获取历史报告
        reports = engine.get_historical_reports(limit=20)
        
        if reports.empty:
            st.info("📝 暂无历史报告")
            st.markdown("""
            **提示**: 
            - 运行智策分析后，报告将自动保存到历史记录中
            - 您可以在此查看和管理所有历史分析报告
            """)
            return
        
        st.success(f"📊 共找到 {len(reports)} 份历史报告")
        
        # 报告列表（精简摘要展示）
        for i, report in reports.iterrows():
            report_id = report['id'] if 'id' in report else None
            created_at = report['created_at'] if 'created_at' in report else ''
            data_date_range = report['data_date_range'] if 'data_date_range' in report else ''
            summary = report['summary'] if 'summary' in report else '智策板块分析报告'
            confidence_score = report['confidence_score'] if 'confidence_score' in report else 0
            risk_level = report['risk_level'] if 'risk_level' in report else '中等'
            market_outlook = report['market_outlook'] if 'market_outlook' in report else '谨慎乐观'

            with st.container():
                st.markdown(f"**📊 报告 #{report_id}**")
                st.caption(f"生成时间: {created_at} | 数据区间: {data_date_range}")

                col1, col2, col3 = st.columns([1, 1, 1])
                with col1:
                    st.metric("置信度", f"{confidence_score:.1%}")
                with col2:
                    st.metric("风险等级", risk_level)
                with col3:
                    st.metric("市场展望", market_outlook)

                # 操作区：加载到分析视图 / 删除
                op1, op2 = st.columns([1, 1])
                with op1:
                    if st.button("📥 加载到分析视图", key=f"load_{report_id}"):
                        # 获取报告详情并写入session以展示到分析视图
                        detail = engine.get_report_detail(report_id)
                        if detail and isinstance(detail.get('analysis_content_parsed'), dict):
                            st.session_state.sector_strategy_result = detail['analysis_content_parsed']
                            st.session_state.sector_strategy_result_source = 'from_history'
                            st.session_state.loaded_report_id = report_id
                            st.success("✅ 已加载到分析视图，请切换到‘智策分析’标签查看")
                            time.sleep(0.5)
                            st.rerun()
                        else:
                            st.error("❌ 加载失败：报告内容缺失")
                with op2:
                    if st.button(f"🗑️ 删除", key=f"delete_{report_id}"):
                        if engine.delete_report(report_id):
                            st.success("报告已删除")
                            st.rerun()
                        else:
                            st.error("删除失败")

                # 改进的摘要展示逻辑，突出看多板块信息
                st.markdown("**📝 报告摘要**")
                summary_text = summary or "智策板块分析报告"
                
                # 解析摘要中的看多板块信息
                if "看多板块:" in summary_text:
                    parts = summary_text.split("，看多板块:")
                    main_summary = parts[0]
                    bullish_info = parts[1] if len(parts) > 1 else ""
                    
                    # 显示主要摘要信息
                    st.markdown(f"🔹 {main_summary}")
                    
                    # 特别突出显示看多板块
                    if bullish_info:
                        st.markdown(f"📈 **看多板块**: :green[{bullish_info}]")
                else:
                    # 原有的简单展示方式
                    short = summary_text if len(summary_text) <= 120 else (summary_text[:120] + "...")
                    with st.expander(f"{short}", expanded=False):
                        st.write(summary_text)

                st.markdown("-")
    
    except Exception as e:
        st.error(f"❌ 加载历史报告失败: {e}")


def display_report_detail(report_id):
    """详细报告页面已移除：保留占位以避免旧调用报错"""
    st.info("当前版本仅提供报告摘要，详细页面已移除。")


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
        # 使用带缓存回退的获取逻辑
        data = fetcher.get_cached_data_with_fallback()
        
        if not data.get("success"):
            st.error("❌ 数据获取失败")
            return
        
        progress_bar.progress(30)
        status_text.text("✓ 数据获取完成")
        
        # 显示数据摘要（含缓存提示）
        display_data_summary(data)
        
        # 2. 运行AI分析
        status_text.text("🤖 AI智能体团队正在分析，预计需要10分钟...")
        progress_bar.progress(40)
        
        engine = SectorStrategyEngine(model=model)
        result = engine.run_comprehensive_analysis(data)
        # 传递缓存元信息到结果以便页面提示
        if data.get("from_cache") or data.get("cache_warning"):
            result["cache_meta"] = {
                "from_cache": bool(data.get("from_cache")),
                "cache_warning": data.get("cache_warning", ""),
                "data_timestamp": data.get("timestamp")
            }
        
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
    # 缓存提示横幅
    if data.get("from_cache") or data.get("cache_warning"):
        st.warning(data.get("cache_warning", "当前数据来自缓存，可能不是最新信息"))
    
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


def display_saved_report_summary(saved_report: dict):
    """在主页面显示保存的报告摘要（标题、时间、关键指标）"""
    st.subheader("📝 报告摘要")
    summary = saved_report.get('summary', '智策板块分析报告')
    created_at = saved_report.get('created_at', '')
    data_date_range = saved_report.get('data_date_range', '')
    confidence_score = saved_report.get('confidence_score', 0)
    risk_level = saved_report.get('risk_level', '中等')
    market_outlook = saved_report.get('market_outlook', '谨慎乐观')
    st.caption(f"生成时间: {created_at} | 数据区间: {data_date_range}")
    
    # 使用改进的摘要展示逻辑，突出看多板块信息
    summary_text = summary or "智策板块分析报告"
    
    # 解析摘要中的看多板块信息
    if "看多板块:" in summary_text:
        parts = summary_text.split("，看多板块:")
        main_summary = parts[0]
        bullish_info = parts[1] if len(parts) > 1 else ""
        
        # 显示主要摘要信息
        st.markdown(f"🔹 {main_summary}")
        
        # 特别突出显示看多板块
        if bullish_info:
            st.markdown(f"📈 **看多板块**: :green[{bullish_info}]")
    else:
        # 原有的简单展示方式
        st.info(summary_text)
        
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("置信度", f"{confidence_score:.1%}")
    with col2:
        st.metric("风险等级", risk_level)
    with col3:
        st.metric("市场展望", market_outlook)


def display_analysis_results(result):
    """显示分析结果"""
    
    st.success("✅ 智策分析完成！")
    st.info(f"📅 分析时间: {result.get('timestamp', 'N/A')}")
    # 显示缓存提示（如果本次分析使用了缓存数据）
    cache_meta = result.get("cache_meta")
    if cache_meta and (cache_meta.get("from_cache") or cache_meta.get("cache_warning")):
        st.warning(cache_meta.get("cache_warning", "当前分析基于缓存数据，可能不是最新信息"))

    # 如果内容源自历史报告，给出返回入口
    if st.session_state.get('sector_strategy_result_source') == 'from_history':
        loaded_id = st.session_state.get('loaded_report_id')
        st.info(f"🗂️ 当前展示为历史报告内容（ID: {loaded_id}）")
        if st.button("↩️ 返回历史报告列表"):
            # 清除已加载的历史报告并返回
            for key in ['sector_strategy_result', 'sector_strategy_result_source', 'loaded_report_id']:
                if key in st.session_state:
                    del st.session_state[key]
            st.rerun()
    
    # 显示引擎回传的保存报告摘要（用于主页面动态更新）
    saved_report = result.get("saved_report")
    if saved_report:
        display_saved_report_summary(saved_report)
    
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
    st.plotly_chart(fig, use_container_width=True, config={'responsive': True}, key="sector_confidence")
    
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
    st.plotly_chart(fig, use_container_width=True, config={'responsive': True}, key="sector_heat")


def display_pdf_export_section(result):
    """显示PDF导出部分"""
    st.subheader("📄 导出报告")
    
    col1, col2, col3, col4 = st.columns([2, 1, 1, 1])
    
    with col1:
        st.write("将分析报告导出为PDF或Markdown文件，方便保存和分享")
    
    with col2:
        if st.button("📥 生成PDF报告", type="primary", width='content'):
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
        if st.button("📝 生成Markdown", type="secondary", width='content'):
            with st.spinner("正在生成Markdown报告..."):
                try:
                    # 生成Markdown内容
                    markdown_content = generate_sector_markdown_report(result)
                    
                    # 保存到session_state
                    st.session_state.sector_markdown_data = markdown_content
                    st.session_state.sector_markdown_filename = f"智策报告_{result.get('timestamp', datetime.now().strftime('%Y%m%d_%H%M%S')).replace(':', '').replace(' ', '_')}.md"
                    
                    st.success("✅ Markdown报告生成成功！")
                    st.rerun()
                    
                except Exception as e:
                    st.error(f"❌ Markdown生成失败: {str(e)}")
    
    with col4:
        # 如果已经生成了PDF，显示下载按钮
        if 'sector_pdf_data' in st.session_state:
            st.download_button(
                        label="💾 下载PDF",
                        data=st.session_state.sector_pdf_data,
                        file_name=st.session_state.sector_pdf_filename,
                        mime="application/pdf",
                        width='content'
                    )
        
        # 如果已经生成了Markdown，显示下载按钮
        if 'sector_markdown_data' in st.session_state:
            st.download_button(
                        label="💾 下载Markdown",
                        data=st.session_state.sector_markdown_data,
                        file_name=st.session_state.sector_markdown_filename,
                        mime="text/markdown",
                        width='content'
                    )


def generate_sector_markdown_report(result_data: dict) -> str:
    """生成智策分析Markdown报告"""
    
    # 获取当前时间
    current_time = datetime.now().strftime("%Y年%m月%d日 %H:%M:%S")
    
    # 标题页
    markdown_content = f"""# 智策板块策略分析报告

**AI驱动的多维度板块投资决策支持系统**

---

## 📊 报告信息

- **生成时间**: {current_time}
- **分析周期**: 当日市场数据
- **AI模型**: DeepSeek Multi-Agent System
- **分析维度**: 宏观·板块·资金·情绪

> ⚠️ 本报告由AI系统自动生成，仅供参考，不构成投资建议。投资有风险，决策需谨慎。

---

## 📈 市场概况

本报告基于{result_data.get('timestamp', 'N/A')}的实时市场数据，
通过四位AI智能体的多维度分析，为您提供板块投资策略建议。

### 分析师团队:

- **宏观策略师** - 分析宏观经济、政策导向、新闻事件
- **板块诊断师** - 分析板块走势、估值水平、轮动特征
- **资金流向分析师** - 分析主力资金、北向资金流向
- **市场情绪解码员** - 分析市场情绪、热度、赚钱效应

"""
    
    # 核心预测
    predictions = result_data.get('final_predictions', {})
    
    if predictions.get('prediction_text'):
        # 文本格式预测
        markdown_content += f"""
## 🎯 核心预测

{predictions.get('prediction_text', '')}

"""
    else:
        # JSON格式预测
        markdown_content += "## 🎯 核心预测\n\n"
        
        # 1. 板块多空预测
        long_short = predictions.get('long_short', {})
        bullish = long_short.get('bullish', [])
        bearish = long_short.get('bearish', [])
        
        markdown_content += "### 📊 板块多空预测\n\n"
        
        if bullish:
            markdown_content += "#### 🟢 看多板块\n\n"
            for idx, item in enumerate(bullish, 1):
                markdown_content += f"{idx}. **{item.get('sector', 'N/A')}** (信心度: {item.get('confidence', 0)}/10)\n"
                markdown_content += f"   - 理由: {item.get('reason', 'N/A')}\n"
                markdown_content += f"   - 风险: {item.get('risk', 'N/A')}\n\n"
        
        if bearish:
            markdown_content += "#### 🔴 看空板块\n\n"
            for idx, item in enumerate(bearish, 1):
                markdown_content += f"{idx}. **{item.get('sector', 'N/A')}** (信心度: {item.get('confidence', 0)}/10)\n"
                markdown_content += f"   - 理由: {item.get('reason', 'N/A')}\n"
                markdown_content += f"   - 风险: {item.get('risk', 'N/A')}\n\n"
        
        # 2. 板块轮动预测
        rotation = predictions.get('rotation', {})
        current_strong = rotation.get('current_strong', [])
        potential = rotation.get('potential', [])
        declining = rotation.get('declining', [])
        
        markdown_content += "### 🔄 板块轮动预测\n\n"
        
        if current_strong:
            markdown_content += "#### 💪 当前强势板块\n\n"
            for item in current_strong:
                markdown_content += f"- **{item.get('sector', 'N/A')}**\n"
                markdown_content += f"  - 轮动逻辑: {item.get('logic', 'N/A')}\n"
                markdown_content += f"  - 时间窗口: {item.get('time_window', 'N/A')}\n"
                markdown_content += f"  - 操作建议: {item.get('advice', 'N/A')}\n\n"
        
        if potential:
            markdown_content += "#### 🌱 潜力接力板块\n\n"
            for item in potential:
                markdown_content += f"- **{item.get('sector', 'N/A')}**\n"
                markdown_content += f"  - 轮动逻辑: {item.get('logic', 'N/A')}\n"
                markdown_content += f"  - 时间窗口: {item.get('time_window', 'N/A')}\n"
                markdown_content += f"  - 操作建议: {item.get('advice', 'N/A')}\n\n"
        
        if declining:
            markdown_content += "#### 📉 衰退板块\n\n"
            for item in declining:
                markdown_content += f"- **{item.get('sector', 'N/A')}**\n"
                markdown_content += f"  - 轮动逻辑: {item.get('logic', 'N/A')}\n"
                markdown_content += f"  - 时间窗口: {item.get('time_window', 'N/A')}\n"
                markdown_content += f"  - 操作建议: {item.get('advice', 'N/A')}\n\n"
        
        # 3. 板块热度排行
        heat = predictions.get('heat', {})
        hottest = heat.get('hottest', [])
        heating = heat.get('heating', [])
        cooling = heat.get('cooling', [])
        
        markdown_content += "### 🔥 板块热度排行\n\n"
        
        if hottest:
            markdown_content += "#### 最热板块\n\n| 排名 | 板块 | 热度评分 | 趋势 | 持续性 |\n|------|------|----------|------|--------|\n"
            for idx, item in enumerate(hottest[:10], 1):
                markdown_content += f"| {idx} | {item.get('sector', 'N/A')} | {item.get('score', 0)} | {item.get('trend', 'N/A')} | {item.get('sustainability', 'N/A')} |\n"
            markdown_content += "\n"
        
        if heating:
            markdown_content += "#### 升温板块\n\n"
            for idx, item in enumerate(heating[:5], 1):
                markdown_content += f"{idx}. {item.get('sector', 'N/A')} (评分: {item.get('score', 0)})\n"
            markdown_content += "\n"
        
        if cooling:
            markdown_content += "#### 降温板块\n\n"
            for idx, item in enumerate(cooling[:5], 1):
                markdown_content += f"{idx}. {item.get('sector', 'N/A')} (评分: {item.get('score', 0)})\n"
            markdown_content += "\n"
        
        # 4. 策略总结
        summary = predictions.get('summary', {})
        if summary:
            markdown_content += "### 📝 策略总结\n\n"
            
            if summary.get('market_view'):
                markdown_content += f"**市场观点:** {summary.get('market_view', '')}\n\n"
            
            if summary.get('key_opportunity'):
                markdown_content += f"**核心机会:** {summary.get('key_opportunity', '')}\n\n"
            
            if summary.get('major_risk'):
                markdown_content += f"**主要风险:** {summary.get('major_risk', '')}\n\n"
            
            if summary.get('strategy'):
                markdown_content += f"**整体策略:** {summary.get('strategy', '')}\n\n"
    
    # AI智能体分析
    agents_analysis = result_data.get('agents_analysis', {})
    if agents_analysis:
        markdown_content += "## 🤖 AI智能体分析\n\n"
        
        for key, agent_data in agents_analysis.items():
            agent_name = agent_data.get('agent_name', '未知分析师')
            agent_role = agent_data.get('agent_role', '')
            focus_areas = ', '.join(agent_data.get('focus_areas', []))
            analysis = agent_data.get('analysis', '')
            
            markdown_content += f"### {agent_name}\n\n"
            markdown_content += f"- **职责**: {agent_role}\n"
            markdown_content += f"- **关注领域**: {focus_areas}\n\n"
            markdown_content += f"{analysis}\n\n"
            markdown_content += "---\n\n"
    
    # 综合研判
    comprehensive_report = result_data.get('comprehensive_report', '')
    if comprehensive_report:
        markdown_content += "## 📊 综合研判\n\n"
        markdown_content += f"{comprehensive_report}\n\n"
    
    markdown_content += """
---

*报告由智策AI系统自动生成*
"""
    
    return markdown_content


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
                    if st.button("▶️ 启动", width='content', type="primary"):
                        if sector_strategy_scheduler.start(schedule_time_str):
                            st.success(f"✅ 定时任务已启动！每天 {schedule_time_str} 运行")
                            time.sleep(1)
                            st.rerun()
                        else:
                            st.error("❌ 启动失败")
                else:
                    if st.button("⏹️ 停止", width='content'):
                        if sector_strategy_scheduler.stop():
                            st.success("✅ 定时任务已停止")
                            time.sleep(1)
                            st.rerun()
                        else:
                            st.error("❌ 停止失败")
            
            with col_b:
                if st.button("🔄 立即运行", width='content'):
                    with st.spinner("正在运行分析..."):
                        sector_strategy_scheduler.manual_run()
                    st.success("✅ 手动分析完成！")
            
            with col_c:
                if st.button("📧 测试邮件", width='content'):
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

