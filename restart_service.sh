#!/bin/bash
# 停止并重启 Docker 服务脚本

cd "$(dirname "$0")"

echo "=========================================="
echo "停止并重启 Docker 服务"
echo "=========================================="
echo ""

# 1. 停止服务
echo "1. 停止现有服务..."
docker-compose down
echo ""

# 2. 重新构建（使用 --no-cache 确保使用最新代码）
echo "2. 重新构建 Docker 镜像（这可能需要几分钟）..."
docker-compose build --no-cache
echo ""

# 3. 启动服务
echo "3. 启动服务..."
docker-compose up -d
echo ""

# 4. 查看服务状态
echo "4. 查看服务状态..."
sleep 3
docker-compose ps
echo ""

# 5. 查看日志
echo "5. 查看最新日志（按 Ctrl+C 退出）..."
echo "=========================================="
docker-compose logs -f --tail=50
