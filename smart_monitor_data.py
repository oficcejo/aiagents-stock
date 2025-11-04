"""
智能盯盘 - A股数据获取模块
使用TDX/akshare获取实时行情和技术指标
支持降级到tushare作为备用数据源
"""

import logging
import os
import akshare as ak
import pandas as pd
from typing import Dict, Optional
from datetime import datetime, timedelta


class SmartMonitorDataFetcher:
    """A股数据获取器（支持多数据源降级：TDX -> AKShare -> Tushare）"""
    
    def __init__(self, use_tdx: bool = None, tdx_base_url: str = None):
        """
        初始化数据获取器
        
        Args:
            use_tdx: 是否使用TDX数据源（可选，从配置读取）
            tdx_base_url: TDX接口地址（可选，从配置读取）
        """
        self.logger = logging.getLogger(__name__)
        
        # TDX数据源配置
        if use_tdx is None:
            from config import TDX_CONFIG
            use_tdx = TDX_CONFIG.get('enabled', False)
        
        if tdx_base_url is None:
            from config import TDX_CONFIG
            tdx_base_url = TDX_CONFIG.get('base_url', 'http://192.168.1.222:8181')
        
        self.use_tdx = use_tdx
        self.tdx_fetcher = None
        
        if self.use_tdx:
            try:
                from smart_monitor_tdx_data import SmartMonitorTDXDataFetcher
                self.tdx_fetcher = SmartMonitorTDXDataFetcher(base_url=tdx_base_url)
                self.logger.info(f"TDX数据源已启用: {tdx_base_url}")
            except Exception as e:
                self.logger.warning(f"TDX数据源初始化失败: {e}，将使用AKShare")
                self.use_tdx = False
        
        # 初始化Tushare（备用数据源）
        self.ts_pro = None
        tushare_token = os.getenv('TUSHARE_TOKEN', '')
        
        if tushare_token:
            try:
                import tushare as ts
                ts.set_token(tushare_token)
                self.ts_pro = ts.pro_api()
                self.logger.info("Tushare备用数据源初始化成功")
            except Exception as e:
                self.logger.warning(f"Tushare初始化失败: {e}")
        else:
            self.logger.info("未配置Tushare Token，仅使用AKShare数据源")
    
    def get_realtime_quote(self, stock_code: str, retry: int = 1) -> Optional[Dict]:
        """
        获取实时行情（带重试和降级机制）
        优先使用TDX，失败时降级到AKShare，最后降级到Tushare
        
        Args:
            stock_code: 股票代码（如：600519）
            retry: 重试次数（默认1次，避免IP封禁）
            
        Returns:
            实时行情数据
        """
        import time
        
        # 方法1: 尝试使用TDX（如果启用）
        if self.use_tdx and self.tdx_fetcher:
            try:
                quote = self.tdx_fetcher.get_realtime_quote(stock_code)
                if quote:
                    return quote
                else:
                    self.logger.warning(f"TDX获取失败 {stock_code}，尝试降级到AKShare")
            except Exception as e:
                self.logger.warning(f"TDX获取异常 {stock_code}: {e}，尝试降级到AKShare")
        
        # 方法2: 组合使用AKShare分钟行情 + 基本信息
        for attempt in range(retry):
            try:
                # 1.1 获取股票基本信息（名称）
                info_df = ak.stock_individual_info_em(symbol=stock_code)
                stock_name = 'N/A'
                if not info_df.empty:
                    info_dict = dict(zip(info_df['item'], info_df['value']))
                    stock_name = info_dict.get('股票简称', 'N/A')
                
                # 1.2 获取分钟级实时行情
                min_df = ak.stock_zh_a_hist_min_em(symbol=stock_code, period='1', adjust='')
                
                if min_df.empty:
                    self.logger.warning(f"AKShare未找到股票 {stock_code} 的分钟行情数据")
                    if attempt < retry - 1:
                        time.sleep(2)
                        continue
                    break
                
                # 1.3 获取历史数据（计算昨收）
                hist_df = ak.stock_zh_a_hist(symbol=stock_code, period='daily', adjust='')
                
                # 提取最新分钟数据
                latest = min_df.iloc[-1]
                current_price = float(latest['收盘'])
                
                # 计算昨收和涨跌幅
                if len(hist_df) >= 2:
                    pre_close = float(hist_df.iloc[-2]['收盘'])
                else:
                    pre_close = current_price
                
                change_amount = current_price - pre_close
                change_pct = (change_amount / pre_close * 100) if pre_close > 0 else 0
                
                # 从历史数据获取今天的统计数据
                if len(hist_df) >= 1:
                    today_data = hist_df.iloc[-1]
                    daily_volume = float(today_data.get('成交量', 0))
                    daily_amount = float(today_data.get('成交额', 0))
                    daily_high = float(today_data.get('最高', 0))
                    daily_low = float(today_data.get('最低', 0))
                    daily_open = float(today_data.get('开盘', 0))
                    turnover_rate = float(today_data.get('换手率', 0))
                else:
                    # 使用分钟数据
                    daily_volume = min_df['成交量'].sum()
                    daily_amount = min_df['成交额'].sum()
                    daily_high = min_df['最高'].max()
                    daily_low = min_df['最低'].min()
                    daily_open = float(min_df.iloc[0]['开盘'])
                    turnover_rate = 0.0
                
                self.logger.info(f"✅ AKShare成功获取 {stock_code} ({stock_name}) 实时行情")
                
                return {
                    'code': stock_code,
                    'name': stock_name,
                    'current_price': current_price,
                    'change_pct': change_pct,
                    'change_amount': change_amount,
                    'volume': daily_volume,  # 手
                    'amount': daily_amount,  # 元
                    'high': daily_high,
                    'low': daily_low,
                    'open': daily_open,
                    'pre_close': pre_close,
                    'turnover_rate': turnover_rate,
                    'volume_ratio': 1.0,
                    'update_time': str(latest['时间']),
                    'data_source': 'akshare'
                }
                
            except Exception as e:
                if attempt < retry - 1:
                    self.logger.warning(f"AKShare获取失败 {stock_code}，第{attempt+1}次重试... 错误: {type(e).__name__}: {str(e)[:50]}")
                    time.sleep(2)  # 等待2秒后重试
                else:
                    self.logger.warning(f"AKShare获取失败 {stock_code}（已重试{retry}次），尝试降级")
        
        # 降级到Tushare
        if self.ts_pro:
            self.logger.info(f"降级到Tushare获取 {stock_code}...")
            return self._get_realtime_quote_from_tushare(stock_code)
        else:
            self.logger.error(f"AKShare失败且未配置Tushare，无法获取 {stock_code} 行情")
            return None
    
    def get_technical_indicators(self, stock_code: str, period: str = 'daily', retry: int = 1) -> Optional[Dict]:
        """
        计算技术指标（带降级机制）
        优先使用TDX，失败时降级到AKShare，最后降级到Tushare
        
        Args:
            stock_code: 股票代码
            period: 周期（daily/weekly/monthly）
            retry: 重试次数（默认1次）
            
        Returns:
            技术指标数据
        """
        import time
        
        # 方法1: 尝试使用TDX（如果启用）
        if self.use_tdx and self.tdx_fetcher:
            try:
                indicators = self.tdx_fetcher.get_technical_indicators(stock_code, period)
                if indicators:
                    return indicators
                else:
                    self.logger.warning(f"TDX计算技术指标失败 {stock_code}，尝试降级到AKShare")
            except Exception as e:
                self.logger.warning(f"TDX计算技术指标异常 {stock_code}: {e}，尝试降级到AKShare")
        
        # 方法2: 尝试使用AKShare
        for attempt in range(retry):
            try:
                # 获取历史数据（最近200个交易日，用于计算指标）
                end_date = datetime.now().strftime('%Y%m%d')
                start_date = (datetime.now() - timedelta(days=300)).strftime('%Y%m%d')
                
                # 获取历史数据
                df = ak.stock_zh_a_hist(
                    symbol=stock_code,
                    period=period,
                    start_date=start_date,
                    end_date=end_date,
                    adjust="qfq"  # 前复权
                )
                
                if df.empty or len(df) < 60:
                    if attempt < retry - 1:
                        self.logger.warning(f"AKShare历史数据不足 {stock_code}，第{attempt+1}次重试...")
                        time.sleep(1)
                        continue
                    else:
                        self.logger.warning(f"AKShare历史数据不足 {stock_code}，尝试降级")
                        break
                
                # 数据充足，计算技术指标
                return self._calculate_all_indicators(df, stock_code)
                
            except Exception as e:
                if attempt < retry - 1:
                    self.logger.warning(f"AKShare获取历史数据失败 {stock_code}，第{attempt+1}次重试... 错误: {type(e).__name__}: {str(e)[:50]}")
                    time.sleep(1)
                else:
                    self.logger.warning(f"AKShare获取历史数据失败 {stock_code}（已重试{retry}次），尝试降级到Tushare")
                    break
        
        # 方法3: 降级到Tushare
        if self.ts_pro:
            self.logger.info(f"降级到Tushare获取 {stock_code} 历史数据...")
            return self._get_technical_indicators_from_tushare(stock_code, period)
        else:
            self.logger.error(f"AKShare失败且未配置Tushare，无法获取 {stock_code} 技术指标")
            return None
    
    def _calculate_all_indicators(self, df: pd.DataFrame, stock_code: str) -> Optional[Dict]:
        """
        根据历史数据计算所有技术指标
        
        Args:
            df: 历史数据DataFrame
            stock_code: 股票代码
            
        Returns:
            技术指标数据
        """
        try:
            if df.empty or len(df) < 60:
                self.logger.warning(f"股票 {stock_code} 历史数据不足")
                return None
            
            # 计算均线
            df['ma5'] = df['收盘'].rolling(window=5).mean()
            df['ma20'] = df['收盘'].rolling(window=20).mean()
            df['ma60'] = df['收盘'].rolling(window=60).mean()
            
            # 计算MACD
            df = self._calculate_macd(df)
            
            # 计算RSI
            df = self._calculate_rsi(df, periods=[6, 12, 24])
            
            # 计算KDJ
            df = self._calculate_kdj(df)
            
            # 计算布林带
            df = self._calculate_bollinger(df)
            
            # 计算量能均线
            df['vol_ma5'] = df['成交量'].rolling(window=5).mean()
            df['vol_ma10'] = df['成交量'].rolling(window=10).mean()
            
            # 取最后一行数据
            latest = df.iloc[-1]
            
            # 判断趋势
            current_price = float(latest['收盘'])
            ma5 = float(latest['ma5'])
            ma20 = float(latest['ma20'])
            ma60 = float(latest['ma60'])
            
            if current_price > ma5 > ma20 > ma60:
                trend = 'up'
            elif current_price < ma5 < ma20 < ma60:
                trend = 'down'
            else:
                trend = 'sideways'
            
            # 布林带位置
            boll_upper = float(latest['boll_upper'])
            boll_mid = float(latest['boll_mid'])
            boll_lower = float(latest['boll_lower'])
            
            if current_price >= boll_upper:
                boll_position = '上轨附近（超买）'
            elif current_price <= boll_lower:
                boll_position = '下轨附近（超卖）'
            elif current_price > boll_mid:
                boll_position = '中轨上方'
            else:
                boll_position = '中轨下方'
            
            return {
                'ma5': ma5,
                'ma20': ma20,
                'ma60': ma60,
                'trend': trend,
                'macd_dif': float(latest['dif']),
                'macd_dea': float(latest['dea']),
                'macd': float(latest['macd']),
                'rsi6': float(latest['rsi6']),
                'rsi12': float(latest['rsi12']),
                'rsi24': float(latest['rsi24']),
                'kdj_k': float(latest['kdj_k']),
                'kdj_d': float(latest['kdj_d']),
                'kdj_j': float(latest['kdj_j']),
                'boll_upper': boll_upper,
                'boll_mid': boll_mid,
                'boll_lower': boll_lower,
                'boll_position': boll_position,
                'vol_ma5': float(latest['vol_ma5']),
                'volume_ratio': float(latest['成交量']) / float(latest['vol_ma5']) if latest['vol_ma5'] > 0 else 1.0
            }
            
        except Exception as e:
            self.logger.error(f"计算技术指标失败 {stock_code}: {e}")
            return None
    
    def _get_technical_indicators_from_tushare(self, stock_code: str, period: str = 'daily') -> Optional[Dict]:
        """
        使用Tushare获取历史数据并计算技术指标
        
        Args:
            stock_code: 股票代码（6位）
            period: 周期（daily/weekly/monthly）
            
        Returns:
            技术指标数据
        """
        try:
            # 转换股票代码格式（Tushare格式：600519.SH, 000001.SZ）
            if stock_code.startswith('6'):
                ts_code = f"{stock_code}.SH"
            elif stock_code.startswith(('0', '3')):
                ts_code = f"{stock_code}.SZ"
            else:
                ts_code = stock_code
            
            # 计算日期范围
            end_date = datetime.now().strftime('%Y%m%d')
            start_date = (datetime.now() - timedelta(days=400)).strftime('%Y%m%d')
            
            # 获取历史数据
            df = self.ts_pro.daily(
                ts_code=ts_code,
                start_date=start_date,
                end_date=end_date
            )
            
            if df is None or df.empty:
                self.logger.error(f"Tushare未返回 {stock_code} 的历史数据")
                return None
            
            # Tushare数据是从新到旧，需要反转
            df = df.sort_values('trade_date', ascending=True).reset_index(drop=True)
            
            if len(df) < 60:
                self.logger.warning(f"Tushare历史数据不足 {stock_code}（仅{len(df)}条）")
                return None
            
            # 统一列名为AKShare格式（完整映射）
            df = df.rename(columns={
                'open': '开盘',
                'high': '最高',
                'low': '最低',
                'close': '收盘',
                'vol': '成交量',
                'amount': '成交额',
                'trade_date': '日期'
            })
            
            # 如果没有关键列，尝试使用其他可能的列名
            column_mapping = {
                '开盘': ['open', 'Open', 'OPEN'],
                '最高': ['high', 'High', 'HIGH'],
                '最低': ['low', 'Low', 'LOW'],
                '收盘': ['close', 'Close', 'CLOSE'],
                '成交量': ['vol', 'volume', 'Volume', 'VOLUME'],
                '成交额': ['amount', 'Amount', 'AMOUNT']
            }
            
            for target_col, possible_cols in column_mapping.items():
                if target_col not in df.columns:
                    for col in possible_cols:
                        if col in df.columns:
                            df[target_col] = df[col]
                            break
            
            # 确认必需的列存在
            required_cols = ['开盘', '最高', '最低', '收盘', '成交量']
            missing_cols = [col for col in required_cols if col not in df.columns]
            if missing_cols:
                self.logger.error(f"Tushare数据缺少列 {stock_code}: {missing_cols}")
                return None
            
            self.logger.info(f"✅ Tushare成功获取 {stock_code} 历史数据，共{len(df)}条")
            
            # 使用统一的计算方法
            return self._calculate_all_indicators(df, stock_code)
            
        except Exception as e:
            self.logger.error(f"Tushare获取历史数据失败 {stock_code}: {type(e).__name__}: {str(e)}")
            import traceback
            self.logger.debug(traceback.format_exc())
            return None
    
    def get_main_force_flow(self, stock_code: str, retry: int = 2) -> Optional[Dict]:
        """
        获取主力资金流向（带重试机制）
        
        Args:
            stock_code: 股票代码
            retry: 重试次数（默认2次）
            
        Returns:
            主力资金数据
        """
        import time
        
        for attempt in range(retry):
            try:
                # 获取个股资金流（新版AKShare API参数调整）
                try:
                    df = ak.stock_individual_fund_flow_rank(market="今日")
                except TypeError:
                    # 如果market参数也不支持，尝试无参数调用
                    try:
                        df = ak.stock_individual_fund_flow_rank()
                    except TypeError as te:
                        self.logger.warning(f"AKShare API参数不兼容: {te}")
                        return None
                
                stock_data = df[df['代码'] == stock_code]
                
                if stock_data.empty:
                    self.logger.warning(f"未找到股票 {stock_code} 的资金流向数据")
                    return None
                
                row = stock_data.iloc[0]
                
                # 主力净额
                main_net = float(row.get('主力净流入-净额', 0)) / 10000  # 转换为万元
                main_net_pct = float(row.get('主力净流入-净占比', 0))
                
                # 判断主力动向
                if main_net > 0 and main_net_pct > 5:
                    trend = '大幅流入'
                elif main_net > 0:
                    trend = '小幅流入'
                elif main_net < 0 and main_net_pct < -5:
                    trend = '大幅流出'
                elif main_net < 0:
                    trend = '小幅流出'
                else:
                    trend = '观望'
                
                return {
                    'main_net': main_net,  # 万元
                    'main_net_pct': main_net_pct,  # 百分比
                    'super_net': float(row.get('超大单净流入-净额', 0)) / 10000,
                    'big_net': float(row.get('大单净流入-净额', 0)) / 10000,
                    'mid_net': float(row.get('中单净流入-净额', 0)) / 10000,
                    'small_net': float(row.get('小单净流入-净额', 0)) / 10000,
                    'trend': trend,
                    'data_source': 'akshare'
                }
                
            except Exception as e:
                if attempt < retry - 1:
                    self.logger.warning(f"AKShare获取资金流向失败 {stock_code}，第{attempt+1}次重试... 错误: {type(e).__name__}")
                    time.sleep(1)  # 等待1秒后重试
                else:
                    self.logger.warning(f"AKShare获取资金流向失败 {stock_code}（已重试{retry}次），尝试降级到Tushare")
                    break
        
        # 降级到Tushare
        if self.ts_pro:
            return self._get_main_force_from_tushare(stock_code)
        else:
            self.logger.error(f"AKShare失败且未配置Tushare，无法获取 {stock_code} 资金流向")
            return None
    
    def get_comprehensive_data(self, stock_code: str) -> Dict:
        """
        获取综合数据（实时行情+技术指标）
        注意：已移除主力资金流向数据，因为该接口不稳定且AI决策不依赖此数据
        
        Args:
            stock_code: 股票代码
            
        Returns:
            综合数据
        """
        result = {}
        
        # 实时行情
        quote = self.get_realtime_quote(stock_code)
        if quote:
            result.update(quote)
        
        # 技术指标
        indicators = self.get_technical_indicators(stock_code)
        if indicators:
            result.update(indicators)
        
        # 主力资金（已禁用 - 接口不稳定）
        # main_force = self.get_main_force_flow(stock_code)
        # if main_force:
        #     result['main_force'] = main_force
        
        return result
    
    # ========== 技术指标计算方法 ==========
    
    def _calculate_macd(self, df: pd.DataFrame, 
                       fast: int = 12, slow: int = 26, signal: int = 9) -> pd.DataFrame:
        """计算MACD指标"""
        ema_fast = df['收盘'].ewm(span=fast, adjust=False).mean()
        ema_slow = df['收盘'].ewm(span=slow, adjust=False).mean()
        
        df['dif'] = ema_fast - ema_slow
        df['dea'] = df['dif'].ewm(span=signal, adjust=False).mean()
        df['macd'] = (df['dif'] - df['dea']) * 2
        
        return df
    
    def _calculate_rsi(self, df: pd.DataFrame, periods: list = [6, 12, 24]) -> pd.DataFrame:
        """计算RSI指标"""
        for period in periods:
            delta = df['收盘'].diff()
            gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
            loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()
            
            rs = gain / loss
            df[f'rsi{period}'] = 100 - (100 / (1 + rs))
        
        return df
    
    def _calculate_kdj(self, df: pd.DataFrame, n: int = 9, 
                      m1: int = 3, m2: int = 3) -> pd.DataFrame:
        """计算KDJ指标"""
        low_list = df['最低'].rolling(window=n).min()
        high_list = df['最高'].rolling(window=n).max()
        
        rsv = (df['收盘'] - low_list) / (high_list - low_list) * 100
        
        df['kdj_k'] = rsv.ewm(com=m1-1, adjust=False).mean()
        df['kdj_d'] = df['kdj_k'].ewm(com=m2-1, adjust=False).mean()
        df['kdj_j'] = 3 * df['kdj_k'] - 2 * df['kdj_d']
        
        return df
    
    def _calculate_bollinger(self, df: pd.DataFrame, 
                           period: int = 20, std_num: int = 2) -> pd.DataFrame:
        """计算布林带"""
        df['boll_mid'] = df['收盘'].rolling(window=period).mean()
        std = df['收盘'].rolling(window=period).std()
        
        df['boll_upper'] = df['boll_mid'] + std_num * std
        df['boll_lower'] = df['boll_mid'] - std_num * std
        
        return df


    # ========== Tushare备用数据源方法 ==========
    
    def _get_realtime_quote_from_tushare(self, stock_code: str) -> Optional[Dict]:
        """
        从Tushare获取实时行情（备用数据源）
        使用免费接口，无需积分
        
        Args:
            stock_code: 股票代码
            
        Returns:
            实时行情数据
        """
        try:
            # 转换股票代码格式（Tushare格式：600519.SH）
            if stock_code.startswith('6'):
                ts_code = f"{stock_code}.SH"
            elif stock_code.startswith(('0', '3')):
                ts_code = f"{stock_code}.SZ"
            else:
                self.logger.warning(f"无法识别股票代码市场: {stock_code}")
                return None
            
            # 方法1: 尝试使用daily_basic（基础日线，无需积分）
            try:
                df = self.ts_pro.daily_basic(ts_code=ts_code, 
                                             trade_date=datetime.now().strftime('%Y%m%d'),
                                             fields='ts_code,trade_date,close,turnover_rate,volume_ratio,pe,pb')
                
                if df.empty:
                    # 获取最近交易日
                    end_date = datetime.now().strftime('%Y%m%d')
                    df = self.ts_pro.daily_basic(ts_code=ts_code, 
                                                 end_date=end_date,
                                                 fields='ts_code,trade_date,close,turnover_rate,volume_ratio,pe,pb')
                    df = df.head(1)
                
                if not df.empty:
                    row = df.iloc[0]
                    
                    # 获取日线数据补充价格信息
                    df_daily = self.ts_pro.daily(ts_code=ts_code, 
                                                 trade_date=row['trade_date'],
                                                 fields='open,high,low,pre_close,change,pct_chg,vol,amount')
                    
                    if not df_daily.empty:
                        daily_row = df_daily.iloc[0]
                        
                        # 获取股票名称
                        stock_basic = self.ts_pro.stock_basic(ts_code=ts_code, fields='name')
                        stock_name = stock_basic.iloc[0]['name'] if not stock_basic.empty else 'N/A'
                        
                        self.logger.info(f"✅ Tushare降级成功（基础接口），获取到 {stock_code} 数据")
                        
                        return {
                            'code': stock_code,
                            'name': stock_name,
                            'current_price': float(row['close']),
                            'change_pct': float(daily_row.get('pct_chg', 0)),
                            'change_amount': float(daily_row.get('change', 0)),
                            'volume': float(daily_row.get('vol', 0)) * 100,
                            'amount': float(daily_row.get('amount', 0)) * 1000,
                            'high': float(daily_row.get('high', 0)),
                            'low': float(daily_row.get('low', 0)),
                            'open': float(daily_row.get('open', 0)),
                            'pre_close': float(daily_row.get('pre_close', 0)),
                            'turnover_rate': float(row.get('turnover_rate', 0)),
                            'volume_ratio': float(row.get('volume_ratio', 1.0)),
                            'update_time': row['trade_date'],
                            'data_source': 'tushare'
                        }
            except Exception as e:
                self.logger.warning(f"Tushare基础接口失败: {str(e)[:100]}")
            
            # 方法2: 降级使用更基础的stock_basic+pro_bar
            try:
                # 获取股票名称
                stock_basic = self.ts_pro.stock_basic(ts_code=ts_code, fields='name')
                stock_name = stock_basic.iloc[0]['name'] if not stock_basic.empty else 'N/A'
                
                # 使用pro_bar获取行情（社区版免费）
                import tushare as ts
                df = ts.pro_bar(ts_code=ts_code, adj='qfq', ma=[5, 20])
                
                if df is not None and not df.empty:
                    row = df.iloc[0]
                    
                    self.logger.info(f"✅ Tushare降级成功（pro_bar接口），获取到 {stock_code} 数据")
                    
                    return {
                        'code': stock_code,
                        'name': stock_name,
                        'current_price': float(row['close']),
                        'change_pct': float(row.get('pct_chg', 0)),
                        'change_amount': float(row.get('change', 0)),
                        'volume': float(row.get('vol', 0)) * 100,
                        'amount': float(row.get('amount', 0)) * 1000,
                        'high': float(row.get('high', 0)),
                        'low': float(row.get('low', 0)),
                        'open': float(row.get('open', 0)),
                        'pre_close': float(row.get('pre_close', 0)),
                        'turnover_rate': float(row.get('turnover_rate', 0)),
                        'volume_ratio': 1.0,
                        'update_time': row['trade_date'],
                        'data_source': 'tushare'
                    }
            except Exception as e:
                self.logger.warning(f"Tushare pro_bar接口失败: {str(e)[:100]}")
            
            # 所有方法都失败
            self.logger.error(f"Tushare所有接口都失败 {stock_code}，可能是积分不足或网络问题")
            self.logger.info("💡 提示：访问 https://tushare.pro/user/token 查看积分和权限")
            return None
            
        except Exception as e:
            error_msg = str(e)
            if "权限" in error_msg or "积分" in error_msg:
                self.logger.error(f"Tushare权限不足 {stock_code}: 需要更多积分")
                self.logger.info("💡 获取积分方法：")
                self.logger.info("   1. 完善个人信息 +100积分")
                self.logger.info("   2. 每日签到 +1积分")
                self.logger.info("   3. 参与社区互动")
                self.logger.info("   详情访问: https://tushare.pro/document/1?doc_id=13")
            else:
                self.logger.error(f"Tushare获取失败 {stock_code}: {error_msg[:100]}")
            return None
    
    def _get_main_force_from_tushare(self, stock_code: str) -> Optional[Dict]:
        """
        从Tushare获取主力资金流向（备用数据源）
        注意：资金流向接口需要较高积分
        
        Args:
            stock_code: 股票代码
            
        Returns:
            主力资金数据
        """
        try:
            # 转换股票代码格式
            if stock_code.startswith('6'):
                ts_code = f"{stock_code}.SH"
            elif stock_code.startswith(('0', '3')):
                ts_code = f"{stock_code}.SZ"
            else:
                return None
            
            # 尝试获取资金流向数据（需要120积分）
            today = datetime.now().strftime('%Y%m%d')
            df = self.ts_pro.moneyflow(ts_code=ts_code, start_date=today, end_date=today)
            
            if df.empty:
                # 获取最近一个交易日
                df = self.ts_pro.moneyflow(ts_code=ts_code, end_date=today)
                df = df.head(1)
            
            if df.empty:
                self.logger.warning(f"Tushare未找到股票 {stock_code} 的资金流向数据")
                return None
            
            row = df.iloc[0]
            
            # 计算主力净额（大单+超大单）
            buy_lg_amount = float(row.get('buy_lg_amount', 0))
            buy_elg_amount = float(row.get('buy_elg_amount', 0))
            sell_lg_amount = float(row.get('sell_lg_amount', 0))
            sell_elg_amount = float(row.get('sell_elg_amount', 0))
            
            main_net = (buy_lg_amount + buy_elg_amount - sell_lg_amount - sell_elg_amount) / 10000
            
            # 计算净占比
            net_mf_amount = float(row.get('net_mf_amount', 0))
            main_net_pct = (main_net / net_mf_amount * 100) if net_mf_amount != 0 else 0
            
            # 判断主力动向
            if main_net > 0 and main_net_pct > 5:
                trend = '大幅流入'
            elif main_net > 0:
                trend = '小幅流入'
            elif main_net < 0 and main_net_pct < -5:
                trend = '大幅流出'
            elif main_net < 0:
                trend = '小幅流出'
            else:
                trend = '观望'
            
            self.logger.info(f"✅ Tushare降级成功，获取到 {stock_code} 资金流向")
            
            return {
                'main_net': main_net,
                'main_net_pct': main_net_pct,
                'super_net': (buy_elg_amount - sell_elg_amount) / 10000,
                'big_net': (buy_lg_amount - sell_lg_amount) / 10000,
                'mid_net': float(row.get('buy_md_amount', 0) - row.get('sell_md_amount', 0)) / 10000,
                'small_net': float(row.get('buy_sm_amount', 0) - row.get('sell_sm_amount', 0)) / 10000,
                'trend': trend
            }
            
        except Exception as e:
            error_msg = str(e)
            if "权限" in error_msg or "积分" in error_msg:
                self.logger.warning(f"⚠️ Tushare资金流向接口需要120积分，当前积分不足")
                self.logger.info("💡 获取积分方法：")
                self.logger.info("   1. 完善个人信息 +100积分")
                self.logger.info("   2. 每日签到累积 +30积分（30天）")
                self.logger.info("   3. 参与社区互动获得积分")
                self.logger.info("   详情: https://tushare.pro/document/1?doc_id=13")
                self.logger.info("   智能盯盘会继续运行，仅缺少资金流向数据")
            else:
                self.logger.error(f"Tushare获取资金流向失败 {stock_code}: {error_msg[:100]}")
            return None


if __name__ == '__main__':
    # 测试代码
    logging.basicConfig(level=logging.INFO)
    
    fetcher = SmartMonitorDataFetcher()
    
    # 测试贵州茅台
    print("测试获取贵州茅台(600519)数据...")
    data = fetcher.get_comprehensive_data('600519')
    
    if data:
        print("\n实时行情:")
        print(f"  当前价: {data.get('current_price')} 元")
        print(f"  涨跌幅: {data.get('change_pct')}%")
        
        print("\n技术指标:")
        print(f"  MA5: {data.get('ma5', 0):.2f}")
        print(f"  MA20: {data.get('ma20', 0):.2f}")
        print(f"  MACD: {data.get('macd', 0):.4f}")
        print(f"  RSI(6): {data.get('rsi6', 0):.2f}")
        
        if 'main_force' in data:
            print("\n主力资金:")
            print(f"  主力净额: {data['main_force']['main_net']:.2f}万")
            print(f"  主力动向: {data['main_force']['trend']}")

