"""
pywencai 安全调用辅助模块

解决 iwencai.com 服务器被屏蔽/返回 403 时
pywencai.get() 内部抛出 NoneType 异常的问题。
"""

import sys
import logging

logger = logging.getLogger(__name__)


def safe_get(query, loop=True, **kwargs):
    """
    安全调用 pywencai.get，捕获内部 NoneType 异常。
    
    当 iwencai 接口不可用时返回 None，由调用方自行处理降级。
    
    Args:
        query: 问财查询语句
        loop: 是否翻页获取全部数据
        **kwargs: 传递给 pywencai.get 的其它参数
        
    Returns:
        正常时返回 pywencai 结果，失败时返回 None
    """
    import pywencai

    try:
        result = pywencai.get(query=query, loop=loop, **kwargs)
        
        # pywencai 内部 get_robot_data 返回 None 后，
        # params.get('data') 抛出 AttributeError 被外层捕获，
        # 正常情况下 result 不会是 None
        return result

    except AttributeError as e:
        # pywencai 内部 'NoneType' object has no attribute 'get'
        # 意味着 iwencai 接口返回为空或被屏蔽（403）
        logger.debug(f"pywencai 内部异常: {e}")
        return None

    except Exception as e:
        logger.debug(f"pywencai 调用异常: {type(e).__name__}: {e}")
        return None
