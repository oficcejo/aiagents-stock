# 🤖 复合多AI智能体股票团队分析系统

基于Python + Streamlit + DeepSeek的智能股票分析系统，模拟证券公司分析师团队，提供全方位的股票投资分析和决策建议。
<img width="1910" height="923" alt="image" src="https://github.com/user-attachments/assets/b482a2bf-6349-476c-9ba4-237960cc632a" />
<img width="1910" height="923" alt="image" src="https://github.com/user-attachments/assets/b2ac735b-5a3a-478c-955d-1a37eb705bb1" />

## ✨ 更新说明
### 增加股票监测功能，增加历史记录中个股导入到监测板块

## ✨ 功能特色

### 🎯 多维度分析
- **技术面分析**：趋势判断、技术指标、支撑阻力位分析
- **基本面分析**：财务指标、估值分析、行业研究
- **资金面分析**：资金流向、主力行为、市场情绪
- **风险管理**：风险识别、风险评估、风险控制策略
- **市场情绪**：投资者情绪、热点板块、消息面分析

### 🤖 AI智能体团队
- **技术分析师**：专注技术指标和图表分析
- **基本面分析师**：专注公司价值和行业研究（含13+财务指标）
- **资金面分析师**：专注资金流向和主力行为
- **风险管理师**：专注风险识别和控制
- **市场情绪分析师**：专注市场心理和热点追踪

### 📊 完整分析流程
1. 📈 获取股票数据（支持A股和美股）
2. 📊 获取详细财务数据（三大报表+财务指标）
3. 🔍 多智能体并行分析
4. 🤝 团队综合讨论
5. 📋 最终投资决策
6. 🎯 操作建议和风险提示
7. 📄 PDF报告导出
<img width="1910" height="923" alt="image" src="https://github.com/user-attachments/assets/836d758f-df6d-44a1-b64a-fd6ad442cb0f" />
<img width="1910" height="923" alt="image" src="https://github.com/user-attachments/assets/903a64c7-7018-44dd-aa87-af4f7904048c" />
<img width="1910" height="923" alt="image" src="https://github.com/user-attachments/assets/d9878153-d743-4d65-9575-62ac37f8cbfb" />
<img width="1910" height="923" alt="image" src="https://github.com/user-attachments/assets/1c1c27af-1fe8-46e8-9e4a-68ead604a24d" />
<img width="1910" height="923" alt="image" src="https://github.com/user-attachments/assets/242ee212-ba6c-4e0a-ae16-47aff3f356e6" />


### 🔍 实时监测功能
- **智能监测**：自动监控股票价格变动
- **关键位置提醒**：进场区间、止盈位、止损位触发通知
- **自定义间隔**：30秒至300秒灵活设置
- **多种通知方式**：网页提醒 + 邮件通知
- **卡片式管理**：直观的股票监测卡片展示
- **完整功能**：添加、编辑、删除、启停、通知开关
- **一键加入监测**：支持历史记录中一键加入监测功能
<img width="1910" height="923" alt="image" src="https://github.com/user-attachments/assets/ca39f4c6-5922-4df5-b38f-8a45a3dbdfb9" />
<img width="1910" height="923" alt="image" src="https://github.com/user-attachments/assets/1463fc59-05aa-4201-a4aa-15e6da373cb7" />
<img width="1910" height="923" alt="image" src="https://github.com/user-attachments/assets/a283fcf9-5ea9-42e5-876f-82920a74dd33" />


### 🤖 量化交易功能（MiniQMT集成）
- **自动交易执行**：监测触发后自动下单
- **智能仓位管理**：灵活配置单股最大仓位比例
- **多种订单类型**：市价单、限价单、止损单支持
- **风险控制**：自动止损、止盈功能
- **持仓监控**：实时查看持仓和盈亏
- **预留接口**：完整的MiniQMT对接接口，可对接真实交易
<img width="1907" height="919" alt="image" src="https://github.com/user-attachments/assets/ea499f1e-5c11-4596-a359-d14de77bff9b" />
<img width="1910" height="923" alt="image" src="https://github.com/user-attachments/assets/a85defbf-321a-4fe2-b491-6855f2aa366c" />
<img width="1869" height="906" alt="image" src="https://github.com/user-attachments/assets/d59de299-6300-4669-9902-7754da7407db" />

### 📧 邮件通知系统
- **多邮箱支持**：QQ邮箱、163邮箱、Gmail等
- **触发条件**：
  - 价格进入进场区间
  - 达到止盈位
  - 触及止损位
- **测试功能**：一键测试邮件配置
- **历史记录**：完整的通知历史查询
<img width="1910" height="923" alt="image" src="https://github.com/user-attachments/assets/a1a3c1ca-f97f-43eb-a043-1011c09e06d0" />
<img width="1910" height="923" alt="image" src="https://github.com/user-attachments/assets/1808f284-e922-4eac-bfea-134996de93f1" />
### 🎨 现代化界面
- **渐变背景设计**：专业的紫色渐变配色
- **响应式布局**：支持桌面、平板、手机
- **实时数据可视化**：Plotly交互式图表
- **卡片式展示**：清晰的信息模块化
- **动画交互**：流畅的悬停和过渡效果

## 🚀 快速开始

### 1. 环境要求
- Python 3.8+
- 稳定的网络连接
- DeepSeek API Key

### 2. 安装依赖
```bash
pip install -r requirements.txt
```

### 3. 配置API

#### 方法一：使用环境变量文件（推荐）
1. 复制环境变量模板文件：
```bash
# Windows (PowerShell)
Copy-Item .env.example .env

# 或者使用命令
cp .env.example .env
```

2. 编辑 `.env` 文件，设置您的配置：
```env
# DeepSeek API配置（必需）
DEEPSEEK_API_KEY=your_actual_deepseek_api_key_here

# 邮件通知配置（可选）
EMAIL_ENABLED=false
SMTP_SERVER=smtp.qq.com
SMTP_PORT=587
EMAIL_FROM=your_email@qq.com
EMAIL_PASSWORD=your_authorization_code
EMAIL_TO=receiver@example.com

# MiniQMT量化交易配置（可选）
MINIQMT_ENABLED=false
MINIQMT_ACCOUNT_ID=your_account_id
MINIQMT_HOST=127.0.0.1
MINIQMT_PORT=58610
```


#### 方法二：设置系统环境变量
您也可以直接在系统环境变量中设置：
- 变量名：`DEEPSEEK_API_KEY`
- 变量值：您的API密钥

**注意**：环境变量文件的优先级高于系统环境变量。

### 4. 启动系统
```bash
python run.py
```
或者直接运行：
```bash
streamlit run app.py
```

### 5. 访问系统
打开浏览器访问：http://localhost:8501

## 📊 使用指南

### 股票代码格式(美股暂不支持)
- **美股**：AAPL, MSFT, GOOGL, TSLA, NVDA
- **A股**：000001, 600036, 000002, 600519

### 分析流程
1. 在输入框中输入股票代码
2. 点击"开始分析"按钮
3. 等待AI分析师团队完成分析
4. 查看各维度分析报告
5. 阅读团队讨论结果
6. 获取最终投资决策

### 结果解读
- **投资评级**：买入/持有/卖出
- **目标价位**：预期价格目标
- **操作建议**：具体交易策略
- **进出场位置**：关键价位点
- **止盈止损**：风险控制位置
- **风险提示**：主要风险因素

### 实时监测功能

#### 快速开始
1. 点击侧边栏"📊 实时监测"按钮
2. 在监测管理页面点击"添加监测股票"
3. 填写股票信息和监测参数
4. 点击"▶️ 启动监测"开始自动监控

#### 添加监测股票
**必填信息**：
- **股票代码**：6位A股代码或美股字母代码
- **股票名称**：便于识别
- **投资评级**：买入/持有/卖出

**监测参数**：
- **进场区间**：设置最小和最大价格
  - 当股票价格进入该区间时触发通知
  - 用于把握最佳买入时机
- **止盈位**：目标卖出价格
  - 价格达到或超过该值时提醒
  - 帮助锁定收益
- **止损位**：最大亏损价格
  - 价格跌破该值时立即提醒
  - 控制投资风险
- **检查间隔**：30-300秒
  - 监测频率，建议60秒以上
  - 避免过于频繁的API调用

#### 管理监测股票
**查看功能**：
- 📊 实时价格显示
- 📈 涨跌幅展示
- ⏰ 最后检查时间
- 🔔 通知状态

**操作按钮**：
- 🔄 **更新**：手动刷新当前价格
- ✏️ **编辑**：修改监测参数
- 🔔/🔕 **通知开关**：启用/禁用通知
- 🗑️ **删除**：移除监测

**批量操作**：
- ▶️ 启动监测：开始后台自动监控所有股票
- ⏹️ 停止监测：暂停监控服务
- 🔄 刷新状态：更新显示信息

#### 通知系统

**网页通知**：
- 自动在界面显示提醒
- 实时查看通知历史
- 支持标记已读和清空

**邮件通知配置**：

1. **编辑.env文件**：
```env
EMAIL_ENABLED=true
SMTP_SERVER=smtp.qq.com
SMTP_PORT=587
EMAIL_FROM=your_email@qq.com
EMAIL_PASSWORD=your_authorization_code
EMAIL_TO=receiver@example.com
```

2. **获取邮箱授权码**：
   - **QQ邮箱**：设置 → 账户 → POP3/IMAP/SMTP → 生成授权码
   - **163邮箱**：设置 → POP3/SMTP/IMAP → 开启服务 → 设置授权密码
   - **Gmail**：开启两步验证 → 生成应用专用密码

3. **测试邮件配置**：
   - 进入"通知管理"区域
   - 点击"📧 发送测试邮件"
   - 检查收件箱（含垃圾箱）

**通知触发条件**：
- ✅ 价格进入进场区间 → 进场提醒
- ✅ 价格达到止盈位 → 止盈提醒
- ✅ 价格跌破止损位 → 止损提醒

#### 使用技巧

**参数设置建议**：
- **进场区间**：根据技术分析设定支撑位和阻力位
- **止盈位**：建议设置10-20%的盈利目标
- **止损位**：建议设置5-10%的止损线
- **检查间隔**：
  - 长线投资：180-300秒
  - 短线交易：30-60秒

**监测策略**：
1. 分析后添加到监测列表
2. 设置合理的进场区间等待买入信号
3. 买入后调整为止盈/止损监测
4. 收到通知后及时决策

**注意事项**：
- ⚠️ 监测间隔不要设置太短，避免频繁API调用
- ⚠️ 邮件通知有延迟，不适用于高频交易
- ⚠️ 定期检查监测服务运行状态
- ⚠️ 及时处理触发的通知，避免错过时机

## 🏗️ 系统架构

```
AI股票分析系统
├── app.py                    # Streamlit主界面
├── stock_data.py             # 股票数据获取模块
├── deepseek_client.py        # DeepSeek API客户端
├── ai_agents.py              # AI智能体分析模块
├── monitor_manager.py        # 监测管理界面
├── monitor_service.py        # 监测服务后台
├── monitor_db.py             # 监测数据库管理
├── notification_service.py   # 通知服务（邮件/界面）
├── miniqmt_interface.py      # MiniQMT量化交易接口 ⭐️
├── pdf_generator.py          # PDF报告生成
├── database.py               # 分析记录数据库
├── config.py                 # 配置文件
├── requirements.txt          # 依赖包列表
└── run.py                    # 启动脚本
```

### 核心模块说明

#### 📈 股票数据模块 (stock_data.py)
- 支持A股和美股数据获取
- 集成yfinance和akshare数据源
- 自动计算技术指标（MA、RSI、MACD、KDJ等）
- 获取详细财务数据（三大报表+13+财务指标）
- 数据清洗和格式化

#### 🤖 AI智能体模块 (ai_agents.py)
- 多个专业分析师AI角色
- 并行分析处理
- 团队讨论机制
- 最终决策生成
- 财务数据深度解读

#### 🔗 API客户端 (deepseek_client.py)
- DeepSeek API封装
- 智能对话管理
- 错误处理和重试
- 响应格式解析
- 支持多模型切换

#### 🔍 监测管理模块 (monitor_manager.py)
- 股票监测管理界面
- 添加/编辑/删除监测
- 卡片式展示
- 搜索和筛选功能
- 通知历史管理

#### ⚙️ 监测服务模块 (monitor_service.py)
- 后台监测线程
- 定时价格检查
- 触发条件判断
- 自动通知发送
- 启动/停止控制

#### 💾 监测数据库 (monitor_db.py)
- SQLite数据持久化
- 监测股票表
- 价格历史表
- 通知记录表
- CRUD操作接口

#### 📧 通知服务模块 (notification_service.py)
- 邮件通知发送
- 网页通知展示
- 多邮箱支持（QQ/163/Gmail）
- 通知历史管理
- 配置测试功能

#### 🤖 量化交易模块 (miniqmt_interface.py) ⭐️ 新增
- MiniQMT接口对接
- 自动交易执行
- 仓位管理
- 风险控制
- 订单管理
- 持仓监控
- 预留接口实现

#### 📄 PDF生成模块 (pdf_generator.py)
- 专业分析报告生成
- 中文字体支持
- 完整分析内容
- 一键下载功能

#### 🎨 前端界面 (app.py)
- 现代化渐变UI设计
- 响应式布局
- 三大功能模块（分析/监测/历史）
- 实时数据可视化
- 交互式操作
- 美观的动画效果

## 📋 技术特性

### 数据源
- **美股数据**：Yahoo Finance (yfinance)
- **A股数据**：AKShare免费接口
- **技术指标**：TA-Lib技术分析库

### AI模型
- **语言模型**：DeepSeek Chat API
- **分析框架**：多智能体协作
- **决策逻辑**：综合评分机制

### 可视化
- **图表库**：Plotly交互式图表
- **K线图**：蜡烛图with技术指标
- **指标图**：RSI、MACD、布林带等

### 性能优化
- **数据缓存**：Streamlit缓存机制
- **异步处理**：并行分析提升效率
- **错误处理**：完善的异常处理机制

## ⚙️ 高级配置

### API配置
```env
# .env 文件
DEEPSEEK_API_KEY=your_api_key
DEEPSEEK_BASE_URL=https://api.deepseek.com/v1
```

**重要提示**：
- 请将 `.env.template` 复制为 `.env` 文件
- 在 `.env` 文件中填写实际的API密钥
- 不要将 `.env` 文件提交到版本控制系统

### 数据配置
```python
DEFAULT_PERIOD = "1y"      # 默认数据周期
DEFAULT_INTERVAL = "1d"    # 默认数据间隔
```

### 系统参数
- **缓存时间**：300秒（5分钟）
- **API超时**：30秒
- **最大重试**：3次

## 🛠️ 故障排除

### 常见问题

1. **API Key错误**
   - 检查.env文件中的DEEPSEEK_API_KEY设置
   - 确保.env文件存在且格式正确
   - 确保API Key有效且有足够余额

2. **股票数据获取失败**
   - 检查网络连接
   - 确认股票代码格式正确（A股6位数字，美股字母代码）
   - 可能是数据源临时不可用，稍后重试

3. **财务数据获取失败**
   - 部分新股可能没有完整财务数据
   - 网络问题可能导致数据获取超时
   - 系统会自动处理，继续进行其他分析

4. **依赖包安装失败**
   - 使用 `pip install -r requirements.txt`
   - 如有问题，尝试手动安装单个包
   - 确保Python版本为3.8+

5. **页面加载缓慢**
   - 首次运行需要下载数据，请耐心等待
   - 系统有5分钟缓存，重复查询会更快
   - 财务数据获取较慢，约需10-20秒

6. **分析过程中出错**
   - 检查网络连接是否稳定
   - 查看终端输出的详细错误信息
   - 尝试重新启动应用

7. **MiniQMT连接失败**
   - 确认MiniQMT客户端已启动
   - 检查账户已登录
   - 验证账户ID配置正确
   - 确认网络连接正常
   - 查看 `MINIQMT_INTEGRATION_GUIDE.md` 详细指南

8. **量化交易未执行**
   - 确认量化功能已启用
   - 检查MiniQMT连接状态
   - 验证监测服务是否运行
   - 查看通知记录中的错误信息
   - 确认交易时间在交易日内

### 日志调试
系统运行时会在控制台输出详细日志，可用于问题诊断。如遇到错误，请查看终端输出。

### 错误报告
如发现bug，请查看 `BUGFIX.md` 文件了解已知问题和解决方案。

## 📜 免责声明

本系统仅供学习和研究使用，不构成投资建议。股票投资有风险，入市需谨慎。使用本系统进行投资决策的风险由用户自行承担。

## 🤝 贡献指南

欢迎提交Issue和Pull Request！

## 📄 许可证

MIT License

---

**享受AI驱动的智能股票分析体验！** 🚀📈任何疑问请留言或联系ws3101001@126.com
