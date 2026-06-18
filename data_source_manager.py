"""
数据源管理器
实现akshare和tushare的自动切换机制
"""

import os
import time
import pandas as pd
from datetime import datetime, timedelta
from dotenv import load_dotenv

# 加载环境变量
load_dotenv()

# ============================================================
# 关键修复: 在引入 akshare 之前打上请求补丁
# 为所有 requests 请求注入 User-Agent 等请求头，
# 解决东方财富服务器 RemoteDisconnected 问题
# ============================================================
from utils.akshare_helper import patch_requests, retry_on_failure
patch_requests()


class DataSourceManager:
    """数据源管理器 - 实现akshare与tushare自动切换"""
    
    def __init__(self):
        self.tushare_token = os.getenv('TUSHARE_TOKEN', '')
        self.tushare_available = False
        self.tushare_api = None
        
        # 初始化tushare
        if self.tushare_token:
            try:
                import tushare as ts
                ts.set_token(self.tushare_token)
                self.tushare_api = ts.pro_api()
                self.tushare_available = True
                print("✅ Tushare数据源初始化成功")
            except Exception as e:
                print(f"⚠️ Tushare数据源初始化失败: {e}")
                self.tushare_available = False
        else:
            print("ℹ️ 未配置Tushare Token，将仅使用Akshare数据源")
    
    def get_stock_hist_data(self, symbol, start_date=None, end_date=None, adjust='qfq'):
        """
        获取股票历史数据（优先akshare，失败时使用tushare）
        
        Args:
            symbol: 股票代码（6位数字）
            start_date: 开始日期（格式：'20240101'或'2024-01-01'）
            end_date: 结束日期
            adjust: 复权类型（'qfq'前复权, 'hfq'后复权, ''不复权）
            
        Returns:
            DataFrame: 包含日期、开盘、收盘、最高、最低、成交量等列
        """
        # 标准化日期格式
        if start_date:
            start_date = start_date.replace('-', '')
        if end_date:
            end_date = end_date.replace('-', '')
        else:
            end_date = datetime.now().strftime('%Y%m%d')
        
        # 优先使用akshare（带重试机制）
        for retry_count in range(3):
            try:
                import akshare as ak
                print(f"[Akshare-腾讯] 正在获取 {symbol} 的历史数据..." +
                      (f" (第{retry_count+1}次)" if retry_count > 0 else ""))
                
                # 使用腾讯数据源（proxy.finance.qq.com），避免东方财富API屏蔽
                tx_symbol = self._convert_to_tx_code(symbol)
                df = ak.stock_zh_a_hist_tx(
                    symbol=tx_symbol,
                    start_date=f"{start_date[:4]}-{start_date[4:6]}-{start_date[6:]}",
                    end_date=f"{end_date[:4]}-{end_date[4:6]}-{end_date[6:]}",
                    adjust=adjust
                )
                
                if df is not None and not df.empty:
                    # Tencent 返回列名: ['date', 'open', 'close', 'high', 'low', 'amount']
                    # 补充标准列名
                    column_map = {
                        'date': 'date',
                        'open': 'open',
                        'close': 'close',
                        'high': 'high',
                        'low': 'low',
                        'amount': 'amount',
                    }
                    df = df.rename(columns=column_map)
                    df['date'] = pd.to_datetime(df['date'])
                    # 腾讯 amount 单位是万元，转为元
                    if 'amount' in df.columns:
                        df['amount'] = df['amount'] * 10000
                    # 估算成交量（成交额/均价），作为备选
                    if 'volume' not in df.columns:
                        avg_price = (df['open'] + df['close'] + df['high'] + df['low']) / 4
                        df['volume'] = (df['amount'] / avg_price.replace(0, float('nan'))).fillna(0).astype('int64')
                    print(f"[Akshare-腾讯] ✅ 成功获取 {len(df)} 条数据")
                    return df
                else:
                    print(f"[Akshare-腾讯] ⚠️ 获取到空数据，重试中...")
                    time.sleep(1)
                    continue
            except Exception as e:
                print(f"[Akshare-腾讯] ❌ 获取失败: {e}")
                if retry_count < 2:
                    delay = (retry_count + 1) * 2
                    print(f"[Akshare-腾讯] ⏳ {delay}s 后重试...")
                    time.sleep(delay)
                else:
                    print(f"[Akshare-腾讯] ❌ 已重试 3 次，放弃")
        
        # akshare失败，尝试tushare
        if self.tushare_available:
            try:
                print(f"[Tushare] 正在获取 {symbol} 的历史数据（备用数据源）...")
                
                # 转换股票代码格式（添加市场后缀）
                ts_code = self._convert_to_ts_code(symbol)
                
                # 转换复权类型
                adj_dict = {'qfq': 'qfq', 'hfq': 'hfq', '': None}
                adj = adj_dict.get(adjust, 'qfq')
                
                # 格式化日期
                start = f"{start_date[:4]}-{start_date[4:6]}-{start_date[6:]}" if start_date else None
                end = f"{end_date[:4]}-{end_date[4:6]}-{end_date[6:]}" if end_date else None
                
                # 获取数据
                df = self.tushare_api.daily(
                    ts_code=ts_code,
                    start_date=start_date,
                    end_date=end_date,
                    adj=adj
                )
                
                if df is not None and not df.empty:
                    # 标准化列名和数据格式
                    df = df.rename(columns={
                        'trade_date': 'date',
                        'vol': 'volume',
                        'amount': 'amount'
                    })
                    df['date'] = pd.to_datetime(df['date'])
                    df = df.sort_values('date')
                    
                    # 转换成交量单位（tushare单位是手，转换为股）
                    df['volume'] = df['volume'] * 100
                    # 转换成交额单位（tushare单位是千元，转换为元）
                    df['amount'] = df['amount'] * 1000
                    
                    print(f"[Tushare] ✅ 成功获取 {len(df)} 条数据")
                    return df
            except Exception as e:
                print(f"[Tushare] ❌ 获取失败: {e}")
        
        # 两个数据源都失败
        print("❌ 所有数据源均获取失败")
        return None
    
    def get_stock_basic_info(self, symbol):
        """
        获取股票基本信息（优先akshare，失败时使用tushare）
        
        Args:
            symbol: 股票代码
            
        Returns:
            dict: 股票基本信息
        """
        info = {
            "symbol": symbol,
            "name": "未知",
            "industry": "未知",
            "market": "未知"
        }
        
        # 优先使用akshare（仅尝试1次，失败快速降级到新浪）
        for retry_count in range(1):
            try:
                import akshare as ak
                print(f"[Akshare] 正在获取 {symbol} 的基本信息...")
                
                stock_info = ak.stock_individual_info_em(symbol=symbol)
                if stock_info is not None and not stock_info.empty:
                    for _, row in stock_info.iterrows():
                        key = row['item']
                        value = row['value']
                        
                        if key == '股票简称':
                            info['name'] = value
                        elif key == '所处行业':
                            info['industry'] = value
                        elif key == '上市时间':
                            info['list_date'] = value
                        elif key == '总市值':
                            info['market_cap'] = value
                        elif key == '流通市值':
                            info['circulating_market_cap'] = value
                    
                    print(f"[Akshare] ✅ 成功获取基本信息")
                    return info
            except Exception as e:
                print(f"[Akshare] ❌ 获取失败: {e}")
        
        # akshare（东方财富）失败，尝试新浪单只股票接口获取名称
        try:
            import requests as req
            tx_code = self._convert_to_tx_code(symbol)
            url = f'https://hq.sinajs.cn/list={tx_code}'
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
                'Referer': 'https://finance.sina.com.cn/',
            }
            r = req.get(url, headers=headers, timeout=10)
            # 返回格式: var hq_str_sh603212="名称,open,pre_close,current,...";
            if r.status_code == 200 and f'hq_str_{tx_code}' in r.text:
                # 提取引号内的数据
                start = r.text.find('"') + 1
                end = r.text.find('"', start)
                if start > 0 and end > start:
                    fields = r.text[start:end].split(',')
                    if len(fields) >= 1 and fields[0]:
                        info['name'] = fields[0]
                        info['market'] = '中国A股'
                        print(f"[新浪个股] ✅ 成功获取基本信息: {info['name']}")
                        return info
        except Exception as e:
            print(f"[新浪个股] ❌ 获取失败: {e}")
        
        # akshare失败，尝试tushare（备用数据源）
        if self.tushare_available:
            try:
                print(f"[Tushare] 正在获取 {symbol} 的基本信息（备用数据源）...")
                
                ts_code = self._convert_to_ts_code(symbol)
                df = self.tushare_api.stock_basic(
                    ts_code=ts_code,
                    fields='ts_code,name,area,industry,market,list_date'
                )
                
                if df is not None and not df.empty:
                    info['name'] = df.iloc[0]['name']
                    info['industry'] = df.iloc[0]['industry']
                    info['market'] = df.iloc[0]['market']
                    info['list_date'] = df.iloc[0]['list_date']
                    
                    print(f"[Tushare] ✅ 成功获取基本信息")
                    return info
            except Exception as e:
                print(f"[Tushare] ❌ 获取失败: {e}")
        
        return info
    
    def get_realtime_quotes(self, symbol):
        """
        获取实时行情数据（优先akshare，失败时使用tushare）
        
        Args:
            symbol: 股票代码
            
        Returns:
            dict: 实时行情数据
        """
        quotes = {}
        
        # 优先使用新浪个股接口（比全市场遍历快得多）
        for retry_count in range(3):
            try:
                import requests as req_sina
                tx_code = self._convert_to_tx_code(symbol)
                url = f'https://hq.sinajs.cn/list={tx_code}'
                headers = {
                    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
                    'Referer': 'https://finance.sina.com.cn/',
                }
                r = req_sina.get(url, headers=headers, timeout=10)
                
                if r.status_code == 200 and f'hq_str_{tx_code}' in r.text:
                    start = r.text.find('"') + 1
                    end = r.text.find('"', start)
                    if start > 0 and end > start:
                        fields = r.text[start:end].split(',')
                        if len(fields) >= 32:
                            def safe_float(val, default=0):
                                try: return float(val) if val else default
                                except: return default
                            
                            quotes = {
                                'symbol': symbol,
                                'name': fields[0] if fields[0] else '',
                                'open': safe_float(fields[1]),
                                'pre_close': safe_float(fields[2]),
                                'price': safe_float(fields[3]),
                                'high': safe_float(fields[4]),
                                'low': safe_float(fields[5]),
                                'volume': safe_float(fields[8]),
                                'amount': safe_float(fields[9]),
                            }
                            # 计算涨跌幅
                            if quotes['pre_close'] > 0:
                                quotes['change'] = round(quotes['price'] - quotes['pre_close'], 3)
                                quotes['change_percent'] = round(
                                    (quotes['change'] / quotes['pre_close']) * 100, 2
                                )
                            print(f"[新浪个股] ✅ 成功获取实时行情: {quotes['name']} {quotes['price']}")
                            return quotes
            except Exception as e:
                print(f"[新浪个股] ❌ 获取失败: {e}")
                if retry_count < 2:
                    delay = (retry_count + 1) * 2
                    print(f"[新浪个股] ⏳ {delay}s 后重试...")
                    time.sleep(delay)
        
        # akshare失败，尝试tushare
        if self.tushare_available:
            try:
                print(f"[Tushare] 正在获取 {symbol} 的实时行情（备用数据源）...")
                
                ts_code = self._convert_to_ts_code(symbol)
                df = self.tushare_api.daily(
                    ts_code=ts_code,
                    start_date=datetime.now().strftime('%Y%m%d'),
                    end_date=datetime.now().strftime('%Y%m%d')
                )
                
                if df is not None and not df.empty:
                    row = df.iloc[0]
                    quotes = {
                        'symbol': symbol,
                        'price': row['close'],
                        'change_percent': row['pct_chg'],
                        'volume': row['vol'] * 100,
                        'amount': row['amount'] * 1000,
                        'high': row['high'],
                        'low': row['low'],
                        'open': row['open'],
                        'pre_close': row['pre_close']
                    }
                    print(f"[Tushare] ✅ 成功获取实时行情")
                    return quotes
            except Exception as e:
                print(f"[Tushare] ❌ 获取失败: {e}")
        
        return quotes
    
    def get_financial_data(self, symbol, report_type='income'):
        """
        获取财务数据（优先akshare，失败时使用tushare）
        
        Args:
            symbol: 股票代码
            report_type: 报表类型（'income'利润表, 'balance'资产负债表, 'cashflow'现金流量表）
            
        Returns:
            DataFrame: 财务数据
        """
        # 优先使用akshare（带重试机制）
        for retry_count in range(3):
            try:
                import akshare as ak
                print(f"[Akshare] 正在获取 {symbol} 的财务数据..." +
                      (f" (第{retry_count+1}次)" if retry_count > 0 else ""))
                
                if report_type == 'income':
                    df = ak.stock_financial_report_sina(stock=symbol, symbol="利润表")
                elif report_type == 'balance':
                    df = ak.stock_financial_report_sina(stock=symbol, symbol="资产负债表")
                elif report_type == 'cashflow':
                    df = ak.stock_financial_report_sina(stock=symbol, symbol="现金流量表")
                else:
                    df = None
                
                if df is not None and not df.empty:
                    print(f"[Akshare] ✅ 成功获取财务数据")
                    return df
            except Exception as e:
                print(f"[Akshare] ❌ 获取失败: {e}")
                if retry_count < 2:
                    delay = (retry_count + 1) * 2
                    print(f"[Akshare] ⏳ {delay}s 后重试...")
                    time.sleep(delay)
        
        # akshare失败，尝试tushare
        if self.tushare_available:
            try:
                print(f"[Tushare] 正在获取 {symbol} 的财务数据（备用数据源）...")
                
                ts_code = self._convert_to_ts_code(symbol)
                
                if report_type == 'income':
                    df = self.tushare_api.income(ts_code=ts_code)
                elif report_type == 'balance':
                    df = self.tushare_api.balancesheet(ts_code=ts_code)
                elif report_type == 'cashflow':
                    df = self.tushare_api.cashflow(ts_code=ts_code)
                else:
                    df = None
                
                if df is not None and not df.empty:
                    print(f"[Tushare] ✅ 成功获取财务数据")
                    return df
            except Exception as e:
                print(f"[Tushare] ❌ 获取失败: {e}")
        
        return None
    
    def _convert_to_ts_code(self, symbol):
        """
        将6位股票代码转换为tushare格式（带市场后缀）
        
        Args:
            symbol: 6位股票代码
            
        Returns:
            str: tushare格式代码（如：000001.SZ）
        """
        if not symbol or len(symbol) != 6:
            return symbol
        
        # 根据代码判断市场
        if symbol.startswith('6'):
            # 上海主板
            return f"{symbol}.SH"
        elif symbol.startswith('0') or symbol.startswith('3'):
            # 深圳主板和创业板
            return f"{symbol}.SZ"
        elif symbol.startswith('8') or symbol.startswith('4'):
            # 北交所
            return f"{symbol}.BJ"
        else:
            # 默认深圳
            return f"{symbol}.SZ"
    
    def _convert_from_ts_code(self, ts_code):
        """
        将tushare格式代码转换为6位代码
        
        Args:
            ts_code: tushare格式代码（如：000001.SZ）
            
        Returns:
            str: 6位股票代码
        """
        if '.' in ts_code:
            return ts_code.split('.')[0]
        return ts_code
    
    def _convert_to_tx_code(self, symbol):
        """
        将6位股票代码转换为腾讯数据源格式（带 sh/sz 前缀）
        
        Args:
            symbol: 6位股票代码
            
        Returns:
            str: 腾讯格式代码（如：sh603212, sz000001）
        """
        if not symbol or len(symbol) != 6:
            return symbol
        
        if symbol.startswith('6'):
            return f"sh{symbol}"
        elif symbol.startswith('0') or symbol.startswith('3'):
            return f"sz{symbol}"
        elif symbol.startswith('8') or symbol.startswith('4'):
            return f"bj{symbol}"
        else:
            return f"sz{symbol}"


# 全局数据源管理器实例
data_source_manager = DataSourceManager()

