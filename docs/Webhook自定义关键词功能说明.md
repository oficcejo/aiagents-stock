# Webhook自定义关键词功能说明

## 功能概述

系统现已支持自定义Webhook关键词配置，用户可以根据自己的钉钉/飞书机器人安全设置灵活配置关键词。

## 配置方法

### 1. 在.env文件中配置

```env
# ========== Webhook通知配置（可选）==========
WEBHOOK_ENABLED="true"
WEBHOOK_TYPE="dingtalk"
WEBHOOK_URL="https://oapi.dingtalk.com/robot/send?access_token=YOUR_TOKEN"
WEBHOOK_KEYWORD="aiagents通知"
```

### 2. 配置说明

| 配置项 | 说明 | 示例 |
|-------|------|------|
| WEBHOOK_ENABLED | 是否启用Webhook | true / false |
| WEBHOOK_TYPE | Webhook类型 | dingtalk（钉钉）/ feishu（飞书）|
| WEBHOOK_URL | Webhook地址 | 机器人Webhook完整URL |
| WEBHOOK_KEYWORD | 自定义关键词 | aiagents通知（或您机器人设置的任何关键词）|

## 钉钉机器人关键词设置

### 步骤1：创建钉钉自定义机器人
1. 打开钉钉群聊
2. 点击右上角"..."  → 机器人 → 添加机器人
3. 选择"自定义"机器人

### 步骤2：安全设置
1. 安全设置选择：**自定义关键词**
2. 输入关键词：**aiagents通知**（或您自己定义的关键词）
3. 复制Webhook地址

![钉钉关键词设置](https://user-images.githubusercontent.com/...)

### 步骤3：配置到系统
将关键词和Webhook地址配置到`.env`文件中：

```env
WEBHOOK_KEYWORD="aiagents通知"
WEBHOOK_URL="https://oapi.dingtalk.com/robot/send?access_token=YOUR_TOKEN"
```

**重要提示**：
- `.env`文件中的关键词必须与钉钉机器人设置的关键词完全一致
- 如果不匹配，消息将发送失败
- 如果关键词为空，则不会在消息中添加关键词前缀

## 飞书机器人配置

飞书机器人通常不需要关键词，可以将WEBHOOK_KEYWORD留空或使用默认值：

```env
WEBHOOK_TYPE="feishu"
WEBHOOK_KEYWORD=""
```

## 消息格式

### 钉钉消息示例

**有关键词时：**
```markdown
标题：aiagents通知 - 000001 平安银行

### aiagents通知 - 股票监测提醒

**股票代码**: 000001
**股票名称**: 平安银行
...
```

**无关键词时：**
```markdown
标题：000001 平安银行

### 股票监测提醒

**股票代码**: 000001
**股票名称**: 平安银行
...
```

## 测试配置

配置完成后，运行测试工具验证：

```bash
# Windows
.\venv\Scripts\python.exe test_notification_config.py

# Linux/Mac  
python test_notification_config.py
```

**成功输出示例：**
```
============================================================
[Webhook] 测试Webhook配置
============================================================

当前配置:
  - 启用状态: [已启用]
  - Webhook类型: dingtalk
  - 配置完整性: [完整]

[钉钉] 正在发送Webhook...
[成功] 钉钉Webhook发送成功
[成功] 钉钉Webhook测试成功！请检查钉钉群消息。
```

## 常见问题

### Q1: 提示"关键词不匹配"

**原因**：
- .env文件中的WEBHOOK_KEYWORD与钉钉机器人设置不一致
- .env文件编码问题导致关键词乱码

**解决方案**：
1. 检查钉钉机器人的关键词设置
2. 确保.env文件使用UTF-8编码
3. 运行`fix_env.py`重新生成.env文件：
   ```bash
   python fix_env.py
   ```

### Q2: .env文件中文显示乱码

**原因**：
文件编码不是UTF-8

**解决方案**：
运行修复脚本：
```bash
python fix_env.py
```

### Q3: 如何修改关键词

**方法1：直接编辑.env文件**
1. 用支持UTF-8的编辑器（VS Code、Notepad++等）打开.env
2. 修改WEBHOOK_KEYWORD的值
3. 保存为UTF-8编码

**方法2：使用环境配置界面**
1. 启动应用
2. 进入"环境配置"页面
3. 修改"Webhook自定义关键词"
4. 保存配置

**方法3：使用配置管理器**
```python
from config_manager import config_manager

# 读取当前配置
config = config_manager.read_env()

# 修改关键词
config['WEBHOOK_KEYWORD'] = '您的新关键词'

# 保存配置
config_manager.write_env(config)
```

### Q4: 是否可以不使用关键词

**可以！**

如果您的钉钉机器人使用其他安全方式（如加签、IP白名单），可以将关键词设为空：

```env
WEBHOOK_KEYWORD=""
```

系统会自动检测，如果关键词为空，则不会在消息中添加关键词前缀。

## 更新日志

### v1.1 (2025-10-14)
- ✅ 新增WEBHOOK_KEYWORD配置项
- ✅ 支持自定义关键词
- ✅ 修复.env文件中文编码问题
- ✅ 优化消息格式，去除多余空格
- ✅ 提供fix_env.py工具修复编码问题

### v1.0 (2025-10-14)
- ✅ 初始版本
- ✅ 硬编码"aiagents通知"关键词

## 相关文件

- `.env` - 环境配置文件
- `.env.example` - 配置模板
- `fix_env.py` - 编码修复工具
- `config_manager.py` - 配置管理模块
- `notification_service.py` - 通知服务模块
- `sector_strategy_scheduler.py` - 定时任务模块
- `test_notification_config.py` - 测试工具

## 技术实现

### 配置读取流程

```python
# 1. 从环境变量读取
import os
from dotenv import load_dotenv
load_dotenv()
keyword = os.getenv('WEBHOOK_KEYWORD', 'aiagents通知')

# 2. 在notification_service中使用
class NotificationService:
    def _load_config(self):
        config['webhook_keyword'] = os.getenv('WEBHOOK_KEYWORD')
        
    def _send_dingtalk_webhook(self, notification):
        keyword = self.config.get('webhook_keyword', '')
        title_prefix = f"{keyword} - " if keyword else ""
        # ...构建消息
```

### 消息构建逻辑

```python
# 如果有关键词
if keyword:
    title = f"{keyword} - {notification['symbol']} {notification['name']}"
    text = f"### {keyword} - 股票监测提醒\n..."
else:
    title = f"{notification['symbol']} {notification['name']}"
    text = f"### 股票监测提醒\n..."
```

## 总结

现在系统完全支持自定义Webhook关键词，用户可以根据自己的需求灵活配置：

✅ **灵活性**：支持任意自定义关键词  
✅ **兼容性**：支持钉钉和飞书  
✅ **易用性**：简单配置即可使用  
✅ **稳定性**：自动处理编码问题  

祝您使用愉快！

