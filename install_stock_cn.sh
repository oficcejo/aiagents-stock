#!/bin/bash
set -e

echo "🚀 开始安装 Docker 及部署本地 AI 股票分析系统 (国内加速版)..."

# 1. 配置阿里云 Docker 镜像源
echo "正在配置阿里云 Docker 镜像源..."
sudo apt update
sudo apt install -y ca-certificates curl gnupg

# 创建 keyrings 目录
sudo install -m 0755 -d /etc/apt/keyrings

# 下载阿里云的 Docker GPG 密钥 (使用 -f 强制覆盖已存在的旧密钥)
curl -fsSL https://mirrors.aliyun.com/docker-ce/linux/ubuntu/gpg | sudo gpg --dearmor --yes -o /etc/apt/keyrings/docker.gpg
sudo chmod a+r /etc/apt/keyrings/docker.gpg

# 配置阿里云的 Apt 仓库源
echo \
  "deb [arch="$(dpkg --print-architecture )" signed-by=/etc/apt/keyrings/docker.gpg] https://mirrors.aliyun.com/docker-ce/linux/ubuntu \
  "$(. /etc/os-release && echo "$VERSION_CODENAME" )" stable" | \
  sudo tee /etc/apt/sources.list.d/docker.list > /dev/null

echo "正在更新软件包列表并安装 Docker..."
sudo apt update
sudo apt install -y docker-ce docker-ce-cli containerd.io docker-buildx-plugin docker-compose-plugin

# 2. 检查当前目录是否为项目目录
if [ ! -f "docker-compose.yml" ]; then
    echo "❌ 错误: 当前目录下未找到 docker-compose.yml 文件。"
    echo "请确认您已在 aiagents-stock 目录下运行此脚本。"
    exit 1
fi

# 3. 配置环境变量
if [ ! -f ".env" ]; then
    if [ -f ".env.example" ]; then
        cp .env.example .env
        echo "✅ 已根据 .env.example 创建 .env 文件"
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
echo "✅ 部署完成！"
echo "👉 请执行以下命令填入您的 API Key:"
echo "   nano .env"
echo "👉 重启服务使配置生效:"
echo "   sudo docker compose restart"
echo "🌐 访问地址: http://100.110.102.24:8503"
echo "------------------------------------------------"
