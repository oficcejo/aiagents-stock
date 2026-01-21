#!/bin/bash
# 清理根目录的数据库文件（已迁移到 data 目录）

echo "🧹 清理根目录的数据库文件..."
echo ""

# 数据库文件列表
DB_FILES=(
    "stock_analysis.db"
    "sector_strategy.db"
    "low_price_bull_monitor.db"
    "main_force_batch.db"
    "stock_monitor.db"
    "portfolio_stocks.db"
    "longhubang.db"
    "smart_monitor.db"
    "profit_growth_monitor.db"
)

for db_file in "${DB_FILES[@]}"; do
    if [ -f "$db_file" ]; then
        # 检查 data 目录是否有对应的文件
        if [ -f "data/$db_file" ]; then
            echo "✅ 删除根目录的 $db_file (已迁移到 data 目录)"
            rm "$db_file"
        else
            echo "⚠️  跳过 $db_file (data 目录不存在对应文件)"
        fi
    fi
done

# 清理备份文件
if [ -f "data/main_force_batch.db.backup" ]; then
    echo ""
    echo "🗑️  删除备份文件: data/main_force_batch.db.backup"
    rm "data/main_force_batch.db.backup"
fi

echo ""
echo "✅ 清理完成！"
