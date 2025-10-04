# 🚀 部署指南

## 问题解决

### OpenAI库版本兼容性问题

**错误信息**：
```
Client.init() got an unexpected keyword argument 'proxies'
```

**原因**：
- OpenAI库版本过旧（1.3.0）
- 新版本API有变化，不再支持`proxies`参数

**解决方案**：

#### 方案1：升级依赖包（推荐）

```bash
# 1. 激活虚拟环境
source venv/bin/activate  # Linux/Mac
# 或
.\venv\Scripts\Activate.ps1  # Windows

# 2. 升级openai库
pip install --upgrade openai

# 3. 或者重新安装所有依赖
pip install -r requirements.txt --upgrade
```

#### 方案2：指定版本安装

```bash
pip install openai>=1.12.0
```

#### 方案3：清理后重新安装

```bash
# 1. 卸载旧版本
pip uninstall openai -y

# 2. 安装新版本
pip install openai

# 3. 重新安装所有依赖
pip install -r requirements.txt
```

## 📋 完整部署流程

### 1. 环境准备

```bash
# 克隆项目
git clone <your-repo-url>
cd agentsstock1

# 创建虚拟环境
python -m venv venv

# 激活虚拟环境
# Windows:
.\venv\Scripts\Activate.ps1
# Linux/Mac:
source venv/bin/activate
```

### 2. 安装依赖

```bash
# 安装所有依赖
pip install -r requirements.txt

# 如果遇到问题，逐个安装
pip install streamlit requests pandas numpy plotly
pip install yfinance akshare openai python-dotenv
pip install pytz ta reportlab peewee schedule
```

### 3. 配置环境变量

```bash
# 复制配置文件
cp .env.example .env

# 编辑.env文件
# Windows:
notepad .env
# Linux/Mac:
nano .env
```

在`.env`文件中配置：
```env
# DeepSeek API配置（必需）
DEEPSEEK_API_KEY=your_actual_api_key_here
DEEPSEEK_BASE_URL=https://api.deepseek.com/v1

# 邮件通知配置（可选）
EMAIL_ENABLED=false
SMTP_SERVER=smtp.qq.com
SMTP_PORT=587
EMAIL_FROM=your_email@qq.com
EMAIL_PASSWORD=your_authorization_code
EMAIL_TO=receiver@example.com
```

### 4. 测试运行

```bash
# 本地测试
streamlit run app.py

# 指定端口
streamlit run app.py --server.port 8501
```

### 5. 服务器部署

#### 使用Streamlit Cloud

1. 推送代码到GitHub
2. 登录 https://streamlit.io/cloud
3. 连接GitHub仓库
4. 在Settings中配置环境变量
5. 部署

#### 使用Docker

创建`Dockerfile`：
```dockerfile
FROM python:3.9-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

EXPOSE 8501

CMD ["streamlit", "run", "app.py", "--server.port=8501", "--server.address=0.0.0.0"]
```

构建和运行：
```bash
# 构建镜像
docker build -t stock-analysis .

# 运行容器
docker run -p 8501:8501 --env-file .env stock-analysis
```

#### 使用PM2（适用于VPS）

```bash
# 安装PM2
npm install -g pm2

# 创建启动脚本 start.sh
echo "streamlit run app.py --server.port 8501" > start.sh
chmod +x start.sh

# 使用PM2启动
pm2 start start.sh --name stock-analysis

# 保存PM2配置
pm2 save
pm2 startup
```

## 🔧 常见部署问题

### 1. 端口被占用

**错误**：`Address already in use`

**解决**：
```bash
# 更换端口
streamlit run app.py --server.port 8502
```

### 2. 依赖安装失败

**错误**：`No matching distribution found`

**解决**：
```bash
# 升级pip
pip install --upgrade pip

# 使用国内镜像源
pip install -r requirements.txt -i https://pypi.tuna.tsinghua.edu.cn/simple
```

### 3. API连接失败

**错误**：`Connection timeout`

**解决**：
- 检查网络连接
- 验证API Key是否正确
- 检查BASE_URL是否正确
- 检查防火墙设置

### 4. 中文字体问题（PDF生成）

**错误**：`Font not found`

**解决**：
```bash
# Linux服务器安装中文字体
sudo apt-get install fonts-wqy-zenhei fonts-wqy-microhei

# 或手动下载字体
wget https://github.com/adobe-fonts/source-han-sans/releases/download/2.004R/SourceHanSansCN.zip
unzip SourceHanSansCN.zip -d /usr/share/fonts/
fc-cache -fv
```

### 5. 数据库权限问题

**错误**：`Permission denied: stock_monitor.db`

**解决**：
```bash
# 设置正确的权限
chmod 666 stock_monitor.db stock_analysis.db
chmod 777 .  # 确保当前目录可写
```

### 6. 内存不足

**错误**：`MemoryError`

**解决**：
```bash
# 增加系统交换空间
sudo fallocate -l 2G /swapfile
sudo chmod 600 /swapfile
sudo mkswap /swapfile
sudo swapon /swapfile

# 或限制Streamlit内存使用
streamlit run app.py --server.maxUploadSize 100
```

## 🔐 安全建议

### 1. 保护敏感信息

```bash
# 确保.env文件在.gitignore中
echo ".env" >> .gitignore

# 不要在代码中硬编码密钥
# ❌ BAD
API_KEY = "sk-xxxxx"

# ✅ GOOD
API_KEY = os.getenv("DEEPSEEK_API_KEY")
```

### 2. 配置防火墙

```bash
# 只允许特定IP访问
# UFW (Ubuntu)
sudo ufw allow from YOUR_IP to any port 8501

# iptables
sudo iptables -A INPUT -p tcp --dport 8501 -s YOUR_IP -j ACCEPT
```

### 3. 使用HTTPS

```bash
# 使用nginx反向代理
sudo apt-get install nginx

# 配置nginx
sudo nano /etc/nginx/sites-available/stock-analysis
```

nginx配置：
```nginx
server {
    listen 80;
    server_name your-domain.com;

    location / {
        proxy_pass http://localhost:8501;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
        proxy_set_header Host $host;
    }
}
```

### 4. 定期更新

```bash
# 更新依赖包
pip list --outdated
pip install --upgrade package_name

# 更新系统
sudo apt-get update && sudo apt-get upgrade
```

## 📊 性能优化

### 1. 启用缓存

代码中已使用`@st.cache_data`装饰器

### 2. 配置Streamlit

创建`.streamlit/config.toml`：
```toml
[server]
port = 8501
enableCORS = false
enableXsrfProtection = true

[browser]
gatherUsageStats = false

[client]
showErrorDetails = false
```

### 3. 使用CDN

对于静态资源使用CDN加速

## 🔄 更新部署

```bash
# 拉取最新代码
git pull origin main

# 更新依赖
pip install -r requirements.txt --upgrade

# 重启服务
pm2 restart stock-analysis
# 或
docker restart stock-analysis
```

## 📝 监控和日志

### 查看日志

```bash
# PM2日志
pm2 logs stock-analysis

# Docker日志
docker logs stock-analysis

# Streamlit日志
tail -f ~/.streamlit/logs/*
```

### 监控性能

```bash
# 系统资源
htop

# PM2监控
pm2 monit

# Docker stats
docker stats stock-analysis
```

## 🆘 获取帮助

如果遇到其他问题：
1. 查看BUGFIX.md
2. 查看GitHub Issues
3. 检查系统日志
4. 联系技术支持

---

**最后更新**：2025-10-03

