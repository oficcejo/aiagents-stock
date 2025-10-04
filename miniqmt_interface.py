#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
MiniQMT量化交易接口
为监测板块提供量化交易功能预留接口
支持自动下单、仓位管理、策略执行等功能
"""

import json
from typing import Dict, List, Optional, Tuple
from datetime import datetime
from enum import Enum

class TradeAction(Enum):
    """交易动作枚举"""
    BUY = "buy"  # 买入
    SELL = "sell"  # 卖出
    HOLD = "hold"  # 持有
    
class OrderType(Enum):
    """订单类型枚举"""
    MARKET = "market"  # 市价单
    LIMIT = "limit"  # 限价单
    STOP = "stop"  # 止损单
    STOP_LIMIT = "stop_limit"  # 止损限价单

class PositionSide(Enum):
    """持仓方向枚举"""
    LONG = "long"  # 多头
    SHORT = "short"  # 空头
    NONE = "none"  # 无持仓

class MiniQMTInterface:
    """
    MiniQMT量化交易接口类
    提供与MiniQMT的对接功能
    """
    
    def __init__(self, config: Dict = None):
        """
        初始化接口
        
        Args:
            config: 配置字典，包含账户信息、连接参数等
        """
        self.config = config or {}
        self.connected = False
        self.account_id = None
        self.positions = {}  # 持仓信息
        self.orders = {}  # 订单信息
        self.enabled = self.config.get('enabled', False)
        
    def connect(self, account_id: str = None) -> Tuple[bool, str]:
        """
        连接到MiniQMT
        
        Args:
            account_id: 交易账户ID
            
        Returns:
            (成功标志, 消息)
        """
        try:
            # TODO: 实现与MiniQMT的实际连接逻辑
            self.account_id = account_id or self.config.get('account_id')
            
            if not self.account_id:
                return False, "账户ID未配置"
            
            # 预留接口：连接MiniQMT
            # from xtquant import xtdata
            # xtdata.connect()
            
            self.connected = True
            return True, f"已连接到账户 {self.account_id}"
            
        except Exception as e:
            self.connected = False
            return False, f"连接失败: {str(e)}"
    
    def disconnect(self) -> bool:
        """断开连接"""
        try:
            # TODO: 实现断开连接逻辑
            self.connected = False
            return True
        except Exception as e:
            print(f"断开连接失败: {e}")
            return False
    
    def is_connected(self) -> bool:
        """检查连接状态"""
        return self.connected and self.enabled
    
    def get_account_info(self) -> Dict:
        """
        获取账户信息
        
        Returns:
            账户信息字典
        """
        if not self.is_connected():
            return {
                'error': '未连接到MiniQMT',
                'connected': False
            }
        
        # TODO: 实现获取账户信息的逻辑
        # 预留接口：从MiniQMT获取账户信息
        return {
            'account_id': self.account_id,
            'total_assets': 0.0,  # 总资产
            'available_cash': 0.0,  # 可用资金
            'market_value': 0.0,  # 持仓市值
            'frozen_cash': 0.0,  # 冻结资金
            'profit_loss': 0.0,  # 盈亏
            'connected': True
        }
    
    def get_positions(self) -> List[Dict]:
        """
        获取当前持仓
        
        Returns:
            持仓列表
        """
        if not self.is_connected():
            return []
        
        # TODO: 实现获取持仓的逻辑
        # 预留接口：从MiniQMT获取持仓信息
        # from xtquant import xttrader
        # positions = xttrader.query_stock_positions(self.account_id)
        
        return list(self.positions.values())
    
    def get_position(self, symbol: str) -> Optional[Dict]:
        """
        获取指定股票的持仓
        
        Args:
            symbol: 股票代码
            
        Returns:
            持仓信息字典，无持仓返回None
        """
        if not self.is_connected():
            return None
        
        return self.positions.get(symbol)
    
    def place_order(self, 
                   symbol: str, 
                   action: TradeAction,
                   quantity: int,
                   price: float = None,
                   order_type: OrderType = OrderType.MARKET) -> Tuple[bool, str, str]:
        """
        下单
        
        Args:
            symbol: 股票代码
            action: 交易动作
            quantity: 数量
            price: 价格（限价单时需要）
            order_type: 订单类型
            
        Returns:
            (成功标志, 消息, 订单ID)
        """
        if not self.is_connected():
            return False, "未连接到MiniQMT", ""
        
        # 参数验证
        if quantity <= 0:
            return False, "数量必须大于0", ""
        
        if order_type == OrderType.LIMIT and price is None:
            return False, "限价单必须指定价格", ""
        
        try:
            # TODO: 实现实际下单逻辑
            # 预留接口：通过MiniQMT下单
            # from xtquant import xttrader
            # if action == TradeAction.BUY:
            #     order_id = xttrader.order_stock(
            #         self.account_id, symbol, 
            #         xtconstant.STOCK_BUY, quantity, 
            #         xtconstant.FIX_PRICE, price
            #     )
            # elif action == TradeAction.SELL:
            #     order_id = xttrader.order_stock(
            #         self.account_id, symbol, 
            #         xtconstant.STOCK_SELL, quantity, 
            #         xtconstant.FIX_PRICE, price
            #     )
            
            # 模拟订单ID
            order_id = f"ORD_{symbol}_{datetime.now().strftime('%Y%m%d%H%M%S')}"
            
            # 记录订单
            self.orders[order_id] = {
                'order_id': order_id,
                'symbol': symbol,
                'action': action.value,
                'quantity': quantity,
                'price': price,
                'order_type': order_type.value,
                'status': 'submitted',
                'create_time': datetime.now().isoformat()
            }
            
            return True, f"订单已提交: {order_id}", order_id
            
        except Exception as e:
            return False, f"下单失败: {str(e)}", ""
    
    def cancel_order(self, order_id: str) -> Tuple[bool, str]:
        """
        撤销订单
        
        Args:
            order_id: 订单ID
            
        Returns:
            (成功标志, 消息)
        """
        if not self.is_connected():
            return False, "未连接到MiniQMT"
        
        try:
            # TODO: 实现撤单逻辑
            # 预留接口：通过MiniQMT撤单
            # from xtquant import xttrader
            # xttrader.cancel_order(self.account_id, order_id)
            
            if order_id in self.orders:
                self.orders[order_id]['status'] = 'cancelled'
                return True, f"订单 {order_id} 已撤销"
            else:
                return False, "订单不存在"
                
        except Exception as e:
            return False, f"撤单失败: {str(e)}"
    
    def get_order_status(self, order_id: str) -> Optional[Dict]:
        """
        查询订单状态
        
        Args:
            order_id: 订单ID
            
        Returns:
            订单信息字典
        """
        if not self.is_connected():
            return None
        
        # TODO: 实现查询订单状态逻辑
        return self.orders.get(order_id)
    
    def get_all_orders(self) -> List[Dict]:
        """
        获取所有订单
        
        Returns:
            订单列表
        """
        if not self.is_connected():
            return []
        
        return list(self.orders.values())
    
    def execute_strategy_signal(self, 
                                stock_id: int,
                                symbol: str,
                                signal: Dict,
                                position_size: float = 0.2) -> Tuple[bool, str]:
        """
        执行策略信号
        根据监测触发的信号自动执行交易
        
        Args:
            stock_id: 监测股票ID
            symbol: 股票代码
            signal: 信号字典，包含type, price, message等
            position_size: 仓位比例（默认20%）
            
        Returns:
            (成功标志, 执行结果消息)
        """
        if not self.is_connected():
            return False, "MiniQMT未连接，无法执行交易"
        
        signal_type = signal.get('type')
        current_price = signal.get('price')
        
        try:
            # 获取账户信息
            account_info = self.get_account_info()
            available_cash = account_info.get('available_cash', 0)
            
            # 根据信号类型执行不同操作
            if signal_type == 'entry':
                # 进场信号 - 买入
                buy_amount = available_cash * position_size
                quantity = int(buy_amount / current_price / 100) * 100  # A股100股为一手
                
                if quantity > 0:
                    success, msg, order_id = self.place_order(
                        symbol=symbol,
                        action=TradeAction.BUY,
                        quantity=quantity,
                        price=current_price,
                        order_type=OrderType.LIMIT
                    )
                    
                    if success:
                        return True, f"进场买入成功: {quantity}股 @ ¥{current_price}, 订单号: {order_id}"
                    else:
                        return False, f"进场买入失败: {msg}"
                else:
                    return False, "可用资金不足，无法买入"
            
            elif signal_type == 'take_profit':
                # 止盈信号 - 卖出
                position = self.get_position(symbol)
                if position and position.get('quantity', 0) > 0:
                    quantity = position['quantity']
                    
                    success, msg, order_id = self.place_order(
                        symbol=symbol,
                        action=TradeAction.SELL,
                        quantity=quantity,
                        price=current_price,
                        order_type=OrderType.LIMIT
                    )
                    
                    if success:
                        return True, f"止盈卖出成功: {quantity}股 @ ¥{current_price}, 订单号: {order_id}"
                    else:
                        return False, f"止盈卖出失败: {msg}"
                else:
                    return False, "无持仓，无需卖出"
            
            elif signal_type == 'stop_loss':
                # 止损信号 - 紧急卖出
                position = self.get_position(symbol)
                if position and position.get('quantity', 0) > 0:
                    quantity = position['quantity']
                    
                    # 止损使用市价单，快速成交
                    success, msg, order_id = self.place_order(
                        symbol=symbol,
                        action=TradeAction.SELL,
                        quantity=quantity,
                        order_type=OrderType.MARKET
                    )
                    
                    if success:
                        return True, f"止损卖出成功: {quantity}股, 订单号: {order_id}"
                    else:
                        return False, f"止损卖出失败: {msg}"
                else:
                    return False, "无持仓，无需止损"
            
            else:
                return False, f"未知的信号类型: {signal_type}"
                
        except Exception as e:
            return False, f"执行策略信号失败: {str(e)}"
    
    def calculate_position_size(self, 
                               symbol: str,
                               price: float,
                               max_position_pct: float = 0.2,
                               max_risk_pct: float = 0.02) -> int:
        """
        计算建议仓位大小
        
        Args:
            symbol: 股票代码
            price: 买入价格
            max_position_pct: 最大仓位比例（默认20%）
            max_risk_pct: 最大风险比例（默认2%）
            
        Returns:
            建议买入数量（股）
        """
        if not self.is_connected():
            return 0
        
        try:
            account_info = self.get_account_info()
            total_assets = account_info.get('total_assets', 0)
            available_cash = account_info.get('available_cash', 0)
            
            # 基于最大仓位计算
            max_position_value = total_assets * max_position_pct
            
            # 基于可用资金计算
            max_buy_value = min(max_position_value, available_cash)
            
            # 计算股数（A股100股为一手）
            quantity = int(max_buy_value / price / 100) * 100
            
            return quantity
            
        except Exception as e:
            print(f"计算仓位失败: {e}")
            return 0
    
    def get_risk_metrics(self, symbol: str) -> Dict:
        """
        获取风险指标
        
        Args:
            symbol: 股票代码
            
        Returns:
            风险指标字典
        """
        if not self.is_connected():
            return {}
        
        position = self.get_position(symbol)
        if not position:
            return {
                'has_position': False,
                'profit_loss': 0,
                'profit_loss_pct': 0,
                'risk_exposure': 0
            }
        
        # 计算盈亏
        cost_price = position.get('cost_price', 0)
        current_price = position.get('current_price', 0)
        quantity = position.get('quantity', 0)
        
        profit_loss = (current_price - cost_price) * quantity
        profit_loss_pct = (current_price - cost_price) / cost_price * 100 if cost_price > 0 else 0
        
        # 计算风险敞口
        account_info = self.get_account_info()
        total_assets = account_info.get('total_assets', 0)
        position_value = current_price * quantity
        risk_exposure = position_value / total_assets if total_assets > 0 else 0
        
        return {
            'has_position': True,
            'quantity': quantity,
            'cost_price': cost_price,
            'current_price': current_price,
            'position_value': position_value,
            'profit_loss': profit_loss,
            'profit_loss_pct': profit_loss_pct,
            'risk_exposure': risk_exposure
        }
    
    def validate_trade(self, 
                      symbol: str,
                      action: TradeAction,
                      quantity: int,
                      price: float = None) -> Tuple[bool, str]:
        """
        验证交易是否可行
        
        Args:
            symbol: 股票代码
            action: 交易动作
            quantity: 数量
            price: 价格
            
        Returns:
            (可行标志, 原因)
        """
        if not self.is_connected():
            return False, "未连接到MiniQMT"
        
        # 检查数量
        if quantity <= 0:
            return False, "数量必须大于0"
        
        if quantity % 100 != 0:
            return False, "A股必须以100股（1手）为单位交易"
        
        # 获取账户信息
        account_info = self.get_account_info()
        
        if action == TradeAction.BUY:
            # 买入验证
            if price is None:
                return False, "买入需要指定价格"
            
            required_cash = quantity * price * 1.001  # 考虑手续费
            available_cash = account_info.get('available_cash', 0)
            
            if required_cash > available_cash:
                return False, f"资金不足: 需要¥{required_cash:.2f}, 可用¥{available_cash:.2f}"
            
            return True, "验证通过"
        
        elif action == TradeAction.SELL:
            # 卖出验证
            position = self.get_position(symbol)
            if not position:
                return False, "无持仓，无法卖出"
            
            available_quantity = position.get('quantity', 0)
            if quantity > available_quantity:
                return False, f"持仓不足: 需要{quantity}股, 可用{available_quantity}股"
            
            return True, "验证通过"
        
        return False, "未知的交易动作"


class QuantStrategyConfig:
    """量化策略配置"""
    
    def __init__(self):
        self.auto_trade_enabled = False  # 是否启用自动交易
        self.max_position_pct = 0.2  # 最大单个仓位比例
        self.max_total_position_pct = 0.8  # 最大总仓位比例
        self.max_risk_per_trade = 0.02  # 单笔最大风险比例
        self.min_trade_amount = 5000  # 最小交易金额
        self.use_stop_loss = True  # 是否使用止损
        self.use_take_profit = True  # 是否使用止盈
        self.trailing_stop_pct = 0.05  # 移动止损比例
    
    def to_dict(self) -> Dict:
        """转换为字典"""
        return {
            'auto_trade_enabled': self.auto_trade_enabled,
            'max_position_pct': self.max_position_pct,
            'max_total_position_pct': self.max_total_position_pct,
            'max_risk_per_trade': self.max_risk_per_trade,
            'min_trade_amount': self.min_trade_amount,
            'use_stop_loss': self.use_stop_loss,
            'use_take_profit': self.use_take_profit,
            'trailing_stop_pct': self.trailing_stop_pct
        }
    
    @classmethod
    def from_dict(cls, data: Dict):
        """从字典创建"""
        config = cls()
        config.auto_trade_enabled = data.get('auto_trade_enabled', False)
        config.max_position_pct = data.get('max_position_pct', 0.2)
        config.max_total_position_pct = data.get('max_total_position_pct', 0.8)
        config.max_risk_per_trade = data.get('max_risk_per_trade', 0.02)
        config.min_trade_amount = data.get('min_trade_amount', 5000)
        config.use_stop_loss = data.get('use_stop_loss', True)
        config.use_take_profit = data.get('use_take_profit', True)
        config.trailing_stop_pct = data.get('trailing_stop_pct', 0.05)
        return config


# 全局MiniQMT接口实例
miniqmt = MiniQMTInterface()


def init_miniqmt(config: Dict = None) -> Tuple[bool, str]:
    """
    初始化MiniQMT接口
    
    Args:
        config: 配置字典
        
    Returns:
        (成功标志, 消息)
    """
    global miniqmt
    
    try:
        # 从配置文件或环境变量读取配置
        if config is None:
            try:
                from config import MINIQMT_CONFIG
                config = MINIQMT_CONFIG
            except ImportError:
                config = {
                    'enabled': False,
                    'account_id': None
                }
        
        miniqmt = MiniQMTInterface(config)
        
        # 如果启用，尝试连接
        if config.get('enabled', False):
            success, msg = miniqmt.connect()
            return success, msg
        else:
            return True, "MiniQMT接口已初始化（未启用）"
            
    except Exception as e:
        return False, f"初始化MiniQMT接口失败: {str(e)}"


def get_miniqmt_status() -> Dict:
    """
    获取MiniQMT接口状态
    
    Returns:
        状态字典
    """
    global miniqmt
    
    return {
        'enabled': miniqmt.enabled,
        'connected': miniqmt.connected,
        'account_id': miniqmt.account_id,
        'ready': miniqmt.is_connected()
    }

