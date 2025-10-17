# API配置问题修复说明

## 问题描述

用户遇到股票分析API调用失败，提示：
```
API调用失败: Error code: 401 - {'error': {'message': 'Authentication Fails, Your api key: ****a7fc is invalid'}}
```

虽然`.env`文件中已配置了新的API key，但系统仍在使用旧的key（结尾为`a7fc`）。

## 问题原因

1. **PowerShell环境变量中存在旧的API key**
   - 用户之前在系统环境变量中设置过旧的`DEEPSEEK_API_KEY`
   - 旧key: `sk-b6c714570b9844f392aa3812f3f7a7fc`

2. **python-dotenv默认行为**
   - `load_dotenv()`默认**不会覆盖**已存在的环境变量
   - 导致系统读取的是环境变量中的旧key，而非`.env`文件中的新key

3. **调用链路**
   ```
   .env文件 (新key) → load_dotenv() → 不覆盖环境变量 → config.py读取环境变量 (旧key) → deepseek_client使用旧key → API调用失败
   ```

## 修复方案

### 1. 修改 `config.py`

**修改前：**
```python
load_dotenv()
```

**修改后：**
```python
# 加载环境变量（override=True 强制覆盖已存在的环境变量）
load_dotenv(override=True)
```

### 2. 修改 `config_manager.py`

在`reload_config()`方法中也添加`override=True`：
```python
def reload_config(self):
    """重新加载配置（重新加载.env文件）"""
    from dotenv import load_dotenv
    # 强制覆盖已存在的环境变量
    load_dotenv(override=True)
```

### 3. 清除Python缓存

```bash
Remove-Item -Recurse -Force __pycache__
```

## 修复验证

运行测试脚本验证修复：
```bash
.\venv\Scripts\python.exe test_api_config.py
```

测试结果：
```
✅ .env文件存在
   .env中的API Key: sk-e32f5***********************2abe

⚠️ 环境变量中的API Key（加载前）: sk-b6c71***********************a7fc

✅ config.py读取到的API Key: sk-e32f5***********************2abe
✅ 环境变量已被覆盖: sk-e32f5***********************2abe
✅ config.py读取的key与.env文件一致！
✅ API调用成功！
```

## 影响范围

此修复影响所有使用API的模块：

### 1. 股票分析模块
- ✅ `ai_agents.py` - 个股分析
- ✅ `deepseek_client.py` - API客户端

### 2. 智策板块模块
- ✅ `sector_strategy_agents.py` - 板块分析
- ✅ `sector_strategy_engine.py` - 策略引擎

### 3. 主力选股模块
- ✅ `main_force_analysis.py` - 主力资金分析

### 4. UI和服务模块
- ✅ `app.py` - 主应用
- ✅ `monitor_service.py` - 监测服务

## 验证步骤

修复后，所有模块都会从`.env`文件读取正确的API key：

1. **启动应用**
   ```bash
   python run.py
   ```

2. **测试股票分析**
   - 在Web界面输入股票代码
   - 点击"开始分析"
   - 确认API调用成功

3. **测试智策板块**
   - 点击"智策板块"
   - 开始板块分析
   - 确认API调用成功

4. **测试主力选股**
   - 点击"主力选股"
   - 运行主力资金筛选
   - 确认API调用成功

## 预防措施

为避免将来再次出现此问题：

1. **优先使用.env文件配置**
   - 不要在系统环境变量中设置API key
   - 统一在`.env`文件中管理所有配置

2. **清除旧的环境变量**
   - Windows: 系统属性 → 高级 → 环境变量 → 删除`DEEPSEEK_API_KEY`
   - PowerShell临时清除: `Remove-Item Env:DEEPSEEK_API_KEY`

3. **重启应用生效**
   - 修改`.env`文件后，需要重启Streamlit应用
   - 或使用环境配置界面的"保存并重新加载"功能

## 技术细节

### python-dotenv 的 override 参数

```python
load_dotenv(override=True)
```

- `override=False` (默认): 不覆盖已存在的环境变量，优先使用系统环境变量
- `override=True`: 强制覆盖环境变量，优先使用`.env`文件中的值

### 配置优先级

**修复前：**
1. 系统环境变量 (最高优先级)
2. .env文件

**修复后：**
1. .env文件 (最高优先级)
2. 系统环境变量 (作为默认值)

## 相关文件

- `config.py` - 主配置文件
- `config_manager.py` - 配置管理器
- `.env` - 环境变量配置文件
- `test_api_config.py` - API配置测试脚本

## 修复日期

2025-10-17

## 测试人员

AI Assistant

## 状态

✅ 已修复并验证通过

