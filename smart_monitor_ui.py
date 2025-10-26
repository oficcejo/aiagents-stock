"""
智能盯盘 - UI界面
集成到主程序的智能盯盘功能界面
"""

import streamlit as st
import pandas as pd
from datetime import datetime
import logging
import os
from typing import Dict
from dotenv import load_dotenv

from smart_monitor_engine import SmartMonitorEngine
from smart_monitor_db import SmartMonitorDB
from config_manager import config_manager  # 使用主程序的配置管理器


# 加载环境变量
load_dotenv()


def smart_monitor_ui():
    """AI盯盘主界面"""
    
    st.title("🤖 AI盯盘 - AI决策交易系统")
    st.caption("参照AlphaArena项目，基于DeepSeek AI的A股自动化交易系统")
    
    # 使用说明
    with st.expander("📖 快速使用指南", expanded=False):
        st.markdown("""
        ### 🚀 快速开始
        
        **第一步：环境配置**
        1. 点击左侧菜单"⚙️ 环境配置"
        2. 填写 DeepSeek API Key（必需）
        3. 配置 miniQMT 账户（可选，用于实盘交易）
        4. 配置通知方式（可选，邮件/Webhook）
        
        **第二步：开始使用**
        - **实时分析**：输入股票代码，AI即时分析并给出交易建议
        - **监控任务**：添加股票到监控列表，定时自动分析
        - **持仓管理**：查看和管理当前持仓（已持仓股票可直接监控）
        
        ---
        
        ### 💡 核心功能
        
        | 功能 | 说明 |
        |------|------|
        | 📊 **实时分析** | 输入股票代码，AI分析市场数据并给出买入/卖出/持有建议 |
        | 🎯 **监控任务** | 定时自动分析目标股票，可设置自动交易 |
        | 📈 **持仓管理** | 记录持仓成本，实时显示盈亏，AI决策考虑持仓情况 |
        | 📜 **历史记录** | 查看所有AI决策历史、交易记录和通知记录 |
        | ⚙️ **系统设置** | 配置API、交易方式（实盘/模拟）、通知等 |
        
        ---
        
        ### 🎯 AI决策逻辑
        
        **买入信号**（至少满足3个）：
        1. ✅ 趋势向上：价格 > MA5 > MA20 > MA60（多头排列）
        2. ✅ 量价配合：成交量 > 5日均量的120%（放量上涨）
        3. ✅ MACD金叉：MACD > 0 且DIF上穿DEA
        4. ✅ RSI健康：RSI在50-70区间（不超买不超卖）
        5. ✅ 突破关键位：突破前期高点或重要阻力位
        6. ✅ 布林带位置：价格接近布林中轨上方，有上行空间
        
        **卖出信号**（满足任一立即卖出）：
        1. 🔴 止损触发：亏损 ≥ -5%（明天开盘立即卖出）
        2. 🟢 止盈触发：盈利 ≥ +10%（锁定收益）
        3. 🔴 趋势转弱：跌破MA20/MA60，MACD死叉
        4. 🔴 放量下跌：成交量放大但价格下跌
        5. 🔴 技术破位：跌破重要支撑位
        
        ---
        
        ### ⚠️ A股T+1规则
        
        **关键限制**：
        - 今天买入的股票，**今天不能卖出**
        - 必须等到下一个交易日才能卖出
        - 系统会自动检查并遵守T+1规则
        
        **建议**：
        - **宁可错过，不可做错** - 买入前务必确认趋势
        - 单只股票仓位 ≤ 30%（T+1风险较大）
        - 止损位：-5%（明天开盘立即执行）
        - 止盈位：+8-15%（分批止盈）
        
        ---
        
        ### 🔧 使用技巧
        
        **新手建议**：
        1. 先使用"模拟交易"模式测试
        2. 小仓位试水（建议5-10%）
        3. 严格执行止损，不要心存侥幸
        4. 关注交易时段（9:30-11:30, 13:00-15:00）
        
        **高级功能**：
        - 在"监控任务"中勾选"已持仓"，填入成本价
        - AI会考虑当前盈亏情况给出更准确的建议
        - 可设置多个监控任务，同时盯盘多只股票
        
        ---
        
        ### 📞 常见问题
        
        **Q: 提示"DeepSeek API调用失败"？**
        - 检查API Key是否正确
        - 确认API账户余额充足
        - 检查网络连接
        
        **Q: 数据显示为0或获取失败？**
        - 可能是非交易时间
        - AKShare接口可能暂时不可用
        - 尝试更换股票代码测试
        
        **Q: 想实盘交易如何操作？**
        1. 下载并安装 [miniQMT](https://www.xtp-mini.com/)
        2. 启动miniQMT客户端并登录
        3. 在"系统设置"中填写账户ID
        4. 取消勾选"使用模拟交易"
        
        ---
        
        ### ⚠️ 风险提示
        
        1. **股市有风险，投资需谨慎**
        2. AI决策仅供参考，不构成投资建议
        3. 建议先使用模拟交易充分测试
        4. 严格控制仓位，不要满仓操作
        5. 不要投入超过承受能力的资金
        
        ---
        
        **🎉 祝您交易顺利！如有问题，请查看详细文档或联系技术支持。**
        """)
    
    st.markdown("---")
    
    # 初始化组件（自动从配置读取）
    if 'engine' not in st.session_state:
        try:
            # SmartMonitorEngine会自动从config_manager读取配置
            st.session_state.engine = SmartMonitorEngine()
            st.session_state.db = SmartMonitorDB()
        except Exception as e:
            st.error(f"初始化失败: {e}")
            st.error("请先在'环境配置'中完成基础配置")
            return
    
    # 创建标签页
    tabs = st.tabs([
        "📊 实时分析", 
        "🎯 监控任务", 
        "📈 持仓管理", 
        "📜 历史记录",
        "⚙️ 系统设置"
    ])
    
    # 标签页1: 实时分析
    with tabs[0]:
        render_realtime_analysis()
    
    # 标签页2: 监控任务
    with tabs[1]:
        render_monitor_tasks()
    
    # 标签页3: 持仓管理
    with tabs[2]:
        render_position_management()
    
    # 标签页4: 历史记录
    with tabs[3]:
        render_history()
    
    # 标签页5: 系统设置
    with tabs[4]:
        render_settings()


def render_realtime_analysis():
    """实时分析界面"""
    
    st.header("📊 实时分析")
    
    col1, col2 = st.columns([2, 1])
    
    with col1:
        stock_code = st.text_input(
            "输入股票代码",
            placeholder="例如: 600519",
            help="输入6位股票代码"
        )
    
    with col2:
        auto_trade = st.checkbox("自动交易", value=False, 
                                help="开启后AI会自动执行交易决策")
    
    if st.button("🔍 开始分析", type="primary"):
        if not stock_code:
            st.error("请输入股票代码")
            return
        
        if len(stock_code) != 6 or not stock_code.isdigit():
            st.error("股票代码格式错误，请输入6位数字")
            return
        
        # 显示进度
        with st.spinner('正在分析...'):
            engine = st.session_state.engine
            result = engine.analyze_stock(
                stock_code=stock_code,
                auto_trade=auto_trade,
                notify=True
            )
        
        if result['success']:
            # 显示分析结果
            display_analysis_result(result)
        else:
            st.error(f"分析失败: {result.get('error')}")


def display_analysis_result(result: dict):
    """显示分析结果"""
    
    stock_code = result['stock_code']
    stock_name = result['stock_name']
    decision = result['decision']
    market_data = result['market_data']
    session_info = result['session_info']
    
    st.success(f"✅ 分析完成: {stock_code} {stock_name}")
    
    # 交易时段信息
    st.info(f"⏰ 当前时段: {session_info['session']} - {session_info['recommendation']}")
    
    # AI决策
    st.markdown("### 🤖 AI决策")
    
    col1, col2, col3, col4 = st.columns(4)
    
    # 决策动作
    action = decision['action']
    action_emoji = {"BUY": "📈", "SELL": "📉", "HOLD": "⏸️"}
    action_color = {"BUY": "green", "SELL": "red", "HOLD": "gray"}
    
    col1.metric("决策", action, delta=None)
    col2.metric("信心度", f"{decision['confidence']}%")
    col3.metric("风险等级", decision.get('risk_level', 'N/A'))
    col4.metric("建议仓位", f"{decision.get('position_size_pct', 0)}%")
    
    # 决策理由
    st.markdown("**决策理由:**")
    st.text_area("决策理由", decision['reasoning'], height=150, disabled=True, label_visibility="hidden")
    
    # 市场数据
    st.markdown("### 📊 市场数据")
    
    col1, col2, col3, col4 = st.columns(4)
    col1.metric("当前价", f"¥{market_data.get('current_price', 0):.2f}")
    col2.metric("涨跌幅", f"{market_data.get('change_pct', 0):+.2f}%")
    col3.metric("成交量", f"{market_data.get('volume', 0):,.0f}手")
    col4.metric("换手率", f"{market_data.get('turnover_rate', 0):.2f}%")
    
    # 技术指标
    st.markdown("### 📈 技术指标")
    
    tech_col1, tech_col2, tech_col3 = st.columns(3)
    
    with tech_col1:
        st.markdown("**均线系统**")
        st.write(f"MA5: ¥{market_data.get('ma5', 0):.2f}")
        st.write(f"MA20: ¥{market_data.get('ma20', 0):.2f}")
        st.write(f"MA60: ¥{market_data.get('ma60', 0):.2f}")
        st.write(f"趋势: {market_data.get('trend', 'N/A')}")
    
    with tech_col2:
        st.markdown("**动量指标**")
        st.write(f"MACD: {market_data.get('macd', 0):.4f}")
        st.write(f"DIF: {market_data.get('macd_dif', 0):.4f}")
        st.write(f"DEA: {market_data.get('macd_dea', 0):.4f}")
    
    with tech_col3:
        st.markdown("**摆动指标**")
        st.write(f"RSI(6): {market_data.get('rsi6', 0):.2f}")
        st.write(f"RSI(12): {market_data.get('rsi12', 0):.2f}")
        st.write(f"RSI(24): {market_data.get('rsi24', 0):.2f}")
    
    # 主力资金（已禁用 - 接口不稳定）
    # if 'main_force' in market_data:
    #     st.markdown("### 💰 主力资金")
    #     mf = market_data['main_force']
    #     
    #     mf_col1, mf_col2, mf_col3 = st.columns(3)
    #     mf_col1.metric("主力净额", f"{mf['main_net']:,.2f}万", 
    #                   delta=f"{mf['main_net_pct']:+.2f}%")
    #     mf_col2.metric("超大单", f"{mf['super_net']:,.2f}万")
    #     mf_col3.metric("大单", f"{mf['big_net']:,.2f}万")
    #     
    #     st.info(f"主力动向: {mf['trend']}")
    
    # 执行结果（如果有）
    if result.get('execution_result'):
        exec_result = result['execution_result']
        st.markdown("### ⚡ 执行结果")
        
        if exec_result.get('success'):
            st.success(f"✅ {exec_result.get('message', '执行成功')}")
        else:
            st.error(f"❌ {exec_result.get('error', '执行失败')}")


def render_monitor_tasks():
    """监控任务界面"""
    
    st.header("🎯 监控任务管理")
    
    db = st.session_state.db
    engine = st.session_state.engine
    
    # 添加新任务
    with st.expander("➕ 添加新监控任务", expanded=True):
        # 改回使用form，确保值正确提交
        with st.form("add_monitor_task_form", clear_on_submit=False):
            col1, col2 = st.columns(2)
            
            with col1:
                task_name = st.text_input("任务名称", placeholder="例如: 茅台盯盘")
                stock_code = st.text_input("股票代码", placeholder="例如: 600519")
                check_interval = st.slider("检查间隔(秒)", 60, 3600, 300)
                
                # 持仓信息
                st.markdown("---")
                st.markdown("**📊 持仓信息**")
                has_position = st.checkbox("已持仓该股票", value=False,
                                          help="勾选后可填写持仓成本和数量，AI会考虑持仓情况")
                
                # 注意：在form内部，复选框的变化要到提交后才能看到
                # 所以持仓输入框始终显示，用户可以选择填写或不填写
                position_cost = st.number_input("持仓成本(元)", min_value=0.01, value=10.0, step=0.01,
                                               help="如果已持仓，填写买入时的成本价格（未持仓可忽略）")
                position_quantity = st.number_input("持仓数量(股)", min_value=100, value=100, step=100,
                                                   help="如果已持仓，填写持有的股票数量（未持仓可忽略）")
            
            with col2:
                auto_trade = st.checkbox("自动交易", value=False,
                                        help="AI决策后自动执行交易")
                position_size = st.slider("仓位百分比(%)", 5, 50, 20,
                                         help="新建仓位时使用的资金比例")
                notify_email = st.text_input("通知邮箱（可选）")
            
            # 添加任务按钮（表单提交按钮）
            submitted = st.form_submit_button("➕ 添加任务", type="primary", use_container_width=True)
        
        if submitted:
            # 验证必填项（form中直接使用局部变量）
            if not task_name or not stock_code:
                st.error("❌ 请填写必填项：任务名称和股票代码")
            else:
                
                try:
                    # 检查是否已存在该股票的监控任务
                    existing_tasks = db.get_monitor_tasks(enabled_only=False)
                    existing_task = next((t for t in existing_tasks if t['stock_code'] == stock_code), None)
                    
                    if existing_task:
                        st.error(f"❌ 股票代码 {stock_code} 已存在监控任务！")
                        st.warning(f"任务名称: {existing_task['task_name']}")
                        st.info("💡 请在下方任务列表中找到该任务，点击启动或删除后重新添加")
                    else:
                        # 创建任务（初始状态为禁用，需要用户手动启动）
                        task_data = {
                            'task_name': task_name,
                            'stock_code': stock_code,
                            'enabled': 0,  # 关键修改：初始状态为禁用，不自动启动
                            'check_interval': check_interval,
                            'auto_trade': 1 if auto_trade else 0,
                            'position_size_pct': position_size,
                            'notify_email': notify_email,
                            'has_position': 1 if has_position else 0,
                            'position_cost': position_cost if has_position else 0,
                            'position_quantity': position_quantity if has_position else 0,
                            'position_date': datetime.now().strftime('%Y-%m-%d') if has_position else None
                        }
                        
                        task_id = db.add_monitor_task(task_data)
                        
                        st.success(f"✅ 任务创建成功! ID: {task_id}")
                        if has_position:
                            st.info(f"📊 已记录持仓: {position_quantity}股 @ {position_cost:.2f}元")
                        st.info("💡 任务已创建但未启动，请在下方任务列表中点击'▶️ 启动'按钮开始监控")
                        
                        st.rerun()
                except Exception as e:
                    error_msg = str(e)
                    if "UNIQUE constraint failed" in error_msg:
                        st.error(f"❌ 股票代码 {stock_code} 已存在监控任务！")
                        st.info("💡 请在下方任务列表中找到该任务")
                    else:
                        st.error(f"创建失败: {error_msg}")
    
    # 显示任务列表
    st.markdown("### 📋 监控任务列表")
    
    tasks = db.get_monitor_tasks(enabled_only=False)
    
    if not tasks:
        st.info("暂无监控任务，点击上方'添加新监控任务'创建")
        return
    
    for task in tasks:
        with st.container():
            # 获取实时价格计算盈亏
            has_position = task.get('has_position', 0)
            position_cost = task.get('position_cost', 0)
            position_quantity = task.get('position_quantity', 0)
            
            # 尝试获取当前价格
            current_price = 0
            profit_loss = 0
            profit_loss_pct = 0
            
            if has_position and position_cost > 0 and position_quantity > 0:
                try:
                    # 获取实时行情
                    from smart_monitor_data import SmartMonitorDataFetcher
                    data_fetcher = SmartMonitorDataFetcher()
                    quote = data_fetcher.get_realtime_quote(task['stock_code'], retry=1)
                    if quote:
                        current_price = quote.get('current_price', 0)
                        if current_price > 0:
                            # 计算盈亏
                            cost_total = position_cost * position_quantity
                            current_total = current_price * position_quantity
                            profit_loss = current_total - cost_total
                            profit_loss_pct = (profit_loss / cost_total) * 100
                except Exception as e:
                    pass
            
            col1, col2, col3, col4, col5 = st.columns([2, 2, 1.5, 1, 1])
            
            with col1:
                st.write(f"**{task['task_name']}**")
                st.caption(f"{task['stock_code']} - 间隔{task['check_interval']}秒")
            
            with col2:
                status = "✅ 已启用" if task['enabled'] else "⏸️ 已禁用"
                auto_trade_status = "🤖 自动交易" if task['auto_trade'] else "👀 仅监控"
                st.write(status)
                st.caption(auto_trade_status)
                
                # 显示持仓状态
                if has_position:
                    st.caption(f"📊 持仓: {position_quantity}股 @ {position_cost:.2f}元")
            
            with col3:
                is_running = task['stock_code'] in engine.monitoring_threads
                if is_running:
                    st.success("▶️ 运行中")
                else:
                    st.info("⏸️ 未运行")
                
                # 显示盈亏
                if has_position and current_price > 0:
                    if profit_loss > 0:
                        st.success(f"💰 +{profit_loss:.2f}元 ({profit_loss_pct:+.2f}%)")
                    elif profit_loss < 0:
                        st.error(f"📉 {profit_loss:.2f}元 ({profit_loss_pct:+.2f}%)")
                    else:
                        st.info("持平")
            
            with col4:
                if is_running:
                    if st.button("⏹️ 停止", key=f"stop_{task['id']}"):
                        engine.stop_monitor(task['stock_code'])
                        # 停止时更新数据库状态为禁用
                        db.update_monitor_task(task['stock_code'], {'enabled': 0})
                        st.success("已停止")
                        st.rerun()
                else:
                    # 启动按钮始终可点击（只要任务未运行）
                    if st.button("▶️ 启动", key=f"start_{task['id']}"):
                        # 启动监控
                        engine.start_monitor(
                            stock_code=task['stock_code'],
                            check_interval=task['check_interval'],
                            auto_trade=task['auto_trade'] == 1,
                            notify=True,
                            has_position=has_position == 1,
                            position_cost=position_cost,
                            position_quantity=position_quantity
                        )
                        # 启动时更新数据库状态为启用
                        db.update_monitor_task(task['stock_code'], {'enabled': 1})
                        st.success("已启动")
                        st.rerun()
            
            with col5:
                if st.button("🗑️ 删除", key=f"del_{task['id']}"):
                    # 如果正在运行，先停止
                    if task['stock_code'] in engine.monitoring_threads:
                        engine.stop_monitor(task['stock_code'])
                    
                    db.delete_monitor_task(task['id'])
                    st.success("已删除")
                    st.rerun()
            
            # K线图和AI决策详情（可展开）
            with st.expander(f"📊 K线图 & AI决策 - {task['task_name']}", expanded=False):
                _render_task_kline_and_decisions(task, db, engine)
            
            st.markdown("---")


def render_position_management():
    """持仓管理界面"""
    
    st.header("📈 持仓管理")
    
    engine = st.session_state.engine
    qmt = engine.qmt
    
    # 获取账户信息
    account_info = qmt.get_account_info()
    
    st.markdown("### 💰 账户概览")
    
    col1, col2, col3, col4 = st.columns(4)
    col1.metric("总资产", f"¥{account_info['total_value']:,.2f}")
    col2.metric("可用资金", f"¥{account_info['available_cash']:,.2f}")
    col3.metric("持仓数量", f"{account_info['positions_count']}个")
    col4.metric("总盈亏", f"¥{account_info['total_profit_loss']:,.2f}")
    
    # 获取持仓列表
    positions = qmt.get_all_positions()
    
    if not positions:
        st.info("当前无持仓")
        return
    
    st.markdown("### 📊 持仓列表")
    
    # 转换为DataFrame
    df = pd.DataFrame(positions)
    
    # 显示表格
    st.dataframe(
        df[[
            'stock_code', 'stock_name', 'quantity', 'can_sell',
            'cost_price', 'current_price', 'profit_loss', 'profit_loss_pct'
        ]],
        column_config={
            "stock_code": "代码",
            "stock_name": "名称",
            "quantity": "持仓",
            "can_sell": "可卖",
            "cost_price": "成本价",
            "current_price": "现价",
            "profit_loss": "盈亏",
            "profit_loss_pct": "盈亏%"
        },
        hide_index=True,
        use_container_width=True
    )
    
    # 单只股票操作
    st.markdown("### ⚡ 快速操作")
    
    selected_stock = st.selectbox(
        "选择股票",
        options=[f"{p['stock_code']} {p['stock_name']}" for p in positions]
    )
    
    col1, col2 = st.columns(2)
    
    with col1:
        if st.button("🔍 AI分析", type="secondary"):
            stock_code = selected_stock.split()[0]
            with st.spinner("分析中..."):
                result = engine.analyze_stock(stock_code, auto_trade=False)
                if result['success']:
                    st.success("分析完成，查看'实时分析'标签页")
    
    with col2:
        if st.button("📤 卖出", type="primary"):
            stock_code = selected_stock.split()[0]
            # 这里可以添加卖出确认对话框
            st.warning("请在'实时分析'中使用AI决策后卖出")


def render_history():
    """历史记录界面"""
    
    st.header("📜 历史记录")
    
    db = st.session_state.db
    
    tab1, tab2, tab3 = st.tabs(["AI决策历史", "交易记录", "通知记录"])
    
    # AI决策历史
    with tab1:
        st.subheader("🤖 AI决策历史")
        
        decisions = db.get_ai_decisions(limit=50)
        
        if not decisions:
            st.info("暂无决策记录")
        else:
            for dec in decisions:
                with st.expander(
                    f"{dec['decision_time']} - {dec['stock_code']} {dec['stock_name']} "
                    f"- {dec['action']} (信心度{dec['confidence']}%)"
                ):
                    col1, col2 = st.columns([1, 3])
                    
                    with col1:
                        st.write(f"**时段:** {dec['trading_session']}")
                        st.write(f"**风险:** {dec['risk_level']}")
                        st.write(f"**仓位:** {dec['position_size_pct']}%")
                    
                    with col2:
                        st.write("**决策理由:**")
                        st.text(dec['reasoning'])
    
    # 交易记录
    with tab2:
        st.subheader("💱 交易记录")
        
        trades = db.get_trade_records(limit=50)
        
        if not trades:
            st.info("暂无交易记录")
        else:
            df = pd.DataFrame(trades)
            st.dataframe(
                df[[
                    'trade_time', 'stock_code', 'stock_name', 'trade_type',
                    'quantity', 'price', 'amount', 'profit_loss'
                ]],
                column_config={
                    "trade_time": "时间",
                    "stock_code": "代码",
                    "stock_name": "名称",
                    "trade_type": "类型",
                    "quantity": "数量",
                    "price": "价格",
                    "amount": "金额",
                    "profit_loss": "盈亏"
                },
                hide_index=True,
                use_container_width=True
            )
    
    # 通知记录
    with tab3:
        st.subheader("📬 通知记录")
        st.info("通知记录功能开发中...")


def render_settings():
    """系统设置界面（跳转到主程序的环境配置）"""
    
    st.header("⚙️ 系统设置")
    
    st.info("""
    ### 📌 配置说明
    
    智能盯盘使用主程序的统一配置系统，包括：
    - 🤖 **DeepSeek API** - AI决策引擎
    - 🔌 **MiniQMT** - 量化交易接口
    - 📧 **邮件通知** - SMTP配置
    - 🔔 **Webhook** - 钉钉/飞书通知
    
    请前往主程序的 **"环境配置"** 页面进行统一配置。
    """)
    
    # 显示当前配置状态
    st.markdown("### 📊 当前配置状态")
    
    config = config_manager.read_env()
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("**🤖 DeepSeek API**")
        api_key = config.get('DEEPSEEK_API_KEY', '')
        if api_key:
            st.success(f"✅ 已配置（{api_key[:8]}...）")
        else:
            st.error("❌ 未配置")
        
        st.markdown("**🔌 MiniQMT**")
        miniqmt_enabled = config.get('MINIQMT_ENABLED', 'false').lower() == 'true'
        if miniqmt_enabled:
            account_id = config.get('MINIQMT_ACCOUNT_ID', '')
            st.success(f"✅ 已启用（账户：{account_id or '未设置'}）")
        else:
            st.warning("⚠️ 未启用（使用模拟交易）")
    
    with col2:
        st.markdown("**📧 邮件通知**")
        email_enabled = config.get('EMAIL_ENABLED', 'false').lower() == 'true'
        if email_enabled:
            email_to = config.get('EMAIL_TO', '')
            st.success(f"✅ 已启用（{email_to}）")
        else:
            st.warning("⚠️ 未启用")
        
        st.markdown("**🔔 Webhook通知**")
        webhook_enabled = config.get('WEBHOOK_ENABLED', 'false').lower() == 'true'
        if webhook_enabled:
            webhook_type = config.get('WEBHOOK_TYPE', 'dingtalk')
            st.success(f"✅ 已启用（{webhook_type}）")
        else:
            st.warning("⚠️ 未启用")
    
    st.markdown("---")
    
    # 快速跳转按钮
    st.markdown("### 🔧 配置管理")
    
    st.info("""
    **配置步骤：**
    1. 点击左侧菜单 → **"环境配置"**
    2. 填写所需的配置项
    3. 点击 **"保存配置"**
    4. 返回智能盯盘页面
    5. 刷新页面使配置生效
    """)
    
    if st.button("🔄 重新加载配置", type="primary"):
        config_manager.reload_config()
        st.success("✅ 配置已重新加载")
        st.info("💡 如果修改了配置，请刷新页面（Ctrl+R）")
        st.rerun()


def _render_task_kline_and_decisions(task: Dict, db: SmartMonitorDB, engine):
    """
    渲染单个任务的K线图和AI决策
    
    Args:
        task: 任务信息
        db: 数据库实例
        engine: 监控引擎实例
    """
    from smart_monitor_kline import SmartMonitorKline
    from smart_monitor_data import SmartMonitorDataFetcher
    
    stock_code = task['stock_code']
    stock_name = task.get('stock_name', stock_code)
    
    # 创建两列：左侧K线图，右侧AI决策列表
    col_chart, col_decisions = st.columns([2, 1])
    
    with col_chart:
        st.markdown("#### 📈 K线图")
        
        # 添加刷新按钮
        if st.button("🔄 刷新K线", key=f"refresh_kline_{task['id']}"):
            st.rerun()
        
        # 获取K线数据
        try:
            kline = SmartMonitorKline()
            data_fetcher = SmartMonitorDataFetcher()
            
            # 获取K线数据（60天）
            with st.spinner(f"正在获取 {stock_code} 的K线数据..."):
                kline_data = kline.get_kline_data(stock_code, days=60, data_fetcher=data_fetcher)
            
            if kline_data is not None and not kline_data.empty:
                # 获取AI决策历史（最近100条，用于K线图标注）
                ai_decisions = db.get_ai_decisions(
                    stock_code=stock_code,
                    limit=100
                )
                
                # 过滤最近30天的决策（用于K线图标注）
                from datetime import timedelta
                if ai_decisions:
                    start_date = (datetime.now() - timedelta(days=30)).strftime('%Y-%m-%d')
                    ai_decisions = [
                        d for d in ai_decisions 
                        if d.get('decision_time', '').split()[0] >= start_date
                    ]
                
                # 创建K线图
                fig = kline.create_kline_with_decisions(
                    stock_code=stock_code,
                    stock_name=stock_name,
                    kline_data=kline_data,
                    ai_decisions=ai_decisions,
                    show_volume=True,
                    show_ma=True,
                    height=500
                )
                
                # 显示图表
                st.plotly_chart(fig, use_container_width=True)
                
                st.caption(f"📅 数据时间范围：{kline_data['日期'].min()} ~ {kline_data['日期'].max()}")
            else:
                st.error(f"❌ 无法获取 {stock_code} 的K线数据")
                
        except Exception as e:
            st.error(f"❌ K线图加载失败: {str(e)}")
            import traceback
            st.text(traceback.format_exc())
    
    with col_decisions:
        st.markdown("#### 🤖 AI决策历史")
        
        # 添加刷新按钮
        if st.button("🔄 刷新决策", key=f"refresh_decisions_{task['id']}"):
            st.rerun()
        
        # 获取最近的AI决策（最近5条）
        try:
            recent_decisions = db.get_ai_decisions(
                stock_code=stock_code,
                limit=5
            )
            
            if recent_decisions:
                for idx, decision in enumerate(recent_decisions):
                    action = decision.get('action', 'unknown')
                    decision_time = decision.get('decision_time', '')
                    confidence = decision.get('confidence', 0)
                    reasoning = decision.get('reasoning', '无')
                    executed = decision.get('executed', 0)
                    
                    # 决策类型图标和颜色
                    action_icons = {
                        'buy': '🔺',
                        'sell': '🔻',
                        'add_position': '⬆️',
                        'reduce_position': '⬇️',
                        'hold': '⏸️'
                    }
                    
                    action_colors = {
                        'buy': '#ef5350',
                        'sell': '#26a69a',
                        'add_position': '#ff9800',
                        'reduce_position': '#9c27b0',
                        'hold': '#607d8b'
                    }
                    
                    action_names = {
                        'buy': '买入',
                        'sell': '卖出',
                        'add_position': '加仓',
                        'reduce_position': '减仓',
                        'hold': '持有'
                    }
                    
                    icon = action_icons.get(action, '❓')
                    color = action_colors.get(action, '#000000')
                    action_name = action_names.get(action, action)
                    
                    # 显示决策卡片
                    with st.container():
                        st.markdown(f"""
                        <div style="border-left: 4px solid {color}; padding-left: 10px; margin-bottom: 10px;">
                            <p style="margin: 0;">
                                <strong>{icon} {action_name}</strong>
                                {'✅' if executed else '⏳'}
                            </p>
                            <p style="margin: 5px 0; font-size: 0.85em; color: gray;">
                                {decision_time}
                            </p>
                            <p style="margin: 5px 0; font-size: 0.9em;">
                                <strong>置信度:</strong> {confidence}%
                            </p>
                            <p style="margin: 5px 0; font-size: 0.9em;">
                                <strong>推理:</strong> {reasoning[:100]}{'...' if len(reasoning) > 100 else ''}
                            </p>
                        </div>
                        """, unsafe_allow_html=True)
                        
                        st.markdown("---")
            else:
                st.info("📭 暂无AI决策记录")
                st.caption("启动监控后，AI会定期分析并记录决策")
                
        except Exception as e:
            st.error(f"❌ 加载决策历史失败: {str(e)}")


if __name__ == '__main__':
    smart_monitor_ui()

