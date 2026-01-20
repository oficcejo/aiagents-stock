#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
主力选股批量分析历史记录UI模块
"""

import streamlit as st
import pandas as pd
from datetime import datetime
from main_force_batch_db import batch_db


def display_batch_history():
    """显示批量分析历史记录"""
    
    # 返回按钮
    col_back, col_stats = st.columns([1, 4])
    with col_back:
        if st.button("← 返回主页"):
            st.session_state.main_force_view_history = False
            st.rerun()
    
    st.markdown("## 📚 主力选股批量分析历史记录")
    st.markdown("---")
    
    # 获取统计信息
    try:
        stats = batch_db.get_statistics()
        
        # 显示统计指标
        col1, col2, col3, col4, col5 = st.columns(5)
        with col1:
            st.metric("总记录数", f"{stats['total_records']} 条")
        with col2:
            st.metric("分析股票总数", f"{stats['total_stocks_analyzed']} 只")
        with col3:
            st.metric("成功分析", f"{stats['total_success']} 只")
        with col4:
            st.metric("成功率", f"{stats['success_rate']}%")
        with col5:
            st.metric("平均耗时", f"{stats['average_time']:.1f}秒")
        
        st.markdown("---")
        
    except Exception as e:
        st.warning(f"⚠️ 无法获取统计信息: {str(e)}")
        import traceback
        st.code(traceback.format_exc())
    
    # 获取历史记录
    try:
        # 添加调试信息（使用expander折叠，避免影响正常显示）
        with st.expander("🔍 调试信息", expanded=False):
            st.caption(f"📊 数据库路径: {batch_db.db_path}")
            import os
            if os.path.exists(batch_db.db_path):
                db_size = os.path.getsize(batch_db.db_path)
                st.caption(f"📊 数据库文件大小: {db_size} 字节")
            else:
                st.warning(f"⚠️ 数据库文件不存在: {batch_db.db_path}")
        
        history_records = batch_db.get_all_history(limit=50)
        
        if not history_records:
            st.info("📝 暂无批量分析历史记录")
            st.caption(f"💡 数据库文件位置: {batch_db.db_path}")
            st.caption("💡 提示: 如果您已经运行过批量分析，请确认数据是否正确保存到数据库")
            
            # 提供手动检查数据库的按钮
            if st.button("🔍 检查数据库状态"):
                import os
                import sqlite3
                
                with st.expander("📊 数据库详细信息", expanded=True):
                    st.write(f"**数据库路径**: {batch_db.db_path}")
                    st.write(f"**文件存在**: {'✅ 是' if os.path.exists(batch_db.db_path) else '❌ 否'}")
                    
                    if os.path.exists(batch_db.db_path):
                        db_size = os.path.getsize(batch_db.db_path)
                        st.write(f"**文件大小**: {db_size} 字节")
                        
                        # 尝试连接数据库并查询表
                        try:
                            conn = sqlite3.connect(batch_db.db_path)
                            cursor = conn.cursor()
                            
                            # 检查表是否存在
                            cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='batch_analysis_history'")
                            table_exists = cursor.fetchone() is not None
                            st.write(f"**表存在**: {'✅ 是' if table_exists else '❌ 否'}")
                            
                            if table_exists:
                                # 查询记录数
                                cursor.execute("SELECT COUNT(*) FROM batch_analysis_history")
                                count = cursor.fetchone()[0]
                                st.write(f"**记录数**: {count} 条")
                                
                                if count > 0:
                                    # 显示最近几条记录的信息
                                    cursor.execute("""
                                        SELECT id, analysis_date, batch_count, success_count, failed_count 
                                        FROM batch_analysis_history 
                                        ORDER BY created_at DESC 
                                        LIMIT 5
                                    """)
                                    rows = cursor.fetchall()
                                    st.write("**最近5条记录**:")
                                    for row in rows:
                                        st.write(f"- ID: {row[0]}, 时间: {row[1]}, 数量: {row[2]}, 成功: {row[3]}, 失败: {row[4]}")
                            else:
                                st.warning("⚠️ 表 'batch_analysis_history' 不存在，可能是数据库未初始化")
                            
                            conn.close()
                        except Exception as e:
                            st.error(f"❌ 查询数据库时出错: {str(e)}")
                    else:
                        st.warning("⚠️ 数据库文件不存在，可能是首次运行或数据库路径配置错误")
            
            return
        
        st.markdown(f"### 📋 最近 {len(history_records)} 条记录")
        
        # 显示每条记录
        for idx, record in enumerate(history_records):
            with st.expander(
                f"🔍 {record['analysis_date']} | "
                f"共{record['batch_count']}只 | "
                f"成功{record['success_count']}只 | "
                f"{record['analysis_mode']} | "
                f"耗时{record['total_time']/60:.1f}分钟",
                expanded=(idx == 0)  # 第一条默认展开
            ):
                # 记录基本信息
                col1, col2, col3, col4 = st.columns(4)
                with col1:
                    st.write(f"**分析时间**: {record['analysis_date']}")
                with col2:
                    st.write(f"**分析模式**: {record['analysis_mode']}")
                with col3:
                    st.write(f"**总数**: {record['batch_count']} 只")
                with col4:
                    st.write(f"**耗时**: {record['total_time']/60:.1f} 分钟")
                
                col5, col6, col7, col8 = st.columns(4)
                with col5:
                    st.metric("✅ 成功", record['success_count'])
                with col6:
                    st.metric("❌ 失败", record['failed_count'])
                with col7:
                    success_rate = (record['success_count'] / record['batch_count'] * 100) if record['batch_count'] > 0 else 0
                    st.metric("成功率", f"{success_rate:.1f}%")
                with col8:
                    avg_time = record['total_time'] / record['batch_count'] if record['batch_count'] > 0 else 0
                    st.metric("平均耗时", f"{avg_time:.1f}秒")
                
                st.markdown("---")
                
                # 成功的股票
                results = record.get('results', [])
                success_results = [r for r in results if r.get('success', False)]
                failed_results = [r for r in results if not r.get('success', False)]
                
                if success_results:
                    st.markdown(f"#### ✅ 成功分析的股票 ({len(success_results)} 只)")
                    
                    # 构建结果表格
                    table_data = []
                    for r in success_results:
                        stock_info = r.get('stock_info', {})
                        final_decision = r.get('final_decision', {})
                        
                        table_data.append({
                            '代码': r.get('symbol', 'N/A'),
                            '名称': stock_info.get('name', stock_info.get('股票名称', 'N/A')),
                            '评级': final_decision.get('rating', final_decision.get('investment_rating', 'N/A')),
                            '信心度': final_decision.get('confidence_level', 'N/A'),
                            '进场区间': final_decision.get('entry_range', 'N/A'),
                            '止盈位': final_decision.get('take_profit', 'N/A'),
                            '止损位': final_decision.get('stop_loss', 'N/A')
                        })
                    
                    df = pd.DataFrame(table_data)
                    
                    # 类型统一，避免Arrow序列化错误
                    numeric_cols = ['信心度', '止盈位', '止损位']
                    for col in numeric_cols:
                        if col in df.columns:
                            df[col] = pd.to_numeric(df[col], errors='coerce')

                    text_cols = ['代码', '名称', '评级', '进场区间']
                    for col in text_cols:
                        if col in df.columns:
                            df[col] = df[col].astype(str)
                    
                    st.dataframe(df, width='content')
                    
                    # 显示详细分析（可展开）
                    with st.expander("📊 查看详细分析报告"):
                        for r in success_results:
                            stock_info = r.get('stock_info', {})
                            final_decision = r.get('final_decision', {})
                            
                            st.markdown(f"### {r.get('symbol', 'N/A')} - {stock_info.get('name', stock_info.get('股票名称', 'N/A'))}")
                            
                            # 投资建议
                            st.markdown("#### 💡 投资建议")
                            st.write(final_decision.get('operation_advice', final_decision.get('investment_advice', '无')))
                            
                            # 风险提示
                            st.markdown("#### ⚠️ 风险提示")
                            st.write(final_decision.get('risk_warning', '无'))
                            
                            st.markdown("---")
                
                # 失败的股票
                if failed_results:
                    st.markdown(f"#### ❌ 分析失败的股票 ({len(failed_results)} 只)")
                    
                    fail_data = []
                    for r in failed_results:
                        fail_data.append({
                            '代码': r.get('symbol', 'N/A'),
                            '错误原因': r.get('error', '未知错误')
                        })
                    
                    df_fail = pd.DataFrame(fail_data)
                    st.dataframe(df_fail, width='content')
                
                # 操作按钮
                col_del, col_reload = st.columns([1, 1])
                with col_del:
                    if st.button(f"🗑️ 删除此记录", key=f"del_{record['id']}"):
                        if batch_db.delete_record(record['id']):
                            st.success("✅ 删除成功")
                            st.rerun()
                        else:
                            st.error("❌ 删除失败")
                
                with col_reload:
                    if st.button(f"🔄 加载到当前结果", key=f"reload_{record['id']}"):
                        # 将历史记录加载到session_state
                        st.session_state.main_force_batch_results = {
                            "results": record['results'],
                            "total": record['batch_count'],
                            "success": record['success_count'],
                            "failed": record['failed_count'],
                            "elapsed_time": record['total_time'],
                            "analysis_mode": record['analysis_mode']
                        }
                        st.session_state.main_force_view_history = False
                        st.success("✅ 已加载到当前结果，返回主页查看")
                        st.rerun()
    
    except Exception as e:
        st.error(f"❌ 获取历史记录失败: {str(e)}")
        import traceback
        st.code(traceback.format_exc())

