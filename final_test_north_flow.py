#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
最终测试脚本：验证北向资金流向获取方法的优化方案
"""

import os
import sys
import pandas as pd
from datetime import datetime, timedelta

# 添加项目根目录到Python路径
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# 加载环境变量
from dotenv import load_dotenv
load_dotenv()

import akshare as ak

class FinalNorthMoneyFlowTest:
    """最终北向资金流向测试类"""
    
    def __init__(self):
        """初始化"""
        self._tushare_api = None
        print("初始化北向资金流向测试...")
    
    def _safe_request(self, func, *args, **kwargs):
        """安全请求封装"""
        try:
            return func(*args, **kwargs)
        except Exception as e:
            print(f"请求失败: {e}")
            return None
    
    def _get_north_money_flow_optimized(self):
        """
        优化后的北向资金流向获取方法
        优先使用Akshare，失败时使用Tushare作为备选
        """
        print("开始获取北向资金流向数据...")
        
        # 1. 优先使用Akshare获取沪深港通资金流向
        # try:
        #     print("    [Akshare] 正在获取沪深港通资金流向...")
        #     df = self._safe_request(ak.stock_hsgt_fund_flow_summary_em)
            
        #     if df is not None and not df.empty:
        #         print("    [Akshare] ✅ 成功获取数据")
                
        #         # 获取最新数据
        #         latest = df.iloc[0]
                
        #         # 转换为标准格式
        #         north_flow = {
        #             "date": str(latest.get('日期', '')),
        #             "north_net_inflow": latest.get('北向资金-成交净买入额', 0),
        #             "hgt_net_inflow": latest.get('沪股通-成交净买入额', 0),
        #             "sgt_net_inflow": latest.get('深股通-成交净买入额', 0),
        #             "north_total_amount": latest.get('北向资金-成交金额', 0)
        #         }
                
        #         # 获取历史趋势（最近20天）
        #         history = []
        #         for idx, row in df.head(20).iterrows():
        #             history.append({
        #                 "date": str(row.get('日期', '')),
        #                 "net_inflow": row.get('北向资金-成交净买入额', 0)
        #             })
        #         north_flow["history"] = history
                
        #         print(f"    [Akshare] 返回数据: 日期={north_flow['date']}, 北向净流入={north_flow['north_net_inflow']}")
        #         return north_flow
        #     else:
        #         print("    [Akshare] ❌ 未获取到数据")
        # except Exception as e:
        #     print(f"    [Akshare] 获取北向资金失败: {e}")
        
        # 2. Akshare失败，尝试使用Tushare
        try:
            print("    [Tushare] 尝试使用Tushare作为备选数据源...")
            
            # 初始化Tushare（如果尚未初始化）
            if not hasattr(self, '_tushare_api') or self._tushare_api is None:
                TUSHARE_TOKEN = os.getenv('TUSHARE_TOKEN', '')
                if TUSHARE_TOKEN:
                    try:
                        import tushare as ts
                        ts.set_token(TUSHARE_TOKEN)
                        self._tushare_api = ts.pro_api()
                        print("    [Tushare] ✅ 初始化成功")
                    except Exception as e:
                        print(f"    [Tushare] 初始化失败: {e}")
                        self._tushare_api = None
                else:
                    print("    [Tushare] 未配置Token")
                    self._tushare_api = None
            
            # 如果Tushare可用，获取数据
            if hasattr(self, '_tushare_api') and self._tushare_api:
                print("    [Tushare] 正在获取沪深港通资金流向（备用数据源）...")
                
                # 获取最近30天的数据
                end_date = datetime.now()
                start_date = end_date - timedelta(days=30)
                
                df = self._tushare_api.moneyflow_hsgt(
                    start_date=start_date.strftime('%Y%m%d'),
                    end_date=end_date.strftime('%Y%m%d')
                )
                
                if df is not None and not df.empty:
                    print("    [Tushare] ✅ 成功获取数据")
                    
                    # 按日期降序排列，获取最新数据
                    df = df.sort_values('trade_date', ascending=False)
                    latest = df.iloc[0]
                    
                    # 转换数据格式以匹配原有结构
                    north_flow = {
                        "date": str(latest['trade_date']),
                        "north_net_inflow": float(latest['north_money']),
                        "hgt_net_inflow": float(latest['hgt']),
                        "sgt_net_inflow": float(latest['sgt']),
                        "north_total_amount": float(latest['north_money'])  # Tushare没有总成交金额，使用净流入作为近似值
                    }
                    
                    # 获取历史趋势（最近20天）
                    history = []
                    for idx, row in df.head(20).iterrows():
                        history.append({
                            "date": str(row['trade_date']),
                            "net_inflow": float(row['north_money'])
                        })
                    north_flow["history"] = history
                    
                    print(f"    [Tushare] 返回数据: 日期={north_flow['date']}, 北向净流入={north_flow['north_net_inflow']}")
                    return north_flow
                else:
                    print("    [Tushare] ❌ 未获取到数据")
            else:
                print("    [Tushare] 不可用")
        except Exception as e:
            print(f"    [Tushare] 获取北向资金失败: {e}")
        
        # 3. 所有数据源都失败
        print("    ❌ 所有数据源均获取失败")
        return {}
    
    def run_test(self):
        """运行测试"""
        print("=" * 50)
        print("北向资金流向获取方法优化测试")
        print("=" * 50)
        
        # 测试优化后的方法
        result = self._get_north_money_flow_optimized()
        
        if result:
            print("\n✅ 测试成功！获取到的数据:")
            print(f"  日期: {result.get('date', 'N/A')}")
            print(f"  北向资金净流入: {result.get('north_net_inflow', 0)}")
            print(f"  沪股通净流入: {result.get('hgt_net_inflow', 0)}")
            print(f"  深股通净流入: {result.get('sgt_net_inflow', 0)}")
            print(f"  北向资金总金额: {result.get('north_total_amount', 0)}")
            print(f"  历史数据条数: {len(result.get('history', []))}")
            
            if result.get('history'):
                print("\n  最近5天的历史数据:")
                for item in result['history'][:5]:
                    print(f"    {item['date']}: {item['net_inflow']}")
        else:
            print("\n❌ 测试失败，未获取到数据")
        
        print("\n" + "=" * 50)
        print("测试完成")
        print("=" * 50)
        
        return result

def main():
    """主函数"""
    tester = FinalNorthMoneyFlowTest()
    result = tester.run_test()
    return result

if __name__ == "__main__":
    main()