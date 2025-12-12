#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
低价擒牛UI模块
"""

import streamlit as st
import pandas as pd
from datetime import datetime
from low_price_bull_selector import LowPriceBullSelector
from low_price_bull_strategy import LowPriceBullStrategy
from notification_service import notification_service
from low_price_bull_monitor import low_price_bull_monitor
from low_price_bull_service import low_price_bull_service


def display_low_price_bull():
    """显示低价擒牛选股界面"""
    
    # 检查是否显示监控面板
    if st.session_state.get('show_low_price_monitor'):
        from low_price_bull_monitor_ui import display_monitor_panel
        display_monitor_panel()
        
        # 返回按钮
        if st.button("🔙 返回选股", type="secondary"):
            del st.session_state.show_low_price_monitor
            st.rerun()
        return
    
    st.markdown("顶部按钮区")
    col_select, col_monitor = st.columns([3, 1])
    
    with col_select:
        st.markdown("## 🐂 低价擒牛 - 低价高成长股票筛选")
    
    with col_monitor:
        st.write("")  # 占位
        if st.button("📊 策略监控", type="primary", width='content'):
            st.session_state.show_low_price_monitor = True
            st.rerun()
    
    st.markdown("---")
    
    st.markdown("""
    ### 📋 选股策略说明
    
    **筛选条件**：
    - ✅ 股价 < 10元
    - ✅ 净利润增长率 ≥ 100%（净利润同比增长率）
    - ✅ 非ST股票
    - ✅ 非科创板
    - ✅ 非创业板
    - ✅ 深圳A股
    - ✅ 按成交额由小至大排名
    
    **量化交易策略**：
    - 💰 资金量：100万元
    - 📅 持股周期：5天
    - 💼 仓位控制：满仓
    - 📊 个股最大持仓：4成（40%）
    - 🎯 账户最大持股数：4只
    - 🛒 单日最大买入数：2只
    - 📈 买入时机：开盘买入
    - 📉 卖出时机：MA5下穿MA20或持股满5天
    """)
    
    st.markdown("---")
    
    # 参数设置
    col1, col2 = st.columns([2, 1])
    
    with col1:
        top_n = st.slider(
            "筛选数量",
            min_value=3,
            max_value=10,
            value=5,
            step=1,
            help="选择展示的股票数量"
        )
    
    with col2:
        st.info(f"💡 将筛选成交额最小的前{top_n}只股票")
    
    st.markdown("---")
    
    # 开始选股按钮
    if st.button("🚀 开始低价擒牛选股", type="primary", width='content'):
        
        with st.spinner("正在获取数据，请稍候..."):
            # 创建选股器
            selector = LowPriceBullSelector()
            
            # 获取股票
            success, stocks_df, message = selector.get_low_price_stocks(top_n=top_n)
            
            if success and stocks_df is not None:
                # 保存结果
                st.session_state.low_price_bull_stocks = stocks_df
                st.session_state.low_price_bull_selector = selector
                
                st.success(f"✅ {message}")
                
                # 发送钉钉通知
                send_dingtalk_notification(stocks_df, top_n)
                
                st.rerun()
            else:
                st.error(f"❌ {message}")
    
    # 显示选股结果
    if 'low_price_bull_stocks' in st.session_state:
        display_stock_results(
            st.session_state.low_price_bull_stocks,
            st.session_state.get('low_price_bull_selector')
        )


def display_stock_results(stocks_df: pd.DataFrame, selector):
    """显示选股结果"""
    
    st.markdown("---")
    st.markdown("## 📊 选股结果")
    
    # 统计信息
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.metric("筛选数量", f"{len(stocks_df)} 只")
    
    with col2:
        # 智能计算平均净利增长率（过滤无效值）
        growth_col = stocks_df.get('净利润增长率', stocks_df.get('净利润同比增长率', pd.Series([])))
        valid_growth = growth_col[growth_col.notna() & (growth_col != '') & (growth_col != 'N/A')]
        if len(valid_growth) > 0:
            avg_growth = pd.to_numeric(valid_growth, errors='coerce').mean()
            if not pd.isna(avg_growth):
                st.metric("平均净利增长率", f"{avg_growth:.1f}%")
            else:
                st.metric("平均净利增长率", "-")
        else:
            st.metric("平均净利增长率", "-")
    
    with col3:
        # 智能计算平均股价（过滤无效值）
        price_col = stocks_df.get('股价', stocks_df.get('最新价', pd.Series([])))
        valid_price = price_col[price_col.notna() & (price_col != '') & (price_col != 'N/A')]
        if len(valid_price) > 0:
            avg_price = pd.to_numeric(valid_price, errors='coerce').mean()
            if not pd.isna(avg_price):
                st.metric("平均股价", f"{avg_price:.2f} 元")
            else:
                st.metric("平均股价", "-")
        else:
            st.metric("平均股价", "-")
    
    st.markdown("---")
    
    # 显示股票列表
    st.markdown("### 📋 精选股票列表")
    
    for idx, row in stocks_df.iterrows():
        # 获取股票代码和简称
        code = row.get('股票代码', 'N/A')
        name = row.get('股票简称', 'N/A')
        
        # 获取价格信息作为标题补充
        price = row.get('股价', row.get('最新价', None))
        price_str = ''
        if price is not None and not pd.isna(price):
            try:
                price_float = float(price)
                price_str = f" | 价格: {price_float:.2f}元"
            except:
                pass
        
        with st.expander(
            f"【第{idx+1}名】{code} - {name}{price_str}",
            expanded=(idx < 3)
        ):
            display_stock_detail(row)
    
    # 完整数据表格
    st.markdown("---")
    st.markdown("### 📊 完整数据表格")
    
    # 选择关键列显示
    display_cols = ['股票代码', '股票简称']
    
    # 智能匹配列名
    for pattern in ['股价', '最新价']:
        matching = [col for col in stocks_df.columns if pattern in col]
        if matching:
            display_cols.append(matching[0])
            break
    
    for pattern in ['净利润增长率', '净利润同比增长率']:
        matching = [col for col in stocks_df.columns if pattern in col]
        if matching:
            display_cols.append(matching[0])
            break
    
    for pattern in ['成交额']:
        matching = [col for col in stocks_df.columns if pattern in col]
        if matching:
            display_cols.append(matching[0])
            break
    
    for col_name in ['总市值', '市盈率', '市净率', '所属行业']:
        matching = [col for col in stocks_df.columns if col_name in col]
        if matching:
            display_cols.append(matching[0])
    
    # 选择存在的列
    final_cols = [col for col in display_cols if col in stocks_df.columns]
    
    if final_cols:
        st.dataframe(stocks_df[final_cols], width='content', height=400)
        
        # 下载按钮
        csv = stocks_df[final_cols].to_csv(index=False, encoding='utf-8-sig')
        st.download_button(
            label="📥 下载股票列表CSV",
            data=csv,
            file_name=f"low_price_bull_{datetime.now().strftime('%Y%m%d')}.csv",
            mime="text/csv"
        )
    
    # 量化交易模拟
    st.markdown("---")
    display_strategy_simulation(stocks_df, selector)


def display_stock_detail(row: pd.Series):
    """显示单个股票详情"""
    
    def is_valid_value(value):
        """判断值是否有效（非None、非NaN、非空字符串、非'N/A'）"""
        if value is None:
            return False
        if pd.isna(value):
            return False
        if str(value).strip() in ['', 'N/A', 'nan', 'None']:
            return False
        return True
    
    def format_value(value, suffix=''):
        """格式化显示值"""
        if isinstance(value, float):
            if abs(value) >= 100000000:  # 亿
                return f"{value/100000000:.2f}亿{suffix}"
            elif abs(value) >= 10000:  # 万
                return f"{value/10000:.2f}万{suffix}"
            else:
                return f"{value:.2f}{suffix}"
        return f"{value}{suffix}"
    
    # 先检查是否有任何财务数据
    has_any_data = False
    financial_fields = [
        ('所属行业', row.get('所属行业', row.get('所属同花顺行业', None))),
        ('总市值', row.get('总市值', row.get('总市值[20241211]', None))),
        ('市盈率', row.get('市盈率', row.get('市盈率pe', None))),
        ('市净率', row.get('市净率', row.get('市净率pb', None))),
        ('流通市值', row.get('流通市值', row.get('流通市值[20241211]', None))),
        ('换手率', row.get('换手率', row.get('换手率[%]', None)))
    ]
    
    for _, value in financial_fields:
        if is_valid_value(value):
            has_any_data = True
            break
    
    # 只有当存在有效数据时才显示两列布局
    if has_any_data:
        col1, col2 = st.columns(2)
    else:
        col1 = st.container()
        col2 = None
    
    with col1:
        st.markdown("#### 📊 基本信息")
        
        # 股票代码（必显示）
        code = row.get('股票代码', '')
        if is_valid_value(code):
            st.markdown(f"**股票代码**: {code}")
        
        # 股票简称（必显示）
        name = row.get('股票简称', '')
        if is_valid_value(name):
            st.markdown(f"**股票简称**: {name}")
        
        # 当前价格
        price = row.get('股价', row.get('最新价', None))
        if is_valid_value(price):
            st.markdown(f"**当前价格**: {format_value(price, '元')}")
        
        # 净利润增长率
        growth = row.get('净利润增长率', row.get('净利润同比增长率', None))
        if is_valid_value(growth):
            st.markdown(f"**净利润增长率**: {format_value(growth, '%')}")
        
        # 成交额
        turnover = row.get('成交额', None)
        if is_valid_value(turnover):
            st.markdown(f"**成交额**: {format_value(turnover, '元')}")
        
        # 涨跌幅
        change_pct = row.get('涨跌幅', row.get('涨跌幅:前复权[%]', None))
        if is_valid_value(change_pct):
            st.markdown(f"**涨跌幅**: {format_value(change_pct, '%')}")
    
    # 只有当有财务数据时才显示财务指标栏目
    if col2 is not None:
        with col2:
            st.markdown("#### 💼 财务指标")
            
            # 所属行业
            industry = row.get('所属行业', row.get('所属同花顺行业', None))
            if is_valid_value(industry):
                st.markdown(f"**所属行业**: {industry}")
            
            # 总市值
            market_cap = row.get('总市值', row.get('总市值[20241211]', None))
            if is_valid_value(market_cap):
                st.markdown(f"**总市值**: {format_value(market_cap, '元')}")
            
            # 市盈率
            pe = row.get('市盈率', row.get('市盈率pe', None))
            if is_valid_value(pe):
                st.markdown(f"**市盈率**: {format_value(pe, '')}")
            
            # 市净率
            pb = row.get('市净率', row.get('市净率pb', None))
            if is_valid_value(pb):
                st.markdown(f"**市净率**: {format_value(pb, '')}")
            
            # 流通市值
            float_cap = row.get('流通市值', row.get('流通市值[20241211]', None))
            if is_valid_value(float_cap):
                st.markdown(f"**流通市值**: {format_value(float_cap, '元')}")
            
            # 换手率
            turnover_rate = row.get('换手率', row.get('换手率[%]', None))
            if is_valid_value(turnover_rate):
                st.markdown(f"**换手率**: {format_value(turnover_rate, '%')}")
    
    # 添加监控按钮
    st.markdown("---")
    st.markdown("#### 📊 策略监控")
    
    from low_price_bull_monitor_ui import add_stock_to_monitor_button
    
    stock_code = row.get('股票代码', '')
    stock_name = row.get('股票简称', '')
    price = row.get('股价', row.get('最新价', None))
    
    # 去掉代码后缀
    if isinstance(stock_code, str) and '.' in stock_code:
        stock_code = stock_code.split('.')[0]
    
    # 转换价格
    try:
        price_float = float(price) if price and not pd.isna(price) else None
    except:
        price_float = None
    
    if stock_code and stock_name:
        add_stock_to_monitor_button(stock_code, stock_name, price_float)


def display_strategy_simulation(stocks_df: pd.DataFrame, selector):
    """显示量化交易策略模拟"""
    
    st.markdown("## 🎯 策略监控与模拟")
    
    st.info("""
    **监控说明**：
    - 在上方股票列表中点击"➕ 加入策略监控"按钮即可加入
    - 监控条件：① 持股满5天第6天开盘提醒卖出 ② MA5下穿MA20提醒卖出
    - 扫描频率：每分钟扫描1次（可在监控面板配置）
    - 提醒卖出后自动移出监控列表
    - 点击右上角"📊 策略监控"按钮查看监控面板
    """)
    
    col1, col2 = st.columns(2)
    
    with col1:
        if st.button("🎮 开始策略模拟", type="primary", width='content'):
            st.session_state.show_strategy_simulation = True
    
    with col2:
        if st.button("🔗 连接MiniQMT实盘", type="secondary", width='content'):
            st.warning("⚠️ MiniQMT实盘交易功能需要先配置环境变量，详见系统配置")
    
    # 显示模拟结果
    if st.session_state.get('show_strategy_simulation'):
        run_strategy_simulation(stocks_df)


def run_strategy_simulation(stocks_df: pd.DataFrame):
    """运行策略模拟"""
    
    st.markdown("---")
    st.markdown("### 📈 策略模拟执行")
    
    # 创建策略实例
    strategy = LowPriceBullStrategy(initial_capital=1000000.0)
    
    # 模拟买入（按成交额排序，优先买入成交额小的）
    st.markdown("#### 1️⃣ 模拟买入信号")
    
    buy_results = []
    current_date = datetime.now().strftime("%Y-%m-%d")
    
    for idx, row in stocks_df.head(strategy.max_daily_buy).iterrows():
        code = str(row.get('股票代码', '')).split('.')[0]
        name = row.get('股票简称', 'N/A')
        price = float(row.get('股价', row.get('最新价', 0)))
        
        if price > 0:
            success, message, trade = strategy.buy(code, name, price, current_date)
            buy_results.append({
                'success': success,
                'message': message,
                'trade': trade
            })
    
    # 显示买入结果
    for result in buy_results:
        if result['success']:
            st.success(result['message'])
        else:
            st.warning(f"⚠️ {result['message']}")
    
    # 显示持仓
    st.markdown("---")
    st.markdown("#### 2️⃣ 当前持仓")
    
    positions = strategy.get_positions()
    if positions:
        positions_df = pd.DataFrame(positions)
        st.dataframe(positions_df, width='content')
    else:
        st.info("暂无持仓")
    
    # 显示账户摘要
    st.markdown("---")
    st.markdown("#### 3️⃣ 账户摘要")
    
    summary = strategy.get_portfolio_summary()
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("初始资金", f"{summary['initial_capital']:,.0f} 元")
    
    with col2:
        st.metric("可用资金", f"{summary['available_cash']:,.0f} 元")
    
    with col3:
        st.metric("持仓市值", f"{summary['position_value']:,.0f} 元")
    
    with col4:
        st.metric("总资产", f"{summary['total_value']:,.0f} 元")
    
    st.markdown("---")
    
    # 策略说明
    st.markdown("#### 📝 策略执行说明")
    st.markdown("""
    **后续操作**：
    1. **持有期管理**：系统会自动跟踪每只股票的持有天数
    2. **卖出信号监测**：
       - 每日收盘后计算MA5和MA20
       - 如果MA5下穿MA20，触发卖出信号
       - 如果持股满5天，强制卖出
    3. **轮动买入**：卖出后释放资金，继续买入新的符合条件的股票
    
    **风险提示**：
    - ⚠️ 本策略为模拟演示，实际交易存在滑点、手续费等成本
    - ⚠️ 历史业绩不代表未来收益
    - ⚠️ 请谨慎评估风险，理性投资
    """)


def send_dingtalk_notification(stocks_df: pd.DataFrame, top_n: int):
    """发送钉钉通知"""
    
    try:
        # 检查webhook配置
        webhook_config = notification_service.get_webhook_config_status()
        
        if not webhook_config['enabled'] or not webhook_config['configured']:
            st.info("💡 未配置Webhook通知，如需接收钉钉消息请在环境配置中设置")
            return
        
        # 构建消息内容
        keyword = notification_service.config.get('webhook_keyword', 'aiagents通知')
        
        message_text = f"### {keyword} - 低价擒牛选股完成\n\n"
        message_text += f"**筛选策略**: 股价<10元 + 净利润增长率≥100% + 深圳A股\n\n"
        message_text += f"**筛选数量**: {len(stocks_df)} 只\n\n"
        message_text += f"**精选股票**:\n\n"
        
        for idx, row in stocks_df.head(top_n).iterrows():
            code = row.get('股票代码', '')
            name = row.get('股票简称', '')
            
            # 只显示有效的信息
            message_text += f"{idx+1}. **{code} {name}**\n"
            
            # 股价
            price = row.get('股价', row.get('最新价', None))
            if price is not None and not pd.isna(price) and str(price).strip() not in ['', 'N/A']:
                try:
                    price_float = float(price)
                    message_text += f"   - 股价: {price_float:.2f}元\n"
                except:
                    pass
            
            # 净利润增长率
            growth = row.get('净利润增长率', row.get('净利润同比增长率', None))
            if growth is not None and not pd.isna(growth) and str(growth).strip() not in ['', 'N/A']:
                try:
                    growth_float = float(growth)
                    message_text += f"   - 净利增长: {growth_float:.2f}%\n"
                except:
                    pass
            
            # 成交额
            turnover = row.get('成交额', None)
            if turnover is not None and not pd.isna(turnover) and str(turnover).strip() not in ['', 'N/A']:
                try:
                    turnover_float = float(turnover)
                    if turnover_float >= 100000000:  # 亿
                        message_text += f"   - 成交额: {turnover_float/100000000:.2f}亿元\n"
                    elif turnover_float >= 10000:  # 万
                        message_text += f"   - 成交额: {turnover_float/10000:.2f}万元\n"
                    else:
                        message_text += f"   - 成交额: {turnover_float:.2f}元\n"
                except:
                    pass
            
            # 所属行业
            industry = row.get('所属行业', row.get('所属同花顺行业', None))
            if industry is not None and not pd.isna(industry) and str(industry).strip() not in ['', 'N/A']:
                message_text += f"   - 所属行业: {industry}\n"
            
            message_text += "\n"
        
        message_text += f"**生成时间**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n"
        message_text += "_此消息由AI股票分析系统自动发送_"
        
        # 直接发送钉钉Webhook（不使用notification_service的默认格式）
        if notification_service.config['webhook_type'] == 'dingtalk':
            import requests
            
            data = {
                "msgtype": "markdown",
                "markdown": {
                    "title": f"{keyword}",
                    "text": message_text
                }
            }
            
            try:
                response = requests.post(
                    notification_service.config['webhook_url'],
                    json=data,
                    headers={'Content-Type': 'application/json'},
                    timeout=10
                )
                
                if response.status_code == 200:
                    result = response.json()
                    if result.get('errcode') == 0:
                        st.success("✅ 已发送钉钉通知")
                    else:
                        st.warning(f"⚠️ 钉钉通知发送失败: {result.get('errmsg')}")
                else:
                    st.warning(f"⚠️ 钉钉通知请求失败: HTTP {response.status_code}")
            except Exception as e:
                st.warning(f"⚠️ 发送钉钉通知失败: {str(e)}")
        
    except Exception as e:
        st.warning(f"⚠️ 发送通知时出错: {str(e)}")
