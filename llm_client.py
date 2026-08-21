"""
LLM客户端工厂

根据 .env 配置自动选择 AI 引擎：
- 设置了 ORCAROUTER_API_KEY → 使用 OrcaRouter（命名 OpenAI 兼容网关）
- 否则回落到 DeepSeek（原有默认引擎）
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
