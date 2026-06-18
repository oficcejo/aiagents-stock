"""
Akshare 请求补丁模块

解决 Akshare 因缺少请求头（User-Agent）导致东方财富等服务器
关闭连接（RemoteDisconnected）的问题。

工作原理：
1. 在 import akshare 之前调用 patch_requests()，全局注入默认请求头
2. 同时修补 akshare 自带的请求重试函数，确保 timeout 参数被传递
3. 提供 retry_on_failure 装饰器，方便包装有问题的 Akshare 接口
"""

import functools
import time
import random

# 默认请求头 — 模拟现代 Chrome 浏览器
DEFAULT_HEADERS = {
    'User-Agent': (
        'Mozilla/5.0 (Windows NT 10.0; Win64; x64) '
        'AppleWebKit/537.36 (KHTML, like Gecko) '
        'Chrome/120.0.0.0 Safari/537.36'
    ),
    'Accept': (
        'text/html,application/xhtml+xml,application/xml;q=0.9,'
        'image/avif,image/webp,image/apng,*/*;q=0.8'
    ),
    'Accept-Language': 'zh-CN,zh;q=0.9,en;q=0.8',
    'Accept-Encoding': 'gzip, deflate, br',
    'Connection': 'keep-alive',
    'Referer': 'https://quote.eastmoney.com/',
    'Cache-Control': 'no-cache',
}

# 多个 User-Agent 轮换，降低被屏蔽概率
USER_AGENTS = [
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36',
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36',
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:120.0) Gecko/20100101 Firefox/120.0',
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36 Edg/120.0.0.0',
]

_patched = False


def patch_requests():
    """
    全局修补 requests.get / requests.post / requests.request，
    注入默认请求头和超时，避免 Akshare 请求被东方财富服务器拒绝。
    
    在 import akshare 之前调用一次即可。
    """
    global _patched
    if _patched:
        return
    _patched = True

    import requests as req_lib

    # --- 保存原始函数 ---
    _original_get = req_lib.get
    _original_post = req_lib.post
    _original_request = req_lib.Session.request

    # --- 1. 修补 Session.request（所有 Session 方法底层都走这） ---
    @functools.wraps(_original_request)
    def _patched_session_request(self, method, url, **kwargs):
        # 合并默认请求头（用户传入的 headers 优先）
        headers = dict(DEFAULT_HEADERS)
        # 随机轮换 User-Agent
        headers['User-Agent'] = random.choice(USER_AGENTS)
        user_headers = kwargs.pop('headers', None)
        if user_headers:
            headers.update(user_headers)
        kwargs['headers'] = headers

        # 默认超时 30 秒
        if 'timeout' not in kwargs or kwargs['timeout'] is None:
            kwargs['timeout'] = 30

        return _original_request(self, method, url, **kwargs)

    req_lib.Session.request = _patched_session_request

    # --- 2. 修补 requests.get （兼容直接调用 requests.get 的代码） ---
    @functools.wraps(_original_get)
    def _patched_get(url, **kwargs):
        headers = dict(DEFAULT_HEADERS)
        headers['User-Agent'] = random.choice(USER_AGENTS)
        user_headers = kwargs.pop('headers', None)
        if user_headers:
            headers.update(user_headers)
        kwargs['headers'] = headers

        if 'timeout' not in kwargs or kwargs['timeout'] is None:
            kwargs['timeout'] = 30

        return _original_get(url, **kwargs)

    req_lib.get = _patched_get

    # --- 3. 修补 requests.post ---
    @functools.wraps(_original_post)
    def _patched_post(url, **kwargs):
        headers = dict(DEFAULT_HEADERS)
        headers['User-Agent'] = random.choice(USER_AGENTS)
        user_headers = kwargs.pop('headers', None)
        if user_headers:
            headers.update(user_headers)
        kwargs['headers'] = headers

        if 'timeout' not in kwargs or kwargs['timeout'] is None:
            kwargs['timeout'] = 30

        return _original_post(url, **kwargs)

    req_lib.post = _patched_post

    # --- 4. 修补 akshare 内部的 request 模块（如果有的话） ---
    try:
        import akshare as _ak
        if hasattr(_ak, 'request') and hasattr(_ak.request, 'make_request_with_retry_json'):
            _orig_retry = _ak.request.make_request_with_retry_json

            @functools.wraps(_orig_retry)
            def _patched_retry_json(url, params=None, headers=None, proxies=None, max_retries=3, retry_delay=1):
                if headers is None:
                    headers = {}
                final_headers = dict(DEFAULT_HEADERS)
                final_headers['User-Agent'] = random.choice(USER_AGENTS)
                final_headers.update(headers)
                return _orig_retry(url, params=params, headers=final_headers,
                                   proxies=proxies, max_retries=max_retries, retry_delay=retry_delay)

            _ak.request.make_request_with_retry_json = _patched_retry_json
    except (ImportError, AttributeError):
        pass

    print("[AkshareHelper] 请求补丁已应用 — 默认请求头 + 超时 30s")


def retry_on_failure(max_retries=3, base_delay=1.0, backoff=2.0, exceptions=(Exception,)):
    """
    重试装饰器 — 用于包装不稳定的数据获取函数。
    
    用法:
        @retry_on_failure(max_retries=3)
        def fetch_something():
            return ak.stock_xxx(...)
    """
    def decorator(func):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            last_exc = None
            for attempt in range(max_retries):
                try:
                    return func(*args, **kwargs)
                except exceptions as e:
                    last_exc = e
                    if attempt < max_retries - 1:
                        delay = base_delay * (backoff ** attempt) + random.uniform(0, 0.5)
                        print(f"[Retry] {func.__name__} 失败 (第{attempt+1}次): {e}, "
                              f"{delay:.1f}s 后重试...")
                        time.sleep(delay)
            raise last_exc
        return wrapper
    return decorator
