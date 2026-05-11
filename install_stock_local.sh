#!/bin/bash
set -e

echo "🚀 开始安装 Docker 及部署本地 AI 股票分析系统..."

# 1. 安装 Docker & Docker Compose (Ubuntu 优化方式)
echo "正在配置 Docker 仓库..."
sudo apt update
sudo apt install -y ca-certificates curl gnupg
sudo install -m 0755 -d /etc/apt/keyrings
curl -fsSL https://download.docker.com/linux/ubuntu/gpg | sudo gpg --dearmor -o /etc/apt/keyrings/docker.gpg
sudo chmod a+r /etc/apt/keyrings/docker.gpg

echo \
  "deb [arch="$(dpkg --print-architecture )" signed-by=/etc/apt/keyrings/docker.gpg] https://download.docker.com/linux/ubuntu \
  "$(. /etc/os-release && echo "$VERSION_CODENAME" )" stable" | \
  sudo tee /etc/apt/sources.list.d/docker.list > /dev/null

sudo apt update
sudo apt install -y docker-ce docker-ce-cli containerd.io docker-buildx-plugin docker-compose-plugin

# 2. 检查当前目录是否为项目目录
if [ ! -f "docker-compose.yml" ]; then
    echo "❌ 错误: 当前目录下未找到 docker-compose.yml 文件。"
    echo "请确保您在 aiagents-stock 项目根目录下运行此脚本。"
    exit 1
fi

# 3. 配置环境变量
if [ ! -f ".env" ]; then
    if [ -f ".env.example" ]; then
        cp .env.example .env
        echo "✅ 已根据 .env.example 创建 .env 文件"
    else
        echo "⚠️ 警告: 未找到 .env.example 文件，请手动创建 .env"
    fi
fi

# 4. 启动服务
echo "正在通过 Docker Compose 启动服务..."
sudo docker compose up -d

# 5. 配置防火墙开放 8503 端口
if command -v ufw > /dev/null; then
    sudo ufw allow 8503/tcp
    echo "✅ 已通过 ufw 开放 8503 端口"
fi

echo "------------------------------------------------"
echo "✅ 部署基本完成！"
echo "👉 请执行以下命令填入您的 API Key:"
echo "   nano .env"
echo "👉 然后重启服务使配置生效:"
echo "   sudo docker compose restart"
echo "🌐 访问地址:"
echo "   - Tailscale 访问: http://100.110.102.24:8503"
echo "   - 本机访问: http://localhost:8503"
echo "------------------------------------------------"
