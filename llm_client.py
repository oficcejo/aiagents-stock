"""
LLM客户端工厂

根据 .env 配置自动选择 AI 引擎：
- 设置了 ORCAROUTER_API_KEY → 使用 OrcaRouter（命名 OpenAI 兼容网关）
- 否则回落到 DeepSeek（原有默认引擎）

另提供 TypeSafe Jev 结构化决策客户端工厂（与聊天引擎独立）：
- 设置了 TYPESAFE_API_KEY → get_jev_client() 返回 JevDecisionClient
- 否则返回 None（结构化决策能力关闭，调用点走既有文本链路）
"""
import config
from deepseek_client import DeepSeekClient


def get_llm_client(model=None):
    """返回当前配置对应的 LLM 客户端。

    Args:
        model: 可选的模型名称覆盖，默认从对应 provider 的配置读取。
    """
    if config.ORCAROUTER_API_KEY:
        from orcarouter_client import OrcaRouterClient
        return OrcaRouterClient(model=model)
    return DeepSeekClient(model=model)


def get_jev_client():
    """返回 TypeSafe Jev 结构化决策客户端；未配置 TYPESAFE_API_KEY 时返回 None。

    调用方约定：返回 None 或后续 ask() 抛 JevError 时，必须降级回既有
    DeepSeek 文本 + 正则解析链路（降级链在调用点适配层实现）。
    """
    if not config.TYPESAFE_API_KEY:
        return None
    try:
        from typesafe_decision_client import JevDecisionClient
        return JevDecisionClient()
    except Exception as e:
        print(f"⚠️ Jev 决策客户端初始化失败，回退文本链路: {e}")
        return None


def compute_price_fields(current_price):
    """按现价与 config 百分比常量计算价位字段（Jev 决策链路专用）。

    输出字符串格式与 docs/UNIFIED_ANALYSIS_SPEC.md 保持一致，保证下游
    split("-") / re.findall 解析兼容；同时附带数值字段供直接使用。

    Args:
        current_price: 当前价格（float）
    Returns:
        dict 或 None（价格非法时返回 None，由调用点降级）
    """
    try:
        price = float(current_price)
        if price <= 0:
            return None
    except (TypeError, ValueError):
        return None

    entry_min = price * (1 - config.PRICE_ENTRY_PCT)
    take_profit = price * (1 + config.PRICE_TAKE_PROFIT_PCT)
    stop_loss = price * (1 - config.PRICE_STOP_LOSS_PCT)
    return {
        # 字符串字段：与统一规范格式一致（如 "10.20-10.40"）
        "entry_range": f"{entry_min:.2f}-{price:.2f}",
        "take_profit": f"{take_profit:.2f}",
        "stop_loss": f"{stop_loss:.2f}",
        "target_price": f"{take_profit:.2f}",
        # 数值字段：供新代码直接读取，避免再走文本解析
        "entry_min": round(entry_min, 2),
        "entry_max": round(price, 2),
        "take_profit_value": round(take_profit, 2),
        "stop_loss_value": round(stop_loss, 2),
        "target_price_value": round(take_profit, 2),
    }
