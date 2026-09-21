# TypeSafe Jev 决策引擎接入说明

> 提案与设计：`openspec/changes/add-typesafe-jev-decision/`
> Jev 文档：https://docs.typesafe.ai/introduction

## 1. Jev 是什么

Jev 是 TypeSafe 的 System One 模型：**传入 state（自由文本）+ 类型化问题，直接返回类型化答案**（Choice / Score / Noul + 概率分布 + 校准置信度），不生成文本、无需解析。本项目用它做"文本 → 结构化决策"的收口，替代脆弱的"LLM 输出文本再正则抠 JSON"链路。

## 2. 开启方法（可选功能）

1. 申请 Key：https://console.typesafe.ai/keys （Playground 可先免费验证：https://console.typesafe.ai/playground ）
2. 在 `.env` 中配置：

```ini
TYPESAFE_API_KEY=你的key
# 以下均可省略（有默认值）
TYPESAFE_BASE_URL=https://api.typesafe.ai/v1
TYPESAFE_MODEL=jev-latest
JEV_MIN_CONFIDENCE=0.5      # 评级置信度低于此值 → 降级文本链路
JEV_ALERT_MIN_CONFIDENCE=0.6  # 新闻告警门控阈值
```

3. **不配置 `TYPESAFE_API_KEY` 时功能完全关闭，所有行为与接入前一致（零侵入）。**
4. 回滚方式：删除/置空 `TYPESAFE_API_KEY` 即回到现状。

## 3. 启用后改变了什么

| 场景 | 原链路 | Jev 链路 |
|---|---|---|
| 最终投资决策 `make_final_decision` | DeepSeek 输出 JSON 文本 + `re.search(r'\{.*\}')` 解析 | 评级 Choice 五档直出；信心度 = 校准 confidence × 10 |
| 价位字段（入场/止盈/止损/目标价） | 模型文本给数字 + `re.findall(r'\d+\.?\d*')` 提取 | **由代码按现价 ± 百分比计算**（`config.PRICE_*_PCT`），格式与规范完全兼容 |
| 新闻情绪分类 `news_flow_sentiment` | 关键词计数 / DeepSeek 文本 | 立场 Choice + 紧急度 Score + 相关性 Noul 一次调用 |
| 批量选股打分 | 每股一次完整 LLM 决策 | 四维原子 Score 一次并行调用，代码加权合成 `jev_composite_score`（可直接排序） |
| Webhook 新闻告警 | 无置信度门槛 | **仅 confidence ≥ 0.6 的利空/利好结论才推送**（利空优先） |

所有结果携带 `decision_source` 字段：`jev` / `deepseek_fallback`（主力选股与龙虎榜批量结果表已展示"决策来源"列）。

## 4. 三级降级链（自动，无需干预）

```
Jev 调用 ──成功且置信度达标──→ decision_source=jev
   │失败/超时(10s×2次)/置信度<0.5/现价非法
   ▼
DeepSeek 文本 + 正则解析（原链路）──成功──→ decision_source=deepseek_fallback
   │LLM 也不可用（仅新闻分类）
   ▼
关键词启发式兜底 → decision_source=keyword_fallback
```

- 降级发生在调用点适配层（`ai_agents.make_final_decision`、`news_flow_sentiment.classify_news_stance`），旧文本链路代码原样保留。
- 与"AKShare→Tushare 数据源降级"是同一心智模型；重试 1 次防限流。
- 境外 API 不可达时只会变慢（最多 2×10 秒），不会导致分析失败。

## 5. 涉及文件

| 文件 | 角色 |
|---|---|
| `typesafe_decision_client.py` | Jev 客户端（SDK 优先 / requests 兜底）、问题模板、state 构建、答案读取 |
| `llm_client.py` | `get_jev_client()` 工厂 + `compute_price_fields()` 价位计算 |
| `config.py` | `TYPESAFE_*`、`JEV_*`、`PRICE_*_PCT`、`JEV_SCORE_WEIGHTS` 常量 |
| `ai_agents.py` | 最终决策适配层（含多维打分合成） |
| `news_flow_sentiment.py` | 新闻立场分类（Jev→文本→关键词三级兜底）+ 告警候选汇总 |
| `news_flow_alert.py` | 第 7 类预警 `news_stance`（置信度二次门控，可由告警配置 `jev_min_alert_confidence` 覆盖） |
| `main_force_ui.py` / `longhubang_ui.py` | 批量结果展示决策来源 / 综合评分 |
| `test_typesafe_decision_client.py` | 16 项单元测试（mock，不触真网络） |

## 6. 调参说明

- **价位百分比**：`config.py` 的 `PRICE_ENTRY_PCT=0.02`（入场下限=现价-2%）、`PRICE_TAKE_PROFIT_PCT=0.08`、`PRICE_STOP_LOSS_PCT=0.05`
- **打分权重**：`config.JEV_SCORE_WEIGHTS`（技术 0.30 / 基本面 0.30 / 资金 0.25 / 风险 0.15，权重之和自动归一）
- 调整权重/百分比只需改常量，**不需要改任何提示词**——这是 Jev"原子问题+代码组合"模式的核心收益

## 7. 灰度观察

新闻分类处于灰度双写期：Jev 结果与关键词启发式结果同时写入日志（搜 `[双写]` 关键字），用于分析分歧、迭代问题措辞。批量场景 `jev_composite_score` 与 AI 评分排名的相关性可作为观察指标。

## 8. 测试

```bash
venv\Scripts\python.exe -m pytest test_typesafe_decision_client.py -v
```

覆盖：HTTP 路径请求构造、重试、JevError、低置信度降级、价位字符串与 `split("-")`/`re.findall` 兼容性、告警门控、未配置 Key 零侵入。
