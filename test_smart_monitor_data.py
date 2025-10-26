#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
智能盯盘 - 数据获取功能测试脚本

用于验证实时行情数据获取是否正常工作
"""

import logging
import sys

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

def test_data_fetcher():
    """测试数据获取功能"""
    print("\n" + "="*70)
    print("智能盯盘 - 数据获取功能测试")
    print("="*70 + "\n")
    
    try:
        from smart_monitor_data import SmartMonitorDataFetcher
        
        # 创建数据获取器
        fetcher = SmartMonitorDataFetcher()
        print("✅ 数据获取器初始化成功\n")
        
        # 测试股票列表（可以自行修改）
        test_stocks = [
            ('600519', '贵州茅台'),
            ('000001', '平安银行'),
            ('002167', '东方锆业')
        ]
        
        for stock_code, stock_name in test_stocks:
            print(f"\n{'─'*70}")
            print(f"测试股票: {stock_code} ({stock_name})")
            print(f"{'─'*70}")
            
            # 获取实时行情
            quote = fetcher.get_realtime_quote(stock_code)
            
            if quote:
                print(f"\n✅ 数据获取成功:")
                print(f"  📌 股票代码: {quote['code']}")
                print(f"  📌 股票名称: {quote['name']}")
                print(f"  💰 当前价格: ¥{quote['current_price']:.2f}")
                print(f"  📊 涨跌幅: {quote['change_pct']:+.2f}%")
                print(f"  💵 涨跌额: ¥{quote['change_amount']:+.2f}")
                print(f"  📦 成交量: {quote['volume']:.0f}手")
                print(f"  💸 成交额: ¥{quote['amount']/10000:.2f}万")
                print(f"  📈 最高: ¥{quote['high']:.2f}")
                print(f"  📉 最低: ¥{quote['low']:.2f}")
                print(f"  🔓 今开: ¥{quote['open']:.2f}")
                print(f"  🔒 昨收: ¥{quote['pre_close']:.2f}")
                print(f"  🔄 换手率: {quote['turnover_rate']:.2f}%")
                print(f"  ⏰ 更新时间: {quote['update_time']}")
                print(f"  🌐 数据源: {quote['data_source']}")
                
                # 验证数据是否有效（不全为0）
                if quote['current_price'] > 0:
                    print(f"\n  ✅ 数据有效性检查: 通过")
                else:
                    print(f"\n  ⚠️ 数据有效性检查: 价格为0，可能是非交易时间")
            else:
                print(f"\n❌ 获取 {stock_code} 的数据失败")
                return False
        
        print("\n" + "="*70)
        print("✅ 所有测试通过！数据获取功能正常工作")
        print("="*70 + "\n")
        return True
        
    except ImportError as e:
        print(f"❌ 导入模块失败: {e}")
        print("请确保 smart_monitor_data.py 文件存在")
        return False
    except Exception as e:
        print(f"❌ 测试过程中出现错误: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == '__main__':
    print("\n💡 提示：")
    print("  - 此脚本用于测试智能盯盘的数据获取功能")
    print("  - 需要网络连接以访问AKShare API")
    print("  - 如果所有数据都正常显示，说明修复成功")
    print("  - 如果仍然显示0，请检查网络或查看日志\n")
    
    success = test_data_fetcher()
    
    if success:
        print("🎉 恭喜！数据获取功能测试通过，可以正常使用智能盯盘了！\n")
        sys.exit(0)
    else:
        print("⚠️ 测试失败，请查看上方错误信息并联系技术支持\n")
        sys.exit(1)

