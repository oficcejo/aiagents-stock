# 🐳 Docker 部署指南

本文档详细说明如何使用 Docker 部署 AI 股票分析系统。

## 📋 前置要求

- Docker 20.10+ 
- Docker Compose 2.0+（可选，但推荐）
- 至少 2GB 可用磁盘空间
- DeepSeek API Key

### 安装 Docker

#### Windows
1. 下载并安装 [Docker Desktop for Windows](https://www.docker.com/products/docker-desktop/)
2. 启动 Docker Desktop
3. 确认安装成功：
```bash
docker --version
docker-compose --version
```

#### macOS
1. 下载并安装 [Docker Desktop for Mac](https://www.docker.com/products/docker-desktop/)
2. 启动 Docker Desktop
3. 确认安装成功：
```bash
docker --version
docker-compose --version
```

#### Linux
```bash
# Ubuntu/Debian
curl -fsSL https://get.docker.com -o get-docker.sh
sudo sh get-docker.sh
sudo systemctl start docker
sudo systemctl enable docker

# 安装 Docker Compose
sudo curl -L "https://github.com/docker/compose/releases/latest/download/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
sudo chmod +x /usr/local/bin/docker-compose

# 验证安装
docker --version
docker-compose --version
```

## 🚀 快速开始

### 方法一：使用 Docker Compose（推荐）

1. **克隆或下载项目**
```bash
cd /path/to/agentsstock1
```

2. **配置环境变量**
```bash
# Windows (PowerShell)
Copy-Item .env.example .env

# Linux/macOS
cp .env.example .env
```

3. **编辑 `.env` 文件，填入您的配置**
```env
DEEPSEEK_API_KEY=sk-your-actual-api-key-here
EMAIL_ENABLED=false
# ... 其他配置
```

4. **启动服务**
```bash
docker-compose up -d
```

5. **访问应用**
打开浏览器访问：http://localhost:8503

6. **查看日志**
```bash
docker-compose logs -f
```

7. **停止服务**
```bash
docker-compose down
```

### 方法二：使用 Docker 命令

1. **构建镜像**
```bash
docker build -t agentsstock1:latest .
```

2. **创建数据目录**
```bash
mkdir -p data
```

3. **运行容器**
```bash
docker run -d \
  --name agentsstock1 \
  -p 8503:8503 \
  -v $(pwd)/data:/app/data \
  -v $(pwd)/.env:/app/.env \
  -v $(pwd)/stock_analysis.db:/app/stock_analysis.db \
  -v $(pwd)/stock_monitor.db:/app/stock_monitor.db \
  -e TZ=Asia/Shanghai \
  --restart unless-stopped \
  agentsstock1:latest
```

**Windows PowerShell 用户请使用：**
```powershell
docker run -d `
  --name agentsstock1 `
  -p 8503:8503 `
  -v ${PWD}/data:/app/data `
  -v ${PWD}/.env:/app/.env `
  -v ${PWD}/stock_analysis.db:/app/stock_analysis.db `
  -v ${PWD}/stock_monitor.db:/app/stock_monitor.db `
  -e TZ=Asia/Shanghai `
  --restart unless-stopped `
  agentsstock1:latest
```

4. **查看日志**
```bash
docker logs -f agentsstock1
```

5. **停止容器**
```bash
docker stop agentsstock1
docker rm agentsstock1
```

## 📁 数据持久化

Docker 部署会自动挂载以下目录/文件到宿主机：

- `./data` - 临时数据目录
- `./stock_analysis.db` - 分析历史数据库
- `./stock_monitor.db` - 监测数据库
- `./.env` - 环境变量配置

**重要**：即使删除容器，这些数据也会保留在宿主机上。

## 🔧 常用命令

### Docker Compose

```bash
# 启动服务（后台运行）
docker-compose up -d

# 启动服务（前台运行，可看日志）
docker-compose up

# 停止服务
docker-compose down

# 重启服务
docker-compose restart

# 查看日志
docker-compose logs -f

# 查看服务状态
docker-compose ps

# 重新构建并启动
docker-compose up -d --build

# 完全清理（包括volumes）
docker-compose down -v
```

### Docker 命令

```bash
# 查看运行中的容器
docker ps

# 查看所有容器
docker ps -a

# 查看日志
docker logs agentsstock1
docker logs -f agentsstock1  # 实时日志

# 进入容器
docker exec -it agentsstock1 bash

# 重启容器
docker restart agentsstock1

# 停止容器
docker stop agentsstock1

# 启动已停止的容器
docker start agentsstock1

# 删除容器
docker rm agentsstock1

# 删除镜像
docker rmi agentsstock1:latest

# 查看镜像
docker images

# 查看容器资源使用
docker stats agentsstock1
```

## 🐛 故障排除

### 1. 容器启动失败

**检查日志**：
```bash
docker-compose logs
# 或
docker logs agentsstock1
```

**常见原因**：
- `.env` 文件未配置或配置错误
- 端口 8503 已被占用
- Docker 资源不足

### 2. 端口被占用

修改 `docker-compose.yml` 中的端口映射：
```yaml
ports:
  - "8504:8503"  # 改为其他端口
```

或在 docker run 命令中修改：
```bash
docker run ... -p 8504:8503 ...
```

### 3. 无法访问网页

**检查容器状态**：
```bash
docker ps
```

**检查健康状态**：
```bash
docker inspect agentsstock1 | grep Health -A 10
```

**检查网络**：
```bash
# 确认端口映射
docker port agentsstock1

# 尝试从容器内访问
docker exec agentsstock1 curl http://localhost:8503
```

### 4. 数据库权限问题

Linux/macOS 用户可能遇到权限问题：
```bash
# 修改数据库文件权限
chmod 666 *.db
chmod 777 data/
```

### 5. Node.js 相关错误

如果遇到 pywencai 相关错误，进入容器检查：
```bash
docker exec -it agentsstock1 bash
node --version
npm --version
```

### 6. 内存不足

增加 Docker 可用内存（Docker Desktop → Settings → Resources）：
- 推荐至少 4GB RAM
- 推荐至少 2GB Swap

或在 docker-compose.yml 中限制：
```yaml
services:
  agentsstock:
    # ... 其他配置
    deploy:
      resources:
        limits:
          memory: 2G
        reservations:
          memory: 1G
```

## 🔒 安全建议

1. **保护 .env 文件**
   - 不要提交到 Git
   - 设置适当的文件权限：`chmod 600 .env`

2. **使用 secrets（生产环境）**
```yaml
services:
  agentsstock:
    secrets:
      - deepseek_api_key
    environment:
      - DEEPSEEK_API_KEY_FILE=/run/secrets/deepseek_api_key

secrets:
  deepseek_api_key:
    file: ./secrets/deepseek_api_key.txt
```

3. **定期更新镜像**
```bash
docker-compose pull
docker-compose up -d
```

## 🌐 反向代理（可选）

如需通过域名访问，可配置 Nginx：

```nginx
server {
    listen 80;
    server_name yourdomain.com;

    location / {
        proxy_pass http://localhost:8503;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
```

## 📊 性能优化

1. **使用构建缓存**
```bash
docker-compose build --no-cache  # 清除缓存重建
```

2. **多阶段构建（高级）**
可以修改 Dockerfile 使用多阶段构建减小镜像体积。

3. **资源限制**
```yaml
services:
  agentsstock:
    deploy:
      resources:
        limits:
          cpus: '2'
          memory: 2G
```

## 📝 生产环境部署建议

1. 使用环境变量管理敏感信息
2. 配置日志轮转
3. 设置健康检查和自动重启
4. 使用 Docker volumes 而非 bind mounts
5. 配置备份策略（数据库文件）
6. 使用 HTTPS（配合 Nginx/Caddy）
7. 配置防火墙规则

## 🆘 获取帮助

如遇到问题：
1. 查看日志：`docker-compose logs -f`
2. 检查容器状态：`docker ps -a`
3. 查看 GitHub Issues
4. 联系：ws3101001@126.com

---

**享受 Docker 带来的便捷部署体验！** 🚀

