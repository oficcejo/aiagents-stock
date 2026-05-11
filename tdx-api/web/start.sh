#!/bin/bash

echo "========================================"
echo "  股票数据查询Web系统"
echo "========================================"
echo ""
echo "正在启动服务器..."
echo ""

cd "$(dirname "$0")"
go run server.go

