# 🚀 快速配置指南

## 1️⃣ 基础配置（必需）

### 安装依赖
```bash
pip install -r requirements.txt
```

### 配置API密钥
在 `.env` 文件中添加：
```env
DEEPSEEK_API_KEY=your_api_key_here
```

### 启动系统
```bash
streamlit run app.py
```

访问：http://localhost:8501

---

## 2️⃣ 邮件通知配置（可选）

### QQ邮箱（推荐）

#### 第一步：获取授权码
1. 登录 QQ 邮箱：https://mail.qq.com
2. 设置 → 账户 → POP3/IMAP/SMTP/Exchange
3. 开启"IMAP/SMTP服务"
4. 生成授权码（16位）
5. 保存授权码备用

#### 第二步：配置.env文件
在 `.env` 文件中添加：
```env
EMAIL_ENABLED=true
SMTP_SERVER=smtp.qq.com
SMTP_PORT=587
EMAIL_FROM=your_email@qq.com
EMAIL_PASSWORD=your_16_digit_code
EMAIL_TO=receiver@example.com
```

#### 第三步：测试邮件
1. 进入"实时监测"页面
2. 滚动到"通知管理"区域
3. 点击"📧 发送测试邮件"
4. 检查收件箱（包括垃圾邮件箱）

### 163邮箱

#### 配置示例
```env
EMAIL_ENABLED=true
SMTP_SERVER=smtp.163.com
SMTP_PORT=465
EMAIL_FROM=your_email@163.com
EMAIL_PASSWORD=your_authorization_code
EMAIL_TO=receiver@example.com
```

**注意**：163邮箱推荐使用465端口（SSL）

---

## 3️⃣ 使用监测功能

### 添加监测股票
1. 进入"实时监测"页面
2. 填写股票信息：
   - 股票代码（如：600519）
   - 股票名称
   - 投资评级
3. 设置关键位置：
   - 进场区间（最小-最大价格）
   - 止盈位
   - 止损位
4. 选择监测间隔（30-300秒）
5. 开启邮件通知开关
6. 点击"添加监测"

### 启动监测服务
- 点击"▶️ 启动监测"按钮
- 系统开始后台自动监测
- 价格触发条件时自动发送通知

### 管理监测股票
- **更新**：手动刷新股票价格
- **编辑**：修改监测参数
- **通知开关**：启用/禁用通知
- **删除**：移除监测

---

## 4️⃣ 导出PDF报告

1. 完成股票分析后
2. 滚动到分析结果底部
3. 点击"📄 生成并下载PDF报告"
4. 等待生成完成
5. 点击下载链接保存报告

---

## ❓ 常见问题

### 邮件无法发送？
- ✅ 检查是否使用授权码（不是登录密码）
- ✅ 确认SMTP服务器和端口正确
- ✅ 尝试切换端口（587 ↔ 465）
- ✅ 检查网络连接和防火墙

### 监测不工作？
- ✅ 确认监测服务已启动
- ✅ 检查股票代码格式是否正确
- ✅ 查看系统日志中的错误信息

### PDF中文乱码？
- ✅ 系统已自动注册中文字体
- ✅ 确保Windows系统字体完整
- ✅ 重新生成PDF报告

---

## 📞 获取帮助

- 查看 README.md 了解详细功能
- 查看 CHANGELOG.md 了解更新内容
- 查看界面内的配置说明

---

**祝您使用愉快！📈**

