#!/bin/bash
# 数据库文件迁移脚本
# 将根目录下的数据库文件迁移到 data 目录（如果 data 目录下没有或更旧）

cd "$(dirname "$0")"

echo "开始迁移数据库文件到 data 目录..."

# 确保 data 目录存在
mkdir -p data

# 需要迁移的数据库文件列表
databases=(
    "stock_analysis.db"
    "stock_monitor.db"
    "portfolio_stocks.db"
    "sector_strategy.db"
    "longhubang.db"
    "main_force_batch.db"
    "smart_monitor.db"
    "low_price_bull_monitor.db"
    "profit_growth_monitor.db"
)

for db in "${databases[@]}"; do
    if [ -f "$db" ]; then
        data_db="data/$db"
        if [ ! -f "$data_db" ] || [ "$db" -nt "$data_db" ]; then
            echo "迁移: $db -> $data_db"
            cp "$db" "$data_db"
            echo "  ✅ 已迁移"
        else
            echo "跳过: $db (data目录下已有更新版本)"
        fi
    else
        echo "不存在: $db (跳过)"
    fi
done

echo ""
echo "迁移完成！现在可以安全地删除根目录下的数据库文件（如果确认data目录下的数据正确）。"
