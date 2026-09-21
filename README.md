# 🤖 复合多AI智能体股票团队分析系统

> 基于 **Python + Streamlit + 多AI智能体** 的智能股票分析系统——模拟证券公司分析师团队，覆盖 A股 / 港股 / 美股，提供分析、选股、监测、盯盘、量化交易与通知推送的全流程投资决策支持。

## 🙏 初心

在股市摸爬滚打多年，自学自编各种指标，花冤枉钱学习了各种战法各种策略，也曾入各种小班，总是赚少赔多，逐渐失去在股市玩的信心。自从去年 deepseek 上市，一直探索用 AI 辅助分析，近日受 tradingagents 项目启发（感谢原作），多 agent 结合跟踪主力资金战法（某指每年收费6000rmb），用各种 AI 辅助编程，拼凑了这么个小程序。根据软件提供的辅助信息，实盘测试胜率还是挺高的，并且逐步形成了自己的交易系统，近一个月来，账户也慢慢在扭亏为盈。

开源此软件的目的，就是为了使像我一样的小散，不再迷茫。也许这个软件不能让你发大财，但是它能给你足够的信心。

**⚠️ 股市有风险，入市需谨慎！**

## 💬 社区与教程

| 资源 | 链接 |
|---|---|
| QQ交流群1 | 1059277514 |
| QQ交流群2 | 975536948 |
| B站本地部署教程 | https://www.bilibili.com/video/BV1qHFPz9EXY/ |
| B站Docker部署教程 | https://www.bilibili.com/video/BV1j2FNz4EAi/ |
| 股票知识讲解合集 | https://www.bilibili.com/video/BV1Y2FGzzEeS/ |
| 投资认知提升合集 | https://www.bilibili.com/video/BV1ugBMBAEbW |
| 价值投资核心逻辑 | https://www.bilibili.com/video/BV1eJfxBrEjZ |

## 📸 界面预览

<img width="1910" height="923" alt="image" src="https://github.com/user-attachments/assets/fe366e1d-2352-46db-a3cc-6f147ee6d9d9" />
<img width="1910" height="923" alt="image" src="https://github.com/user-attachments/assets/112e9e34-381e-4e61-b7b6-6614260b2594" />
<img width="1910" height="923" alt="image" src="https://github.com/user-attachments/assets/46e36075-2f08-4113-bd1d-913ef4dd279c" />
<img width="1910" height="923" alt="image" src="https://github.com/user-attachments/assets/cb3069cc-3cf3-442d-88aa-d4fc756f81eb" />
<img width="1910" height="923" alt="image" src="https://github.com/user-attachments/assets/ff80584a-0599-4891-9b8d-47485fa3678a" />

---

## ✨ 功能总览

### 📊 股票分析
| 功能 | 说明 | 详细文档 |
|---|---|---|
| **单股深度分析** | 6位AI分析师（技术/基本面/资金/风险/情绪/新闻）→ 团队讨论 → 最终决策 → PDF报告；支持A股、港股、美股 | [QUICK_START.md](docs/QUICK_START.md) |
| **批量分析** | 顺序/多线程并行双模式，对比表格+详细卡片视图，自动存历史 | [UNIFIED_ANALYSIS_SPEC.md](docs/UNIFIED_ANALYSIS_SPEC.md) |
| **TypeSafe Jev 结构化决策**（可选） | 评级/信心度/价位/新闻情绪由 Jev 类型化直返，告别正则抠JSON；失败自动降级文本链路 | [Jev接入说明](docs/TypeSafe%20Jev决策引擎接入说明.md) |

### 🎯 策略选股
| 功能 | 筛选逻辑 | 详细文档 |
|---|---|---|
| **主力选股** | 问财主力资金净流入TOP100 → 多维筛选 → AI团队精选3-5只；支持TOP 10/20/30/50 批量深度分析+历史记录 | [主力选股使用指南](docs/主力选股使用指南.md) |
| **低价擒牛** | 股价<10元 + 净利润高增长 + 深圳A股；策略监控自动提醒卖出 | [低价擒牛功能说明](docs/低价擒牛功能说明.md) |
| **小市值策略** | 总市值≤50亿 + 营收增长≥10% + 净利增长≥100% | [小市值策略功能说明](docs/小市值策略功能说明.md) |
| **净利增长策略** | 净利润增长率≥10%，按成交额由小到大排序 | [净利增长相关模块](profit_growth_selector.py) |
| **低估值价值投资** | 低PE(≤20) + 低PB(≤1.5) + 高股息(≥1%) + 低负债(≤30%) | [value_stock_ui.py](value_stock_ui.py) |

### 🧭 策略分析
| 功能 | 说明 | 详细文档 |
|---|---|---|
| **智策板块** | 4位AI智能体，板块多空/轮动/热度三维预测，定时分析+推送，PDF报告 | [智策功能总览](docs/智策功能总览.md) |
| **智瞰龙虎** | 龙虎榜数据 × 5位AI分析师，次日潜力股/游资追踪/题材识别，TOP股票批量分析 | [智瞰龙虎功能说明](docs/智瞰龙虎功能说明.md) |
| **宏观周期分析** | 康波周期 × 美林投资时钟 × 中国政策，4位AI分析师三维研判 | [macro_cycle_ui.py](macro_cycle_ui.py) |
| **宏观分析** | 国家统计局官方数据直连 → AI研判 → A股行业映射 → 优质标的推荐 | [macro_analysis_ui.py](macro_analysis_ui.py) |
| **新闻流量监测** | 百度/微博/东财/财联社/抖音/B站等20平台热点监测，AI情绪分析+高置信度告警 | [新闻流量监测功能说明](docs/新闻流量监测功能说明.md) |

### 💼 投资管理
| 功能 | 说明 | 详细文档 |
|---|---|---|
| **实时监测** | 进场区间/止盈/止损价格告警，邮件+钉钉/飞书Webhook推送 | [AGENTS.md](docs/AGENTS.md) |
| **AI盯盘（智能盯盘）** | DeepSeek自动化交易决策，K线图可视化+AI标注，持仓管理，T+1适配 | [智能盯盘使用指南](docs/智能盯盘使用指南.md) |
| **持仓定时分析** | 持仓清单管理、批量/定时分析（多时间点）、自动同步监测、通知推送、评级历史 | [PORTFOLIO_USAGE.md](docs/PORTFOLIO_USAGE.md) |
| **量化交易** | MiniQMT接口集成，自动下单/仓位管理/风险控制 | [MINIQMT_INTEGRATION_GUIDE.md](docs/MINIQMT_INTEGRATION_GUIDE.md) |

### 🔧 系统能力
| 功能 | 说明 | 详细文档 |
|---|---|---|
| **通知系统** | 邮件（QQ/163/Gmail）+ 钉钉/飞书 Webhook，支持自定义关键词 | [Webhook通知配置指南](docs/Webhook通知配置指南.md) |
| **环境配置界面** | Web UI 可视化配置所有 API Key 与通知，免改代码 | [环境配置功能说明](docs/环境配置功能说明.md) |
| **多数据源降级** | TDX → Tushare → AKShare 自动切换，行情不断供 | [TDX数据源配置指南](docs/TDX数据源配置指南.md) |
| **Docker部署** | 一键启动，含国内镜像源加速版本 | [DOCKER_DEPLOYMENT.md](docs/DOCKER_DEPLOYMENT.md) |

---

## 🚀 快速开始

本系统支持两种部署方式：
- **🐳 Docker部署（推荐）**：一键启动，环境隔离，无需配置 Python/Node.js
- **💻 本地部署**：适合开发者，便于调试与二次开发

### 方式一：Docker 部署（推荐）⭐

**前置要求**：Docker 20.10+、Docker Compose 2.0+、DeepSeek API Key

```bash
# 1. 配置环境变量
cp .env.example .env          # Windows PowerShell 可用: Copy-Item .env.example .env
# 编辑 .env，至少填入 DEEPSEEK_API_KEY

# 2. 启动服务（仓库自带 Dockerfile 已预配国内镜像源：阿里 apt / 清华 pip / npmmirror，国内网络构建速度快6倍+）
docker build -t agentsstock1 .
docker run -d -p 8503:8503 -v ./.env:/app/.env --name agentsstock1 agentsstock1
# 或使用 Compose：
docker-compose up -d

# 3. 常用命令
docker-compose logs -f      # 查看日志
docker-compose down         # 停止服务
docker-compose restart      # 重启服务
```

**访问系统**：http://localhost:8503 （Docker 映射端口为 8503，避免端口冲突）

📖 详细文档：[DOCKER_DEPLOYMENT.md](docs/DOCKER_DEPLOYMENT.md) ｜ [国内源构建指南](docs/DOCKER_CN_BUILD_GUIDE.md) ⭐推荐

### 方式二：本地部署

**环境要求**：Python 3.8+（推荐3.12）、Node.js 16+（pywencai 需要）、稳定网络（大陆网络请关闭VPN）、DeepSeek API Key

```bash
# 1. 创建并激活虚拟环境（PowerShell）
python -m venv venv
.\venv\Scripts\Activate.ps1

# 2. 安装依赖
pip install -r requirements.txt
playwright install chromium        # 选股功能需要（问财 TLS 指纹绕过）

# 3. 配置 .env（见下方「环境配置参考」，也可启动后在 Web「环境配置」界面填写）
Copy-Item .env.example .env

# 4. 启动
python run.py                      # 或 streamlit run app.py
```

**访问系统**：http://localhost:8501

**问财选股登录**（主力选股/低价擒牛/净利增长/小市值/低估值等功能的前提，见下方配置参考 §4）

---

## ⚙️ 环境配置参考（.env）

> 💡 所有配置项均可在启动后的「⚙️ 环境配置」Web 界面中可视化填写；完整模板与注释见 [env_example.txt](env_example.txt) / [.env.example](.env.example)。

### 1. AI 引擎（必填其一）

```env
# ===== 必填：DeepSeek（核心AI引擎）=====
DEEPSEEK_API_KEY=your_key_here
DEEPSEEK_BASE_URL=https://api.deepseek.com/v1

# 模型名称：支持任意 OpenAI 兼容模型，一键切换无需改代码
# 常用：deepseek-chat, deepseek-reasoner, qwen-plus, qwen3.6-flash, gpt-4o
DEFAULT_MODEL_NAME=deepseek-chat

# ===== 可选：OrcaRouter 统一模型网关（设置后优先于 DeepSeek）=====
# 一个 key 路由 DeepSeek/Qwen/Kimi 等主流模型 | https://www.orcarouter.ai
ORCAROUTER_API_KEY=
ORCAROUTER_BASE_URL=https://api.orcarouter.ai/v1
ORCAROUTER_MODEL=orcarouter/auto
```

### 2. TypeSafe Jev 结构化决策（可选，不配置则功能关闭）

```env
# 配置后：最终评级/信心度/新闻情绪/批量打分由 Jev 直接返回类型化结果
# 失败/低置信度自动降级 DeepSeek 文本链路，行为零侵入
TYPESAFE_API_KEY=
TYPESAFE_MODEL=jev-latest
JEV_MIN_CONFIDENCE=0.5            # 低于此置信度降级
JEV_ALERT_MIN_CONFIDENCE=0.6      # 新闻告警最低置信度
```

Key 申请：https://console.typesafe.ai ｜ 完整说明：[TypeSafe Jev决策引擎接入说明](docs/TypeSafe%20Jev决策引擎接入说明.md)

### 3. 数据源（可选）

```env
TUSHARE_TOKEN=                    # 备用数据源（https://tushare.pro 注册，见 docs/Tushare积分获取指南.md）
YDC_API_KEY=                      # You.com API（智策板块Research功能用）
YDC_RESEARCH_EFFORT=standard      # 搜索深度：lite/standard/deep/exhaustive

# TDX 本地行情数据源（可选，盯盘/监测响应提速5-10倍）
# 项目地址 https://github.com/oficcejo/tdx-api，默认 docker 部署
TDX_ENABLED=false
TDX_BASE_URL=http://192.168.1.222:8181
```

### 4. 问财（iwencai）登录配置 —— 选股功能前提

同花顺问财对未登录访问限制严格，主力选股、低价擒牛、净利增长、小市值、低估值等选股功能需要登录凭证（二选一）：

**方案一：一键终端扫码登录（本地桌面推荐）**
```bash
python login_iwencai.py           # 自动弹出登录窗口，登录后 Cookie 保存至 .iwencai_cookie.txt
```

**方案二：从已登录 Chrome 抓取 Cookie（远程服务器推荐）**
1. Chrome 登录 [问财选股页面](https://www.iwencai.com/screener) → F12 → Network → F5 刷新
2. 点击第一条请求 → Headers → Request Headers → 复制 `Cookie` 字段值
3. 保存方式任选：`python login_iwencai.py --set-cookie "..."` ／ 写入 `.iwencai_cookie.txt` ／ `.env` 中 `IWENCAI_COOKIE=...`

### 5. 通知配置（可选）

```env
# ===== 邮件通知（QQ/163/Gmail，授权码而非密码）=====
EMAIL_ENABLED=false
SMTP_SERVER=smtp.qq.com
SMTP_PORT=587
EMAIL_FROM=your_email@qq.com
EMAIL_PASSWORD=your_authorization_code
EMAIL_TO=receiver@example.com

# ===== Webhook 通知（钉钉/飞书群机器人）=====
WEBHOOK_ENABLED=false
WEBHOOK_TYPE=dingtalk             # 或 feishu
WEBHOOK_URL=https://oapi.dingtalk.com/robot/send?access_token=xxx
WEBHOOK_KEYWORD=股票              # 钉钉自定义关键词（需与机器人安全设置一致），飞书可留空
```

📖 [邮件配置指南](docs/邮件配置指南.md) ｜ [Webhook配置指南](docs/Webhook通知配置指南.md) ｜ [钉钉关键词快速配置](docs/Webhook钉钉关键词快速配置指南.md)

### 6. 量化交易与策略监控（可选）

```env
MINIQMT_ENABLED=false             # MiniQMT 自动交易（需本机启动 MiniQMT 客户端）
MINIQMT_ACCOUNT_ID=
MINIQMT_HOST=127.0.0.1
MINIQMT_PORT=58610

LOW_PRICE_BULL_SCAN_INTERVAL=60   # 低价擒牛扫描间隔（秒）
LOW_PRICE_BULL_HOLDING_DAYS=5     # 持股天数限制
```

### 7. 当前数据链路总览

```
历史K线      → 腾讯 proxy.finance.qq.com         ✅
个股基本信息 → 新浪 hq.sinajs.cn                 ✅
实时行情     → 新浪 hq.sinajs.cn / TDX(本地)     ✅
财务数据     → 同花顺/新浪                       ✅
选股数据     → iwencai.com (浏览器 cookies)      ✅ (需登录)
资金流向     → 东方财富(受限) → 跳过             ⚠️
降级链       → TDX → Tushare → AKShare 多层保障  ⏳
```

---

## 🎯 主要功能使用说明（精要）

> 各功能的完整操作流程详见 `docs/` 对应文档，此处仅列高频要点。

### 📊 股票分析（单股/批量）

**股票代码格式**：A股 6位数字（`600519`）｜港股 1-5位数字（`00700`）或 `HK00700`｜美股字母（`AAPL`）

**单股流程**：输入代码 → 选择分析师团队 → 开始分析 → 各维度报告 → 团队讨论 → 最终决策 → PDF导出

**批量分析技巧**：
- 代码输入支持每行一个 / 逗号 / 空格分隔
- 3-5只建议顺序分析（稳定），6只以上建议多线程并行（最多3并发，避免API限流）
- 一次建议不超过20只；结果可按评级筛选、按涨跌幅/信心度/RSI排序
- 统一决策字段：`rating`（强烈买入/买入/持有/卖出/强烈卖出）、`confidence_level`、`entry_range`、`take_profit`、`stop_loss`

### 🔍 实时监测

- **进场区间**：价格进入区间触发进场提醒；**止盈位**：建议10-20%盈利目标；**止损位**：建议5-10%止损线
- **检查间隔**：长线180-300秒、短线30-60秒，建议≥60秒避免频繁API调用
- 分析完成后各页面均支持"➕ 加入监测"一键带入价位参数

### 🤖 AI盯盘（智能盯盘）

- DeepSeek 实时决策 + K线图AI标注 + 持仓盈亏管理 + 自动交易（miniQMT，T+1适配）
- 推荐勾选「仅交易时段监控」：API消耗↓75%、无效通知↓95%
- 详细文档：[智能盯盘使用指南](docs/智能盯盘使用指南.md) ｜ [AI盯盘交易时段优化](docs/AI盯盘交易时段优化说明.md)

### 🎯 智瞰龙虎

- 最佳分析时间：交易日 18:00-21:00（龙虎榜T日数据已更新）
- 流程：获取数据 → 5位AI分析师并行分析（8-15分钟）→ 推荐股票/AI评分排名/历史报告
- TOP10 可一键批量深度分析（3/5/10只）→ 加入实时监测
- 仓位参考：高确定性30-40% ／ 中确定性20-30% ／ 低确定性10-15%

### 🎯 智策板块

- 四位智能体：宏观策略师、板块诊断师、资金流向分析师、市场情绪解码员
- 三维输出：板块多空（含信心度，≥8分重点关注）／轮动（潜力接力板块为最佳布局时机）／热度排行
- 定时分析：设置每日时间（盘前8:00-8:30 ／ 盘后16:00-17:00 ／ 晚间21:00-22:00），邮件+Webhook推送
- 📖 [智策定时分析部署清单](docs/智策定时分析部署清单.md)

### 💼 持仓定时分析

```
侧边栏 持仓分析 → 添加持仓（成本价/数量/备注）→ 配置多个定时时间点
→ 启动调度器 → 自动分析+同步监测+邮件/Webhook推送 → 查看评级历史
```
支持A股/港股/美股；多时间点配置见 [MULTI_SCHEDULE_GUIDE.md](docs/MULTI_SCHEDULE_GUIDE.md)

### 📈 新闻流量监测

- 20平台热点新闻实时监测 → AI情绪分析（启用Jev后立场/紧急度/相关性类型化输出）
- 告警门槛：仅 Jev 置信度 ≥ `JEV_ALERT_MIN_CONFIDENCE`（默认0.6）的利好/利空结论触发 Webhook
- 📖 [新闻流量监测快速开始](docs/新闻流量监测快速开始.md)

### 🌏 宏观周期 & 宏观分析

- **宏观周期**（🧭）：康波周期 × 美林投资时钟 × 中国政策三维研判，偏周期框架，适合战略资产配置
- **宏观分析**（🌏）：国家统计局官方数据直连 → AI研判 → 行业利好/利空映射 → 优质标的，偏当前宏观现实
- 两板块配合使用效果更佳

---

## 🏗️ 系统架构

### 分层结构

```
UI层 (Streamlit *_ui.py) → 引擎层 (*_engine.py / *_scheduler.py)
→ AI智能体层 (*_agents.py / ai_agents.py / typesafe_decision_client.py)
→ 数据层 (*_data.py / data_source_manager.py / 各数据源适配器)
→ 持久层 (*_db.py + SQLite/Peewee)
```

**统一分析规范（强制）**：所有股票分析必须走 `app.analyze_single_stock_for_batch()`，字段名/解析/UI/通知全链统一 → [UNIFIED_ANALYSIS_SPEC.md](docs/UNIFIED_ANALYSIS_SPEC.md)

### 模块文件地图

```
核心分析
├── app.py                     # Streamlit 主界面与统一批量分析出口
├── ai_agents.py               # 6位AI分析师团队 + 最终决策（Jev优先）
├── stock_data.py              # A股/港股/美股数据获取与技术指标
├── llm_client.py              # LLM工厂（OrcaRouter/DeepSeek）+ get_jev_client + 价位计算
├── typesafe_decision_client.py# TypeSafe Jev 客户端（SDK/HTTP双路径+三级降级链）⭐ NEW
├── deepseek_client.py         # DeepSeek API 封装
├── data_source_manager.py     # 多数据源管理与降级
└── config.py / config_manager.py / model_config.py  # 配置体系

策略选股
├── main_force_selector/analysis/ui/pdf_generator    # 主力选股（含批量分析）
├── low_price_bull_*           # 低价擒牛（选股/监控/服务/策略）
├── small_cap_selector/ui      # 小市值策略
├── profit_growth_*            # 净利增长策略
├── value_stock_*              # 低估值价值投资
└── small_cap / quarterly_report_data / fund_flow_akshare / news_announcement_data  # 选数支撑

策略分析
├── sector_strategy_*          # 智策板块（agents/data/engine/scheduler/ui/pdf）
├── longhubang_*               # 智瞰龙虎（data/db/agents/engine/scoring/pdf/ui/history）
├── macro_cycle_*              # 宏观周期（agents/data/engine/pdf/ui）
├── macro_analysis_*           # 宏观分析（国家统计局数据+AI研判）
└── news_flow_*                # 新闻流量监测（agents/data/engine/sentiment/alert/db/pdf/ui...）

投资管理
├── portfolio_*                # 持仓定时分析（manager/db/scheduler/ui）
├── monitor_*                  # 实时监测（manager/service/db/ui）
├── smart_monitor_*            # AI盯盘（engine/ui/kline/qmt/tdx_data/deepseek）
├── miniqmt_interface.py       # MiniQMT 量化交易接口
└── notification_service.py    # 邮件 + 钉钉/飞书 Webhook 通知

支撑设施
├── database.py / *_db.py      # Peewee + SQLite 持久层
├── pdf_generator*.py           # PDF 报告生成
├── utils/iwencai_browser.py    # Playwright 绕过问财 TLS 指纹 ⭐
├── utils/pywencai_helper.py    # safe_get 双路径降级 ⭐
├── utils/akshare_helper.py     # 全局请求补丁 + 重试装饰器
├── run.py / start_app.bat      # 启动脚本
└── Dockerfile / docker-compose.yml  # 容器化部署
```

### 技术特性

| 维度 | 说明 |
|---|---|
| **AI模型** | 任意 OpenAI 兼容模型（`DEFAULT_MODEL_NAME` 切换）；OrcaRouter 网关优先；结构化决策可选 TypeSafe Jev |
| **数据源** | AKShare / Tushare / TDX本地 / 腾讯 / 新浪 / 问财(pywencai) / StockAPI龙虎榜 / 国家统计局；多层自动降级 |
| **可视化** | Plotly 交互式K线与指标图（MA/RSI/MACD/KDJ/布林带，TA-Lib计算） |
| **持久化** | SQLite + Peewee（分析记录、监测、持仓、龙虎榜、新闻、板块、组合等各自库） |
| **通知** | 网页 + 邮件（HTML精美格式）+ 钉钉/飞书 Webhook |
| **性能** | Streamlit 缓存5分钟、并行分析（≤3线程）、3次指数退避重试、30秒超时 |

---

## 🛠️ 故障排除

1. **API Key 错误**：检查 `.env` 中 `DEEPSEEK_API_KEY`（或 `ORCAROUTER_API_KEY`）是否存在、有效、余额充足
2. **股票数据获取失败**：检查网络与代码格式；数据源临时不可用时系统自动降级，稍后重试
3. **财务数据获取失败**：新股可能无完整财报，系统自动跳过继续其余分析
4. **依赖安装失败**：`pip install -r requirements.txt`；Python 需 3.8+；`ModuleNotFoundError: schedule` → `pip install schedule`
5. **选股功能全部报错/验证码**：确认已完成问财登录配置（`.iwencai_cookie.txt` 或 `IWENCAI_COOKIE`），并已 `playwright install chromium`
6. **页面加载慢**：首次运行需下载数据；缓存5分钟内重复查询更快；财务数据获取约10-20秒
7. **MiniQMT 连接失败**：确认 MiniQMT 客户端已启动并登录、账户ID正确 → [集成指南](docs/MINIQMT_INTEGRATION_GUIDE.md)
8. **量化交易未执行**：确认功能已启用、连接正常、监测服务运行中、处于交易日内
9. **Docker 问题**：`docker ps` 查状态、`docker-compose logs -f` 看日志、端口冲突改映射、Linux下 `chmod 666 *.db` → [DOCKER_DEPLOYMENT.md](docs/DOCKER_DEPLOYMENT.md)
10. **Webhook 收不到/关键词不匹配(310000)**：核对 `WEBHOOK_ENABLED/URL/KEYWORD`（钉钉关键词须与机器人设置一致）；用「📱 发送测试Webhook」验证 → [配置指南](docs/Webhook通知配置指南.md)
11. **TDX 数据源问题**：`docker ps | grep tdx` 查容器、`curl http://localhost:8080/api/quote?code=000001` 测接口、核对 `TDX_BASE_URL` → [TDX快速配置](docs/TDX数据源快速配置.md)
12. **智策分析超时/定时不跑**：定时任务需保持程序运行；`deepseek-reasoner` 较慢可切 `deepseek-chat`；「立即运行一次」测试 → [部署清单](docs/智策定时分析部署清单.md)

日志调试：终端实时输出；Docker 下 `docker-compose logs -f`。如发现 bug 请查看 `BUGFIX.md` 了解已知问题。

---

## 📚 文档索引（docs/）

| 分类 | 文档 |
|---|---|
| **入门** | [QUICK_START](docs/QUICK_START.md) ｜ [AGENTS.md](docs/AGENTS.md) ｜ [环境配置功能说明](docs/环境配置功能说明.md) ｜ [环境配置快速指南](docs/环境配置快速指南.md) |
| **部署** | [DOCKER_DEPLOYMENT](docs/DOCKER_DEPLOYMENT.md) ｜ [DOCKER_README](docs/DOCKER_README.md) ｜ [国内源构建指南](docs/DOCKER_CN_BUILD_GUIDE.md) |
| **统一规范** | [UNIFIED_ANALYSIS_SPEC](docs/UNIFIED_ANALYSIS_SPEC.md) ｜ [Jev决策引擎接入说明](docs/TypeSafe%20Jev决策引擎接入说明.md) |
| **主力选股** | [使用指南](docs/主力选股使用指南.md) ｜ [功能说明](docs/主力选股功能说明.md) ｜ [批量分析](docs/主力选股批量分析功能说明.md) ｜ [批量历史](docs/主力选股批量分析历史记录功能说明.md) ｜ [修复说明](docs/主力选股批量分析修复说明.md) |
| **智瞰龙虎** | [快速开始](docs/智瞰龙虎快速开始.md) ｜ [功能说明](docs/智瞰龙虎功能说明.md) ｜ [AI评分说明](docs/智瞰龙虎AI评分说明.md) ｜ [历史报告](docs/智瞰龙虎历史报告功能说明.md) ｜ [评分排名历史](docs/智瞰龙虎评分排名历史记录说明.md) ｜ [批量分析](docs/LONGHUBANG_BATCH_ANALYSIS.md) |
| **智策板块** | [功能总览](docs/智策功能总览.md) ｜ [使用指南](docs/智策板块使用指南.md) ｜ [快速开始](docs/智策板块快速开始.md) ｜ [定时分析](docs/智策定时分析使用指南.md) ｜ [部署清单](docs/智策定时分析部署清单.md) |
| **持仓与监测** | [PORTFOLIO_USAGE](docs/PORTFOLIO_USAGE.md) ｜ [MULTI_SCHEDULE_GUIDE](docs/MULTI_SCHEDULE_GUIDE.md) ｜ [实时监测定时功能](docs/实时监测定时功能说明.md) ｜ [监测配置](docs/智能盯盘配置说明.md) ｜ [盯盘指南](docs/智能盯盘使用指南.md) ｜ [持仓管理](docs/智能盯盘持仓管理功能说明.md) ｜ [交易时段优化](docs/AI盯盘交易时段优化说明.md) |
| **选股策略** | [低价擒牛说明](docs/低价擒牛功能说明.md) ｜ [低价擒牛快速开始](docs/低价擒牛快速开始.md) ｜ [低价擒牛监控配置](docs/低价擒牛策略监控配置说明.md) ｜ [小市值说明](docs/小市值策略功能说明.md) ｜ [选股板块菜单重构](docs/选股板块菜单重构说明.md) |
| **新闻与宏观** | [新闻流量监测](docs/新闻流量监测功能说明.md) ｜ [新闻监测快速开始](docs/新闻流量监测快速开始.md) ｜ [新闻流量转化炒股法](新闻流量转化炒股法.md) |
| **数据源** | [TDX配置指南](docs/TDX数据源配置指南.md) ｜ [TDX快速配置](docs/TDX数据源快速配置.md) ｜ [TDX集成说明](docs/TDX数据源集成完成说明.md) ｜ [Tushare积分](docs/Tushare积分获取指南.md) ｜ [toshare说明](docs/toshare说明.md) |
| **通知** | [Webhook配置指南](docs/Webhook通知配置指南.md) ｜ [钉钉关键词](docs/Webhook钉钉关键词快速配置指南.md) ｜ [邮件配置](docs/邮件配置指南.md) |
| **量化** | [MiniQMT集成](docs/MINIQMT_INTEGRATION_GUIDE.md) ｜ [量化快速指南](docs/量化交易快速指南.md) |
| **港股** | [港股功能说明](docs/港股功能说明.md) |
| **OpenSpec** | [openspec/](openspec/) — 变更提案与规格存档（流程见 [openspec/AGENTS.md](openspec/AGENTS.md)） |

---

## 📜 更新记录

完整更新历史见 **[docs/UPDATE_LOG.md](docs/UPDATE_LOG.md)**。近期要点：

| 日期 | 更新 |
|---|---|
| 2026.9.21 | 🎯 TypeSafe Jev 结构化决策引擎接入（评级/价位/新闻情绪/批量打分类型化，三级降级链，零侵入） |
| 2026.6.27 | 🚀 问财 TLS 指纹修复（Playwright cookies + safe_get 双路径降级），问财登录配置上线 |
| 2026.6.18 | 🔧 东方财富屏蔽修复：K线切腾讯、行情切新浪，akshare_helper 全局请求补丁 |
| 2026.3.23 | 🌏 宏观分析板块（国家统计局数据直连 + 行业映射 + 优质标的） |
| 2026.2.27 | 💎 低估值价值投资策略 ｜ 🧭 宏观周期分析 ｜ 🤖 AI模型自由切换 + OrcaRouter 网关 |
| 2026.1.25 | 📈 新闻流量监测（20平台热点 + AI影响分析） |
| 2025.12 | 📈 净利增长策略 ｜ 📊 小市值策略 ｜ 🐂 低价擒牛策略监控 |
| 2025.11 | 📡 TDX本地数据源 ｜ ⏱ 交易时段盯盘 ｜ 🤖 AI盯盘系统（K线图/持仓/自动交易） |
| 2025.10 | ⭐ 持仓定时分析+统一分析规范 ｜ 🎯 主力选股/智瞰龙虎批量分析 ｜ 🎯 智瞰龙虎上线 ｜ 🎯 智策板块+Webhook上线 |

---

## ⚠️ 免责声明

本系统仅供学习和研究使用，不构成投资建议。股票投资有风险，入市需谨慎。使用本系统进行投资决策的风险由用户自行承担。

## 🤝 贡献与联系

欢迎提交 Issue 和 Pull Request！任何疑问请留言或联系 ws3101001@126.com（可加微信，请备注 aiagents-stock）。

**License**：MIT

---

**享受AI驱动的智能股票分析体验！** 🚀📈

**技术支持：山东科技大学 于舒馨**
