#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
股票监测管理模块
支持添加、删除、编辑监测股票
卡片式布局，支持关键位置监测
"""

import streamlit as st
import time
import uuid
from datetime import datetime, timedelta
from typing import Dict, List
import json

from db.monitor_db import monitor_db
from services.monitor_service import monitor_service
from services.notification_service import notification_service
from data_sources.stock_data import StockDataFetcher
from interfaces.miniqmt_interface import miniqmt, get_miniqmt_status, QuantStrategyConfig

def display_monitor_manager():
    """显示监测管理主页面"""
    
    st.markdown("## 📊 股票监测管理")
    st.markdown("---")
    
    # 检查是否有跳转提示
    if 'monitor_jump_highlight' in st.session_state:
        symbol = st.session_state.monitor_jump_highlight
        st.success(f"✅ {symbol} 已成功加入监测列表！您可以在下方查看。")
        del st.session_state.monitor_jump_highlight
    
    # 监测服务状态
    display_monitor_status()
    
    # 添加新股票监测
    display_add_stock_section()
    
    # 监测股票列表
    display_monitored_stocks()
    
    # 通知管理
    display_notification_management()

def display_monitor_status():
    """显示监测服务状态"""
    
    col1, col2, col3, col4, col5, col6 = st.columns(6)
    
    with col1:
        if monitor_service.running:
            st.success("🟢 运行中")
        else:
            st.error("🔴 已停止")
    
    with col2:
        stocks = monitor_db.get_monitored_stocks()
        st.metric("监测股票", len(stocks))
    
    with col3:
        notifications = monitor_db.get_pending_notifications()
        st.metric("待处理通知", len(notifications))
    
    with col4:
        # 显示MiniQMT状态
        qmt_status = get_miniqmt_status()
        if qmt_status['ready']:
            st.success("🤖 QMT在线")
        else:
            st.info("🤖 QMT离线")
    
    with col5:
        if monitor_service.running:
            if st.button("⏹️ 停止监测", type="secondary"):
                monitor_service.stop_monitoring()
                st.success("✅ 监测服务已停止")
                st.rerun()
        else:
            if st.button("▶️ 启动监测", type="primary"):
                monitor_service.start_monitoring()
                st.success("✅ 监测服务已启动")
                st.rerun()
    
    with col6:
        if st.button("🔄 刷新状态"):
            st.rerun()
    
    # 显示定时调度状态和配置
    display_scheduler_section()

def display_add_stock_section():
    """显示添加股票监测区域"""
    
    st.markdown("### ➕ 添加股票监测")
    
    with st.expander("点击展开添加股票监测", expanded=False):
        col1, col2 = st.columns([1, 1])
        
        with col1:
            # 股票信息输入
            st.subheader("📈 股票信息")
            symbol = st.text_input("股票代码", placeholder="例如: AAPL, 000001", help="支持美股和A股代码")
            name = st.text_input("股票名称", placeholder="例如: 苹果公司", help="可选，用于显示")
            
            # 获取股票基本信息
            if symbol:
                if st.button("🔍 获取股票信息"):
                    with st.spinner("正在获取股票信息..."):
                        fetcher = StockDataFetcher()
                        stock_info = fetcher.get_stock_info(symbol)
                        
                        if "error" not in stock_info:
                            st.success("✅ 股票信息获取成功")
                            st.session_state.temp_stock_info = stock_info
                        else:
                            st.error(f"❌ {stock_info['error']}")
        
        with col2:
            # 监测设置
            st.subheader("⚙️ 监测设置")
            
            # 关键位置设置
            st.markdown("**🎯 关键位置设置**")
            entry_min = st.number_input("进场区间最低价", value=0.0, step=0.01, format="%.2f")
            entry_max = st.number_input("进场区间最高价", value=0.0, step=0.01, format="%.2f")
            take_profit = st.number_input("止盈价位", value=0.0, step=0.01, format="%.2f", help="可选")
            stop_loss = st.number_input("止损价位", value=0.0, step=0.01, format="%.2f", help="可选")
            
            # 监测参数
            st.markdown("**⏰ 监测参数**")
            check_interval = st.slider("监测间隔(分钟)", 5, 120, 30)
            notification_enabled = st.checkbox("启用通知", value=True)
            
            # 投资评级
            rating = st.selectbox("投资评级", ["买入", "持有", "卖出"], index=0)
            
            # 量化交易设置
            st.markdown("**🤖 量化交易（MiniQMT）**")
            quant_enabled = st.checkbox("启用量化自动交易", value=False, help="需要先配置MiniQMT连接")
            
            if quant_enabled:
                max_position_pct = st.slider("最大仓位比例", 0.05, 0.5, 0.2, 0.05, help="单只股票最大占总资金的比例")
                auto_stop_loss = st.checkbox("自动止损", value=True)
                auto_take_profit = st.checkbox("自动止盈", value=True)
        
        # 添加按钮
        if st.button("✅ 添加监测", type="primary", width='stretch'):
            if symbol and entry_min > 0 and entry_max > 0 and entry_max > entry_min:
                try:
                    # 准备数据
                    entry_range = {"min": entry_min, "max": entry_max}
                    
                    # 准备量化配置
                    quant_config = None
                    if quant_enabled:
                        quant_config = {
                            'max_position_pct': max_position_pct,
                            'auto_stop_loss': auto_stop_loss,
                            'auto_take_profit': auto_take_profit,
                            'min_trade_amount': 5000
                        }
                    
                    # 添加到数据库
                    stock_id = monitor_db.add_monitored_stock(
                        symbol=symbol,
                        name=name or symbol,
                        rating=rating,
                        entry_range=entry_range,
                        take_profit=take_profit if take_profit > 0 else None,
                        stop_loss=stop_loss if stop_loss > 0 else None,
                        check_interval=check_interval,
                        notification_enabled=notification_enabled,
                        quant_enabled=quant_enabled,
                        quant_config=quant_config
                    )
                    
                    st.success(f"✅ 已成功添加 {symbol} 到监测列表")
                    st.balloons()
                    
                    # 立即更新一次价格
                    monitor_service.manual_update_stock(stock_id)
                    
                    # 清空表单
                    st.rerun()
                    
                except Exception as e:
                    st.error(f"❌ 添加失败: {str(e)}")
            else:
                st.error("❌ 请填写完整的股票信息和有效的进场区间")

def display_monitored_stocks():
    """显示监测股票列表 - 卡片式布局"""
    
    st.markdown("### 📋 监测股票列表")
    
    stocks = monitor_db.get_monitored_stocks()
    
    if not stocks:
        st.info("📭 暂无监测股票，请添加股票开始监测")
        return
    
    # 筛选和搜索
    col1, col2, col3 = st.columns([2, 1, 1])
    
    with col1:
        search_term = st.text_input("🔍 搜索股票", placeholder="输入股票代码或名称")
    
    with col2:
        rating_filter = st.selectbox("评级筛选", ["全部", "买入", "持有", "卖出"])
    
    with col3:
        if st.button("🔄 刷新列表"):
            st.rerun()
    
    # 筛选股票
    filtered_stocks = stocks
    if search_term:
        filtered_stocks = [s for s in stocks if search_term.lower() in s['symbol'].lower() or search_term.lower() in s['name'].lower()]
    
    if rating_filter != "全部":
        filtered_stocks = [s for s in filtered_stocks if s['rating'] == rating_filter]
    
    if not filtered_stocks:
        st.warning("🔍 未找到匹配的股票")
        return
    
    # 卡片式布局 - 每行显示2个卡片
    for i in range(0, len(filtered_stocks), 2):
        cols = st.columns(2)
        
        for j, col in enumerate(cols):
            if i + j < len(filtered_stocks):
                stock = filtered_stocks[i + j]
                with col:
                    display_stock_card(stock)
    
    # 显示编辑对话框
    if 'editing_stock_id' in st.session_state:
        display_edit_dialog(st.session_state.editing_stock_id)
    
    # 显示删除确认对话框
    if 'deleting_stock_id' in st.session_state:
        display_delete_confirm_dialog(st.session_state.deleting_stock_id)

def display_stock_card(stock: Dict):
    """显示单个股票监测卡片"""
    
    with st.container():
        # 卡片头部
        st.markdown(f"""
        <div style="
            border: 1px solid #ddd;
            border-radius: 10px;
            padding: 15px;
            margin: 10px 0;
            background-color: #f9f9f9;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        ">
        """, unsafe_allow_html=True)
        
        # 股票基本信息
        col1, col2 = st.columns([2, 1])
        
        with col1:
            st.markdown(f"**{stock['symbol']}** - {stock['name']}")
            
            # 评级显示
            rating_color = {
                '买入': '🟢',
                '持有': '🟡',
                '卖出': '🔴'
            }
            st.markdown(f"评级: {rating_color.get(stock['rating'], '⚪')} {stock['rating']}")
        
        with col2:
            if stock['current_price'] and stock['current_price'] != 'N/A':
                st.metric("当前价格", f"¥{stock['current_price']}")
            else:
                st.metric("当前价格", "等待更新")
        
        # 关键位置信息
        st.markdown("**🎯 关键位置**")
        
        entry_range = stock.get('entry_range')
        col1, col2, col3 = st.columns(3)
        
        with col1:
            if entry_range and isinstance(entry_range, dict):
                st.info(f"**进场区间**\n¥{entry_range.get('min', 0)} - ¥{entry_range.get('max', 0)}")
            else:
                st.warning("**进场区间**\n未设置")
        
        with col2:
            if stock['take_profit']:
                st.success(f"**止盈位**\n¥{stock['take_profit']}")
            else:
                st.info("**止盈位**\n未设置")
        
        with col3:
            if stock['stop_loss']:
                st.error(f"**止损位**\n¥{stock['stop_loss']}")
            else:
                st.info("**止损位**\n未设置")
        
        # 监测状态
        st.markdown("**📊 监测状态**")
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.caption(f"监测间隔: {stock['check_interval']}分钟")
        
        with col2:
            if stock['last_checked']:
                last_checked = datetime.fromisoformat(stock['last_checked'])
                st.caption(f"最后检查: {last_checked.strftime('%m-%d %H:%M')}")
            else:
                st.caption("最后检查: 从未检查")
        
        with col3:
            status = "🟢 启用" if stock['notification_enabled'] else "🔴 禁用"
            st.caption(f"通知: {status}")
            
            # 显示量化状态
            if stock.get('quant_enabled', False):
                st.caption("🤖 量化: 🟢 启用")
            else:
                st.caption("🤖 量化: 🔴 禁用")
        
        # 操作按钮
        st.markdown("**🔧 操作**")
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            if st.button("🔄 更新", key=f"update_{stock['id']}"):
                if monitor_service.manual_update_stock(stock['id']):
                    st.success("✅ 更新成功")
                else:
                    st.error("❌ 更新失败")
        
        with col2:
            if st.button("✏️ 编辑", key=f"edit_{stock['id']}"):
                st.session_state.editing_stock_id = stock['id']
                st.rerun()
        
        with col3:
            # 切换通知状态
            current_status = stock['notification_enabled']
            if current_status:
                if st.button("🔕 禁用", key=f"notify_{stock['id']}"):
                    monitor_db.toggle_notification(stock['id'], False)
                    st.success("✅ 已禁用通知")
                    st.rerun()
            else:
                if st.button("🔔 启用", key=f"notify_{stock['id']}"):
                    monitor_db.toggle_notification(stock['id'], True)
                    st.success("✅ 已启用通知")
                    st.rerun()
        
        with col4:
            if st.button("🗑️ 删除", key=f"delete_{stock['id']}"):
                st.session_state.deleting_stock_id = stock['id']
                st.rerun()
        
        st.markdown("</div>", unsafe_allow_html=True)

def display_edit_dialog(stock_id: int):
    """显示编辑股票对话框"""
    
    stock = monitor_db.get_stock_by_id(stock_id)
    if not stock:
        st.error("❌ 股票不存在")
        del st.session_state.editing_stock_id
        return
    
    st.markdown("---")
    st.markdown(f"### ✏️ 编辑监测 - {stock['symbol']} {stock['name']}")
    
    with st.form(key=f"edit_form_{stock_id}"):
        col1, col2 = st.columns([1, 1])
        
        with col1:
            st.subheader("🎯 关键位置")
            entry_range = stock.get('entry_range', {})
            entry_min = st.number_input("进场区间最低价", value=float(entry_range.get('min', 0)), step=0.01, format="%.2f")
            entry_max = st.number_input("进场区间最高价", value=float(entry_range.get('max', 0)), step=0.01, format="%.2f")
            take_profit = st.number_input("止盈价位", value=float(stock['take_profit']) if stock['take_profit'] else 0.0, step=0.01, format="%.2f")
            stop_loss = st.number_input("止损价位", value=float(stock['stop_loss']) if stock['stop_loss'] else 0.0, step=0.01, format="%.2f")
        
        with col2:
            st.subheader("⚙️ 监测设置")
            check_interval = st.slider("监测间隔(分钟)", 5, 120, stock['check_interval'])
            rating = st.selectbox("投资评级", ["买入", "持有", "卖出"], 
                                 index=["买入", "持有", "卖出"].index(stock['rating']) if stock['rating'] in ["买入", "持有", "卖出"] else 0)
            notification_enabled = st.checkbox("启用通知", value=stock['notification_enabled'])
            
            # 量化交易设置
            st.markdown("**🤖 量化交易**")
            quant_enabled = st.checkbox("启用量化自动交易", value=stock.get('quant_enabled', False))
            
            if quant_enabled:
                quant_config = stock.get('quant_config', {})
                max_position_pct = st.slider("最大仓位比例", 0.05, 0.5, 
                                            quant_config.get('max_position_pct', 0.2), 0.05)
                auto_stop_loss = st.checkbox("自动止损", value=quant_config.get('auto_stop_loss', True))
                auto_take_profit = st.checkbox("自动止盈", value=quant_config.get('auto_take_profit', True))
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            submit = st.form_submit_button("✅ 保存修改", type="primary", width='stretch')
        
        with col2:
            cancel = st.form_submit_button("❌ 取消", width='stretch')
        
        if submit:
            if entry_min > 0 and entry_max > 0 and entry_max > entry_min:
                try:
                    # 更新数据库
                    new_entry_range = {"min": entry_min, "max": entry_max}
                    
                    # 准备量化配置
                    new_quant_config = None
                    if quant_enabled:
                        new_quant_config = {
                            'max_position_pct': max_position_pct,
                            'auto_stop_loss': auto_stop_loss,
                            'auto_take_profit': auto_take_profit,
                            'min_trade_amount': 5000
                        }
                    
                    monitor_db.update_monitored_stock(
                        stock_id=stock_id,
                        rating=rating,
                        entry_range=new_entry_range,
                        take_profit=take_profit if take_profit > 0 else None,
                        stop_loss=stop_loss if stop_loss > 0 else None,
                        check_interval=check_interval,
                        notification_enabled=notification_enabled,
                        quant_enabled=quant_enabled,
                        quant_config=new_quant_config
                    )
                    
                    st.success("✅ 修改已保存")
                    del st.session_state.editing_stock_id
                    st.rerun()
                except Exception as e:
                    st.error(f"❌ 保存失败: {str(e)}")
            else:
                st.error("❌ 请输入有效的进场区间")
        
        if cancel:
            del st.session_state.editing_stock_id
            st.rerun()

def display_delete_confirm_dialog(stock_id: int):
    """显示删除确认对话框"""
    
    stock = monitor_db.get_stock_by_id(stock_id)
    if not stock:
        st.error("❌ 股票不存在或已被删除")
        if 'deleting_stock_id' in st.session_state:
            del st.session_state.deleting_stock_id
        st.rerun()
        return
    
    st.markdown("---")
    st.markdown(f"### ⚠️ 确认删除")
    
    st.warning(f"""
    您确定要删除以下监测吗？
    
    **股票代码**: {stock['symbol']}
    
    **股票名称**: {stock['name']}
    
    **投资评级**: {stock['rating']}
    
    此操作不可撤销！
    """)
    
    col1, col2, col3 = st.columns([1, 1, 1])
    
    with col1:
        if st.button("🗑️ 确认删除", type="primary", width='stretch', key=f"confirm_delete_{stock_id}"):
            try:
                result = monitor_db.remove_monitored_stock(stock_id)
                if result:
                    # 清理session state
                    if 'deleting_stock_id' in st.session_state:
                        del st.session_state.deleting_stock_id
                    
                    st.success("✅ 已成功删除监测")
                    st.balloons()
                    time.sleep(0.8)  # 短暂延迟，让用户看到成功消息
                    st.rerun()
                else:
                    st.error("❌ 删除失败：股票不存在或已被删除")
                    time.sleep(1)
                    if 'deleting_stock_id' in st.session_state:
                        del st.session_state.deleting_stock_id
                    st.rerun()
            except Exception as e:
                st.error(f"❌ 删除失败：{str(e)}")
                time.sleep(1)
                if 'deleting_stock_id' in st.session_state:
                    del st.session_state.deleting_stock_id
                st.rerun()
    
    with col2:
        if st.button("❌ 取消", width='stretch', key=f"cancel_delete_{stock_id}"):
            del st.session_state.deleting_stock_id
            st.rerun()

def display_notification_management():
    """显示通知管理"""
    
    st.markdown("### 🔔 通知管理")
    
    # 显示MiniQMT量化交易状态
    display_miniqmt_status()
    
    st.markdown("---")
    
    # 通知设置
    col1, col2 = st.columns([1, 1])
    
    with col1:
        st.subheader("📧 邮件通知设置")
        
        # 获取当前邮件配置状态
        email_config = notification_service.get_email_config_status()
        
        # 显示配置状态
        if email_config['configured']:
            st.success("✅ 邮件配置已完成")
        else:
            st.warning("⚠️ 邮件未配置或配置不完整")
        
        # 显示配置信息
        st.info(f"""
        **当前配置：**
        - SMTP服务器: {email_config['smtp_server']}
        - SMTP端口: {email_config['smtp_port']}
        - 发送邮箱: {email_config['email_from']}
        - 接收邮箱: {email_config['email_to']}
        - 启用状态: {'是' if email_config['enabled'] else '否'}
        """)
        
        st.markdown("---")
        st.markdown("**⚙️ 配置说明**")
        st.caption("""
        在 `.env` 文件中配置以下参数：
        ```
        EMAIL_ENABLED=true
        SMTP_SERVER=smtp.qq.com
        SMTP_PORT=587
        EMAIL_FROM=your_email@qq.com
        EMAIL_PASSWORD=your_authorization_code
        EMAIL_TO=receiver@example.com
        ```
        
        💡 提示：
        - 端口：587 (TLS) 或 465 (SSL)
        - 密码：使用邮箱授权码，不是登录密码
        - QQ邮箱授权码获取：设置 → 账户 → POP3/IMAP/SMTP → 生成授权码
        """)
        
        # 测试邮件按钮
        if email_config['configured']:
            if st.button("📧 发送测试邮件", type="primary", width='stretch'):
                with st.spinner("正在发送测试邮件..."):
                    success, message = notification_service.send_test_email()
                    if success:
                        st.success(f"✅ {message}")
                        st.balloons()
                    else:
                        st.error(f"❌ {message}")
        else:
            st.button("📧 发送测试邮件", type="primary", width='stretch', disabled=True)
            st.caption("请先在.env文件中配置邮件参数")
    
    with col2:
        st.subheader("📱 通知历史")
        
        # 显示所有通知（包括已发送和未发送的）
        all_notifications = monitor_db.get_all_recent_notifications(limit=10)
        
        if all_notifications:
            # 显示通知列表
            for notification in all_notifications:
                notification_type = notification['type']
                color_map = {
                    'entry': '🟢',
                    'take_profit': '🟡',
                    'stop_loss': '🔴',
                    'quant_trade': '🤖'
                }
                icon = color_map.get(notification_type, '🔵')
                
                # 显示已发送状态
                sent_status = "✅ 已发送" if notification.get('sent') else "⏳ 待发送"
                
                # 显示通知信息
                st.info(f"{icon} **{notification['symbol']}** - {notification['message']}\n\n_{notification['triggered_at']}_ | {sent_status}")
            
            # 显示待发送通知数量
            pending_count = len([n for n in all_notifications if not n.get('sent')])
            if pending_count > 0:
                st.warning(f"⚠️ 有 {pending_count} 条待发送通知")
            
            # 清空通知按钮
            col_a, col_b = st.columns(2)
            with col_a:
                if st.button("✅ 标记已读"):
                    monitor_db.mark_all_notifications_sent()
                    st.success("✅ 所有通知已标记为已读")
                    st.rerun()
            
            with col_b:
                if st.button("🗑️ 清空通知"):
                    monitor_db.clear_all_notifications()
                    st.success("✅ 通知已清空")
                    st.rerun()
        else:
            st.info("📭 暂无通知")

def display_miniqmt_status():
    """显示MiniQMT量化交易状态"""
    st.markdown("### 🤖 MiniQMT量化交易")
    
    qmt_status = get_miniqmt_status()
    
    col1, col2 = st.columns([1, 1])
    
    with col1:
        st.subheader("📊 连接状态")
        
        if qmt_status['enabled']:
            st.success("✅ MiniQMT已启用")
        else:
            st.warning("⚠️ MiniQMT未启用")
        
        if qmt_status['connected']:
            st.success("✅ 已连接到MiniQMT")
        else:
            st.info("⏸️ 未连接到MiniQMT")
        
        if qmt_status['account_id']:
            st.info(f"**账户ID**: {qmt_status['account_id']}")
        else:
            st.caption("未配置账户ID")
        
        st.markdown("---")
        st.markdown("**⚙️ 配置说明**")
        st.caption("""
        在 `config.py` 中配置以下参数：
        ```python
        MINIQMT_CONFIG = {
            'enabled': True,
            'account_id': 'your_account_id'
        }
        ```
        
        💡 提示：
        - 需要安装并启动MiniQMT客户端
        - 确保账户已登录
        - 预留接口已实现，可对接真实交易
        """)
    
    with col2:
        st.subheader("📈 量化统计")
        
        # 统计启用量化的股票
        stocks = monitor_db.get_monitored_stocks()
        quant_stocks = [s for s in stocks if s.get('quant_enabled', False)]
        
        st.metric("启用量化的股票", f"{len(quant_stocks)}/{len(stocks)}")
        
        if quant_stocks:
            st.markdown("**量化监测列表：**")
            for stock in quant_stocks:
                st.caption(f"🤖 {stock['symbol']} - {stock['name']}")
        else:
            st.info("暂无启用量化交易的股票")
        
        st.markdown("---")
        
        # 连接按钮
        if qmt_status['enabled'] and not qmt_status['connected']:
            if st.button("🔗 连接MiniQMT", type="primary", width='stretch'):
                success, msg = miniqmt.connect()
                if success:
                    st.success(f"✅ {msg}")
                else:
                    st.error(f"❌ {msg}")
                st.rerun()
        elif qmt_status['connected']:
            if st.button("🔌 断开连接", width='stretch'):
                if miniqmt.disconnect():
                    st.info("⏸️ 已断开MiniQMT连接")
                    st.rerun()

def display_scheduler_section():
    """显示定时调度配置区域"""
    st.markdown("---")
    st.markdown("### ⏰ 定时自动启动/关闭")
    
    # 获取调度器实例
    scheduler = monitor_service.get_scheduler()
    status = scheduler.get_status()
    
    # 状态显示
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        if status['scheduler_enabled']:
            st.success("🟢 定时已启用")
        else:
            st.info("⚪ 定时未启用")
    
    with col2:
        if status['scheduler_running']:
            st.success("🔄 调度器运行中")
        else:
            st.info("⏸️ 调度器未运行")
    
    with col3:
        if status['is_trading_day']:
            st.success(f"📅 交易日")
        else:
            st.info("📅 非交易日")
    
    with col4:
        if status['is_trading_time']:
            st.success("⏰ 交易时间内")
        else:
            st.info(f"⏰ {status['next_trading_time']}")
    
    # 配置设置
    with st.expander("⚙️ 定时调度设置", expanded=False):
        col1, col2 = st.columns([1, 1])
        
        with col1:
            st.subheader("📊 市场选择")
            
            market = st.selectbox(
                "选择市场",
                ["CN", "US", "HK"],
                index=["CN", "US", "HK"].index(scheduler.config.get('market', 'CN')),
                help="CN=中国A股, US=美股, HK=港股"
            )
            
            market_names = {
                "CN": "中国A股",
                "US": "美股",
                "HK": "港股"
            }
            st.info(f"**当前市场**: {market_names.get(market, market)}")
            
            # 显示交易时间
            trading_hours = scheduler.config['trading_hours'].get(market, [])
            st.markdown("**📅 交易时间：**")
            for i, period in enumerate(trading_hours, 1):
                st.caption(f"时段{i}: {period['start']} - {period['end']}")
            
            # 交易日设置
            st.markdown("**📅 交易日设置**")
            trading_days = st.multiselect(
                "选择交易日",
                options=[1, 2, 3, 4, 5, 6, 7],
                default=scheduler.config.get('trading_days', [1, 2, 3, 4, 5]),
                format_func=lambda x: ["周一", "周二", "周三", "周四", "周五", "周六", "周日"][x-1],
                help="选择哪些日期为交易日"
            )
        
        with col2:
            st.subheader("⚙️ 调度参数")
            
            enabled = st.checkbox(
                "启用定时调度",
                value=scheduler.config.get('enabled', False),
                help="启用后将在交易时间自动启动监测服务"
            )
            
            auto_stop = st.checkbox(
                "收盘后自动停止",
                value=scheduler.config.get('auto_stop', True),
                help="在交易时间结束后自动停止监测服务"
            )
            
            pre_market_minutes = st.slider(
                "提前启动(分钟)",
                min_value=0,
                max_value=30,
                value=scheduler.config.get('pre_market_minutes', 5),
                help="在开盘前提前多少分钟启动"
            )
            
            post_market_minutes = st.slider(
                "延后停止(分钟)",
                min_value=0,
                max_value=30,
                value=scheduler.config.get('post_market_minutes', 5),
                help="在收盘后延后多少分钟停止"
            )
            
            st.markdown("---")
            
            # 说明信息
            st.info("""
            **💡 使用说明：**
            - 启用定时调度后，系统将在交易时间自动启动监测
            - 非交易时间或非交易日将自动停止监测（如启用自动停止）
            - 调度器独立运行，不影响手动启动/停止
            - 支持中国A股、美股、港股交易时间
            """)
        
        # 保存按钮
        col1, col2, col3 = st.columns([1, 1, 1])
        
        with col1:
            if st.button("💾 保存设置", type="primary", width='stretch'):
                try:
                    # 更新配置
                    scheduler.update_config(
                        enabled=enabled,
                        market=market,
                        trading_days=trading_days,
                        auto_stop=auto_stop,
                        pre_market_minutes=pre_market_minutes,
                        post_market_minutes=post_market_minutes
                    )
                    
                    st.success("✅ 设置已保存")
                    st.balloons()
                    time.sleep(1)
                    st.rerun()
                except Exception as e:
                    st.error(f"❌ 保存失败: {e}")
        
        with col2:
            if status['scheduler_running']:
                if st.button("⏹️ 停止调度器", width='stretch'):
                    scheduler.stop_scheduler()
                    st.info("⏸️ 调度器已停止")
                    time.sleep(0.5)
                    st.rerun()
            else:
                if enabled:
                    if st.button("▶️ 启动调度器", type="secondary", width='stretch'):
                        scheduler.start_scheduler()
                        st.success("✅ 调度器已启动")
                        time.sleep(0.5)
                        st.rerun()
                else:
                    st.button("▶️ 启动调度器", width='stretch', disabled=True)
                    st.caption("请先启用定时调度")
        
        with col3:
            if st.button("🔄 刷新状态", width='stretch'):
                st.rerun()

def get_monitor_summary():
    """获取监测摘要信息"""
    stocks = monitor_db.get_monitored_stocks()
    
    summary = {
        'total_stocks': len(stocks),
        'stocks_needing_update': len(monitor_service.get_stocks_needing_update()),
        'pending_notifications': len(monitor_db.get_pending_notifications()),
        'active_monitoring': monitor_service.running
    }
    
    return summary
