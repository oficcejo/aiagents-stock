"""
测试 OrcaRouter LLM 客户端工厂

运行方式:
  # 无需 API key，单元测试全部通过
  python3 -m pytest test_orcarouter_client.py -v

覆盖:
  - 设置了 ORCAROUTER_API_KEY 时，工厂返回 OrcaRouterClient
  - 未设置 ORCAROUTER_API_KEY 时，工厂返回 DeepSeekClient（原有默认行为）
  - OrcaRouterClient 使用 OrcaRouter 的 base_url 与模型
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
    """隔离 ORCAROUTER_API_KEY 环境变量"""
    with patch.dict(os.environ, {}, clear=False):
        os.environ.pop("ORCAROUTER_API_KEY", None)
        os.environ.pop("ORCAROUTER_BASE_URL", None)
        os.environ.pop("ORCAROUTER_MODEL", None)
        yield


def test_factory_returns_orcarouter_when_configured():
    import config
    from llm_client import get_llm_client

    with patch.object(config, "ORCAROUTER_API_KEY", "sk-orca-test-123"):
        client = get_llm_client()
        from orcarouter_client import OrcaRouterClient
        assert isinstance(client, OrcaRouterClient)
        assert client.client.base_url == "https://api.orcarouter.ai/v1/"
        assert client.model == "orcarouter/auto"


def test_factory_returns_deepseek_by_default():
    import config
    from llm_client import get_llm_client

    with patch.object(config, "ORCAROUTER_API_KEY", ""), \
         patch.object(config, "DEEPSEEK_API_KEY", "sk-deepseek-test-123"):
        client = get_llm_client()
        from deepseek_client import DeepSeekClient
        assert isinstance(client, DeepSeekClient)


def test_orcarouter_default_base_url_and_model():
    import config

    assert config.ORCAROUTER_BASE_URL == "https://api.orcarouter.ai/v1"
    assert config.ORCAROUTER_MODEL == "orcarouter/auto"


def test_orcarouter_custom_model_passed_through():
    import config
    from llm_client import get_llm_client

    with patch.object(config, "ORCAROUTER_API_KEY", "sk-orca-test-123"):
        client = get_llm_client(model="deepseek/deepseek-v4-pro")
        assert client.model == "deepseek/deepseek-v4-pro"


def test_orcarouter_maps_deepseek_default_placeholder():
    """显式传入 DeepSeek 默认占位模型名时，应落到 OrcaRouter 默认模型。"""
    import config
    from llm_client import get_llm_client

    with patch.object(config, "ORCAROUTER_API_KEY", "sk-orca-test-123"):
        client = get_llm_client(model="deepseek-chat")
        assert client.model == "orcarouter/auto"


def test_config_manager_accepts_orcarouter_only():
    """仅配置 OrcaRouter 密钥时，DeepSeek 密钥不再必填。"""
    from config_manager import config_manager

    ok, msg = config_manager.validate_config({
        "DEEPSEEK_API_KEY": "",
        "ORCAROUTER_API_KEY": "sk-orca-1234567890",
    })
    assert ok is True

    ok, msg = config_manager.validate_config({
        "DEEPSEEK_API_KEY": "sk-deepseek-1234567890",
        "ORCAROUTER_API_KEY": "",
    })
    assert ok is True
