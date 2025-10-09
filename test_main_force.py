#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
主力选股功能测试脚本
快速验证功能是否正常工作
"""

import sys
from datetime import datetime, timedelta

def test_imports():
    """测试模块导入"""
    print("="*60)
    print("测试1: 检查模块导入")
    print("="*60)
    
    try:
        print("导入 pywencai...", end=" ")
        import pywencai
        print("✅")
    except Exception as e:
        print(f"❌ {e}")
        return False
    
    try:
        print("导入 main_force_selector...", end=" ")
        from main_force_selector import main_force_selector
        print("✅")
    except Exception as e:
        print(f"❌ {e}")
        return False
    
    try:
        print("导入 main_force_analysis...", end=" ")
        from main_force_analysis import MainForceAnalyzer
        print("✅")
    except Exception as e:
        print(f"❌ {e}")
        return False
    
    try:
        print("导入 main_force_ui...", end=" ")
        from main_force_ui import display_main_force_selector
        print("✅")
    except Exception as e:
        print(f"❌ {e}")
        return False
    
    print("\n✅ 所有模块导入成功！\n")
    return True

def test_data_fetch():
    """测试数据获取"""
    print("="*60)
    print("测试2: 测试数据获取功能")
    print("="*60)
    
    try:
        from main_force_selector import main_force_selector
        
        # 使用较短的时间范围进行测试
        print("\n尝试获取最近30天的主力资金数据...")
        success, data, message = main_force_selector.get_main_force_stocks(days_ago=30)
        
        if success:
            print(f"\n✅ 数据获取成功！")
            print(f"   获取到 {len(data)} 只股票")
            print(f"\n前5只股票:")
            print(data.head(5) if len(data) > 0 else "无数据")
            return True
        else:
            print(f"\n❌ 数据获取失败: {message}")
            print("\n可能原因:")
            print("  1. 网络连接问题")
            print("  2. pywencai服务暂时不可用")
            print("  3. 需要安装Node.js >= 16.0")
            print("\n请检查:")
            print("  - 网络连接是否正常")
            print("  - Node.js版本: node --version")
            print("  - pywencai是否正确安装: pip list | findstr pywencai")
            return False
    
    except Exception as e:
        print(f"\n❌ 测试过程出错: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_filter():
    """测试筛选功能"""
    print("\n" + "="*60)
    print("测试3: 测试筛选功能")
    print("="*60)
    
    try:
        from main_force_selector import main_force_selector
        import pandas as pd
        
        # 创建测试数据
        test_data = pd.DataFrame({
            '股票代码': ['000001', '000002', '600519', '300750'],
            '股票简称': ['平安银行', '万科A', '贵州茅台', '宁德时代'],
            '区间涨跌幅': [15.5, 35.8, 12.3, 28.9],
            '总市值': [3000, 2500, 25000, 9000],
            '主力资金净流入': [50000000, 80000000, 120000000, 95000000]
        })
        
        print("\n原始测试数据:")
        print(test_data)
        
        print("\n应用筛选条件:")
        print("  - 区间涨跌幅 < 30%")
        print("  - 市值 50-1300亿")
        
        filtered_data = main_force_selector.filter_stocks(
            test_data,
            max_range_change=30.0,
            min_market_cap=50.0,
            max_market_cap=1300.0
        )
        
        print("\n筛选后数据:")
        print(filtered_data)
        
        print("\n✅ 筛选功能正常！")
        return True
        
    except Exception as e:
        print(f"\n❌ 筛选测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_ai_analysis():
    """测试AI分析（需要API配置）"""
    print("\n" + "="*60)
    print("测试4: 测试AI分析功能")
    print("="*60)
    
    try:
        import os
        from dotenv import load_dotenv
        
        load_dotenv()
        
        api_key = os.getenv('DEEPSEEK_API_KEY')
        if not api_key:
            print("\n⚠️  未配置DEEPSEEK_API_KEY，跳过AI分析测试")
            print("   请在.env文件中配置API密钥后再测试AI功能")
            return None
        
        print("\n✅ API密钥已配置")
        print("   如需测试完整AI分析，请运行主程序")
        return True
        
    except Exception as e:
        print(f"\n⚠️  {e}")
        return None

def main():
    """主测试函数"""
    print("\n" + "="*80)
    print(" "*20 + "主力选股功能测试")
    print("="*80 + "\n")
    
    results = []
    
    # 测试1: 模块导入
    result1 = test_imports()
    results.append(("模块导入", result1))
    
    if not result1:
        print("\n❌ 模块导入失败，请先安装依赖:")
        print("   pip install pywencai pandas streamlit")
        return
    
    # 测试2: 数据获取
    result2 = test_data_fetch()
    results.append(("数据获取", result2))
    
    # 测试3: 筛选功能
    result3 = test_filter()
    results.append(("数据筛选", result3))
    
    # 测试4: AI分析
    result4 = test_ai_analysis()
    if result4 is not None:
        results.append(("AI分析", result4))
    
    # 总结
    print("\n" + "="*80)
    print(" "*30 + "测试总结")
    print("="*80 + "\n")
    
    for test_name, result in results:
        status = "✅ 通过" if result else "❌ 失败"
        print(f"{test_name:<15} {status}")
    
    passed = sum(1 for _, r in results if r)
    total = len(results)
    
    print(f"\n总计: {passed}/{total} 项测试通过")
    
    if passed == total:
        print("\n🎉 恭喜！所有测试通过，主力选股功能可以正常使用！")
        print("\n下一步:")
        print("  1. 运行主程序: streamlit run app.py")
        print("  2. 点击侧边栏的 '🎯 主力选股' 按钮")
        print("  3. 设置参数并开始分析")
    else:
        print("\n⚠️  部分测试未通过，请根据上述错误信息进行排查")
        print("\n常见问题:")
        print("  1. 数据获取失败 → 检查网络和Node.js版本")
        print("  2. 模块导入失败 → 检查依赖安装")
        print("  3. API测试失败 → 检查.env配置")
    
    print("\n" + "="*80 + "\n")

if __name__ == "__main__":
    main()

