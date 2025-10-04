# ⚡ 快速修复指南

## 部署错误：proxies参数问题

### 🔴 错误信息
```
分析过程中出现错误: Client.init() got an unexpected keyword argument 'proxies'
```

### ✅ 快速解决（3步）

#### 步骤1：升级OpenAI库
```bash
pip install --upgrade openai
```

#### 步骤2：重新安装依赖
```bash
pip install -r requirements.txt --upgrade
```

#### 步骤3：重启应用
```bash
streamlit run app.py
```

---

## 其他常见问题快速修复

### 1. 模块未找到错误

**错误**：`ModuleNotFoundError: No module named 'xxx'`

**修复**：
```bash
pip install xxx
# 或重新安装所有依赖
pip install -r requirements.txt
```

### 2. API密钥错误

**错误**：`API Key未配置`

**修复**：
```bash
# 创建.env文件
cp .env.example .env

# 编辑.env文件，添加API密钥
# DEEPSEEK_API_KEY=your_api_key_here
```

### 3. 端口被占用

**错误**：`Address already in use`

**修复**：
```bash
# 使用其他端口
streamlit run app.py --server.port 8502
```

### 4. 数据库锁定错误

**错误**：`database is locked`

**修复**：
```bash
# 停止所有streamlit进程
pkill -f streamlit

# 删除锁文件
rm -f *.db-wal *.db-shm

# 重新启动
streamlit run app.py
```

### 5. 权限错误

**错误**：`Permission denied`

**修复**：
```bash
# 设置正确权限
chmod 666 *.db
chmod 755 .
```

### 6. 中文乱码

**错误**：PDF中文显示为方框

**修复**：
```bash
# Windows: 确保系统安装了中文字体
# Linux: 安装中文字体包
sudo apt-get install fonts-wqy-zenhei
```

### 7. 网络超时

**错误**：`Connection timeout`

**修复**：
- 检查网络连接
- 验证防火墙设置
- 尝试使用代理

### 8. 内存不足

**错误**：`MemoryError`

**修复**：
```bash
# 限制数据加载大小
# 或增加系统内存
# 或使用更小的数据周期
```

---

## 🚀 完整重置流程

如果多个问题同时出现，可以尝试完整重置：

```bash
# 1. 停止所有进程
pkill -f streamlit

# 2. 清理虚拟环境
rm -rf venv/

# 3. 创建新虚拟环境
python -m venv venv
source venv/bin/activate  # Linux/Mac
# 或
.\venv\Scripts\Activate.ps1  # Windows

# 4. 升级pip
pip install --upgrade pip

# 5. 重新安装依赖
pip install -r requirements.txt

# 6. 配置环境变量
cp .env.example .env
# 编辑.env文件添加API密钥

# 7. 重新启动
streamlit run app.py
```

---

## 📞 需要更多帮助？

1. 查看 `DEPLOYMENT_GUIDE.md` - 完整部署指南
2. 查看 `BUGFIX.md` - 详细错误记录
3. 查看 `README.md` - 使用说明
4. 检查GitHub Issues

---

**提示**：大多数问题都可以通过重新安装依赖或重启应用解决！

