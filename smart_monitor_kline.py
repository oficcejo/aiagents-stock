"""
智能盯盘 - K线图绘制模块
支持AI决策标注、实时更新
"""

import plotly.graph_objects as go
from plotly.subplots import make_subplots
import pandas as pd
from datetime import datetime, timedelta
from typing import Dict, List, Optional
import logging


class SmartMonitorKline:
    """智能盯盘K线图"""
    
    def __init__(self):
        """初始化K线图"""
        self.logger = logging.getLogger(__name__)
    
    def create_kline_with_decisions(
        self,
        stock_code: str,
        stock_name: str,
        kline_data: pd.DataFrame,
        ai_decisions: List[Dict],
        show_volume: bool = True,
        show_ma: bool = True,
        height: int = 600
    ) -> go.Figure:
        """
        创建带AI决策标注的K线图
        
        Args:
            stock_code: 股票代码
            stock_name: 股票名称
            kline_data: K线数据（DataFrame）
            ai_decisions: AI决策列表
            show_volume: 是否显示成交量
            show_ma: 是否显示均线
            height: 图表高度
            
        Returns:
            plotly Figure对象
        """
        try:
            # 确保数据不为空
            if kline_data is None or kline_data.empty:
                self.logger.warning(f"K线数据为空 {stock_code}")
                return self._create_empty_figure(stock_code, stock_name, height)
            
            # 确保必需的列存在
            required_cols = ['日期', '开盘', '收盘', '最高', '最低']
            if not all(col in kline_data.columns for col in required_cols):
                self.logger.error(f"K线数据缺少必需列 {stock_code}")
                return self._create_empty_figure(stock_code, stock_name, height)
            
            # 创建子图
            if show_volume:
                fig = make_subplots(
                    rows=2, cols=1,
                    shared_xaxes=True,
                    vertical_spacing=0.03,
                    row_heights=[0.7, 0.3],
                    subplot_titles=(f'{stock_code} {stock_name}', '成交量')
                )
            else:
                fig = make_subplots(
                    rows=1, cols=1,
                    subplot_titles=(f'{stock_code} {stock_name}',)
                )
            
            # 1. 添加K线图
            fig.add_trace(
                go.Candlestick(
                    x=kline_data['日期'],
                    open=kline_data['开盘'],
                    high=kline_data['最高'],
                    low=kline_data['最低'],
                    close=kline_data['收盘'],
                    name='K线',
                    increasing_line_color='#ef5350',  # 红色（涨）
                    decreasing_line_color='#26a69a'   # 绿色（跌）
                ),
                row=1, col=1
            )
            
            # 2. 添加均线（如果需要）
            if show_ma:
                self._add_moving_averages(fig, kline_data, row=1, col=1)
            
            # 3. 添加AI决策标注
            if ai_decisions:
                self._add_ai_decision_markers(fig, kline_data, ai_decisions, row=1, col=1)
            
            # 4. 添加成交量（如果需要）
            if show_volume and '成交量' in kline_data.columns:
                self._add_volume(fig, kline_data, row=2, col=1)
            
            # 5. 更新布局
            fig.update_layout(
                height=height,
                xaxis_rangeslider_visible=False,
                showlegend=True,
                hovermode='x unified',
                template='plotly_white',
                margin=dict(l=50, r=50, t=50, b=50),
            )
            
            # 更新x轴
            fig.update_xaxes(
                title_text="日期",
                row=2 if show_volume else 1,
                col=1
            )
            
            # 更新y轴
            fig.update_yaxes(title_text="价格(元)", row=1, col=1)
            if show_volume:
                fig.update_yaxes(title_text="成交量", row=2, col=1)
            
            return fig
            
        except Exception as e:
            self.logger.error(f"创建K线图失败 {stock_code}: {e}")
            import traceback
            self.logger.debug(traceback.format_exc())
            return self._create_empty_figure(stock_code, stock_name, height)
    
    def _add_moving_averages(self, fig, kline_data: pd.DataFrame, row: int, col: int):
        """添加均线"""
        try:
            # 计算均线
            ma_periods = [5, 10, 20, 60]
            ma_colors = ['#FF6B6B', '#4ECDC4', '#45B7D1', '#FFA07A']
            
            for period, color in zip(ma_periods, ma_colors):
                if len(kline_data) >= period:
                    ma = kline_data['收盘'].rolling(window=period).mean()
                    fig.add_trace(
                        go.Scatter(
                            x=kline_data['日期'],
                            y=ma,
                            name=f'MA{period}',
                            line=dict(color=color, width=1),
                            opacity=0.7
                        ),
                        row=row, col=col
                    )
        except Exception as e:
            self.logger.warning(f"添加均线失败: {e}")
    
    def _add_ai_decision_markers(
        self,
        fig,
        kline_data: pd.DataFrame,
        ai_decisions: List[Dict],
        row: int,
        col: int
    ):
        """在K线图上添加AI决策标注"""
        try:
            # 决策类型映射
            action_config = {
                'buy': {
                    'symbol': 'triangle-up',
                    'color': '#ef5350',
                    'text': '买入',
                    'size': 15
                },
                'sell': {
                    'symbol': 'triangle-down',
                    'color': '#26a69a',
                    'text': '卖出',
                    'size': 15
                },
                'add_position': {
                    'symbol': 'triangle-up',
                    'color': '#ff9800',
                    'text': '加仓',
                    'size': 12
                },
                'reduce_position': {
                    'symbol': 'triangle-down',
                    'color': '#9c27b0',
                    'text': '减仓',
                    'size': 12
                },
                'hold': {
                    'symbol': 'circle',
                    'color': '#607d8b',
                    'text': '持有',
                    'size': 8
                }
            }
            
            # 将K线数据日期转换为字符串，便于匹配
            kline_data['日期_str'] = pd.to_datetime(kline_data['日期']).dt.strftime('%Y-%m-%d')
            
            # 按决策类型分组
            for action_type, config in action_config.items():
                decisions_of_type = [d for d in ai_decisions if d.get('action') == action_type]
                
                if not decisions_of_type:
                    continue
                
                # 提取决策的日期和价格
                decision_dates = []
                decision_prices = []
                decision_texts = []
                
                for decision in decisions_of_type:
                    decision_date = decision.get('decision_time', '').split()[0]  # 只取日期部分
                    
                    # 在K线数据中查找对应日期的收盘价
                    matching_rows = kline_data[kline_data['日期_str'] == decision_date]
                    
                    if not matching_rows.empty:
                        price = matching_rows.iloc[0]['收盘']
                        decision_dates.append(decision_date)
                        decision_prices.append(price)
                        
                        # 构建hover文本
                        confidence = decision.get('confidence', 0)
                        reasoning = decision.get('reasoning', '无')[:50]  # 截断过长的推理
                        hover_text = (
                            f"<b>{config['text']}</b><br>"
                            f"日期: {decision_date}<br>"
                            f"价格: ¥{price:.2f}<br>"
                            f"置信度: {confidence}%<br>"
                            f"推理: {reasoning}..."
                        )
                        decision_texts.append(hover_text)
                
                # 添加标注
                if decision_dates:
                    fig.add_trace(
                        go.Scatter(
                            x=decision_dates,
                            y=decision_prices,
                            mode='markers+text',
                            name=config['text'],
                            marker=dict(
                                symbol=config['symbol'],
                                size=config['size'],
                                color=config['color'],
                                line=dict(color='white', width=1)
                            ),
                            text=[config['text']] * len(decision_dates),
                            textposition='top center',
                            textfont=dict(size=10, color=config['color']),
                            hovertext=decision_texts,
                            hoverinfo='text',
                            showlegend=True
                        ),
                        row=row, col=col
                    )
            
        except Exception as e:
            self.logger.error(f"添加AI决策标注失败: {e}")
            import traceback
            self.logger.debug(traceback.format_exc())
    
    def _add_volume(self, fig, kline_data: pd.DataFrame, row: int, col: int):
        """添加成交量柱状图"""
        try:
            # 计算颜色（红涨绿跌）
            colors = []
            for i in range(len(kline_data)):
                if i == 0:
                    colors.append('#ef5350')
                else:
                    if kline_data.iloc[i]['收盘'] >= kline_data.iloc[i-1]['收盘']:
                        colors.append('#ef5350')  # 红色（涨）
                    else:
                        colors.append('#26a69a')  # 绿色（跌）
            
            fig.add_trace(
                go.Bar(
                    x=kline_data['日期'],
                    y=kline_data['成交量'],
                    name='成交量',
                    marker_color=colors,
                    showlegend=False
                ),
                row=row, col=col
            )
        except Exception as e:
            self.logger.warning(f"添加成交量失败: {e}")
    
    def _create_empty_figure(self, stock_code: str, stock_name: str, height: int) -> go.Figure:
        """创建空图表"""
        fig = go.Figure()
        fig.add_annotation(
            text=f"暂无 {stock_code} {stock_name} 的K线数据",
            xref="paper",
            yref="paper",
            x=0.5,
            y=0.5,
            showarrow=False,
            font=dict(size=20, color="gray")
        )
        fig.update_layout(
            height=height,
            xaxis=dict(visible=False),
            yaxis=dict(visible=False),
            template='plotly_white'
        )
        return fig
    
    def get_kline_data(self, stock_code: str, days: int = 60, data_fetcher=None) -> Optional[pd.DataFrame]:
        """
        获取K线数据（支持TDX/AKShare/Tushare降级机制）
        
        Args:
            stock_code: 股票代码
            days: 获取天数
            data_fetcher: 数据获取器实例
            
        Returns:
            K线数据DataFrame
        """
        try:
            if data_fetcher is None:
                from smart_monitor_data import SmartMonitorDataFetcher
                data_fetcher = SmartMonitorDataFetcher()
            
            # 方法1: 尝试使用TDX获取（如果启用）
            if hasattr(data_fetcher, 'use_tdx') and data_fetcher.use_tdx and data_fetcher.tdx_fetcher:
                try:
                    df = data_fetcher.tdx_fetcher.get_kline_data(stock_code, kline_type='day', limit=days)
                    if df is not None and not df.empty:
                        self.logger.info(f"✅ TDX获取K线数据成功 {stock_code}，共{len(df)}条")
                        return df
                    else:
                        self.logger.warning(f"TDX未返回K线数据 {stock_code}，尝试降级到AKShare")
                except Exception as e:
                    self.logger.warning(f"TDX获取K线数据失败 {stock_code}: {type(e).__name__}, 尝试降级到AKShare")
            
            # 计算日期范围
            end_date = datetime.now().strftime('%Y%m%d')
            start_date = (datetime.now() - timedelta(days=days + 30)).strftime('%Y%m%d')  # 多取30天以确保足够数据
            
            # 方法2: 尝试使用AKShare获取（只尝试1次，避免IP封禁）
            try:
                import akshare as ak
                df = ak.stock_zh_a_hist(
                    symbol=stock_code,
                    period='daily',
                    start_date=start_date,
                    end_date=end_date,
                    adjust='qfq'
                )
                
                if df is not None and not df.empty:
                    # 只保留最近days天的数据
                    df = df.tail(days)
                    self.logger.info(f"✅ AKShare获取K线数据成功 {stock_code}，共{len(df)}条")
                    return df
                else:
                    self.logger.warning(f"AKShare未返回K线数据 {stock_code}，尝试降级到Tushare")
            except Exception as e:
                self.logger.warning(f"AKShare获取K线数据失败 {stock_code}: {type(e).__name__}, 尝试降级到Tushare")
            
            # 方法3: 降级到Tushare
            if data_fetcher and data_fetcher.ts_pro:
                self.logger.info(f"降级使用Tushare获取K线数据 {stock_code}")
                df = self._get_kline_from_tushare(stock_code, days, data_fetcher.ts_pro)
                if df is not None and not df.empty:
                    self.logger.info(f"✅ Tushare获取K线数据成功 {stock_code}，共{len(df)}条")
                    return df
            
            self.logger.error(f"所有数据源都无法获取K线数据 {stock_code}")
            return None
            
        except Exception as e:
            self.logger.error(f"获取K线数据失败 {stock_code}: {e}")
            import traceback
            self.logger.debug(traceback.format_exc())
            return None
    
    def _get_kline_from_tushare(self, stock_code: str, days: int, ts_pro) -> Optional[pd.DataFrame]:
        """
        从Tushare获取K线数据
        
        Args:
            stock_code: 股票代码
            days: 获取天数
            ts_pro: Tushare API实例
            
        Returns:
            K线数据DataFrame
        """
        try:
            # 转换股票代码格式
            if stock_code.startswith('6'):
                ts_code = f"{stock_code}.SH"
            elif stock_code.startswith(('0', '3')):
                ts_code = f"{stock_code}.SZ"
            else:
                ts_code = stock_code
            
            # 计算日期范围（多取一些确保足够）
            end_date = datetime.now().strftime('%Y%m%d')
            start_date = (datetime.now() - timedelta(days=days + 60)).strftime('%Y%m%d')
            
            # 获取日K线数据（前复权）
            df = ts_pro.daily(
                ts_code=ts_code,
                start_date=start_date,
                end_date=end_date,
                adj='qfq'
            )
            
            if df is None or df.empty:
                self.logger.error(f"Tushare未返回K线数据 {stock_code}")
                return None
            
            # Tushare数据是从新到旧，需要反转
            df = df.sort_values('trade_date', ascending=True).reset_index(drop=True)
            
            # 统一列名为AKShare格式
            df = df.rename(columns={
                'trade_date': '日期',
                'open': '开盘',
                'high': '最高',
                'low': '最低',
                'close': '收盘',
                'vol': '成交量',
                'amount': '成交额'
            })
            
            # 转换日期格式（Tushare: 20240115 -> 2024-01-15）
            df['日期'] = pd.to_datetime(df['日期'])
            
            # 只保留最近days天的数据
            df = df.tail(days)
            
            return df
            
        except Exception as e:
            self.logger.error(f"Tushare获取K线数据失败 {stock_code}: {type(e).__name__}: {str(e)}")
            return None


if __name__ == '__main__':
    # 测试代码
    logging.basicConfig(level=logging.INFO)
    
    kline = SmartMonitorKline()
    
    # 测试获取K线数据
    df = kline.get_kline_data('600519', days=60)
    
    if df is not None:
        print(f"获取到 {len(df)} 条K线数据")
        print(df.head())
        
        # 模拟AI决策
        ai_decisions = [
            {
                'decision_time': '2024-01-15 10:00:00',
                'action': 'buy',
                'confidence': 85,
                'reasoning': '技术指标良好，MACD金叉'
            },
            {
                'decision_time': '2024-01-20 14:30:00',
                'action': 'add_position',
                'confidence': 75,
                'reasoning': '突破关键压力位'
            },
            {
                'decision_time': '2024-01-25 11:00:00',
                'action': 'sell',
                'confidence': 80,
                'reasoning': 'RSI超买，建议止盈'
            }
        ]
        
        # 创建K线图
        fig = kline.create_kline_with_decisions(
            stock_code='600519',
            stock_name='贵州茅台',
            kline_data=df,
            ai_decisions=ai_decisions,
            show_volume=True,
            show_ma=True
        )
        
        # 保存为HTML
        fig.write_html('test_kline.html')
        print("K线图已保存到 test_kline.html")
    else:
        print("获取K线数据失败")

