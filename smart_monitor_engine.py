"""
智能盯盘 - 主引擎
整合DeepSeek AI决策、数据获取、交易执行、通知等功能
"""

import logging
import time
from typing import Dict, List, Optional
from datetime import datetime
import threading

from smart_monitor_deepseek import SmartMonitorDeepSeek
from smart_monitor_data import SmartMonitorDataFetcher
from smart_monitor_qmt import SmartMonitorQMT, SmartMonitorQMTSimulator
from smart_monitor_db import SmartMonitorDB
from notification_service import notification_service  # 复用主程序的通知服务
from config_manager import config_manager  # 复用主程序的配置管理器


class SmartMonitorEngine:
    """智能盯盘引擎"""
    
    def __init__(self, deepseek_api_key: str = None, qmt_account_id: str = None,
                 use_simulator: bool = None):
        """
        初始化智能盯盘引擎
        
        Args:
            deepseek_api_key: DeepSeek API密钥（可选，从配置读取）
            qmt_account_id: miniQMT账户ID（可选，从配置读取）
            use_simulator: 是否使用模拟交易（可选，从配置读取）
        """
        self.logger = logging.getLogger(__name__)
        
        # 从配置管理器读取配置
        config = config_manager.read_env()
        
        # DeepSeek API
        if deepseek_api_key is None:
            deepseek_api_key = config.get('DEEPSEEK_API_KEY', '')
        
        # MiniQMT配置
        if qmt_account_id is None:
            qmt_account_id = config.get('MINIQMT_ACCOUNT_ID', '')
        
        if use_simulator is None:
            # 如果MINIQMT_ENABLED=false，则使用模拟器
            miniqmt_enabled = config.get('MINIQMT_ENABLED', 'false').lower() == 'true'
            use_simulator = not miniqmt_enabled
        
        # 初始化各个模块
        self.deepseek = SmartMonitorDeepSeek(deepseek_api_key)
        self.data_fetcher = SmartMonitorDataFetcher()
        self.db = SmartMonitorDB()
        self.notification = notification_service  # 使用主程序的通知服务
        
        # 初始化交易接口
        if use_simulator:
            self.qmt = SmartMonitorQMTSimulator()
            self.qmt.connect(qmt_account_id or "simulator")
            self.logger.info("使用模拟交易模式")
        else:
            self.qmt = SmartMonitorQMT()
            if qmt_account_id:
                success = self.qmt.connect(qmt_account_id)
                if success:
                    self.logger.info(f"已连接miniQMT账户: {qmt_account_id}")
                else:
                    self.logger.warning(f"连接miniQMT失败，切换到模拟模式")
                    self.qmt = SmartMonitorQMTSimulator()
                    self.qmt.connect("simulator")
            else:
                self.logger.warning("未配置miniQMT账户，使用模拟模式")
                self.qmt = SmartMonitorQMTSimulator()
                self.qmt.connect("simulator")
        
        # 监控线程控制
        self.monitoring_threads = {}
        self.stop_flags = {}
        
        self.logger.info("智能盯盘引擎初始化完成")
    
    def analyze_stock(self, stock_code: str, auto_trade: bool = False,
                     notify: bool = True, has_position: bool = False,
                     position_cost: float = 0, position_quantity: int = 0,
                     trading_hours_only: bool = True) -> Dict:
        """
        分析单只股票并做出决策
        
        Args:
            stock_code: 股票代码
            auto_trade: 是否自动交易
            notify: 是否发送通知
            has_position: 是否已持仓（可选）
            position_cost: 持仓成本（可选）
            position_quantity: 持仓数量（可选）
            trading_hours_only: 是否仅在交易时段分析（可选，默认True）
            
        Returns:
            分析结果
        """
        try:
            self.logger.info(f"[{stock_code}] 开始分析...")
            
            # 1. 检查交易时段
            session_info = self.deepseek.get_trading_session()
            self.logger.info(f"[{stock_code}] 当前时段: {session_info['session']}")
            
            # 如果启用了仅交易时段分析，且当前不在交易时段，则跳过分析
            if trading_hours_only and not session_info.get('can_trade', False):
                self.logger.info(f"[{stock_code}] 非交易时段，跳过分析")
                return {
                    'success': False,
                    'error': f"非交易时段（{session_info['session']}），跳过分析",
                    'session_info': session_info,
                    'skipped': True
                }
            
            # 2. 获取市场数据
            market_data = self.data_fetcher.get_comprehensive_data(stock_code)
            if not market_data:
                return {
                    'success': False,
                    'error': '获取市场数据失败'
                }
            
            # 3. 获取账户信息
            account_info = self.qmt.get_account_info()
            
            # 4. 检查是否已持有该股票
            # 优先使用传入的持仓信息，否则从QMT获取
            if has_position and position_cost > 0 and position_quantity > 0:
                # 使用用户设置的持仓信息
                self.logger.info(f"[{stock_code}] 使用监控任务设置的持仓: {position_quantity}股 @ {position_cost:.2f}元")
            else:
                # 从QMT获取持仓
                position = self.qmt.get_position(stock_code)
                has_position = position is not None
                
                if has_position:
                    position_cost = position.get('cost_price', 0)
                    position_quantity = position.get('quantity', 0)
                    account_info['current_position'] = position
                    self.logger.info(f"[{stock_code}] 从QMT获取持仓: {position_quantity}股, "
                                   f"成本价: {position_cost:.2f}, "
                                   f"浮动盈亏: {position.get('profit_loss_pct', 0):+.2f}%")
            
            # 5. 调用DeepSeek AI决策
            ai_result = self.deepseek.analyze_stock_and_decide(
                stock_code=stock_code,
                market_data=market_data,
                account_info=account_info,
                has_position=has_position,
                position_cost=position_cost,
                position_quantity=position_quantity
            )
            
            if not ai_result['success']:
                return {
                    'success': False,
                    'error': 'AI决策失败',
                    'details': ai_result
                }
            
            decision = ai_result['decision']
            
            self.logger.info(f"[{stock_code}] AI决策: {decision['action']} "
                           f"(信心度: {decision['confidence']}%)")
            self.logger.info(f"[{stock_code}] 决策理由: {decision['reasoning'][:100]}...")
            
            # 6. 保存AI决策到数据库
            decision_id = self.db.save_ai_decision({
                'stock_code': stock_code,
                'stock_name': market_data.get('name'),
                'trading_session': session_info['session'],
                'action': decision['action'],
                'confidence': decision['confidence'],
                'reasoning': decision['reasoning'],
                'position_size_pct': decision.get('position_size_pct'),
                'stop_loss_pct': decision.get('stop_loss_pct'),
                'take_profit_pct': decision.get('take_profit_pct'),
                'risk_level': decision.get('risk_level'),
                'key_price_levels': decision.get('key_price_levels', {}),
                'market_data': market_data,
                'account_info': account_info
            })
            
            # 7. 执行交易（如果开启自动交易）
            execution_result = None
            if auto_trade and session_info['can_trade']:
                execution_result = self._execute_decision(
                    stock_code=stock_code,
                    decision=decision,
                    market_data=market_data,
                    has_position=has_position
                )
                
                # 更新决策执行状态
                self.db.update_decision_execution(
                    decision_id=decision_id,
                    executed=execution_result.get('success', False),
                    result=str(execution_result)
                )
            
            # 8. 发送通知
            if notify:
                self._send_notification(
                    stock_code=stock_code,
                    stock_name=market_data.get('name'),
                    decision=decision,
                    execution_result=execution_result,
                    market_data=market_data
                )
            
            return {
                'success': True,
                'stock_code': stock_code,
                'stock_name': market_data.get('name'),
                'session_info': session_info,
                'market_data': market_data,
                'decision': decision,
                'decision_id': decision_id,
                'execution_result': execution_result
            }
            
        except Exception as e:
            self.logger.error(f"[{stock_code}] 分析失败: {e}")
            import traceback
            traceback.print_exc()
            return {
                'success': False,
                'error': str(e)
            }
    
    def _execute_decision(self, stock_code: str, decision: Dict,
                         market_data: Dict, has_position: bool) -> Dict:
        """
        执行AI决策
        
        Args:
            stock_code: 股票代码
            decision: AI决策
            market_data: 市场数据
            has_position: 是否已持有
            
        Returns:
            执行结果
        """
        action = decision['action']
        
        try:
            if action == 'BUY' and not has_position:
                # 买入逻辑
                return self._execute_buy(stock_code, decision, market_data)
            
            elif action == 'SELL' and has_position:
                # 卖出逻辑
                return self._execute_sell(stock_code, decision, market_data)
            
            elif action == 'HOLD':
                # 持有，不操作
                return {
                    'success': True,
                    'action': 'HOLD',
                    'message': 'AI建议持有，未执行交易'
                }
            
            else:
                return {
                    'success': False,
                    'error': f'无效操作: {action}'
                }
                
        except Exception as e:
            self.logger.error(f"[{stock_code}] 执行交易失败: {e}")
            return {
                'success': False,
                'error': str(e)
            }
    
    def _execute_buy(self, stock_code: str, decision: Dict, market_data: Dict) -> Dict:
        """执行买入"""
        try:
            # 获取账户信息
            account_info = self.qmt.get_account_info()
            available_cash = account_info['available_cash']
            
            # 计算买入金额
            position_size_pct = decision.get('position_size_pct', 20)
            buy_amount = available_cash * (position_size_pct / 100)
            
            # 计算买入数量（必须是100的整数倍）
            current_price = market_data['current_price']
            quantity = int(buy_amount / current_price / 100) * 100
            
            if quantity < 100:
                return {
                    'success': False,
                    'error': f'资金不足，最少需要买入100股（约{current_price * 100:.2f}元）'
                }
            
            # 执行买入
            result = self.qmt.buy_stock(
                stock_code=stock_code,
                quantity=quantity,
                price=current_price,
                order_type='market'
            )
            
            if result['success']:
                # 保存交易记录
                self.db.save_trade_record({
                    'stock_code': stock_code,
                    'stock_name': market_data.get('name'),
                    'trade_type': 'BUY',
                    'quantity': quantity,
                    'price': current_price,
                    'amount': quantity * current_price,
                    'order_id': result.get('order_id'),
                    'order_status': '已提交'
                })
                
                # 保存持仓监控
                self.db.save_position({
                    'stock_code': stock_code,
                    'stock_name': market_data.get('name'),
                    'quantity': quantity,
                    'cost_price': current_price,
                    'current_price': current_price,
                    'profit_loss': 0,
                    'profit_loss_pct': 0,
                    'holding_days': 0,
                    'buy_date': datetime.now().strftime('%Y-%m-%d'),
                    'stop_loss_price': current_price * (1 - decision.get('stop_loss_pct', 5) / 100),
                    'take_profit_price': current_price * (1 + decision.get('take_profit_pct', 10) / 100)
                })
                
                self.logger.info(f"[{stock_code}] 买入成功: {quantity}股 @ {current_price:.2f}元")
            
            return result
            
        except Exception as e:
            self.logger.error(f"[{stock_code}] 买入失败: {e}")
            return {
                'success': False,
                'error': str(e)
            }
    
    def _execute_sell(self, stock_code: str, decision: Dict, market_data: Dict) -> Dict:
        """执行卖出"""
        try:
            # 获取持仓
            position = self.qmt.get_position(stock_code)
            if not position:
                return {
                    'success': False,
                    'error': '未持有该股票'
                }
            
            # 可卖数量（考虑T+1限制）
            can_sell = position['can_sell']
            if can_sell <= 0:
                return {
                    'success': False,
                    'error': 'T+1限制，今天买入的股票明天才能卖出'
                }
            
            # 执行卖出
            current_price = market_data['current_price']
            result = self.qmt.sell_stock(
                stock_code=stock_code,
                quantity=can_sell,
                price=current_price,
                order_type='market'
            )
            
            if result['success']:
                # 计算盈亏
                profit_loss = (current_price - position['cost_price']) * can_sell
                
                # 保存交易记录
                self.db.save_trade_record({
                    'stock_code': stock_code,
                    'stock_name': market_data.get('name'),
                    'trade_type': 'SELL',
                    'quantity': can_sell,
                    'price': current_price,
                    'amount': can_sell * current_price,
                    'order_id': result.get('order_id'),
                    'order_status': '已提交',
                    'profit_loss': profit_loss
                })
                
                # 更新或关闭持仓记录
                if can_sell >= position['quantity']:
                    self.db.close_position(stock_code)
                
                self.logger.info(f"[{stock_code}] 卖出成功: {can_sell}股 @ {current_price:.2f}元, "
                               f"盈亏: {profit_loss:+.2f}元")
            
            return result
            
        except Exception as e:
            self.logger.error(f"[{stock_code}] 卖出失败: {e}")
            return {
                'success': False,
                'error': str(e)
            }
    
    def _send_notification(self, stock_code: str, stock_name: str,
                          decision: Dict, execution_result: Optional[Dict],
                          market_data: Dict):
        """
        发送通知（使用主程序的通知服务）
        优化策略：仅在买入或卖出信号时发送通知，持有信号不发送
        """
        try:
            action = decision['action'].upper()
            
            # 仅在买入或卖出时发送通知，持有信号不发送
            if action not in ['BUY', 'SELL']:
                self.logger.info(f"[{stock_code}] 决策为{action}，不发送通知")
                return
            
            # 构建通知内容
            action_text = {
                'BUY': '🟢 买入',
                'SELL': '🔴 卖出'
            }.get(action, action)
            
            message = f"{action_text}信号 - {stock_name}({stock_code})"
            
            # 简化的AI决策内容（提取核心信息）
            reasoning_summary = decision['reasoning'][:150] + '...' if len(decision['reasoning']) > 150 else decision['reasoning']
            
            # 提取关键价位信息
            key_levels = decision.get('key_price_levels', {})
            support = key_levels.get('support', 'N/A')
            resistance = key_levels.get('resistance', 'N/A')
            
            # 构建简化的详细内容
            content = f"""
【{action_text}信号】{stock_name}({stock_code})

📊 市场信息
• 当前价: ¥{market_data.get('current_price', 0):.2f}
• 涨跌幅: {market_data.get('change_pct', 0):+.2f}%
• 成交量: {market_data.get('volume', 0):,.0f}手

🤖 AI决策
• 操作: {action_text}
• 信心度: {decision['confidence']}%
• 风险: {decision.get('risk_level', '中')}

💡 核心理由
{reasoning_summary}

📈 关键价位
• 支撑位: {support}
• 阻力位: {resistance}
• 止盈: {decision.get('take_profit_pct', 'N/A')}%
• 止损: {decision.get('stop_loss_pct', 'N/A')}%

📉 技术指标
• MA5: {market_data.get('ma5', 0):.2f} / MA20: {market_data.get('ma20', 0):.2f}
• RSI(6): {market_data.get('rsi6', 0):.1f}
• MACD: {market_data.get('macd', 0):.4f}
"""
            
            if execution_result:
                if execution_result.get('success'):
                    content += f"\n✅ 操作已自动执行"
                else:
                    content += f"\n⚠️ 执行失败: {execution_result.get('error')}"
            
            content += f"\n\n⏰ {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
            
            # 使用主程序的通知服务格式
            notification_data = {
                'symbol': stock_code,
                'name': stock_name,
                'type': '智能盯盘',
                'message': message,
                'details': content,
                'triggered_at': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            }
            
            # 直接调用主程序的通知服务发送
            success = self.notification.send_notification(notification_data)
            
            if success:
                self.logger.info(f"[{stock_code}] {action_text}通知已发送")
            else:
                self.logger.warning(f"[{stock_code}] 通知发送失败")
            
            # 同时保存到智能盯盘的数据库
            self.db.save_notification({
                'stock_code': stock_code,
                'notify_type': 'decision',
                'subject': f"智能盯盘 - {message}",
                'content': content,
                'status': 'sent' if success else 'failed'
            })
            
        except Exception as e:
            self.logger.error(f"[{stock_code}] 发送通知失败: {e}")
            import traceback
            traceback.print_exc()
    
    def start_monitor(self, stock_code: str, check_interval: int = 300,
                     auto_trade: bool = False, notify: bool = True,
                     has_position: bool = False, position_cost: float = 0,
                     position_quantity: int = 0, trading_hours_only: bool = True):
        """
        启动股票监控（在独立线程中运行）
        
        Args:
            stock_code: 股票代码
            check_interval: 检查间隔（秒）
            auto_trade: 是否自动交易
            notify: 是否发送通知
            has_position: 是否已持仓
            position_cost: 持仓成本
            position_quantity: 持仓数量
            trading_hours_only: 是否仅在交易时段监控（默认True）
        """
        if stock_code in self.monitoring_threads:
            self.logger.warning(f"[{stock_code}] 监控已在运行中")
            return
        
        # 创建停止标志
        stop_flag = threading.Event()
        self.stop_flags[stock_code] = stop_flag
        
        # 创建监控线程
        thread = threading.Thread(
            target=self._monitor_loop,
            args=(stock_code, check_interval, auto_trade, notify, stop_flag,
                 has_position, position_cost, position_quantity, trading_hours_only),
            daemon=True
        )
        
        self.monitoring_threads[stock_code] = thread
        thread.start()
        
        position_info = f"（持仓: {position_quantity}股 @ {position_cost:.2f}元）" if has_position else ""
        trading_info = "（仅交易时段）" if trading_hours_only else "（全时段）"
        self.logger.info(f"[{stock_code}] 监控已启动{trading_info}，间隔: {check_interval}秒 {position_info}")
    
    def stop_monitor(self, stock_code: str):
        """停止股票监控"""
        if stock_code not in self.monitoring_threads:
            self.logger.warning(f"[{stock_code}] 监控未运行")
            return
        
        # 设置停止标志
        self.stop_flags[stock_code].set()
        
        # 等待线程结束
        self.monitoring_threads[stock_code].join(timeout=5)
        
        # 清理
        del self.monitoring_threads[stock_code]
        del self.stop_flags[stock_code]
        
        self.logger.info(f"[{stock_code}] 监控已停止")
    
    def _monitor_loop(self, stock_code: str, check_interval: int,
                     auto_trade: bool, notify: bool, stop_flag: threading.Event,
                     has_position: bool = False, position_cost: float = 0,
                     position_quantity: int = 0, trading_hours_only: bool = True):
        """监控循环（在独立线程中运行）"""
        self.logger.info(f"[{stock_code}] 监控线程已启动")
        
        while not stop_flag.is_set():
            try:
                # 执行分析
                result = self.analyze_stock(
                    stock_code=stock_code,
                    auto_trade=auto_trade,
                    notify=notify,
                    has_position=has_position,
                    position_cost=position_cost,
                    position_quantity=position_quantity,
                    trading_hours_only=trading_hours_only
                )
                
                if result.get('skipped'):
                    # 非交易时段跳过，不算错误
                    self.logger.debug(f"[{stock_code}] {result.get('error')}")
                elif result['success']:
                    self.logger.info(f"[{stock_code}] 分析完成: {result['decision']['action']}")
                else:
                    self.logger.error(f"[{stock_code}] 分析失败: {result.get('error')}")
                
            except Exception as e:
                self.logger.error(f"[{stock_code}] 监控循环异常: {e}")
            
            # 等待下一次检查
            stop_flag.wait(check_interval)
        
        self.logger.info(f"[{stock_code}] 监控线程已退出")


if __name__ == '__main__':
    # 测试代码
    import os
    from dotenv import load_dotenv
    
    load_dotenv()
    
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    # 使用模拟模式测试
    engine = SmartMonitorEngine(
        deepseek_api_key=os.getenv('DEEPSEEK_API_KEY'),
        use_simulator=True
    )
    
    # 测试分析贵州茅台
    print("\n测试分析贵州茅台(600519)...")
    result = engine.analyze_stock('600519', auto_trade=False, notify=False)
    
    if result['success']:
        print(f"\n分析成功!")
        print(f"  决策: {result['decision']['action']}")
        print(f"  信心度: {result['decision']['confidence']}%")
        print(f"  理由: {result['decision']['reasoning'][:100]}...")
    else:
        print(f"\n分析失败: {result.get('error')}")

