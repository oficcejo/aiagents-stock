import streamlit as st
from datetime import datetime
from typing import Dict, List

from db.monitor_db import monitor_db
from services.monitor_service import monitor_service
from services.notification_service import notification_service

def display_monitor_panel():
    """显示监测面板"""
    
    st.markdown("## 📊 实时监测面板")
    
    # 监测服务控制
    col1, col2, col3, col4 = st.columns([1, 1, 1, 1])
    
    with col1:
        if st.button("▶️ 启动监测服务", type="primary"):
            monitor_service.start_monitoring()
    
    with col2:
        if st.button("⏹️ 停止监测服务"):
            monitor_service.stop_monitoring()
    
    with col3:
        if st.button("🔄 手动更新所有"):
            stocks = monitor_service.get_stocks_needing_update()
            for stock in stocks:
                monitor_service.manual_update_stock(stock['id'])
            st.success(f"✅ 已手动更新 {len(stocks)} 只股票")
    
    with col4:
        # 显示定时调度状态
        try:
            scheduler = monitor_service.get_scheduler()
            status = scheduler.get_status()
            if status['scheduler_running']:
                st.success("⏰ 定时已启用")
            else:
                st.info("⏰ 定时未启用")
        except:
            st.info("⏰ 定时未配置")
    
    # 显示通知
    display_notifications()
    
    # 显示监测股票
    display_monitored_stocks()

def display_notifications():
    """显示通知"""
    notifications = notification_service.get_streamlit_notifications()
    
    if notifications:
        st.markdown("### 🔔 最新提醒")
        
        for notification in notifications[-5:]:  # 只显示最近5条
            notification_type = notification['type']
            color_map = {
                'entry': '🟢',
                'take_profit': '🟡', 
                'stop_loss': '🔴'
            }
            icon = color_map.get(notification_type, '🔵')
            
            st.info(f"{icon} **{notification['symbol']}** - {notification['message']}")
        
        if st.button("清空提醒"):
            notification_service.clear_streamlit_notifications()
            st.rerun()

def display_monitored_stocks():
    """显示监测股票卡片"""
    stocks = monitor_db.get_monitored_stocks()
    
    if not stocks:
        st.info("📋 暂无监测股票，请在分析完成后点击'加入监测'按钮添加")
        return
    
    st.markdown(f"### 📈 监测中 ({len(stocks)} 只)")
    
    # 每行显示3个卡片
    cols = st.columns(3)
    
    for i, stock in enumerate(stocks):
        col_idx = i % 3
        with cols[col_idx]:
            display_stock_card(stock)

def display_stock_card(stock: Dict):
    """显示单个股票监测卡片（显示交易时段设置）"""
    
    with st.container():
        # 标题行：添加交易时段标识
        trading_badge = "🕒仅交易时段" if stock.get('trading_hours_only', True) else "🌐全时段"
        st.markdown(f"### {stock['symbol']} - {stock['name']} {trading_badge}")
        
        # 评级和状态
        col1, col2 = st.columns([1, 1])
        with col1:
            rating_color = {
                '买入': '🟢',
                '持有': '🟡',
                '卖出': '🔴'
            }
            st.metric("评级", f"{rating_color.get(stock['rating'], '⚪')} {stock['rating']}")
        
        with col2:
            if stock['current_price'] and stock['current_price'] != 'N/A':
                st.metric("当前价格", f"¥{stock['current_price']}")
            else:
                st.metric("当前价格", "等待更新")
        
        # 关键价位
        entry_range = stock['entry_range']
        st.info(f"**进场区间**: ¥{entry_range['min']} - ¥{entry_range['max']}")
        
        if stock['take_profit']:
            st.success(f"**止盈位**: ¥{stock['take_profit']}")
        
        if stock['stop_loss']:
            st.error(f"**止损位**: ¥{stock['stop_loss']}")
        
        # 最后更新时间和监控模式
        if stock['last_checked']:
            last_checked = datetime.fromisoformat(stock['last_checked'])
            st.caption(f"最后更新: {last_checked.strftime('%m-%d %H:%M')}")
        
        # 监控模式提示
        if stock.get('trading_hours_only', True):
            st.caption("⏰ 监控模式：交易日 9:30-11:30, 13:00-15:00")
        else:
            st.caption("🌐 监控模式：全天候")
        
        # 操作按钮
        col1, col2 = st.columns([1, 1])
        with col1:
            if st.button("🔄 更新", key=f"update_{stock['id']}"):
                if monitor_service.manual_update_stock(stock['id']):
                    st.success("✅ 更新成功")
                else:
                    st.error("❌ 更新失败")
        
        with col2:
            if st.button("🗑️ 移除", key=f"remove_{stock['id']}"):
                monitor_db.remove_monitored_stock(stock['id'])
                st.success("✅ 已移除监测")
                st.rerun()

def add_to_monitor_dialog(stock_info: Dict, analysis_result: Dict):
    """显示添加到监测的对话框（支持交易时段选项）"""
    
    st.markdown("---")
    st.markdown("## 📈 添加到实时监测")
    
    # 从分析结果中提取关键数据
    final_decision = analysis_result.get('final_decision', {})
    rating = final_decision.get('rating', '持有')
    reasoning = final_decision.get('reasoning', '')
    
    # 生成唯一的session标识符
    import uuid
    import time
    session_id = f"{stock_info.get('symbol', 'unknown')}_{int(time.time())}_{uuid.uuid4().hex[:6]}"
    
    # 解析关键价位（从分析结果中提取或手动输入）
    col1, col2 = st.columns([1, 1])
    
    with col1:
        # 进场区间
        st.subheader("🎯 进场区间")
        entry_min = st.number_input("最低进场价", value=0.0, key=f"entry_min_{session_id}")
        entry_max = st.number_input("最高进场价", value=0.0, key=f"entry_max_{session_id}")
        
        if entry_min > 0 and entry_max > 0 and entry_max > entry_min:
            entry_range = {"min": entry_min, "max": entry_max}
        else:
            st.warning("请输入有效的进场区间")
            entry_range = None
    
    with col2:
        # 止盈止损
        st.subheader("⚖️ 风险控制")
        take_profit = st.number_input("止盈价位", value=0.0, key=f"take_profit_{session_id}")
        stop_loss = st.number_input("止损价位", value=0.0, key=f"stop_loss_{session_id}")
        
        if take_profit > 0:
            st.success(f"止盈位: ¥{take_profit}")
        if stop_loss > 0:
            st.error(f"止损位: ¥{stop_loss}")
    
    # 监测设置
    st.subheader("⏰ 监测设置")
    col3, col4 = st.columns([1, 1])
    
    with col3:
        check_interval = st.slider("监测间隔(分钟)", 5, 120, 30, key=f"check_interval_{session_id}")
        notification_enabled = st.checkbox("启用提醒", value=True, key=f"notification_enabled_{session_id}")
    
    with col4:
        trading_hours_only = st.checkbox(
            "仅交易时段监控", 
            value=True, 
            key=f"trading_hours_only_{session_id}",
            help="开启后，只在交易日的交易时段（9:30-11:30, 13:00-15:00）进行AI分析和监控"
        )
        st.info("💡 推荐开启，节省资源且更高效")
    
    # 添加按钮
    if st.button("✅ 确认加入监测", type="primary", key=f"add_monitor_{session_id}"):
        if entry_range:
            # 添加到监测数据库
            stock_id = monitor_db.add_monitored_stock(
                symbol=stock_info.get('symbol'),
                name=stock_info.get('name'),
                rating=rating,
                entry_range=entry_range,
                take_profit=take_profit if take_profit > 0 else None,
                stop_loss=stop_loss if stop_loss > 0 else None,
                check_interval=check_interval,
                notification_enabled=notification_enabled,
                trading_hours_only=trading_hours_only
            )
            
            st.success(f"✅ 已成功将 {stock_info.get('symbol')} 加入实时监测")
            st.balloons()
            
            # 立即更新一次价格
            monitor_service.manual_update_stock(stock_id)
        else:
            st.error("❌ 请设置有效的进场区间")

def get_monitor_summary() -> Dict:
    """获取监测摘要信息"""
    stocks = monitor_db.get_monitored_stocks()
    
    summary = {
        'total_stocks': len(stocks),
        'stocks_needing_update': len(monitor_service.get_stocks_needing_update()),
        'pending_notifications': len(monitor_db.get_pending_notifications()),
        'active_monitoring': monitor_service.running
    }
    
    return summary