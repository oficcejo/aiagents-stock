import time
import threading
import schedule
from datetime import datetime, timedelta
from typing import Dict, List
import streamlit as st

from monitor_db import monitor_db
from stock_data import StockDataFetcher

class StockMonitorService:
    """股票监测服务"""
    
    def __init__(self):
        self.fetcher = StockDataFetcher()
        self.running = False
        self.thread = None
    
    def start_monitoring(self):
        """启动监测服务"""
        if self.running:
            return
        
        self.running = True
        self.thread = threading.Thread(target=self._monitor_loop, daemon=True)
        self.thread.start()
        st.success("✅ 监测服务已启动")
    
    def stop_monitoring(self):
        """停止监测服务"""
        self.running = False
        if self.thread:
            self.thread.join(timeout=5)
        st.info("⏹️ 监测服务已停止")
    
    def _monitor_loop(self):
        """监测循环"""
        while self.running:
            try:
                self._check_all_stocks()
                time.sleep(60)  # 每分钟检查一次
            except Exception as e:
                print(f"监测服务错误: {e}")
                time.sleep(10)
    
    def _check_all_stocks(self):
        """检查所有监测股票"""
        stocks = monitor_db.get_monitored_stocks()
        current_time = datetime.now()
        
        for stock in stocks:
            # 检查是否需要更新价格
            last_checked = stock.get('last_checked')
            check_interval = stock.get('check_interval', 30)
            
            if last_checked:
                last_checked_dt = datetime.fromisoformat(last_checked)
                next_check = last_checked_dt + timedelta(minutes=check_interval)
                if current_time < next_check:
                    continue
            
            try:
                self._update_stock_price(stock)
            except Exception as e:
                print(f"更新股票 {stock['symbol']} 价格失败: {e}")
    
    def _update_stock_price(self, stock: Dict):
        """更新股票价格并检查条件"""
        symbol = stock['symbol']
        
        # 获取最新价格
        try:
            # 使用get_stock_info获取当前价格
            stock_info = self.fetcher.get_stock_info(symbol)
            current_price = stock_info.get('current_price')
            
            if current_price and current_price != 'N/A':
                try:
                    current_price = float(current_price)
                    # 更新数据库
                    monitor_db.update_stock_price(stock['id'], current_price)
                    
                    # 检查触发条件
                    self._check_trigger_conditions(stock, current_price)
                except (ValueError, TypeError):
                    print(f"股票 {symbol} 价格格式错误: {current_price}")
            else:
                print(f"无法获取股票 {symbol} 的当前价格")
                
        except Exception as e:
            print(f"获取股票 {symbol} 数据失败: {e}")
    
    def _check_trigger_conditions(self, stock: Dict, current_price: float):
        """检查触发条件"""
        if not stock.get('notification_enabled', True):
            return
        
        entry_range = stock.get('entry_range', {})
        take_profit = stock.get('take_profit')
        stop_loss = stock.get('stop_loss')
        
        # 检查进场区间
        if entry_range and entry_range.get('min') and entry_range.get('max'):
            if current_price >= entry_range['min'] and current_price <= entry_range['max']:
                message = f"股票 {stock['symbol']} ({stock['name']}) 价格 {current_price} 进入进场区间 [{entry_range['min']}-{entry_range['max']}]"
                monitor_db.add_notification(stock['id'], 'entry', message)
        
        # 检查止盈
        if take_profit and current_price >= take_profit:
            message = f"股票 {stock['symbol']} ({stock['name']}) 价格 {current_price} 达到止盈位 {take_profit}"
            monitor_db.add_notification(stock['id'], 'take_profit', message)
        
        # 检查止损
        if stop_loss and current_price <= stop_loss:
            message = f"股票 {stock['symbol']} ({stock['name']}) 价格 {current_price} 达到止损位 {stop_loss}"
            monitor_db.add_notification(stock['id'], 'stop_loss', message)
    
    def get_stocks_needing_update(self) -> List[Dict]:
        """获取需要更新价格的股票"""
        stocks = monitor_db.get_monitored_stocks()
        current_time = datetime.now()
        need_update = []
        
        for stock in stocks:
            last_checked = stock.get('last_checked')
            check_interval = stock.get('check_interval', 30)
            
            if not last_checked:
                need_update.append(stock)
                continue
            
            last_checked_dt = datetime.fromisoformat(last_checked)
            next_check = last_checked_dt + timedelta(minutes=check_interval)
            if current_time >= next_check:
                need_update.append(stock)
        
        return need_update
    
    def manual_update_stock(self, stock_id: int):
        """手动更新股票价格"""
        stock = monitor_db.get_stock_by_id(stock_id)
        if stock:
            self._update_stock_price(stock)
            return True
        return False

# 全局监测服务实例
monitor_service = StockMonitorService()