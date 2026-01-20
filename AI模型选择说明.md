# AI模型选择机制说明

## 📋 问题回答

### 1. 左侧的AI模型选择会全局默认生效吗？

**答案：部分生效，但不完全全局**

**当前状态**：
- ✅ 模型选择器会保存到 `st.session_state.selected_model`
- ❌ 但很多功能模块**强制使用** `config.DEEPSEEK_MODEL_NAME`（从 `.env` 文件读取），**忽略**了 `session_state` 中的选择
- ✅ 只有部分页面（如"主力选股"）会使用页面内的模型选择

**具体表现**：
- **股票分析页面**：强制使用 `config.DEEPSEEK_MODEL_NAME`，忽略侧边栏选择
- **批量分析功能**：强制使用 `config.DEEPSEEK_MODEL_NAME`，忽略侧边栏选择
- **主力选股页面**：使用页面内的模型选择（不是侧边栏的）
- **智策板块页面**：强制使用 `config.DEEPSEEK_MODEL_NAME`

### 2. 如果选择其他模型，模型信息在哪里配置？

**答案：两个地方**

#### 位置1：模型选项列表 - `model_config.py`

**文件路径**：`model_config.py`

**作用**：定义所有可用的AI模型选项

**内容示例**：
```python
model_options = {
    "deepseek-chat": "DeepSeek Chat (默认)",
    "deepseek-reasoner": "DeepSeek Reasoner (推理增强)",
    "qwen-plus": "qwen-plus (阿里百炼)",
    # ... 更多模型
}
```

**如何添加新模型**：
1. 在 `model_config.py` 的 `model_options` 字典中添加新项
2. 格式：`"模型ID": "显示名称"`

#### 位置2：默认模型配置 - `.env` 文件

**文件路径**：`.env`（项目根目录）

**作用**：设置系统默认使用的模型

**配置项**：
```bash
DEEPSEEK_MODEL_NAME=deepseek-chat
```

**如何修改默认模型**：
1. 编辑 `.env` 文件
2. 修改 `DEEPSEEK_MODEL_NAME` 的值
3. 值必须是 `model_config.py` 中 `model_options` 的键之一

---

## 🔍 代码实现分析

### 模型选择器（侧边栏）

**位置**：`app.py` 的 `model_selector()` 函数

**代码**：
```python
def model_selector():
    """模型选择器"""
    st.sidebar.subheader("🤖 AI模型选择")
    
    # 获取配置文件中的默认模型
    default_model = config.DEEPSEEK_MODEL_NAME
    
    # 从 session_state 获取当前选择
    current_model = st.session_state.get('selected_model', default_model)
    
    # 显示选择框
    selected_model = st.sidebar.selectbox(
        "选择AI模型",
        options=list(model_options.keys()),
        ...
    )
    
    return selected_model
```

**问题**：虽然保存到 `session_state`，但很多地方不使用它

### 实际使用情况

#### ❌ 不生效的地方（强制使用配置文件）

**1. 股票分析页面** (`app.py` 的 `run_stock_analysis`)
```python
# 强制使用配置文件中的默认模型（忽略 session_state 中的旧值）
config_model = config.DEEPSEEK_MODEL_NAME
if config_model in model_options:
    selected_model = config_model
else:
    selected_model = list(model_options.keys())[0]

agents = StockAnalysisAgents(model=selected_model)  # 使用配置文件的值
```

**2. 批量分析功能** (`app.py` 的 `run_batch_analysis`)
```python
# 强制使用配置文件中的默认模型
config_model = config.DEEPSEEK_MODEL_NAME
if config_model in model_options:
    selected_model = config_model
else:
    selected_model = list(model_options.keys())[0]
```

**3. 批量分析中的单个股票分析** (`app.py` 的 `analyze_single_stock_for_batch`)
```python
# 强制使用配置文件中的默认模型（忽略传入的旧值）
config_model = config.DEEPSEEK_MODEL_NAME
if selected_model is None or selected_model == "" or selected_model == "deepseek-chat":
    selected_model = config_model
```

#### ✅ 生效的地方

**1. 主力选股页面** (`main_force_ui.py`)
```python
# 页面内有自己的模型选择
model = st.selectbox(
    "选择AI模型",
    list(app_model_options.keys()),
    ...
)

analyzer = MainForceAnalyzer(model=model)  # 使用页面选择的值
```

---

## 🔧 如何让侧边栏选择全局生效？

### 方案1：修改代码使用 session_state（推荐）

修改所有强制使用 `config.DEEPSEEK_MODEL_NAME` 的地方，改为优先使用 `session_state.selected_model`：

```python
# 修改前
config_model = config.DEEPSEEK_MODEL_NAME
selected_model = config_model

# 修改后
selected_model = st.session_state.get('selected_model', config.DEEPSEEK_MODEL_NAME)
if selected_model not in model_options:
    selected_model = config.DEEPSEEK_MODEL_NAME
```

**需要修改的文件**：
1. `app.py` - `run_stock_analysis()` 函数
2. `app.py` - `run_batch_analysis()` 函数
3. `app.py` - `analyze_single_stock_for_batch()` 函数

### 方案2：保持现状，使用配置文件

**优点**：
- 配置持久化（重启后仍然有效）
- 不依赖 Streamlit session

**缺点**：
- 需要修改 `.env` 文件才能改变模型
- 不能通过UI快速切换

---

## 📝 模型配置详细说明

### model_config.py 结构

```python
model_options = {
    # 键：模型ID（用于API调用）
    # 值：显示名称（在UI中显示）
    "deepseek-chat": "DeepSeek Chat (默认)",
    "deepseek-reasoner": "DeepSeek Reasoner (推理增强)",
    # ...
}
```

### 添加新模型的步骤

1. **确定模型ID**：从API文档获取模型标识符
2. **添加到 model_config.py**：
   ```python
   model_options = {
       # ... 现有模型
       "new-model-id": "新模型显示名称",
   }
   ```
3. **（可选）设置为默认**：在 `.env` 文件中设置
   ```bash
   DEEPSEEK_MODEL_NAME=new-model-id
   ```

### 当前可用的模型

根据 `model_config.py`，当前支持以下模型：

| 模型ID | 显示名称 | 说明 |
|--------|----------|------|
| `deepseek-chat` | DeepSeek Chat (默认) | 默认模型 |
| `deepseek-reasoner` | DeepSeek Reasoner (推理增强) | 推理能力更强 |
| `qwen-plus` | qwen-plus (阿里百炼) | 阿里云模型 |
| `qwen-plus-latest` | qwen-plus-latest (阿里百炼) | 最新版本 |
| `qwen-flash` | qwen-flash (阿里百炼) | 快速版本 |
| `qwen-turbo` | qwen-turbo (阿里百炼) | 加速版本 |
| `qwen3-max` | qwen-max (阿里百炼) | 最大版本 |
| `qwen-long` | qwen-long (阿里百炼) | 长文本版本 |
| `deepseek-ai/DeepSeek-R1-0528-Qwen3-8B` | DeepSeek-R1 免费(硅基流动) | 免费模型 |
| `Qwen/Qwen2.5-7B-Instruct` | Qwen 免费(硅基流动) | 免费模型 |
| `Pro/deepseek-ai/DeepSeek-V3.1-Terminus` | DeepSeek-V3.1-Terminus (硅基流动) | 专业版 |
| `deepseek-ai/DeepSeek-R1` | DeepSeek-R1 (硅基流动) | R1版本 |
| `Qwen/Qwen3-235B-A22B-Thinking-2507` | Qwen3-235B (硅基流动) | 大模型 |
| `zai-org/GLM-4.6` | 智谱(硅基流动) | 智谱模型 |
| `moonshotai/Kimi-K2-Instruct-0905` | Kimi (硅基流动) | Kimi模型 |
| `Ring-1T` | 蚂蚁百灵 (硅基流动) | 蚂蚁模型 |
| `step3` | 阶跃星辰(硅基流动) | 阶跃模型 |

---

## 🎯 建议

### 短期方案（保持现状）

1. **修改默认模型**：编辑 `.env` 文件，修改 `DEEPSEEK_MODEL_NAME`
2. **主力选股页面**：使用页面内的模型选择（已生效）

### 长期方案（推荐）

修改代码，让侧边栏的模型选择真正全局生效：

1. 修改 `app.py` 中所有使用模型的地方
2. 优先使用 `st.session_state.selected_model`
3. 如果不存在或无效，回退到 `config.DEEPSEEK_MODEL_NAME`

这样可以：
- ✅ 通过UI快速切换模型
- ✅ 配置持久化（通过 `.env`）
- ✅ 用户体验更好

---

## 📚 相关文件

- **模型选项定义**：`model_config.py`
- **默认模型配置**：`.env` 文件中的 `DEEPSEEK_MODEL_NAME`
- **模型选择器**：`app.py` 的 `model_selector()` 函数
- **配置文件加载**：`config.py`
