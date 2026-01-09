#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
净利增长策略监控数据库管理模块
复用低价擒牛的数据库结构，但标识为不同策略
"""

import sqlite3
import logging
from datetime import datetime
from typing import List, Dict, Tuple, Optional
import os


class ProfitGrowthMonitor:
    """净利增长策略监控数据库管理"""
    
    def __init__(self, db_path: str = "profit_growth_monitor.db"):
        """
        初始化监控数据库
        
        Args:
            db_path: 数据库文件路径
        """
        self.db_path = db_path
        self.logger = logging.getLogger(__name__)
        self._init_database()
    
    def _init_database(self):
        """初始化数据库表结构"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # 创建监控股票表
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
                    alert_reason TEXT,
                    current_price REAL,
                    kdj_k REAL,
                    kdj_d REAL,
                    kdj_j REAL,
                    holding_days INTEGER,
                    alert_time TEXT NOT NULL,
                    is_processed INTEGER DEFAULT 0
                )
            """)
            
            conn.commit()
            conn.close()
            self.logger.info("净利增长监控数据库初始化成功")
            
        except Exception as e:
            self.logger.error(f"数据库初始化失败: {e}")
    
    def add_stock(self, stock_code: str, stock_name: str, buy_price: float, 
                  buy_date: str = None) -> Tuple[bool, str]:
        """
        添加股票到监控列表
        
        Args:
            stock_code: 股票代码
            stock_name: 股票名称
            buy_price: 买入价格
            buy_date: 买入日期（可选，默认为当前日期）
            
        Returns:
            (是否成功, 消息)
        """
        try:
            if buy_date is None:
                buy_date = datetime.now().strftime("%Y-%m-%d")
            
            add_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            
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
            
            # 插入新记录
            cursor.execute("""
                INSERT INTO monitored_stocks 
                (stock_code, stock_name, buy_price, buy_date, add_time)
                VALUES (?, ?, ?, ?, ?)
            """, (stock_code, stock_name, buy_price, buy_date, add_time))
            
            conn.commit()
            conn.close()
            
            self.logger.info(f"添加股票到监控: {stock_code} {stock_name}")
            return True, f"成功添加 {stock_name} 到监控列表"
            
        except Exception as e:
            self.logger.error(f"添加股票失败: {e}")
            return False, f"添加失败: {str(e)}"
    
    def get_monitoring_stocks(self) -> List[Dict]:
        """获取所有监控中的股票"""
        try:
            conn = sqlite3.connect(self.db_path)
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            
            cursor.execute("""
                SELECT * FROM monitored_stocks 
                WHERE status = 'holding'
                ORDER BY add_time DESC
            """)
            
            stocks = [dict(row) for row in cursor.fetchall()]
            conn.close()
            
            return stocks
            
        except Exception as e:
            self.logger.error(f"获取监控股票失败: {e}")
            return []
    
    def update_holding_days(self, stock_code: str, days: int) -> bool:
        """更新持股天数"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute("""
                UPDATE monitored_stocks 
                SET holding_days = ?
                WHERE stock_code = ? AND status = 'holding'
            """, (days, stock_code))
            
            conn.commit()
            conn.close()
            return True
            
        except Exception as e:
            self.logger.error(f"更新持股天数失败: {e}")
            return False
    
    def add_sell_alert(self, stock_code: str, stock_name: str, alert_type: str,
                      alert_reason: str = None, current_price: float = None,
                      kdj_k: float = None, kdj_d: float = None, kdj_j: float = None,
                      holding_days: int = None) -> Tuple[bool, str]:
        """添加卖出提醒"""
        try:
            alert_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute("""
                INSERT INTO sell_alerts 
                (stock_code, stock_name, alert_type, alert_reason, 
                 current_price, kdj_k, kdj_d, kdj_j, holding_days, alert_time)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (stock_code, stock_name, alert_type, alert_reason,
                  current_price, kdj_k, kdj_d, kdj_j, holding_days, alert_time))
            
            conn.commit()
            conn.close()
            
            self.logger.info(f"添加卖出提醒: {stock_code} - {alert_type}")
            return True, "提醒添加成功"
            
        except Exception as e:
            self.logger.error(f"添加卖出提醒失败: {e}")
            return False, str(e)
    
    def get_unprocessed_alerts(self) -> List[Dict]:
        """获取未处理的卖出提醒"""
        try:
            conn = sqlite3.connect(self.db_path)
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            
            cursor.execute("""
                SELECT * FROM sell_alerts 
                WHERE is_processed = 0
                ORDER BY alert_time DESC
            """)
            
            alerts = [dict(row) for row in cursor.fetchall()]
            conn.close()
            
            return alerts
            
        except Exception as e:
            self.logger.error(f"获取卖出提醒失败: {e}")
            return []
    
    def get_all_alerts(self, limit: int = 50) -> List[Dict]:
        """获取所有卖出提醒历史"""
        try:
            conn = sqlite3.connect(self.db_path)
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            
            cursor.execute("""
                SELECT * FROM sell_alerts 
                ORDER BY alert_time DESC
                LIMIT ?
            """, (limit,))
            
            alerts = [dict(row) for row in cursor.fetchall()]
            conn.close()
            
            return alerts
            
        except Exception as e:
            self.logger.error(f"获取提醒历史失败: {e}")
            return []
    
    def remove_stock(self, stock_code: str, reason: str = "手动移除") -> Tuple[bool, str]:
        """从监控列表移除股票"""
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
    
    def get_removed_stocks(self, limit: int = 50) -> List[Dict]:
        """获取已移除的股票历史"""
        try:
            conn = sqlite3.connect(self.db_path)
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            
            cursor.execute("""
                SELECT * FROM monitored_stocks 
                WHERE status = 'removed'
                ORDER BY remove_time DESC
                LIMIT ?
            """, (limit,))
            
            stocks = [dict(row) for row in cursor.fetchall()]
            conn.close()
            
            return stocks
            
        except Exception as e:
            self.logger.error(f"获取移除历史失败: {e}")
            return []


# 全局实例
profit_growth_monitor = ProfitGrowthMonitor()
