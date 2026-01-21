import os
from pathlib import Path
from dotenv import load_dotenv

# 获取当前文件的目录
current_dir = Path(__file__).parent.absolute()

# 尝试多个可能的 .env 文件路径
env_paths = [
    current_dir / '.env',           # 当前目录
    Path('.env'),                   # 工作目录
    Path('/app/.env'),              # Docker 容器中的路径
]

env_loaded = False
env_file_path = None

# 尝试加载 .env 文件
for env_path in env_paths:
    if env_path.exists():
        env_loaded = load_dotenv(env_path, override=True)
        if env_loaded:
            env_file_path = env_path
            print(f"[config.py] ✅ 成功加载 .env 文件: {env_path}")
            break
    else:
        print(f"[config.py] .env 文件不存在: {env_path}")

# 如果都没有找到，尝试从当前目录加载（load_dotenv 的默认行为）
if not env_loaded:
    env_loaded = load_dotenv(override=True)
    print(f"[config.py] 尝试默认路径加载 .env: {'成功' if env_loaded else '失败'}")

# DeepSeek API配置
DEEPSEEK_API_KEY = os.getenv("DEEPSEEK_API_KEY", "")
DEEPSEEK_BASE_URL = os.getenv("DEEPSEEK_BASE_URL", "https://api.deepseek.com/v1")
DEEPSEEK_MODEL_NAME = os.getenv("DEEPSEEK_MODEL_NAME", "deepseek-chat")

# 调试：打印配置值（隐藏敏感信息）
print(f"[config.py] =========================================")
print(f"[config.py] 配置加载结果:")
print(f"[config.py]   DEEPSEEK_MODEL_NAME: {DEEPSEEK_MODEL_NAME}")
print(f"[config.py]   DEEPSEEK_BASE_URL: {DEEPSEEK_BASE_URL}")
print(f"[config.py]   DEEPSEEK_API_KEY: {'已设置' if DEEPSEEK_API_KEY else '未设置'}")
print(f"[config.py]   环境变量 DEEPSEEK_MODEL_NAME: {os.getenv('DEEPSEEK_MODEL_NAME', '未设置')}")

# 如果 DEEPSEEK_MODEL_NAME 仍然是默认值，尝试从 .env 文件直接读取
if DEEPSEEK_MODEL_NAME == "deepseek-chat":
    print("[config.py] ⚠️ 警告: DEEPSEEK_MODEL_NAME 仍然是默认值 'deepseek-chat'")
    print("[config.py] 尝试直接读取 .env 文件...")
    
    # 尝试所有可能的路径
    for env_path in env_paths:
        if env_path.exists():
            print(f"[config.py] 检查 .env 文件: {env_path}")
            try:
                with open(env_path, 'r', encoding='utf-8') as f:
                    for line_num, line in enumerate(f, 1):
                        line = line.strip()
                        # 跳过空行和注释
                        if not line or line.startswith('#'):
                            continue
                        if 'DEEPSEEK_MODEL_NAME' in line and '=' in line:
                            value = line.split('=', 1)[1].strip().strip('"').strip("'")
                            if value and value != "deepseek-chat":
                                DEEPSEEK_MODEL_NAME = value
                                # 更新环境变量
                                os.environ['DEEPSEEK_MODEL_NAME'] = value
                                print(f"[config.py] ✅ 从 .env 文件直接读取到 DEEPSEEK_MODEL_NAME: {DEEPSEEK_MODEL_NAME} (第 {line_num} 行)")
                                break
            except Exception as e:
                print(f"[config.py] ❌ 读取 .env 文件失败 ({env_path}): {e}")
    
print(f"[config.py] 最终使用的 DEEPSEEK_MODEL_NAME: {DEEPSEEK_MODEL_NAME}")
print(f"[config.py] =========================================")

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