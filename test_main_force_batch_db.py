#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
主力选股批量分析数据库功能测试
"""

from main_force_batch_db import batch_db
import json

def test_database():
    """测试数据库功能"""
    
    print("=" * 60)
    print("主力选股批量分析数据库功能测试")
    print("=" * 60)
    
    # 测试1: 保存批量分析结果
    print("\n📝 测试1: 保存批量分析结果")
    test_results = [
        {
            "symbol": "000001",
            "success": True,
            "stock_info": {"股票名称": "平安银行"},
            "final_decision": {
                "investment_rating": "买入",
                "confidence_level": 85,
                "entry_range": "10.0-10.5",
                "take_profit": "12.0",
                "stop_loss": "9.5"
            }
        },
        {
            "symbol": "600036",
            "success": True,
            "stock_info": {"股票名称": "招商银行"},
            "final_decision": {
                "investment_rating": "持有",
                "confidence_level": 75,
                "entry_range": "35.0-36.0",
                "take_profit": "40.0",
                "stop_loss": "33.0"
            }
        },
        {
            "symbol": "600519",
            "success": False,
            "error": "数据获取失败"
        }
    ]
    
    try:
        record_id = batch_db.save_batch_analysis(
            batch_count=3,
            analysis_mode="sequential",
            success_count=2,
            failed_count=1,
            total_time=180.5,
            results=test_results
        )
        print(f"✅ 保存成功，记录ID: {record_id}")
    except Exception as e:
        print(f"❌ 保存失败: {str(e)}")
        return
    
    # 测试2: 获取统计信息
    print("\n📊 测试2: 获取统计信息")
    try:
        stats = batch_db.get_statistics()
        print(f"✅ 统计信息:")
        print(f"   总记录数: {stats['total_records']}")
        print(f"   分析股票总数: {stats['total_stocks_analyzed']}")
        print(f"   成功数: {stats['total_success']}")
        print(f"   失败数: {stats['total_failed']}")
        print(f"   成功率: {stats['success_rate']}%")
        print(f"   平均耗时: {stats['average_time']}秒")
    except Exception as e:
        print(f"❌ 获取统计信息失败: {str(e)}")
    
    # 测试3: 获取历史记录列表
    print("\n📚 测试3: 获取历史记录列表")
    try:
        history = batch_db.get_all_history(limit=5)
        print(f"✅ 获取到 {len(history)} 条记录")
        for idx, record in enumerate(history[:3], 1):
            print(f"\n   记录{idx}:")
            print(f"   - ID: {record['id']}")
            print(f"   - 时间: {record['analysis_date']}")
            print(f"   - 数量: {record['batch_count']}")
            print(f"   - 成功: {record['success_count']}")
            print(f"   - 失败: {record['failed_count']}")
            print(f"   - 耗时: {record['total_time']}秒")
    except Exception as e:
        print(f"❌ 获取历史记录失败: {str(e)}")
    
    # 测试4: 获取单条记录
    print(f"\n🔍 测试4: 获取单条记录 (ID: {record_id})")
    try:
        record = batch_db.get_record_by_id(record_id)
        if record:
            print(f"✅ 获取成功")
            print(f"   分析时间: {record['analysis_date']}")
            print(f"   结果数量: {len(record['results'])}")
            print(f"   成功股票: {[r['symbol'] for r in record['results'] if r.get('success')]}")
            print(f"   失败股票: {[r['symbol'] for r in record['results'] if not r.get('success')]}")
        else:
            print(f"❌ 记录不存在")
    except Exception as e:
        print(f"❌ 获取记录失败: {str(e)}")
    
    # 测试5: 删除记录
    print(f"\n🗑️  测试5: 删除记录 (ID: {record_id})")
    confirm = input("   是否删除测试记录? (y/n): ")
    if confirm.lower() == 'y':
        try:
            success = batch_db.delete_record(record_id)
            if success:
                print(f"✅ 删除成功")
            else:
                print(f"❌ 删除失败")
        except Exception as e:
            print(f"❌ 删除失败: {str(e)}")
    else:
        print("   跳过删除")
    
    print("\n" + "=" * 60)
    print("测试完成！")
    print("=" * 60)
    print("\n💡 提示:")
    print("   - 数据库文件: main_force_batch.db")
    print("   - 可使用 SQLite 工具查看数据库内容")
    print("   - 在Streamlit应用中点击'📚 批量分析历史'查看UI界面")
    print("=" * 60)


if __name__ == "__main__":
    test_database()

