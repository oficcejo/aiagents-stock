"""
新闻流量监测UI界面
为短线炒股提供新闻流量分析和交易指导
包含：仪表盘、实时监测、预警中心、趋势分析、历史记录、设置
"""
import streamlit as st
import plotly.graph_objects as go
import plotly.express as px
import pandas as pd
from datetime import datetime, timedelta
import time


def display_news_flow_monitor():
    """显示新闻流量监测主界面"""
    st.title("📰 新闻流量监测")
    
    # 功能说明
    with st.expander("💡 功能说明 - 流量为王理念", expanded=False):
        st.markdown("""
        ### 核心公式
        **接盘总量 = 流量 × 转化率 × 客单价**
        
        ### 核心理念
        - **流量高潮 = 价格高潮 = 逃命时刻**
        - 当热搜、媒体报道、KOL转发同时达到高潮时，就是出货时机
        - 短线操作：快进快出，紧跟龙头
        
        ### 流量阶段
        1. **启动** - 刚开始发酵，可关注
        2. **加速** - 增速加快，可参与
        3. **分歧** - 多空分歧，需谨慎
        4. **一致** - 流量高潮，危险！准备跑路
        5. **退潮** - 热度下降，及时止盈止损
        
        ### 流量类型
        - **存量流量型**：出生自带顶流（政策/大事件），时间窗口短（2-3天）
        - **增量流量型**：逐步发酵（话题传播），时间窗口长（5-10天）
        """)
    
    # 标签页
    tabs = st.tabs([
        "📊 仪表盘",
        "🔥 实时监测", 
        "⚠️ 预警中心",
        "📈 趋势分析",
        "📚 历史记录",
        "⚙️ 设置"
    ])
    
    with tabs[0]:
        display_dashboard()
    
    with tabs[1]:
        display_realtime_monitor()
    
    with tabs[2]:
        display_alert_center()
    
    with tabs[3]:
        display_trend_analysis()
    
    with tabs[4]:
        display_history_records()
    
    with tabs[5]:
        display_settings()


def display_dashboard():
    """显示仪表盘"""
    st.subheader("📊 流量仪表盘")
    
    try:
        from news_flow_engine import news_flow_engine
        dashboard_data = news_flow_engine.get_dashboard_data()
    except Exception as e:
        st.error(f"获取仪表盘数据失败: {e}")
        return
    
    # 核心指标卡片
    col1, col2, col3, col4 = st.columns(4)
    
    latest = dashboard_data.get('latest_snapshot', {})
    sentiment = dashboard_data.get('latest_sentiment', {})
    ai = dashboard_data.get('latest_ai_analysis', {})
    
    with col1:
        score = latest.get('total_score', 0) if latest else 0
        level = latest.get('flow_level', '无数据') if latest else '无数据'
        st.metric("流量得分", f"{score}", delta=level)
    
    with col2:
        sent_idx = sentiment.get('sentiment_index', 50) if sentiment else 50
        sent_class = sentiment.get('sentiment_class', '中性') if sentiment else '中性'
        st.metric("情绪指数", f"{sent_idx}", delta=sent_class)
    
    with col3:
        stage = sentiment.get('flow_stage', '未知') if sentiment else '未知'
        k_val = sentiment.get('viral_k', 1.0) if sentiment else 1.0
        st.metric("流量阶段", stage, delta=f"K值:{k_val}")
    
    with col4:
        advice = ai.get('advice', '观望') if ai else '观望'
        confidence = ai.get('confidence', 50) if ai else 50
        st.metric("AI建议", advice, delta=f"置信度:{confidence}%")
    
    st.divider()
    
    # 两列布局
    left_col, right_col = st.columns([2, 1])
    
    with left_col:
        # 流量趋势图
        st.markdown("#### 流量趋势（7天）")
        trend = dashboard_data.get('flow_trend', {})
        
        if trend.get('dates'):
            fig = go.Figure()
            fig.add_trace(go.Scatter(
                x=trend['dates'],
                y=trend['avg_scores'],
                mode='lines+markers',
                name='平均得分',
                line=dict(color='#1f77b4', width=2)
            ))
            fig.add_trace(go.Scatter(
                x=trend['dates'],
                y=trend['max_scores'],
                mode='lines',
                name='最高得分',
                line=dict(color='#ff7f0e', dash='dash')
            ))
            fig.update_layout(
                height=250,
                margin=dict(l=0, r=0, t=20, b=0),
                legend=dict(orientation="h", yanchor="bottom", y=1.02)
            )
            st.plotly_chart(fig, width='stretch')
            st.caption(f"趋势: {trend.get('trend', '无数据')} - {trend.get('analysis', '')[:50]}...")
        else:
            st.info("暂无趋势数据，请先执行监测")
    
    with right_col:
        # 最近预警
        st.markdown("#### 最近预警")
        alerts = dashboard_data.get('recent_alerts', [])
        
        if alerts:
            for alert in alerts[:5]:
                level = alert.get('alert_level', 'info')
                icon = {'danger': '🔴', 'warning': '🟠', 'info': '🔵'}.get(level, '⚪')
                st.markdown(f"{icon} **{alert.get('title', '')[:20]}...**")
                st.caption(alert.get('created_at', '')[:16])
        else:
            st.info("暂无预警")
    
    st.divider()
    
    # 热点词云和TOP100新闻
    display_wordcloud_and_top_news()
    
    st.divider()
    
    # 调度器状态
    scheduler = dashboard_data.get('scheduler_status', {})
    if scheduler:
        st.markdown("#### ⏰ 定时任务状态")
        cols = st.columns(4)
        cols[0].metric("运行状态", "运行中" if scheduler.get('running') else "已停止")
        
        next_runs = scheduler.get('next_run_times', {})
        cols[1].caption(f"热点同步: {next_runs.get('sync_hotspots', 'N/A')[:16] if next_runs.get('sync_hotspots') else 'N/A'}")
        cols[2].caption(f"预警生成: {next_runs.get('generate_alerts', 'N/A')[:16] if next_runs.get('generate_alerts') else 'N/A'}")
        cols[3].caption(f"深度分析: {next_runs.get('deep_analysis', 'N/A')[:16] if next_runs.get('deep_analysis') else 'N/A'}")


def display_wordcloud_and_top_news():
    """显示热点词云和跨平台TOP100新闻"""
    
    # 尝试获取最新数据
    try:
        from news_flow_db import news_flow_db
        from news_flow_data import NewsFlowDataFetcher
        
        # 获取最近的快照
        recent_snapshots = news_flow_db.get_recent_snapshots(limit=1)
        
        if not recent_snapshots:
            st.info("暂无数据，请先执行实时监测")
            return
        
        snapshot_id = recent_snapshots[0]['id']
        detail = news_flow_db.get_snapshot_detail(snapshot_id)
        
        hot_topics = detail.get('hot_topics', [])
        
    except Exception as e:
        st.warning(f"获取数据失败: {e}")
        return
    
    # 两列布局
    col1, col2 = st.columns([1, 1])
    
    with col1:
        st.markdown("#### ☁️ 热点词云")
        
        if hot_topics:
            # 使用Plotly生成词云效果（气泡图模拟）
            import random
            
            # 准备数据
            words_data = []
            for i, topic in enumerate(hot_topics[:30]):
                words_data.append({
                    'word': topic.get('topic', '')[:10],
                    'heat': topic.get('heat', 10),
                    'x': random.uniform(0, 100),
                    'y': random.uniform(0, 100),
                })
            
            if words_data:
                df_words = pd.DataFrame(words_data)
                
                # 创建气泡图模拟词云
                fig = px.scatter(
                    df_words,
                    x='x',
                    y='y',
                    size='heat',
                    text='word',
                    color='heat',
                    color_continuous_scale='YlOrRd',
                    size_max=60
                )
                
                fig.update_traces(
                    textposition='middle center',
                    textfont=dict(size=12),
                    marker=dict(opacity=0.7)
                )
                
                fig.update_layout(
                    height=350,
                    showlegend=False,
                    xaxis=dict(visible=False),
                    yaxis=dict(visible=False),
                    margin=dict(l=0, r=0, t=0, b=0),
                    coloraxis_showscale=False
                )
                
                st.plotly_chart(fig, width='stretch', key="wordcloud_chart")
        else:
            st.info("暂无热点词云数据")
    
    with col2:
        st.markdown("#### 📊 热点话题TOP20")
        
        if hot_topics:
            for i, topic in enumerate(hot_topics[:20], 1):
                heat = topic.get('heat', 0)
                cross = topic.get('cross_platform', 0)
                
                # 热度条
                heat_pct = min(heat, 100)
                st.markdown(f"**{i}. {topic.get('topic', '')[:15]}**")
                st.progress(heat_pct / 100)
                st.caption(f"热度: {heat} | 跨{cross}个平台")
        else:
            st.info("暂无热点话题")
    
    st.divider()
    
    # 跨平台热点新闻TOP100
    st.markdown("#### 📰 跨平台热点新闻TOP100")
    
    try:
        # 获取所有平台新闻
        fetcher = NewsFlowDataFetcher()
        multi_result = fetcher.get_multi_platform_news()
        
        if multi_result.get('success'):
            # 汇总所有新闻
            all_news = []
            for platform_data in multi_result.get('platforms_data', []):
                if platform_data.get('success'):
                    platform_name = platform_data.get('platform_name', '')
                    category = platform_data.get('category', '')
                    weight = platform_data.get('weight', 5)
                    
                    for news in platform_data.get('data', []):
                        rank = news.get('rank', 99)
                        # 计算综合得分
                        score = (100 - rank) * weight
                        
                        all_news.append({
                            '排名': len(all_news) + 1,
                            '平台': platform_name,
                            '类别': {'finance': '财经', 'social': '社交', 'news': '新闻', 'tech': '科技'}.get(category, '其他'),
                            '标题': (news.get('title') or '')[:40],
                            '平台排名': rank,
                            '综合分': score,
                        })
            
            # 按综合分排序
            all_news.sort(key=lambda x: x['综合分'], reverse=True)
            
            # 取TOP100
            top_100 = all_news[:100]
            
            # 重新编排名
            for i, news in enumerate(top_100, 1):
                news['排名'] = i
            
            if top_100:
                df_news = pd.DataFrame(top_100)
                
                # 添加筛选
                filter_col1, filter_col2 = st.columns([1, 3])
                with filter_col1:
                    category_filter = st.selectbox(
                        "按类别筛选",
                        ["全部", "财经", "社交", "新闻", "科技"],
                        key="news_category_filter"
                    )
                
                if category_filter != "全部":
                    df_news = df_news[df_news['类别'] == category_filter]
                
                st.dataframe(
                    df_news[['排名', '平台', '类别', '标题', '综合分']],
                    width='stretch',
                    hide_index=True,
                    height=400
                )
                
                st.caption(f"共 {len(df_news)} 条新闻 | 数据来源: {multi_result.get('success_count', 0)} 个平台")
            else:
                st.info("暂无新闻数据")
        else:
            st.warning("获取新闻数据失败")
            
    except Exception as e:
        st.error(f"加载新闻失败: {e}")


def display_realtime_monitor():
    """显示实时监测"""
    st.subheader("🔥 实时监测")
    
    # 监测参数
    col1, col2, col3 = st.columns([1, 1, 1])
    
    with col1:
        category = st.selectbox(
            "平台类别",
            ["全部平台", "财经平台", "社交媒体", "新闻媒体", "科技媒体"],
            key="monitor_category"
        )
    
    category_map = {
        "全部平台": None,
        "财经平台": "finance",
        "社交媒体": "social",
        "新闻媒体": "news",
        "科技媒体": "tech",
    }
    
    with col2:
        st.write("")
        st.write("")
        run_btn = st.button("🚀 开始AI智能分析", type="primary", width='stretch')
    
    with col3:
        st.write("")
        st.write("")
        # 空占位
    
    if run_btn:
        with st.spinner("🤖 AI正在分析全网热点新闻..."):
            try:
                from news_flow_engine import news_flow_engine
                
                cat = category_map.get(category)
                
                # 显示分析进度
                progress_bar = st.progress(0)
                status_text = st.empty()
                
                status_text.text("📊 获取多平台新闻数据...")
                progress_bar.progress(10)
                
                result = news_flow_engine.run_full_analysis(category=cat, include_ai=True)
                
                progress_bar.progress(100)
                status_text.empty()
                progress_bar.empty()
                
                if result['success']:
                    st.session_state['news_flow_result'] = result
                    # 清除之前的PDF缓存
                    if 'news_flow_pdf_data' in st.session_state:
                        del st.session_state['news_flow_pdf_data']
                    st.success(f"✅ AI分析完成！耗时 {result.get('duration', 0):.1f} 秒")
                else:
                    st.error(f"❌ 分析失败: {result.get('error')}")
                    
            except Exception as e:
                st.error(f"❌ 分析异常: {e}")
    
    # 显示结果
    if 'news_flow_result' in st.session_state:
        display_analysis_results(st.session_state['news_flow_result'])


def display_analysis_results(result: dict):
    """显示分析结果"""
    st.divider()
    
    flow_data = result.get('flow_data', {})
    model_data = result.get('model_data', {})
    sentiment_data = result.get('sentiment_data', {})
    ai_analysis = result.get('ai_analysis')
    trading_signals = result.get('trading_signals', {})
    
    # 核心指标
    st.markdown("### 📊 核心指标")
    
    cols = st.columns(5)
    
    with cols[0]:
        score = flow_data.get('total_score', 0)
        level = flow_data.get('level', '中')
        level_color = {'极高': '🔴', '高': '🟠', '中': '🟡', '低': '🔵'}.get(level, '⚪')
        st.metric("流量得分", f"{score}", delta=f"{level_color} {level}")
    
    with cols[1]:
        if sentiment_data:
            sent = sentiment_data.get('sentiment', {})
            st.metric("情绪指数", f"{sent.get('sentiment_index', 50)}", 
                     delta=sent.get('sentiment_class', '中性'))
    
    with cols[2]:
        if sentiment_data:
            stage = sentiment_data.get('flow_stage', {})
            signal = stage.get('signal', '观察')
            st.metric("流量阶段", stage.get('stage_name', '未知'), delta=signal)
    
    with cols[3]:
        if model_data:
            viral = model_data.get('viral_k', {})
            st.metric("K值", f"{viral.get('k_value', 1.0)}", delta=viral.get('trend', ''))
    
    with cols[4]:
        signal = trading_signals.get('overall_signal', '观望')
        conf = trading_signals.get('confidence', 50)
        signal_color = {'卖出': '🔴', '观望': '🟡', '买入': '🟢', '关注': '🔵'}.get(signal, '⚪')
        st.metric("交易信号", f"{signal_color} {signal}", delta=f"置信度:{conf}%")
    
    # 关键提示
    key_msg = trading_signals.get('key_message', '')
    if key_msg:
        if '危险' in key_msg or '逃命' in key_msg:
            st.error(f"⚠️ {key_msg}")
        elif '加速' in key_msg or '买入' in key_msg:
            st.success(f"💡 {key_msg}")
        else:
            st.info(f"💡 {key_msg}")
    
    st.divider()
    
    # 详细分析（两列）
    left_col, right_col = st.columns(2)
    
    with left_col:
        # 流量模型
        st.markdown("#### 🔬 流量模型分析")
        
        if model_data:
            # 潜力计算
            potential = model_data.get('potential', {})
            conversion = model_data.get('conversion', {})
            
            st.markdown(f"""
            - **接盘潜力**: {potential.get('potential_volume', 0):.1f}亿元 ({potential.get('potential_level', '未知')})
            - **转化率**: {conversion.get('conversion_rate', 0):.4%}
            - **流量类型**: {model_data.get('flow_type', {}).get('flow_type', '未知')}
            """)
            
            # 流量类型详情
            flow_type = model_data.get('flow_type', {})
            if flow_type.get('characteristics'):
                st.caption(f"特征: {', '.join(flow_type.get('characteristics', [])[:2])}")
                st.caption(f"时间窗口: {flow_type.get('time_window', 'N/A')}")
        
        # 情绪分析
        st.markdown("#### 💭 情绪分析")
        
        if sentiment_data:
            sentiment = sentiment_data.get('sentiment', {})
            flow_stage = sentiment_data.get('flow_stage', {})
            momentum = sentiment_data.get('momentum', {})
            
            st.markdown(f"""
            - **情绪分类**: {sentiment.get('sentiment_class', '中性')} ({sentiment.get('sentiment_index', 50)}分)
            - **流量阶段**: {flow_stage.get('stage_name', '未知')} - {flow_stage.get('signal', '观察')}
            - **情绪动量**: {momentum.get('momentum', 1.0)} ({momentum.get('trend', '稳定')})
            - **风险等级**: {sentiment_data.get('risk_level', '中等')}
            """)
            
            st.caption(sentiment_data.get('advice', ''))
    
    with right_col:
        # AI分析（如果有）
        if ai_analysis:
            st.markdown("#### 🤖 AI智能分析")
            
            # 投资建议
            advice = ai_analysis.get('investment_advice', {})
            if advice:
                advice_emoji = {'买入': '🟢', '持有': '🔵', '观望': '🟡', '回避': '🔴'}.get(advice.get('advice', '观望'), '⚪')
                st.markdown(f"**{advice_emoji} AI建议**: {advice.get('advice', '观望')} (置信度: {advice.get('confidence', 50)}%)")
                
                key_msg = advice.get('key_message', '')
                if key_msg:
                    st.info(f"💡 {key_msg}")
                
                if advice.get('action_plan'):
                    with st.expander("📋 行动计划"):
                        for i, plan in enumerate(advice.get('action_plan', [])[:5], 1):
                            st.write(f"{i}. {plan}")
            
            # 风险评估
            risk = ai_analysis.get('risk_assess', {})
            if risk:
                risk_color = {'低': '🟢', '中': '🟡', '高': '🔴'}.get(risk.get('risk_level', '中'), '🟡')
                st.markdown(f"**{risk_color} 风险等级**: {risk.get('risk_level', '未知')} (分数: {risk.get('risk_score', 50)}/100)")
                
        else:
            st.info("未运行AI分析。选择'完整分析（含AI）'模式获取AI智能分析。")
    
    st.divider()
    
    # AI详细分析区域（如果有AI分析）
    if ai_analysis:
        st.markdown("### 📊 AI深度分析报告")
        
        # 热门题材
        sector_analysis = ai_analysis.get('sector_analysis', {})
        hot_themes = sector_analysis.get('hot_themes', [])
        
        if hot_themes:
            st.markdown("#### 🔥 今日热门题材")
            theme_cols = st.columns(min(len(hot_themes), 4))
            for i, theme in enumerate(hot_themes[:4]):
                with theme_cols[i]:
                    heat_emoji = {'极高': '🔴', '高': '🟠', '中': '🟡'}.get(theme.get('heat_level', '中'), '🟡')
                    st.metric(
                        theme.get('theme', '未知'),
                        f"{heat_emoji} {theme.get('heat_level', '中')}",
                        delta=theme.get('sustainability', '')
                    )
            st.caption(f"题材来源: {', '.join([t.get('source', '')[:15] for t in hot_themes[:3]])}")
        
        # 受益板块详细分析
        benefited_sectors = sector_analysis.get('benefited_sectors', [])
        if benefited_sectors:
            st.markdown("#### 📈 受益板块分析")
            for sector in benefited_sectors[:5]:
                with st.expander(f"**{sector.get('name', '')}** - 置信度 {sector.get('confidence', 0)}%"):
                    st.write(f"**分析**: {sector.get('reason', '')}")
                    if sector.get('related_concepts'):
                        st.write(f"**相关概念**: {', '.join(sector.get('related_concepts', []))}")
                    if sector.get('leader_characteristics'):
                        st.write(f"**龙头特征**: {sector.get('leader_characteristics', '')}")
        
        # 多板块深度分析（多次AI调用结果）
        multi_sector = ai_analysis.get('multi_sector', {})
        sector_analyses = multi_sector.get('sector_analyses', [])
        
        if sector_analyses:
            st.markdown("#### 🎯 板块深度分析（多Agent分析）")
            st.caption(f"共分析 {len(sector_analyses)} 个热门板块，耗时 {multi_sector.get('analysis_time', 0)} 秒")
            
            # 板块核心指标卡片
            sector_cols = st.columns(min(len(sector_analyses), 4))
            for i, sector in enumerate(sector_analyses[:4]):
                with sector_cols[i]:
                    heat_emoji = {'极高': '🔴', '高': '🟠', '中': '🟡', '低': '🔵'}.get(
                        sector.get('heat_level', '中'), '🟡'
                    )
                    outlook_emoji = {'看涨': '📈', '震荡': '📊', '看跌': '📉'}.get(
                        sector.get('short_term_outlook', '震荡'), '📊'
                    )
                    
                    st.metric(
                        sector.get('sector_name', '未知'),
                        f"{heat_emoji} 热度{sector.get('heat_score', 50)}",
                        delta=f"{outlook_emoji} {sector.get('short_term_outlook', '震荡')}"
                    )
                    
                    # 显示关键指标
                    indicators = sector.get('key_indicators', {})
                    if indicators:
                        indicator_text = ' | '.join([f"{k}:{v}" for k, v in list(indicators.items())[:3]])
                        st.caption(indicator_text)
            
            # 详细分析展开
            for sector in sector_analyses:
                with st.expander(f"📊 {sector.get('sector_name', '')} - 详细分析"):
                    # 驱动因素
                    drivers = sector.get('drivers', [])
                    if drivers:
                        st.markdown("**驱动因素**:")
                        for driver in drivers[:3]:
                            impact_emoji = '✅' if driver.get('impact') == '正面' else '❌'
                            st.write(f"- {impact_emoji} [{driver.get('type', '')}] {driver.get('content', '')}")
                    
                    # 预判理由
                    st.markdown(f"**短期预判**: {sector.get('short_term_outlook', '震荡')} - {sector.get('outlook_reason', '')}")
                    
                    # 龙头股
                    leaders = sector.get('leader_stocks', [])
                    if leaders:
                        st.markdown("**板块龙头股**:")
                        leader_data = []
                        for stock in leaders[:5]:
                            leader_data.append({
                                '代码': stock.get('code', ''),
                                '名称': stock.get('name', ''),
                                '理由': stock.get('reason', '')[:30],
                                '策略': stock.get('strategy', '')[:30],
                            })
                        if leader_data:
                            st.dataframe(pd.DataFrame(leader_data), width='stretch', hide_index=True)
                    
                    # 投资建议
                    st.info(f"💡 {sector.get('investment_advice', '')}")
                    st.warning(f"⚠️ {sector.get('risk_warning', '')}")
        
        # 股票推荐
        stock_recommend = ai_analysis.get('stock_recommend', {})
        recommended_stocks = stock_recommend.get('recommended_stocks', [])
        
        if recommended_stocks:
            st.markdown("#### 💰 AI选股推荐")
            st.warning("⚠️ 以下为AI分析结果，仅供参考，不构成投资建议。股市有风险，投资需谨慎！")
            
            # 用表格展示推荐股票
            stock_data = []
            for stock in recommended_stocks[:8]:
                stock_data.append({
                    '代码': stock.get('code', ''),
                    '名称': stock.get('name', ''),
                    '板块': stock.get('sector', ''),
                    '风险': stock.get('risk_level', '中'),
                    '目标空间': stock.get('target_space', '-'),
                    '推荐理由': stock.get('reason', '')[:30] + '...' if len(stock.get('reason', '')) > 30 else stock.get('reason', ''),
                })
            
            if stock_data:
                df_stocks = pd.DataFrame(stock_data)
                st.dataframe(df_stocks, width='stretch', hide_index=True)
            
            # 展开查看详情
            with st.expander("📋 查看详细推荐理由"):
                for stock in recommended_stocks[:8]:
                    st.markdown(f"**{stock.get('code', '')} {stock.get('name', '')}**")
                    st.write(f"- 板块: {stock.get('sector', '')}")
                    st.write(f"- 理由: {stock.get('reason', '')}")
                    st.write(f"- 催化剂: {stock.get('catalyst', '')}")
                    st.write(f"- 策略: {stock.get('strategy', '')}")
                    if stock.get('attention_points'):
                        st.write(f"- 注意: {', '.join(stock.get('attention_points', []))}")
                    st.divider()
            
            # 整体策略
            if stock_recommend.get('overall_strategy'):
                st.info(f"📊 **整体策略**: {stock_recommend.get('overall_strategy', '')}")
            if stock_recommend.get('timing_advice'):
                st.caption(f"⏰ 时机建议: {stock_recommend.get('timing_advice', '')}")
            if stock_recommend.get('risk_warning'):
                st.error(f"⚠️ {stock_recommend.get('risk_warning', '')}")
        
        # 机会评估
        opportunity = sector_analysis.get('opportunity_assessment', '')
        trading_suggestion = sector_analysis.get('trading_suggestion', '')
        if opportunity or trading_suggestion:
            st.markdown("#### 💡 综合评估")
            if opportunity:
                st.write(opportunity)
            if trading_suggestion:
                st.success(f"📌 {trading_suggestion}")
        
        st.divider()
    
    # 热门话题和新闻
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("#### 🔥 热门话题TOP10")
        hot_topics = result.get('hot_topics', [])[:10]
        
        if hot_topics:
            df = pd.DataFrame([{
                '话题': t['topic'],
                '热度': t['heat'],
                '跨平台': t.get('cross_platform', 0),
            } for t in hot_topics])
            
            fig = px.bar(df, x='热度', y='话题', orientation='h',
                        color='热度', color_continuous_scale='Oranges')
            fig.update_layout(height=300, margin=dict(l=0, r=0, t=0, b=0))
            st.plotly_chart(fig, width='stretch')
    
    with col2:
        st.markdown("#### 📰 股票相关新闻TOP5")
        stock_news = result.get('stock_news', [])[:5]
        
        if stock_news:
            for news in stock_news:
                st.markdown(f"**[{news.get('platform_name', '')}]** {news.get('title', '')[:40]}...")
                st.caption(f"关键词: {', '.join(news.get('matched_keywords', [])[:3])}")
        else:
            st.info("暂无股票相关新闻")
    
    # PDF导出区域
    display_pdf_export_section(result)


def display_pdf_export_section(result: dict):
    """显示PDF导出区域"""
    st.divider()
    st.markdown("### 📄 导出报告")
    
    col1, col2, col3 = st.columns([3, 1, 1])
    
    with col1:
        st.write("将分析报告导出为PDF文件，方便保存和分享")
    
    with col2:
        if st.button("📥 生成PDF报告", type="primary", key="gen_pdf_btn"):
            with st.spinner("正在生成PDF报告..."):
                try:
                    from news_flow_pdf import NewsFlowPDFGenerator
                    generator = NewsFlowPDFGenerator()
                    pdf_path = generator.generate_report(result)
                    
                    if pdf_path:
                        with open(pdf_path, "rb") as f:
                            pdf_bytes = f.read()
                        
                        # 保存到session_state
                        st.session_state.news_flow_pdf_data = pdf_bytes
                        st.session_state.news_flow_pdf_filename = f"新闻流量分析报告_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf"
                        
                        st.success("✅ PDF报告生成成功！")
                        st.rerun()
                    else:
                        st.error("❌ PDF生成失败")
                except Exception as e:
                    st.error(f"❌ PDF生成失败: {str(e)}")
    
    with col3:
        # 如果已经生成了PDF，显示下载按钮
        if 'news_flow_pdf_data' in st.session_state:
            st.download_button(
                label="💾 下载PDF",
                data=st.session_state.news_flow_pdf_data,
                file_name=st.session_state.news_flow_pdf_filename,
                mime="application/pdf",
                key="download_pdf_btn"
            )


def display_alert_center():
    """显示预警中心"""
    st.subheader("⚠️ 预警中心")
    
    try:
        from news_flow_alert import news_flow_alert_system
        from news_flow_db import news_flow_db
    except Exception as e:
        st.error(f"模块加载失败: {e}")
        return
    
    # 预警统计
    summary = news_flow_alert_system.get_alert_summary(days=7)
    
    cols = st.columns(4)
    cols[0].metric("总预警数", summary.get('total_count', 0))
    cols[1].metric("危险预警", summary.get('danger_count', 0))
    cols[2].metric("警告预警", summary.get('warning_count', 0))
    cols[3].metric("提示预警", summary.get('info_count', 0))
    
    st.divider()
    
    # 预警列表
    col1, col2 = st.columns([3, 1])
    
    with col2:
        days = st.selectbox("时间范围", [1, 3, 7, 30], index=2, key="alert_days")
        alert_type = st.selectbox("预警类型", ["全部", "热度飙升", "流量高潮", "情绪极值", "病毒传播", "流量退潮"], key="alert_type_filter")
    
    type_map = {
        "热度飙升": "heat_surge",
        "流量高潮": "flow_peak",
        "情绪极值": "sentiment_extreme",
        "病毒传播": "viral_spread",
        "流量退潮": "flow_decline",
    }
    
    filter_type = type_map.get(alert_type) if alert_type != "全部" else None
    alerts = news_flow_alert_system.get_alert_history(days=days, alert_type=filter_type)
    
    with col1:
        if alerts:
            for alert in alerts[:20]:
                level = alert.get('alert_level', 'info')
                icon = {'danger': '🔴', 'warning': '🟠', 'info': '🔵'}.get(level, '⚪')
                level_name = {'danger': '危险', 'warning': '警告', 'info': '提示'}.get(level, '未知')
                
                with st.expander(f"{icon} [{level_name}] {alert.get('title', '')[:40]}..."):
                    st.markdown(alert.get('content', ''))
                    st.caption(f"时间: {alert.get('created_at', '')} | 类型: {alert.get('alert_type', '')}")
        else:
            st.info("暂无预警记录")
    
    st.divider()
    
    # 预警配置
    st.markdown("#### ⚙️ 预警阈值配置")
    
    config = news_flow_alert_system.get_threshold_config()
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        heat_th = st.number_input("热度阈值", value=int(config.get('heat_threshold', 800)), 
                                   min_value=100, max_value=1000, key="heat_th")
        k_th = st.number_input("K值阈值", value=float(config.get('viral_k_threshold', 1.5)),
                               min_value=1.0, max_value=3.0, step=0.1, key="k_th")
    
    with col2:
        sent_high = st.number_input("情绪高位阈值", value=int(config.get('sentiment_high_threshold', 90)),
                                     min_value=70, max_value=100, key="sent_high")
        sent_low = st.number_input("情绪低位阈值", value=int(config.get('sentiment_low_threshold', 20)),
                                    min_value=0, max_value=30, key="sent_low")
    
    with col3:
        rank_th = st.number_input("排名变化阈值", value=int(config.get('rank_change_threshold', 10)),
                                   min_value=5, max_value=50, key="rank_th")
        
        if st.button("保存配置", key="save_alert_config"):
            news_flow_alert_system.set_threshold('heat_threshold', heat_th)
            news_flow_alert_system.set_threshold('viral_k_threshold', k_th)
            news_flow_alert_system.set_threshold('sentiment_high_threshold', sent_high)
            news_flow_alert_system.set_threshold('sentiment_low_threshold', sent_low)
            news_flow_alert_system.set_threshold('rank_change_threshold', rank_th)
            st.success("配置已保存")


def display_trend_analysis():
    """显示趋势分析"""
    st.subheader("📈 趋势分析")
    
    try:
        from news_flow_engine import news_flow_engine
        from news_flow_db import news_flow_db
    except Exception as e:
        st.error(f"模块加载失败: {e}")
        return
    
    # 时间范围选择
    days = st.slider("分析天数", min_value=3, max_value=30, value=7, key="trend_days")
    
    # 流量趋势
    trend = news_flow_engine.get_flow_trend(days=days)
    
    col1, col2 = st.columns([2, 1])
    
    with col1:
        st.markdown("#### 流量趋势图")
        
        if trend.get('dates'):
            fig = go.Figure()
            
            # 平均得分
            fig.add_trace(go.Scatter(
                x=trend['dates'],
                y=trend['avg_scores'],
                mode='lines+markers',
                name='平均得分',
                line=dict(color='#1f77b4', width=2),
                fill='tozeroy',
                fillcolor='rgba(31, 119, 180, 0.1)'
            ))
            
            # 最高得分
            fig.add_trace(go.Scatter(
                x=trend['dates'],
                y=trend['max_scores'],
                mode='lines',
                name='最高得分',
                line=dict(color='#ff7f0e', dash='dash')
            ))
            
            # 最低得分
            fig.add_trace(go.Scatter(
                x=trend['dates'],
                y=trend.get('min_scores', []),
                mode='lines',
                name='最低得分',
                line=dict(color='#2ca02c', dash='dot')
            ))
            
            fig.update_layout(
                height=350,
                margin=dict(l=0, r=0, t=20, b=0),
                legend=dict(orientation="h", yanchor="bottom", y=1.02),
                yaxis_title="流量得分"
            )
            st.plotly_chart(fig, width='stretch')
        else:
            st.info("暂无趋势数据")
    
    with col2:
        st.markdown("#### 趋势分析")
        st.markdown(f"**趋势方向**: {trend.get('trend', '无数据')}")
        st.markdown(trend.get('analysis', '暂无分析'))
    
    st.divider()
    
    # 情绪趋势
    st.markdown("#### 情绪趋势")
    
    sentiments = news_flow_db.get_sentiment_history(limit=days * 3)
    
    if sentiments:
        df = pd.DataFrame([{
            '时间': s.get('fetch_time', s.get('created_at', ''))[:16],
            '情绪指数': s.get('sentiment_index', 50),
            'K值': s.get('viral_k', 1.0),
            '阶段': s.get('flow_stage', '未知'),
        } for s in sentiments])
        
        if not df.empty:
            df = df.sort_values('时间')
            
            fig = go.Figure()
            
            fig.add_trace(go.Scatter(
                x=df['时间'],
                y=df['情绪指数'],
                mode='lines+markers',
                name='情绪指数',
                line=dict(color='#9467bd', width=2)
            ))
            
            # 添加阈值线
            fig.add_hline(y=80, line_dash="dash", line_color="red", 
                         annotation_text="乐观区", annotation_position="right")
            fig.add_hline(y=20, line_dash="dash", line_color="green",
                         annotation_text="悲观区", annotation_position="right")
            
            fig.update_layout(
                height=250,
                margin=dict(l=0, r=0, t=20, b=0),
                yaxis_title="情绪指数"
            )
            st.plotly_chart(fig, width='stretch')
    else:
        st.info("暂无情绪数据")
    
    st.divider()
    
    # 每日统计表格
    st.markdown("#### 每日统计")
    
    stats = news_flow_db.get_daily_statistics(days)
    
    if stats:
        df = pd.DataFrame([{
            '日期': s['date'],
            '平均得分': s['avg_score'],
            '最高得分': s['max_score'],
            '最低得分': s['min_score'],
            '采集次数': s['snapshot_count'],
            '热门话题': ', '.join(s.get('top_topics', [])[:3]),
        } for s in stats])
        
        st.dataframe(df, width='stretch', hide_index=True)
    else:
        st.info("暂无统计数据")


def display_history_records():
    """显示历史记录"""
    st.subheader("📚 历史记录")
    
    try:
        from news_flow_db import news_flow_db
    except Exception as e:
        st.error(f"模块加载失败: {e}")
        return
    
    # 获取历史快照
    snapshots = news_flow_db.get_history_snapshots(limit=50)
    
    if not snapshots:
        st.info("暂无历史记录，请先执行监测")
        return
    
    # 快照列表
    st.markdown("#### 分析报告列表")
    
    for snapshot in snapshots[:20]:
        score = snapshot.get('total_score', 0)
        level = snapshot.get('flow_level', '中')
        level_icon = {'极高': '🔴', '高': '🟠', '中': '🟡', '低': '🔵'}.get(level, '⚪')
        
        with st.expander(f"{level_icon} {snapshot.get('fetch_time', '')} - 流量得分: {score} ({level})"):
            # 获取详情
            detail = news_flow_db.get_snapshot_detail(snapshot['id'])
            
            if detail:
                col1, col2 = st.columns(2)
                
                with col1:
                    st.markdown("**基本信息**")
                    st.markdown(f"- 流量得分: {score}")
                    st.markdown(f"- 流量等级: {level}")
                    st.markdown(f"- 平台数: {snapshot.get('total_platforms', 0)}")
                    st.markdown(f"- 成功数: {snapshot.get('success_count', 0)}")
                    
                    # 情绪信息
                    sentiment = detail.get('sentiment')
                    if sentiment:
                        st.markdown("**情绪分析**")
                        st.markdown(f"- 情绪指数: {sentiment.get('sentiment_index', 'N/A')}")
                        st.markdown(f"- 情绪分类: {sentiment.get('sentiment_class', 'N/A')}")
                        st.markdown(f"- 流量阶段: {sentiment.get('flow_stage', 'N/A')}")
                
                with col2:
                    # AI分析
                    ai = detail.get('ai_analysis')
                    if ai:
                        st.markdown("**AI分析结果**")
                        st.markdown(f"- 投资建议: {ai.get('advice', 'N/A')}")
                        st.markdown(f"- 置信度: {ai.get('confidence', 'N/A')}%")
                        st.markdown(f"- 风险等级: {ai.get('risk_level', 'N/A')}")
                        
                        if ai.get('summary'):
                            st.caption(ai['summary'][:100] + "...")
                    
                    # 热门话题
                    topics = detail.get('hot_topics', [])[:5]
                    if topics:
                        st.markdown("**热门话题**")
                        for t in topics:
                            st.markdown(f"- {t['topic']} (热度:{t['heat']})")
    
    st.divider()
    
    # AI分析历史
    st.markdown("#### AI分析历史")
    
    ai_history = news_flow_db.get_ai_analysis_history(limit=10)
    
    if ai_history:
        df = pd.DataFrame([{
            '时间': a.get('created_at', '')[:16],
            '建议': a.get('advice', 'N/A'),
            '置信度': f"{a.get('confidence', 0)}%",
            '风险': a.get('risk_level', 'N/A'),
            '摘要': (a.get('summary', '') or '')[:30] + "...",
        } for a in ai_history])
        
        st.dataframe(df, width='stretch', hide_index=True)
    else:
        st.info("暂无AI分析记录")


def display_settings():
    """显示设置"""
    st.subheader("⚙️ 设置")
    
    # 平台配置
    st.markdown("#### 📡 支持的平台")
    
    try:
        from news_flow_data import NewsFlowDataFetcher
        fetcher = NewsFlowDataFetcher()
        platforms = fetcher.get_platform_list()
        
        # 按类别分组
        categories = {}
        for p in platforms:
            cat = p['category']
            if cat not in categories:
                categories[cat] = []
            categories[cat].append(p)
        
        cat_names = {
            'social': '社交媒体',
            'news': '新闻媒体',
            'finance': '财经平台',
            'tech': '科技媒体',
        }
        
        cols = st.columns(len(categories))
        for i, (cat, items) in enumerate(categories.items()):
            with cols[i]:
                st.markdown(f"**{cat_names.get(cat, cat)}** ({len(items)}个)")
                for p in items:
                    st.caption(f"- {p['name']} (权重:{p['weight']})")
    except:
        st.warning("无法加载平台列表")
    
    st.divider()
    
    # 定时任务配置
    st.markdown("#### ⏰ 定时任务管理")
    
    try:
        from news_flow_scheduler import news_flow_scheduler
        
        status = news_flow_scheduler.get_status()
        
        col1, col2 = st.columns([1, 2])
        
        with col1:
            st.markdown(f"**运行状态**: {'✅ 运行中' if status.get('running') else '⏸️ 已停止'}")
            
            if status.get('running'):
                if st.button("停止调度器", key="stop_scheduler"):
                    news_flow_scheduler.stop()
                    st.success("调度器已停止")
                    st.rerun()
            else:
                if st.button("启动调度器", key="start_scheduler"):
                    news_flow_scheduler.start()
                    st.success("调度器已启动")
                    st.rerun()
        
        with col2:
            st.markdown("**任务配置**")
            
            intervals = status.get('task_intervals', {})
            enabled = status.get('task_enabled', {})
            
            tasks = [
                ('sync_hotspots', '热点同步', 30),
                ('generate_alerts', '预警生成', 60),
                ('deep_analysis', '深度分析', 120),
            ]
            
            for task_id, task_name, default_interval in tasks:
                col_a, col_b, col_c = st.columns([2, 2, 1])
                
                with col_a:
                    is_enabled = st.checkbox(
                        task_name,
                        value=enabled.get(task_id, True),
                        key=f"task_enabled_{task_id}"
                    )
                
                with col_b:
                    interval = st.number_input(
                        "间隔(分钟)",
                        value=intervals.get(task_id, default_interval),
                        min_value=5,
                        max_value=240,
                        key=f"task_interval_{task_id}",
                        label_visibility="collapsed"
                    )
                
                with col_c:
                    if st.button("立即执行", key=f"run_{task_id}"):
                        if task_id == 'sync_hotspots':
                            news_flow_scheduler.run_sync_now()
                        elif task_id == 'generate_alerts':
                            news_flow_scheduler.run_alerts_now()
                        else:
                            news_flow_scheduler.run_analysis_now()
                        st.success(f"{task_name} 已触发")
            
            if st.button("保存任务配置", key="save_task_config"):
                for task_id, _, _ in tasks:
                    news_flow_scheduler.set_task_enabled(
                        task_id,
                        st.session_state.get(f"task_enabled_{task_id}", True)
                    )
                    news_flow_scheduler.set_task_interval(
                        task_id,
                        st.session_state.get(f"task_interval_{task_id}", 30)
                    )
                st.success("任务配置已保存")
                
    except Exception as e:
        st.warning(f"定时任务模块加载失败: {e}")
    
    st.divider()
    
    # 使用建议
    st.markdown("#### 💡 使用建议")
    st.markdown("""
    1. **盘前分析** (09:00前)
       - 运行快速分析，了解当日热点
       - 关注流量阶段和情绪指数
       
    2. **盘中监测** (交易时间)
       - 开启定时任务自动监测
       - 关注预警通知
       
    3. **盘后复盘** (15:00后)
       - 运行完整分析（含AI）
       - 分析当日流量变化趋势
       
    4. **风险提示**
       - 当流量阶段进入"一致"时，立即警惕
       - 当情绪指数>85或K值>1.5时，注意风险
       - 本工具仅供参考，投资决策需谨慎
    """)


# 入口
if __name__ == "__main__":
    display_news_flow_monitor()
