#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
低价擒牛策略监控模块
监控持仓股票的卖出信号
"""

import sqlite3
import pandas as pd
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
import logging
import os


class LowPriceBullMonitor:
    """低价擒牛策略监控器"""
    
    def __init__(self, db_path: str = "low_price_bull_monitor.db"):
        """
        初始化监控器
        
        Args:
            db_path: 数据库文件路径
        """
        self.logger = logging.getLogger(__name__)
        self.db_path = db_path
        self._init_database()
    
    def _init_database(self):
        """初始化数据库"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # 创建监控列表表
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS monitored_stocks (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                stock_code TEXT NOT NULL,
                stock_name TEXT NOT NULL,
                buy_price REAL NOT NULL,
                buy_date TEXT NOT NULL,
                holding_days INTEGER DEFAULT 0,
                status TEXT DEFAULT 'holding',
                add_time TEXT NOT NULL,
                remove_time TEXT,
                remove_reason TEXT,
                UNIQUE(stock_code, status)
            )
        """)
        
        # 创建卖出提醒表
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS sell_alerts (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                stock_code TEXT NOT NULL,
                stock_name TEXT NOT NULL,
                alert_type TEXT NOT NULL,
                alert_reason TEXT NOT NULL,
                current_price REAL,
                ma5 REAL,
                ma20 REAL,
                holding_days INTEGER,
                alert_time TEXT NOT NULL,
                is_sent INTEGER DEFAULT 0
            )
        """)
        
        conn.commit()
        conn.close()
        
        self.logger.info("低价擒牛监控数据库初始化完成")
    
    def add_stock(self, stock_code: str, stock_name: str, buy_price: float, 
                  buy_date: str = None) -> Tuple[bool, str]:
        """
        添加股票到监控列表
        
        Args:
            stock_code: 股票代码（不含后缀）
            stock_name: 股票名称
            buy_price: 买入价格
            buy_date: 买入日期（格式：YYYY-MM-DD）
            
        Returns:
            (是否成功, 消息)
        """
        try:
            if buy_date is None:
                buy_date = datetime.now().strftime("%Y-%m-%d")
            
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # 检查是否已存在
            cursor.execute("""
                SELECT id FROM monitored_stocks 
                WHERE stock_code = ? AND status = 'holding'
            """, (stock_code,))
            
            if cursor.fetchone():
                conn.close()
                return False, f"股票 {stock_code} 已在监控列表中"
            
            # 添加到监控列表
            cursor.execute("""
                INSERT INTO monitored_stocks 
                (stock_code, stock_name, buy_price, buy_date, add_time)
                VALUES (?, ?, ?, ?, ?)
            """, (stock_code, stock_name, buy_price, buy_date, 
                  datetime.now().strftime("%Y-%m-%d %H:%M:%S")))
            
            conn.commit()
            conn.close()
            
            self.logger.info(f"添加股票到监控: {stock_code} {stock_name}")
            return True, f"成功添加 {stock_code} {stock_name} 到监控列表"
            
        except Exception as e:
            self.logger.error(f"添加股票失败: {e}")
            return False, f"添加失败: {str(e)}"
    
    def remove_stock(self, stock_code: str, reason: str = "手动移除") -> Tuple[bool, str]:
        """
        从监控列表移除股票
        
        Args:
            stock_code: 股票代码
            reason: 移除原因
            
        Returns:
            (是否成功, 消息)
        """
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # 先检查是否存在持仓中的股票
            cursor.execute("""
                SELECT id FROM monitored_stocks 
                WHERE stock_code = ? AND status = 'holding'
            """, (stock_code,))
            
            if not cursor.fetchone():
                conn.close()
                return False, f"股票 {stock_code} 不在监控列表中"
            
            # 先删除该股票的所有'removed'记录（避免UNIQUE约束冲突）
            cursor.execute("""
                DELETE FROM monitored_stocks 
                WHERE stock_code = ? AND status = 'removed'
            """, (stock_code,))
            
            # 然后更新持仓中的记录为'removed'
            cursor.execute("""
                UPDATE monitored_stocks 
                SET status = 'removed',
                    remove_time = ?,
                    remove_reason = ?
                WHERE stock_code = ? AND status = 'holding'
            """, (datetime.now().strftime("%Y-%m-%d %H:%M:%S"), reason, stock_code))
            
            conn.commit()
            conn.close()
            
            self.logger.info(f"移除股票: {stock_code}, 原因: {reason}")
            return True, f"成功移除 {stock_code}"
            
        except Exception as e:
            self.logger.error(f"移除股票失败: {e}")
            return False, f"移除失败: {str(e)}"
    
    def get_monitored_stocks(self) -> List[Dict]:
        """
        获取所有监控中的股票
        
        Returns:
            股票列表
        """
        try:
            conn = sqlite3.connect(self.db_path)
            df = pd.read_sql_query("""
                SELECT * FROM monitored_stocks 
                WHERE status = 'holding'
                ORDER BY add_time DESC
            """, conn)
            conn.close()
            
            return df.to_dict('records') if not df.empty else []
            
        except Exception as e:
            self.logger.error(f"获取监控列表失败: {e}")
            return []
    
    def update_holding_days(self):
        """更新所有股票的持有天数"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # 获取所有持仓股票
            cursor.execute("""
                SELECT stock_code, buy_date FROM monitored_stocks 
                WHERE status = 'holding'
            """)
            
            stocks = cursor.fetchall()
            today = datetime.now().date()
            
            for stock_code, buy_date in stocks:
                buy_date_obj = datetime.strptime(buy_date, "%Y-%m-%d").date()
                holding_days = (today - buy_date_obj).days
                
                cursor.execute("""
                    UPDATE monitored_stocks 
                    SET holding_days = ?
                    WHERE stock_code = ? AND status = 'holding'
                """, (holding_days, stock_code))
            
            conn.commit()
            conn.close()
            
            self.logger.info("持有天数更新完成")
            
        except Exception as e:
            self.logger.error(f"更新持有天数失败: {e}")
    
    def add_sell_alert(self, stock_code: str, stock_name: str, alert_type: str,
                      alert_reason: str, current_price: float = None,
                      ma5: float = None, ma20: float = None,
                      holding_days: int = None) -> bool:
        """
        添加卖出提醒
        
        Args:
            stock_code: 股票代码
            stock_name: 股票名称
            alert_type: 提醒类型（holding_days/ma_cross）
            alert_reason: 提醒原因
            current_price: 当前价格
            ma5: MA5值
            ma20: MA20值
            holding_days: 持有天数
            
        Returns:
            是否成功
        """
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # 检查是否已存在相同的提醒
            cursor.execute("""
                SELECT id FROM sell_alerts 
                WHERE stock_code = ? AND alert_type = ? AND is_sent = 0
            """, (stock_code, alert_type))
            
            if cursor.fetchone():
                conn.close()
                return False
            
            cursor.execute("""
                INSERT INTO sell_alerts 
                (stock_code, stock_name, alert_type, alert_reason, 
                 current_price, ma5, ma20, holding_days, alert_time)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (stock_code, stock_name, alert_type, alert_reason,
                  current_price, ma5, ma20, holding_days,
                  datetime.now().strftime("%Y-%m-%d %H:%M:%S")))
            
            conn.commit()
            conn.close()
            
            self.logger.info(f"添加卖出提醒: {stock_code} - {alert_reason}")
            return True
            
        except Exception as e:
            self.logger.error(f"添加卖出提醒失败: {e}")
            return False
    
    def get_pending_alerts(self) -> List[Dict]:
        """
        获取待发送的提醒
        
        Returns:
            提醒列表
        """
        try:
            conn = sqlite3.connect(self.db_path)
            df = pd.read_sql_query("""
                SELECT * FROM sell_alerts 
                WHERE is_sent = 0
                ORDER BY alert_time DESC
            """, conn)
            conn.close()
            
            return df.to_dict('records') if not df.empty else []
            
        except Exception as e:
            self.logger.error(f"获取提醒失败: {e}")
            return []
    
    def mark_alert_sent(self, alert_id: int):
        """标记提醒已发送"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute("""
                UPDATE sell_alerts 
                SET is_sent = 1
                WHERE id = ?
            """, (alert_id,))
            
            conn.commit()
            conn.close()
            
        except Exception as e:
            self.logger.error(f"标记提醒失败: {e}")
    
    def get_history_alerts(self, limit: int = 50) -> List[Dict]:
        """
        获取历史提醒记录
        
        Args:
            limit: 返回记录数
            
        Returns:
            提醒列表
        """
        try:
            conn = sqlite3.connect(self.db_path)
            df = pd.read_sql_query(f"""
                SELECT * FROM sell_alerts 
                ORDER BY alert_time DESC
                LIMIT {limit}
            """, conn)
            conn.close()
            
            return df.to_dict('records') if not df.empty else []
            
        except Exception as e:
            self.logger.error(f"获取历史提醒失败: {e}")
            return []
    
    def clear_old_alerts(self, days: int = 30):
        """
        清理旧的提醒记录
        
        Args:
            days: 保留天数
        """
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cutoff_date = (datetime.now() - timedelta(days=days)).strftime("%Y-%m-%d")
            
            cursor.execute("""
                DELETE FROM sell_alerts 
                WHERE alert_time < ? AND is_sent = 1
            """, (cutoff_date,))
            
            deleted = cursor.rowcount
            conn.commit()
            conn.close()
            
            self.logger.info(f"清理了 {deleted} 条旧提醒记录")
            
        except Exception as e:
            self.logger.error(f"清理旧提醒失败: {e}")


# 全局监控器实例
low_price_bull_monitor = LowPriceBullMonitor()
