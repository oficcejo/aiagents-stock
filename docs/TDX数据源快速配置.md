# TDX数据源快速配置指南

## 📖 简介

TDX（通达信）数据源是一个本地化的股票行情数据接口，提供实时行情、K线数据、技术指标等功能。相比于公网API，TDX数据源具有以下优势：

### ✨ 核心优势

- **🚀 速度快**: 本地局域网访问，响应时间<50ms
- **💰 零成本**: 完全免费，无API调用限制
- **📊 数据全**: 支持实时行情、K线、分时、技术指标
- **🔒 稳定性**: 不受公网API限流影响
- **🌐 本地化**: Docker一键部署，数据完全可控

---

## 🎯 快速开始

### 1. 部署TDX数据API服务

#### 方式一：使用Docker部署（推荐）

```bash
# 克隆TDX API项目
git clone https://github.com/oficcejo/tdx-api.git
cd tdx-api

# 启动服务
docker-compose up -d

# 查看日志
docker-compose logs -f
```

**访问测试**：
```bash
# 测试接口是否正常
curl "http://localhost:8080/api/quote?code=000001"
```

#### 方式二：手动构建

```bash
# 构建镜像
docker build -t tdx-api .

# 运行容器
docker run -d -p 8080:8080 --name tdx-api tdx-api
```

### 2. 配置AI股票分析系统

在项目根目录的`.env`文件中添加以下配置：

```env
# TDX数据源配置
TDX_ENABLED=true
TDX_BASE_URL=http://192.168.1.222:8080
```

**配置说明**：
- `TDX_ENABLED`: 是否启用TDX数据源（`true`/`false`）
- `TDX_BASE_URL`: TDX API服务地址
  - 本机部署：`http://localhost:8080`
  - 局域网部署：`http://192.168.1.222:8080`（替换为实际IP）

### 3. 重启AI股票分析系统

```bash
# 本地部署
streamlit run app.py

# Docker部署
docker-compose restart
```

---

## 📊 功能集成说明

### 已集成模块

#### 1. AI盯盘 - 实时行情获取

**文件**: `smart_monitor_data.py`, `smart_monitor_ui.py`

**功能**：
- ✅ 实时行情查询（价格、涨跌幅、成交量）
- ✅ K线数据获取（日K、周K、月K）
- ✅ 技术指标计算（MA、MACD、RSI、KDJ、布林带）
- ✅ 降级机制（TDX失败时自动切换Tushare）

**使用示例**：
```python
from smart_monitor_tdx_data import SmartMonitorTDXDataFetcher

# 初始化
fetcher = SmartMonitorTDXDataFetcher(base_url="http://192.168.1.222:8080")

# 获取实时行情
quote = fetcher.get_realtime_quote('000001')
print(f"当前价: {quote['current_price']} 元")

# 获取K线数据
kline_df = fetcher.get_kline_data('000001', kline_type='day', limit=200)

# 获取技术指标
indicators = fetcher.get_technical_indicators('000001')
print(f"RSI: {indicators['rsi6']:.2f}")
```

#### 2. 实时监测 - 价格监控

**文件**: `monitor_service.py`

**功能**：
- ✅ 自动价格监控（优先使用TDX数据源）
- ✅ 降级机制（TDX失败时切换AKShare/yfinance）
- ✅ A股自动识别（6位数字代码）

**工作流程**：
```
1. 检测股票代码是否为A股（6位数字）
   ↓
2. 如果是A股且TDX已启用 → 使用TDX获取行情
   ↓
3. TDX失败 → 自动降级到AKShare
   ↓
4. 更新数据库 → 检查触发条件 → 发送通知
```

---

## 🔧 配置示例

### 完整.env配置

```env
# DeepSeek AI配置（必需）
DEEPSEEK_API_KEY=sk-your-api-key

# TDX数据源配置（可选，提升实时监测性能）
TDX_ENABLED=true
TDX_BASE_URL=http://192.168.1.222:8080

# Tushare配置（可选，作为降级数据源）
TUSHARE_TOKEN=your-tushare-token

# 邮件通知配置（可选）
EMAIL_ENABLED=true
SMTP_SERVER=smtp.qq.com
SMTP_PORT=587
EMAIL_FROM=your_email@qq.com
EMAIL_PASSWORD=your_authorization_code
EMAIL_TO=receiver@example.com

# Webhook通知配置（可选）
WEBHOOK_ENABLED=false
WEBHOOK_TYPE=dingtalk
WEBHOOK_URL=your_webhook_url
WEBHOOK_KEYWORD=股票
```

---

## 📈 TDX数据API接口说明

### 核心接口

| 接口 | 方法 | 说明 | 示例 |
|------|------|------|------|
| `/api/quote` | GET | 实时行情 | `?code=000001` |
| `/api/kline` | GET | K线数据 | `?code=000001&type=day` |
| `/api/minute` | GET | 分时数据 | `?code=000001` |
| `/api/trade` | GET | 分时成交 | `?code=000001` |
| `/api/search` | GET | 股票搜索 | `?keyword=平安` |

### 实时行情响应示例

```json
{
  "code": 0,
  "message": "success",
  "data": [
    {
      "K": {
        "Close": 12345,    // 收盘价（厘，需除以1000）
        "Open": 12300,     // 开盘价（厘）
        "High": 12400,     // 最高价（厘）
        "Low": 12200,      // 最低价（厘）
        "Last": 12350      // 昨收价（厘）
      },
      "TotalHand": 123456, // 成交量（手）
      "Amount": 1234567890 // 成交额（厘）
    }
  ]
}
```

**注意**: 价格单位为"厘"（1元 = 1000厘），系统会自动转换。

---

## 🚨 常见问题

### 1. TDX服务无法访问

**症状**：
```
❌ TDX连接失败，请检查接口地址: http://192.168.1.222:8080
```

**解决方案**：
1. 检查TDX Docker容器是否运行：
   ```bash
   docker ps | grep tdx
   ```

2. 测试接口可用性：
   ```bash
   curl "http://192.168.1.222:8080/api/quote?code=000001"
   ```

3. 检查防火墙设置（确保8080端口开放）

4. 修改`.env`中的`TDX_BASE_URL`为正确的IP地址

### 2. TDX数据源未启用

**症状**：
```
⚠️ TDX数据源模块未找到，将使用默认数据源
```

**解决方案**：
1. 确认`.env`中已配置：
   ```env
   TDX_ENABLED=true
   ```

2. 确认`smart_monitor_tdx_data.py`文件存在

3. 重启应用

### 3. TDX获取数据失败，降级到其他数据源

**症状**：
```
⚠️ TDX获取失败，降级到默认数据源: 000001
```

**原因**：
- TDX服务临时不可用
- 股票代码不存在
- 网络延迟

**解决方案**：
- 系统会自动降级到AKShare，无需干预
- 如频繁降级，检查TDX服务状态

### 4. 价格数据显示为0

**原因**：
- TDX接口返回的数据单位为"厘"（1元=1000厘）
- 系统会自动转换，如显示为0可能是数据源问题

**解决方案**：
1. 检查TDX服务日志
2. 尝试重启TDX容器：
   ```bash
   docker-compose restart
   ```

---

## 🔍 性能对比

| 数据源 | 响应时间 | 调用限制 | 稳定性 | 成本 |
|--------|----------|----------|--------|------|
| **TDX（本地）** | <50ms | 无限制 | ⭐⭐⭐⭐⭐ | 免费 |
| **AKShare** | 500-2000ms | 频繁限流 | ⭐⭐⭐ | 免费 |
| **Tushare** | 300-1000ms | 积分限制 | ⭐⭐⭐⭐ | 免费/付费 |
| **yfinance** | 1000-3000ms | 有限制 | ⭐⭐⭐ | 免费 |

**结论**: TDX数据源在本地部署时，性能和稳定性远超公网API。

---

## 📚 相关资源

- **TDX API项目地址**: https://github.com/oficcejo/tdx-api
- **完整API文档**: [TDX API_接口文档.md](https://github.com/oficcejo/tdx-api/blob/main/API_接口文档.md)
- **Docker部署指南**: [TDX DOCKER_DEPLOY.md](https://github.com/oficcejo/tdx-api/blob/main/DOCKER_DEPLOY.md)

---

## 📝 版本历史

- **v1.0.0** (2025-11-04): TDX数据源集成完成
  - ✅ AI盯盘模块集成TDX实时行情
  - ✅ 实时监测模块集成TDX价格获取
  - ✅ 降级机制（TDX→Tushare→AKShare）
  - ✅ 完整技术指标计算

---

**提示**: 如有问题，请查看项目 [README.md](../README.md) 或联系技术支持。
