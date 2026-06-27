"""
pywencai 安全调用辅助模块

解决 iwencai.com 服务器被屏蔽/返回 403 时
pywencai.get() 内部抛出 NoneType 异常的问题。

工作流程：
1. 先用 pywencai 直接调用（快速路径）
2. 失败后通过 Playwright 获取浏览器 cookies 重试（绕过 TLS 指纹限制）

💡 如遇选股失败，请在浏览器中登录 https://www.iwencai.com/screener
"""

import sys
import logging

logger = logging.getLogger(__name__)


def safe_get(query, loop=True, **kwargs):
    """
    安全调用 pywencai.get，捕获内部 NoneType 异常。
    
    自动降级：常规调用失败后，尝试用浏览器 cookies 重试。
    
    Args:
        query: 问财查询语句
        loop: 是否翻页获取全部数据
        **kwargs: 传递给 pywencai.get 的其它参数
        
    Returns:
        正常时返回 pywencai 结果，失败时返回 None
    """
    import pywencai

    # 尝试1: 直接调用（快速路径）
    result = _try_call(query, loop, **kwargs)
    if result is not None:
        return result

    print(f"[pywencai] ⚠️ 直接调用失败，尝试浏览器会话...")

    # 尝试2: 用浏览器 cookies 重试（绕过 TLS 指纹验证）  
    try:
        from utils.iwencai_browser import get_browser_cookies
        cookie_str = get_browser_cookies()
        if cookie_str:
            kwargs_with_cookie = dict(kwargs)
            kwargs_with_cookie['cookie'] = cookie_str
            result = _try_call(query, loop, **kwargs_with_cookie)
            if result is not None:
                print(f"[pywencai] ✅ 浏览器会话成功，共获取 {len(result) if hasattr(result,'__len__') else '?'} 条数据")
                return result
            else:
                print(f"[pywencai] ❌ 浏览器会话也失败，选股功能暂时不可用")
                print(f"[pywencai] 💡 请用浏览器打开 https://www.iwencai.com/screener 并登录")
    except Exception as e:
        logger.debug(f"浏览器 cookies 方案也失败: {e}")

    return None


def _try_call(query, loop=True, **kwargs):
    """内部调用 pywencai.get，捕获异常"""
    import pywencai
    try:
        result = pywencai.get(query=query, loop=loop, **kwargs)
        return result
    except AttributeError as e:
        logger.debug(f"pywencai 内部异常: {e}")
        return None
    except Exception as e:
        logger.debug(f"pywencai 调用异常: {type(e).__name__}: {e}")
        return None
