#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
一进二策略筛选引擎
实现一进二策略的智能筛选和评分逻辑
"""

import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from typing import Dict, List, Tuple, Optional
from momentum_filter_data import MomentumFilterData


class MomentumFilterEngine:
    """一进二策略筛选引擎"""

    def __init__(self):
        self.data_fetcher = MomentumFilterData()
        self.filtered_stocks = None
        self.scored_stocks = None

    def filter_first_board_stocks(self,
                                  df: pd.DataFrame,
                                  max_price: float = 30.0,
                                  max_market_cap: float = 100.0,
                                  exclude_sh: bool = True,
                                  exclude_cyb: bool = True,
                                  exclude_one_word: bool = True) -> pd.DataFrame:
        """
        筛选符合一进二条件的首板股票

        Args:
            df: 原始涨停板数据
            max_price: 最大股价（元）
            max_market_cap: 最大流通市值（亿元）
            exclude_sh: 是否排除沪市股票
            exclude_cyb: 是否排除创业板（300开头）
            exclude_one_word: 是否排除一字板

        Returns:
            筛选后的DataFrame
        """
        try:
            print(f"\n{'='*60}")
            print(f"📊 一进二策略 - 首板筛选")
            print(f"{'='*60}")
            print(f"原始涨停股票数量: {len(df)}")

            filtered_df = df.copy()

            # 1. 股价筛选
            if 'price' in filtered_df.columns:
                before_count = len(filtered_df)
                filtered_df = filtered_df[filtered_df['price'] <= max_price]
                print(f"✓ 股价≤{max_price}元: 剩余 {len(filtered_df)} 只 (过滤 {before_count - len(filtered_df)} 只)")

            # 2. 市值筛选
            if 'circulation_market_cap' in filtered_df.columns:
                before_count = len(filtered_df)
                filtered_df = filtered_df[filtered_df['circulation_market_cap'] <= max_market_cap]
                print(f"✓ 流通市值≤{max_market_cap}亿: 剩余 {len(filtered_df)} 只 (过滤 {before_count - len(filtered_df)} 只)")

            # 3. 排除沪市股票（60开头）
            if exclude_sh and 'code' in filtered_df.columns:
                before_count = len(filtered_df)
                filtered_df = filtered_df[~filtered_df['code'].astype(str).str.startswith('6')]
                print(f"✓ 排除沪市股票: 剩余 {len(filtered_df)} 只 (过滤 {before_count - len(filtered_df)} 只)")

            # 4. 排除创业板（300开头）
            if exclude_cyb and 'code' in filtered_df.columns:
                before_count = len(filtered_df)
                filtered_df = filtered_df[~filtered_df['code'].astype(str).str.startswith('300')]
                print(f"✓ 排除创业板: 剩余 {len(filtered_df)} 只 (过滤 {before_count - len(filtered_df)} 只)")

            # 5. 排除一字板（没有换手或换手率极低）
            if exclude_one_word and 'turnover_rate' in filtered_df.columns:
                before_count = len(filtered_df)
                # 换手率低于0.5%的认为是一字板
                filtered_df = filtered_df[
                    (filtered_df['turnover_rate'].isna()) |
                    (filtered_df['turnover_rate'] > 0.5)
                ]
                print(f"✓ 排除一字板: 剩余 {len(filtered_df)} 只 (过滤 {before_count - len(filtered_df)} 只)")

            # 6. 排除ST股票
            if 'name' in filtered_df.columns:
                before_count = len(filtered_df)
                filtered_df = filtered_df[~filtered_df['name'].str.contains('ST', na=False)]
                print(f"✓ 排除ST股票: 剩余 {len(filtered_df)} 只 (过滤 {before_count - len(filtered_df)} 只)")

            print(f"\n最终筛选结果: {len(filtered_df)} 只股票")
            self.filtered_stocks = filtered_df

            return filtered_df

        except Exception as e:
            print(f"❌ 筛选失败: {str(e)}")
            return df

    def score_stocks(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        对筛选后的股票进行评分

        评分维度：
        1. 涨停时间（越早越好）- 30分
        2. 封单强度（封单金额/流通市值）- 25分
        3. 炸板次数（越少越好）- 20分
        4. 换手率（适中为好）- 15分
        5. 市值大小（越小越好）- 10分

        Args:
            df: 筛选后的股票数据

        Returns:
            带有评分的DataFrame
        """
        try:
            print(f"\n{'='*60}")
            print(f"⭐ 一进二策略 - 股票评分")
            print(f"{'='*60}")

            scored_df = df.copy()
            scored_df['score'] = 0.0

            # 1. 涨停时间评分（30分）
            if 'limit_time' in scored_df.columns:
                scored_df['time_score'] = self._score_limit_time(scored_df['limit_time'])
                print(f"✓ 涨停时间评分完成")
            else:
                scored_df['time_score'] = 15.0  # 默认中等分

            # 2. 封单强度评分（25分）
            if 'seal_amount' in scored_df.columns and 'circulation_market_cap' in scored_df.columns:
                scored_df['seal_score'] = self._score_seal_strength(
                    scored_df['seal_amount'],
                    scored_df['circulation_market_cap']
                )
                print(f"✓ 封单强度评分完成")
            else:
                scored_df['seal_score'] = 12.5  # 默认中等分

            # 3. 炸板次数评分（20分）
            if 'broken_times' in scored_df.columns:
                scored_df['broken_score'] = self._score_broken_times(scored_df['broken_times'])
                print(f"✓ 炸板次数评分完成")
            else:
                scored_df['broken_score'] = 10.0  # 默认中等分

            # 4. 换手率评分（15分）
            if 'turnover_rate' in scored_df.columns:
                scored_df['turnover_score'] = self._score_turnover_rate(scored_df['turnover_rate'])
                print(f"✓ 换手率评分完成")
            else:
                scored_df['turnover_score'] = 7.5  # 默认中等分

            # 5. 市值评分（10分）
            if 'circulation_market_cap' in scored_df.columns:
                scored_df['cap_score'] = self._score_market_cap(scored_df['circulation_market_cap'])
                print(f"✓ 市值评分完成")
            else:
                scored_df['cap_score'] = 5.0  # 默认中等分

            # 计算总分
            scored_df['total_score'] = (
                scored_df['time_score'] +
                scored_df['seal_score'] +
                scored_df['broken_score'] +
                scored_df['turnover_score'] +
                scored_df['cap_score']
            )

            # 按总分排序
            scored_df = scored_df.sort_values('total_score', ascending=False)

            print(f"\n✅ 评分完成，最高分: {scored_df['total_score'].max():.1f}，最低分: {scored_df['total_score'].min():.1f}")

            self.scored_stocks = scored_df

            return scored_df

        except Exception as e:
            print(f"❌ 评分失败: {str(e)}")
            return df

    def _score_limit_time(self, limit_time_series: pd.Series) -> pd.Series:
        """
        涨停时间评分
        9:30-10:00: 25-30分（最强）
        10:00-11:00: 15-25分
        11:00-14:00: 5-15分
        14:00-15:00: 0-5分（最弱）
        """
        scores = pd.Series(index=limit_time_series.index, dtype=float)

        for idx, time_str in limit_time_series.items():
            if pd.isna(time_str):
                scores[idx] = 15.0  # 默认中等分
                continue

            try:
                # 处理不同的时间格式
                time_str = str(time_str).strip()

                # 尝试解析时间
                if ':' in time_str:
                    # 格式: "09:30:00" 或 "09:30"
                    parts = time_str.split(':')
                    hour = int(parts[0])
                    minute = int(parts[1])
                elif len(time_str) >= 4:
                    # 格式: "0930" 或 "093000"
                    hour = int(time_str[:2])
                    minute = int(time_str[2:4])
                else:
                    scores[idx] = 15.0
                    continue

                # 计算分钟数（从9:30开始）
                minutes_from_start = (hour - 9) * 60 + minute - 30

                if minutes_from_start < 0:
                    minutes_from_start = 0
                elif minutes_from_start > 330:  # 15:00之后
                    minutes_from_start = 330

                # 评分逻辑
                if minutes_from_start <= 30:  # 9:30-10:00
                    scores[idx] = 30.0 - (minutes_from_start / 30) * 5  # 25-30分
                elif minutes_from_start <= 90:  # 10:00-11:00
                    scores[idx] = 25.0 - ((minutes_from_start - 30) / 60) * 10  # 15-25分
                elif minutes_from_start <= 270:  # 11:00-14:00
                    scores[idx] = 15.0 - ((minutes_from_start - 90) / 180) * 10  # 5-15分
                else:  # 14:00-15:00
                    scores[idx] = 5.0 - ((minutes_from_start - 270) / 60) * 5  # 0-5分

            except:
                scores[idx] = 15.0  # 解析失败，给默认分

        return scores

    def _score_seal_strength(self, seal_amount: pd.Series, market_cap: pd.Series) -> pd.Series:
        """
        封单强度评分
        封单比例 = 封单金额 / 流通市值
        比例越高，分数越高
        """
        scores = pd.Series(index=seal_amount.index, dtype=float)

        for idx in seal_amount.index:
            try:
                seal = seal_amount[idx]
                cap = market_cap[idx]

                if pd.isna(seal) or pd.isna(cap) or cap == 0:
                    scores[idx] = 12.5  # 默认中等分
                    continue

                # 计算封单比例（百分比）
                ratio = (seal / (cap * 100000000)) * 100  # 市值单位是亿

                # 评分逻辑
                if ratio >= 10:  # 封单比例>=10%，非常强
                    scores[idx] = 25.0
                elif ratio >= 5:  # 5-10%，很强
                    scores[idx] = 20.0 + (ratio - 5) / 5 * 5
                elif ratio >= 2:  # 2-5%，较强
                    scores[idx] = 15.0 + (ratio - 2) / 3 * 5
                elif ratio >= 1:  # 1-2%，一般
                    scores[idx] = 10.0 + (ratio - 1) * 5
                else:  # <1%，较弱
                    scores[idx] = ratio * 10

            except:
                scores[idx] = 12.5

        return scores

    def _score_broken_times(self, broken_times: pd.Series) -> pd.Series:
        """
        炸板次数评分
        0次: 20分（最佳）
        1次: 15分
        2次: 10分
        3次及以上: 5分
        """
        scores = pd.Series(index=broken_times.index, dtype=float)

        for idx, times in broken_times.items():
            if pd.isna(times):
                scores[idx] = 20.0  # 假设没有炸板
            elif times == 0:
                scores[idx] = 20.0
            elif times == 1:
                scores[idx] = 15.0
            elif times == 2:
                scores[idx] = 10.0
            else:
                scores[idx] = 5.0

        return scores

    def _score_turnover_rate(self, turnover_rate: pd.Series) -> pd.Series:
        """
        换手率评分
        5-15%: 15分（最佳，充分换手）
        3-5% 或 15-20%: 10-15分（较好）
        1-3% 或 20-30%: 5-10分（一般）
        <1% 或 >30%: 0-5分（不好）
        """
        scores = pd.Series(index=turnover_rate.index, dtype=float)

        for idx, rate in turnover_rate.items():
            if pd.isna(rate):
                scores[idx] = 7.5  # 默认中等分
                continue

            if 5 <= rate <= 15:  # 最佳区间
                scores[idx] = 15.0
            elif 3 <= rate < 5:  # 偏低但可接受
                scores[idx] = 10.0 + (rate - 3) / 2 * 5
            elif 15 < rate <= 20:  # 偏高但可接受
                scores[idx] = 15.0 - (rate - 15) / 5 * 5
            elif 1 <= rate < 3:  # 较低
                scores[idx] = 5.0 + (rate - 1) / 2 * 5
            elif 20 < rate <= 30:  # 较高
                scores[idx] = 10.0 - (rate - 20) / 10 * 5
            elif rate < 1:  # 很低（可能是一字板）
                scores[idx] = rate * 5
            else:  # >30%，换手太大
                scores[idx] = max(0, 5.0 - (rate - 30) / 10)

        return scores

    def _score_market_cap(self, market_cap: pd.Series) -> pd.Series:
        """
        市值评分
        市值越小，分数越高
        <30亿: 10分
        30-50亿: 7-10分
        50-80亿: 5-7分
        >80亿: 0-5分
        """
        scores = pd.Series(index=market_cap.index, dtype=float)

        for idx, cap in market_cap.items():
            if pd.isna(cap):
                scores[idx] = 5.0  # 默认中等分
                continue

            if cap < 30:
                scores[idx] = 10.0
            elif cap < 50:
                scores[idx] = 10.0 - (cap - 30) / 20 * 3
            elif cap < 80:
                scores[idx] = 7.0 - (cap - 50) / 30 * 2
            else:
                scores[idx] = max(0, 5.0 - (cap - 80) / 40 * 5)

        return scores

    def get_top_stocks(self, n: int = 10) -> pd.DataFrame:
        """
        获取评分最高的前N只股票

        Args:
            n: 返回的股票数量

        Returns:
            前N只股票的DataFrame
        """
        if self.scored_stocks is None or self.scored_stocks.empty:
            return pd.DataFrame()

        return self.scored_stocks.head(n)

    def generate_report(self, stock_df: pd.DataFrame) -> str:
        """
        生成选股报告

        Args:
            stock_df: 股票数据

        Returns:
            报告文本
        """
        try:
            if stock_df.empty:
                return "暂无数据"

            report = []
            report.append("="*60)
            report.append("一进二策略选股报告")
            report.append("="*60)
            report.append("")

            for idx, row in stock_df.iterrows():
                code = row.get('code', 'N/A')
                name = row.get('name', 'N/A')
                price = row.get('price', 0)
                score = row.get('total_score', 0)

                report.append(f"【{name}】({code})")
                report.append(f"  股价: {price:.2f}元")
                report.append(f"  综合评分: {score:.1f}/100")

                if 'limit_time' in row:
                    report.append(f"  涨停时间: {row['limit_time']}")

                if 'circulation_market_cap' in row:
                    report.append(f"  流通市值: {row['circulation_market_cap']:.2f}亿")

                if 'turnover_rate' in row:
                    report.append(f"  换手率: {row['turnover_rate']:.2f}%")

                if 'broken_times' in row and not pd.isna(row['broken_times']):
                    report.append(f"  炸板次数: {int(row['broken_times'])}次")

                if 'sector' in row:
                    report.append(f"  所属板块: {row['sector']}")

                report.append("")

            return "\n".join(report)

        except Exception as e:
            return f"生成报告失败: {str(e)}"
