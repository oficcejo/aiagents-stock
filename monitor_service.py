import time
import threading
import schedule
from datetime import datetime, timedelta
from typing import Dict, List
import streamlit as st

from monitor_db import monitor_db
from stock_data import StockDataFetcher
from miniqmt_interface import miniqmt, get_miniqmt_status
from notification_service import notification_service

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
        print("监测服务已启动")
        while self.running:
            try:
                self._check_all_stocks()
                # 根据最小监测间隔决定循环间隔，最少5分钟检查一次
                time.sleep(300)  # 每5分钟检查一次
            except Exception as e:
                print(f"监测服务错误: {e}")
                time.sleep(60)  # 错误后等待1分钟再重试
    
    def _check_all_stocks(self):
        """检查所有监测股票"""
        stocks = monitor_db.get_monitored_stocks()
        current_time = datetime.now()
        
        updated_count = 0
        for stock in stocks:
            # 检查是否需要更新价格
            last_checked = stock.get('last_checked')
            check_interval = stock.get('check_interval', 30)
            
            if last_checked:
                last_checked_dt = datetime.fromisoformat(last_checked)
                next_check = last_checked_dt + timedelta(minutes=check_interval)
                if current_time < next_check:
                    # 显示距离下次检查的时间
                    time_left = (next_check - current_time).total_seconds() / 60
                    print(f"股票 {stock['symbol']} 距离下次检查还有 {time_left:.1f} 分钟")
                    continue
            
            try:
                print(f"正在更新股票 {stock['symbol']} 的价格...")
                self._update_stock_price(stock)
                updated_count += 1
                
                # 在每个股票请求之间增加延迟，避免API限流
                if updated_count < len(stocks):
                    time.sleep(3)  # 每个股票之间等待3秒
            except Exception as e:
                print(f"❌ 更新股票 {stock['symbol']} 价格失败: {e}")
                time.sleep(3)  # 失败后也等待3秒再继续
        
        if updated_count > 0:
            print(f"✅ 本轮共更新了 {updated_count} 只股票")
    
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
                    # 更新数据库（包括更新last_checked时间）
                    monitor_db.update_stock_price(stock['id'], current_price)
                    print(f"✅ {symbol} 当前价格: ¥{current_price}")
                    
                    # 检查触发条件
                    self._check_trigger_conditions(stock, current_price)
                except (ValueError, TypeError) as e:
                    print(f"❌ 股票 {symbol} 价格格式错误: {current_price}")
                    # 即使失败也更新last_checked，避免持续重试
                    monitor_db.update_last_checked(stock['id'])
            else:
                print(f"⚠️ 无法获取股票 {symbol} 的当前价格")
                # 更新last_checked，避免持续重试
                monitor_db.update_last_checked(stock['id'])
                
        except Exception as e:
            print(f"❌ 获取股票 {symbol} 数据失败: {e}")
            # 即使失败也更新last_checked，避免持续重试
            try:
                monitor_db.update_last_checked(stock['id'])
            except:
                pass
    
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
                # 检查是否在最近60分钟内已发送过相同通知，避免重复
                if not monitor_db.has_recent_notification(stock['id'], 'entry', minutes=60):
                    message = f"股票 {stock['symbol']} ({stock['name']}) 价格 {current_price} 进入进场区间 [{entry_range['min']}-{entry_range['max']}]"
                    monitor_db.add_notification(stock['id'], 'entry', message)
                    
                    # 立即发送通知（包括邮件）
                    notification_service.send_notifications()
                
                # 如果启用量化交易，执行自动交易
                if stock.get('quant_enabled', False):
                    self._execute_quant_trade(stock, 'entry', current_price)
        
        # 检查止盈
        if take_profit and current_price >= take_profit:
            # 检查是否在最近60分钟内已发送过相同通知，避免重复
            if not monitor_db.has_recent_notification(stock['id'], 'take_profit', minutes=60):
                message = f"股票 {stock['symbol']} ({stock['name']}) 价格 {current_price} 达到止盈位 {take_profit}"
                monitor_db.add_notification(stock['id'], 'take_profit', message)
                
                # 立即发送通知（包括邮件）
                notification_service.send_notifications()
            
            # 如果启用量化交易，执行自动交易
            if stock.get('quant_enabled', False):
                self._execute_quant_trade(stock, 'take_profit', current_price)
        
        # 检查止损
        if stop_loss and current_price <= stop_loss:
            # 检查是否在最近60分钟内已发送过相同通知，避免重复
            if not monitor_db.has_recent_notification(stock['id'], 'stop_loss', minutes=60):
                message = f"股票 {stock['symbol']} ({stock['name']}) 价格 {current_price} 达到止损位 {stop_loss}"
                monitor_db.add_notification(stock['id'], 'stop_loss', message)
                
                # 立即发送通知（包括邮件）
                notification_service.send_notifications()
            
            # 如果启用量化交易，执行自动交易
            if stock.get('quant_enabled', False):
                self._execute_quant_trade(stock, 'stop_loss', current_price)
    
    def _execute_quant_trade(self, stock: Dict, signal_type: str, current_price: float):
        """执行量化交易"""
        try:
            # 检查MiniQMT是否连接
            if not miniqmt.is_connected():
                print(f"MiniQMT未连接，无法执行 {stock['symbol']} 的量化交易")
                return
            
            # 获取量化配置
            quant_config = stock.get('quant_config', {})
            if not quant_config:
                print(f"股票 {stock['symbol']} 未配置量化参数")
                return
            
            # 执行策略信号
            signal = {
                'type': signal_type,
                'price': current_price,
                'message': f"{signal_type} signal triggered"
            }
            
            position_size = quant_config.get('max_position_pct', 0.2)
            success, msg = miniqmt.execute_strategy_signal(
                stock['id'], 
                stock['symbol'], 
                signal, 
                position_size
            )
            
            if success:
                print(f"✅ 量化交易成功: {stock['symbol']} - {msg}")
                # 记录交易通知（量化交易通知不检查重复，因为每次交易都应该通知）
                monitor_db.add_notification(
                    stock['id'], 
                    'quant_trade', 
                    f"量化交易执行: {msg}"
                )
                # 立即发送通知（包括邮件）
                notification_service.send_notifications()
            else:
                print(f"❌ 量化交易失败: {stock['symbol']} - {msg}")
                
        except Exception as e:
            print(f"执行量化交易异常: {stock['symbol']} - {str(e)}")
    
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
    
    def get_scheduler(self):
        """获取调度器实例"""
        from monitor_scheduler import get_scheduler
        return get_scheduler(self)

# 全局监测服务实例
monitor_service = StockMonitorService()