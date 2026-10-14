"""
测试 Atlas Cloud LLM 客户端工厂

运行方式:
  python3 -m pytest test_atlascloud_client.py -v
"""

import os
import sys
import types
from unittest.mock import patch

import pytest

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Stub dotenv before importing config
_dotenv = types.ModuleType("dotenv")
_dotenv.load_dotenv = lambda *a, **k: None
sys.modules["dotenv"] = _dotenv


@pytest.fixture(autouse=True)
def clean_env():
    with patch.dict(os.environ, {}, clear=False):
        os.environ.pop("ATLASCLOUD_API_KEY", None)
        os.environ.pop("ATLASCLOUD_BASE_URL", None)
        yield


def test_factory_uses_atlascloud_when_configured():
    import config
    from deepseek_client import DeepSeekClient
    from llm_client import get_llm_client

    with patch.object(config, "ORCAROUTER_API_KEY", ""), \
         patch.object(config, "NVIDIA_API_KEY", ""), \
         patch.object(config, "ATLASCLOUD_API_KEY", "test-key"):
        client = get_llm_client(model="deepseek-ai/deepseek-v4-flash")
        assert isinstance(client, DeepSeekClient)
        assert client.client.base_url == "https://api.atlascloud.ai/v1/"
        assert client.api_key == "test-key"
        assert client.model == "deepseek-ai/deepseek-v4-flash"


def test_factory_prefers_nvidia_over_atlascloud():
    import config
    from llm_client import get_llm_client

    with patch.object(config, "ORCAROUTER_API_KEY", ""), \
         patch.object(config, "NVIDIA_API_KEY", "nv-key"), \
         patch.object(config, "ATLASCLOUD_API_KEY", "test-key"):
        client = get_llm_client()
        assert client.api_key == "nv-key"


def test_atlascloud_default_base_url():
    import config

    assert config.ATLASCLOUD_BASE_URL == "https://api.atlascloud.ai/v1"


def test_config_manager_accepts_atlascloud_only():
    from config_manager import config_manager

    ok, _ = config_manager.validate_config({
        "DEEPSEEK_API_KEY": "",
        "ATLASCLOUD_API_KEY": "test-key-1234567890",
    })
    assert ok is True
