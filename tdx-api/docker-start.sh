#!/bin/bash

echo "========================================"
echo "  TDX股票数据查询系统 - Docker版"
echo "========================================"
echo ""

# 检查Docker是否安装
if ! command -v docker &> /dev/null; then
    echo "[错误] 未检测到Docker，请先安装Docker"
    echo ""
    echo "安装方法: https://docs.docker.com/get-docker/"
    echo ""
    exit 1
fi

echo "[√] Docker已安装"
echo ""

# 检查Docker是否运行
if ! docker ps &> /dev/null; then
    echo "[错误] Docker未运行，请先启动Docker"
    echo ""
    echo "启动命令: sudo systemctl start docker"
    echo ""
    exit 1
fi

echo "[√] Docker正在运行"
echo ""

# 检查docker-compose是否可用
if ! command -v docker-compose &> /dev/null; then
    echo "[错误] docker-compose不可用，请先安装"
    echo ""
    echo "安装命令: sudo apt-get install docker-compose"
    echo ""
    exit 1
fi

echo "[√] docker-compose可用"
echo ""

echo "----------------------------------------"
echo "正在构建并启动服务..."
echo "----------------------------------------"
echo ""

# 启动服务
docker-compose up -d

if [ $? -ne 0 ]; then
    echo ""
    echo "[错误] 启动失败，请查看上面的错误信息"
    echo ""
    exit 1
fi

echo ""
echo "========================================"
echo "  启动成功！"
echo "========================================"
echo ""
echo "访问地址: http://localhost:8080"
echo ""
echo "常用命令:"
echo "  查看日志: docker-compose logs -f"
echo "  停止服务: docker-compose stop"
echo "  重启服务: docker-compose restart"
echo "  完全清理: docker-compose down"
echo ""
echo "----------------------------------------"
echo ""

# 等待服务完全启动
sleep 3

# 尝试在浏览器中打开（不同系统）
if command -v xdg-open &> /dev/null; then
    xdg-open http://localhost:8080
elif command -v open &> /dev/null; then
    open http://localhost:8080
else
    echo "请手动在浏览器中打开: http://localhost:8080"
fi

echo "准备就绪！"

