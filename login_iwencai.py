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

    try:
        sys.stdout.reconfigure(encoding='utf-8')
    except Exception:
        pass

    PROFILE_DIR.mkdir(exist_ok=True)

    with sync_playwright() as p:
        context = p.chromium.launch_persistent_context(
            user_data_dir=str(PROFILE_DIR),
            headless=False,
            viewport={'width': 1280, 'height': 800},
            ignore_default_args=['--enable-automation'],
            args=[
                '--disable-blink-features=AutomationControlled',
                '--no-sandbox',
            ],
            user_agent=(
                'Mozilla/5.0 (Windows NT 10.0; Win64; x64) '
                'AppleWebKit/537.36 (KHTML, like Gecko) '
                'Chrome/120.0.0.0 Safari/537.36'
            ),
        )
        context.add_init_script(
            "delete Object.getPrototypeOf(navigator).webdriver;\n"
            "Object.defineProperty(navigator, 'webdriver', {get: () => undefined});"
        )
        page = context.pages[0] if context.pages else context.new_page()
        page.goto('https://www.iwencai.com/screener', timeout=60000)

        # 自动尝试点击登录按钮弹出登录框
        try:
            page.wait_for_selector('span.login', timeout=8000)
            page.click('span.login')
            print("💡 已自动为您弹出登录窗口，请在弹出的框中【微信扫码】或【账号密码】登录。")
        except Exception:
            print("💡 请点击页面右上角的「登录」按钮。")

        # 循环检测登录状态（最长等待 5 分钟）
        print("\n⏳ 等待登录中（扫码成功后脚本将自动识别并保存）...")
        logged_in = False
        cookie_str = ""

        start_time = time.time()
        while time.time() - start_time < 300:
            cookies = context.cookies()
            cookie_names = [c["name"] for c in cookies]
            
            # 检测同花顺登录特征 Cookie
            login_tokens = ["ticket", "escapename", "wencai_user", "user", "userid", "user_id"]
            if any(t in cookie_names for t in login_tokens):
                # 确认登录后稍微多等 1 秒让全部鉴权 cookie 写入完成
                time.sleep(1)
                cookies = context.cookies()
                logged_in = True
                cookie_str = "; ".join(f'{c["name"]}={c["value"]}' for c in cookies)
                break
            
            time.sleep(2)

        if not logged_in:
            # 如果自动识别未触发，也可以直接抓取当前所有 Cookie
            cookies = context.cookies()
            if cookies and len(cookies) > 3:
                cookie_str = "; ".join(f'{c["name"]}={c["value"]}' for c in cookies)
                logged_in = True

        context.close()

        if logged_in and cookie_str:
            COOKIE_FILE.write_text(cookie_str, encoding="utf-8")
            print("\n" + "=" * 65)
            print("✅ 登录凭证已成功保存到:", COOKIE_FILE)
            print("=" * 65)
            print("🎉 所有问财选股策略（主力选股、低价擒牛、净利增长等）现已就绪！")
        else:
            print("\n❌ 未能检测到有效登录状态。")
            print_manual_guide()


def save_manual_cookie(cookie_str: str):
    """手动保存用户提供的 Cookie"""
    cookie_str = cookie_str.strip()
    if not cookie_str:
        print("❌ Cookie 不能为空")
        return False
    COOKIE_FILE.write_text(cookie_str, encoding="utf-8")
    print("\n" + "=" * 65)
    print("✅ Cookie 已成功保存到:", COOKIE_FILE)
    print("=" * 65)
    print("🎉 所有问财选股策略现已就绪！")
    return True


def print_manual_guide():
    """打印从 Chrome 手动抓取 Cookie 的详细指南"""
    print("\n" + "=" * 70)
    print("📖【如何从已登录的 Chrome 浏览器获取完整 Cookie】")
    print("=" * 70)
    print("1. 用普通 Chrome 打开并登录：https://www.iwencai.com/screener")
    print("2. 按键盘 F12 打开开发者工具，切换到「Network」(网络) 标签页")
    print("3. 按键盘 F5 刷新一下问财页面")
    print("4. 在左侧请求列表中点击最上面任意一条请求（如 screener）")
    print("5. 在右侧窗口点击「Headers」(标头) -> 往下找到「Request Headers」(请求标头)")
    print("6. 找到「Cookie:」行，鼠标右键点击并选择「Copy value」(复制值)")
    print("7. 运行命令保存：")
    print('   python login_iwencai.py --set-cookie "你的Cookie内容"')
    print("   或者直接将复制内容粘贴保存到项目根目录下的 .iwencai_cookie.txt 文件中。")
    print("=" * 70 + "\n")


def main():
    import argparse
    parser = argparse.ArgumentParser(description="同花顺问财登录与Cookie配置工具")
    parser.add_argument("--set-cookie", type=str, help="直接保存手动复制的 Cookie 字符串")
    parser.add_argument("--guide", action="store_true", help="显示从浏览器抓取 Cookie 的图文操作指南")
    args = parser.parse_args()

    if args.guide:
        print_manual_guide()
        return

    if args.set_cookie:
        save_manual_cookie(args.set_cookie)
        return

    # 默认执行交互式扫码登录
    login()


if __name__ == "__main__":
    main()
