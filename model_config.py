"""
模型配置文件
包含所有可用的AI模型选项
支持通过 .env 中的 DEFAULT_MODEL_NAME 自定义默认模型
"""
import config

# 预置模型列表（用户可以在UI中选择）
_preset_models = {
    "deepseek-chat": "DeepSeek Chat",
    "deepseek-reasoner": "DeepSeek Reasoner (推理增强)",
    "qwen-plus": "qwen-plus (阿里百炼)",
    "qwen-plus-latest": "qwen-plus-latest (阿里百炼)",
    "qwen-flash": "qwen-flash (阿里百炼)",
    "qwen-turbo": "qwen-turbo (阿里百炼)",
    "qwen3-max": "qwen-max (阿里百炼)",
    "qwen-long": "qwen-long (阿里百炼)",
    "deepseek-ai/DeepSeek-R1-0528-Qwen3-8B": "DeepSeek-R1 免费(硅基流动)",
    "Qwen/Qwen2.5-7B-Instruct": "Qwen 免费(硅基流动)",
    "Pro/deepseek-ai/DeepSeek-V3.1-Terminus": "DeepSeek-V3.1-Terminus (硅基流动)",
    "deepseek-ai/DeepSeek-R1": "DeepSeek-R1 (硅基流动)",
    "Qwen/Qwen3-235B-A22B-Thinking-2507": "Qwen3-235B (硅基流动)",
    "zai-org/GLM-4.6": "智谱(硅基流动)",
    "moonshotai/Kimi-K2-Instruct-0905": "Kimi (硅基流动)",
    "Ring-1T": "蚂蚁百灵 (硅基流动)",
    "step3": "阶跃星辰(硅基流动)",
}

# 获取 .env 中配置的默认模型名称
_default_model = config.DEFAULT_MODEL_NAME

# 如果 .env 中配置的默认模型不在预置列表中，自动将其加入列表首位
if _default_model and _default_model not in _preset_models:
    _preset_models = {_default_model: f"{_default_model} (自定义默认)"} | _preset_models

# 确保默认模型的显示名称带有 "(默认)" 标记
if _default_model in _preset_models:
    original_label = _preset_models[_default_model]
    if "(默认)" not in original_label:
        _preset_models[_default_model] = f"{original_label} (默认)"

# 导出模型选项字典，确保默认模型排在第一位
model_options = {}
if _default_model in _preset_models:
    model_options[_default_model] = _preset_models[_default_model]
for k, v in _preset_models.items():
    if k not in model_options:
        model_options[k] = v

# 导出默认模型名称，供其他模块使用
default_model_name = _default_model