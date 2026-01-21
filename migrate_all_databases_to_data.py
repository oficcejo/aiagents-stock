#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
将所有数据库文件迁移到 data 目录
统一数据库文件存储规范
"""

import os
import shutil
import sqlite3
from pathlib import Path

# 数据库文件映射（根目录 -> data目录）
DB_FILES = [
    'stock_analysis.db',
    'sector_strategy.db',
    'low_price_bull_monitor.db',
    'main_force_batch.db',
    'stock_monitor.db',
    'portfolio_stocks.db',
    'longhubang.db',
    'smart_monitor.db',
    'profit_growth_monitor.db',
]

def check_database_tables(db_path):
    """检查数据库文件是否有表"""
    if not os.path.exists(db_path):
        return False, []
    
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
        tables = [row[0] for row in cursor.fetchall()]
        conn.close()
        return len(tables) > 0, tables
    except Exception as e:
        print(f"   ⚠️  检查数据库时出错: {e}")
        return False, []

def migrate_database(root_file, data_file):
    """迁移单个数据库文件"""
    root_path = Path(root_file)
    data_path = Path(data_file)
    
    # 检查根目录文件是否存在
    if not root_path.exists():
        return "skip", "根目录文件不存在"
    
    # 检查 data 目录文件是否存在
    if data_path.exists():
        # 检查两个文件的内容
        root_has_tables, root_tables = check_database_tables(str(root_path))
        data_has_tables, data_tables = check_database_tables(str(data_path))
        
        root_size = root_path.stat().st_size
        data_size = data_path.stat().st_size
        
        if root_has_tables and not data_has_tables:
            # 根目录有数据，data目录没有，备份后替换
            backup_path = data_path.with_suffix('.db.backup')
            shutil.copy2(data_path, backup_path)
            shutil.copy2(root_path, data_path)
            return "replaced", f"已替换（根目录有数据，data目录为空，已备份到 {backup_path.name}）"
        elif root_has_tables and data_has_tables:
            # 两个都有数据，比较大小
            if root_size > data_size:
                # 根目录的数据更多，询问是否替换
                backup_path = data_path.with_suffix('.db.backup')
                shutil.copy2(data_path, backup_path)
                shutil.copy2(root_path, data_path)
                return "replaced", f"已替换（根目录数据更多，已备份到 {backup_path.name}）"
            else:
                return "skip", "data目录已有数据，跳过"
        elif not root_has_tables and data_has_tables:
            return "skip", "data目录已有数据，根目录为空，跳过"
        else:
            # 两个都为空，删除根目录的
            return "skip", "两个都为空，跳过"
    else:
        # data目录不存在，直接移动
        data_path.parent.mkdir(parents=True, exist_ok=True)
        shutil.move(str(root_path), str(data_path))
        return "moved", "已移动到data目录"

def main():
    """主函数"""
    print("=" * 80)
    print("📦 数据库文件迁移工具 - 统一到 data 目录")
    print("=" * 80)
    print()
    
    # 确保 data 目录存在
    data_dir = Path('data')
    data_dir.mkdir(exist_ok=True)
    
    results = []
    
    for db_file in DB_FILES:
        root_file = Path(db_file)
        data_file = data_dir / db_file
        
        print(f"📁 处理: {db_file}")
        
        if not root_file.exists():
            print(f"   ✅ 根目录不存在，检查 data 目录...")
            if data_file.exists():
                has_tables, tables = check_database_tables(str(data_file))
                if has_tables:
                    print(f"   ✅ data 目录已存在且有数据（{len(tables)} 个表）")
                    results.append((db_file, "already_in_data", "已在data目录"))
                else:
                    print(f"   ⚠️  data 目录存在但无表")
                    results.append((db_file, "empty_in_data", "data目录存在但无表"))
            else:
                print(f"   ⚠️  两个位置都不存在")
                results.append((db_file, "not_found", "两个位置都不存在"))
        else:
            # 根目录存在，进行迁移
            status, message = migrate_database(str(root_file), str(data_file))
            print(f"   {message}")
            results.append((db_file, status, message))
        
        print()
    
    # 清理空的根目录数据库文件
    print("=" * 80)
    print("🧹 清理根目录的空数据库文件...")
    print("=" * 80)
    
    for db_file in DB_FILES:
        root_file = Path(db_file)
        data_file = data_dir / db_file
        
        if root_file.exists() and data_file.exists():
            root_has_tables, _ = check_database_tables(str(root_file))
            data_has_tables, _ = check_database_tables(str(data_file))
            
            if not root_has_tables and data_has_tables:
                # 根目录为空，data目录有数据，删除根目录的
                try:
                    root_file.unlink()
                    print(f"   ✅ 已删除空文件: {db_file}")
                except Exception as e:
                    print(f"   ⚠️  删除失败: {db_file} - {e}")
    
    # 清理 main_force_batch1.db（重复文件）
    batch1_file = data_dir / 'main_force_batch1.db'
    if batch1_file.exists():
        has_tables, _ = check_database_tables(str(batch1_file))
        if not has_tables:
            try:
                batch1_file.unlink()
                print(f"   ✅ 已删除空文件: main_force_batch1.db")
            except Exception as e:
                print(f"   ⚠️  删除失败: main_force_batch1.db - {e}")
    
    # 验证迁移结果
    print()
    print("=" * 80)
    print("✅ 迁移完成！验证结果：")
    print("=" * 80)
    
    for db_file in DB_FILES:
        data_file = data_dir / db_file
        if data_file.exists():
            has_tables, tables = check_database_tables(str(data_file))
            if has_tables:
                print(f"   ✅ {db_file}: data目录存在，{len(tables)} 个表")
            else:
                print(f"   ⚠️  {db_file}: data目录存在但无表")
        else:
            print(f"   ❌ {db_file}: data目录不存在")
    
    print()
    print("=" * 80)
    print("📝 注意事项：")
    print("   1. 所有数据库文件现在应该在 data 目录下")
    print("   2. 如果根目录还有数据库文件，请手动检查并删除")
    print("   3. 建议重启应用以确保使用正确的数据库文件")
    print("=" * 80)

if __name__ == '__main__':
    main()
