#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
持仓管理UI模块
提供持仓股票的增删改查、批量分析、定时任务管理界面
"""

import streamlit as st
import pandas as pd
from datetime import datetime
from typing import List, Dict
import time

from portfolio_manager import portfolio_manager
from portfolio_scheduler import portfolio_scheduler


def display_portfolio_manager():
    """显示持仓管理主界面"""
    
    st.markdown("## 📊 持仓定时分析")
    st.markdown("---")
    
    # 创建标签页
    tab1, tab2, tab3, tab4 = st.tabs([
        "📝 持仓管理", 
        "🔄 批量分析", 
        "⏰ 定时任务", 
        "📈 分析历史"
    ])
    
    with tab1:
        display_portfolio_stocks()
    
    with tab2:
        display_batch_analysis()
    
    with tab3:
        display_scheduler_management()
    
    with tab4:
        display_analysis_history()


def display_portfolio_stocks():
    """显示持仓股票列表和管理"""
    
    st.markdown("### 📝 持仓股票管理")
    
    # 添加新股票表单
    with st.expander("➕ 添加持仓股票", expanded=False):
        display_add_stock_form()
    
    # 获取所有持仓股票
    stocks = portfolio_manager.get_all_stocks()
    
    if not stocks:
        st.info("暂无持仓股票，请添加股票代码开始管理。")
        return
    
    # 显示统计
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("持仓股票数", len(stocks))
    with col2:
        auto_monitor_count = sum(1 for s in stocks if s.get("auto_monitor"))
        st.metric("启用自动监测", auto_monitor_count)
    with col3:
        total_cost = sum(
            s.get("cost_price", 0) * s.get("quantity", 0) 
            for s in stocks 
            if s.get("cost_price") and s.get("quantity")
        )
        st.metric("总持仓成本", f"¥{total_cost:,.2f}")
    
    st.markdown("---")
    
    # 显示股票列表（卡片式布局）
    for stock in stocks:
        display_stock_card(stock)


def display_stock_card(stock: Dict):
    """显示单个股票卡片"""
    
    stock_id = stock.get("id")  # 获取股票ID
    code = stock.get("code", "")
    name = stock.get("name", "")
    cost_price = stock.get("cost_price")
    quantity = stock.get("quantity")
    note = stock.get("note", "")
    auto_monitor = stock.get("auto_monitor", True)
    created_at = stock.get("created_at", "")
    
    # 创建卡片
    with st.container():
        col1, col2, col3, col4 = st.columns([3, 2, 2, 2])
        
        with col1:
            st.markdown(f"**{code}** {name}")
            if note:
                st.caption(f"备注: {note}")
        
        with col2:
            if cost_price and quantity:
                st.write(f"成本: ¥{cost_price:.2f}")
                st.caption(f"数量: {quantity}股")
            else:
                st.caption("未设置持仓")
        
        with col3:
            if auto_monitor:
                st.success("🔔 自动监测")
            else:
                st.info("🔕 不监测")
        
        with col4:
            col_edit, col_del = st.columns(2)
            with col_edit:
                if st.button("✏️", key=f"edit_{code}", help="编辑"):
                    st.session_state[f"editing_{code}"] = True
                    st.rerun()
            with col_del:
                if st.button("🗑️", key=f"del_{code}", help="删除"):
                    portfolio_manager.delete_stock(stock_id)  # 使用stock_id而不是code
                    st.success(f"已删除 {code}")
                    time.sleep(0.5)
                    st.rerun()
        
        # 编辑表单（如果处于编辑状态）
        if st.session_state.get(f"editing_{code}"):
            with st.form(key=f"edit_form_{code}"):
                st.markdown(f"#### 编辑 {code}")
                
                col_a, col_b = st.columns(2)
                with col_a:
                    new_cost = st.number_input(
                        "成本价", 
                        value=cost_price if cost_price else 0.0, 
                        min_value=0.0, 
                        step=0.01
                    )
                    new_quantity = st.number_input(
                        "持仓数量", 
                        value=quantity if quantity else 0, 
                        min_value=0, 
                        step=100
                    )
                
                with col_b:
                    new_note = st.text_area("备注", value=note, height=80)
                    new_auto_monitor = st.checkbox("自动同步到监测", value=auto_monitor)
                
                col_submit, col_cancel = st.columns(2)
                with col_submit:
                    if st.form_submit_button("保存", type="primary"):
                        portfolio_manager.update_stock(
                            stock_id,  # 使用stock_id而不是code
                            cost_price=new_cost if new_cost > 0 else None,
                            quantity=new_quantity if new_quantity > 0 else None,
                            note=new_note,
                            auto_monitor=new_auto_monitor
                        )
                        del st.session_state[f"editing_{code}"]
                        st.success("更新成功！")
                        time.sleep(0.5)
                        st.rerun()
                
                with col_cancel:
                    if st.form_submit_button("取消"):
                        del st.session_state[f"editing_{code}"]
                        st.rerun()
        
        st.markdown("---")


def display_add_stock_form():
    """显示添加股票表单"""
    
    with st.form(key="add_stock_form"):
        col1, col2 = st.columns(2)
        
        with col1:
            code = st.text_input(
                "股票代码*", 
                placeholder="例如: 600519.SH 或 000001.SZ",
                help="必填，格式：代码.市场（SH/SZ/HK/US）"
            )
            name = st.text_input(
                "股票名称", 
                placeholder="例如: 贵州茅台",
                help="可选，留空将自动获取"
            )
        
        with col2:
            cost_price = st.number_input(
                "成本价", 
                min_value=0.0, 
                step=0.01,
                help="可选，用于计算收益"
            )
            quantity = st.number_input(
                "持仓数量", 
                min_value=0, 
                step=100,
                help="可选，单位：股"
            )
        
        note = st.text_area("备注", height=80, placeholder="可选，记录买入理由等信息")
        auto_monitor = st.checkbox("分析后自动同步到监测", value=True)
        
        if st.form_submit_button("➕ 添加股票", type="primary"):
            if not code:
                st.error("请输入股票代码")
            else:
                try:
                    portfolio_manager.add_stock(
                        code=code.strip().upper(),
                        name=name.strip() if name else None,
                        cost_price=cost_price if cost_price > 0 else None,
                        quantity=quantity if quantity > 0 else None,
                        note=note.strip() if note else None,
                        auto_monitor=auto_monitor
                    )
                    st.success(f"✅ 已添加 {code} 到持仓列表")
                    time.sleep(0.5)
                    st.rerun()
                except Exception as e:
                    st.error(f"添加失败: {str(e)}")


def display_batch_analysis():
    """显示批量分析功能"""
    
    st.markdown("### 🔄 批量分析持仓股票")
    
    stocks = portfolio_manager.get_all_stocks()
    
    if not stocks:
        st.warning("暂无持仓股票，请先添加股票。")
        return
    
    # 分析选项
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.metric("持仓股票数", len(stocks))
    
    with col2:
        analysis_mode = st.selectbox(
            "分析模式",
            options=["sequential", "parallel"],
            format_func=lambda x: "顺序分析" if x == "sequential" else "并行分析",
            help="顺序分析较慢但稳定，并行分析更快但消耗更多资源"
        )
    
    with col3:
        if analysis_mode == "parallel":
            max_workers = st.number_input(
                "并行线程数",
                min_value=2,
                max_value=10,
                value=3,
                help="同时分析的股票数量"
            )
        else:
            max_workers = 1
    
    st.markdown("---")
    
    # 同步和通知选项
    col_a, col_b = st.columns(2)
    
    with col_a:
        auto_sync = st.checkbox(
            "自动同步到监测",
            value=True,
            help="分析完成后自动将评级结果同步到实时监测列表"
        )
    
    with col_b:
        send_notification = st.checkbox(
            "发送完成通知",
            value=True,
            help="通过邮件或Webhook发送分析完成通知"
        )
    
    # 立即分析按钮
    if st.button("🚀 立即开始分析", type="primary", use_container_width=True):
        with st.spinner("正在批量分析持仓股票..."):
            # 显示进度
            progress_bar = st.progress(0)
            status_text = st.empty()
            
            # 执行批量分析
            try:
                # 定义进度回调函数
                def update_progress(current, total, code, status):
                    progress_bar.progress(current / total)
                    status_map = {
                        "analyzing": "正在分析",
                        "success": "✅ 完成",
                        "failed": "❌ 失败",
                        "error": "⚠️ 错误"
                    }
                    status_text.text(f"{status_map.get(status, '处理中')} {code} ({current}/{total})")
                
                result = portfolio_manager.batch_analyze_portfolio(
                    mode=analysis_mode,
                    max_workers=max_workers,
                    progress_callback=update_progress
                )
                
                # 清除进度显示
                progress_bar.empty()
                status_text.empty()
                
                # 显示结果
                st.success(f"✅ 批量分析完成！")
                
                col_r1, col_r2, col_r3, col_r4 = st.columns(4)
                with col_r1:
                    st.metric("总计", result.get("total", 0))
                with col_r2:
                    st.metric("成功", result.get("succeeded", 0))
                with col_r3:
                    st.metric("失败", result.get("failed", 0))
                with col_r4:
                    st.metric("耗时", f"{result.get('elapsed_time', 0):.1f}秒")
                
                # 保存分析结果到数据库
                saved_ids = portfolio_manager.save_analysis_results(result)
                st.info(f"💾 已保存 {len(saved_ids)} 条分析记录到数据库")
                
                # 同步到监测
                sync_result = None  # 初始化同步结果
                if auto_sync:
                    with st.spinner("正在同步到监测列表..."):
                        from monitor_db import monitor_db
                        
                        # 准备同步数据
                        monitors_to_sync = []
                        for item in result.get("results", []):
                            # 检查分析是否成功
                            if not item.get("result", {}).get("success"):
                                continue
                            
                            code = item["code"]
                            stock = portfolio_manager.db.get_stock_by_code(code)
                            
                            # 只同步启用了自动监测的股票
                            if not stock or not stock.get("auto_monitor"):
                                continue
                            
                            analysis_result = item["result"]
                            stock_info = analysis_result.get("stock_info", {})
                            final_decision = analysis_result.get("final_decision", {})
                            
                            # 从final_decision中提取数据
                            rating = final_decision.get("rating", "持有")
                            entry_range = final_decision.get("entry_range", "")
                            take_profit_str = final_decision.get("take_profit", "")
                            stop_loss_str = final_decision.get("stop_loss", "")
                            
                            # 解析进场区间（格式如"10.5-12.3"）
                            entry_min, entry_max = None, None
                            if entry_range and isinstance(entry_range, str) and "-" in entry_range:
                                try:
                                    parts = entry_range.split("-")
                                    entry_min = float(parts[0].strip())
                                    entry_max = float(parts[1].strip())
                                except:
                                    pass
                            
                            # 解析止盈止损（提取数字）
                            import re
                            take_profit, stop_loss = None, None
                            if take_profit_str:
                                try:
                                    numbers = re.findall(r'\d+\.?\d*', str(take_profit_str))
                                    if numbers:
                                        take_profit = float(numbers[0])
                                except:
                                    pass
                            
                            if stop_loss_str:
                                try:
                                    numbers = re.findall(r'\d+\.?\d*', str(stop_loss_str))
                                    if numbers:
                                        stop_loss = float(numbers[0])
                                except:
                                    pass
                            
                            # 只有当所有必需字段都有效时才添加
                            if entry_min and entry_max and take_profit and stop_loss:
                                monitors_to_sync.append({
                                    "code": code,
                                    "name": stock_info.get("name", stock.get("name", "")),
                                    "rating": rating,
                                    "entry_min": entry_min,
                                    "entry_max": entry_max,
                                    "take_profit": take_profit,
                                    "stop_loss": stop_loss
                                })
                        
                        if monitors_to_sync:
                            sync_result = monitor_db.batch_add_or_update_monitors(monitors_to_sync)
                            st.info(f"📊 监测同步: 新增 {sync_result.get('added', 0)} 只, 更新 {sync_result.get('updated', 0)} 只")
                        else:
                            sync_result = {"added": 0, "updated": 0, "failed": 0, "total": 0}
                            st.info("📊 无需同步监测列表（无启用自动监测的股票）")
                
                # 发送通知
                if send_notification:
                    from notification_service import notification_service
                    notification_service.send_portfolio_analysis_notification(
                        result, 
                        sync_result if auto_sync else None
                    )
                    st.info("✉️ 已发送完成通知")
                
                # 显示详细结果
                st.markdown("### 分析结果详情")
                for item in result.get("results", []):
                    display_analysis_result_card(item)
                
            except Exception as e:
                st.error(f"批量分析失败: {str(e)}")
                import traceback
                st.code(traceback.format_exc())


def display_analysis_result_card(item: Dict):
    """显示单个分析结果卡片"""
    
    code = item.get("code", "")
    result = item.get("result", {})
    
    # 检查分析是否成功
    if result.get("success"):
        final_decision = result.get("final_decision", {})
        stock_info = result.get("stock_info", {})
        
        # 使用正确的字段名
        rating = final_decision.get("rating", "未知")
        confidence = final_decision.get("confidence_level", "N/A")
        target_price = final_decision.get("target_price", "N/A")
        entry_range = final_decision.get("entry_range", "N/A")
        take_profit = final_decision.get("take_profit", "N/A")
        stop_loss = final_decision.get("stop_loss", "N/A")
        
        # 评级颜色
        if "强烈买入" in rating or "买入" in rating:
            rating_color = "🟢"
        elif "卖出" in rating:
            rating_color = "🔴"
        else:
            rating_color = "🟡"
        
        with st.expander(f"{rating_color} {code} {stock_info.get('name', '')} - {rating} (信心度: {confidence})"):
            col1, col2 = st.columns(2)
            
            with col1:
                st.markdown("**进出场位置**")
                st.write(f"进场区间: {entry_range}")
                st.write(f"目标价: {target_price}")
            
            with col2:
                st.markdown("**风控位置**")
                st.write(f"止盈位: {take_profit}")
                st.write(f"止损位: {stop_loss}")
            
            # 投资建议
            advice = final_decision.get("advice", "")
            if advice:
                st.markdown("**投资建议**")
                st.info(advice)
    
    else:
        # 分析失败
        error = result.get("error", "未知错误")
        with st.expander(f"🔴 {code} - 分析失败"):
            st.error(f"错误: {error}")


def display_scheduler_management():
    """显示定时任务管理"""
    
    st.markdown("### ⏰ 定时任务管理")
    
    # 调度器状态
    is_running = portfolio_scheduler.is_running()
    schedule_times = portfolio_scheduler.get_schedule_times()
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        if is_running:
            st.success("🟢 调度器运行中")
        else:
            st.error("🔴 调度器已停止")
    
    with col2:
        st.info(f"⏰ 定时数量: {len(schedule_times)}个")
    
    with col3:
        next_run = portfolio_scheduler.get_next_run_time()
        if next_run:
            st.info(f"⏭️ 下次运行: {next_run}")
        else:
            st.info("⏭️ 下次运行: 未设置")
    
    st.markdown("---")
    
    # 显示所有定时时间点
    st.markdown("#### 📋 已配置的定时时间")
    
    if schedule_times:
        cols_per_row = 4
        for i in range(0, len(schedule_times), cols_per_row):
            cols = st.columns(cols_per_row)
            for j, col in enumerate(cols):
                idx = i + j
                if idx < len(schedule_times):
                    time_str = schedule_times[idx]
                    with col:
                        col_time, col_del = st.columns([3, 1])
                        with col_time:
                            st.info(f"⏰ {time_str}")
                        with col_del:
                            if st.button("🗑️", key=f"del_time_{idx}", help="删除"):
                                if len(schedule_times) > 1:
                                    portfolio_scheduler.remove_schedule_time(time_str)
                                    st.success(f"已删除 {time_str}")
                                    time.sleep(0.3)
                                    st.rerun()
                                else:
                                    st.error("至少保留一个定时时间")
    else:
        st.warning("暂无定时配置")
    
    # 添加新的定时时间
    with st.expander("➕ 添加定时时间", expanded=False):
        col_input, col_add = st.columns([3, 1])
        with col_input:
            new_time = st.time_input(
                "选择时间",
                value=datetime.strptime("15:05", "%H:%M").time(),
                help="添加新的每日分析时间"
            )
        with col_add:
            st.write("")  # 占位，对齐按钮
            st.write("")
            if st.button("➕ 添加", type="primary", use_container_width=True):
                time_str = new_time.strftime("%H:%M")
                if portfolio_scheduler.add_schedule_time(time_str):
                    st.success(f"已添加 {time_str}")
                    time.sleep(0.3)
                    st.rerun()
                else:
                    st.warning(f"{time_str} 已存在")
    
    st.markdown("---")
    
    # 任务配置
    with st.form(key="scheduler_config_form"):
        st.markdown("#### 分析配置")
        
        col_a, col_b = st.columns(2)
        
        with col_a:
            analysis_mode = st.selectbox(
                "分析模式",
                options=["sequential", "parallel"],
                format_func=lambda x: "顺序分析" if x == "sequential" else "并行分析",
                index=0 if portfolio_scheduler.analysis_mode == "sequential" else 1
            )
        
        with col_b:
            max_workers = st.number_input(
                "并行线程数",
                min_value=2,
                max_value=10,
                value=portfolio_scheduler.max_workers,
                disabled=(analysis_mode == "sequential"),
                help="仅在并行模式下生效"
            )
        
        auto_sync_monitor = st.checkbox(
            "自动同步到监测", 
            value=portfolio_scheduler.auto_monitor_sync,
            help="分析完成后自动将结果同步到实时监测列表"
        )
        send_notification = st.checkbox(
            "发送完成通知", 
            value=portfolio_scheduler.notification_enabled,
            help="通过邮件或Webhook发送分析结果"
        )
        
        col_update, col_reset = st.columns(2)
        
        with col_update:
            if st.form_submit_button("💾 更新配置", type="primary"):
                portfolio_scheduler.update_config(
                    analysis_mode=analysis_mode,
                    max_workers=max_workers if analysis_mode == "parallel" else 1,
                    auto_sync_monitor=auto_sync_monitor,
                    send_notification=send_notification
                )
                st.success("配置已更新！")
                time.sleep(0.5)
                st.rerun()
        
        with col_reset:
            if st.form_submit_button("🔄 恢复默认"):
                portfolio_scheduler.set_schedule_times(["09:30"])
                portfolio_scheduler.update_config(
                    analysis_mode="sequential",
                    max_workers=1,
                    auto_sync_monitor=True,
                    send_notification=True
                )
                st.success("已恢复默认配置！")
                time.sleep(0.5)
                st.rerun()
    
    st.markdown("---")
    
    # 控制按钮
    col_btn1, col_btn2, col_btn3 = st.columns(3)
    
    with col_btn1:
        if is_running:
            if st.button("⏹️ 停止调度器", type="secondary", use_container_width=True):
                portfolio_scheduler.stop_scheduler()
                st.success("调度器已停止")
                time.sleep(0.5)
                st.rerun()
        else:
            if st.button("▶️ 启动调度器", type="primary", use_container_width=True):
                portfolio_scheduler.start_scheduler()
                st.success("调度器已启动")
                time.sleep(0.5)
                st.rerun()
    
    with col_btn2:
        if st.button("🚀 立即执行一次", type="primary", use_container_width=True):
            with st.spinner("正在执行持仓分析..."):
                try:
                    portfolio_scheduler.run_analysis_now()
                    st.success("执行完成！请查看分析历史。")
                except Exception as e:
                    st.error(f"执行失败: {str(e)}")
    
    with col_btn3:
        if st.button("🔄 刷新状态", use_container_width=True):
            st.rerun()


def display_analysis_history():
    """显示分析历史"""
    
    st.markdown("### 📈 分析历史记录")
    
    stocks = portfolio_manager.get_all_stocks()
    
    if not stocks:
        st.info("暂无持仓股票")
        return
    
    # 选择股票
    stock_codes = [s["code"] for s in stocks]
    selected_code = st.selectbox(
        "选择股票",
        options=["全部"] + stock_codes,
        help="查看特定股票的分析历史"
    )
    
    # 获取历史记录
    if selected_code == "全部":
        # 获取所有股票的最新历史
        all_history = []
        for stock in stocks:
            stock_id = stock["id"]
            history = portfolio_manager.db.get_latest_analysis_history(stock_id, limit=5)
            for h in history:
                h["code"] = stock["code"]
                h["name"] = stock["name"]
            all_history.extend(history)
        
        # 按时间排序
        all_history.sort(key=lambda x: x.get("analysis_time", ""), reverse=True)
        history_list = all_history[:20]  # 只显示最近20条
    else:
        # 获取指定股票的历史
        stock = next((s for s in stocks if s["code"] == selected_code), None)
        if stock:
            history_list = portfolio_manager.db.get_latest_analysis_history(
                stock["id"], limit=20
            )
            for h in history_list:
                h["code"] = stock["code"]
                h["name"] = stock["name"]
        else:
            history_list = []
    
    if not history_list:
        st.info(f"暂无分析历史记录")
        return
    
    # 显示历史记录
    st.markdown(f"共 {len(history_list)} 条记录")
    
    for record in history_list:
        display_history_record(record)


def display_history_record(record: Dict):
    """显示单条历史记录"""
    
    code = record.get("code", "")
    name = record.get("name", "")
    analysis_time = record.get("analysis_time", "")
    rating = record.get("rating", "未知")
    confidence = record.get("confidence", 0)
    current_price = record.get("current_price")
    target_price = record.get("target_price")
    entry_min = record.get("entry_min")
    entry_max = record.get("entry_max")
    take_profit = record.get("take_profit")
    stop_loss = record.get("stop_loss")
    summary = record.get("summary", "")
    
    # 评级颜色
    if "强烈买入" in rating or "买入" in rating:
        rating_icon = "🟢"
    elif "卖出" in rating:
        rating_icon = "🔴"
    else:
        rating_icon = "🟡"
    
    with st.expander(
        f"{rating_icon} {code} {name} - {rating} | {analysis_time}",
        expanded=False
    ):
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.markdown("**价格信息**")
            if current_price:
                st.write(f"当时价格: ¥{current_price:.2f}")
            if target_price:
                st.write(f"目标价: ¥{target_price:.2f}")
        
        with col2:
            st.markdown("**进场区间**")
            if entry_min and entry_max:
                st.write(f"¥{entry_min:.2f} ~ ¥{entry_max:.2f}")
        
        with col3:
            st.markdown("**风控位置**")
            if take_profit:
                st.write(f"止盈: ¥{take_profit:.2f}")
            if stop_loss:
                st.write(f"止损: ¥{stop_loss:.2f}")
        
        if summary:
            st.markdown("**分析摘要**")
            st.info(summary)
        
        st.caption(f"置信度: {confidence}%")

