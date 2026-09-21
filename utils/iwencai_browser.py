"""
iwencai 浏览器会话模块

使用 Playwright (Chromium) 启动真实浏览器获取 cookies，
解决 pywencai 因 TLS 指纹 / IP 限制被 iwencai 服务器
要求验证码 (CAPTCHA) 的问题。

工作原理：
1. 启动无头 Chrome 浏览器
2. 访问 iwencai.com 获取真实浏览器 cookies
3. 将 cookies 注入 pywencai 的请求头
4. pywencai 使用浏览器级别的会话发送查询

使用方式（在 safe_get 中自动调用）：
    from utils.iwencai_browser import get_browser_cookies
    cookies = get_browser_cookies()
    result = pywencai.get(query=..., cookie=cookies)
"""

import time
import logging

logger = logging.getLogger(__name__)

import os
from pathlib import Path

# 缓存浏览器 cookies（每次有效期为5分钟）
_cookie_cache = None
_cookie_time = 0
_COOKIE_TTL = 300  # 缓存时间（秒）

PROJECT_ROOT = Path(__file__).resolve().parent.parent
COOKIE_FILE = PROJECT_ROOT / ".iwencai_cookie.txt"
PROFILE_DIR = PROJECT_ROOT / ".iwencai_profile"


def get_browser_cookies(force_refresh=False):
    """
    获取 iwencai 的有效 cookies。
    
    优先级：
    1. 环境变量 IWENCAI_COOKIE
    2. 本地缓存文件 .iwencai_cookie.txt
    3. 内存缓存（5分钟有效）
    4. Playwright 持久化浏览器会话 (.iwencai_profile)
    """
    global _cookie_cache, _cookie_time

    # 1. 优先读取环境变量
    env_cookie = os.getenv("IWENCAI_COOKIE", "").strip()
    if env_cookie:
        return env_cookie

    # 2. 读取本地 Cookie 保存文件
    if not force_refresh and COOKIE_FILE.exists():
        try:
            saved_cookie = COOKIE_FILE.read_text(encoding="utf-8").strip()
            if saved_cookie and len(saved_cookie) > 20:
                _cookie_cache = saved_cookie
                _cookie_time = time.time()
                return saved_cookie
        except Exception:
            pass

    # 3. 如果内存缓存还在有效期内，直接返回
    now = time.time()
    if not force_refresh and _cookie_cache and (now - _cookie_time) < _COOKIE_TTL:
        return _cookie_cache
    
    print(f"[iwencai] 🚀 启动浏览器获取会话...")
    
    try:
        from playwright.sync_api import sync_playwright
    except ImportError:
        logger.warning("playwright 未安装，无法获取浏览器 cookies")
        return ""
    
    try:
        with sync_playwright() as p:
            # 使用持久化上下文保存登录状态
            PROFILE_DIR.mkdir(exist_ok=True)
            context = p.chromium.launch_persistent_context(
                user_data_dir=str(PROFILE_DIR),
                headless=True,
                viewport={'width': 1280, 'height': 800},
                user_agent=(
                    'Mozilla/5.0 (Windows NT 10.0; Win64; x64) '
                    'AppleWebKit/537.36 (KHTML, like Gecko) '
                    'Chrome/120.0.0.0 Safari/537.36'
                ),
            )
            page = context.new_page()
            
            # 访问问财选股页面触发 cookie 设置
            page.goto('https://www.iwencai.com/screener', wait_until='load', timeout=30000)
            time.sleep(2)  # 等待 JS 设置 cookie
            
            # 获取所有 cookies
            cookies = context.cookies()
            cookie_str = '; '.join(
                f'{c["name"]}={c["value"]}'
                for c in cookies
            )
            
            context.close()
            
            if cookie_str:
                _cookie_cache = cookie_str
                _cookie_time = time.time()
                try:
                    COOKIE_FILE.write_text(cookie_str, encoding="utf-8")
                except Exception:
                    pass
                print(f"[iwencai] ✅ 成功获取浏览器会话")
                return cookie_str
            else:
                print(f"[iwencai] ⚠️ 浏览器未返回任何 cookies")
                return ""
            
    except Exception as e:
        print(f"[iwencai] ❌ 获取浏览器会话失败: {e}")
        return ""
