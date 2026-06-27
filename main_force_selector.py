#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
主力选股模块
使用pywencai获取主力资金净流入前100名股票，并进行智能筛选
"""

from numpy.ma import minimum_fill_value
import pandas as pd
import pywencai
from datetime import datetime, timedelta
from typing import Dict, List, Tuple
import time
from utils.pywencai_helper import safe_get

class MainForceStockSelector:
    """主力选股类"""
    
    def __init__(self):
        self.raw_data = None
        self.filtered_stocks = None
    
    def get_main_force_stocks(self, start_date: str = None, days_ago: int = None,
                             min_market_cap: float = None, max_market_cap: float = None) -> Tuple[bool, pd.DataFrame, str]:
        """
        获取主力资金净流入前100名股票
        
        Args:
            start_date: 开始日期，格式如"2025年10月1日"，如果不提供则使用days_ago
            days_ago: 距今多少天
            min_market_cap: 最小市值限制
            max_market_cap: 最大市值限制
            
        Returns:
            (success, dataframe, message)
        """
        try:
            # 如果没有提供开始日期，根据days_ago计算
            if not start_date:
                date_obj = datetime.now() - timedelta(days=days_ago)
                start_date = f"{date_obj.year}年{date_obj.month}月{date_obj.day}日"
            
            print(f"\n{'='*60}")
            print(f"🔍 主力选股 - 数据获取中")
            print(f"{'='*60}")
            print(f"开始日期: {start_date}")
            print(f"目标: 获取主力资金净流入排名前100名股票")
            
            # 构建查询语句 - 使用多个备选方案，所有方案都要求计算区间涨跌幅
            queries = [
                # 方案1: 完整查询（最优）
                f"{start_date}以来主力资金净流入排名，并计算区间涨跌幅，市值{min_market_cap}-{max_market_cap}亿之间，非科创非st，"
                f"所属同花顺行业，总市值，净利润，营收，市盈率，市净率，"
                f"盈利能力评分，成长能力评分，营运能力评分，偿债能力评分，"
                f"现金流评分，资产质量评分，流动性评分，资本充足性评分",
                
                # 方案2: 简化查询
                f"{start_date}以来主力资金净流入，并计算区间涨跌幅，市值{min_market_cap}-{max_market_cap}亿，非科创非st，"
                f"所属同花顺行业，总市值，净利润，营收，市盈率，市净率",
                
                # 方案3: 基础查询
                f"{start_date}以来主力资金净流入排名，并计算区间涨跌幅，市值{min_market_cap}-{max_market_cap}亿，非科创非st，"
                f"所属行业，总市值",
                
                # 方案4: 最简查询
                f"{start_date}以来主力资金净流入前100名，并计算区间涨跌幅，市值{min_market_cap}-{max_market_cap}亿，非st非科创板，所属行业，总市值",
            ]
            
            # 尝试不同的查询方案
            for i, query in enumerate(queries, 1):
                print(f"\n尝试方案 {i}/{len(queries)}...")
                print(f"查询语句: {query[:100]}...")
                
                try:
                    result = safe_get(query=query, loop=True)
                    
                    if result is None:
                        print(f"  ⚠️ 方案{i}返回None，尝试下一个方案")
                        continue
                    
                    # 转换为DataFrame
                    df_result = self._convert_to_dataframe(result)
                    
                    if df_result is None or df_result.empty:
                        print(f"  ⚠️ 方案{i}数据为空，尝试下一个方案")
                        continue
                    
                    # 成功获取数据
                    print(f"  ✅ 方案{i}成功！获取到 {len(df_result)} 只股票")
                    self.raw_data = df_result
                    
                    # 显示获取到的列名
                    print(f"\n获取到的数据字段:")
                    for col in df_result.columns[:15]:  # 只显示前15个字段
                        print(f"  - {col}")
                    if len(df_result.columns) > 15:
                        print(f"  ... 还有 {len(df_result.columns) - 15} 个字段")
                    
                    return True, df_result, f"成功获取{len(df_result)}只股票数据"
                
                except Exception as e:
                    print(f"  ❌ 方案{i}失败: {str(e)}")
                    time.sleep(2)  # 失败后等待2秒再试
                    continue
            
            # 所有方案都失败
            error_msg = "所有查询方案都失败了，请检查网络或稍后重试"
            print(f"\n❌ {error_msg}")
            return False, None, error_msg
        
        except Exception as e:
            error_msg = f"获取主力选股数据失败: {str(e)}"
            print(f"\n❌ {error_msg}")
            return False, None, error_msg
    
    def _convert_to_dataframe(self, result) -> pd.DataFrame:
        """转换问财返回结果为DataFrame"""
        try:
            if isinstance(result, pd.DataFrame):
                return result
            elif isinstance(result, dict):
                # 检查是否有嵌套的tableV1结构
                if 'tableV1' in result:
                    table_data = result['tableV1']
                    if isinstance(table_data, pd.DataFrame):
                        return table_data
                    elif isinstance(table_data, list):
                        return pd.DataFrame(table_data)
                # 直接转换字典
                return pd.DataFrame([result])
            elif isinstance(result, list):
                return pd.DataFrame(result)
            else:
                return None
        except Exception as e:
            print(f"  转换DataFrame失败: {e}")
            return None
    
    def filter_stocks(self, df: pd.DataFrame, 
                     max_range_change: float = None,
                     min_market_cap: float = None,
                     max_market_cap: float = None) -> pd.DataFrame:
        """
        智能筛选股票 - 基于涨跌幅和市值
        
        Args:
            df: 原始股票数据DataFrame
            max_range_change: 最大涨跌幅限制
            min_market_cap: 最小市值限制
            max_market_cap: 最大市值限制
            
        Returns:
            筛选后的DataFrame
        """
        if df is None or df.empty:
            return df
        
        print(f"\n{'='*60}")
        print(f"🔍 智能筛选中...")
        print(f"{'='*60}")
        print(f"筛选条件:")
        print(f"  - 区间涨跌幅 < {max_range_change}%")
        print(f"  - 市值范围: {min_market_cap}-{max_market_cap}亿")
        
        original_count = len(df)
        filtered_df = df.copy()
        
        # 1. 筛选区间涨跌幅（智能匹配列名）
        # 优先精确匹配，按优先级查找
        interval_pct_col = None
        possible_interval_pct_names = [
            '区间涨跌幅:前复权', 
            '区间涨跌幅:前复权(%)', 
            '区间涨跌幅(%)', 
            '区间涨跌幅', 
            '涨跌幅:前复权', 
            '涨跌幅:前复权(%)',
            '涨跌幅(%)',
            '涨跌幅'
        ]
        
        # 优先精确匹配
        for name in possible_interval_pct_names:
            for col in df.columns:
                if name in col:
                    interval_pct_col = col
                    break
            if interval_pct_col:
                break
        
        if interval_pct_col:
            print(f"\n使用字段: {interval_pct_col}")
            
            # 转换为数值并筛选
            filtered_df[interval_pct_col] = pd.to_numeric(filtered_df[interval_pct_col], errors='coerce')
            before = len(filtered_df)
            filtered_df = filtered_df[
                (filtered_df[interval_pct_col].notna()) & 
                (filtered_df[interval_pct_col] < max_range_change)
            ]
            print(f"  区间涨跌幅筛选: {before} -> {len(filtered_df)} 只")
        else:
            print(f"  ⚠️ 未找到区间涨跌幅字段，跳过涨跌幅筛选")
            print(f"  可用字段: {list(df.columns[:10])}")
        
        # 2. 筛选市值
        market_cap_cols = [col for col in df.columns if '总市值' in col or '市值' in col]
        if market_cap_cols:
            col_name = market_cap_cols[0]
            print(f"\n使用字段: {col_name}")
            
            # 转换为数值（单位可能是亿或元）
            filtered_df[col_name] = pd.to_numeric(filtered_df[col_name], errors='coerce')
            
            # 判断单位（如果值很大，可能是元）
            max_val = filtered_df[col_name].max()
            if max_val > 100000:  # 大于10万，认为是元
                print(f"  检测到单位为元，转换为亿")
                filtered_df[col_name] = filtered_df[col_name] / 100000000
            
            before = len(filtered_df)
            filtered_df = filtered_df[
                (filtered_df[col_name].notna()) & 
                (filtered_df[col_name] >= min_market_cap) &
                (filtered_df[col_name] <= max_market_cap)
            ]
            print(f"  市值筛选: {before} -> {len(filtered_df)} 只")
        
        # 3. 去除ST股票（额外保险）
        if '股票简称' in filtered_df.columns:
            before = len(filtered_df)
            filtered_df = filtered_df[~filtered_df['股票简称'].str.contains('ST', na=False)]
            if before != len(filtered_df):
                print(f"  ST股票过滤: {before} -> {len(filtered_df)} 只")
        
        print(f"\n筛选完成: {original_count} -> {len(filtered_df)} 只股票")
        
        self.filtered_stocks = filtered_df
        return filtered_df
    
    def get_top_stocks(self, df: pd.DataFrame, top_n: int = None) -> pd.DataFrame:
        """
        获取主力资金净流入前N名股票
        
        Args:
            df: 筛选后的股票数据
            top_n: 返回前N名
            
        Returns:
            前N名股票DataFrame
        """
        if df is None or df.empty:
            return df
        
        # 查找主力资金相关列（智能匹配）
        main_fund_col = None
        main_fund_patterns = [
            '区间主力资金流向',      # 实际列名
            '区间主力资金净流入',
            '主力资金流向',
            '主力资金净流入',
            '主力净流入'
        ]
        for pattern in main_fund_patterns:
            matching = [col for col in df.columns if pattern in col]
            if matching:
                main_fund_col = matching[0]
                break
        
        if main_fund_col:
            print(f"\n使用字段排序: {main_fund_col}")
            
            # 转换为数值并排序
            df[main_fund_col] = pd.to_numeric(df[main_fund_col], errors='coerce')
            top_df = df.nlargest(top_n, main_fund_col)
            
            print(f"获取主力资金净流入前 {len(top_df)} 名")
            return top_df
        else:
            # 如果没有主力资金列，直接返回前N条
            print(f"未找到主力资金列，返回前{top_n}条数据")
            return df.head(top_n)
    
    def format_stock_list_for_analysis(self, df: pd.DataFrame) -> List[Dict]:
        """
        格式化股票列表，准备提交给AI分析师
        
        Args:
            df: 股票数据DataFrame
            
        Returns:
            格式化后的股票列表
        """
        if df is None or df.empty:
            return []
        
        stock_list = []
        
        for idx, row in df.iterrows():
            stock_data = {
                'symbol': row.get('股票代码', 'N/A'),
                'name': row.get('股票简称', 'N/A'),
                'industry': row.get('所属同花顺行业', row.get('所属行业', 'N/A')),
                'market_cap': row.get('总市值[20241209]', row.get('总市值', 'N/A')),
                'range_change': None,
                'main_fund_inflow': None,
                'pe_ratio': row.get('市盈率', 'N/A'),
                'pb_ratio': row.get('市净率', 'N/A'),
                'revenue': row.get('营业收入', row.get('营收', 'N/A')),
                'net_profit': row.get('净利润', 'N/A'),
                'scores': {},
                'raw_data': row.to_dict()
            }
            
            # 提取区间涨跌幅（使用智能匹配）
            interval_pct_col = None
            possible_names = [
                '区间涨跌幅:前复权', '区间涨跌幅:前复权(%)', '区间涨跌幅(%)', 
                '区间涨跌幅', '涨跌幅:前复权', '涨跌幅:前复权(%)', '涨跌幅(%)', '涨跌幅'
            ]
            for name in possible_names:
                for col in df.columns:
                    if name in col:
                        interval_pct_col = col
                        break
                if interval_pct_col:
                    break
            if interval_pct_col:
                stock_data['range_change'] = row.get(interval_pct_col, 'N/A')
            
            # 提取主力资金（智能匹配）
            main_fund_col = None
            main_fund_patterns = [
                '区间主力资金流向', '区间主力资金净流入', 
                '主力资金流向', '主力资金净流入', '主力净流入'
            ]
            for pattern in main_fund_patterns:
                matching = [col for col in df.columns if pattern in col]
                if matching:
                    main_fund_col = matching[0]
                    break
            if main_fund_col:
                stock_data['main_fund_inflow'] = row.get(main_fund_col, 'N/A')
            
            # 提取评分
            score_keywords = ['评分', '能力']
            for col in df.columns:
                if any(keyword in col for keyword in score_keywords):
                    stock_data['scores'][col] = row.get(col, 'N/A')
            
            stock_list.append(stock_data)
        
        return stock_list
    
    def print_stock_summary(self, stock_list: List[Dict]):
        """打印股票摘要信息"""
        print(f"\n{'='*80}")
        print(f"📊 候选股票列表 ({len(stock_list)}只)")
        print(f"{'='*80}")
        print(f"{'序号':<4} {'代码':<8} {'名称':<12} {'行业':<15} {'主力资金':<12} {'涨跌幅':<8}")
        print(f"{'-'*80}")
        
        for i, stock in enumerate(stock_list, 1):
            symbol = stock['symbol']
            name = stock['name'][:10] if isinstance(stock['name'], str) else 'N/A'
            industry = stock['industry'][:13] if isinstance(stock['industry'], str) else 'N/A'
            
            # 格式化主力资金
            main_fund = stock['main_fund_inflow']
            if isinstance(main_fund, (int, float)):
                if abs(main_fund) >= 100000000:  # 大于1亿
                    main_fund_str = f"{main_fund/100000000:.2f}亿"
                else:
                    main_fund_str = f"{main_fund/10000:.2f}万"
            else:
                main_fund_str = 'N/A'
            
            # 格式化涨跌幅
            change = stock['range_change']
            if isinstance(change, (int, float)):
                change_str = f"{change:.2f}%"
            else:
                change_str = 'N/A'
            
            print(f"{i:<4} {symbol:<8} {name:<12} {industry:<15} {main_fund_str:<12} {change_str:<8}")
        
        print(f"{'='*80}\n")

# 全局实例
main_force_selector = MainForceStockSelector()

