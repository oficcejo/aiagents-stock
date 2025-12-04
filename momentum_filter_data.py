#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
一进二策略数据获取模块
获取涨停板股票数据，支持多种数据源
"""

import pandas as pd
import akshare as ak
import pywencai
from datetime import datetime, timedelta
from typing import Dict, List, Tuple, Optional
import time
import numpy as np


class MomentumFilterData:
    """一进二策略数据获取类"""

    def __init__(self):
        self.raw_data = None
        self.limit_up_stocks = None

    def get_limit_up_stocks(self, trade_date: str = None) -> Tuple[bool, pd.DataFrame, str]:
        """
        获取指定日期的涨停板股票（首板）

        Args:
            trade_date: 交易日期，格式"YYYYMMDD"或"YYYY-MM-DD"，默认为最近交易日

        Returns:
            (success, dataframe, message)
        """
        try:
            # 如果没有指定日期，使用最近交易日
            if not trade_date:
                trade_date = datetime.now().strftime("%Y%m%d")

            # 统一日期格式为YYYYMMDD
            trade_date_str = trade_date.replace("-", "")

            print(f"\n{'='*60}")
            print(f"🔍 一进二策略 - 获取涨停板数据")
            print(f"{'='*60}")
            print(f"交易日期: {trade_date_str}")

            # 尝试多种方法获取涨停板数据
            df = None

            # 方法1: 使用问财获取涨停板数据（推荐）
            try:
                df = self._get_limit_up_from_wencai(trade_date_str)
                if df is not None and not df.empty:
                    print(f"✅ 使用问财成功获取 {len(df)} 只涨停股票")
            except Exception as e:
                print(f"⚠️ 问财获取失败: {str(e)}")

            # 方法2: 使用akshare获取涨停板数据（备用）
            if df is None or df.empty:
                try:
                    df = self._get_limit_up_from_akshare(trade_date_str)
                    if df is not None and not df.empty:
                        print(f"✅ 使用akshare成功获取 {len(df)} 只涨停股票")
                except Exception as e:
                    print(f"⚠️ akshare获取失败: {str(e)}")

            if df is None or df.empty:
                return False, None, "未能获取到涨停板数据，请检查日期是否为交易日"

            self.raw_data = df
            return True, df, f"成功获取{len(df)}只涨停股票数据"

        except Exception as e:
            error_msg = f"获取涨停板数据失败: {str(e)}"
            print(f"\n❌ {error_msg}")
            return False, None, error_msg

    def _get_limit_up_from_wencai(self, trade_date: str) -> Optional[pd.DataFrame]:
        """
        使用问财获取涨停板数据

        Args:
            trade_date: 交易日期字符串，格式YYYYMMDD

        Returns:
            DataFrame或None
        """
        try:
            # 转换日期格式为问财可识别的格式
            date_obj = datetime.strptime(trade_date, "%Y%m%d")
            wencai_date = f"{date_obj.year}年{date_obj.month}月{date_obj.day}日"

            # 构建查询语句 - 获取首板涨停股票及相关数据
            queries = [
                # 方案1: 完整查询
                f"{wencai_date}涨停，非st，非科创板，非一字板，"
                f"涨停时间，涨停封单量，炸板次数，所属板块，流通市值，"
                f"昨日成交额，今日成交额，换手率，市盈率，股价，"
                f"连板天数=1",

                # 方案2: 简化查询
                f"{wencai_date}涨停板，排除st，排除科创板，排除一字板，"
                f"涨停时间，封板金额，所属行业，流通市值，股价",

                # 方案3: 基础查询
                f"{wencai_date}涨停股票，非st非科创板，流通市值，股价，所属行业",
            ]

            for i, query in enumerate(queries, 1):
                print(f"  尝试问财方案 {i}/{len(queries)}...")
                try:
                    result = pywencai.get(query=query, loop=True)

                    if result is None:
                        continue

                    df = self._convert_to_dataframe(result)

                    if df is not None and not df.empty:
                        # 数据清洗和标准化
                        df = self._clean_limit_up_data(df)
                        return df

                except Exception as e:
                    print(f"  问财方案{i}失败: {str(e)}")
                    time.sleep(1)
                    continue

            return None

        except Exception as e:
            print(f"问财获取失败: {e}")
            return None

    def _get_limit_up_from_akshare(self, trade_date: str) -> Optional[pd.DataFrame]:
        """
        使用akshare获取涨停板数据

        Args:
            trade_date: 交易日期字符串，格式YYYYMMDD

        Returns:
            DataFrame或None
        """
        try:
            # 转换日期格式
            date_str = f"{trade_date[:4]}-{trade_date[4:6]}-{trade_date[6:]}"

            # 获取涨停板数据
            df = ak.stock_zt_pool_em(date=date_str)

            if df is None or df.empty:
                return None

            # 数据标准化
            df = self._standardize_akshare_data(df)

            return df

        except Exception as e:
            print(f"akshare获取失败: {e}")
            return None

    def _convert_to_dataframe(self, result) -> Optional[pd.DataFrame]:
        """转换问财返回结果为DataFrame"""
        try:
            if isinstance(result, pd.DataFrame):
                return result
            elif isinstance(result, dict):
                if 'tableV1' in result:
                    table_data = result['tableV1']
                    if isinstance(table_data, pd.DataFrame):
                        return table_data
                    elif isinstance(table_data, list):
                        return pd.DataFrame(table_data)
                return pd.DataFrame([result])
            elif isinstance(result, list):
                return pd.DataFrame(result)
            return None
        except Exception as e:
            print(f"转换DataFrame失败: {e}")
            return None

    def _clean_limit_up_data(self, df: pd.DataFrame) -> pd.DataFrame:
        """清洗和标准化涨停板数据"""
        try:
            # 标准化列名（问财返回的列名可能不同）
            column_mapping = {
                '股票代码': 'code',
                '代码': 'code',
                '股票简称': 'name',
                '名称': 'name',
                '最新价': 'price',
                '现价': 'price',
                '涨停价': 'limit_price',
                '涨跌幅': 'change_pct',
                '涨跌幅%': 'change_pct',
                '涨停时间': 'limit_time',
                '首次涨停时间': 'limit_time',
                '封板金额': 'seal_amount',
                '涨停封单量': 'seal_amount',
                '炸板次数': 'broken_times',
                '打开次数': 'broken_times',
                '流通市值': 'circulation_market_cap',
                '流通市值(元)': 'circulation_market_cap',
                '总市值': 'total_market_cap',
                '所属板块': 'sector',
                '所属行业': 'sector',
                '行业': 'sector',
                '换手率': 'turnover_rate',
                '换手率%': 'turnover_rate',
                '昨日成交额': 'yesterday_volume',
                '今日成交额': 'today_volume',
                '成交额': 'today_volume',
                '市盈率': 'pe_ratio',
                '市盈率(动态)': 'pe_ratio',
                '连板天数': 'continuous_limit',
            }

            # 重命名列
            for old_name, new_name in column_mapping.items():
                if old_name in df.columns:
                    df = df.rename(columns={old_name: new_name})

            # 确保必要的列存在
            required_columns = ['code', 'name']
            for col in required_columns:
                if col not in df.columns:
                    print(f"⚠️ 缺少必要列: {col}")

            # 数据类型转换
            numeric_columns = ['price', 'change_pct', 'seal_amount', 'circulation_market_cap',
                             'total_market_cap', 'turnover_rate', 'pe_ratio', 'broken_times']

            for col in numeric_columns:
                if col in df.columns:
                    df[col] = pd.to_numeric(df[col], errors='coerce')

            # 处理市值单位（统一为亿元）
            if 'circulation_market_cap' in df.columns:
                # 如果是元为单位，转换为亿元
                max_val = df['circulation_market_cap'].max()
                if max_val > 10000:  # 假设超过10000的是元为单位
                    df['circulation_market_cap'] = df['circulation_market_cap'] / 100000000

            if 'total_market_cap' in df.columns:
                max_val = df['total_market_cap'].max()
                if max_val > 10000:
                    df['total_market_cap'] = df['total_market_cap'] / 100000000

            return df

        except Exception as e:
            print(f"数据清洗失败: {e}")
            return df

    def _standardize_akshare_data(self, df: pd.DataFrame) -> pd.DataFrame:
        """标准化akshare数据格式"""
        try:
            # akshare涨停板数据的列名映射
            column_mapping = {
                '代码': 'code',
                '名称': 'name',
                '涨跌幅': 'change_pct',
                '最新价': 'price',
                '涨停价': 'limit_price',
                '成交额': 'today_volume',
                '流通市值': 'circulation_market_cap',
                '总市值': 'total_market_cap',
                '换手率': 'turnover_rate',
                '封板资金': 'seal_amount',
                '首次封板时间': 'limit_time',
                '最后封板时间': 'last_limit_time',
                '炸板次数': 'broken_times',
                '涨停统计': 'limit_statistics',
            }

            # 重命名列
            for old_name, new_name in column_mapping.items():
                if old_name in df.columns:
                    df = df.rename(columns={old_name: new_name})

            # 数据类型转换
            numeric_columns = ['price', 'change_pct', 'seal_amount', 'circulation_market_cap',
                             'total_market_cap', 'turnover_rate', 'broken_times']

            for col in numeric_columns:
                if col in df.columns:
                    df[col] = pd.to_numeric(df[col], errors='coerce')

            # 处理市值单位
            if 'circulation_market_cap' in df.columns:
                max_val = df['circulation_market_cap'].max()
                if max_val > 10000:
                    df['circulation_market_cap'] = df['circulation_market_cap'] / 100000000

            if 'total_market_cap' in df.columns:
                max_val = df['total_market_cap'].max()
                if max_val > 10000:
                    df['total_market_cap'] = df['total_market_cap'] / 100000000

            return df

        except Exception as e:
            print(f"akshare数据标准化失败: {e}")
            return df

    def get_stock_historical_data(self, code: str, days: int = 60) -> Optional[pd.DataFrame]:
        """
        获取个股历史数据

        Args:
            code: 股票代码
            days: 获取天数

        Returns:
            DataFrame或None
        """
        try:
            # 计算开始日期
            end_date = datetime.now()
            start_date = end_date - timedelta(days=days)

            start_str = start_date.strftime("%Y%m%d")
            end_str = end_date.strftime("%Y%m%d")

            # 使用akshare获取历史数据
            df = ak.stock_zh_a_hist(symbol=code, period="daily",
                                   start_date=start_str, end_date=end_str, adjust="qfq")

            return df

        except Exception as e:
            print(f"获取{code}历史数据失败: {e}")
            return None

    def get_stock_basic_info(self, code: str) -> Dict:
        """
        获取股票基本信息

        Args:
            code: 股票代码

        Returns:
            字典格式的基本信息
        """
        try:
            # 使用akshare获取个股信息
            info = ak.stock_individual_info_em(symbol=code)

            if info is None or info.empty:
                return {}

            # 转换为字典
            info_dict = {}
            for _, row in info.iterrows():
                key = row.get('item', '')
                value = row.get('value', '')
                info_dict[key] = value

            return info_dict

        except Exception as e:
            print(f"获取{code}基本信息失败: {e}")
            return {}
