#!/bin/bash
# 数据库文件迁移脚本（按文件大小判断）
# 将根目录下较大的数据库文件迁移到 data 目录

cd "$(dirname "$0")"

echo "开始迁移数据库文件到 data 目录（按文件大小判断）..."
echo ""

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
        root_size=$(stat -f%z "$db" 2>/dev/null || stat -c%s "$db" 2>/dev/null || echo 0)
        
        if [ -f "$data_db" ]; then
            data_size=$(stat -f%z "$data_db" 2>/dev/null || stat -c%s "$data_db" 2>/dev/null || echo 0)
            if [ "$root_size" -gt "$data_size" ]; then
                echo "迁移: $db (根目录: $(numfmt --to=iec-i --suffix=B $root_size 2>/dev/null || echo ${root_size}B) > data目录: $(numfmt --to=iec-i --suffix=B $data_size 2>/dev/null || echo ${data_size}B))"
                cp "$db" "$data_db"
                echo "  ✅ 已迁移（保留根目录文件作为备份）"
            else
                echo "跳过: $db (data目录版本已更新或相同)"
            fi
        else
            echo "迁移: $db -> $data_db"
            cp "$db" "$data_db"
            echo "  ✅ 已迁移"
        fi
    fi
done

echo ""
echo "迁移完成！现在可以停止并重启 Docker 服务了。"
