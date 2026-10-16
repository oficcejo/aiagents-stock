"""统一的数据文件目录定位。

所有 SQLite 库统一存放在项目根目录 data/ 下：
- Docker 部署时 data/ 由 docker-compose 挂载到宿主机，重建容器数据不丢失
- 本地直接运行时即项目根目录下的 data/

可用环境变量 DATA_DIR 覆盖存放位置。
"""

import os

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_DIR = os.environ.get("DATA_DIR") or os.path.join(PROJECT_ROOT, "data")

os.makedirs(DATA_DIR, exist_ok=True)


def data_file(name: str) -> str:
    """返回 data/ 目录下指定文件名的绝对路径"""
    return os.path.join(DATA_DIR, name)
