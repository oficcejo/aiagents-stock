"""
测试Tushare数据源是否能满足AI盯盘监控要求
测试内容：
1. 实时行情数据获取
2. 技术指标计算
3. K线图数据获取
"""

import logging
import os
from dotenv import load_dotenv

# 设置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

# 加载环境变量
load_dotenv()

def test_tushare_token():
    """测试Tushare Token是否配置"""
    token = os.getenv('TUSHARE_TOKEN', '')
    if token:
        print(f"✅ Tushare Token已配置: {token[:10]}...")
        return True
    else:
        print("❌ Tushare Token未配置")
        return False


def test_realtime_quote(stock_code='000063'):
    """测试实时行情获取（Tushare降级）"""
    print(f"\n{'='*60}")
    print(f"测试1: 实时行情数据 - {stock_code}")
    print(f"{'='*60}")
    
    from smart_monitor_data import SmartMonitorDataFetcher
    
    fetcher = SmartMonitorDataFetcher()
    
    # 强制使用Tushare（模拟AKShare失败）
    print("正在通过Tushare获取实时行情...")
    quote = fetcher._get_realtime_quote_from_tushare(stock_code)
    
    if quote:
        print("✅ 实时行情获取成功！")
        print(f"   股票名称: {quote.get('stock_name', 'N/A')}")
        print(f"   当前价格: ¥{quote.get('current_price', 0):.2f}")
        print(f"   涨跌幅: {quote.get('change_pct', 0):+.2f}%")
        print(f"   成交量: {quote.get('volume', 0):,}手")
        print(f"   换手率: {quote.get('turnover_rate', 0):.2f}%")
        print(f"   数据来源: {quote.get('data_source', 'N/A')}")
        return True
    else:
        print("❌ 实时行情获取失败")
        return False


def test_technical_indicators(stock_code='000063'):
    """测试技术指标计算（Tushare降级）"""
    print(f"\n{'='*60}")
    print(f"测试2: 技术指标计算 - {stock_code}")
    print(f"{'='*60}")
    
    from smart_monitor_data import SmartMonitorDataFetcher
    
    fetcher = SmartMonitorDataFetcher()
    
    # 强制使用Tushare
    print("正在通过Tushare获取历史数据并计算技术指标...")
    indicators = fetcher._get_technical_indicators_from_tushare(stock_code)
    
    if indicators:
        print("✅ 技术指标计算成功！")
        print(f"\n均线系统:")
        print(f"   MA5:  {indicators.get('ma5', 0):.2f}")
        print(f"   MA20: {indicators.get('ma20', 0):.2f}")
        print(f"   MA60: {indicators.get('ma60', 0):.2f}")
        print(f"   趋势: {indicators.get('trend', 'N/A')}")
        
        print(f"\nMACD指标:")
        print(f"   DIF: {indicators.get('macd_dif', 0):.4f}")
        print(f"   DEA: {indicators.get('macd_dea', 0):.4f}")
        print(f"   MACD: {indicators.get('macd', 0):.4f}")
        
        print(f"\nRSI指标:")
        print(f"   RSI6:  {indicators.get('rsi6', 0):.2f}")
        print(f"   RSI12: {indicators.get('rsi12', 0):.2f}")
        print(f"   RSI24: {indicators.get('rsi24', 0):.2f}")
        
        print(f"\nKDJ指标:")
        print(f"   K: {indicators.get('kdj_k', 0):.2f}")
        print(f"   D: {indicators.get('kdj_d', 0):.2f}")
        print(f"   J: {indicators.get('kdj_j', 0):.2f}")
        
        print(f"\n布林带:")
        print(f"   上轨: {indicators.get('boll_upper', 0):.2f}")
        print(f"   中轨: {indicators.get('boll_mid', 0):.2f}")
        print(f"   下轨: {indicators.get('boll_lower', 0):.2f}")
        print(f"   位置: {indicators.get('boll_position', 'N/A')}")
        
        return True
    else:
        print("❌ 技术指标计算失败")
        return False


def test_kline_data(stock_code='000063'):
    """测试K线图数据获取（Tushare降级）"""
    print(f"\n{'='*60}")
    print(f"测试3: K线图数据 - {stock_code}")
    print(f"{'='*60}")
    
    from smart_monitor_kline import SmartMonitorKline
    from smart_monitor_data import SmartMonitorDataFetcher
    
    kline = SmartMonitorKline()
    fetcher = SmartMonitorDataFetcher()
    
    # 使用Tushare获取K线数据
    print("正在通过Tushare获取K线数据（60天）...")
    df = kline._get_kline_from_tushare(stock_code, days=60, ts_pro=fetcher.ts_pro)
    
    if df is not None and not df.empty:
        print(f"✅ K线数据获取成功！")
        print(f"   数据条数: {len(df)}条")
        print(f"   日期范围: {df['日期'].min()} ~ {df['日期'].max()}")
        print(f"\n数据列:")
        for col in df.columns:
            print(f"   - {col}")
        
        print(f"\n最近5条数据预览:")
        print(df.tail(5)[['日期', '开盘', '最高', '最低', '收盘', '成交量']].to_string())
        
        return True
    else:
        print("❌ K线数据获取失败")
        return False


def test_full_monitoring_flow(stock_code='000063'):
    """测试完整的监控流程（使用Tushare）"""
    print(f"\n{'='*60}")
    print(f"测试4: 完整监控流程 - {stock_code}")
    print(f"{'='*60}")
    
    from smart_monitor_data import SmartMonitorDataFetcher
    
    fetcher = SmartMonitorDataFetcher()
    
    # 1. 获取实时行情
    print("\n步骤1: 获取实时行情...")
    quote = fetcher.get_realtime_quote(stock_code, retry=1)
    if not quote:
        print("   ❌ 实时行情获取失败")
        return False
    print(f"   ✅ 当前价: ¥{quote.get('current_price', 0):.2f}")
    
    # 2. 计算技术指标
    print("\n步骤2: 计算技术指标...")
    indicators = fetcher.get_technical_indicators(stock_code, retry=1)
    if not indicators:
        print("   ❌ 技术指标计算失败")
        return False
    print(f"   ✅ MA5: {indicators.get('ma5', 0):.2f}, 趋势: {indicators.get('trend', 'N/A')}")
    
    # 3. 综合数据
    print("\n步骤3: 获取综合数据...")
    comprehensive_data = fetcher.get_comprehensive_data(stock_code)
    if not comprehensive_data:
        print("   ❌ 综合数据获取失败")
        return False
    
    print("   ✅ 综合数据包含:")
    print(f"      - 实时行情: {comprehensive_data.get('realtime_quote') is not None}")
    print(f"      - 技术指标: {comprehensive_data.get('technical_indicators') is not None}")
    
    print("\n✅ 完整监控流程测试通过！")
    print("   Tushare可以满足AI盯盘的监控要求")
    return True


def main():
    """主测试函数"""
    print("="*60)
    print("Tushare数据源监控能力测试")
    print("="*60)
    
    # 检查Token
    if not test_tushare_token():
        print("\n❌ 请在.env文件中配置TUSHARE_TOKEN")
        return
    
    # 测试股票代码
    test_stock = '000063'  # 中兴通讯
    
    results = []
    
    # 测试1: 实时行情
    results.append(("实时行情获取", test_realtime_quote(test_stock)))
    
    # 测试2: 技术指标
    results.append(("技术指标计算", test_technical_indicators(test_stock)))
    
    # 测试3: K线数据
    results.append(("K线图数据", test_kline_data(test_stock)))
    
    # 测试4: 完整流程
    results.append(("完整监控流程", test_full_monitoring_flow(test_stock)))
    
    # 汇总结果
    print(f"\n{'='*60}")
    print("测试结果汇总")
    print(f"{'='*60}")
    
    for test_name, result in results:
        status = "✅ 通过" if result else "❌ 失败"
        print(f"{test_name:20} {status}")
    
    all_passed = all(result for _, result in results)
    
    if all_passed:
        print(f"\n{'='*60}")
        print("🎉 所有测试通过！")
        print(f"{'='*60}")
        print("✅ Tushare完全可以满足AI盯盘的监控要求")
        print("✅ 数据源降级策略工作正常")
        print("✅ 可以在AKShare IP被封时使用Tushare作为备用")
        print("\n建议:")
        print("1. 保持Tushare Token配置在.env文件中")
        print("2. AKShare重试次数已设置为1次，减少IP封禁风险")
        print("3. Tushare 10000积分可以支持日常监控需求")
    else:
        print(f"\n{'='*60}")
        print("⚠️ 部分测试失败")
        print(f"{'='*60}")
        print("请检查:")
        print("1. Tushare Token是否有效")
        print("2. Tushare积分是否足够")
        print("3. 网络连接是否正常")


if __name__ == '__main__':
    main()

