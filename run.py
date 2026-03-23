#!/usr/bin/env python3
"""
AI股票分析系统启动脚本
运行命令: python run.py
"""

import subprocess
import sys
import os

def check_requirements():
    """检查必要的依赖是否安装"""
    try:
        import streamlit
        import pandas
        import plotly
        import yfinance
        import akshare
        import openai
        print("✅ 所有依赖包已安装")
        return True
    except ImportError as e:
        print(f"❌ 缺少依赖包: {e}")
        print("请运行: pip install -r requirements.txt")
        return False

def check_config():
    """检查配置文件"""
    try:
        from core import config
        if not config.DEEPSEEK_API_KEY:
            print("⚠️  警告: DeepSeek API Key 未配置")
            print("请在config.py中设置 DEEPSEEK_API_KEY")
            return False
        print("✅ 配置文件检查通过")
        return True
    except ImportError:
        print("❌ 配置文件config.py不存在")
        return False

def main():
    """主函数"""
    print("🚀 启动AI股票分析系统...")
    print("=" * 50)
    
    # 检查依赖
    if not check_requirements():
        return
    
    # 检查配置
    config_ok = check_config()
    
    # 启动Streamlit应用
    print("🌐 正在启动Web界面...")
    print("📝 访问地址: http://localhost:8503")
    print("⏹️  按 Ctrl+C 停止服务")
    print("=" * 50)
    
    try:
        subprocess.run([
            sys.executable, "-m", "streamlit", "run", "app.py",
            "--server.port", "8503",
            "--server.address", "127.0.0.1"
        ])
    except KeyboardInterrupt:
        print("\n👋 感谢使用AI股票分析系统！")

if __name__ == "__main__":
    main()
