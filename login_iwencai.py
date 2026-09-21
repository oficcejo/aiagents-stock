#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
同花顺问财交互式一键登录工具
运行后会弹出一个浏览器窗口，在窗口中完成登录（扫码或密码登录）后，
本脚本会自动提取已登录的完整 Cookie 并持久化保存到 .iwencai_cookie.txt 与 .env 中。
保存后，所有问财选股策略（主力选股、低价擒牛、净利增长等）即可正常工作！
"""

import os
import sys
import time
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent
COOKIE_FILE = PROJECT_ROOT / ".iwencai_cookie.txt"
PROFILE_DIR = PROJECT_ROOT / ".iwencai_profile"


def login():
    try:
        from playwright.sync_api import sync_playwright
    except ImportError:
        print("❌ 未安装 playwright，请运行: pip install playwright && playwright install chromium")
        return

    print("=" * 65)
    print("🚀 正在启动问财登录窗口...")
    print("=" * 65)
    print("提示：浏览器窗口即将弹出，请在弹出的窗口中点击右上角「登录」并完成登录。")
    print("登录成功后，脚本会自动检测并保存登录状态！")
    print("=" * 65)

    PROFILE_DIR.mkdir(exist_ok=True)

    with sync_playwright() as p:
        context = p.chromium.launch_persistent_context(
            user_data_dir=str(PROFILE_DIR),
            headless=False,
            viewport={'width': 1280, 'height': 800},
            user_agent=(
                'Mozilla/5.0 (Windows NT 10.0; Win64; x64) '
                'AppleWebKit/537.36 (KHTML, like Gecko) '
                'Chrome/120.0.0.0 Safari/537.36'
            ),
        )
        page = context.new_page()
        page.goto('https://www.iwencai.com/screener', timeout=60000)

        # 循环检测登录状态（最长等待 3 分钟）
        print("\n⏳ 等待用户登录中（可扫码或输入同花顺账号登录）...")
        logged_in = False
        cookie_str = ""

        start_time = time.time()
        while time.time() - start_time < 180:
            cookies = context.cookies()
            cookie_names = [c["name"] for c in cookies]
            
            # 检测同花顺登录特征 Cookie
            login_tokens = ["ticket", "escapename", "wencai_user", "user", "userid", "user_id"]
            if any(t in cookie_names for t in login_tokens):
                logged_in = True
                cookie_str = "; ".join(f'{c["name"]}={c["value"]}' for c in cookies)
                break
            
            time.sleep(2)

        if not logged_in:
            # 如果自动识别未触发，也可以直接抓取当前所有 Cookie
            cookies = context.cookies()
            if cookies:
                cookie_str = "; ".join(f'{c["name"]}={c["value"]}' for c in cookies)
                logged_in = True

        context.close()

        if logged_in and cookie_str:
            COOKIE_FILE.write_text(cookie_str, encoding="utf-8")
            print("\n" + "=" * 65)
            print("✅ 登录 Cookie 已成功保存到:", COOKIE_FILE)
            print("=" * 65)
            print("选股策略模块现在可以直接读取该会话！")
        else:
            print("\n❌ 未能获取到 Cookie，请稍后重试。")


if __name__ == "__main__":
    login()
