import os
from dotenv import load_dotenv

# 加载环境变量（override=True 强制覆盖已存在的环境变量）
load_dotenv(override=True)

# DeepSeek API配置
DEEPSEEK_API_KEY = os.getenv("DEEPSEEK_API_KEY", "")
DEEPSEEK_BASE_URL = os.getenv("DEEPSEEK_BASE_URL", "https://api.deepseek.com/v1")

# OrcaRouter API配置（可选，设置了 ORCAROUTER_API_KEY 后作为 AI 引擎使用）
ORCAROUTER_API_KEY = os.getenv("ORCAROUTER_API_KEY", "")
ORCAROUTER_BASE_URL = os.getenv("ORCAROUTER_BASE_URL", "https://api.orcarouter.ai/v1")
ORCAROUTER_MODEL = os.getenv("ORCAROUTER_MODEL", "orcarouter/auto")

# 默认AI模型名称（支持任何OpenAI兼容的模型）
# 设置了 ORCAROUTER_API_KEY 时，默认模型自动落到 OrcaRouter 的配置模型
DEFAULT_MODEL_NAME = os.getenv(
    "DEFAULT_MODEL_NAME",
    ORCAROUTER_MODEL if ORCAROUTER_API_KEY else "deepseek-chat"
)

# TypeSafe Jev 结构化决策引擎配置（可选，设置了 TYPESAFE_API_KEY 后启用）
# 文档：https://docs.typesafe.ai/introduction
TYPESAFE_API_KEY = os.getenv("TYPESAFE_API_KEY", "")
TYPESAFE_BASE_URL = os.getenv("TYPESAFE_BASE_URL", "https://api.typesafe.ai/v1")
TYPESAFE_MODEL = os.getenv("TYPESAFE_MODEL", "jev-latest")
# Jev 请求超时（秒）与重试次数（重试1次，与数据源降级防封禁策略一致）
TYPESAFE_TIMEOUT_SEC = float(os.getenv("TYPESAFE_TIMEOUT_SEC", "10"))
TYPESAFE_MAX_RETRIES = 1
# Jev 关键答案置信度低于该值时视为低质量响应，降级回 DeepSeek 文本链路
JEV_MIN_CONFIDENCE = float(os.getenv("JEV_MIN_CONFIDENCE", "0.5"))
# 新闻告警门控：仅置信度不低于该值的 Jev 利好/利空结论才触发 Webhook 推送
JEV_ALERT_MIN_CONFIDENCE = float(os.getenv("JEV_ALERT_MIN_CONFIDENCE", "0.6"))

# 价位计算常量（Jev 决策链路下 entry_range/take_profit/stop_loss 由代码按现价计算，
# 不再从模型文本正则提取）
PRICE_ENTRY_PCT = 0.02        # 入场区间下限 = 现价 -2%
PRICE_TAKE_PROFIT_PCT = 0.08  # 止盈位 = 现价 +8%
PRICE_STOP_LOSS_PCT = 0.05    # 止损位 = 现价 -5%

# 批量选股多维度加权合成总分的权重（Jev 原子 Score 问题由代码侧合成）
JEV_SCORE_WEIGHTS = {
    'technical': 0.30,    # 技术面强度
    'fundamental': 0.30,  # 基本面质量
    'fund_flow': 0.25,    # 资金面
    'risk': 0.15,         # 风险维度（分数越高风险越低）
}

# You.com API配置
YDC_API_KEY = os.getenv("YDC_API_KEY", "")

# 其他配置
TUSHARE_TOKEN = os.getenv("TUSHARE_TOKEN", "")

# 股票数据源配置
DEFAULT_PERIOD = "1y"  # 默认获取1年数据
DEFAULT_INTERVAL = "1d"  # 默认日线数据

# MiniQMT量化交易配置
MINIQMT_CONFIG = {
    'enabled': os.getenv("MINIQMT_ENABLED", "false").lower() == "true",
    'account_id': os.getenv("MINIQMT_ACCOUNT_ID", ""),
    'host': os.getenv("MINIQMT_HOST", "127.0.0.1"),
    'port': int(os.getenv("MINIQMT_PORT", "58610")),
}

# TDX股票数据API配置项目地址github.com/oficcejo/tdx-api
TDX_CONFIG = {
    'enabled': os.getenv("TDX_ENABLED", "false").lower() == "true",
    'base_url': os.getenv("TDX_BASE_URL", "http://192.168.1.222:8181"),
}