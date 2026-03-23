#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
低价擒牛量化交易策略
实现基于MA均线的买卖择时策略
"""

import pandas as pd
from datetime import datetime, timedelta
from typing import Dict, List, Optional
import logging


class LowPriceBullStrategy:
    """低价擒牛量化交易策略"""
    
    def __init__(self, initial_capital: float = 1000000.0):
        """
        初始化策略
        
        Args:
            initial_capital: 初始资金（默认100万）
        """
        self.logger = logging.getLogger(__name__)
        
        # 策略参数
        self.initial_capital = initial_capital
        self.available_cash = initial_capital
        self.max_stocks = 4  # 账户最大持股数
        self.max_position_per_stock = 0.4  # 个股最大持仓比例（4成）
        self.max_daily_buy = 2  # 单日最大买入数
        self.holding_period = 5  # 持股周期（天）
        
        # 持仓信息
        self.positions: Dict[str, Dict] = {}  # {股票代码: {买入价, 数量, 买入日期, 持有天数}}
        self.trade_history: List[Dict] = []  # 交易历史
        
        # 当日交易计数
        self.daily_buy_count = 0
        self.current_date = None
    
    def reset_daily_counter(self, date):
        """重置当日计数器"""
        if self.current_date != date:
            self.current_date = date
            self.daily_buy_count = 0
    
    def can_buy(self, stock_code: str) -> tuple[bool, str]:
        """
        检查是否可以买入
        
        Returns:
            (是否可买, 原因)
        """
        # 检查是否已持有
        if stock_code in self.positions:
            return False, "已持有该股票"
        
        # 检查持股数量
        if len(self.positions) >= self.max_stocks:
            return False, f"已达最大持股数限制({self.max_stocks}只)"
        
        # 检查当日买入数量
        if self.daily_buy_count >= self.max_daily_buy:
            return False, f"今日已达最大买入数限制({self.max_daily_buy}只)"
        
        # 检查资金
        if self.available_cash <= 0:
            return False, "可用资金不足"
        
        return True, "可以买入"
    
    def calculate_buy_amount(self, stock_price: float) -> tuple[int, float]:
        """
        计算买入数量（满仓策略）
        
        Args:
            stock_price: 股票价格
            
        Returns:
            (买入股数, 买入金额)
        """
        # 满仓策略：使用所有可用资金
        max_amount = self.available_cash
        
        # 但不能超过个股最大持仓
        max_per_stock = self.initial_capital * self.max_position_per_stock
        target_amount = min(max_amount, max_per_stock)
        
        # 计算股数（A股100股为1手）
        shares = int(target_amount / stock_price / 100) * 100
        
        if shares < 100:
            return 0, 0
        
        actual_amount = shares * stock_price
        return shares, actual_amount
    
    def buy(self, stock_code: str, stock_name: str, price: float, date: str) -> tuple[bool, str, Optional[Dict]]:
        """
        执行买入操作
        
        Returns:
            (是否成功, 消息, 交易详情)
        """
        # 重置当日计数
        self.reset_daily_counter(date)
        
        # 检查是否可买入
        can_buy, reason = self.can_buy(stock_code)
        if not can_buy:
            return False, reason, None
        
        # 计算买入数量
        shares, amount = self.calculate_buy_amount(price)
        
        if shares == 0:
            return False, "资金不足，无法买入100股", None
        
        # 执行买入
        self.positions[stock_code] = {
            'name': stock_name,
            'shares': shares,
            'buy_price': price,
            'buy_date': date,
            'holding_days': 0
        }
        
        self.available_cash -= amount
        self.daily_buy_count += 1
        
        # 记录交易
        trade = {
            'type': 'BUY',
            'code': stock_code,
            'name': stock_name,
            'price': price,
            'shares': shares,
            'amount': amount,
            'date': date,
            'cash_after': self.available_cash
        }
        self.trade_history.append(trade)
        
        message = f"✅ 买入成功: {stock_code} {stock_name} | 价格:{price:.2f} | 数量:{shares}股 | 金额:{amount:.2f}元"
        self.logger.info(message)
        
        return True, message, trade
    
    def should_sell(self, stock_code: str, ma5: float, ma20: float, current_date: str) -> tuple[bool, str]:
        """
        判断是否应该卖出
        
        策略：
        1. MA5下穿MA20时卖出
        2. 持股满5天强制卖出
        
        Returns:
            (是否卖出, 原因)
        """
        if stock_code not in self.positions:
            return False, "未持有该股票"
        
        position = self.positions[stock_code]
        
        # 更新持有天数
        # 简化处理，按交易日计算
        position['holding_days'] += 1
        
        # 检查持股周期
        if position['holding_days'] >= self.holding_period:
            return True, f"持股满{self.holding_period}天，到期卖出"
        
        # 检查MA5下穿MA20
        if ma5 is not None and ma20 is not None:
            if ma5 < ma20:
                return True, "MA5下穿MA20，技术信号卖出"
        
        return False, "持有"
    
    def sell(self, stock_code: str, price: float, date: str, reason: str = "") -> tuple[bool, str, Optional[Dict]]:
        """
        执行卖出操作
        
        Returns:
            (是否成功, 消息, 交易详情)
        """
        if stock_code not in self.positions:
            return False, "未持有该股票", None
        
        position = self.positions[stock_code]
        shares = position['shares']
        buy_price = position['buy_price']
        
        # 计算盈亏
        amount = shares * price
        cost = shares * buy_price
        profit = amount - cost
        profit_pct = (profit / cost) * 100 if cost > 0 else 0
        
        # 归还资金
        self.available_cash += amount
        
        # 移除持仓
        del self.positions[stock_code]
        
        # 记录交易
        trade = {
            'type': 'SELL',
            'code': stock_code,
            'name': position['name'],
            'price': price,
            'shares': shares,
            'amount': amount,
            'date': date,
            'reason': reason,
            'buy_price': buy_price,
            'profit': profit,
            'profit_pct': profit_pct,
            'cash_after': self.available_cash
        }
        self.trade_history.append(trade)
        
        profit_str = f"+{profit:.2f}" if profit >= 0 else f"{profit:.2f}"
        message = f"✅ 卖出成功: {stock_code} {position['name']} | 价格:{price:.2f} | 数量:{shares}股 | 盈亏:{profit_str}元({profit_pct:+.2f}%) | 原因:{reason}"
        self.logger.info(message)
        
        return True, message, trade
    
    def get_portfolio_summary(self) -> Dict:
        """
        获取投资组合摘要
        
        Returns:
            组合摘要信息
        """
        # 计算持仓市值（需要当前价格，这里用买入价估算）
        position_value = sum(
            pos['shares'] * pos['buy_price'] 
            for pos in self.positions.values()
        )
        
        total_value = self.available_cash + position_value
        
        # 计算收益
        total_profit = total_value - self.initial_capital
        total_profit_pct = (total_profit / self.initial_capital) * 100
        
        return {
            'initial_capital': self.initial_capital,
            'available_cash': self.available_cash,
            'position_value': position_value,
            'total_value': total_value,
            'total_profit': total_profit,
            'total_profit_pct': total_profit_pct,
            'positions_count': len(self.positions),
            'max_stocks': self.max_stocks,
            'trade_count': len(self.trade_history)
        }
    
    def get_positions(self) -> List[Dict]:
        """获取当前持仓列表"""
        return [
            {
                'code': code,
                'name': pos['name'],
                'shares': pos['shares'],
                'buy_price': pos['buy_price'],
                'buy_date': pos['buy_date'],
                'holding_days': pos['holding_days']
            }
            for code, pos in self.positions.items()
        ]
    
    def get_trade_history(self) -> List[Dict]:
        """获取交易历史"""
        return self.trade_history.copy()
