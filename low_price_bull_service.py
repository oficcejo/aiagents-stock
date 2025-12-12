#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
低价擒牛策略监控服务
定时扫描股票，检测卖出信号
"""

import time
import threading
import logging
from datetime import datetime
from typing import Optional
import os

from low_price_bull_monitor import low_price_bull_monitor
from notification_service import notification_service


class LowPriceBullService:
    """低价擒牛策略监控服务"""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.running = False
        self.thread: Optional[threading.Thread] = None
        self.scan_interval = 60  # 默认扫描间隔（秒）
        self.holding_days_limit = 5  # 持股天数限制
        
        # 从环境变量读取配置
        self._load_config()
    
    def _load_config(self):
        """从环境变量加载配置"""
        try:
            from dotenv import load_dotenv
            load_dotenv()
            
            # 扫描间隔
            interval = os.getenv('LOW_PRICE_BULL_SCAN_INTERVAL', '60')
            self.scan_interval = int(interval)
            
            # 持股天数限制
            days = os.getenv('LOW_PRICE_BULL_HOLDING_DAYS', '5')
            self.holding_days_limit = int(days)
            
            # TDX API配置
            self.tdx_api_url = os.getenv('TDX_BASE_URL', 'http://127.0.0.1:5000')
            
            self.logger.info(f"监控配置: 扫描间隔={self.scan_interval}秒, 持股天数限制={self.holding_days_limit}天")
            self.logger.info(f"TDX API: {self.tdx_api_url}")
            
        except Exception as e:
            self.logger.warning(f"加载配置失败，使用默认值: {e}")
    
    def start(self):
        """启动监控服务"""
        if self.running:
            self.logger.warning("监控服务已在运行")
            return False
        
        self.running = True
        self.thread = threading.Thread(target=self._monitor_loop, daemon=True)
        self.thread.start()
        
        self.logger.info("低价擒牛监控服务已启动")
        return True
    
    def stop(self):
        """停止监控服务"""
        if not self.running:
            return False
        
        self.running = False
        if self.thread:
            self.thread.join(timeout=5)
        
        self.logger.info("低价擒牛监控服务已停止")
        return True
    
    def _monitor_loop(self):
        """监控循环"""
        while self.running:
            try:
                self._scan_stocks()
                time.sleep(self.scan_interval)
            except Exception as e:
                self.logger.error(f"监控循环错误: {e}")
                time.sleep(self.scan_interval)
    
    def _scan_stocks(self):
        """扫描所有监控的股票"""
        try:
            # 更新持有天数
            low_price_bull_monitor.update_holding_days()
            
            # 获取监控列表
            stocks = low_price_bull_monitor.get_monitored_stocks()
            
            if not stocks:
                return
            
            self.logger.info(f"开始扫描 {len(stocks)} 只股票")
            
            for stock in stocks:
                try:
                    self._check_stock(stock)
                except Exception as e:
                    self.logger.error(f"检查股票 {stock['stock_code']} 失败: {e}")
            
            # 处理提醒
            self._process_alerts()
            
        except Exception as e:
            self.logger.error(f"扫描股票失败: {e}")
    
    def _check_stock(self, stock: dict):
        """
        检查单只股票的卖出信号
        
        Args:
            stock: 股票信息字典
        """
        stock_code = stock['stock_code']
        stock_name = stock['stock_name']
        holding_days = stock['holding_days']
        
        # 检查1: 持股天数
        if holding_days >= self.holding_days_limit:
            # 添加提醒
            low_price_bull_monitor.add_sell_alert(
                stock_code=stock_code,
                stock_name=stock_name,
                alert_type='holding_days',
                alert_reason=f'持股满{self.holding_days_limit}天，建议卖出',
                holding_days=holding_days
            )
            self.logger.info(f"{stock_code} 持股满{self.holding_days_limit}天，生成卖出提醒")
            return
        
        # 检查2: MA5下穿MA20
        current_price, ma5, ma20 = self._get_stock_data(stock_code)
        
        if current_price and ma5 and ma20:
            if ma5 < ma20:
                # MA5下穿MA20，添加提醒
                low_price_bull_monitor.add_sell_alert(
                    stock_code=stock_code,
                    stock_name=stock_name,
                    alert_type='ma_cross',
                    alert_reason='MA5下穿MA20，技术信号卖出',
                    current_price=current_price,
                    ma5=ma5,
                    ma20=ma20,
                    holding_days=holding_days
                )
                self.logger.info(f"{stock_code} MA5下穿MA20，生成卖出提醒")
    
    def _get_stock_data(self, stock_code: str) -> tuple:
        """
        获取股票数据（价格和均线）
        
        Args:
            stock_code: 股票代码（可能带后缀，如002259.SZ）
            
        Returns:
            (当前价格, MA5, MA20)
        """
        try:
            import requests
            import pandas as pd
            
            # 处理股票代码格式：去掉后缀，保留纯数字代码
            # 例如：002259.SZ -> 002259
            clean_code = stock_code.split('.')[0] if '.' in stock_code else stock_code
            
            # 判断市场并添加前缀（TDX API可能需要）
            # 深圳：0开头、3开头 -> SZ前缀
            # 上海：6开头 -> SH前缀
            if clean_code.startswith(('0', '3')):
                api_code = f"SZ{clean_code}"
            elif clean_code.startswith('6'):
                api_code = f"SH{clean_code}"
            else:
                api_code = clean_code
            
            # 调用TDX API获取K线数据
            url = f"{self.tdx_api_url}/api/kline"
            params = {
                'code': api_code,
                'type': 'day'  # 日K线
            }
            
            self.logger.debug(f"请求TDX API: code={stock_code} -> api_code={api_code}")
            
            response = requests.get(url, params=params, timeout=10)
            
            if response.status_code != 200:
                self.logger.warning(f"获取 {stock_code} K线数据失败: HTTP {response.status_code}")
                self.logger.warning(f"请求URL: {url}?code={api_code}&type=day")
                
                # 尝试使用纯数字代码重试
                if api_code != clean_code:
                    self.logger.info(f"尝试使用纯数字代码重试: {clean_code}")
                    params['code'] = clean_code
                    response = requests.get(url, params=params, timeout=10)
                    
                    if response.status_code != 200:
                        self.logger.warning(f"重试失败: HTTP {response.status_code}")
                        return None, None, None
                else:
                    return None, None, None
            
            data = response.json()
            
            # 检查数据格式
            # 支持两种格式：
            # 1. 直接返回数组: [{date, open, high, low, close, volume}, ...]
            # 2. 嵌套格式: {code: 0, message: "success", data: {List: [...]}}
            if isinstance(data, dict) and 'data' in data:
                # 嵌套格式
                if data.get('code') != 0:
                    self.logger.warning(f"{stock_code} API返回错误: {data.get('message')}")
                    return None, None, None
                
                data_obj = data.get('data', {})
                kline_list = data_obj.get('List', [])
                
                if not kline_list or len(kline_list) < 20:
                    self.logger.warning(f"{stock_code} K线数据不足，需要至少20天，当前{len(kline_list)}天")
                    return None, None, None
                
                # 转换为DataFrame，字段名需要映射
                # API返回：{Time, Open, High, Low, Close, Volume, Amount}
                # 需要：{date, open, high, low, close, volume}
                df = pd.DataFrame(kline_list)
                
                # 重命名字段（大小写转换）
                if 'Time' in df.columns:
                    df['date'] = df['Time']
                if 'Open' in df.columns:
                    df['open'] = df['Open']
                if 'High' in df.columns:
                    df['high'] = df['High']
                if 'Low' in df.columns:
                    df['low'] = df['Low']
                if 'Close' in df.columns:
                    df['close'] = df['Close']
                if 'Volume' in df.columns:
                    df['volume'] = df['Volume']
                    
            elif isinstance(data, list):
                # 直接数组格式
                if len(data) < 20:
                    self.logger.warning(f"{stock_code} K线数据不足，需要至少20天")
                    return None, None, None
                
                df = pd.DataFrame(data)
            else:
                self.logger.warning(f"{stock_code} K线数据格式错误")
                return None, None, None
            
            # 确保有close列
            if 'close' not in df.columns:
                self.logger.warning(f"{stock_code} K线数据缺少close字段")
                return None, None, None
            
            # 转换为浮点数
            df['close'] = pd.to_numeric(df['close'], errors='coerce')
            
            # 计算MA5和MA20
            df['MA5'] = df['close'].rolling(window=5).mean()
            df['MA20'] = df['close'].rolling(window=20).mean()
            
            # 获取最新数据
            latest = df.iloc[-1]
            current_price = latest['close']
            ma5 = latest['MA5']
            ma20 = latest['MA20']
            
            # 检查是否有效
            if pd.isna(current_price) or pd.isna(ma5) or pd.isna(ma20):
                self.logger.warning(f"{stock_code} 数据包含NaN值")
                return None, None, None
            
            self.logger.info(f"{stock_code} 数据: 价格={current_price:.2f}, MA5={ma5:.2f}, MA20={ma20:.2f}")
            return current_price, ma5, ma20
            
        except requests.exceptions.RequestException as e:
            self.logger.error(f"请求TDX API失败 {stock_code}: {e}")
            self.logger.error(f"请检查.env中的TDX_BASE_URL配置: {self.tdx_api_url}")
            return None, None, None
        except Exception as e:
            self.logger.error(f"获取股票数据失败 {stock_code}: {e}")
            import traceback
            traceback.print_exc()
            return None, None, None
    
    def _process_alerts(self):
        """处理待发送的提醒"""
        try:
            alerts = low_price_bull_monitor.get_pending_alerts()
            
            if not alerts:
                return
            
            self.logger.info(f"处理 {len(alerts)} 条卖出提醒")
            
            for alert in alerts:
                try:
                    # 发送通知
                    self._send_alert_notification(alert)
                    
                    # 标记已发送
                    low_price_bull_monitor.mark_alert_sent(alert['id'])
                    
                    # 自动移除股票
                    low_price_bull_monitor.remove_stock(
                        alert['stock_code'],
                        reason=alert['alert_reason']
                    )
                    
                    self.logger.info(f"已处理提醒并移除股票: {alert['stock_code']}")
                    
                except Exception as e:
                    self.logger.error(f"处理提醒失败: {e}")
        
        except Exception as e:
            self.logger.error(f"处理提醒失败: {e}")
    
    def _send_alert_notification(self, alert: dict):
        """
        发送卖出提醒通知
        
        Args:
            alert: 提醒信息字典
        """
        try:
            # 构建消息
            keyword = notification_service.config.get('webhook_keyword', 'aiagents通知')
            
            message_text = f"### {keyword} - 低价擒牛卖出提醒\n\n"
            message_text += f"**股票代码**: {alert['stock_code']}\n\n"
            message_text += f"**股票名称**: {alert['stock_name']}\n\n"
            message_text += f"**提醒类型**: {self._get_alert_type_name(alert['alert_type'])}\n\n"
            message_text += f"**提醒原因**: {alert['alert_reason']}\n\n"
            
            # 添加详细信息（确保数据类型正确）
            current_price = alert.get('current_price')
            if current_price is not None:
                try:
                    price_val = float(current_price)
                    message_text += f"**当前价格**: {price_val:.2f}元\n\n"
                except (ValueError, TypeError):
                    pass
            
            ma5 = alert.get('ma5')
            ma20 = alert.get('ma20')
            if ma5 is not None and ma20 is not None:
                try:
                    ma5_val = float(ma5)
                    ma20_val = float(ma20)
                    message_text += f"**MA5**: {ma5_val:.2f}\n\n"
                    message_text += f"**MA20**: {ma20_val:.2f}\n\n"
                except (ValueError, TypeError):
                    pass
            
            holding_days = alert.get('holding_days')
            if holding_days is not None:
                try:
                    days_val = int(holding_days)
                    message_text += f"**持有天数**: {days_val}天\n\n"
                except (ValueError, TypeError):
                    pass
            
            message_text += f"**提醒时间**: {alert['alert_time']}\n\n"
            message_text += "---\n\n"
            message_text += "**建议**: 开盘时卖出该股票\n\n"
            message_text += "_此消息由AI股票分析系统自动发送_"
            
            # 发送钉钉通知
            if notification_service.config['webhook_enabled']:
                import requests
                
                data = {
                    "msgtype": "markdown",
                    "markdown": {
                        "title": f"{keyword} - 卖出提醒",
                        "text": message_text
                    }
                }
                
                response = requests.post(
                    notification_service.config['webhook_url'],
                    json=data,
                    headers={'Content-Type': 'application/json'},
                    timeout=10
                )
                
                if response.status_code == 200:
                    self.logger.info(f"卖出提醒已发送: {alert['stock_code']}")
                else:
                    self.logger.error(f"发送提醒失败: HTTP {response.status_code}")
            
        except Exception as e:
            self.logger.error(f"发送通知失败: {e}")
    
    def _get_alert_type_name(self, alert_type: str) -> str:
        """获取提醒类型名称"""
        type_map = {
            'holding_days': '持股到期',
            'ma_cross': 'MA均线死叉'
        }
        return type_map.get(alert_type, alert_type)
    
    def get_status(self) -> dict:
        """获取服务状态"""
        stocks = low_price_bull_monitor.get_monitored_stocks()
        alerts = low_price_bull_monitor.get_pending_alerts()
        
        return {
            'running': self.running,
            'scan_interval': self.scan_interval,
            'holding_days_limit': self.holding_days_limit,
            'monitored_count': len(stocks),
            'pending_alerts': len(alerts)
        }


# 全局服务实例
low_price_bull_service = LowPriceBullService()
