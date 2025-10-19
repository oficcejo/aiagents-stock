"""
调试风险数据获取和格式化
检查数据是否真的传递给AI
"""

from risk_data_fetcher import RiskDataFetcher
import json


def test_full_data_flow(symbol="300433"):
    """测试完整数据流程"""
    
    print("=" * 80)
    print(f"测试股票: {symbol}")
    print("=" * 80)
    
    fetcher = RiskDataFetcher()
    
    # 1. 获取原始数据
    print("\n【步骤1】获取原始风险数据...")
    risk_data = fetcher.get_risk_data(symbol)
    
    print(f"\n数据获取成功: {risk_data.get('data_success', False)}")
    
    # 2. 查看每类数据的详情
    print("\n【步骤2】查看原始数据详情...")
    
    # 限售解禁
    lifting_ban = risk_data.get('lifting_ban')
    if lifting_ban:
        print(f"\n限售解禁数据:")
        print(f"  has_data: {lifting_ban.get('has_data')}")
        df = lifting_ban.get('data')
        if df is not None:
            print(f"  记录数: {len(df)}")
            print(f"  列名: {list(df.columns)}")
            print(f"\n  前3条数据:")
            print(df.head(3))
        else:
            print(f"  data字段为None")
    
    # 大股东减持
    reduction = risk_data.get('shareholder_reduction')
    if reduction:
        print(f"\n大股东减持数据:")
        print(f"  has_data: {reduction.get('has_data')}")
        df = reduction.get('data')
        if df is not None:
            print(f"  记录数: {len(df)}")
            print(f"  列名: {list(df.columns)}")
            print(f"\n  前3条数据:")
            print(df.head(3))
            print(f"\n  完整第1条数据:")
            if len(df) > 0:
                first_row = df.iloc[0]
                for col in df.columns:
                    print(f"    {col}: {first_row[col]}")
        else:
            print(f"  data字段为None")
    
    # 重要事件
    events = risk_data.get('important_events')
    if events:
        print(f"\n重要事件数据:")
        print(f"  has_data: {events.get('has_data')}")
        df = events.get('data')
        if df is not None:
            print(f"  记录数: {len(df)}")
            print(f"  列名: {list(df.columns)}")
            print(f"\n  前3条数据:")
            print(df.head(3))
        else:
            print(f"  data字段为None")
    
    # 3. 测试格式化后的数据
    print("\n" + "=" * 80)
    print("【步骤3】测试格式化后传给AI的数据")
    print("=" * 80)
    
    formatted_data = fetcher.format_risk_data_for_ai(risk_data)
    
    print("\n格式化后的数据长度:", len(formatted_data), "字符")
    print("\n格式化后的数据内容:")
    print(formatted_data)
    
    # 4. 保存到文件供查看
    print("\n" + "=" * 80)
    print("【步骤4】保存数据到文件")
    print("=" * 80)
    
    with open("risk_data_debug_output.txt", "w", encoding="utf-8") as f:
        f.write("=" * 80 + "\n")
        f.write("原始数据结构\n")
        f.write("=" * 80 + "\n\n")
        
        # 保存原始数据（不包含DataFrame，只保存基本信息）
        f.write("data_success: " + str(risk_data.get('data_success')) + "\n\n")
        
        for key in ['lifting_ban', 'shareholder_reduction', 'important_events']:
            data = risk_data.get(key)
            if data:
                f.write(f"\n{key}:\n")
                f.write(f"  has_data: {data.get('has_data')}\n")
                f.write(f"  query: {data.get('query')}\n")
                df = data.get('data')
                if df is not None:
                    f.write(f"  记录数: {len(df)}\n")
                    f.write(f"  列名: {list(df.columns)}\n")
        
        f.write("\n" + "=" * 80 + "\n")
        f.write("格式化后传给AI的数据\n")
        f.write("=" * 80 + "\n\n")
        f.write(formatted_data)
    
    print("✓ 数据已保存到 risk_data_debug_output.txt")
    
    # 5. 检查数据是否完整
    print("\n" + "=" * 80)
    print("【步骤5】数据完整性检查")
    print("=" * 80)
    
    if "【大股东减持数据】" in formatted_data:
        print("✓ 格式化数据中包含大股东减持数据")
        
        # 检查是否有实际内容
        reduction_section = formatted_data.split("【大股东减持数据】")[1].split("=" * 80)[0]
        if len(reduction_section.strip()) > 100:
            print(f"✓ 减持数据部分有 {len(reduction_section)} 字符")
        else:
            print(f"⚠️ 减持数据部分只有 {len(reduction_section)} 字符，可能数据不完整")
    else:
        print("❌ 格式化数据中未找到大股东减持数据")
    
    print("\n" + "=" * 80)
    print("测试完成！请查看 risk_data_debug_output.txt 文件")
    print("=" * 80)


if __name__ == "__main__":
    import sys
    
    # 默认测试300433，也可以通过命令行参数指定其他股票
    symbol = sys.argv[1] if len(sys.argv) > 1 else "300433"
    
    test_full_data_flow(symbol)

