#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
TDX股票数据API使用示例

演示如何使用所有API接口获取股票数据
"""

import requests
import json
from datetime import datetime

# 配置
BASE_URL = "http://localhost:8080"  # 修改为你的服务器地址

class StockAPI:
    """股票数据API客户端"""
    
    def __init__(self, base_url=BASE_URL):
        self.base_url = base_url
    
    def get_quote(self, code):
        """获取五档行情"""
        url = f"{self.base_url}/api/quote?code={code}"
        response = requests.get(url)
        data = response.json()
        if data['code'] == 0:
            return data['data']
        return None
    
    def get_kline(self, code, ktype='day', limit=100):
        """获取K线数据"""
        url = f"{self.base_url}/api/kline?code={code}&type={ktype}"
        response = requests.get(url)
        data = response.json()
        if data['code'] == 0:
            return data['data']['List']
        return None
    
    def get_minute(self, code, date=None):
        """获取分时数据（返回包含date/Count/List的字典）"""
        url = f"{self.base_url}/api/minute?code={code}"
        if date:
            url += f"&date={date}"
        response = requests.get(url)
        data = response.json()
        if data['code'] == 0:
            return data['data']
        return None
    
    def get_trade(self, code, date=None):
        """获取分时成交"""
        url = f"{self.base_url}/api/trade?code={code}"
        if date:
            url += f"&date={date}"
        response = requests.get(url)
        data = response.json()
        if data['code'] == 0:
            return data['data']['List']
        return None
    
    def search(self, keyword):
        """搜索股票"""
        url = f"{self.base_url}/api/search?keyword={keyword}"
        response = requests.get(url)
        data = response.json()
        if data['code'] == 0:
            return data['data']
        return None
    
    def get_stock_info(self, code):
        """获取股票综合信息"""
        url = f"{self.base_url}/api/stock-info?code={code}"
        response = requests.get(url)
        data = response.json()
        if data['code'] == 0:
            return data['data']
        return None
    
    def get_all_codes(self, exchange='all'):
        """获取股票代码列表"""
        url = f"{self.base_url}/api/codes?exchange={exchange}"
        response = requests.get(url)
        data = response.json()
        if data['code'] == 0:
            return data['data']
        return None
    
    def batch_get_quote(self, codes):
        """批量获取行情"""
        url = f"{self.base_url}/api/batch-quote"
        response = requests.post(url, json={'codes': codes})
        data = response.json()
        if data['code'] == 0:
            return data['data']
        return None

    def get_etf_list(self, exchange=None, limit=None):
        """获取ETF基金列表"""
        params = {}
        if exchange:
            params['exchange'] = exchange
        if limit:
            params['limit'] = limit
        url = f"{self.base_url}/api/etf"
        response = requests.get(url, params=params)
        data = response.json()
        if data['code'] == 0:
            return data['data']
        return None

    def get_trade_history(self, code, date, start=0, count=2000):
        """获取历史分时成交（分页）"""
        params = {'code': code, 'date': date}
        if start:
            params['start'] = start
        if count:
            params['count'] = count
        url = f"{self.base_url}/api/trade-history"
        response = requests.get(url, params=params)
        data = response.json()
        if data['code'] == 0:
            return data['data']
        return None

    def get_minute_trade_all(self, code, date=None):
        """获取全天分时成交"""
        params = {'code': code}
        if date:
            params['date'] = date
        url = f"{self.base_url}/api/minute-trade-all"
        response = requests.get(url, params=params)
        data = response.json()
        if data['code'] == 0:
            return data['data']
        return None

    def get_workday(self, date=None, count=None):
        """查询交易日信息"""
        params = {}
        if date:
            params['date'] = date
        if count:
            params['count'] = count
        url = f"{self.base_url}/api/workday"
        response = requests.get(url, params=params)
        data = response.json()
        if data['code'] == 0:
            return data['data']
        return None

    def create_pull_kline_task(self, codes=None, tables=None, limit=None, start_date=None, directory=None):
        """创建批量K线入库任务"""
        payload = {}
        if codes:
            payload['codes'] = codes
        if tables:
            payload['tables'] = tables
        if limit:
            payload['limit'] = limit
        if start_date:
            payload['start_date'] = start_date
        if directory:
            payload['dir'] = directory
        url = f"{self.base_url}/api/tasks/pull-kline"
        response = requests.post(url, json=payload or {})
        data = response.json()
        if data['code'] == 0:
            return data['data']['task_id']
        raise RuntimeError(data.get('message', '创建任务失败'))

    def create_pull_trade_task(self, code, start_year=None, end_year=None, directory=None):
        """创建分时成交入库任务"""
        payload = {'code': code}
        if start_year:
            payload['start_year'] = start_year
        if end_year:
            payload['end_year'] = end_year
        if directory:
            payload['dir'] = directory
        url = f"{self.base_url}/api/tasks/pull-trade"
        response = requests.post(url, json=payload)
        data = response.json()
        if data['code'] == 0:
            return data['data']['task_id']
        raise RuntimeError(data.get('message', '创建任务失败'))

    def list_tasks(self):
        """查询所有任务"""
        url = f"{self.base_url}/api/tasks"
        response = requests.get(url)
        data = response.json()
        if data['code'] == 0:
            return data['data']
        return []

    def get_task(self, task_id):
        """查询任务详情"""
        url = f"{self.base_url}/api/tasks/{task_id}"
        response = requests.get(url)
        data = response.json()
        if data['code'] == 0:
            return data['data']
        return None

    def cancel_task(self, task_id):
        """取消任务"""
        url = f"{self.base_url}/api/tasks/{task_id}/cancel"
        response = requests.post(url)
        data = response.json()
        return data

    def get_market_count(self):
        """获取市场证券数量"""
        url = f"{self.base_url}/api/market-count"
        response = requests.get(url)
        data = response.json()
        if data['code'] == 0:
            return data['data']
        return None

    def get_stock_codes(self, limit=None, prefix=True):
        """获取全部股票代码"""
        params = {}
        if limit:
            params['limit'] = limit
        if not prefix:
            params['prefix'] = 'false'
        url = f"{self.base_url}/api/stock-codes"
        response = requests.get(url, params=params)
        data = response.json()
        if data['code'] == 0:
            return data['data']
        return None

    def get_etf_codes(self, limit=None, prefix=True):
        """获取全部ETF代码"""
        params = {}
        if limit:
            params['limit'] = limit
        if not prefix:
            params['prefix'] = 'false'
        url = f"{self.base_url}/api/etf-codes"
        response = requests.get(url, params=params)
        data = response.json()
        if data['code'] == 0:
            return data['data']
        return None

    def get_kline_all(self, code, ktype='day', limit=None):
        """获取股票全量历史K线"""
        params = {'code': code, 'type': ktype}
        if limit:
            params['limit'] = limit
        url = f"{self.base_url}/api/kline-all"
        response = requests.get(url, params=params)
        data = response.json()
        if data['code'] == 0:
            return data['data']
        return None

    def get_index_all(self, code, ktype='day', limit=None):
        """获取指数全量历史K线"""
        params = {'code': code, 'type': ktype}
        if limit:
            params['limit'] = limit
        url = f"{self.base_url}/api/index/all"
        response = requests.get(url, params=params)
        data = response.json()
        if data['code'] == 0:
            return data['data']
        return None

    def get_trade_history_full(self, code, before=None, limit=None):
        """获取上市以来分时成交"""
        params = {'code': code}
        if before:
            params['before'] = before
        if limit:
            params['limit'] = limit
        url = f"{self.base_url}/api/trade-history/full"
        response = requests.get(url, params=params)
        data = response.json()
        if data['code'] == 0:
            return data['data']
        return None

    def get_workday_range(self, start, end):
        """获取交易日范围"""
        params = {'start': start, 'end': end}
        url = f"{self.base_url}/api/workday/range"
        response = requests.get(url, params=params)
        data = response.json()
        if data['code'] == 0:
            return data['data']
        return None

    def get_income(self, code, start_date, days=None):
        """收益区间分析"""
        params = {'code': code, 'start_date': start_date}
        if days:
            params['days'] = ",".join(str(d) for d in days)
        url = f"{self.base_url}/api/income"
        response = requests.get(url, params=params)
        data = response.json()
        if data['code'] == 0:
            return data['data']
        return None


def example1_get_quote():
    """示例1: 获取实时行情"""
    print("\n" + "="*50)
    print("示例1: 获取实时行情")
    print("="*50)
    
    api = StockAPI()
    quote = api.get_quote("000001")
    
    if quote and len(quote) > 0:
        q = quote[0]
        last_price = q['K']['Close'] / 1000  # 转为元
        open_price = q['K']['Open'] / 1000
        high_price = q['K']['High'] / 1000
        low_price = q['K']['Low'] / 1000
        
        print(f"股票代码: {q['Code']}")
        print(f"最新价: {last_price:.2f}元")
        print(f"开盘价: {open_price:.2f}元")
        print(f"最高价: {high_price:.2f}元")
        print(f"最低价: {low_price:.2f}元")
        print(f"成交量: {q['TotalHand']}手")
        print(f"成交额: {q['Amount']/1000:.2f}元")
        
        print("\n买五档:")
        for i, level in enumerate(q['BuyLevel']):
            price = level['Price'] / 1000
            volume = level['Number'] / 100
            print(f"  买{i+1}: {price:.2f}元  {volume:.0f}手")
        
        print("\n卖五档:")
        for i, level in enumerate(q['SellLevel']):
            price = level['Price'] / 1000
            volume = level['Number'] / 100
            print(f"  卖{i+1}: {price:.2f}元  {volume:.0f}手")


def example2_get_kline():
    """示例2: 获取K线数据并分析"""
    print("\n" + "="*50)
    print("示例2: 获取K线数据")
    print("="*50)
    
    api = StockAPI()
    klines = api.get_kline("000001", "day")
    
    if klines and len(klines) > 0:
        print(f"获取到 {len(klines)} 条日K线数据（日/周/月为前复权）")
        
        # 显示最近5天的数据
        print("\n最近5天K线:")
        for k in klines[:5]:
            date = k['Time'][:10]
            open_p = k['Open'] / 1000
            close_p = k['Close'] / 1000
            high_p = k['High'] / 1000
            low_p = k['Low'] / 1000
            volume = k['Volume']
            
            change = close_p - open_p
            change_pct = (change / open_p * 100) if open_p > 0 else 0
            
            print(f"{date}: 开{open_p:.2f} 收{close_p:.2f} "
                  f"高{high_p:.2f} 低{low_p:.2f} "
                  f"量{volume}手 {change_pct:+.2f}%")
        
        # 计算简单移动平均线
        if len(klines) >= 5:
            ma5 = sum([k['Close'] for k in klines[:5]]) / 5 / 1000
            print(f"\nMA5: {ma5:.2f}元")


def example3_search_stock():
    """示例3: 搜索股票"""
    print("\n" + "="*50)
    print("示例3: 搜索股票")
    print("="*50)
    
    api = StockAPI()
    results = api.search("平安")
    
    if results:
        print(f"找到 {len(results)} 只股票:")
        for stock in results:
            print(f"  {stock['code']} ({stock.get('exchange','')}) - {stock['name']}")


def example4_batch_quote():
    """示例4: 批量获取行情"""
    print("\n" + "="*50)
    print("示例4: 批量获取行情")
    print("="*50)
    
    api = StockAPI()
    codes = ["000001", "600519", "601318"]
    quotes = api.batch_get_quote(codes)
    
    if quotes:
        print("批量行情数据:")
        for q in quotes:
            code = q['Code']
            price = q['K']['Close'] / 1000
            volume = q['TotalHand']
            print(f"  {code}: {price:.2f}元, 成交量{volume}手")


def example5_market_analysis():
    """示例5: 市场分析（涨跌统计）"""
    print("\n" + "="*50)
    print("示例5: 市场分析")
    print("="*50)
    
    api = StockAPI()
    
    # 获取部分股票进行分析
    all_codes = api.get_all_codes('sh')
    if all_codes:
        print(f"上海市场共 {all_codes['exchanges']['sh']} 只股票")
        
        # 随机取10只股票分析
        sample_codes = [c['code'] for c in all_codes['codes'][:10]]
        quotes = api.batch_get_quote(sample_codes)
        
        if quotes:
            up_count = 0
            down_count = 0
            flat_count = 0
            
            for q in quotes:
                last = q['K']['Last']
                close = q['K']['Close']
                
                if close > last:
                    up_count += 1
                elif close < last:
                    down_count += 1
                else:
                    flat_count += 1
            
            print(f"\n样本分析（{len(quotes)}只）:")
            print(f"  上涨: {up_count}只")
            print(f"  下跌: {down_count}只")
            print(f"  平盘: {flat_count}只")


def example6_technical_analysis():
    """示例6: 技术分析示例"""
    print("\n" + "="*50)
    print("示例6: 技术分析")
    print("="*50)
    
    api = StockAPI()
    klines = api.get_kline("000001", "day")
    
    if klines and len(klines) >= 20:
        # 计算MA5, MA10, MA20
        closes = [k['Close'] / 1000 for k in klines]
        
        ma5 = sum(closes[:5]) / 5
        ma10 = sum(closes[:10]) / 10
        ma20 = sum(closes[:20]) / 20
        
        current_price = closes[0]
        
        print("技术指标:")
        print(f"  当前价: {current_price:.2f}元")
        print(f"  MA5:   {ma5:.2f}元")
        print(f"  MA10:  {ma10:.2f}元")
        print(f"  MA20:  {ma20:.2f}元")
        
        # 简单趋势判断
        if ma5 > ma10 > ma20:
            print("\n趋势判断: 多头排列 📈")
        elif ma5 < ma10 < ma20:
            print("\n趋势判断: 空头排列 📉")
        else:
            print("\n趋势判断: 震荡盘整 ➡️")


def example7_realtime_monitor():
    """示例7: 实时监控（模拟）"""
    print("\n" + "="*50)
    print("示例7: 实时监控")
    print("="*50)
    
    api = StockAPI()
    watchlist = ["000001", "600519", "601318"]
    
    print(f"监控股票: {', '.join(watchlist)}")
    print("\n实时行情（刷新一次）:")
    
    quotes = api.batch_get_quote(watchlist)
    if quotes:
        print(f"{'代码':<10} {'最新价':<10} {'涨跌幅':<10} {'成交量'}")
        print("-" * 50)
        
        for q in quotes:
            code = q['Code']
            last = q['K']['Last'] / 1000
            close = q['K']['Close'] / 1000
            volume = q['TotalHand']
            
            change_pct = ((close - last) / last * 100) if last > 0 else 0
            
            print(f"{code:<10} {close:<10.2f} {change_pct:+.2f}%  {volume:>10}手")


def example8_data_tasks():
    """示例8: 批量入库任务管理"""
    print("\n" + "="*50)
    print("示例8: 批量入库任务")
    print("="*50)
    
    api = StockAPI()
    today = datetime.now().strftime("%Y-%m-%d")
    
    try:
        kline_task = api.create_pull_kline_task(
            codes=["000001", "600519"],
            tables=["day", "week"],
            limit=2,
            start_date=today
        )
        print(f"创建K线入库任务成功，任务ID: {kline_task}")
    except Exception as err:
        print(f"创建K线任务失败: {err}")
        kline_task = None
    
    try:
        trade_task = api.create_pull_trade_task("000001", start_year=2020)
        print(f"创建分时成交任务成功，任务ID: {trade_task}")
    except Exception as err:
        print(f"创建成交任务失败: {err}")
        trade_task = None
    
    tasks = api.list_tasks()
    print(f"\n当前任务总数: {len(tasks)}")
    for task in tasks:
        print(f"  - {task['id']} [{task['type']}] 状态: {task['status']}")
    
    if kline_task:
        detail = api.get_task(kline_task)
        if detail:
            print(f"\nK线任务详情: 状态={detail['status']} 开始于 {detail['started_at']}")


def example9_data_services():
    """示例9: 新增数据服务接口"""
    print("\n" + "="*50)
    print("示例9: 数据服务接口")
    print("="*50)

    api = StockAPI()

    etfs = api.get_etf_list(limit=5)
    if etfs:
        print(f"ETF样本({etfs['total']}):")
        for item in etfs['list']:
            print(f"  {item['exchange']} {item['code']} - {item['name']}")

    workday_info = api.get_workday(count=1)
    trade_date = None
    if workday_info:
        base = workday_info['date']['numeric']
        if workday_info['is_workday']:
            trade_date = base
        elif workday_info['previous']:
            trade_date = workday_info['previous'][0]['numeric']

    if trade_date:
        history = api.get_trade_history("000001", trade_date, count=100)
        if history and history.get('List'):
            print(f"\n历史分时成交({trade_date}) 返回 {history['Count']} 条，展示前3条：")
            for item in history['List'][:3]:
                print(f"  {item['Time']}  价:{item['Price']/1000:.2f}  量:{item['Volume']}")

        minute_all = api.get_minute_trade_all("000001", trade_date)
        if minute_all:
            print(f"\n全天成交合计: {minute_all.get('Count', 0)} 条记录")

        if workday_info and workday_info['next']:
            next_day = workday_info['next'][0]['iso']
        else:
            next_day = "N/A"
        print(f"\n下一个交易日: {next_day}")
    else:
        print("\n未能确定可用的交易日，请检查交易日接口是否正常。")


def example10_advanced_endpoints():
    """示例10: 高级接口组合"""
    print("\n" + "="*50)
    print("示例10: 高级接口")
    print("="*50)

    api = StockAPI()

    market = api.get_market_count()
    if market:
        print("市场证券数量:")
        for item in market['exchanges']:
            print(f"  {item['exchange']}: {item['count']}")
        print(f"  总计: {market['total']}")

    stocks = api.get_stock_codes(limit=5, prefix=False)
    etfs = api.get_etf_codes(limit=5, prefix=False)
    if stocks:
        print(f"\n股票代码示例: {', '.join(stocks['list'])}")
    if etfs:
        print(f"ETF代码示例: {', '.join(etfs['list'])}")

    kline_all = api.get_kline_all("000001", "day", limit=3)
    if kline_all:
        print("\n日K历史末尾样本:")
        for item in kline_all['list']:
            print(f"  {item['Time']} 收:{item['Close']/1000:.2f}")

    index_all = api.get_index_all("sh000001", "day", limit=3)
    if index_all:
        print("\n上证指数末尾样本:")
        for item in index_all['list']:
            print(f"  {item['Time']} 收:{item['Close']/1000:.2f}")

    trades_full = api.get_trade_history_full("000001", before="20241108", limit=3)
    if trades_full:
        print(f"\n历史成交截取({trades_full['count']}条):")
        for item in trades_full['list']:
            print(f"  {item['Time']} 价:{item['Price']/1000:.2f} 量:{item['Volume']}")

    workdays = api.get_workday_range("2024-11-01", "2024-11-08")
    if workdays:
        print(f"\n交易日范围: {[d['numeric'] for d in workdays['list']]}")

    income = api.get_income("000001", "2024-11-01", days=[5, 10, 20])
    if income:
        print("\n收益区间分析:")
        for item in income['list']:
            print(f"  {item['offset']} 天 -> 涨幅 {item['rise_rate']*100:.2f}% "
                  f"(收盘 {item['current']['close']/1000:.2f} 元)")


def main():
    """主函数"""
    print("""
╔════════════════════════════════════════╗
║   TDX股票数据API使用示例               ║
║   演示所有API接口的使用方法             ║
╚════════════════════════════════════════╝
    """)
    
    try:
        # 运行所有示例
        example1_get_quote()
        example2_get_kline()
        example3_search_stock()
        example4_batch_quote()
        example5_market_analysis()
        example6_technical_analysis()
        example7_realtime_monitor()
        example8_data_tasks()
        example9_data_services()
        example10_advanced_endpoints()
        
        print("\n" + "="*50)
        print("所有示例运行完成！")
        print("="*50)
        
    except requests.exceptions.ConnectionError:
        print("\n❌ 无法连接到API服务器")
        print(f"   请确保服务运行在 {BASE_URL}")
        print("   启动命令: docker-compose up -d")
    except Exception as e:
        print(f"\n❌ 发生错误: {e}")


if __name__ == "__main__":
    main()

