# 🔧 系统设置指南

## 📋 安装步骤

### 1. 安装Python依赖
```bash
pip install -r requirements.txt
```

### 2. 配置API密钥

在 `config.py` 文件中设置您的DeepSeek API密钥：

```python
# config.py
import os
from dotenv import load_dotenv

# 加载环境变量
load_dotenv()

# DeepSeek API配置
DEEPSEEK_API_KEY = "sk-xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx"  # 在这里输入您的API密钥
DEEPSEEK_BASE_URL = "https://api.deepseek.com/v1"
```

### 3. 获取DeepSeek API密钥

1. 访问 [DeepSeek官网](https://platform.deepseek.com/)
2. 注册账号并登录
3. 进入API管理页面
4. 创建新的API密钥
5. 复制密钥并设置到config.py中

### 4. 启动系统

方式一：使用启动脚本
```bash
python run.py
```

方式二：直接启动Streamlit
```bash
streamlit run app.py
```

### 5. 访问系统
打开浏览器访问：http://localhost:8501

## 🧪 测试建议

### 测试用例
1. **美股测试**：输入 `AAPL`
2. **A股测试**：输入 `000001`
3. **错误处理测试**：输入无效代码

### 预期结果
- 成功获取股票基本信息
- 显示股价走势图表
- 生成5个AI分析师报告
- 产生团队讨论结果
- 输出最终投资决策

## ⚠️ 注意事项

1. **API配额**：注意DeepSeek API的使用配额
2. **网络要求**：需要稳定的网络连接
3. **首次运行**：第一次运行可能需要较长时间
4. **数据源**：依赖第三方数据源，可能有延迟

## 🔍 故障排除

### 常见错误及解决方案

1. **模块导入错误**
   ```bash
   pip install --upgrade -r requirements.txt
   ```

2. **API密钥错误**
   - 检查config.py中的密钥设置
   - 确保密钥格式正确且有效

3. **数据获取失败**
   - 检查网络连接
   - 确认股票代码正确

4. **页面无法访问**
   - 检查端口8501是否被占用
   - 尝试使用其他端口：`streamlit run app.py --server.port 8502`
