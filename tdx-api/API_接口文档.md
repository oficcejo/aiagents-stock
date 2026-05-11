# 📡 TDX股票数据API接口文档

## 🌐 基础信息

**Base URL**: `http://your-server:8080`  
**Content-Type**: `application/json; charset=utf-8`  
**编码**: UTF-8

---

## 📋 响应格式

所有接口统一返回格式：

```json
{
  "code": 0,           // 0=成功, -1=失败
  "message": "success", // 提示信息
  "data": {}           // 数据内容
}
```

---

## 📊 API接口列表

### 1. 获取五档行情

**接口**: `GET /api/quote`

**描述**: 获取股票实时五档买卖盘口数据

**请求参数**:
| 参数 | 类型 | 必填 | 说明 |
|-----|------|------|------|
| code | string | 是 | 股票代码（如：000001）支持多个，逗号分隔 |

**请求示例**:
```
GET /api/quote?code=000001
GET /api/quote?code=000001,600519
```

**响应示例**:
```json
{
  "code": 0,
  "message": "success",
  "data": [
    {
      "Exchange": 0,
      "Code": "000001",
      "Active1": 2843,
      "K": {
        "Last": 12250,    // 昨收价（厘）
        "Open": 12300,    // 开盘价（厘）
        "High": 12600,    // 最高价（厘）
        "Low": 12280,     // 最低价（厘）
        "Close": 12500    // 收盘价/最新价（厘）
      },
      "ServerTime": "1730617200",
      "TotalHand": 1235000,    // 总手数
      "Intuition": 100,        // 现量
      "Amount": 156000000,     // 成交额
      "InsideDish": 520000,    // 内盘
      "OuterDisc": 715000,     // 外盘
      "BuyLevel": [            // 买五档
        {
          "Buy": true,
          "Price": 12500,      // 买一价（厘）
          "Number": 35000      // 挂单量（股）
        },
        // ... 买二到买五
      ],
      "SellLevel": [           // 卖五档
        {
          "Buy": false,
          "Price": 12510,      // 卖一价（厘）
          "Number": 30000      // 挂单量（股）
        },
        // ... 卖二到卖五
      ],
      "Rate": 0.0,
      "Active2": 2843
    }
  ]
}
```

**数据说明**:
- 价格单位：厘（1元 = 1000厘）
- 成交量单位：手（1手 = 100股）
- 挂单量单位：股

---

### 2. 获取K线数据

**接口**: `GET /api/kline`

**描述**: 获取股票K线数据（OHLC + 成交量成交额）。日/周/月K线默认返回同花顺前复权数据；若第三方源不可用将直接返回错误提示，不再自动切换通达信源。需要原始数据或自行设置兜底时，可调用文末的 `/api/kline-all/tdx` 等接口。
**描述**: 获取股票K线数据（OHLC + 成交量成交额）。日/周/月K线优先返回同花顺前复权数据，若第三方源不可用则自动回退到通达信原始数据；分钟级及小时级为原始数据。

**请求参数**:
| 参数 | 类型 | 必填 | 说明 |
|-----|------|------|------|
| code | string | 是 | 股票代码（如：000001） |
| type | string | 否 | K线类型，默认day |

**K线类型(type)**:
- `minute1` - 1分钟K线（最多24000条）
- `minute5` - 5分钟K线
- `minute15` - 15分钟K线
- `minute30` - 30分钟K线
- `hour` - 60分钟/小时K线
- `day` - 日K线（默认）
- `week` - 周K线
- `month` - 月K线

**请求示例**:
```
GET /api/kline?code=000001&type=day
GET /api/kline?code=600519&type=minute30
```

**响应示例**:
```json
{
  "code": 0,
  "message": "success",
  "data": {
    "Count": 100,
    "List": [
      {
        "Last": 12250,      // 昨收价（厘）
        "Open": 12300,      // 开盘价（厘）
        "High": 12600,      // 最高价（厘）
        "Low": 12280,       // 最低价（厘）
        "Close": 12500,     // 收盘价（厘）
        "Volume": 1235000,  // 成交量（手）
        "Amount": 156000000,// 成交额（厘）
        "Time": "2024-11-03T00:00:00Z",
        "UpCount": 0,       // 上涨数（指数有效）
        "DownCount": 0      // 下跌数（指数有效）
      }
      // ... 更多K线数据
    ]
  }
}
```

**数据说明**:
- 数据按时间倒序排列（最新的在前）
- 价格单位：厘
- 成交量单位：手
- 成交额单位：厘

---

### 3. 获取分时数据

**接口**: `GET /api/minute`

**描述**: 获取股票分时走势数据。接口严格按照请求日期返回结果，不再自动回退其他交易日；若指定日期无数据，将返回空列表并保留原日期。
**描述**: 获取股票分时走势数据；若查询日期或当日无数据，会自动回退至最近一个有交易数据的工作日，并在响应体中附加实际数据日期。

**请求参数**:
| 参数 | 类型 | 必填 | 说明 |
|-----|------|------|------|
| code | string | 是 | 股票代码（如：000001） |
| date | string | 否 | 日期（YYYYMMDD格式），默认当天 |

**请求示例**:
```
GET /api/minute?code=000001
GET /api/minute?code=000001&date=20241103
```

**响应示例**:
```json
{
  "code": 0,
  "message": "success",
  "data": {
    "date": "20251110",   // 实际数据日期，与请求日期一致
    "date": "20251107",   // 实际数据日期，可能与请求日期不同
    "Count": 240,
    "List": [
      {
        "Time": "09:31",
        "Price": 12300,    // 价格（厘）
        "Number": 1500     // 成交量（手）
      },
      {
        "Time": "09:32",
        "Price": 12310,
        "Number": 1200
      }
      // ... 240个数据点（9:30-11:30, 13:00-15:00）
    ]
  }
}
```

**数据说明**:
- 交易时段：9:30-11:30（120分钟）, 13:00-15:00（120分钟）
- 共240个数据点
- 价格单位：厘
- 若 `List` 为空，表示该日期无分时数据，请由调用方自行选择备用日期或数据源

---

### 4. 获取分时成交

**接口**: `GET /api/trade`

**描述**: 获取股票逐笔成交明细

**请求参数**:
| 参数 | 类型 | 必填 | 说明 |
|-----|------|------|------|
| code | string | 是 | 股票代码（如：000001） |
| date | string | 否 | 日期（YYYYMMDD格式），默认当天 |

**请求示例**:
```
GET /api/trade?code=000001
GET /api/trade?code=000001&date=20241103
```

**响应示例**:
```json
{
  "code": 0,
  "message": "success",
  "data": {
    "Count": 1800,
    "List": [
      {
        "Time": "2024-11-03T14:59:58Z",
        "Price": 12500,    // 成交价（厘）
        "Volume": 100,     // 成交量（手）
        "Status": 0,       // 0=买入, 1=卖出, 2=中性
        "Number": 5        // 成交单数
      },
      {
        "Time": "2024-11-03T14:59:55Z",
        "Price": 12490,
        "Volume": 50,
        "Status": 1,
        "Number": 3
      }
      // ... 更多成交记录
    ]
  }
}
```

**数据说明**:
- Status: 0=主动买入(红色), 1=主动卖出(绿色), 2=中性
- 当日最多返回1800条
- 历史日期最多返回2000条
- 价格单位：厘
- 成交量单位：手

---

### 5. 搜索股票代码

**接口**: `GET /api/search`

**描述**: 根据关键词搜索股票代码和名称

**请求参数**:
| 参数 | 类型 | 必填 | 说明 |
|-----|------|------|------|
| keyword | string | 是 | 搜索关键词（代码或名称） |

**请求示例**:
```
GET /api/search?keyword=平安
GET /api/search?keyword=000001
```

**响应示例**:
```json
{
  "code": 0,
  "message": "success",
  "data": [
    {
      "code": "000001",
      "name": "平安银行"
    },
    {
      "code": "601318",
      "name": "中国平安"
    }
    // ... 最多50条结果
  ]
}
```

**数据说明**:
- 支持代码和名称模糊搜索
- 最多返回50条结果
- 仅返回A股（过滤指数等）

---

### 6. 获取股票综合信息

**接口**: `GET /api/stock-info`

**描述**: 一次性获取股票的多种数据（五档行情+日K线+分时）

**请求参数**:
| 参数 | 类型 | 必填 | 说明 |
|-----|------|------|------|
| code | string | 是 | 股票代码（如：000001） |

**请求示例**:
```
GET /api/stock-info?code=000001
```

**响应示例**:
```json
{
  "code": 0,
  "message": "success",
  "data": {
    "quote": {
      // 五档行情数据（同/api/quote）
    },
    "kline_day": {
      // 最近30天日K线（同/api/kline?type=day）
    },
    "minute": {
      // 今日分时数据（同/api/minute）
    }
  }
}
```

**数据说明**:
- 整合了五档行情、最近30条日K线、最新分时数据
- 分时数据自带 `date`、`Count`、`List` 字段；若 `List` 为空表示该日期无分时数据
- 分时数据自带 `date`、`Count`、`List` 字段，便于识别回退日期
- 适合快速获取股票概览，减少API调用次数

---

## 🔧 扩展接口（高级功能）

### 7. 获取股票列表

**接口**: `GET /api/codes`

**描述**: 获取指定交易所的所有股票代码列表

**请求参数**:
| 参数 | 类型 | 必填 | 说明 |
|-----|------|------|------|
| exchange | string | 否 | 交易所代码，默认all |

**交易所代码**:
- `sh` - 上海证券交易所
- `sz` - 深圳证券交易所
- `bj` - 北京证券交易所
- `all` - 全部（默认）

**请求示例**:
```
GET /api/codes
GET /api/codes?exchange=sh
```

**响应示例**:
```json
{
  "code": 0,
  "message": "success",
  "data": {
    "total": 5234,
    "exchanges": {
      "sh": 2156,
      "sz": 2845,
      "bj": 233
    },
    "codes": [
      {
        "code": "000001",
        "name": "平安银行",
        "exchange": "sz"
      }
      // ... 更多股票
    ]
  }
}
```

---

### 8. 批量获取行情

**接口**: `POST /api/batch-quote`

**描述**: 批量获取多只股票的实时行情

**请求参数** (JSON Body):
```json
{
  "codes": ["000001", "600519", "601318"]
}
```

**请求示例**:
```bash
curl -X POST http://localhost:8080/api/batch-quote \
  -H "Content-Type: application/json" \
  -d '{"codes":["000001","600519","601318"]}'
```

**响应示例**:
```json
{
  "code": 0,
  "message": "success",
  "data": [
    // 数组，每个元素同/api/quote的单个股票数据
  ]
}
```

---

### 9. 获取历史K线

**接口**: `GET /api/kline-history`

**描述**: 获取指定时间范围的K线数据

**请求参数**:
| 参数 | 类型 | 必填 | 说明 |
|-----|------|------|------|
| code | string | 是 | 股票代码 |
| type | string | 是 | K线类型 |
| start_date | string | 否 | 开始日期（YYYYMMDD） |
| end_date | string | 否 | 结束日期（YYYYMMDD） |
| limit | int | 否 | 返回条数，默认100，最大800 |

**请求示例**:
```
GET /api/kline-history?code=000001&type=day&limit=30
GET /api/kline-history?code=000001&type=day&start_date=20241001&end_date=20241101
```

---

### 10. 获取指数数据

**接口**: `GET /api/index`

**描述**: 获取指数K线数据（如上证指数、深证成指）

**请求参数**:
| 参数 | 类型 | 必填 | 说明 |
|-----|------|------|------|
| code | string | 是 | 指数代码（如：sh000001） |
| type | string | 否 | K线类型，默认day |

**常用指数代码**:
- `sh000001` - 上证指数
- `sz399001` - 深证成指
- `sz399006` - 创业板指
- `sh000300` - 沪深300

**请求示例**:
```
GET /api/index?code=sh000001&type=day
```

---

### 11. 获取服务状态

**接口**: `GET /api/server-status`

**描述**: 返回API服务运行状态。

**响应示例**:
```json
{
  "code": 0,
  "message": "success",
  "data": {
    "status": "running",
    "connected": true,
    "version": "1.0.0",
    "uptime": "unknown"
  }
}
```

---

### 12. 创建批量K线入库任务

**接口**: `POST /api/tasks/pull-kline`

**描述**: 启动后台任务，批量拉取指定股票、指定周期的K线数据并存入本地数据库（默认目录：`data/database/kline`）。任务在后台异步执行，可通过任务管理接口查询状态。

**请求参数**（JSON Body）:
| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| codes | array | 否 | 股票代码数组，默认遍历全部A股 |
| tables | array | 否 | K线类型列表，取值见下表，默认 `["day"]` |
| dir | string | 否 | 数据库存储目录，默认 `data/database/kline` |
| limit | int | 否 | 并发协程数量，默认1 |
| start_date | string | 否 | 起始日期阈值（`YYYY-MM-DD` 或 `YYYYMMDD`），早于此日期的数据不会重新拉取 |

**K线类型列表**:
`minute`, `5minute`, `15minute`, `30minute`, `hour`, `day`, `week`, `month`, `quarter`, `year`

**请求示例**:
```bash
curl -X POST http://localhost:8080/api/tasks/pull-kline \
  -H "Content-Type: application/json" \
  -d '{
    "codes": ["000001","600519"],
    "tables": ["day","week","month"],
    "limit": 4,
    "start_date": "2020-01-01"
  }'
```

**响应示例**:
```json
{
  "code": 0,
  "message": "success",
  "data": {
    "task_id": "9b0d1b1b-7c3d-4ce6-9a0e-bd9f5e0dcf3b"
  }
}
```

---

### 13. 创建分时成交入库任务

**接口**: `POST /api/tasks/pull-trade`

**描述**: 拉取指定股票从 `start_year` 到 `end_year` 的历史分时成交数据，并自动导出CSV（默认目录：`data/database/trade`）。

**请求参数**（JSON Body）:
| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| code | string | 是 | 股票代码（如：000001） |
| dir | string | 否 | 输出目录，默认 `data/database/trade` |
| start_year | int | 否 | 起始年份，默认2000 |
| end_year | int | 否 | 结束年份，默认当年 |

**请求示例**:
```bash
curl -X POST http://localhost:8080/api/tasks/pull-trade \
  -H "Content-Type: application/json" \
  -d '{
    "code": "000001",
    "start_year": 2015,
    "end_year": 2023
  }'
```

**响应示例**同上，返回 `task_id`。

---

### 14. 查询与控制任务

| 接口 | 方法 | 描述 |
|------|------|------|
| `/api/tasks` | GET | 列出所有已创建任务及状态 |
| `/api/tasks/{task_id}` | GET | 查询指定任务详情 |
| `/api/tasks/{task_id}/cancel` | POST | 取消正在执行的任务 |

**任务状态枚举**:
- `running`：执行中
- `success`：已完成
- `failed`：执行失败，`error` 字段包含原因
- `cancelled`：已取消

**响应示例** (`GET /api/tasks/{task_id}`):
```json
{
  "code": 0,
  "message": "success",
  "data": {
    "id": "9b0d1b1b-7c3d-4ce6-9a0e-bd9f5e0dcf3b",
    "type": "pull_kline",
    "status": "running",
    "started_at": "2025-11-10T13:05:26.123456+08:00"
  }
}
```

---

### 15. 获取ETF列表

**接口**: `GET /api/etf`

**描述**: 返回当前可用的 ETF 基金列表，可按交易所过滤并限制返回数量。

**请求参数**:
| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| exchange | string | 否 | 交易所，`sh` / `sz` / `all`（默认） |
| limit | int | 否 | 返回条数限制 |

**响应示例**:
```json
{
  "code": 0,
  "message": "success",
  "data": {
    "total": 2,
    "list": [
      {
        "code": "510300",
        "name": "沪深300ETF",
        "exchange": "sh",
        "last_price": 4.123
      },
      {
        "code": "159915",
        "name": "创业板ETF",
        "exchange": "sz",
        "last_price": 1.876
      }
    ]
  }
}
```

---

### 16. 获取历史分时成交（分页）

**接口**: `GET /api/trade-history`

**描述**: 分页获取历史交易日的分时成交明细，单次最多返回 2000 条。

**请求参数**:
| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| code | string | 是 | 股票代码 |
| date | string | 是 | 交易日期（YYYYMMDD） |
| start | int | 否 | 起始游标，默认0 |
| count | int | 否 | 返回条数，默认2000，最大2000 |

**响应示例**:
```json
{
  "code": 0,
  "message": "success",
  "data": {
    "Count": 2000,
    "List": [
      {
        "Price": 12345,
        "Time": "2024-11-08T14:58:00+08:00",
        "Status": 0,
        "Volume": 50
      }
    ]
  }
}
```

---

### 17. 获取全天分时成交

**接口**: `GET /api/minute-trade-all`

**描述**: 一次性获取某交易日的全部分时成交明细；未指定日期时返回当日实时成交。

**请求参数**:
| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| code | string | 是 | 股票代码 |
| date | string | 否 | 交易日期（YYYYMMDD），默认当天 |

**响应示例**:
```json
{
  "code": 0,
  "message": "success",
  "data": {
    "Count": 3150,
    "List": [
      {
        "Price": 12500,
        "Time": "2024-11-08T09:30:01+08:00",
        "Volume": 10,
        "Status": 0
      }
    ]
  }
}
```

---

### 18. 查询交易日信息

**接口**: `GET /api/workday`

**描述**: 查询指定日期是否为交易日，并返回前后若干个最近的交易日。

**请求参数**:
| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| date | string | 否 | 查询日期（YYYYMMDD 或 YYYY-MM-DD），默认当天 |
| count | int | 否 | 返回的前后交易日数量，范围 1-30，默认1 |

**响应示例**:
```json
{
  "code": 0,
  "message": "success",
  "data": {
    "date": {
      "iso": "2024-11-08",
      "numeric": "20241108"
    },
    "is_workday": true,
    "next": [
      {
        "iso": "2024-11-11",
        "numeric": "20241111"
      }
    ],
    "previous": [
      {
        "iso": "2024-11-07",
        "numeric": "20241107"
      }
    ]
  }
}
```

---

### 19. 获取市场证券数量

**接口**: `GET /api/market-count`

**描述**: 获取上交所、深交所、北交所当前可用证券数量统计。

**响应示例**:
```json
{
  "code": 0,
  "message": "success",
  "data": {
    "total": 7654,
    "exchanges": [
      { "exchange": "sh", "count": 2163 },
      { "exchange": "sz", "count": 5337 },
      { "exchange": "bj", "count": 154 }
    ]
  }
}
```

---

### 20. 获取股票代码列表

**接口**: `GET /api/stock-codes`

**描述**: 返回全市场股票代码列表，可控制是否携带交易所前缀。

**请求参数**:
| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| limit | int | 否 | 返回条数限制 |
| prefix | bool | 否 | 是否包含交易所前缀（默认 true，即 `sh600000`） |

**响应示例**:
```json
{
  "code": 0,
  "message": "success",
  "data": {
    "count": 5600,
    "list": [
      "sh600000",
      "sz000001"
      // ...
    ]
  }
}
```

---

### 21. 获取ETF代码列表

**接口**: `GET /api/etf-codes`

**描述**: 返回所有 ETF 基金代码，参数与 `/api/stock-codes` 相同。

**响应示例**:
```json
{
  "code": 0,
  "message": "success",
  "data": {
    "count": 200,
    "list": [
      "sh510050",
      "sz159915"
    ]
  }
}
```

---

### 22. 获取股票全部历史K线

**接口**: `GET /api/kline-all`

**描述**: 返回指定股票在某个周期的全部历史 K 线数据（天、周、月自动使用前复权）。

**请求参数**:
| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| code | string | 是 | 股票代码 |
| type | string | 否 | K 线类型，默认 day，可选 minute1/5/15/30/hour/day/week/month/quarter/year |
| limit | int | 否 | 返回条数限制（从最近开始截取） |

**注意**: 全量数据较大，建议配合 `limit` 控制响应大小。

---

### 23. 获取指数全部历史K线

**接口**: `GET /api/index/all`

**描述**: 返回指数在各周期的全部历史 K 线数据。

**请求参数**与 `/api/kline-all` 相同。

---

### 24. 获取上市以来分时成交

**接口**: `GET /api/trade-history/full`

**描述**: 返回指定股票上市以来的全部历史分时成交明细，可选截断截止日期与限制数量。

**请求参数**:
| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| code | string | 是 | 股票代码 |
| before | string | 否 | 截止日期（YYYYMMDD 或 YYYY-MM-DD），默认今日 |
| limit | int | 否 | 返回条数限制（从最近开始截取） |

---

### 25. 获取交易日范围

**接口**: `GET /api/workday/range`

**描述**: 返回指定起止日期之间的所有交易日。

**请求参数**:
| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| start | string | 是 | 起始日期（YYYYMMDD 或 YYYY-MM-DD） |
| end | string | 是 | 结束日期（YYYYMMDD 或 YYYY-MM-DD） |

---

### 26. 计算收益区间指标

**接口**: `GET /api/income`

**描述**: 以某日收盘价格为基准，计算若干交易日后的收益情况。

**请求参数**:
| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| code | string | 是 | 股票代码 |
| start_date | string | 是 | 基准日期（YYYYMMDD 或 YYYY-MM-DD） |
| days | string | 否 | 多个天数偏移（逗号分隔），默认 5,10,20,60,120 |

**响应示例**:
```json
{
  "code": 0,
  "message": "success",
  "data": {
    "count": 3,
    "list": [
      {
        "offset": 5,
        "time": "2024-11-15T15:00:00+08:00",
        "rise": 350.0,
        "rise_rate": 0.0285,
        "source": { "close": 12250.0, "open": 12300.0, "...": 0 },
        "current": { "close": 12580.0, "open": 12600.0, "...": 0 }
      }
    ]
  }
}
```

---

## 💡 使用示例

### Python示例

```python
import requests

BASE_URL = "http://your-server:8080"

# 1. 获取五档行情
def get_quote(code):
    url = f"{BASE_URL}/api/quote?code={code}"
    response = requests.get(url)
    data = response.json()
    if data['code'] == 0:
        return data['data']
    return None

# 2. 获取日K线
def get_kline(code, type='day'):
    url = f"{BASE_URL}/api/kline?code={code}&type={type}"
    response = requests.get(url)
    data = response.json()
    if data['code'] == 0:
        return data['data']['List']
    return None

# 3. 搜索股票
def search_stock(keyword):
    url = f"{BASE_URL}/api/search?keyword={keyword}"
    response = requests.get(url)
    data = response.json()
    if data['code'] == 0:
        return data['data']
    return None

# 使用示例
if __name__ == "__main__":
    # 搜索股票
    stocks = search_stock("平安")
    print(f"搜索结果: {stocks}")
    
    # 获取行情
    quote = get_quote("000001")
    print(f"最新价: {quote[0]['K']['Close'] / 1000}元")
    
    # 获取K线
    klines = get_kline("000001", "day")
    print(f"获取到{len(klines)}条K线数据")
```

### JavaScript示例

```javascript
const BASE_URL = 'http://your-server:8080';

// 1. 获取五档行情
async function getQuote(code) {
    const response = await fetch(`${BASE_URL}/api/quote?code=${code}`);
    const data = await response.json();
    if (data.code === 0) {
        return data.data;
    }
    return null;
}

// 2. 获取K线
async function getKline(code, type = 'day') {
    const response = await fetch(`${BASE_URL}/api/kline?code=${code}&type=${type}`);
    const data = await response.json();
    if (data.code === 0) {
        return data.data.List;
    }
    return null;
}

// 3. 批量获取行情
async function batchGetQuote(codes) {
    const response = await fetch(`${BASE_URL}/api/batch-quote`, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify({ codes })
    });
    const data = await response.json();
    return data.data;
}

// 使用示例
(async () => {
    // 获取行情
    const quote = await getQuote('000001');
    console.log('最新价:', quote[0].K.Close / 1000);
    
    // 获取K线
    const klines = await getKline('000001', 'day');
    console.log('K线数据量:', klines.length);
    
    // 批量获取
    const quotes = await batchGetQuote(['000001', '600519', '601318']);
    console.log('批量行情:', quotes.length);
})();
```

### cURL示例

```bash
# 1. 获取五档行情
curl "http://localhost:8080/api/quote?code=000001"

# 2. 获取日K线
curl "http://localhost:8080/api/kline?code=000001&type=day"

# 3. 获取分时数据
curl "http://localhost:8080/api/minute?code=000001"

# 4. 搜索股票
curl "http://localhost:8080/api/search?keyword=平安"

# 5. 批量获取行情
curl -X POST http://localhost:8080/api/batch-quote \
  -H "Content-Type: application/json" \
  -d '{"codes":["000001","600519"]}'
```

---

## 📚 全量历史K线接口

为了区分不同数据源，并方便调用方自行决定兜底策略，历史K线提供以下两个独立接口，返回格式完全一致：

### 1. 通达信原始历史K线

**接口**: `GET /api/kline-all/tdx`

**说明**: 返回通达信原始（不复权）K线，内部按800条一批拼接完成。支持所有 `type` 取值（分钟、小时、日、周、月、季、年）。

**请求参数**:
| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| code | string | 是 | 股票代码（6位数字） |
| type | string | 否 | 默认 `day`，取值同 `/api/kline` |
| limit | int | 否 | 结果截断条数（从末尾取最近N条），默认返回全量 |

**响应示例**:
```json
{
  "code": 0,
  "message": "success",
  "data": {
    "count": 4100,
    "list": [
      {
        "Time": "1991-04-03T00:00:00Z",
        "Open": 1260,
        "High": 1320,
        "Low": 1240,
        "Close": 1280,
        "Volume": 3500,
        "Amount": 4280000,
        "Last": 0
      }
      // ... 时间正序排列的全部K线
    ],
    "meta": {
      "source": "tdx",
      "type": "day",
      "batch_limit": 800,
      "notes": [
        "通达信单次底层请求最多返回 800 条数据，服务端已顺序拼接全量结果",
        "对于上市时间较长的标的，请预估调用耗时（通常 1-5 秒），客户端需自行设置超时与兜底策略",
        "若实测请求在超时阈值内成功返回数据，即视为成功调用，无需按预设超时上限计入统计"
      ]
    }
  }
}
```

### 2. 同花顺前复权历史K线

**接口**: `GET /api/kline-all/ths`

**说明**: 返回同花顺前复权日K线，并提供基于日K转换的周、月K线。仅支持 `type=day/week/month`。

**请求参数**: 同上，`type` 限于 `day`、`week`、`month`。

**响应示例**:
```json
{
  "code": 0,
  "message": "success",
  "data": {
    "count": 4100,
    "list": [
      {
        "Time": "1991-04-03T00:00:00Z",
        "Open": 1260,
        "High": 1320,
        "Low": 1240,
        "Close": 1280,
        "Volume": 3500,
        "Amount": 4280000,
        "Last": 0
      }
      // ... 全量前复权数据
    ],
    "meta": {
      "source": "ths",
      "type": "day",
      "batch_limit": 4100,
      "notes": [
        "同花顺接口一次性返回前复权数据，响应时长依赖网络与标的数据量（通常 2-8 秒）",
        "建议调用方在 Python 等客户端中设置 ≥10 秒超时时间，并按需准备自定义兜底逻辑",
        "若实测请求在超时阈值内成功返回数据，即视为成功调用，无需按预设超时上限计入统计"
      ]
    }
  }
}
```

> ⚠️ **提示**：上述接口不会对接第三方兜底逻辑；若返回空或失败，请由调用方自行决定重试或切换数据源。

---

## 🔒 错误码说明

| code | message | 说明 |
|------|---------|------|
| 0 | success | 请求成功 |
| -1 | 股票代码不能为空 | 缺少必填参数code |
| -1 | 获取行情失败: xxx | 数据获取失败，xxx为具体错误 |
| -1 | 获取K线失败: xxx | K线数据获取失败 |
| -1 | 未找到相关股票 | 搜索无结果 |
| -1 | 搜索关键词不能为空 | 缺少keyword参数 |

---

## 📊 数据单位换算

### 价格单位
- **返回值**：厘（1元 = 1000厘）
- **换算公式**：元 = 厘 / 1000
- **示例**：12500厘 = 12.50元

### 成交量单位
- **返回值**：手（1手 = 100股）
- **换算公式**：股 = 手 × 100
- **示例**：1235手 = 123500股

### 成交额单位
- **返回值**：厘
- **换算公式**：元 = 厘 / 1000
- **示例**：156000000厘 = 156000元 = 15.6万元

---

## 🚀 性能建议

1. **批量请求**：使用批量接口代替多次单个请求
2. **缓存**：对不常变化的数据（如股票列表）做本地缓存
3. **限流**：避免频繁请求，建议间隔>=3秒
4. **压缩**：使用gzip压缩减少传输量

---

## 📝 更新日志

### v1.0.0 (2024-11-03)
- ✅ 实现基础6个API接口
- ✅ 统一响应格式
- ✅ 完整文档和示例

### v1.1.0 (计划中)
- 🔄 批量查询接口
- 🔄 历史K线范围查询
- 🔄 指数数据接口
- 🔄 WebSocket实时推送

---

## 📞 技术支持

- 文档地址：本文件
- API测试：使用Postman或cURL
- 问题反馈：GitHub Issues

---

**Happy Coding!** 🎉

