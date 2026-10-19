"""
环境配置管理模块
用于读取和保存.env配置文件
"""

import os
from pathlib import Path
from typing import Dict, Any


class ConfigManager:
    """配置管理器"""
    
    def __init__(self, env_file: str = ".env"):
        self.env_file = Path(env_file)
        self.default_config = {
            "DEEPSEEK_API_KEY": {
                "value": "",
                "description": "DeepSeek API密钥",
                "required": True,
                "type": "password"
            },
            "DEEPSEEK_BASE_URL": {
                "value": "https://api.deepseek.com/v1",
                "description": "DeepSeek API地址",
                "required": False,
                "type": "text"
            },
            "DEFAULT_MODEL_NAME": {
                "value": "deepseek-chat",
                "description": "AI模型名称（支持OpenAI兼容模型）",
                "required": False,
                "type": "text"
            },
            "ORCAROUTER_API_KEY": {
                "value": "",
                "description": "OrcaRouter API密钥（可选，设置后优先使用OrcaRouter引擎）",
                "required": False,
                "type": "password"
            },
            "ORCAROUTER_BASE_URL": {
                "value": "https://api.orcarouter.ai/v1",
                "description": "OrcaRouter API地址",
                "required": False,
                "type": "text"
            },
            "ORCAROUTER_MODEL": {
                "value": "orcarouter/auto",
                "description": "OrcaRouter模型名称",
                "required": False,
                "type": "text"
            },
            "NVIDIA_API_KEY": {
                "value": "",
                "description": "NVIDIA NIM API密钥（可选，OpenAI 兼容，issue #47）",
                "required": False,
                "type": "password"
            },
            "NVIDIA_BASE_URL": {
                "value": "https://integrate.api.nvidia.com/v1",
                "description": "NVIDIA NIM API地址",
                "required": False,
                "type": "text"
            },
            "CHEAPER_INFERENCE_API_KEY": {
                "value": "",
                "description": "Cheaper Inference API密钥（可选，OpenAI 兼容）",
                "required": False,
                "type": "password"
            },
            "CHEAPER_INFERENCE_BASE_URL": {
                "value": "https://api.cheaperinference.com/v1",
                "description": "Cheaper Inference API地址",
                "required": False,
                "type": "text"
            },
            "CHEAPER_INFERENCE_MODEL": {
                "value": "gpt-5.4-mini",
                "description": "Cheaper Inference模型名称",
                "required": False,
                "type": "text"
            },
            "TDX_ENABLED": {
                "value": "false",
                "description": "启用TDX本地行情数据源",
                "required": False,
                "type": "boolean"
            },
            "TYPESAFE_API_KEY": {
                "value": "",
                "description": "TypeSafe Jev 结构化决策密钥（可选）",
                "required": False,
                "type": "password"
            },
            "MINIQMT_USERDATA_PATH": {
                "value": "",
                "description": "miniQMT userdata 路径（如 C:\\国金QMT交易端\\userdata_mini）",
                "required": False,
                "type": "text"
            },
            "TUSHARE_TOKEN": {
                "value": "",
                "description": "Tushare数据接口Token（可选）",
                "required": False,
                "type": "password"
            },
            "MINIQMT_ENABLED": {
                "value": "false",
                "description": "启用MiniQMT量化交易",
                "required": False,
                "type": "boolean"
            },
            "MINIQMT_ACCOUNT_ID": {
                "value": "",
                "description": "MiniQMT账户ID",
                "required": False,
                "type": "text"
            },
            "MINIQMT_HOST": {
                "value": "127.0.0.1",
                "description": "MiniQMT服务器地址",
                "required": False,
                "type": "text"
            },
            "MINIQMT_PORT": {
                "value": "58610",
                "description": "MiniQMT服务器端口",
                "required": False,
                "type": "text"
            },
            "EMAIL_ENABLED": {
                "value": "false",
                "description": "启用邮件通知",
                "required": False,
                "type": "boolean"
            },
            "SMTP_SERVER": {
                "value": "",
                "description": "SMTP服务器地址",
                "required": False,
                "type": "text"
            },
            "SMTP_PORT": {
                "value": "587",
                "description": "SMTP服务器端口",
                "required": False,
                "type": "text"
            },
            "EMAIL_FROM": {
                "value": "",
                "description": "发件人邮箱",
                "required": False,
                "type": "text"
            },
            "EMAIL_PASSWORD": {
                "value": "",
                "description": "邮箱授权码",
                "required": False,
                "type": "password"
            },
            "EMAIL_TO": {
                "value": "",
                "description": "收件人邮箱",
                "required": False,
                "type": "text"
            },
            "WEBHOOK_ENABLED": {
                "value": "false",
                "description": "启用Webhook通知",
                "required": False,
                "type": "boolean"
            },
            "WEBHOOK_TYPE": {
                "value": "dingtalk",
                "description": "Webhook类型（dingtalk/feishu）",
                "required": False,
                "type": "select",
                "options": ["dingtalk", "feishu"]
            },
            "WEBHOOK_URL": {
                "value": "",
                "description": "Webhook地址",
                "required": False,
                "type": "text"
            },
            "WEBHOOK_KEYWORD": {
                "value": "aiagents通知",
                "description": "Webhook自定义关键词（钉钉安全验证）",
                "required": False,
                "type": "text"
            },
            "TDX_BASE_URL": {
                "value": "http://127.0.0.1:8080",
                "description": "通达信数据源API地址",
                "required": False,
                "type": "text"
            },
            "YDC_API_KEY": {
                "value": "",
                "description": "You.com Research API密钥",
                "required": False,
                "type": "password"
            },
            "YDC_RESEARCH_EFFORT": {
                "value": "standard",
                "description": "You.com 搜索深度 (lite/standard/deep/exhaustive)",
                "required": False,
                "type": "select",
                "options": ["lite", "standard", "deep", "exhaustive"]
            },
        }
    
    def read_env(self) -> Dict[str, str]:
        """读取.env文件"""
        config = {}
        
        if not self.env_file.exists():
            # 如果文件不存在，返回默认配置的值
            for key, info in self.default_config.items():
                config[key] = info["value"]
            return config
        
        try:
            with open(self.env_file, 'r', encoding='utf-8') as f:
                for line in f:
                    line = line.strip()
                    # 跳过空行和注释
                    if not line or line.startswith('#'):
                        continue
                    
                    # 解析键值对
                    if '=' in line:
                        key, value = line.split('=', 1)
                        key = key.strip()
                        value = value.strip()
                        
                        # 移除引号
                        if value.startswith('"') and value.endswith('"'):
                            value = value[1:-1]
                        elif value.startswith("'") and value.endswith("'"):
                            value = value[1:-1]
                        
                        config[key] = value
        except Exception as e:
            print(f"读取.env文件失败: {e}")
        
        # 确保所有默认配置项都存在
        for key, info in self.default_config.items():
            if key not in config:
                config[key] = info["value"]
        
        return config
    
    def write_env(self, config: Dict[str, str]) -> bool:
        """保存配置到.env文件。

        采用「按行合并」策略（issue #43）：
        - 已存在的键原地更新，注释与未知自定义键原样保留
        - 新键追加到文件末尾
        - 避免整文件重写导致 TDX_ENABLED / TYPESAFE_* 等手工配置丢失
        """
        try:
            current_env = self.read_env()
            # 只合并本次传入的键；未传入的键保持 .env 原值
            updates = {k: ('' if v is None else str(v)) for k, v in config.items()}

            lines = []
            if self.env_file.exists():
                lines = self.env_file.read_text(encoding='utf-8').splitlines()
            else:
                lines = [
                    "# AI股票分析系统环境配置",
                    "# 由系统自动生成和管理",
                    "",
                ]

            key_to_idx = {}
            for i, line in enumerate(lines):
                s = line.strip()
                if not s or s.startswith('#') or '=' not in s:
                    continue
                k = s.split('=', 1)[0].strip()
                if k:
                    key_to_idx[k] = i

            def fmt(k, v):
                v = '' if v is None else str(v)
                # 已含引号则原样；否则统一双引号包裹
                if (v.startswith('"') and v.endswith('"') and len(v) >= 2) or (
                    v.startswith("'") and v.endswith("'") and len(v) >= 2
                ):
                    return f'{k}={v}'
                return f'{k}="{v}"'

            for k, v in updates.items():
                line = fmt(k, v)
                if k in key_to_idx:
                    lines[key_to_idx[k]] = line
                else:
                    if lines and lines[-1].strip() != '':
                        lines.append('')
                    lines.append(line)
                    key_to_idx[k] = len(lines) - 1

            # 确保 default_config 中的键存在（用当前值或默认值）
            for k, info in self.default_config.items():
                if k not in key_to_idx:
                    val = current_env.get(k, info.get("value", ""))
                    lines.append(fmt(k, val))
                    key_to_idx[k] = len(lines) - 1

            self.env_file.write_text('\n'.join(lines) + '\n', encoding='utf-8')
            return True
        except Exception as e:
            print(f"保存.env文件失败: {e}")
            return False
    
    def get_config_info(self) -> Dict[str, Dict[str, Any]]:
        """获取配置信息（包含描述、类型等）"""
        current_values = self.read_env()
        
        config_info = {}
        for key, info in self.default_config.items():
            config_info[key] = {
                "value": current_values.get(key, info["value"]),
                "description": info["description"],
                "required": info["required"],
                "type": info["type"]
            }
            # 如果有options字段，也包含进去
            if "options" in info:
                config_info[key]["options"] = info["options"]
        
        return config_info
    
    def validate_config(self, config: Dict[str, str]) -> tuple[bool, str]:
        """验证配置"""
        # 设置了任一备用 OpenAI 兼容网关密钥时，DeepSeek 密钥不再是必填项
        has_alt_engine = bool(
            config.get("ORCAROUTER_API_KEY")
            or config.get("NVIDIA_API_KEY")
            or config.get("CHEAPER_INFERENCE_API_KEY")
        )

        # 检查必填项
        for key, info in self.default_config.items():
            if key == "DEEPSEEK_API_KEY" and has_alt_engine:
                continue
            if info["required"] and not config.get(key):
                return False, f"必填项 {info['description']} 不能为空"

        # 验证API Key格式（简单检查长度）
        if config.get("DEEPSEEK_API_KEY"):
            api_key = config.get("DEEPSEEK_API_KEY", "")
            if len(api_key) < 20:
                return False, "DeepSeek API Key格式不正确（长度太短）"

        return True, "配置验证通过"

    def reload_config(self):
        """重新加载配置（重新加载.env文件，并刷新 config 模块常量）"""
        from dotenv import load_dotenv
        # 强制覆盖已存在的环境变量
        load_dotenv(override=True)
        # 刷新 config 模块级常量，避免保存后仍用旧模型/旧密钥（issue #43）
        try:
            import config as config_module
            if hasattr(config_module, 'reload_from_env'):
                config_module.reload_from_env()
        except Exception as e:
            print(f"刷新 config 模块失败: {e}")


# 全局配置管理器实例
config_manager = ConfigManager()

