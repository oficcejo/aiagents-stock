"""
测试 Cheaper Inference LLM 客户端工厂

运行方式:
  # 无需 API key，单元测试全部通过
  python3 -m pytest test_cheaperinference_client.py -v

覆盖:
  - 设置了 CHEAPER_INFERENCE_API_KEY 时，工厂返回 CheaperInferenceClient
  - OrcaRouter / NVIDIA 已配置时，优先级保持不变
  - CheaperInferenceClient 使用 Cheaper Inference 的 base_url 与模型
"""

import pytest
import sys
import os
from unittest.mock import patch

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Stub dotenv before importing config
import types
_dotenv = types.ModuleType("dotenv")
_dotenv.load_dotenv = lambda *a, **k: None
sys.modules["dotenv"] = _dotenv


@pytest.fixture(autouse=True)
def clean_env():
    """隔离 CHEAPER_INFERENCE_* 环境变量"""
    with patch.dict(os.environ, {}, clear=False):
        os.environ.pop("CHEAPER_INFERENCE_API_KEY", None)
        os.environ.pop("CHEAPER_INFERENCE_BASE_URL", None)
        os.environ.pop("CHEAPER_INFERENCE_MODEL", None)
        yield


def test_factory_returns_cheaperinference_when_configured():
    import config
    from llm_client import get_llm_client

    with patch.object(config, "ORCAROUTER_API_KEY", ""), \
         patch.object(config, "NVIDIA_API_KEY", ""), \
         patch.object(config, "CHEAPER_INFERENCE_API_KEY", "ci_test_123"):
        client = get_llm_client()
        from cheaperinference_client import CheaperInferenceClient
        assert isinstance(client, CheaperInferenceClient)
        assert client.client.base_url == "https://api.cheaperinference.com/v1/"
        assert client.model == "gpt-5.4-mini"


def test_orcarouter_keeps_priority_over_cheaperinference():
    import config
    from llm_client import get_llm_client

    with patch.object(config, "ORCAROUTER_API_KEY", "sk-orca-test-123"), \
         patch.object(config, "CHEAPER_INFERENCE_API_KEY", "ci_test_123"):
        client = get_llm_client()
        from orcarouter_client import OrcaRouterClient
        assert isinstance(client, OrcaRouterClient)


def test_cheaperinference_default_base_url_and_model():
    import config

    assert config.CHEAPER_INFERENCE_BASE_URL == "https://api.cheaperinference.com/v1"
    assert config.CHEAPER_INFERENCE_MODEL == "gpt-5.4-mini"


def test_cheaperinference_custom_model_passed_through():
    import config
    from llm_client import get_llm_client

    with patch.object(config, "ORCAROUTER_API_KEY", ""), \
         patch.object(config, "NVIDIA_API_KEY", ""), \
         patch.object(config, "CHEAPER_INFERENCE_API_KEY", "ci_test_123"):
        client = get_llm_client(model="deepseek-v4-flash")
        assert client.model == "deepseek-v4-flash"


def test_cheaperinference_maps_deepseek_default_placeholder():
    """显式传入 DeepSeek 默认占位模型名时，应落到 Cheaper Inference 默认模型。"""
    import config
    from llm_client import get_llm_client

    with patch.object(config, "ORCAROUTER_API_KEY", ""), \
         patch.object(config, "NVIDIA_API_KEY", ""), \
         patch.object(config, "CHEAPER_INFERENCE_API_KEY", "ci_test_123"):
        client = get_llm_client(model="deepseek-chat")
        assert client.model == "gpt-5.4-mini"


def test_config_manager_accepts_cheaperinference_only():
    """仅配置 Cheaper Inference 密钥时，DeepSeek 密钥不再必填。"""
    from config_manager import config_manager

    ok, msg = config_manager.validate_config({
        "DEEPSEEK_API_KEY": "",
        "CHEAPER_INFERENCE_API_KEY": "ci_test_1234567890",
    })
    assert ok is True
