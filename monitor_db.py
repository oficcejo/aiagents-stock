import sqlite3
import json
from datetime import datetime
from typing import Dict, List, Optional

class StockMonitorDatabase:
    """股票监测数据库管理类"""
    
    def __init__(self, db_path: str = "stock_monitor.db"):
        self.db_path = db_path
        self.init_database()
    
    def init_database(self):
        """初始化数据库表结构"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # 创建监测股票表
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS monitored_stocks (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                symbol TEXT NOT NULL,
                name TEXT NOT NULL,
                rating TEXT NOT NULL,
                entry_range TEXT NOT NULL,  -- JSON格式: {"min": 10.0, "max": 12.0}
                take_profit REAL,
                stop_loss REAL,
                current_price REAL,
                last_checked TIMESTAMP,
                check_interval INTEGER DEFAULT 30,  -- 分钟
                notification_enabled BOOLEAN DEFAULT TRUE,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # 创建价格历史表
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS price_history (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                stock_id INTEGER,
                price REAL NOT NULL,
                timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (stock_id) REFERENCES monitored_stocks (id)
            )
        ''')
        
        # 创建提醒记录表
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS notifications (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                stock_id INTEGER,
                type TEXT NOT NULL,  -- entry/take_profit/stop_loss
                message TEXT NOT NULL,
                triggered_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                sent BOOLEAN DEFAULT FALSE,
                FOREIGN KEY (stock_id) REFERENCES monitored_stocks (id)
            )
        ''')
        
        conn.commit()
        conn.close()
    
    def add_monitored_stock(self, symbol: str, name: str, rating: str, 
                           entry_range: Dict, take_profit: float, 
                           stop_loss: float, check_interval: int = 30, 
                           notification_enabled: bool = True) -> int:
        """添加监测股票"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT INTO monitored_stocks 
            (symbol, name, rating, entry_range, take_profit, stop_loss, check_interval, notification_enabled)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        ''', (symbol, name, rating, json.dumps(entry_range), take_profit, stop_loss, check_interval, notification_enabled))
        
        stock_id = cursor.lastrowid
        conn.commit()
        conn.close()
        
        return stock_id
    
    def get_monitored_stocks(self) -> List[Dict]:
        """获取所有监测股票"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT id, symbol, name, rating, entry_range, take_profit, stop_loss, 
                   current_price, last_checked, check_interval, notification_enabled,
                   created_at, updated_at
            FROM monitored_stocks
            ORDER BY created_at DESC
        ''')
        
        stocks = []
        for row in cursor.fetchall():
            stocks.append({
                'id': row[0],
                'symbol': row[1],
                'name': row[2],
                'rating': row[3],
                'entry_range': json.loads(row[4]),
                'take_profit': row[5],
                'stop_loss': row[6],
                'current_price': row[7],
                'last_checked': row[8],
                'check_interval': row[9],
                'notification_enabled': bool(row[10]),
                'created_at': row[11],
                'updated_at': row[12]
            })
        
        conn.close()
        return stocks
    
    def update_stock_price(self, stock_id: int, price: float):
        """更新股票价格"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # 更新当前价格
        cursor.execute('''
            UPDATE monitored_stocks 
            SET current_price = ?, last_checked = CURRENT_TIMESTAMP
            WHERE id = ?
        ''', (price, stock_id))
        
        # 记录价格历史
        cursor.execute('''
            INSERT INTO price_history (stock_id, price)
            VALUES (?, ?)
        ''', (stock_id, price))
        
        conn.commit()
        conn.close()
    
    def add_notification(self, stock_id: int, notification_type: str, message: str):
        """添加提醒记录"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT INTO notifications (stock_id, type, message)
            VALUES (?, ?, ?)
        ''', (stock_id, notification_type, message))
        
        conn.commit()
        conn.close()
    
    def get_pending_notifications(self) -> List[Dict]:
        """获取待发送的提醒"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT n.id, n.stock_id, s.symbol, s.name, n.type, n.message, n.triggered_at
            FROM notifications n
            JOIN monitored_stocks s ON n.stock_id = s.id
            WHERE n.sent = FALSE
            ORDER BY n.triggered_at
        ''')
        
        notifications = []
        for row in cursor.fetchall():
            notifications.append({
                'id': row[0],
                'stock_id': row[1],
                'symbol': row[2],
                'name': row[3],
                'type': row[4],
                'message': row[5],
                'triggered_at': row[6]
            })
        
        conn.close()
        return notifications
    
    def mark_notification_sent(self, notification_id: int):
        """标记提醒已发送"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            UPDATE notifications SET sent = TRUE WHERE id = ?
        ''', (notification_id,))
        
        conn.commit()
        conn.close()
    
    def mark_all_notifications_sent(self):
        """标记所有通知为已读"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('UPDATE notifications SET sent = TRUE WHERE sent = FALSE')
        
        conn.commit()
        conn.close()
        
        return cursor.rowcount
    
    def clear_all_notifications(self):
        """清空所有通知"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('DELETE FROM notifications')
        
        conn.commit()
        conn.close()
        
        return cursor.rowcount
    
    def remove_monitored_stock(self, stock_id: int):
        """移除监测股票"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # 删除相关记录
            cursor.execute('DELETE FROM price_history WHERE stock_id = ?', (stock_id,))
            cursor.execute('DELETE FROM notifications WHERE stock_id = ?', (stock_id,))
            cursor.execute('DELETE FROM monitored_stocks WHERE id = ?', (stock_id,))
            
            affected_rows = cursor.rowcount
            conn.commit()
            conn.close()
            
            return affected_rows > 0
        except Exception as e:
            print(f"删除股票失败: {e}")
            return False
    
    def update_monitored_stock(self, stock_id: int, rating: str, entry_range: Dict, 
                              take_profit: float, stop_loss: float, 
                              check_interval: int, notification_enabled: bool):
        """更新监测股票"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            UPDATE monitored_stocks 
            SET rating = ?, entry_range = ?, take_profit = ?, stop_loss = ?, 
                check_interval = ?, notification_enabled = ?, updated_at = CURRENT_TIMESTAMP
            WHERE id = ?
        ''', (rating, json.dumps(entry_range), take_profit, stop_loss, check_interval, notification_enabled, stock_id))
        
        conn.commit()
        conn.close()
        
        return cursor.rowcount > 0
    
    def toggle_notification(self, stock_id: int, enabled: bool):
        """切换通知状态"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            UPDATE monitored_stocks 
            SET notification_enabled = ?, updated_at = CURRENT_TIMESTAMP
            WHERE id = ?
        ''', (enabled, stock_id))
        
        conn.commit()
        conn.close()
        
        return cursor.rowcount > 0
    
    def get_stock_by_id(self, stock_id: int) -> Optional[Dict]:
        """根据ID获取股票信息"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT id, symbol, name, rating, entry_range, take_profit, stop_loss,
                   current_price, last_checked, check_interval, notification_enabled
            FROM monitored_stocks WHERE id = ?
        ''', (stock_id,))
        
        row = cursor.fetchone()
        conn.close()
        
        if row:
            return {
                'id': row[0],
                'symbol': row[1],
                'name': row[2],
                'rating': row[3],
                'entry_range': json.loads(row[4]),
                'take_profit': row[5],
                'stop_loss': row[6],
                'current_price': row[7],
                'last_checked': row[8],
                'check_interval': row[9],
                'notification_enabled': bool(row[10])
            }
        return None

# 全局数据库实例
monitor_db = StockMonitorDatabase()