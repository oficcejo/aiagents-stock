#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
低价擒牛策略监控UI模块
"""

import streamlit as st
import pandas as pd
from datetime import datetime
from db.low_price_bull_db import low_price_bull_monitor
from services.low_price_bull_service import low_price_bull_service


def display_monitor_panel():
    """显示策略监控面板"""
    
    st.markdown("## 📊 策略监控中心")
    st.markdown("---")
    
    # 服务状态
    status = low_price_bull_service.get_status()
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        service_status = "🟢 运行中" if status['running'] else "🔴 已停止"
        st.metric("服务状态", service_status)
    
    with col2:
        st.metric("监控股票", f"{status['monitored_count']} 只")
    
    with col3:
        st.metric("待处理提醒", f"{status['pending_alerts']} 条")
    
    with col4:
        st.metric("扫描间隔", f"{status['scan_interval']} 秒")
    
    st.markdown("---")
    
    # 服务控制
    col_start, col_stop, col_config = st.columns(3)
    
    with col_start:
        if st.button("▶️ 启动监控服务", type="primary", disabled=status['running']):
            if low_price_bull_service.start():
                st.success("✅ 监控服务已启动")
                st.rerun()
            else:
                st.error("❌ 启动失败")
    
    with col_stop:
        if st.button("⏸️ 停止监控服务", type="secondary", disabled=not status['running']):
            if low_price_bull_service.stop():
                st.success("✅ 监控服务已停止")
                st.rerun()
            else:
                st.error("❌ 停止失败")
    
    with col_config:
        with st.popover("⚙️ 监控配置"):
            st.markdown("**扫描间隔**")
            new_interval = st.number_input(
                "扫描间隔（秒）",
                min_value=10,
                max_value=600,
                value=status['scan_interval'],
                step=10,
                label_visibility="collapsed"
            )
            
            if st.button("保存配置"):
                low_price_bull_service.scan_interval = new_interval
                st.success("✅ 配置已保存")
    
    st.markdown("---")
    
    # 标签页
    tab1, tab2, tab3 = st.tabs(["📋 监控列表", "🔔 卖出提醒", "📜 历史记录"])
    
    with tab1:
        display_monitored_stocks()
    
    with tab2:
        display_sell_alerts()
    
    with tab3:
        display_alert_history()


def display_monitored_stocks():
    """显示监控中的股票列表"""
    
    stocks = low_price_bull_monitor.get_monitored_stocks()
    
    if not stocks:
        st.info("暂无监控中的股票")
        return
    
    st.markdown(f"### 📋 监控列表（共{len(stocks)}只）")
    
    # 转换为DataFrame
    df = pd.DataFrame(stocks)
    
    # 显示表格
    display_df = df[['stock_code', 'stock_name', 'buy_price', 'buy_date', 'holding_days', 'add_time']].copy()
    display_df.columns = ['股票代码', '股票名称', '买入价格', '买入日期', '持有天数', '加入时间']
    
    st.dataframe(display_df, width='content', height=400)
    
    # 批量移除
    st.markdown("---")
    st.markdown("### 🗑️ 批量管理")
    
    selected_codes = st.multiselect(
        "选择要移除的股票",
        options=[f"{s['stock_code']} {s['stock_name']}" for s in stocks],
        format_func=lambda x: x
    )
    
    if selected_codes and st.button("🗑️ 移除选中股票", type="secondary"):
        for item in selected_codes:
            code = item.split()[0]
            success, msg = low_price_bull_monitor.remove_stock(code, "手动移除")
            if success:
                st.success(msg)
            else:
                st.error(msg)
        st.rerun()


def display_sell_alerts():
    """显示待处理的卖出提醒"""
    
    alerts = low_price_bull_monitor.get_pending_alerts()
    
    if not alerts:
        st.info("暂无待处理的卖出提醒")
        return
    
    st.markdown(f"### 🔔 卖出提醒（共{len(alerts)}条）")
    
    for alert in alerts:
        with st.expander(
            f"🔔 {alert['stock_code']} {alert['stock_name']} - {alert['alert_reason']}",
            expanded=True
        ):
            col1, col2 = st.columns(2)
            
            with col1:
                st.markdown("#### 📊 提醒信息")
                st.markdown(f"**股票代码**: {alert['stock_code']}")
                st.markdown(f"**股票名称**: {alert['stock_name']}")
                st.markdown(f"**提醒类型**: {_get_alert_type_name(alert['alert_type'])}")
                st.markdown(f"**提醒原因**: {alert['alert_reason']}")
                st.markdown(f"**提醒时间**: {alert['alert_time']}")
            
            with col2:
                st.markdown("#### 💰 市场数据")
                
                # 处理当前价格（避免bytes类型错误）
                current_price = alert.get('current_price')
                if current_price is not None:
                    try:
                        price_val = float(current_price)
                        st.markdown(f"**当前价格**: {price_val:.2f}元")
                    except (ValueError, TypeError):
                        st.markdown(f"**当前价格**: {current_price}")
                
                # 处理MA5和MA20（避免bytes类型错误）
                ma5 = alert.get('ma5')
                ma20 = alert.get('ma20')
                if ma5 is not None and ma20 is not None:
                    try:
                        ma5_val = float(ma5)
                        ma20_val = float(ma20)
                        st.markdown(f"**MA5**: {ma5_val:.2f}")
                        st.markdown(f"**MA20**: {ma20_val:.2f}")
                        st.markdown(f"**均线差**: {(ma5_val - ma20_val):.2f}")
                    except (ValueError, TypeError):
                        st.markdown(f"**MA5**: {ma5}")
                        st.markdown(f"**MA20**: {ma20}")
                
                # 处理持有天数
                holding_days = alert.get('holding_days')
                if holding_days is not None:
                    try:
                        days_val = int(holding_days)
                        st.markdown(f"**持有天数**: {days_val}天")
                    except (ValueError, TypeError):
                        st.markdown(f"**持有天数**: {holding_days}")
            
            # 操作按钮
            st.markdown("---")
            col_action1, col_action2 = st.columns(2)
            
            with col_action1:
                if st.button(f"✅ 已处理 - {alert['stock_code']}", key=f"done_{alert['id']}"):
                    low_price_bull_monitor.mark_alert_sent(alert['id'])
                    low_price_bull_monitor.remove_stock(alert['stock_code'], "已处理提醒")
                    st.success(f"✅ 已标记为已处理并移除 {alert['stock_code']}")
                    st.rerun()
            
            with col_action2:
                if st.button(f"❌ 忽略 - {alert['stock_code']}", key=f"ignore_{alert['id']}"):
                    low_price_bull_monitor.mark_alert_sent(alert['id'])
                    st.success(f"✅ 已忽略提醒（股票保留在监控列表）")
                    st.rerun()


def display_alert_history():
    """显示历史提醒记录"""
    
    alerts = low_price_bull_monitor.get_history_alerts(limit=50)
    
    if not alerts:
        st.info("暂无历史提醒记录")
        return
    
    st.markdown("### 📜 历史提醒记录")
    
    # 转换为DataFrame
    df = pd.DataFrame(alerts)
    
    # 选择显示列
    display_cols = ['stock_code', 'stock_name', 'alert_type', 'alert_reason', 'current_price', 'holding_days', 'alert_time', 'is_sent']
    display_df = df[display_cols].copy()
    
    # 重命名列
    display_df.columns = ['股票代码', '股票名称', '提醒类型', '提醒原因', '当前价格', '持有天数', '提醒时间', '已发送']
    
    # 格式化
    display_df['提醒类型'] = display_df['提醒类型'].apply(_get_alert_type_name)
    display_df['已发送'] = display_df['已发送'].apply(lambda x: '✅' if x == 1 else '❌')
    
    st.dataframe(display_df, width='content', height=400)
    
    # 清理按钮
    st.markdown("---")
    if st.button("🗑️ 清理30天前的记录"):
        low_price_bull_monitor.clear_old_alerts(days=30)
        st.success("✅ 已清理旧记录")
        st.rerun()


def _get_alert_type_name(alert_type: str) -> str:
    """获取提醒类型名称"""
    type_map = {
        'holding_days': '持股到期',
        'ma_cross': 'MA均线死叉'
    }
    return type_map.get(alert_type, alert_type)


def add_stock_to_monitor_button(stock_code: str, stock_name: str, price: float = None):
    """
    添加股票到监控按钮（在股票详情中使用）
    
    Args:
        stock_code: 股票代码
        stock_name: 股票名称
        price: 买入价格
    """
    # 检查是否已在监控
    stocks = low_price_bull_monitor.get_monitored_stocks()
    is_monitored = any(s['stock_code'] == stock_code for s in stocks)
    
    if is_monitored:
        st.info(f"✅ {stock_code} 已在监控列表中")
        if st.button(f"🗑️ 移出监控 - {stock_code}", key=f"remove_{stock_code}"):
            success, msg = low_price_bull_monitor.remove_stock(stock_code, "手动移除")
            if success:
                st.success(msg)
                st.rerun()
            else:
                st.error(msg)
    else:
        if st.button(f"➕ 加入策略监控 - {stock_code}", type="primary", key=f"add_{stock_code}"):
            if price is None:
                price = 0.0  # 如果没有价格，使用0
            
            success, msg = low_price_bull_monitor.add_stock(
                stock_code=stock_code,
                stock_name=stock_name,
                buy_price=price,
                buy_date=datetime.now().strftime("%Y-%m-%d")
            )
            
            if success:
                st.success(msg)
                st.info("💡 提示：请在左侧菜单进入'策略监控'查看监控状态")
                st.rerun()
            else:
                st.error(msg)
