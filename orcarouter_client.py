import openai
from deepseek_client import DeepSeekClient
import config


class OrcaRouterClient(DeepSeekClient):
    """OrcaRouter API客户端

    基于 DeepSeekClient，复用其全部技术面/基本面/资金面分析 prompt 与
    chat/completions 调用逻辑，仅替换为 OrcaRouter 的 OpenAI 兼容网关配置。
    """

    # 系统的 DeepSeek 默认占位模型名：视为"未显式指定模型"
    _deepseek_default_placeholder = "deepseek-chat"

    def __init__(self, model=None):
        if not model or model == self._deepseek_default_placeholder:
            model = config.ORCAROUTER_MODEL
        self.model = model
        self.client = openai.OpenAI(
            api_key=config.ORCAROUTER_API_KEY,
            base_url=config.ORCAROUTER_BASE_URL
        )
