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
        """保存配置到.env文件"""
        try:
            lines = []
            lines.append("# AI股票分析系统环境配置")
            lines.append("# 由系统自动生成和管理")
            lines.append("")
            
            # DeepSeek配置
            lines.append("# ========== DeepSeek API配置 ==========")
            lines.append(f'DEEPSEEK_API_KEY="{config.get("DEEPSEEK_API_KEY", "")}"')
            lines.append(f'DEEPSEEK_BASE_URL="{config.get("DEEPSEEK_BASE_URL", "https://api.deepseek.com/v1")}"')
            lines.append("")
            
            # Tushare配置
            lines.append("# ========== Tushare数据接口（可选）==========")
            lines.append(f'TUSHARE_TOKEN="{config.get("TUSHARE_TOKEN", "")}"')
            lines.append("")
            
            # MiniQMT配置
            lines.append("# ========== MiniQMT量化交易配置（可选）==========")
            lines.append(f'MINIQMT_ENABLED="{config.get("MINIQMT_ENABLED", "false")}"')
            lines.append(f'MINIQMT_ACCOUNT_ID="{config.get("MINIQMT_ACCOUNT_ID", "")}"')
            lines.append(f'MINIQMT_HOST="{config.get("MINIQMT_HOST", "127.0.0.1")}"')
            lines.append(f'MINIQMT_PORT="{config.get("MINIQMT_PORT", "58610")}"')
            lines.append("")
            
            # 邮件通知配置
            lines.append("# ========== 邮件通知配置（可选）==========")
            lines.append(f'EMAIL_ENABLED="{config.get("EMAIL_ENABLED", "false")}"')
            lines.append(f'SMTP_SERVER="{config.get("SMTP_SERVER", "")}"')
            lines.append(f'SMTP_PORT="{config.get("SMTP_PORT", "587")}"')
            lines.append(f'EMAIL_FROM="{config.get("EMAIL_FROM", "")}"')
            lines.append(f'EMAIL_PASSWORD="{config.get("EMAIL_PASSWORD", "")}"')
            lines.append(f'EMAIL_TO="{config.get("EMAIL_TO", "")}"')
            lines.append("")
            
            # Webhook通知配置
            lines.append("# ========== Webhook通知配置（可选）==========")
            lines.append(f'WEBHOOK_ENABLED="{config.get("WEBHOOK_ENABLED", "false")}"')
            lines.append(f'WEBHOOK_TYPE="{config.get("WEBHOOK_TYPE", "dingtalk")}"')
            lines.append(f'WEBHOOK_URL="{config.get("WEBHOOK_URL", "")}"')
            lines.append(f'WEBHOOK_KEYWORD="{config.get("WEBHOOK_KEYWORD", "aiagents通知")}"')
            
            with open(self.env_file, 'w', encoding='utf-8') as f:
                f.write('\n'.join(lines))
            
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
        # 检查必填项
        for key, info in self.default_config.items():
            if info["required"] and not config.get(key):
                return False, f"必填项 {info['description']} 不能为空"
        
        # 验证API Key格式（简单检查长度）
        if config.get("DEEPSEEK_API_KEY"):
            api_key = config.get("DEEPSEEK_API_KEY", "")
            if len(api_key) < 20:
                return False, "DeepSeek API Key格式不正确（长度太短）"
        
        return True, "配置验证通过"
    
    def reload_config(self):
        """重新加载配置（重新加载.env文件）"""
        from dotenv import load_dotenv
        # 强制覆盖已存在的环境变量
        load_dotenv(override=True)


# 全局配置管理器实例
config_manager = ConfigManager()

