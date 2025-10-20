# 统一股票分析调用规范

## 📌 核心原则

**所有涉及股票分析的功能必须使用统一的分析函数和数据结构！**

---

## 🎯 适用场景

✅ 以下所有场景必须遵循此规范：

- 首页单股分析
- 首页批量分析
- 持仓批量分析（UI触发）
- 持仓定时分析（自动触发）
- 智策板块中的个股分析
- 智瞰龙虎中的个股分析
- 主力选股中的个股分析
- **任何未来新增的股票分析功能**

---

## ✅ 正确做法

### 1. 调用统一分析函数

```python
from app import analyze_single_stock_for_batch

result = analyze_single_stock_for_batch(
    symbol="600519.SH",
    period="1y",
    enabled_analysts_config={
        'technical': True,
        'fundamental': True,
        'fund_flow': True,
        'risk': True,
        'sentiment': False,
        'news': False
    },
    selected_model="deepseek-chat"
)
```

### 2. 使用统一字段名

```python
# 提取分析结果
final_decision = result["final_decision"]
stock_info = result["stock_info"]

# 使用正确的字段名
rating = final_decision.get("rating", "未知")                      # ✅
confidence = final_decision.get("confidence_level", "N/A")          # ✅
entry_range = final_decision.get("entry_range", "N/A")             # ✅
take_profit = final_decision.get("take_profit", "N/A")             # ✅
stop_loss = final_decision.get("stop_loss", "N/A")                 # ✅
target_price = final_decision.get("target_price", "N/A")           # ✅
advice = final_decision.get("advice", "")                           # ✅
```

### 3. 统一数据解析

```python
import re

# 解析进场区间（格式如"10.5-12.3"）
entry_range = final_decision.get("entry_range", "")
entry_min, entry_max = None, None
if entry_range and isinstance(entry_range, str) and "-" in entry_range:
    try:
        parts = entry_range.split("-")
        entry_min = float(parts[0].strip())
        entry_max = float(parts[1].strip())
    except:
        pass

# 解析止盈止损（提取数字，如"15.8元" → 15.8）
take_profit_str = final_decision.get("take_profit", "")
take_profit = None
if take_profit_str:
    try:
        numbers = re.findall(r'\d+\.?\d*', str(take_profit_str))
        if numbers:
            take_profit = float(numbers[0])
    except:
        pass

# 止损位同理
stop_loss_str = final_decision.get("stop_loss", "")
stop_loss = None
if stop_loss_str:
    try:
        numbers = re.findall(r'\d+\.?\d*', str(stop_loss_str))
        if numbers:
            stop_loss = float(numbers[0])
    except:
        pass
```

### 4. 统一结果展示

```python
# 评级颜色标识
if "强烈买入" in rating or "买入" in rating:
    rating_color = "🟢"
elif "卖出" in rating:
    rating_color = "🔴"
else:
    rating_color = "🟡"

# UI展示（Streamlit示例）
with st.expander(f"{rating_color} {code} - {rating} (信心度: {confidence})"):
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("**进出场位置**")
        st.write(f"进场区间: {entry_range}")
        st.write(f"目标价: {target_price}")
    
    with col2:
        st.markdown("**风控位置**")
        st.write(f"止盈位: {take_profit}")
        st.write(f"止损位: {stop_loss}")
    
    if advice:
        st.markdown("**投资建议**")
        st.info(advice)
```

---

## ❌ 禁止行为

### 1. 不要直接调用 ai_agents

```python
# ❌ 错误做法
from ai_agents import StockAnalysisAgents
agents = StockAnalysisAgents()
result = agents.technical_analyst_agent(...)  # 禁止！
```

### 2. 不要使用废弃字段名

```python
# ❌ 错误的字段名
rating = final_decision.get("investment_rating")       # 已废弃
confidence = final_decision.get("confidence")          # 已废弃
positions = final_decision.get("entry_exit_positions") # 已废弃
entry_min = positions.get("entry_zone_min")            # 已废弃
```

### 3. 不要重复实现分析逻辑

```python
# ❌ 错误做法
from stock_data import StockDataFetcher
from ai_agents import StockAnalysisAgents

fetcher = StockDataFetcher()
agents = StockAnalysisAgents()

# 自己获取数据
stock_data = fetcher.get_stock_data(symbol)
indicators = fetcher.calculate_technical_indicators(stock_data)

# 自己调用分析师
result = agents.technical_analyst_agent(...)  # 禁止！
```

---

## 📋 字段对照表

| 正确字段名 | 废弃字段名 | 数据类型 | 示例值 |
|-----------|-----------|---------|-------|
| `rating` | `investment_rating` | string | "买入", "持有", "卖出" |
| `confidence_level` | `confidence` | string/number | "8/10", "N/A" |
| `entry_range` | `entry_exit_positions["entry_zone_min/max"]` | string | "10.5-12.3" |
| `take_profit` | `entry_exit_positions["take_profit"]` | string | "止盈: 15.8元" |
| `stop_loss` | `entry_exit_positions["stop_loss"]` | string | "止损: 9.2元" |
| `target_price` | - | string | "目标价: 18.5元" |
| `advice` | `summary` | string | "建议买入..." |

---

## 🔍 代码审查检查清单

提交涉及股票分析的代码时，请确认：

- [ ] 使用了 `app.analyze_single_stock_for_batch()` 而非直接调用 `ai_agents`
- [ ] 使用了正确的字段名（`rating`, `confidence_level`, `entry_range`等）
- [ ] 没有使用废弃字段名（`investment_rating`, `entry_exit_positions`等）
- [ ] 数据解析逻辑与规范一致（split("-"), re.findall()）
- [ ] UI展示格式与其他模块保持一致
- [ ] 通知推送使用相同的数据结构

---

## 📚 参考代码

### 推荐参考

1. **`portfolio_manager.py`** - 完整的分析调用和数据保存示例
2. **`portfolio_ui.py`** - UI展示和数据解析示例
3. **`portfolio_scheduler.py`** - 监测同步和通知推送示例
4. **`notification_service.py`** - 通知内容构建示例

### 设计文档

- **`openspec/changes/add-portfolio-scheduled-analysis/design.md`** - Decision 4: 统一股票分析调用规范
- **`openspec/changes/add-portfolio-scheduled-analysis/specs/stock-analysis/spec.md`** - Requirement: 统一股票分析调用规范

---

## 💡 好处

遵循此规范可以获得：

1. ✅ **维护成本降低**：只需维护一个分析函数
2. ✅ **测试成本降低**：只需测试一个分析流程
3. ✅ **Bug修复效率**：一处修复，全局生效
4. ✅ **新功能快速开发**：直接复用，无需重写
5. ✅ **用户体验一致**：所有场景看到的结果格式一致
6. ✅ **代码复用最大化**：避免重复代码
7. ✅ **自动兼容优化**：首页分析的优化自动应用到所有场景

---

## ⚠️ 违规后果

不遵循此规范可能导致：

- ❌ 字段名不一致，UI显示"未知"或错误
- ❌ 数据解析失败，监测同步失败
- ❌ 通知推送格式错误
- ❌ 代码重复，维护困难
- ❌ Bug修复需要改多处
- ❌ 用户体验不一致

---

## 🆘 常见问题

### Q: 为什么必须使用统一函数？
A: 确保所有场景使用相同的AI模型、数据源、分析流程，避免结果不一致。首页分析的任何优化都会自动应用到所有场景。

### Q: 为什么不能直接调用 ai_agents？
A: `app.analyze_single_stock_for_batch()` 已经封装了完整的数据获取、分析、错误处理流程。直接调用 ai_agents 会导致代码重复和逻辑不一致。

### Q: 旧代码使用了废弃字段怎么办？
A: 必须修改！参考 `portfolio_manager.py` 中的正确用法，使用新的字段名。

### Q: 如何解析字符串字段（如进场区间）？
A: 参考本文档"统一数据解析"章节的代码示例，使用 `split("-")` 和正则表达式。

### Q: 新功能可以不遵循此规范吗？
A: **不可以！** 所有涉及股票分析的功能都必须遵循此规范，这是强制要求。

---

## 📝 更新日志

- **2024-10-20**: 初始版本，基于持仓定时分析功能的实践总结
- **规范来源**: OpenSpec - `add-portfolio-scheduled-analysis` - Decision 4

---

**遵循规范，代码更优！** 🎉

