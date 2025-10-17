"""
智瞰龙虎数据采集模块
使用StockAPI获取龙虎榜数据
"""

import requests
import pandas as pd
from datetime import datetime, timedelta
import time
import warnings

warnings.filterwarnings('ignore')


class LonghubangDataFetcher:
    """龙虎榜数据获取类"""
    
    def __init__(self, api_key=None):
        """
        初始化数据获取器
        
        Args:
            api_key: StockAPI的API密钥（可选，普通请求每日免费1000次）
        """
        print("[智瞰龙虎] 龙虎榜数据获取器初始化...")
        self.base_url = "https://www.stockapi.com.cn/v1"
        self.api_key = api_key
        self.max_retries = 3  # 最大重试次数
        self.retry_delay = 2  # 重试延迟（秒）
        self.request_delay = 0.025  # 请求间隔（秒），40次/秒 = 0.025秒/次
    
    def _safe_request(self, url, params=None):
        """
        安全的HTTP请求，包含重试机制
        
        Args:
            url: 请求URL
            params: 请求参数
            
        Returns:
            dict: 响应数据
        """
        for attempt in range(self.max_retries):
            try:
                response = requests.get(url, params=params, timeout=10)
                
                # 添加请求延迟，遵守40次/秒的限制
                time.sleep(self.request_delay)
                
                if response.status_code == 200:
                    data = response.json()
                    if data.get('code') == 20000:
                        return data
                    else:
                        print(f"    API返回错误: {data.get('msg', '未知错误')}")
                        return None
                else:
                    print(f"    HTTP错误: {response.status_code}")
                    
            except Exception as e:
                if attempt < self.max_retries - 1:
                    print(f"    请求失败，{self.retry_delay}秒后重试... (尝试 {attempt + 1}/{self.max_retries})")
                    time.sleep(self.retry_delay)
                else:
                    print(f"    请求失败，已达最大重试次数: {e}")
                    return None
        
        return None
    
    def get_longhubang_data(self, date):
        """
        获取指定日期的龙虎榜数据
        
        Args:
            date: 日期，格式为 YYYY-MM-DD，如 "2023-03-21"
            
        Returns:
            dict: 龙虎榜数据
        """
        print(f"[智瞰龙虎] 获取 {date} 的龙虎榜数据...")
        
        url = f"{self.base_url}/youzi/all"
        params = {'date': date}
        
        result = self._safe_request(url, params)
        
        if result and result.get('data'):
            print(f"    ✓ 成功获取 {len(result['data'])} 条龙虎榜记录")
            return result
        else:
            print(f"    ✗ 未获取到数据")
            return None
    
    def get_longhubang_data_range(self, start_date, end_date):
        """
        获取日期范围内的龙虎榜数据
        
        Args:
            start_date: 开始日期，格式为 YYYY-MM-DD
            end_date: 结束日期，格式为 YYYY-MM-DD
            
        Returns:
            list: 龙虎榜数据列表
        """
        print(f"[智瞰龙虎] 获取 {start_date} 至 {end_date} 的龙虎榜数据...")
        
        all_data = []
        
        # 转换日期
        current_date = datetime.strptime(start_date, '%Y-%m-%d')
        end_date_obj = datetime.strptime(end_date, '%Y-%m-%d')
        
        while current_date <= end_date_obj:
            date_str = current_date.strftime('%Y-%m-%d')
            
            # 跳过周末
            if current_date.weekday() < 5:  # 0-4表示周一到周五
                result = self.get_longhubang_data(date_str)
                if result and result.get('data'):
                    all_data.extend(result['data'])
            
            # 下一天
            current_date += timedelta(days=1)
        
        print(f"[智瞰龙虎] ✓ 共获取 {len(all_data)} 条记录")
        return all_data
    
    def get_recent_days_data(self, days=5):
        """
        获取最近N个交易日的龙虎榜数据
        
        Args:
            days: 天数（默认5天）
            
        Returns:
            list: 龙虎榜数据列表
        """
        end_date = datetime.now()
        start_date = end_date - timedelta(days=days * 2)  # 乘以2以确保包含足够的交易日
        
        return self.get_longhubang_data_range(
            start_date.strftime('%Y-%m-%d'),
            end_date.strftime('%Y-%m-%d')
        )
    
    def parse_to_dataframe(self, data_list):
        """
        将龙虎榜数据转换为DataFrame
        
        Args:
            data_list: 龙虎榜数据列表
            
        Returns:
            pd.DataFrame: 数据框
        """
        if not data_list:
            return pd.DataFrame()
        
        df = pd.DataFrame(data_list)
        
        # 重命名列
        column_mapping = {
            'yzmc': '游资名称',
            'yyb': '营业部',
            'sblx': '榜单类型',
            'gpdm': '股票代码',
            'gpmc': '股票名称',
            'mrje': '买入金额',
            'mcje': '卖出金额',
            'jlrje': '净流入金额',
            'rq': '日期',
            'gl': '概念'
        }
        
        df = df.rename(columns=column_mapping)
        
        # 转换数据类型
        numeric_columns = ['买入金额', '卖出金额', '净流入金额']
        for col in numeric_columns:
            if col in df.columns:
                df[col] = pd.to_numeric(df[col], errors='coerce')
        
        # 排序
        if '净流入金额' in df.columns:
            df = df.sort_values('净流入金额', ascending=False)
        
        return df
    
    def analyze_data_summary(self, data_list):
        """
        分析龙虎榜数据，生成摘要统计
        
        Args:
            data_list: 龙虎榜数据列表
            
        Returns:
            dict: 统计摘要
        """
        if not data_list:
            return {}
        
        df = self.parse_to_dataframe(data_list)
        
        summary = {
            'total_records': len(df),
            'total_stocks': df['股票代码'].nunique() if '股票代码' in df.columns else 0,
            'total_youzi': df['游资名称'].nunique() if '游资名称' in df.columns else 0,
            'total_buy_amount': df['买入金额'].sum() if '买入金额' in df.columns else 0,
            'total_sell_amount': df['卖出金额'].sum() if '卖出金额' in df.columns else 0,
            'total_net_inflow': df['净流入金额'].sum() if '净流入金额' in df.columns else 0,
        }
        
        # Top游资排名
        if '游资名称' in df.columns and '净流入金额' in df.columns:
            top_youzi = df.groupby('游资名称')['净流入金额'].sum().sort_values(ascending=False)
            summary['top_youzi'] = top_youzi.head(10).to_dict()
        
        # Top股票排名
        if '股票代码' in df.columns and '净流入金额' in df.columns:
            top_stocks = df.groupby(['股票代码', '股票名称'])['净流入金额'].sum().sort_values(ascending=False)
            summary['top_stocks'] = [
                {'code': code, 'name': name, 'net_inflow': amount}
                for (code, name), amount in top_stocks.head(20).items()
            ]
        
        # 热门概念统计
        if '概念' in df.columns:
            all_concepts = []
            for concepts in df['概念'].dropna():
                all_concepts.extend([c.strip() for c in str(concepts).split(',')])
            
            from collections import Counter
            concept_counter = Counter(all_concepts)
            summary['hot_concepts'] = dict(concept_counter.most_common(20))
        
        return summary
    
    def format_data_for_ai(self, data_list, summary=None):
        """
        将龙虎榜数据格式化为适合AI分析的文本格式
        
        Args:
            data_list: 龙虎榜数据列表
            summary: 统计摘要（可选）
            
        Returns:
            str: 格式化的文本
        """
        if not data_list:
            return "暂无龙虎榜数据"
        
        df = self.parse_to_dataframe(data_list)
        
        if summary is None:
            summary = self.analyze_data_summary(data_list)
        
        text_parts = []
        
        # 总体概况
        text_parts.append(f"""
【龙虎榜总体概况】
数据时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
记录总数: {summary.get('total_records', 0)}
涉及股票: {summary.get('total_stocks', 0)} 只
涉及游资: {summary.get('total_youzi', 0)} 个
总买入金额: {summary.get('total_buy_amount', 0):,.2f} 元
总卖出金额: {summary.get('total_sell_amount', 0):,.2f} 元
净流入金额: {summary.get('total_net_inflow', 0):,.2f} 元
""")
        
        # Top游资
        if summary.get('top_youzi'):
            text_parts.append("\n【活跃游资 TOP10】")
            for idx, (name, amount) in enumerate(summary['top_youzi'].items(), 1):
                text_parts.append(f"{idx}. {name}: {amount:,.2f} 元")
        
        # Top股票
        if summary.get('top_stocks'):
            text_parts.append("\n【资金净流入 TOP20股票】")
            for idx, stock in enumerate(summary['top_stocks'], 1):
                text_parts.append(
                    f"{idx}. {stock['name']}({stock['code']}): {stock['net_inflow']:,.2f} 元"
                )
        
        # 热门概念
        if summary.get('hot_concepts'):
            text_parts.append("\n【热门概念 TOP20】")
            for idx, (concept, count) in enumerate(list(summary['hot_concepts'].items())[:20], 1):
                text_parts.append(f"{idx}. {concept}: {count} 次")
        
        # 详细交易记录（前50条）
        text_parts.append("\n【详细交易记录 TOP50】")
        for idx, row in df.head(50).iterrows():
            text_parts.append(
                f"{row.get('游资名称', 'N/A')} | "
                f"{row.get('股票名称', 'N/A')}({row.get('股票代码', 'N/A')}) | "
                f"买入:{row.get('买入金额', 0):,.0f} "
                f"卖出:{row.get('卖出金额', 0):,.0f} "
                f"净流入:{row.get('净流入金额', 0):,.0f} | "
                f"日期:{row.get('日期', 'N/A')}"
            )
        
        return "\n".join(text_parts)


# 测试函数
if __name__ == "__main__":
    print("=" * 60)
    print("测试智瞰龙虎数据采集模块")
    print("=" * 60)
    
    fetcher = LonghubangDataFetcher()
    
    # 测试获取单日数据
    date = (datetime.now() - timedelta(days=1)).strftime('%Y-%m-%d')
    result = fetcher.get_longhubang_data(date)
    
    if result and result.get('data'):
        # 分析数据
        summary = fetcher.analyze_data_summary(result['data'])
        
        print("\n" + "=" * 60)
        print("数据采集成功！")
        print("=" * 60)
        
        # 格式化输出
        formatted_text = fetcher.format_data_for_ai(result['data'], summary)
        print(formatted_text[:2000])  # 显示前2000字符
        print(f"\n... (总长度: {len(formatted_text)} 字符)")
    else:
        print("\n数据采集失败")

