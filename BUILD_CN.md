# 🚀 Docker国内源快速构建指南

## ✨ 特点

- ⚡ **极速构建**：4-6分钟完成（vs 官方源20-35分钟）
- 🇨🇳 **全国内源**：所有依赖从国内镜像下载
- 🔒 **稳定可靠**：无需配置复杂的apt源
- 💪 **多架构支持**：支持x64和arm64

## 📋 一键构建

```bash
# 克隆项目（如果还没有）
git clone <your-repo-url>
cd agentsstock1

# 配置环境变量
cp .env.example .env
# 编辑 .env，填入 DEEPSEEK_API_KEY

# 构建镜像（使用国内源版）
docker build -f "Dockerfile国内源版" -t agentsstock1:latest .

# 运行容器
docker run -d \
  -p 8503:8501 \
  -v $(pwd)/.env:/app/.env \
  --name agentsstock1 \
  agentsstock1:latest

# 访问应用
# 浏览器打开: http://localhost:8503
```

## 🌐 使用的国内镜像源

| 组件 | 镜像源 | 说明 |
|------|--------|------|
| 基础镜像 | 华为云 | Python 3.12 |
| 系统包 | 阿里云 | Debian bookworm |
| Node.js | 淘宝镜像 | v18.20.4 LTS |
| npm包 | 淘宝镜像 | npmmirror |
| Python包 | 清华大学 | PyPI镜像 |

## ⏱️ 预期构建时间

```
[1/11] 下载基础镜像...        ✅ ~1分钟
[2/11] 配置Debian源...        ✅ <5秒
[3/11] 设置工作目录...        ✅ <1秒
[4/11] 安装系统依赖...        ✅ ~45秒
[5/11] 下载Node.js二进制...   ✅ ~15秒  ⭐
[6/11] 验证Node.js...         ✅ <1秒
[7/11] 配置npm镜像...         ✅ <1秒
[8/11] 复制requirements...    ✅ <1秒
[9/11] 安装Python依赖...      ✅ ~2.5分钟
[10/11] 复制项目文件...       ✅ ~2秒
[11/11] 创建数据目录...       ✅ <1秒

✅ 总计: 约 4-6 分钟
```

## 🔧 常用命令

```bash
# 查看日志
docker logs -f agentsstock1

# 停止容器
docker stop agentsstock1

# 启动容器
docker start agentsstock1

# 重启容器
docker restart agentsstock1

# 删除容器
docker rm -f agentsstock1

# 删除镜像
docker rmi agentsstock1:latest

# 进入容器调试
docker exec -it agentsstock1 bash
```

## 🐛 故障排查

### 构建失败：网络错误
```bash
# 检查网络连接
ping mirrors.aliyun.com
ping registry.npmmirror.com
ping pypi.tuna.tsinghua.edu.cn

# 如果网络正常但仍失败，尝试清理缓存重建
docker build --no-cache -f "Dockerfile国内源版" -t agentsstock1:latest .
```

### Node.js下载失败
```bash
# 手动验证下载链接是否可访问
curl -I https://registry.npmmirror.com/-/binary/node/v18.20.4/node-v18.20.4-linux-x64.tar.gz
```

### Python依赖安装超时
```dockerfile
# 已设置超时1000秒，如仍超时可增加：
pip install --no-cache-dir --default-timeout=2000 -r requirements.txt
```

## 📊 验证构建

```bash
# 检查Node.js版本
docker run --rm agentsstock1:latest node --version
# 预期: v18.20.4

# 检查npm版本
docker run --rm agentsstock1:latest npm --version
# 预期: 10.7.0

# 检查Python版本
docker run --rm agentsstock1:latest python --version
# 预期: Python 3.12.x

# 检查已安装的Python包
docker run --rm agentsstock1:latest pip list | grep streamlit
```

## 🎯 性能对比

| 构建方式 | 构建时间 | 网络要求 | 稳定性 |
|---------|---------|---------|-------|
| 官方源 | 20-35分钟 | 需要翻墙/国际网络 | 中等 |
| **国内源** | **4-6分钟** | **仅需国内网络** | **高** ⭐ |

## 📚 详细文档

- [DOCKER_CN_BUILD_GUIDE.md](docs/DOCKER_CN_BUILD_GUIDE.md) - 完整构建指南
- [DOCKER_DEPLOYMENT.md](docs/DOCKER_DEPLOYMENT.md) - Docker部署文档

## 💡 提示

1. **首次构建较慢**：需要下载基础镜像和所有依赖
2. **后续构建很快**：Docker会缓存已完成的层
3. **修改代码无需重建**：使用 `-v` 挂载代码目录即可
4. **生产环境建议**：固定版本标签，如 `agentsstock1:v1.0.0`

---

**享受极速Docker构建！** 🚀

