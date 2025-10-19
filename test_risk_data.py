"""
风险数据获取功能测试脚本
测试pywencai获取限售解禁、大股东减持、重要事件数据
"""

from risk_data_fetcher import RiskDataFetcher


def test_risk_data_fetcher():
    """测试风险数据获取器"""
    
    print("=" * 80)
    print("风险数据获取功能测试")
    print("=" * 80)
    
    # 初始化获取器
    fetcher = RiskDataFetcher()
    
    # 测试股票列表（建议使用大盘股，数据更全）
    test_symbols = [
        "600000",  # 浦发银行
        "000001",  # 平安银行
        "600519",  # 茅台
    ]
    
    for symbol in test_symbols:
        print(f"\n{'=' * 80}")
        print(f"测试股票: {symbol}")
        print(f"{'=' * 80}")
        
        # 获取风险数据
        risk_data = fetcher.get_risk_data(symbol)
        
        # 显示结果
        print(f"\n数据获取成功: {risk_data.get('data_success', False)}")
        
        if risk_data.get('error'):
            print(f"错误信息: {risk_data['error']}")
            continue
        
        # 显示限售解禁数据
        lifting_ban = risk_data.get('lifting_ban')
        if lifting_ban and lifting_ban.get('has_data'):
            print(f"\n✅ 限售解禁数据:")
            print(f"   查询语句: {lifting_ban.get('query')}")
            df_data = lifting_ban.get('data')
            if df_data is not None and not df_data.empty:
                print(f"   记录数: {len(df_data)}")
                print(f"   字段: {', '.join(df_data.columns.tolist())}")
                print(f"   前3条记录:")
                print(df_data.head(3).to_string(index=False))
        else:
            print(f"\nℹ️ 暂无限售解禁数据")
        
        # 显示股东减持数据
        reduction = risk_data.get('shareholder_reduction')
        if reduction and reduction.get('has_data'):
            print(f"\n✅ 大股东减持数据:")
            print(f"   查询语句: {reduction.get('query')}")
            df_data = reduction.get('data')
            if df_data is not None and not df_data.empty:
                print(f"   记录数: {len(df_data)}")
                print(f"   字段: {', '.join(df_data.columns.tolist())}")
                print(f"   前3条记录:")
                print(df_data.head(3).to_string(index=False))
        else:
            print(f"\nℹ️ 暂无大股东减持数据")
        
        # 显示重要事件数据
        events = risk_data.get('important_events')
        if events and events.get('has_data'):
            print(f"\n✅ 重要事件数据:")
            print(f"   查询语句: {events.get('query')}")
            df_data = events.get('data')
            if df_data is not None and not df_data.empty:
                print(f"   记录数: {len(df_data)}")
                print(f"   字段: {', '.join(df_data.columns.tolist())}")
                print(f"   前3条记录:")
                print(df_data.head(3).to_string(index=False))
        else:
            print(f"\nℹ️ 暂无重要事件数据")
        
        # 显示格式化后的数据
        print(f"\n{'=' * 80}")
        print("格式化供AI分析的数据:")
        print(f"{'=' * 80}")
        formatted_data = fetcher.format_risk_data_for_ai(risk_data)
        print(formatted_data)
    
    print(f"\n{'=' * 80}")
    print("测试完成！")
    print(f"{'=' * 80}")


def test_risk_management_agent():
    """测试风险管理师功能"""
    
    print("\n" + "=" * 80)
    print("风险管理师AI分析测试")
    print("=" * 80)
    
    # 需要配置API Key才能测试
    try:
        from ai_agents import StockAnalysisAgents
        from risk_data_fetcher import RiskDataFetcher
        
        # 测试股票
        test_symbol = "600000"
        
        print(f"\n测试股票: {test_symbol}")
        
        # 获取风险数据
        fetcher = RiskDataFetcher()
        risk_data = fetcher.get_risk_data(test_symbol)
        
        if not risk_data.get('data_success'):
            print("未获取到风险数据，跳过AI分析测试")
            return
        
        # 模拟股票信息和指标
        stock_info = {
            'symbol': test_symbol,
            'name': '测试股票',
            'current_price': 10.5,
            'beta': 1.2,
            '52_week_high': 12.0,
            '52_week_low': 8.5
        }
        
        indicators = {
            'rsi': 65.5,
            'macd': 0.15
        }
        
        # 初始化AI分析系统
        print("\n初始化AI分析系统...")
        agents = StockAnalysisAgents()
        
        # 运行风险管理师分析
        print("\n运行风险管理师分析...")
        result = agents.risk_management_agent(stock_info, indicators, risk_data)
        
        # 显示分析结果
        print(f"\n{'=' * 80}")
        print(f"分析师: {result['agent_name']}")
        print(f"职责: {result['agent_role']}")
        print(f"关注领域: {', '.join(result['focus_areas'])}")
        print(f"{'=' * 80}")
        print("\n分析报告:")
        print(result['analysis'])
        
    except ImportError as e:
        print(f"⚠️ 导入模块失败: {e}")
        print("提示：请确保已安装所有依赖并配置API Key")
    except Exception as e:
        print(f"❌ 测试失败: {e}")


if __name__ == "__main__":
    # 测试1：风险数据获取
    test_risk_data_fetcher()
    
    # 测试2：AI分析（需要API Key）
    print("\n\n是否测试AI分析功能？（需要配置DeepSeek API Key）")
    user_input = input("输入 y 继续，其他键跳过: ")
    
    if user_input.lower() == 'y':
        test_risk_management_agent()
    else:
        print("\n跳过AI分析测试")
    
    print("\n✅ 所有测试完成！")

