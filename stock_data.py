import yfinance as yf
import akshare as ak
import pandas as pd
import numpy as np
import ta
from datetime import datetime, timedelta
import requests
import json
import pywencai
from data_source_manager import data_source_manager

class StockDataFetcher:
    """股票数据获取类"""
    
    def __init__(self):
        self.data = None
        self.info = None
        self.financial_data = None
        self.data_source_manager = data_source_manager
        
    def get_stock_info(self, symbol):
        """获取股票基本信息"""
        try:
            # 处理中国A股
            if self._is_chinese_stock(symbol):
                return self._get_chinese_stock_info(symbol)
            # 处理港股
            elif self._is_hk_stock(symbol):
                return self._get_hk_stock_info(symbol)
            # 处理美股
            else:
                return self._get_us_stock_info(symbol)
        except Exception as e:
            return {"error": f"获取股票信息失败: {str(e)}"}
    
    def get_stock_data(self, symbol, period="1y", interval="1d"):
        """获取股票历史数据"""
        try:
            if self._is_chinese_stock(symbol):
                return self._get_chinese_stock_data(symbol, period)
            elif self._is_hk_stock(symbol):
                return self._get_hk_stock_data(symbol, period)
            else:
                return self._get_us_stock_data(symbol, period, interval)
        except Exception as e:
            return {"error": f"获取股票数据失败: {str(e)}"}
    
    def _is_chinese_stock(self, symbol):
        """判断是否为中国A股"""
        # 简单判断：包含数字且长度为6位的认为是中国A股
        return symbol.isdigit() and len(symbol) == 6
    
    def _is_hk_stock(self, symbol):
        """判断是否为港股"""
        # 港股代码通常是1-5位数字，或者前面带HK/hk前缀
        if symbol.upper().startswith('HK'):
            return True
        # 纯数字且长度在1-5位之间，认为可能是港股
        if symbol.isdigit() and 1 <= len(symbol) <= 5:
            return True
        return False
    
    def _normalize_hk_code(self, symbol):
        """规范化港股代码为5位格式（如700 -> 00700）"""
        # 移除HK前缀
        if symbol.upper().startswith('HK'):
            symbol = symbol[2:]
        # 补齐到5位
        return symbol.zfill(5)
    
    def _get_chinese_stock_info(self, symbol):
        """获取中国股票基本信息（支持akshare和tushare数据源自动切换）"""
        try:
            # 初始化基本信息
            info = {
                "symbol": symbol,
                "name": "未知",
                "current_price": "N/A",
                "change_percent": "N/A",
                "pe_ratio": "N/A",
                "pb_ratio": "N/A",
                "market_cap": "N/A",
                "market": "中国A股",
                "exchange": "上海/深圳证券交易所"
            }
            
            # 先尝试使用数据源管理器获取基本信息
            basic_info = self.data_source_manager.get_stock_basic_info(symbol)
            if basic_info:
                info.update(basic_info)
            
            # 方法1: 尝试获取个股详细信息（akshare）
            try:
                stock_info = ak.stock_individual_info_em(symbol=symbol)
                if stock_info is not None and not stock_info.empty:
                    for _, row in stock_info.iterrows():
                        key = row['item']
                        value = row['value']
                        
                        if key == '股票简称':
                            info['name'] = value
                        elif key == '总市值':
                            try:
                                if value and value != '-':
                                    info['market_cap'] = float(value)
                            except:
                                pass
                        elif key == '市盈率-动态':
                            try:
                                if value and value != '-':
                                    pe_value = float(value)
                                    if 0 < pe_value <= 1000:
                                        info['pe_ratio'] = pe_value
                            except:
                                pass
                        elif key == '市净率':
                            try:
                                if value and value != '-':
                                    pb_value = float(value)
                                    if 0 < pb_value <= 100:
                                        info['pb_ratio'] = pb_value
                            except:
                                pass
            except Exception as e:
                print(f"[Akshare] 获取个股详细信息失败: {e}")
                # 如果akshare失败，尝试从tushare获取
                if self.data_source_manager.tushare_available and info['name'] == '未知':
                    print(f"[Tushare] 尝试获取基本信息（备用数据源）...")
                    try:
                        ts_code = self.data_source_manager._convert_to_ts_code(symbol)
                        df = self.data_source_manager.tushare_api.daily_basic(
                            ts_code=ts_code,
                            trade_date=datetime.now().strftime('%Y%m%d')
                        )
                        if df is not None and not df.empty:
                            row = df.iloc[0]
                            info['pe_ratio'] = row.get('pe', 'N/A')
                            info['pb_ratio'] = row.get('pb', 'N/A')
                            info['market_cap'] = row.get('total_mv', 'N/A')
                            print(f"[Tushare] ✅ 成功获取部分信息")
                    except Exception as te:
                        print(f"[Tushare] ❌ 获取失败: {te}")
            
            # 方法2: 尝试获取实时价格和涨跌幅（如果网络允许）
            try:
                # 使用更简单的接口获取实时价格
                real_time_data = ak.stock_zh_a_spot_em()
                if real_time_data is not None and not real_time_data.empty:
                    stock_real_time = real_time_data[real_time_data['代码'] == symbol]
                    if not stock_real_time.empty:
                        row = stock_real_time.iloc[0]
                        info['current_price'] = row.get('最新价', 'N/A')
                        info['change_percent'] = row.get('涨跌幅', 'N/A')
                        if info['name'] == '未知':
                            info['name'] = row.get('名称', '未知')
                        
                        # 如果实时数据中有市盈率和市净率，优先使用
                        if '市盈率-动态' in row and info['pe_ratio'] == 'N/A':
                            try:
                                pe_val = row['市盈率-动态']
                                if pe_val and pe_val != '-':
                                    pe_val = float(pe_val)
                                    if 0 < pe_val <= 1000:
                                        info['pe_ratio'] = pe_val
                            except:
                                pass
                        
                        if '市净率' in row and info['pb_ratio'] == 'N/A':
                            try:
                                pb_val = row['市净率']
                                if pb_val and pb_val != '-':
                                    pb_val = float(pb_val)
                                    if 0 < pb_val <= 100:
                                        info['pb_ratio'] = pb_val
                            except:
                                pass
                                
            except Exception as e:
                print(f"[Akshare] 获取实时数据失败: {e}")
                # 如果实时数据获取失败，尝试使用数据源管理器获取历史数据（支持tushare备用）
                try:
                    print(f"[数据源管理器] 尝试获取最近交易数据...")
                    hist_data = self.data_source_manager.get_stock_hist_data(
                        symbol=symbol,
                        start_date=(datetime.now() - timedelta(days=5)).strftime('%Y%m%d'),
                        end_date=datetime.now().strftime('%Y%m%d'),
                        adjust='qfq'
                    )
                    
                    if hist_data is not None and not hist_data.empty:
                        # 标准化列名
                        if 'close' in hist_data.columns:
                            latest = hist_data.iloc[-1]
                            info['current_price'] = latest['close']
                            # 计算涨跌幅
                            if len(hist_data) > 1:
                                prev_close = hist_data.iloc[-2]['close']
                                change_pct = ((latest['close'] - prev_close) / prev_close) * 100
                                info['change_percent'] = round(change_pct, 2)
                            print(f"[数据源管理器] ✅ 成功获取价格数据")
                except Exception as e2:
                    print(f"获取历史数据也失败: {e2}")
            
            # 方法3: 使用百度估值数据获取市盈率和市净率
            if info['pe_ratio'] == 'N/A':
                try:
                    pe_data = ak.stock_zh_valuation_baidu(symbol=symbol, indicator="市盈率(TTM)")
                    if pe_data is not None and not pe_data.empty:
                        latest_pe = pe_data.iloc[-1]['value']
                        if latest_pe and latest_pe != '-':
                            pe_val = float(latest_pe)
                            if 0 < pe_val <= 1000:
                                info['pe_ratio'] = pe_val
                except Exception as e:
                    print(f"获取市盈率失败: {e}")
            
            if info['pb_ratio'] == 'N/A':
                try:
                    pb_data = ak.stock_zh_valuation_baidu(symbol=symbol, indicator="市净率")
                    if pb_data is not None and not pb_data.empty:
                        latest_pb = pb_data.iloc[-1]['value']
                        if latest_pb and latest_pb != '-':
                            pb_val = float(latest_pb)
                            if 0 < pb_val <= 100:
                                info['pb_ratio'] = pb_val
                except Exception as e:
                    print(f"获取市净率失败: {e}")
            
            return info
            
        except Exception as e:
            print(f"获取中国股票信息完全失败: {e}")
            # 返回基本信息，避免完全失败
            return {
                "symbol": symbol,
                "name": f"股票{symbol}",
                "current_price": "N/A",
                "change_percent": "N/A",
                "pe_ratio": "N/A",
                "pb_ratio": "N/A",
                "market_cap": "N/A",
                "market": "中国A股",
                "exchange": "上海/深圳证券交易所"
            }
    
    def _get_hk_stock_info(self, symbol):
        """获取港股基本信息"""
        try:
            # 规范化港股代码
            hk_code = self._normalize_hk_code(symbol)
            
            # 初始化基本信息
            info = {
                "symbol": hk_code,
                "name": "未知",
                "current_price": "N/A",
                "change_percent": "N/A",
                "pe_ratio": "N/A",
                "pb_ratio": "N/A",
                "market_cap": "N/A",
                "market": "香港股市",
                "exchange": "香港交易所"
            }
            
            # 方法1: 获取港股实时行情
            try:
                # 使用akshare获取港股实时数据
                realtime_df = ak.stock_hk_spot_em()
                if realtime_df is not None and not realtime_df.empty:
                    # 查找对应股票
                    stock_data = realtime_df[realtime_df['代码'] == hk_code]
                    if not stock_data.empty:
                        row = stock_data.iloc[0]
                        info['name'] = row.get('名称', '未知')
                        info['current_price'] = row.get('最新价', 'N/A')
                        info['change_percent'] = row.get('涨跌幅', 'N/A')
                        
                        # 市值（港元）
                        market_cap = row.get('总市值', 'N/A')
                        if market_cap != 'N/A':
                            try:
                                info['market_cap'] = float(market_cap)
                            except:
                                pass
                        
                        # 市盈率
                        pe = row.get('市盈率', 'N/A')
                        if pe != 'N/A' and pe != '-':
                            try:
                                pe_val = float(pe)
                                if 0 < pe_val <= 1000:
                                    info['pe_ratio'] = pe_val
                            except:
                                pass
            except Exception as e:
                print(f"获取港股实时数据失败: {e}")
            
            # 方法2: 尝试使用历史数据获取价格信息
            if info['current_price'] == 'N/A':
                try:
                    hist_df = ak.stock_hk_hist(symbol=hk_code, period="daily", 
                                              start_date=(datetime.now() - timedelta(days=5)).strftime('%Y%m%d'),
                                              end_date=datetime.now().strftime('%Y%m%d'), adjust="qfq")
                    if hist_df is not None and not hist_df.empty:
                        latest = hist_df.iloc[-1]
                        info['current_price'] = latest['收盘']
                        # 计算涨跌幅
                        if len(hist_df) > 1:
                            prev_close = hist_df.iloc[-2]['收盘']
                            change_pct = ((latest['收盘'] - prev_close) / prev_close) * 100
                            info['change_percent'] = round(change_pct, 2)
                except Exception as e:
                    print(f"获取港股历史数据失败: {e}")
            
            return info
            
        except Exception as e:
            print(f"获取港股信息完全失败: {e}")
            # 返回基本信息
            return {
                "symbol": symbol,
                "name": f"港股{symbol}",
                "current_price": "N/A",
                "change_percent": "N/A",
                "pe_ratio": "N/A",
                "pb_ratio": "N/A",
                "market_cap": "N/A",
                "market": "香港股市",
                "exchange": "香港交易所"
            }
    
    def _get_us_stock_info(self, symbol):
        """获取美股基本信息"""
        import time
        
        try:
            # 添加延迟避免频率限制
            time.sleep(1)
            
            ticker = yf.Ticker(symbol)
            
            # 先尝试获取历史数据（通常更稳定）
            try:
                hist = ticker.history(period="2d")
                if not hist.empty:
                    current_price = hist['Close'].iloc[-1]
                    if len(hist) > 1:
                        prev_close = hist['Close'].iloc[-2]
                        change_percent = ((current_price - prev_close) / prev_close) * 100
                    else:
                        change_percent = 'N/A'
                else:
                    current_price = 'N/A'
                    change_percent = 'N/A'
            except:
                current_price = 'N/A'
                change_percent = 'N/A'
            
            # 获取基本信息
            try:
                info = ticker.info
                
                # 获取市盈率，优先使用trailing PE，其次forward PE
                pe_ratio = info.get('trailingPE', info.get('forwardPE', 'N/A'))
                if pe_ratio == 'N/A' or pe_ratio is None or (isinstance(pe_ratio, float) and np.isnan(pe_ratio)):
                    pe_ratio = 'N/A'
                
                # 获取市净率
                pb_ratio = info.get('priceToBook', 'N/A')
                if pb_ratio == 'N/A' or pb_ratio is None or (isinstance(pb_ratio, float) and np.isnan(pb_ratio)):
                    pb_ratio = 'N/A'
                
                # 如果历史数据没有获取到价格，尝试从info获取
                if current_price == 'N/A':
                    current_price = info.get('currentPrice', info.get('regularMarketPrice', 'N/A'))
                
                if change_percent == 'N/A':
                    change_percent = info.get('regularMarketChangePercent', 'N/A')
                    if change_percent != 'N/A' and change_percent is not None:
                        change_percent = change_percent * 100  # 转换为百分比
                
                return {
                    "symbol": symbol,
                    "name": info.get('longName', info.get('shortName', 'N/A')),
                    "current_price": current_price,
                    "change_percent": change_percent,
                    "market_cap": info.get('marketCap', 'N/A'),
                    "pe_ratio": pe_ratio,
                    "pb_ratio": pb_ratio,
                    "dividend_yield": info.get('dividendYield', 'N/A'),
                    "beta": info.get('beta', 'N/A'),
                    "52_week_high": info.get('fiftyTwoWeekHigh', 'N/A'),
                    "52_week_low": info.get('fiftyTwoWeekLow', 'N/A'),
                    "sector": info.get('sector', 'N/A'),
                    "industry": info.get('industry', 'N/A'),
                    "market": "美股",
                    "exchange": info.get('exchange', 'N/A')
                }
                
            except Exception as e:
                # 如果获取详细信息失败，返回基本价格信息
                return {
                    "symbol": symbol,
                    "name": f"美股{symbol}",
                    "current_price": current_price,
                    "change_percent": change_percent,
                    "market_cap": 'N/A',
                    "pe_ratio": 'N/A',
                    "pb_ratio": 'N/A',
                    "dividend_yield": 'N/A',
                    "beta": 'N/A',
                    "52_week_high": 'N/A',
                    "52_week_low": 'N/A',
                    "sector": 'N/A',
                    "industry": 'N/A',
                    "market": "美股",
                    "exchange": 'N/A'
                }
                
        except Exception as e:
            return {"error": f"获取美股信息失败: {str(e)}"}
    
    def _get_chinese_stock_data(self, symbol, period="1y"):
        """获取中国股票历史数据（支持akshare和tushare数据源自动切换）"""
        try:
            # 计算日期范围
            end_date = datetime.now().strftime('%Y%m%d')
            if period == "1y":
                start_date = (datetime.now() - timedelta(days=365)).strftime('%Y%m%d')
            elif period == "6mo":
                start_date = (datetime.now() - timedelta(days=180)).strftime('%Y%m%d')
            elif period == "3mo":
                start_date = (datetime.now() - timedelta(days=90)).strftime('%Y%m%d')
            else:
                start_date = (datetime.now() - timedelta(days=365)).strftime('%Y%m%d')
            
            # 使用数据源管理器获取数据（自动切换akshare和tushare）
            df = self.data_source_manager.get_stock_hist_data(
                symbol=symbol,
                start_date=start_date,
                end_date=end_date,
                adjust='qfq'
            )
            
            if df is not None and not df.empty:
                # 标准化列名为大写（与原有格式保持一致）
                df = df.rename(columns={
                    'date': 'Date',
                    'open': 'Open',
                    'close': 'Close',
                    'high': 'High',
                    'low': 'Low',
                    'volume': 'Volume'
                })
                
                # 确保Date列为datetime类型
                if 'Date' not in df.columns and df.index.name == 'date':
                    df.index.name = 'Date'
                elif 'Date' in df.columns:
                    df['Date'] = pd.to_datetime(df['Date'])
                    df.set_index('Date', inplace=True)
                
                print(f"✅ 成功获取 {symbol} 的历史数据，共 {len(df)} 条记录")
                return df
            else:
                return {"error": "所有数据源均无法获取历史数据"}
                
        except Exception as e:
            return {"error": f"获取中国股票数据失败: {str(e)}"}
    
    def _get_hk_stock_data(self, symbol, period="1y"):
        """获取港股历史数据"""
        try:
            # 规范化港股代码
            hk_code = self._normalize_hk_code(symbol)
            
            # 计算日期范围
            end_date = datetime.now().strftime('%Y%m%d')
            if period == "1y":
                start_date = (datetime.now() - timedelta(days=365)).strftime('%Y%m%d')
            elif period == "6mo":
                start_date = (datetime.now() - timedelta(days=180)).strftime('%Y%m%d')
            elif period == "3mo":
                start_date = (datetime.now() - timedelta(days=90)).strftime('%Y%m%d')
            elif period == "1mo":
                start_date = (datetime.now() - timedelta(days=30)).strftime('%Y%m%d')
            else:
                start_date = (datetime.now() - timedelta(days=365)).strftime('%Y%m%d')
            
            # 获取港股历史数据
            df = ak.stock_hk_hist(symbol=hk_code, period="daily", 
                                start_date=start_date, end_date=end_date, adjust="qfq")
            
            if df is not None and not df.empty:
                # 重命名列以匹配标准格式
                df = df.rename(columns={
                    '日期': 'Date',
                    '开盘': 'Open',
                    '收盘': 'Close',
                    '最高': 'High',
                    '最低': 'Low',
                    '成交量': 'Volume'
                })
                df['Date'] = pd.to_datetime(df['Date'])
                df.set_index('Date', inplace=True)
                return df
            else:
                return {"error": "无法获取港股历史数据"}
                
        except Exception as e:
            return {"error": f"获取港股数据失败: {str(e)}"}
    
    def _get_us_stock_data(self, symbol, period="1y", interval="1d"):
        """获取美股历史数据"""
        try:
            ticker = yf.Ticker(symbol)
            df = ticker.history(period=period, interval=interval)
            if not df.empty:
                return df
            else:
                return {"error": "无法获取历史数据"}
        except Exception as e:
            return {"error": f"获取美股数据失败: {str(e)}"}
    
    def calculate_technical_indicators(self, df):
        """计算技术指标"""
        try:
            if isinstance(df, dict) and "error" in df:
                return df
                
            # 移动平均线
            df['MA5'] = ta.trend.sma_indicator(df['Close'], window=5)
            df['MA10'] = ta.trend.sma_indicator(df['Close'], window=10)
            df['MA20'] = ta.trend.sma_indicator(df['Close'], window=20)
            df['MA60'] = ta.trend.sma_indicator(df['Close'], window=60)
            
            # RSI
            df['RSI'] = ta.momentum.rsi(df['Close'], window=14)
            
            # MACD
            macd = ta.trend.MACD(df['Close'])
            df['MACD'] = macd.macd()
            df['MACD_signal'] = macd.macd_signal()
            df['MACD_histogram'] = macd.macd_diff()
            
            # 布林带
            bollinger = ta.volatility.BollingerBands(df['Close'])
            df['BB_upper'] = bollinger.bollinger_hband()
            df['BB_middle'] = bollinger.bollinger_mavg()
            df['BB_lower'] = bollinger.bollinger_lband()
            
            # KDJ指标
            df['K'] = ta.momentum.stoch(df['High'], df['Low'], df['Close'])
            df['D'] = ta.momentum.stoch_signal(df['High'], df['Low'], df['Close'])
            
            # 成交量指标
            df['Volume_MA5'] = ta.trend.sma_indicator(df['Volume'], window=5)
            df['Volume_ratio'] = df['Volume'] / df['Volume_MA5']
            
            return df
            
        except Exception as e:
            return {"error": f"计算技术指标失败: {str(e)}"}
    
    def get_latest_indicators(self, df):
        """获取最新的技术指标值"""
        try:
            if isinstance(df, dict) and "error" in df:
                return df
                
            latest = df.iloc[-1]
            
            return {
                "price": latest['Close'],
                "ma5": latest['MA5'],
                "ma10": latest['MA10'], 
                "ma20": latest['MA20'],
                "ma60": latest['MA60'],
                "rsi": latest['RSI'],
                "macd": latest['MACD'],
                "macd_signal": latest['MACD_signal'],
                "bb_upper": latest['BB_upper'],
                "bb_lower": latest['BB_lower'],
                "k_value": latest['K'],
                "d_value": latest['D'],
                "volume_ratio": latest['Volume_ratio']
            }
        except Exception as e:
            return {"error": f"获取最新指标失败: {str(e)}"}
    
    def get_financial_data(self, symbol):
        """获取详细财务数据"""
        try:
            if self._is_chinese_stock(symbol):
                return self._get_chinese_financial_data(symbol)
            elif self._is_hk_stock(symbol):
                return self._get_hk_financial_data(symbol)
            else:
                return self._get_us_financial_data(symbol)
        except Exception as e:
            return {"error": f"获取财务数据失败: {str(e)}"}
    
    def _get_chinese_financial_data(self, symbol):
        """获取中国股票财务数据"""
        financial_data = {
            "symbol": symbol,
            "balance_sheet": None,  # 资产负债表
            "income_statement": None,  # 利润表
            "cash_flow": None,  # 现金流量表
            "financial_ratios": {},  # 财务比率
            "quarter_data": None,  # 季度数据
        }
        
        try:
            # 1. 获取资产负债表
            try:
                balance_sheet = ak.stock_financial_abstract_ths(symbol=symbol, indicator="资产负债表")
                if balance_sheet is not None and not balance_sheet.empty:
                    financial_data["balance_sheet"] = balance_sheet.head(8).to_dict('records')
            except Exception as e:
                print(f"获取资产负债表失败: {e}")
            
            # 2. 获取利润表
            try:
                income_statement = ak.stock_financial_abstract_ths(symbol=symbol, indicator="利润表")
                if income_statement is not None and not income_statement.empty:
                    financial_data["income_statement"] = income_statement.head(8).to_dict('records')
            except Exception as e:
                print(f"获取利润表失败: {e}")
            
            # 3. 获取现金流量表
            try:
                cash_flow = ak.stock_financial_abstract_ths(symbol=symbol, indicator="现金流量表")
                if cash_flow is not None and not cash_flow.empty:
                    financial_data["cash_flow"] = cash_flow.head(8).to_dict('records')
            except Exception as e:
                print(f"获取现金流量表失败: {e}")
            
            # 4. 获取主要财务指标
            try:
                financial_indicators = ak.stock_financial_analysis_indicator(symbol=symbol)
                if financial_indicators is not None and not financial_indicators.empty:
                    latest_data = financial_indicators.iloc[0]
                    
                    financial_data["financial_ratios"] = {
                        "报告期": latest_data.get('报告期', 'N/A'),
                        "净资产收益率ROE": latest_data.get('净资产收益率', 'N/A'),
                        "总资产收益率ROA": latest_data.get('总资产收益率', 'N/A'),
                        "销售毛利率": latest_data.get('销售毛利率', 'N/A'),
                        "销售净利率": latest_data.get('销售净利率', 'N/A'),
                        "资产负债率": latest_data.get('资产负债率', 'N/A'),
                        "流动比率": latest_data.get('流动比率', 'N/A'),
                        "速动比率": latest_data.get('速动比率', 'N/A'),
                        "存货周转率": latest_data.get('存货周转率', 'N/A'),
                        "应收账款周转率": latest_data.get('应收账款周转率', 'N/A'),
                        "总资产周转率": latest_data.get('总资产周转率', 'N/A'),
                        "营业收入同比增长": latest_data.get('营业收入同比增长', 'N/A'),
                        "净利润同比增长": latest_data.get('净利润同比增长', 'N/A'),
                    }
            except Exception as e:
                print(f"获取财务指标失败: {e}")
            
            # 注意：季报数据现在由 quarterly_report_data.py 模块使用 akshare 获取（8期完整季报）
            # 不再使用问财获取季报，避免重复
            
            return financial_data
            
        except Exception as e:
            print(f"获取中国股票财务数据失败: {e}")
            return financial_data
    
    # 已删除 _get_quarter_data_from_wencai 方法
    # 季报数据现在统一由 quarterly_report_data.py 模块使用 akshare 获取
    # 获取最近8期完整季报（利润表、资产负债表、现金流量表）
    # 避免重复获取，提高效率
    
    def _get_hk_financial_data(self, symbol):
        """获取港股财务数据"""
        hk_code = self._normalize_hk_code(symbol)
        
        financial_data = {
            "symbol": hk_code,
            "balance_sheet": None,
            "income_statement": None,
            "cash_flow": None,
            "financial_ratios": {},
            "quarter_data": None,
            "data_source": "eastmoney",
            "note": "港股财务数据来自东方财富"
        }
        
        try:
            # 使用akshare获取港股财务指标（东方财富数据源）
            print(f"正在获取港股 {hk_code} 的财务指标...")
            try:
                financial_indicator = ak.stock_hk_financial_indicator_em(symbol=hk_code)
                
                if financial_indicator is not None and not financial_indicator.empty:
                    # 将财务指标数据转换为字典
                    indicator_dict = financial_indicator.iloc[0].to_dict()
                    
                    # 整理财务比率数据
                    financial_data["financial_ratios"] = {
                        "基本每股收益": self._safe_convert(indicator_dict.get('基本每股收益(元)', 'N/A')),
                        "每股净资产": self._safe_convert(indicator_dict.get('每股净资产(元)', 'N/A')),
                        "每股股息TTM": self._safe_convert(indicator_dict.get('每股股息TTM(港元)', 'N/A')),
                        "派息比率": self._safe_convert(indicator_dict.get('派息比率(%)', 'N/A')),
                        "每股经营现金流": self._safe_convert(indicator_dict.get('每股经营现金流(元)', 'N/A')),
                        "股息率TTM": self._safe_convert(indicator_dict.get('股息率TTM(%)', 'N/A')),
                        "总市值": self._safe_convert(indicator_dict.get('总市值(港元)', 'N/A')),
                        "港股市值": self._safe_convert(indicator_dict.get('港股市值(港元)', 'N/A')),
                        "营业总收入": self._safe_convert(indicator_dict.get('营业总收入', 'N/A')),
                        "营业收入环比增长": self._safe_convert(indicator_dict.get('营业总收入滚动环比增长(%)', 'N/A')),
                        "销售净利率": self._safe_convert(indicator_dict.get('销售净利率(%)', 'N/A')),
                        "净利润": self._safe_convert(indicator_dict.get('净利润', 'N/A')),
                        "净利润环比增长": self._safe_convert(indicator_dict.get('净利润滚动环比增长(%)', 'N/A')),
                        "ROE股东权益回报率": self._safe_convert(indicator_dict.get('股东权益回报率(%)', 'N/A')),
                        "市盈率": self._safe_convert(indicator_dict.get('市盈率', 'N/A')),
                        "市净率": self._safe_convert(indicator_dict.get('市净率', 'N/A')),
                        "ROA总资产回报率": self._safe_convert(indicator_dict.get('总资产回报率(%)', 'N/A')),
                        "法定股本": self._safe_convert(indicator_dict.get('法定股本(股)', 'N/A')),
                        "已发行股本": self._safe_convert(indicator_dict.get('已发行股本(股)', 'N/A')),
                        "每手股": self._safe_convert(indicator_dict.get('每手股', 'N/A')),
                    }
                    
                    print(f"✅ 成功获取港股 {hk_code} 的财务指标")
                    print(f"   ROE: {financial_data['financial_ratios']['ROE股东权益回报率']}")
                    print(f"   市盈率: {financial_data['financial_ratios']['市盈率']}")
                    print(f"   市净率: {financial_data['financial_ratios']['市净率']}")
                else:
                    print(f"⚠️ 未获取到港股 {hk_code} 的财务指标数据")
                    financial_data["note"] = "未获取到财务数据"
                    
            except Exception as e:
                print(f"⚠️ 获取港股财务指标失败: {e}")
                financial_data["note"] = f"获取财务数据失败: {str(e)}"
            
            return financial_data
            
        except Exception as e:
            print(f"获取港股财务数据异常: {e}")
            financial_data["note"] = f"获取失败: {str(e)}"
            return financial_data
    
    def _get_us_financial_data(self, symbol):
        """获取美股财务数据"""
        financial_data = {
            "symbol": symbol,
            "balance_sheet": None,
            "income_statement": None,
            "cash_flow": None,
            "financial_ratios": {},
            "quarter_data": None,
        }
        
        try:
            stock = yf.Ticker(symbol)
            info = stock.info
            
            # 1. 资产负债表
            try:
                balance_sheet = stock.balance_sheet
                if balance_sheet is not None and not balance_sheet.empty:
                    financial_data["balance_sheet"] = balance_sheet.iloc[:, :4].to_dict('index')
            except Exception as e:
                print(f"获取资产负债表失败: {e}")
            
            # 2. 利润表
            try:
                income_stmt = stock.income_stmt
                if income_stmt is not None and not income_stmt.empty:
                    financial_data["income_statement"] = income_stmt.iloc[:, :4].to_dict('index')
            except Exception as e:
                print(f"获取利润表失败: {e}")
            
            # 3. 现金流量表
            try:
                cash_flow = stock.cashflow
                if cash_flow is not None and not cash_flow.empty:
                    financial_data["cash_flow"] = cash_flow.iloc[:, :4].to_dict('index')
            except Exception as e:
                print(f"获取现金流量表失败: {e}")
            
            # 4. 财务比率（从info中提取）
            financial_data["financial_ratios"] = {
                "ROE": info.get('returnOnEquity', 'N/A'),
                "ROA": info.get('returnOnAssets', 'N/A'),
                "毛利率": info.get('grossMargins', 'N/A'),
                "营业利润率": info.get('operatingMargins', 'N/A'),
                "净利率": info.get('profitMargins', 'N/A'),
                "资产负债率": info.get('debtToEquity', 'N/A'),
                "流动比率": info.get('currentRatio', 'N/A'),
                "速动比率": info.get('quickRatio', 'N/A'),
                "EPS": info.get('trailingEps', 'N/A'),
                "每股账面价值": info.get('bookValue', 'N/A'),
                "股息率": info.get('dividendYield', 'N/A'),
                "派息率": info.get('payoutRatio', 'N/A'),
                "收入增长": info.get('revenueGrowth', 'N/A'),
                "盈利增长": info.get('earningsGrowth', 'N/A'),
            }
            
            return financial_data
            
        except Exception as e:
            print(f"获取美股财务数据失败: {e}")
            return financial_data
    
    # 已删除 get_fund_flow_data 方法（使用问财）
    # 资金流向数据现在统一由 fund_flow_akshare.py 模块使用 akshare 获取
    # 获取近20个交易日的详细资金流向数据（主力、超大单、大单、中单、小单）
    # 避免重复获取，提高效率和数据质量
    # 
    # 删除说明：
    # - 删除了约160行代码
    # - 删除原因：重复获取，数据格式不规整，日期范围不准确
    # - 新方案：使用 akshare 的 stock_individual_fund_flow 接口
    # - 新方案优势：数据标准化、准确获取最近20个交易日、6类资金详细分类
    
    def get_risk_data(self, symbol):
        """
        获取股票风险数据（限售解禁、大股东减持、重要事件）
        只支持中国A股
        """
        try:
            # 只有中国A股才支持风险数据查询
            if not self._is_chinese_stock(symbol):
                return {
                    'symbol': symbol,
                    'data_success': False,
                    'error': '仅支持中国A股风险数据查询'
                }
            
            # 使用风险数据获取器
            from risk_data_fetcher import RiskDataFetcher
            fetcher = RiskDataFetcher()
            risk_data = fetcher.get_risk_data(symbol)
            
            return risk_data
            
        except Exception as e:
            return {
                'symbol': symbol,
                'data_success': False,
                'error': f'获取风险数据失败: {str(e)}'
            }
    
    def _safe_convert(self, value):
        """安全地转换数值"""
        if value is None or value == '' or (isinstance(value, float) and np.isnan(value)):
            return 'N/A'
        try:
            if isinstance(value, str):
                # 移除百分号和逗号
                value = value.replace('%', '').replace(',', '')
                return float(value)
            return value
        except:
            return value
    
    def _calculate_main_fund_ratio(self, main_fund, total_fund):
        """计算主力资金占比"""
        try:
            if main_fund != 'N/A' and total_fund != 'N/A' and total_fund != 0:
                ratio = (main_fund / total_fund) * 100
                return f"{ratio:.2f}%"
        except:
            pass
        return 'N/A'
