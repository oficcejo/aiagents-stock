import streamlit as st
import plotly.graph_objects as go
import plotly.express as px
import pandas as pd
import json
from datetime import datetime
import time
import base64
import os

from stock_data import StockDataFetcher
from ai_agents import StockAnalysisAgents
from pdf_generator import display_pdf_export_section
from database import db
from monitor_manager import display_monitor_manager, get_monitor_summary
from monitor_service import monitor_service
from notification_service import notification_service
from config_manager import config_manager

# 页面配置
st.set_page_config(
    page_title="复合多AI智能体股票团队分析系统",
    page_icon="📈",
    layout="wide",
    initial_sidebar_state="expanded"
)

# 模型选择器
def model_selector():
    """模型选择器"""
    st.sidebar.markdown("---")
    st.sidebar.subheader("🤖 AI模型选择")
    
    model_options = {
        "deepseek-chat": "DeepSeek Chat (默认)",
        "deepseek-reasoner": "DeepSeek Reasoner (推理增强)"
    }
    
    selected_model = st.sidebar.selectbox(
        "选择AI模型",
        options=list(model_options.keys()),
        format_func=lambda x: model_options[x],
        help="DeepSeek Reasoner提供更强的推理能力，但响应时间可能更长"
    )
    
    return selected_model

# 自定义CSS样式 - 专业版
st.markdown("""
<style>
    /* 全局样式 */
    .main {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        background-attachment: fixed;
    }
    
    .stApp {
        background: transparent;
    }
    
    /* 主容器 */
    .block-container {
        padding-top: 2rem;
        padding-bottom: 2rem;
        background: rgba(255, 255, 255, 0.95);
        border-radius: 20px;
        box-shadow: 0 10px 40px rgba(0, 0, 0, 0.1);
        margin-top: 1rem;
    }
    
    /* 顶部导航栏 */
    .top-nav {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        padding: 1.5rem 2rem;
        border-radius: 15px;
        margin-bottom: 2rem;
        box-shadow: 0 8px 32px rgba(102, 126, 234, 0.3);
    }
    
    .nav-title {
        font-size: 2rem;
        font-weight: 800;
        color: white;
        text-align: center;
        margin: 0;
        text-shadow: 2px 2px 4px rgba(0,0,0,0.2);
        letter-spacing: 1px;
    }
    
    .nav-subtitle {
        text-align: center;
        color: rgba(255, 255, 255, 0.9);
        font-size: 0.95rem;
        margin-top: 0.5rem;
        font-weight: 300;
    }
    
    /* 标签页样式 */
    .stTabs [data-baseweb="tab-list"] {
        gap: 2rem;
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        padding: 1rem 2rem;
        border-radius: 15px;
        box-shadow: 0 4px 15px rgba(102, 126, 234, 0.2);
    }
    
    .stTabs [data-baseweb="tab"] {
        height: 60px;
        background: rgba(255, 255, 255, 0.1);
        border-radius: 10px;
        color: white;
        font-weight: 600;
        font-size: 1.1rem;
        padding: 0 2rem;
        border: none;
        transition: all 0.3s ease;
    }
    
    .stTabs [data-baseweb="tab"]:hover {
        background: rgba(255, 255, 255, 0.2);
        transform: translateY(-2px);
    }
    
    .stTabs [aria-selected="true"] {
        background: white !important;
        color: #667eea !important;
        box-shadow: 0 4px 15px rgba(0, 0, 0, 0.1);
    }
    
    /* 侧边栏美化 */
    .css-1d391kg, [data-testid="stSidebar"] {
        background: linear-gradient(180deg, #667eea 0%, #764ba2 100%);
        padding-top: 2rem;
    }
    
    .css-1d391kg h1, .css-1d391kg h2, .css-1d391kg h3,
    [data-testid="stSidebar"] h1, [data-testid="stSidebar"] h2, [data-testid="stSidebar"] h3 {
        color: white !important;
    }
    
    .css-1d391kg .stMarkdown, [data-testid="stSidebar"] .stMarkdown {
        color: rgba(255, 255, 255, 0.95) !important;
    }
    
    /* 分析师卡片 */
    .agent-card {
        background: linear-gradient(135deg, #f5f7fa 0%, #c3cfe2 100%);
        padding: 1.5rem;
        border-radius: 15px;
        margin: 1rem 0;
        border-left: 5px solid #667eea;
        box-shadow: 0 4px 15px rgba(0, 0, 0, 0.1);
        transition: transform 0.3s ease;
    }
    
    .agent-card:hover {
        transform: translateX(5px);
    }
    
    /* 决策卡片 */
    .decision-card {
        background: linear-gradient(135deg, #e8f5e9 0%, #c8e6c9 100%);
        padding: 2rem;
        border-radius: 15px;
        border: 3px solid #4caf50;
        margin: 1.5rem 0;
        box-shadow: 0 8px 30px rgba(76, 175, 80, 0.2);
    }
    
    /* 警告卡片 */
    .warning-card {
        background: linear-gradient(135deg, #fff3e0 0%, #ffe0b2 100%);
        padding: 1.5rem;
        border-radius: 15px;
        border-left: 5px solid #ff9800;
        box-shadow: 0 4px 15px rgba(255, 152, 0, 0.2);
    }
    
    /* 指标卡片 */
    .metric-card {
        background: white;
        padding: 1.5rem;
        border-radius: 12px;
        box-shadow: 0 4px 20px rgba(0, 0, 0, 0.08);
        text-align: center;
        transition: transform 0.3s ease, box-shadow 0.3s ease;
        border-top: 4px solid #667eea;
    }
    
    .metric-card:hover {
        transform: translateY(-5px);
        box-shadow: 0 8px 30px rgba(0, 0, 0, 0.15);
    }
    
    /* 按钮美化 */
    .stButton>button {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white;
        border: none;
        border-radius: 10px;
        padding: 0.75rem 2rem;
        font-weight: 600;
        font-size: 1rem;
        transition: all 0.3s ease;
        box-shadow: 0 4px 15px rgba(102, 126, 234, 0.3);
    }
    
    .stButton>button:hover {
        transform: translateY(-2px);
        box-shadow: 0 6px 25px rgba(102, 126, 234, 0.4);
    }
    
    /* 输入框美化 */
    .stTextInput>div>div>input {
        border-radius: 10px;
        border: 2px solid #e0e0e0;
        padding: 0.75rem;
        font-size: 1rem;
        transition: border-color 0.3s ease;
    }
    
    .stTextInput>div>div>input:focus {
        border-color: #667eea;
        box-shadow: 0 0 0 3px rgba(102, 126, 234, 0.1);
    }
    
    /* 进度条美化 */
    .stProgress > div > div > div > div {
        background: linear-gradient(90deg, #667eea 0%, #764ba2 100%);
    }
    
    /* 成功/错误/警告/信息消息框 */
    .stSuccess, .stError, .stWarning, .stInfo {
        border-radius: 10px;
        padding: 1rem;
        box-shadow: 0 2px 10px rgba(0, 0, 0, 0.1);
    }
    
    /* 图表容器 */
    .js-plotly-plot {
        border-radius: 15px;
        box-shadow: 0 4px 20px rgba(0, 0, 0, 0.1);
    }
    
    /* Expander美化 */
    .streamlit-expanderHeader {
        background: linear-gradient(135deg, #f5f7fa 0%, #c3cfe2 100%);
        border-radius: 10px;
        font-weight: 600;
    }
    
    /* 数据框美化 */
    .dataframe {
        border-radius: 10px;
        overflow: hidden;
        box-shadow: 0 2px 10px rgba(0, 0, 0, 0.1);
    }
    
    /* 隐藏Streamlit默认元素 */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    
    /* 响应式设计 */
    @media (max-width: 768px) {
        .nav-title {
            font-size: 1.5rem;
        }
        .stTabs [data-baseweb="tab"] {
            font-size: 0.9rem;
            padding: 0 1rem;
        }
    }
</style>
""", unsafe_allow_html=True)

def main():
    # 顶部标题栏
    st.markdown("""
    <div class="top-nav">
        <h1 class="nav-title">📈 复合多AI智能体股票团队分析系统</h1>
        <p class="nav-subtitle">基于DeepSeek的专业量化投资分析平台 | Multi-Agent Stock Analysis System</p>
    </div>
    """, unsafe_allow_html=True)
    
    # 侧边栏
    with st.sidebar:
        # 快捷导航 - 移到顶部
        st.markdown("### 🔍 快捷导航")
        
        if st.button("📖 历史记录", use_container_width=True, key="nav_history"):
            st.session_state.show_history = True
            if 'show_monitor' in st.session_state:
                del st.session_state.show_monitor
        
        if st.button("📊 实时监测", use_container_width=True, key="nav_monitor"):
            st.session_state.show_monitor = True
            if 'show_history' in st.session_state:
                del st.session_state.show_history
        
        if st.button("🏠 返回首页", use_container_width=True, key="nav_home"):
            if 'show_history' in st.session_state:
                del st.session_state.show_history
            if 'show_monitor' in st.session_state:
                del st.session_state.show_monitor
            if 'show_config' in st.session_state:
                del st.session_state.show_config
        
        if st.button("⚙️ 环境配置", use_container_width=True, key="nav_config"):
            st.session_state.show_config = True
            if 'show_history' in st.session_state:
                del st.session_state.show_history
            if 'show_monitor' in st.session_state:
                del st.session_state.show_monitor
        
        st.markdown("---")
        
        # 系统配置
        st.markdown("### ⚙️ 系统配置")
        
        # API密钥检查
        api_key_status = check_api_key()
        if api_key_status:
            st.success("✅ API已连接")
        else:
            st.error("❌ API未配置")
            st.caption("请在.env中配置API密钥")
            
        st.markdown("---")
        
        # 模型选择器
        selected_model = model_selector()
        st.session_state.selected_model = selected_model
        
        st.markdown("---")
        
        # 系统状态面板
        st.markdown("### 📊 系统状态")
        
        monitor_status = "🟢 运行中" if monitor_service.running else "🔴 已停止"
        st.markdown(f"**监测服务**: {monitor_status}")
        
        try:
            from monitor_db import monitor_db
            stocks = monitor_db.get_monitored_stocks()
            notifications = monitor_db.get_pending_notifications()
            record_count = db.get_record_count()
            
            st.markdown(f"**分析记录**: {record_count}条")
            st.markdown(f"**监测股票**: {len(stocks)}只")
            st.markdown(f"**待处理**: {len(notifications)}条")
        except:
            pass
        
        st.markdown("---")
        
        # 分析参数设置
        st.markdown("### 📊 分析参数")
        period = st.selectbox(
            "数据周期",
            ["1y", "6mo", "3mo", "1mo"],
            index=0,
            help="选择历史数据的时间范围"
        )
        
        st.markdown("---")
        
        # 帮助信息
        with st.expander("💡 使用帮助"):
            st.markdown("""
            **股票代码格式**
            - 🇨🇳 A股：6位数字（如600519）
            - 🇺🇸 美股：字母代码（如AAPL）
            
            **功能说明**
            - **智能分析**：AI团队深度分析
            - **实时监测**：价格监控与提醒
            - **历史记录**：查看分析历史
            
            **AI分析流程**
            1. 数据获取 → 2. 技术分析
            3. 基本面分析 → 4. 资金分析
            5. 情绪数据(ARBR) → 6. 新闻公告
            7. AI团队分析 → 8. 团队讨论 → 9. 决策
            """)
    
    # 检查是否显示历史记录
    if 'show_history' in st.session_state and st.session_state.show_history:
        display_history_records()
        return
    
    # 检查是否显示监测面板
    if 'show_monitor' in st.session_state and st.session_state.show_monitor:
        display_monitor_manager()
        return
    
    # 检查是否显示环境配置
    if 'show_config' in st.session_state and st.session_state.show_config:
        display_config_manager()
        return
    
    # 主界面
    col1, col2, col3 = st.columns([2, 1, 1])
    
    with col1:
        stock_input = st.text_input(
            "🔍 请输入股票代码或名称", 
            placeholder="例如: AAPL, 000001, 600036",
            help="支持美股代码(如AAPL)和A股代码(如000001)"
        )
    
    with col2:
        analyze_button = st.button("🚀 开始分析", type="primary", use_container_width=True)
    
    with col3:
        if st.button("🔄 清除缓存", use_container_width=True):
            st.cache_data.clear()
            st.success("缓存已清除")
    
    # 分析师团队选择
    st.markdown("---")
    st.subheader("👥 选择分析师团队")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        enable_technical = st.checkbox("📊 技术分析师", value=True, 
                                       help="负责技术指标分析、图表形态识别、趋势判断")
        enable_fundamental = st.checkbox("💼 基本面分析师", value=True,
                                        help="负责公司财务分析、行业研究、估值分析")
    
    with col2:
        enable_fund_flow = st.checkbox("💰 资金面分析师", value=True,
                                      help="负责资金流向分析、主力行为研究")
        enable_risk = st.checkbox("⚠️ 风险管理师", value=True,
                                 help="负责风险识别、风险评估、风险控制策略制定")
    
    with col3:
        enable_sentiment = st.checkbox("📈 市场情绪分析师", value=False,
                                      help="负责市场情绪研究、ARBR指标分析（仅A股）")
        enable_news = st.checkbox("📰 新闻公告分析师", value=False,
                                 help="负责新闻事件分析、公司公告解读（仅A股）")
    
    # 显示已选择的分析师
    selected_analysts = []
    if enable_technical:
        selected_analysts.append("技术分析师")
    if enable_fundamental:
        selected_analysts.append("基本面分析师")
    if enable_fund_flow:
        selected_analysts.append("资金面分析师")
    if enable_risk:
        selected_analysts.append("风险管理师")
    if enable_sentiment:
        selected_analysts.append("市场情绪分析师")
    if enable_news:
        selected_analysts.append("新闻公告分析师")
    
    if selected_analysts:
        st.info(f"✅ 已选择 {len(selected_analysts)} 位分析师: {', '.join(selected_analysts)}")
    else:
        st.warning("⚠️ 请至少选择一位分析师")
    
    # 保存选择到session_state
    st.session_state.enable_technical = enable_technical
    st.session_state.enable_fundamental = enable_fundamental
    st.session_state.enable_fund_flow = enable_fund_flow
    st.session_state.enable_risk = enable_risk
    st.session_state.enable_sentiment = enable_sentiment
    st.session_state.enable_news = enable_news
    
    st.markdown("---")
    
    if analyze_button and stock_input:
        if not api_key_status:
            st.error("❌ 请先配置 DeepSeek API Key")
            return
        
        # 检查是否至少选择了一位分析师
        if not selected_analysts:
            st.error("❌ 请至少选择一位分析师参与分析")
            return
        
        # 清除之前的分析结果
        if 'analysis_completed' in st.session_state:
            del st.session_state.analysis_completed
        if 'stock_info' in st.session_state:
            del st.session_state.stock_info
        if 'agents_results' in st.session_state:
            del st.session_state.agents_results
        if 'discussion_result' in st.session_state:
            del st.session_state.discussion_result
        if 'final_decision' in st.session_state:
            del st.session_state.final_decision
            
        run_stock_analysis(stock_input, period)
    
    # 检查是否有已完成的分析结果
    if 'analysis_completed' in st.session_state and st.session_state.analysis_completed:
        # 重新显示分析结果
        stock_info = st.session_state.stock_info
        agents_results = st.session_state.agents_results
        discussion_result = st.session_state.discussion_result
        final_decision = st.session_state.final_decision
        
        # 重新获取股票数据用于显示图表
        stock_info_current, stock_data, indicators = get_stock_data(stock_info['symbol'], period)
        
        # 显示股票基本信息
        display_stock_info(stock_info, indicators)
        
        # 显示股票图表
        if stock_data is not None:
            display_stock_chart(stock_data, stock_info)
        
        # 显示各分析师报告
        display_agents_analysis(agents_results)
        
        # 显示团队讨论
        display_team_discussion(discussion_result)
        
        # 显示最终决策
        display_final_decision(final_decision, stock_info, agents_results, discussion_result)
    
    # 示例和说明
    elif not stock_input:
        show_example_interface()

def check_api_key():
    """检查API密钥是否配置"""
    try:
        import config
        return bool(config.DEEPSEEK_API_KEY and config.DEEPSEEK_API_KEY.strip())
    except:
        return False

@st.cache_data(ttl=300)  # 缓存5分钟
def get_stock_data(symbol, period):
    """获取股票数据（带缓存）"""
    fetcher = StockDataFetcher()
    stock_info = fetcher.get_stock_info(symbol)
    stock_data = fetcher.get_stock_data(symbol, period)
    
    if isinstance(stock_data, dict) and "error" in stock_data:
        return stock_info, None, None
    
    stock_data_with_indicators = fetcher.calculate_technical_indicators(stock_data)
    indicators = fetcher.get_latest_indicators(stock_data_with_indicators)
    
    return stock_info, stock_data_with_indicators, indicators

def run_stock_analysis(symbol, period):
    """运行股票分析"""
    
    # 进度条
    progress_bar = st.progress(0)
    status_text = st.empty()
    
    try:
        # 1. 获取股票数据
        status_text.text("📈 正在获取股票数据...")
        progress_bar.progress(10)
        
        stock_info, stock_data, indicators = get_stock_data(symbol, period)
        
        if "error" in stock_info:
            st.error(f"❌ {stock_info['error']}")
            return
        
        if stock_data is None:
            st.error("❌ 无法获取股票历史数据")
            return
        
        # 显示股票基本信息
        display_stock_info(stock_info, indicators)
        progress_bar.progress(20)
        
        # 显示股票图表
        display_stock_chart(stock_data, stock_info)
        progress_bar.progress(30)
        
        # 2. 获取财务数据
        status_text.text("📊 正在获取财务数据...")
        fetcher = StockDataFetcher()  # 创建fetcher实例
        financial_data = fetcher.get_financial_data(symbol)
        progress_bar.progress(35)
        
        # 获取分析师选择状态
        enable_fund_flow = st.session_state.get('enable_fund_flow', True)
        enable_sentiment = st.session_state.get('enable_sentiment', False)
        enable_news = st.session_state.get('enable_news', False)
        
        # 3. 获取资金流向数据（仅在选择了资金面分析师时）
        fund_flow_data = None
        if enable_fund_flow and fetcher._is_chinese_stock(symbol):
            status_text.text("💰 正在获取资金流向数据（主力）...")
            try:
                fund_flow_data = fetcher.get_fund_flow_data(symbol)
                if fund_flow_data and fund_flow_data.get('query_success'):
                    st.info("✅ 成功获取主力资金流向数据")
                else:
                    st.warning("⚠️ 未能获取主力资金流向数据，将基于技术指标进行资金面分析")
            except Exception as e:
                st.warning(f"⚠️ 获取资金流向数据时出错: {str(e)}")
                fund_flow_data = None
        elif enable_fund_flow and not fetcher._is_chinese_stock(symbol):
            st.info("ℹ️ 美股暂不支持资金流向数据")
        progress_bar.progress(40)
        
        # 4. 获取市场情绪数据（仅在选择了市场情绪分析师时）
        sentiment_data = None
        if enable_sentiment and fetcher._is_chinese_stock(symbol):
            status_text.text("📊 正在获取市场情绪数据（ARBR等指标）...")
            try:
                from market_sentiment_data import MarketSentimentDataFetcher
                sentiment_fetcher = MarketSentimentDataFetcher()
                sentiment_data = sentiment_fetcher.get_market_sentiment_data(symbol, stock_data)
                if sentiment_data and sentiment_data.get('data_success'):
                    st.info("✅ 成功获取市场情绪数据（ARBR、换手率、涨跌停等）")
                else:
                    st.warning("⚠️ 未能获取完整的市场情绪数据，将基于基本信息进行分析")
            except Exception as e:
                st.warning(f"⚠️ 获取市场情绪数据时出错: {str(e)}")
                sentiment_data = None
        elif enable_sentiment and not fetcher._is_chinese_stock(symbol):
            st.info("ℹ️ 美股暂不支持市场情绪数据（ARBR等指标）")
        progress_bar.progress(45)
        
        # 5. 获取新闻公告数据（仅在选择了新闻公告分析师时）
        news_announcement_data = None
        if enable_news and fetcher._is_chinese_stock(symbol):
            status_text.text("📰 正在获取新闻公告数据（问财）...")
            try:
                from news_announcement_data import NewsAnnouncementDataFetcher
                news_fetcher = NewsAnnouncementDataFetcher()
                news_announcement_data = news_fetcher.get_news_and_announcements(symbol)
                if news_announcement_data and news_announcement_data.get('data_success'):
                    news_count = news_announcement_data.get('news_data', {}).get('count', 0) if news_announcement_data.get('news_data') else 0
                    announcement_count = news_announcement_data.get('announcement_data', {}).get('count', 0) if news_announcement_data.get('announcement_data') else 0
                    st.info(f"✅ 成功获取 {news_count} 条新闻，{announcement_count} 条公告")
                else:
                    st.warning("⚠️ 未能获取新闻公告数据，将基于基本信息进行分析")
            except Exception as e:
                st.warning(f"⚠️ 获取新闻公告数据时出错: {str(e)}")
                news_announcement_data = None
        elif enable_news and not fetcher._is_chinese_stock(symbol):
            st.info("ℹ️ 美股暂不支持新闻公告数据")
        progress_bar.progress(50)
        
        # 6. 初始化AI分析系统
        status_text.text("🤖 正在初始化AI分析系统...")
        # 使用选择的模型
        selected_model = st.session_state.get('selected_model', 'deepseek-chat')
        agents = StockAnalysisAgents(model=selected_model)
        progress_bar.progress(55)
        
        # 获取所有分析师选择状态
        enable_technical = st.session_state.get('enable_technical', True)
        enable_fundamental = st.session_state.get('enable_fundamental', True)
        enable_risk = st.session_state.get('enable_risk', True)
        
        # 创建分析师启用字典
        enabled_analysts = {
            'technical': enable_technical,
            'fundamental': enable_fundamental,
            'fund_flow': enable_fund_flow,
            'risk': enable_risk,
            'sentiment': enable_sentiment,
            'news': enable_news
        }
        
        # 7. 运行多智能体分析（传入所有数据和分析师选择）
        status_text.text("🔍 AI分析师团队正在分析,请耐心等待几分钟...")
        agents_results = agents.run_multi_agent_analysis(
            stock_info, stock_data, indicators, financial_data, 
            fund_flow_data, sentiment_data, news_announcement_data,
            enabled_analysts=enabled_analysts
        )
        progress_bar.progress(75)
        
        # 显示各分析师报告
        display_agents_analysis(agents_results)
        
        # 8. 团队讨论
        status_text.text("🤝 分析团队正在讨论...")
        discussion_result = agents.conduct_team_discussion(agents_results, stock_info)
        progress_bar.progress(88)
        
        # 显示团队讨论
        display_team_discussion(discussion_result)
        
        # 9. 最终决策
        status_text.text("📋 正在制定最终投资决策...")
        final_decision = agents.make_final_decision(discussion_result, stock_info, indicators)
        progress_bar.progress(100)
        
        # 保存分析结果到session_state
        st.session_state.analysis_completed = True
        st.session_state.stock_info = stock_info
        st.session_state.agents_results = agents_results
        st.session_state.discussion_result = discussion_result
        st.session_state.final_decision = final_decision
        
        # 保存到数据库
        try:
            db.save_analysis(
                symbol=stock_info.get('symbol', ''),
                stock_name=stock_info.get('name', ''),
                period=period,
                stock_info=stock_info,
                agents_results=agents_results,
                discussion_result=discussion_result,
                final_decision=final_decision
            )
            st.success("✅ 分析记录已保存到数据库")
        except Exception as e:
            st.warning(f"⚠️ 保存到数据库时出现错误: {str(e)}")
        
        # 显示最终决策
        display_final_decision(final_decision, stock_info, agents_results, discussion_result)
        
        status_text.text("✅ 分析完成！")
        time.sleep(1)
        status_text.empty()
        progress_bar.empty()
        
    except Exception as e:
        st.error(f"❌ 分析过程中出现错误: {str(e)}")
        progress_bar.empty()
        status_text.empty()

def display_stock_info(stock_info, indicators):
    """显示股票基本信息"""
    st.subheader(f"📊 {stock_info.get('name', 'N/A')} ({stock_info.get('symbol', 'N/A')})")
    
    # 基本信息卡片
    col1, col2, col3, col4, col5 = st.columns(5)
    
    with col1:
        current_price = stock_info.get('current_price', 'N/A')
        st.metric("当前价格", f"{current_price}")
    
    with col2:
        change_percent = stock_info.get('change_percent', 'N/A')
        if isinstance(change_percent, (int, float)):
            st.metric("涨跌幅", f"{change_percent:.2f}%", f"{change_percent:.2f}%")
        else:
            st.metric("涨跌幅", f"{change_percent}")
    
    with col3:
        pe_ratio = stock_info.get('pe_ratio', 'N/A')
        st.metric("市盈率", f"{pe_ratio}")
    
    with col4:
        pb_ratio = stock_info.get('pb_ratio', 'N/A')
        st.metric("市净率", f"{pb_ratio}")
    
    with col5:
        market_cap = stock_info.get('market_cap', 'N/A')
        if isinstance(market_cap, (int, float)):
            market_cap_str = f"{market_cap/1e9:.2f}B" if market_cap > 1e9 else f"{market_cap/1e6:.2f}M"
            st.metric("市值", market_cap_str)
        else:
            st.metric("市值", f"{market_cap}")
    
    # 技术指标
    if indicators and not isinstance(indicators, dict) or "error" not in indicators:
        st.subheader("📈 关键技术指标")
        
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            rsi = indicators.get('rsi', 'N/A')
            if isinstance(rsi, (int, float)):
                rsi_color = "normal"
                if rsi > 70:
                    rsi_color = "inverse"
                elif rsi < 30:
                    rsi_color = "off"
                st.metric("RSI", f"{rsi:.2f}")
            else:
                st.metric("RSI", f"{rsi}")
        
        with col2:
            ma20 = indicators.get('ma20', 'N/A')
            if isinstance(ma20, (int, float)):
                st.metric("MA20", f"{ma20:.2f}")
            else:
                st.metric("MA20", f"{ma20}")
        
        with col3:
            volume_ratio = indicators.get('volume_ratio', 'N/A')
            if isinstance(volume_ratio, (int, float)):
                st.metric("量比", f"{volume_ratio:.2f}")
            else:
                st.metric("量比", f"{volume_ratio}")
        
        with col4:
            macd = indicators.get('macd', 'N/A')
            if isinstance(macd, (int, float)):
                st.metric("MACD", f"{macd:.4f}")
            else:
                st.metric("MACD", f"{macd}")

def display_stock_chart(stock_data, stock_info):
    """显示股票图表"""
    st.subheader("📈 股价走势图")
    
    # 创建蜡烛图
    fig = go.Figure()
    
    # 添加蜡烛图
    fig.add_trace(go.Candlestick(
        x=stock_data.index,
        open=stock_data['Open'],
        high=stock_data['High'],
        low=stock_data['Low'],
        close=stock_data['Close'],
        name="K线"
    ))
    
    # 添加移动平均线
    if 'MA5' in stock_data.columns:
        fig.add_trace(go.Scatter(
            x=stock_data.index,
            y=stock_data['MA5'],
            name="MA5",
            line=dict(color='orange', width=1)
        ))
    
    if 'MA20' in stock_data.columns:
        fig.add_trace(go.Scatter(
            x=stock_data.index,
            y=stock_data['MA20'],
            name="MA20",
            line=dict(color='blue', width=1)
        ))
    
    if 'MA60' in stock_data.columns:
        fig.add_trace(go.Scatter(
            x=stock_data.index,
            y=stock_data['MA60'],
            name="MA60",
            line=dict(color='purple', width=1)
        ))
    
    # 布林带
    if 'BB_upper' in stock_data.columns and 'BB_lower' in stock_data.columns:
        fig.add_trace(go.Scatter(
            x=stock_data.index,
            y=stock_data['BB_upper'],
            name="布林上轨",
            line=dict(color='red', width=1, dash='dash')
        ))
        fig.add_trace(go.Scatter(
            x=stock_data.index,
            y=stock_data['BB_lower'],
            name="布林下轨",
            line=dict(color='green', width=1, dash='dash'),
            fill='tonexty',
            fillcolor='rgba(0,100,80,0.1)'
        ))
    
    fig.update_layout(
        title=f"{stock_info.get('name', 'N/A')} 股价走势",
        xaxis_title="日期",
        yaxis_title="价格",
        height=500,
        showlegend=True
    )
    
    # 生成唯一的key
    chart_key = f"main_stock_chart_{stock_info.get('symbol', 'unknown')}_{int(time.time())}"
    st.plotly_chart(fig, use_container_width=True, key=chart_key)
    
    # 成交量图
    if 'Volume' in stock_data.columns:
        fig_volume = go.Figure()
        fig_volume.add_trace(go.Bar(
            x=stock_data.index,
            y=stock_data['Volume'],
            name="成交量",
            marker_color='lightblue'
        ))
        
        fig_volume.update_layout(
            title="成交量",
            xaxis_title="日期",
            yaxis_title="成交量",
            height=200
        )
        
        # 生成唯一的key
        volume_key = f"volume_chart_{stock_info.get('symbol', 'unknown')}_{int(time.time())}"
        st.plotly_chart(fig_volume, use_container_width=True, key=volume_key)

def display_agents_analysis(agents_results):
    """显示各分析师报告"""
    st.subheader("🤖 AI分析师团队报告")
    
    # 创建标签页
    tab_names = []
    tab_contents = []
    
    for agent_key, agent_result in agents_results.items():
        agent_name = agent_result.get('agent_name', '未知分析师')
        tab_names.append(agent_name)
        tab_contents.append(agent_result)
    
    tabs = st.tabs(tab_names)
    
    for i, tab in enumerate(tabs):
        with tab:
            agent_result = tab_contents[i]
            
            # 分析师信息
            st.markdown(f"""
            <div class="agent-card">
                <h4>👨‍💼 {agent_result.get('agent_name', '未知')}</h4>
                <p><strong>职责：</strong>{agent_result.get('agent_role', '未知')}</p>
                <p><strong>关注领域：</strong>{', '.join(agent_result.get('focus_areas', []))}</p>
                <p><strong>分析时间：</strong>{agent_result.get('timestamp', '未知')}</p>
            </div>
            """, unsafe_allow_html=True)
            
            # 分析报告
            st.markdown("**📄 分析报告:**")
            st.write(agent_result.get('analysis', '暂无分析'))

def display_team_discussion(discussion_result):
    """显示团队讨论"""
    st.subheader("🤝 分析团队讨论")
    
    st.markdown("""
    <div class="agent-card">
        <h4>💭 团队综合讨论</h4>
        <p>各位分析师正在就该股票进行深入讨论，整合不同维度的分析观点...</p>
    </div>
    """, unsafe_allow_html=True)
    
    st.write(discussion_result)

def display_final_decision(final_decision, stock_info, agents_results=None, discussion_result=None):
    """显示最终投资决策"""
    st.subheader("📋 最终投资决策")
    
    if isinstance(final_decision, dict) and "decision_text" not in final_decision:
        # JSON格式的决策
        col1, col2 = st.columns([1, 2])
        
        with col1:
            # 投资评级
            rating = final_decision.get('rating', '未知')
            rating_color = {"买入": "🟢", "持有": "🟡", "卖出": "🔴"}.get(rating, "⚪")
            
            st.markdown(f"""
            <div class="decision-card">
                <h3 style="text-align: center;">{rating_color} {rating}</h3>
                <h4 style="text-align: center;">投资评级</h4>
            </div>
            """, unsafe_allow_html=True)
            
            # 关键指标
            confidence = final_decision.get('confidence_level', 'N/A')
            st.metric("信心度", f"{confidence}/10")
            
            target_price = final_decision.get('target_price', 'N/A')
            st.metric("目标价格", f"{target_price}")
            
            position_size = final_decision.get('position_size', 'N/A')
            st.metric("建议仓位", f"{position_size}")
        
        with col2:
            # 详细建议
            st.markdown("**🎯 操作建议:**")
            st.write(final_decision.get('operation_advice', '暂无建议'))
            
            st.markdown("**📍 关键位置:**")
            col2_1, col2_2 = st.columns(2)
            
            with col2_1:
                st.write(f"**进场区间:** {final_decision.get('entry_range', 'N/A')}")
                st.write(f"**止盈位:** {final_decision.get('take_profit', 'N/A')}")
            
            with col2_2:
                st.write(f"**止损位:** {final_decision.get('stop_loss', 'N/A')}")
                st.write(f"**持有周期:** {final_decision.get('holding_period', 'N/A')}")
        
        # 风险提示
        risk_warning = final_decision.get('risk_warning', '')
        if risk_warning:
            st.markdown(f"""
            <div class="warning-card">
                <h4>⚠️ 风险提示</h4>
                <p>{risk_warning}</p>
            </div>
            """, unsafe_allow_html=True)
    
    else:
        # 文本格式的决策
        decision_text = final_decision.get('decision_text', str(final_decision))
        st.write(decision_text)
    
    # 添加PDF导出功能
    st.markdown("---")
    if agents_results and discussion_result:
        display_pdf_export_section(stock_info, agents_results, discussion_result, final_decision)
    else:
        st.warning("⚠️ PDF导出功能需要完整的分析数据")

def show_example_interface():
    """显示示例界面"""
    st.subheader("💡 使用说明")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("""
        ### 🚀 如何使用
        1. **输入股票代码**：支持美股(如AAPL、MSFT)和A股(如000001、600036)
        2. **点击开始分析**：系统将启动AI分析师团队
        3. **查看分析报告**：5位专业分析师将从不同角度分析
        4. **获得投资建议**：获得最终的投资评级和操作建议
        
        ### 📊 分析维度
        - **技术面**：趋势、指标、支撑阻力
        - **基本面**：财务、估值、行业分析
        - **资金面**：资金流向、主力行为
        - **风险管理**：风险识别与控制
        - **市场情绪**：情绪指标、热点分析
        """)
    
    with col2:
        st.markdown("""
        ### 📈 示例股票代码
        
        **美股热门**
        - AAPL (苹果)
        - MSFT (微软)
        - GOOGL (谷歌)
        - TSLA (特斯拉)
        - NVDA (英伟达)
        
        **A股热门**
        - 000001 (平安银行)
        - 600036 (招商银行)
        - 000002 (万科A)
        - 600519 (贵州茅台)
        - 000858 (五粮液)
        """)
    
    st.info("💡 提示：首次运行需要配置DeepSeek API Key，请在.env中设置DEEPSEEK_API_KEY")

def display_history_records():
    """显示历史分析记录"""
    st.subheader("📚 历史分析记录")
    
    # 获取所有记录
    records = db.get_all_records()
    
    if not records:
        st.info("📭 暂无历史分析记录")
        return
    
    st.write(f"📊 共找到 {len(records)} 条分析记录")
    
    # 搜索和筛选
    col1, col2 = st.columns([3, 1])
    with col1:
        search_term = st.text_input("🔍 搜索股票代码或名称", placeholder="输入股票代码或名称进行搜索")
    with col2:
        st.write("")
        st.write("")
        if st.button("🔄 刷新列表"):
            st.rerun()
    
    # 筛选记录
    filtered_records = records
    if search_term:
        filtered_records = [
            record for record in records 
            if search_term.lower() in record['symbol'].lower() or 
               search_term.lower() in record['stock_name'].lower()
        ]
    
    if not filtered_records:
        st.warning("🔍 未找到匹配的记录")
        return
    
    # 显示记录列表
    for record in filtered_records:
        # 根据评级设置颜色和图标
        rating = record.get('rating', '未知')
        rating_color = {
            "买入": "🟢",
            "持有": "🟡", 
            "卖出": "🔴",
            "强烈买入": "🟢",
            "强烈卖出": "🔴"
        }.get(rating, "⚪")
        
        with st.expander(f"{rating_color} {record['stock_name']} ({record['symbol']}) - {record['analysis_date']}"):
            col1, col2, col3, col4 = st.columns([2, 2, 1, 1])
            
            with col1:
                st.write(f"**股票代码:** {record['symbol']}")
                st.write(f"**股票名称:** {record['stock_name']}")
            
            with col2:
                st.write(f"**分析时间:** {record['analysis_date']}")
                st.write(f"**数据周期:** {record['period']}")
                st.write(f"**投资评级:** **{rating}**")
            
            with col3:
                if st.button("👀 查看详情", key=f"view_{record['id']}"):
                    st.session_state.viewing_record_id = record['id']
            
            with col4:
                if st.button("➕ 监测", key=f"add_monitor_{record['id']}"):
                    st.session_state.add_to_monitor_id = record['id']
                    st.session_state.viewing_record_id = record['id']
            
            # 删除按钮（新增一行）
            col5, _, _, _ = st.columns(4)
            with col5:
                if st.button("🗑️ 删除", key=f"delete_{record['id']}"):
                    if db.delete_record(record['id']):
                        st.success("✅ 记录已删除")
                        st.rerun()
                    else:
                        st.error("❌ 删除失败")
    
    # 查看详细记录
    if 'viewing_record_id' in st.session_state:
        display_record_detail(st.session_state.viewing_record_id)

def display_add_to_monitor_dialog(record):
    """显示加入监测的对话框"""
    st.markdown("---")
    st.subheader("➕ 加入监测")
    
    final_decision = record['final_decision']
    
    # 从final_decision中提取关键数据
    if isinstance(final_decision, dict):
        # 解析进场区间
        entry_range_str = final_decision.get('entry_range', 'N/A')
        entry_min = 0.0
        entry_max = 0.0
        
        # 尝试解析进场区间字符串，支持多种格式
        if entry_range_str and entry_range_str != 'N/A':
            try:
                import re
                # 移除常见的前缀和单位
                clean_str = str(entry_range_str).replace('¥', '').replace('元', '').replace('$', '')
                # 使用正则表达式提取数字
                # 支持格式：10.5-12.0, 10.5 - 12.0, 10.5~12.0, 10.5至12.0 等
                numbers = re.findall(r'\d+\.?\d*', clean_str)
                if len(numbers) >= 2:
                    entry_min = float(numbers[0])
                    entry_max = float(numbers[1])
            except:
                # 如果解析失败，尝试用分隔符split
                try:
                    clean_str = str(entry_range_str).replace('¥', '').replace('元', '').replace('$', '')
                    # 尝试多种分隔符
                    for sep in ['-', '~', '至', '到']:
                        if sep in clean_str:
                            parts = clean_str.split(sep)
                            if len(parts) == 2:
                                entry_min = float(parts[0].strip())
                                entry_max = float(parts[1].strip())
                                break
                except:
                    pass
        
        # 提取止盈和止损
        take_profit_str = final_decision.get('take_profit', 'N/A')
        stop_loss_str = final_decision.get('stop_loss', 'N/A')
        
        take_profit = 0.0
        stop_loss = 0.0
        
        # 解析止盈位
        if take_profit_str and take_profit_str != 'N/A':
            try:
                import re
                # 移除单位和符号
                clean_str = str(take_profit_str).replace('¥', '').replace('元', '').replace('$', '').strip()
                # 提取第一个数字
                numbers = re.findall(r'\d+\.?\d*', clean_str)
                if numbers:
                    take_profit = float(numbers[0])
            except:
                pass
        
        # 解析止损位
        if stop_loss_str and stop_loss_str != 'N/A':
            try:
                import re
                # 移除单位和符号
                clean_str = str(stop_loss_str).replace('¥', '').replace('元', '').replace('$', '').strip()
                # 提取第一个数字
                numbers = re.findall(r'\d+\.?\d*', clean_str)
                if numbers:
                    stop_loss = float(numbers[0])
            except:
                pass
        
        # 获取评级
        rating = final_decision.get('rating', '买入')
        
        # 检查是否已经在监测列表中
        from monitor_db import monitor_db
        existing_stocks = monitor_db.get_monitored_stocks()
        is_duplicate = any(stock['symbol'] == record['symbol'] for stock in existing_stocks)
        
        if is_duplicate:
            st.warning(f"⚠️ {record['symbol']} 已经在监测列表中。继续添加将创建重复监测项。")
        
        st.info(f"""
        **从分析结果中提取的数据：**
        - 进场区间: {entry_min} - {entry_max}
        - 止盈位: {take_profit if take_profit > 0 else '未设置'}
        - 止损位: {stop_loss if stop_loss > 0 else '未设置'}
        - 投资评级: {rating}
        """)
        
        # 显示表单供用户确认或修改
        with st.form(key=f"monitor_form_{record['id']}"):
            st.markdown("**请确认或修改监测参数：**")
            
            col1, col2 = st.columns([1, 1])
            
            with col1:
                st.subheader("🎯 关键位置")
                new_entry_min = st.number_input("进场区间最低价", value=float(entry_min), step=0.01, format="%.2f")
                new_entry_max = st.number_input("进场区间最高价", value=float(entry_max), step=0.01, format="%.2f")
                new_take_profit = st.number_input("止盈价位", value=float(take_profit), step=0.01, format="%.2f")
                new_stop_loss = st.number_input("止损价位", value=float(stop_loss), step=0.01, format="%.2f")
            
            with col2:
                st.subheader("⚙️ 监测设置")
                check_interval = st.slider("监测间隔(分钟)", 5, 120, 30)
                notification_enabled = st.checkbox("启用通知", value=True)
                new_rating = st.selectbox("投资评级", ["买入", "持有", "卖出"], 
                                         index=["买入", "持有", "卖出"].index(rating) if rating in ["买入", "持有", "卖出"] else 0)
            
            col_a, col_b, col_c = st.columns(3)
            
            with col_a:
                submit = st.form_submit_button("✅ 确认加入监测", type="primary", use_container_width=True)
            
            with col_b:
                cancel = st.form_submit_button("❌ 取消", use_container_width=True)
            
            if submit:
                if new_entry_min > 0 and new_entry_max > 0 and new_entry_max > new_entry_min:
                    try:
                        # 添加到监测数据库
                        entry_range = {"min": new_entry_min, "max": new_entry_max}
                        
                        stock_id = monitor_db.add_monitored_stock(
                            symbol=record['symbol'],
                            name=record['stock_name'],
                            rating=new_rating,
                            entry_range=entry_range,
                            take_profit=new_take_profit if new_take_profit > 0 else None,
                            stop_loss=new_stop_loss if new_stop_loss > 0 else None,
                            check_interval=check_interval,
                            notification_enabled=notification_enabled
                        )
                        
                        st.success(f"✅ 已成功将 {record['symbol']} 加入监测列表！")
                        st.balloons()
                        
                        # 立即更新一次价格
                        from monitor_service import monitor_service
                        monitor_service.manual_update_stock(stock_id)
                        
                        # 清理session state并跳转到监测页面
                        if 'add_to_monitor_id' in st.session_state:
                            del st.session_state.add_to_monitor_id
                        if 'viewing_record_id' in st.session_state:
                            del st.session_state.viewing_record_id
                        if 'show_history' in st.session_state:
                            del st.session_state.show_history
                        
                        # 设置跳转到监测页面
                        st.session_state.show_monitor = True
                        st.session_state.monitor_jump_highlight = record['symbol']  # 标记要高亮显示的股票
                        
                        time.sleep(1.5)
                        st.rerun()
                        
                    except Exception as e:
                        st.error(f"❌ 加入监测失败: {str(e)}")
                else:
                    st.error("❌ 请输入有效的进场区间（最低价应小于最高价，且都大于0）")
            
            if cancel:
                if 'add_to_monitor_id' in st.session_state:
                    del st.session_state.add_to_monitor_id
                st.rerun()
    else:
        st.warning("⚠️ 无法从分析结果中提取关键数据")
        if st.button("❌ 取消"):
            if 'add_to_monitor_id' in st.session_state:
                del st.session_state.add_to_monitor_id
            st.rerun()

def display_record_detail(record_id):
    """显示单条记录的详细信息"""
    st.markdown("---")
    st.subheader("📋 详细分析记录")
    
    record = db.get_record_by_id(record_id)
    if not record:
        st.error("❌ 记录不存在")
        return
    
    # 基本信息
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("股票代码", record['symbol'])
    with col2:
        st.metric("股票名称", record['stock_name'])
    with col3:
        st.metric("分析时间", record['analysis_date'])
    
    # 股票基本信息
    st.subheader("📊 股票基本信息")
    stock_info = record['stock_info']
    if stock_info:
        col1, col2, col3, col4, col5 = st.columns(5)
        
        with col1:
            current_price = stock_info.get('current_price', 'N/A')
            st.metric("当前价格", f"{current_price}")
        
        with col2:
            change_percent = stock_info.get('change_percent', 'N/A')
            if isinstance(change_percent, (int, float)):
                st.metric("涨跌幅", f"{change_percent:.2f}%", f"{change_percent:.2f}%")
            else:
                st.metric("涨跌幅", f"{change_percent}")
        
        with col3:
            pe_ratio = stock_info.get('pe_ratio', 'N/A')
            st.metric("市盈率", f"{pe_ratio}")
        
        with col4:
            pb_ratio = stock_info.get('pb_ratio', 'N/A')
            st.metric("市净率", f"{pb_ratio}")
        
        with col5:
            market_cap = stock_info.get('market_cap', 'N/A')
            if isinstance(market_cap, (int, float)):
                market_cap_str = f"{market_cap/1e9:.2f}B" if market_cap > 1e9 else f"{market_cap/1e6:.2f}M"
                st.metric("市值", market_cap_str)
            else:
                st.metric("市值", f"{market_cap}")
    
    # 各分析师报告
    st.subheader("🤖 AI分析师团队报告")
    agents_results = record['agents_results']
    if agents_results:
        tab_names = []
        tab_contents = []
        
        for agent_key, agent_result in agents_results.items():
            agent_name = agent_result.get('agent_name', '未知分析师')
            tab_names.append(agent_name)
            tab_contents.append(agent_result)
        
        tabs = st.tabs(tab_names)
        
        for i, tab in enumerate(tabs):
            with tab:
                agent_result = tab_contents[i]
                
                st.markdown(f"""
                <div class="agent-card">
                    <h4>👨‍💼 {agent_result.get('agent_name', '未知')}</h4>
                    <p><strong>职责：</strong>{agent_result.get('agent_role', '未知')}</p>
                    <p><strong>关注领域：</strong>{', '.join(agent_result.get('focus_areas', []))}</p>
                </div>
                """, unsafe_allow_html=True)
                
                st.markdown("**📄 分析报告:**")
                st.write(agent_result.get('analysis', '暂无分析'))
    
    # 团队讨论
    st.subheader("🤝 分析团队讨论")
    discussion_result = record['discussion_result']
    if discussion_result:
        st.markdown("""
        <div class="agent-card">
            <h4>💭 团队综合讨论</h4>
        </div>
        """, unsafe_allow_html=True)
        st.write(discussion_result)
    
    # 最终决策
    st.subheader("📋 最终投资决策")
    final_decision = record['final_decision']
    if final_decision:
        if isinstance(final_decision, dict) and "decision_text" not in final_decision:
            col1, col2 = st.columns([1, 2])
            
            with col1:
                rating = final_decision.get('rating', '未知')
                rating_color = {"买入": "🟢", "持有": "🟡", "卖出": "🔴"}.get(rating, "⚪")
                
                st.markdown(f"""
                <div class="decision-card">
                    <h3 style="text-align: center;">{rating_color} {rating}</h3>
                    <h4 style="text-align: center;">投资评级</h4>
                </div>
                """, unsafe_allow_html=True)
                
                confidence = final_decision.get('confidence_level', 'N/A')
                st.metric("信心度", f"{confidence}/10")
                
                target_price = final_decision.get('target_price', 'N/A')
                st.metric("目标价格", f"{target_price}")
                
                position_size = final_decision.get('position_size', 'N/A')
                st.metric("建议仓位", f"{position_size}")
            
            with col2:
                st.markdown("**🎯 操作建议:**")
                st.write(final_decision.get('operation_advice', '暂无建议'))
                
                st.markdown("**📍 关键位置:**")
                col2_1, col2_2 = st.columns(2)
                
                with col2_1:
                    st.write(f"**进场区间:** {final_decision.get('entry_range', 'N/A')}")
                    st.write(f"**止盈位:** {final_decision.get('take_profit', 'N/A')}")
                
                with col2_2:
                    st.write(f"**止损位:** {final_decision.get('stop_loss', 'N/A')}")
                    st.write(f"**持有周期:** {final_decision.get('holding_period', 'N/A')}")
        else:
            decision_text = final_decision.get('decision_text', str(final_decision))
            st.write(decision_text)
    
    # 加入监测功能
    st.markdown("---")
    st.subheader("🎯 操作")
    
    # 检查是否需要显示加入监测的对话框
    if 'add_to_monitor_id' in st.session_state and st.session_state.add_to_monitor_id == record_id:
        display_add_to_monitor_dialog(record)
    else:
        # 只有在不显示对话框时才显示按钮
        col1, col2 = st.columns([1, 3])
        
        with col1:
            if st.button("➕ 加入监测", type="primary", use_container_width=True):
                st.session_state.add_to_monitor_id = record_id
                st.rerun()
    
    # 返回按钮
    st.markdown("---")
    if st.button("⬅️ 返回历史记录列表"):
        if 'viewing_record_id' in st.session_state:
            del st.session_state.viewing_record_id
        if 'add_to_monitor_id' in st.session_state:
            del st.session_state.add_to_monitor_id
        st.rerun()

def display_config_manager():
    """显示环境配置管理界面"""
    st.subheader("⚙️ 环境配置管理")
    
    st.markdown("""
    <div class="agent-card">
        <p>在这里可以配置系统的环境变量，包括API密钥、数据源配置、量化交易配置等。</p>
        <p><strong>注意：</strong>配置修改后需要重启应用才能生效。</p>
    </div>
    """, unsafe_allow_html=True)
    
    # 获取当前配置
    config_info = config_manager.get_config_info()
    
    # 创建标签页
    tab1, tab2, tab3 = st.tabs(["📝 基本配置", "📊 数据源配置", "🤖 量化交易配置"])
    
    # 使用session_state保存临时配置
    if 'temp_config' not in st.session_state:
        st.session_state.temp_config = {key: info["value"] for key, info in config_info.items()}
    
    with tab1:
        st.markdown("### DeepSeek API配置")
        st.markdown("DeepSeek是系统的核心AI引擎，必须配置才能使用分析功能。")
        
        # DeepSeek API Key
        api_key_info = config_info["DEEPSEEK_API_KEY"]
        current_api_key = st.session_state.temp_config.get("DEEPSEEK_API_KEY", "")
        
        new_api_key = st.text_input(
            f"🔑 {api_key_info['description']} {'*' if api_key_info['required'] else ''}",
            value=current_api_key,
            type="password",
            help="从 https://platform.deepseek.com 获取API密钥",
            key="input_deepseek_api_key"
        )
        st.session_state.temp_config["DEEPSEEK_API_KEY"] = new_api_key
        
        # 显示当前状态
        if new_api_key:
            masked_key = new_api_key[:8] + "*" * (len(new_api_key) - 12) + new_api_key[-4:] if len(new_api_key) > 12 else "***"
            st.success(f"✅ API密钥已设置: {masked_key}")
        else:
            st.warning("⚠️ 未设置API密钥，系统无法使用AI分析功能")
        
        st.markdown("---")
        
        # DeepSeek Base URL
        base_url_info = config_info["DEEPSEEK_BASE_URL"]
        current_base_url = st.session_state.temp_config.get("DEEPSEEK_BASE_URL", "")
        
        new_base_url = st.text_input(
            f"🌐 {base_url_info['description']}",
            value=current_base_url,
            help="一般无需修改，保持默认即可",
            key="input_deepseek_base_url"
        )
        st.session_state.temp_config["DEEPSEEK_BASE_URL"] = new_base_url
        
        st.info("💡 如何获取DeepSeek API密钥？\n\n1. 访问 https://platform.deepseek.com\n2. 注册/登录账号\n3. 进入API密钥管理页面\n4. 创建新的API密钥\n5. 复制密钥并粘贴到上方输入框")
    
    with tab2:
        st.markdown("### Tushare数据接口（可选）")
        st.markdown("Tushare提供更丰富的A股财务数据，配置后可以获取更详细的财务分析。")
        
        tushare_info = config_info["TUSHARE_TOKEN"]
        current_tushare = st.session_state.temp_config.get("TUSHARE_TOKEN", "")
        
        new_tushare = st.text_input(
            f"🎫 {tushare_info['description']}",
            value=current_tushare,
            type="password",
            help="从 https://tushare.pro 获取Token",
            key="input_tushare_token"
        )
        st.session_state.temp_config["TUSHARE_TOKEN"] = new_tushare
        
        if new_tushare:
            st.success("✅ Tushare Token已设置")
        else:
            st.info("ℹ️ 未设置Tushare Token，系统将使用其他数据源")
        
        st.info("💡 如何获取Tushare Token？\n\n1. 访问 https://tushare.pro\n2. 注册账号\n3. 进入个人中心\n4. 获取Token\n5. 复制并粘贴到上方输入框")
    
    with tab3:
        st.markdown("### MiniQMT量化交易配置（可选）")
        st.markdown("配置后可以使用量化交易功能，自动执行交易策略。")
        
        # 启用开关
        miniqmt_enabled_info = config_info["MINIQMT_ENABLED"]
        current_enabled = st.session_state.temp_config.get("MINIQMT_ENABLED", "false") == "true"
        
        new_enabled = st.checkbox(
            "启用MiniQMT量化交易",
            value=current_enabled,
            help="开启后可以使用量化交易功能",
            key="input_miniqmt_enabled"
        )
        st.session_state.temp_config["MINIQMT_ENABLED"] = "true" if new_enabled else "false"
        
        # 其他配置
        col1, col2 = st.columns(2)
        
        with col1:
            account_id_info = config_info["MINIQMT_ACCOUNT_ID"]
            current_account_id = st.session_state.temp_config.get("MINIQMT_ACCOUNT_ID", "")
            
            new_account_id = st.text_input(
                f"🆔 {account_id_info['description']}",
                value=current_account_id,
                disabled=not new_enabled,
                key="input_miniqmt_account_id"
            )
            st.session_state.temp_config["MINIQMT_ACCOUNT_ID"] = new_account_id
            
            host_info = config_info["MINIQMT_HOST"]
            current_host = st.session_state.temp_config.get("MINIQMT_HOST", "")
            
            new_host = st.text_input(
                f"🖥️ {host_info['description']}",
                value=current_host,
                disabled=not new_enabled,
                key="input_miniqmt_host"
            )
            st.session_state.temp_config["MINIQMT_HOST"] = new_host
        
        with col2:
            port_info = config_info["MINIQMT_PORT"]
            current_port = st.session_state.temp_config.get("MINIQMT_PORT", "")
            
            new_port = st.text_input(
                f"🔌 {port_info['description']}",
                value=current_port,
                disabled=not new_enabled,
                key="input_miniqmt_port"
            )
            st.session_state.temp_config["MINIQMT_PORT"] = new_port
        
        if new_enabled:
            st.success("✅ MiniQMT已启用")
        else:
            st.info("ℹ️ MiniQMT未启用")
        
        st.warning("⚠️ 警告：量化交易涉及真实资金操作，请谨慎配置和使用！")
    
    # 操作按钮
    st.markdown("---")
    col1, col2, col3, col4 = st.columns([1, 1, 1, 2])
    
    with col1:
        if st.button("💾 保存配置", type="primary", use_container_width=True):
            # 验证配置
            is_valid, message = config_manager.validate_config(st.session_state.temp_config)
            
            if is_valid:
                # 保存配置
                if config_manager.write_env(st.session_state.temp_config):
                    st.success("✅ 配置已保存到 .env 文件")
                    st.info("ℹ️ 请重启应用使配置生效")
                    
                    # 尝试重新加载配置
                    try:
                        config_manager.reload_config()
                        st.success("✅ 配置已重新加载")
                    except Exception as e:
                        st.warning(f"⚠️ 配置重新加载失败: {e}")
                    
                    time.sleep(2)
                    st.rerun()
                else:
                    st.error("❌ 保存配置失败")
            else:
                st.error(f"❌ 配置验证失败: {message}")
    
    with col2:
        if st.button("🔄 重置", use_container_width=True):
            # 重置为当前文件中的值
            st.session_state.temp_config = {key: info["value"] for key, info in config_info.items()}
            st.success("✅ 已重置为当前配置")
            st.rerun()
    
    with col3:
        if st.button("⬅️ 返回", use_container_width=True):
            if 'show_config' in st.session_state:
                del st.session_state.show_config
            if 'temp_config' in st.session_state:
                del st.session_state.temp_config
            st.rerun()
    
    # 显示当前.env文件内容
    st.markdown("---")
    with st.expander("📄 查看当前 .env 文件内容"):
        current_config = config_manager.read_env()
        
        st.code(f"""# AI股票分析系统环境配置
# 由系统自动生成和管理

# ========== DeepSeek API配置 ==========
DEEPSEEK_API_KEY="{current_config.get('DEEPSEEK_API_KEY', '')}"
DEEPSEEK_BASE_URL="{current_config.get('DEEPSEEK_BASE_URL', '')}"

# ========== Tushare数据接口（可选）==========
TUSHARE_TOKEN="{current_config.get('TUSHARE_TOKEN', '')}"

# ========== MiniQMT量化交易配置（可选）==========
MINIQMT_ENABLED="{current_config.get('MINIQMT_ENABLED', 'false')}"
MINIQMT_ACCOUNT_ID="{current_config.get('MINIQMT_ACCOUNT_ID', '')}"
MINIQMT_HOST="{current_config.get('MINIQMT_HOST', '127.0.0.1')}"
MINIQMT_PORT="{current_config.get('MINIQMT_PORT', '58610')}"
""", language="bash")

if __name__ == "__main__":
    main()