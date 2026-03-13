"""
智能盯盘 - miniQMT交易接口适配器
封装miniQMT的交易功能，支持A股T+1交易
使用主程序的配置管理系统
"""

import logging
import os
from typing import Dict, List, Optional
from datetime import datetime


class SmartMonitorQMT:
    """miniQMT交易接口"""
    
    def __init__(self, mini_qmt_path: str = None):
        """
        初始化miniQMT接口
        
        Args:
            mini_qmt_path: miniQMT安装路径
        """
        self.logger = logging.getLogger(__name__)
        self.xt_trader = None
        self.account = None
        self.connected = False
        
        # 尝试导入miniQMT
        try:
            from xtquant import xttrader, xtdata
            self.xttrader = xttrader
            self.xtdata = xtdata
            self.logger.info("miniQMT模块加载成功")
        except ImportError as e:
            self.logger.warning(f"miniQMT模块未安装: {e}")
            self.logger.warning("将使用模拟模式（不实际下单）")
    
    def connect(self, account_id: str = None) -> bool:
        """
        连接miniQMT
        
        Args:
            account_id: 交易账户ID（可选，从环境变量读取）
            
        Returns:
            是否连接成功
        """
        if not self.xttrader:
            self.logger.warning("miniQMT未安装，使用模拟模式")
            self.connected = False
            return False
        
        # 从配置读取账户ID
        if account_id is None:
            account_id = os.getenv('MINIQMT_ACCOUNT_ID', '')
        
        if not account_id:
            self.logger.error("未配置miniQMT账户ID，请在环境配置中设置")
            self.connected = False
            return False
        
        try:
            # 创建交易对象
            self.xt_trader = self.xttrader.XtQuantTrader()
            
            # 连接
            self.xt_trader.start()
            
            # 连接账户
            self.account = self.xttrader.StockAccount(account_id)
            connect_result = self.xt_trader.connect()
            
            if connect_result == 0:
                self.connected = True
                self.logger.info(f"miniQMT连接成功，账户: {account_id}")
                return True
            else:
                self.logger.error(f"miniQMT连接失败，错误码: {connect_result}")
                return False
                
        except Exception as e:
            self.logger.error(f"连接miniQMT失败: {e}")
            return False
    
    def disconnect(self):
        """断开连接"""
        if self.xt_trader:
            try:
                self.xt_trader.stop()
                self.connected = False
                self.logger.info("miniQMT已断开连接")
            except Exception as e:
                self.logger.error(f"断开连接失败: {e}")
    
    def get_account_info(self) -> Dict:
        """
        获取账户信息
        
        Returns:
            账户信息字典
        """
        if not self.connected or not self.account:
            return {
                'available_cash': 0,
                'total_value': 0,
                'positions_count': 0,
                'total_profit_loss': 0
            }
        
        try:
            # 获取资金信息
            asset = self.xt_trader.query_stock_asset(self.account)
            
            # 获取持仓信息
            positions = self.xt_trader.query_stock_positions(self.account)
            
            # 计算总浮动盈亏
            total_profit_loss = 0
            if positions:
                for pos in positions:
                    total_profit_loss += pos.unrealized_profit
            
            return {
                'available_cash': asset.cash,  # 可用资金
                'total_value': asset.total_asset,  # 总资产
                'positions_count': len(positions) if positions else 0,
                'total_profit_loss': total_profit_loss,
                'frozen_cash': asset.frozen_cash,  # 冻结资金
                'market_value': asset.market_value  # 持仓市值
            }
            
        except Exception as e:
            self.logger.error(f"获取账户信息失败: {e}")
            return {
                'available_cash': 0,
                'total_value': 0,
                'positions_count': 0,
                'total_profit_loss': 0
            }
    
    def get_position(self, stock_code: str) -> Optional[Dict]:
        """
        获取指定股票的持仓信息
        
        Args:
            stock_code: 股票代码
            
        Returns:
            持仓信息，如果未持有则返回None
        """
        if not self.connected or not self.account:
            return None
        
        try:
            positions = self.xt_trader.query_stock_positions(self.account)
            
            if not positions:
                return None
            
            # 查找指定股票
            for pos in positions:
                if pos.stock_code == stock_code:
                    # 计算持仓天数
                    holding_days = 0
                    if hasattr(pos, 'open_date'):
                        try:
                            open_date = datetime.strptime(str(pos.open_date), '%Y%m%d')
                            holding_days = (datetime.now() - open_date).days
                        except:
                            pass
                    
                    return {
                        'stock_code': pos.stock_code,
                        'stock_name': getattr(pos, 'stock_name', ''),
                        'quantity': pos.volume,  # 持仓数量
                        'can_sell': pos.can_use_volume,  # 可用数量（考虑T+1）
                        'cost_price': pos.avg_price,  # 成本价
                        'current_price': pos.last_price,  # 最新价
                        'market_value': pos.market_value,  # 市值
                        'profit_loss': pos.unrealized_profit,  # 浮动盈亏
                        'profit_loss_pct': (pos.last_price - pos.avg_price) / pos.avg_price * 100 if pos.avg_price > 0 else 0,
                        'holding_days': holding_days,
                        'buy_date': getattr(pos, 'open_date', '')
                    }
            
            return None
            
        except Exception as e:
            self.logger.error(f"获取持仓信息失败 {stock_code}: {e}")
            return None
    
    def get_all_positions(self) -> List[Dict]:
        """
        获取所有持仓
        
        Returns:
            持仓列表
        """
        if not self.connected or not self.account:
            return []
        
        try:
            positions = self.xt_trader.query_stock_positions(self.account)
            
            if not positions:
                return []
            
            result = []
            for pos in positions:
                holding_days = 0
                if hasattr(pos, 'open_date'):
                    try:
                        open_date = datetime.strptime(str(pos.open_date), '%Y%m%d')
                        holding_days = (datetime.now() - open_date).days
                    except:
                        pass
                
                result.append({
                    'stock_code': pos.stock_code,
                    'stock_name': getattr(pos, 'stock_name', ''),
                    'quantity': pos.volume,
                    'can_sell': pos.can_use_volume,
                    'cost_price': pos.avg_price,
                    'current_price': pos.last_price,
                    'market_value': pos.market_value,
                    'profit_loss': pos.unrealized_profit,
                    'profit_loss_pct': (pos.last_price - pos.avg_price) / pos.avg_price * 100 if pos.avg_price > 0 else 0,
                    'holding_days': holding_days
                })
            
            return result
            
        except Exception as e:
            self.logger.error(f"获取所有持仓失败: {e}")
            return []
    
    def buy_stock(self, stock_code: str, quantity: int, 
                 price: float = 0, order_type: str = 'market') -> Dict:
        """
        买入股票
        
        Args:
            stock_code: 股票代码（如：600519.SH）
            quantity: 数量（股，必须是100的整数倍）
            price: 价格（限价单时使用，市价单可为0）
            order_type: 订单类型 ('market': 市价, 'limit': 限价)
            
        Returns:
            订单结果
        """
        if not self.connected:
            return {
                'success': False,
                'error': 'miniQMT未连接',
                'message': '模拟模式：买入订单已记录但未实际执行'
            }
        
        # 检查数量是否是100的整数倍
        if quantity % 100 != 0:
            return {
                'success': False,
                'error': 'A股买入数量必须是100的整数倍（1手=100股）'
            }
        
        try:
            # 构造完整股票代码（带市场后缀）
            full_code = self._format_stock_code(stock_code)
            
            # 根据订单类型选择价格类型
            if order_type == 'market':
                # 市价单
                price_type = self.xttrader.XTP_PRICE_MARKET_OR_CANCEL  # 市价剩余转限价
            else:
                # 限价单
                price_type = self.xttrader.XTP_PRICE_LIMIT
            
            # 下单
            order_id = self.xt_trader.order_stock(
                account=self.account,
                stock_code=full_code,
                order_type=self.xttrader.XTP_SIDE_BUY,  # 买入
                order_volume=quantity,
                price_type=price_type,
                price=price
            )
            
            if order_id > 0:
                self.logger.info(f"买入订单已提交: {stock_code}, 数量: {quantity}, 订单号: {order_id}")
                return {
                    'success': True,
                    'order_id': order_id,
                    'stock_code': stock_code,
                    'quantity': quantity,
                    'price': price,
                    'order_type': order_type,
                    'message': '买入订单已提交'
                }
            else:
                return {
                    'success': False,
                    'error': f'下单失败，订单号: {order_id}'
                }
                
        except Exception as e:
            self.logger.error(f"买入股票失败 {stock_code}: {e}")
            return {
                'success': False,
                'error': str(e)
            }
    
    def sell_stock(self, stock_code: str, quantity: int, 
                  price: float = 0, order_type: str = 'market') -> Dict:
        """
        卖出股票
        
        Args:
            stock_code: 股票代码
            quantity: 数量（股）
            price: 价格（限价单时使用）
            order_type: 订单类型 ('market': 市价, 'limit': 限价)
            
        Returns:
            订单结果
        """
        if not self.connected:
            return {
                'success': False,
                'error': 'miniQMT未连接',
                'message': '模拟模式：卖出订单已记录但未实际执行'
            }
        
        try:
            # 检查是否有持仓
            position = self.get_position(stock_code)
            if not position:
                return {
                    'success': False,
                    'error': f'未持有股票 {stock_code}'
                }
            
            # 检查可卖数量（T+1限制）
            if quantity > position['can_sell']:
                return {
                    'success': False,
                    'error': f'可卖数量不足（可卖: {position["can_sell"]}股，T+1限制）'
                }
            
            # 构造完整股票代码
            full_code = self._format_stock_code(stock_code)
            
            # 根据订单类型选择价格类型
            if order_type == 'market':
                price_type = self.xttrader.XTP_PRICE_MARKET_OR_CANCEL
            else:
                price_type = self.xttrader.XTP_PRICE_LIMIT
            
            # 下单
            order_id = self.xt_trader.order_stock(
                account=self.account,
                stock_code=full_code,
                order_type=self.xttrader.XTP_SIDE_SELL,  # 卖出
                order_volume=quantity,
                price_type=price_type,
                price=price
            )
            
            if order_id > 0:
                self.logger.info(f"卖出订单已提交: {stock_code}, 数量: {quantity}, 订单号: {order_id}")
                return {
                    'success': True,
                    'order_id': order_id,
                    'stock_code': stock_code,
                    'quantity': quantity,
                    'price': price,
                    'order_type': order_type,
                    'message': '卖出订单已提交'
                }
            else:
                return {
                    'success': False,
                    'error': f'下单失败，订单号: {order_id}'
                }
                
        except Exception as e:
            self.logger.error(f"卖出股票失败 {stock_code}: {e}")
            return {
                'success': False,
                'error': str(e)
            }
    
    def cancel_order(self, order_id: int) -> bool:
        """
        撤销订单
        
        Args:
            order_id: 订单ID
            
        Returns:
            是否撤销成功
        """
        if not self.connected:
            return False
        
        try:
            result = self.xt_trader.cancel_order_stock(self.account, order_id)
            if result == 0:
                self.logger.info(f"订单已撤销: {order_id}")
                return True
            else:
                self.logger.error(f"撤销订单失败: {order_id}, 错误码: {result}")
                return False
        except Exception as e:
            self.logger.error(f"撤销订单失败: {e}")
            return False
    
    def get_orders(self, stock_code: str = None) -> List[Dict]:
        """
        获取当日委托订单
        
        Args:
            stock_code: 股票代码（可选，不传则返回所有订单）
            
        Returns:
            订单列表
        """
        if not self.connected:
            return []
        
        try:
            orders = self.xt_trader.query_stock_orders(self.account)
            
            if not orders:
                return []
            
            result = []
            for order in orders:
                # 如果指定了股票代码，则过滤
                if stock_code and order.stock_code != self._format_stock_code(stock_code):
                    continue
                
                result.append({
                    'order_id': order.order_id,
                    'stock_code': order.stock_code,
                    'stock_name': getattr(order, 'stock_name', ''),
                    'order_type': '买入' if order.order_type == self.xttrader.XTP_SIDE_BUY else '卖出',
                    'price': order.price,
                    'quantity': order.order_volume,
                    'traded_quantity': order.traded_volume,
                    'status': self._format_order_status(order.order_status),
                    'order_time': getattr(order, 'insert_time', '')
                })
            
            return result
            
        except Exception as e:
            self.logger.error(f"获取订单失败: {e}")
            return []
    
    def _format_stock_code(self, stock_code: str) -> str:
        """
        格式化股票代码（添加市场后缀）
        
        Args:
            stock_code: 股票代码（如：600519）
            
        Returns:
            完整代码（如：600519.SH）
        """
        # 如果已经包含市场后缀，直接返回
        if '.' in stock_code:
            return stock_code
        
        # 沪市：6开头
        if stock_code.startswith('6'):
            return f"{stock_code}.SH"
        # 深市：0、3开头
        elif stock_code.startswith(('0', '3')):
            return f"{stock_code}.SZ"
        else:
            return stock_code
    
    def _format_order_status(self, status: int) -> str:
        """格式化订单状态"""
        status_map = {
            0: '未报',
            1: '待报',
            2: '已报',
            3: '已报待撤',
            4: '部分待撤',
            5: '部成待撤',
            6: '部撤',
            7: '已撤',
            8: '部成',
            9: '已成',
            10: '废单'
        }
        return status_map.get(status, f'未知({status})')


# 模拟交易类（当miniQMT不可用时使用）
class SmartMonitorQMTSimulator:
    """模拟交易（用于测试）"""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.connected = True
        self.cash = 100000  # 模拟资金10万
        self.positions = {}  # 模拟持仓
        self.orders = []  # 模拟订单
        self.logger.info("使用模拟交易模式")
    
    def connect(self, account_id: str) -> bool:
        self.logger.info(f"模拟连接成功: {account_id}")
        return True
    
    def disconnect(self):
        self.logger.info("模拟断开连接")
    
    def get_account_info(self) -> Dict:
        total_value = self.cash
        for pos in self.positions.values():
            total_value += pos['market_value']
        
        return {
            'available_cash': self.cash,
            'total_value': total_value,
            'positions_count': len(self.positions),
            'total_profit_loss': sum(pos['profit_loss'] for pos in self.positions.values())
        }
    
    def get_position(self, stock_code: str) -> Optional[Dict]:
        return self.positions.get(stock_code)
    
    def get_all_positions(self) -> List[Dict]:
        """获取所有持仓"""
        return list(self.positions.values())
    
    def buy_stock(self, stock_code: str, quantity: int, 
                 price: float = 0, order_type: str = 'market') -> Dict:
        cost = quantity * price if price > 0 else quantity * 10  # 假设价格
        if cost > self.cash:
            return {'success': False, 'error': '资金不足'}
        
        self.cash -= cost
        
        # 获取股票名称（简化版，实际应该从数据源获取）
        stock_name = f"股票{stock_code}"
        
        self.positions[stock_code] = {
            'stock_code': stock_code,
            'stock_name': stock_name,
            'quantity': quantity,
            'can_sell': 0,  # T+1，今天买入不能卖
            'cost_price': price if price > 0 else 10,
            'current_price': price if price > 0 else 10,
            'market_value': cost,
            'profit_loss': 0,
            'profit_loss_pct': 0,
            'holding_days': 0,
            'buy_date': datetime.now().strftime('%Y%m%d')
        }
        
        # 记录订单
        self.orders.append({
            'order_id': len(self.orders) + 1,
            'stock_code': stock_code,
            'order_type': 'BUY',
            'quantity': quantity,
            'price': price,
            'status': '已成交',
            'order_time': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        })
        
        self.logger.info(f"[模拟] 买入 {stock_code} {quantity}股 @ {price:.2f}元")
        return {'success': True, 'order_id': len(self.orders), 'message': '模拟买入成功'}
    
    def sell_stock(self, stock_code: str, quantity: int, 
                  price: float = 0, order_type: str = 'market') -> Dict:
        if stock_code not in self.positions:
            return {'success': False, 'error': '未持有该股票'}
        
        pos = self.positions[stock_code]
        if quantity > pos['can_sell']:
            return {'success': False, 'error': 'T+1限制，今天买入不能卖'}
        
        sell_price = price if price > 0 else pos['current_price']
        revenue = quantity * sell_price
        self.cash += revenue
        
        # 计算盈亏
        profit_loss = (sell_price - pos['cost_price']) * quantity
        
        # 记录订单
        self.orders.append({
            'order_id': len(self.orders) + 1,
            'stock_code': stock_code,
            'order_type': 'SELL',
            'quantity': quantity,
            'price': sell_price,
            'status': '已成交',
            'order_time': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        })
        
        # 更新或删除持仓
        if quantity >= pos['quantity']:
            del self.positions[stock_code]
        else:
            pos['quantity'] -= quantity
            pos['can_sell'] -= quantity
            pos['market_value'] = pos['quantity'] * pos['current_price']
        
        self.logger.info(f"[模拟] 卖出 {stock_code} {quantity}股 @ {sell_price:.2f}元, 盈亏: {profit_loss:+.2f}元")
        return {
            'success': True, 
            'order_id': len(self.orders), 
            'profit_loss': profit_loss,
            'message': '模拟卖出成功'
        }
    
    def cancel_order(self, order_id: int) -> bool:
        """撤销订单（模拟）"""
        self.logger.info(f"[模拟] 撤销订单 {order_id}")
        return True
    
    def get_orders(self, stock_code: str = None) -> List[Dict]:
        """获取订单列表（模拟）"""
        return self.orders

