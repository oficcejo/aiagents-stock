#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
QMT连接状态检查工具
用于检查本地QMT客户端是否运行以及API服务地址
"""

import os
import sys
import socket
import subprocess
from datetime import datetime

def check_port(host, port):
    """检查端口是否开放"""
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(2)
        result = sock.connect_ex((host, port))
        sock.close()
        return result == 0
    except Exception as e:
        return False, str(e)

def check_process_by_name(process_names):
    """检查进程是否运行"""
    running_processes = []
    
    try:
        if sys.platform == 'darwin':  # macOS
            ps_command = ['ps', 'aux']
        elif sys.platform == 'win32':  # Windows
            ps_command = ['tasklist']
        else:  # Linux
            ps_command = ['ps', 'aux']
        
        result = subprocess.run(ps_command, capture_output=True, text=True)
        
        for name in process_names:
            if name.lower() in result.stdout.lower():
                running_processes.append(name)
        
        return running_processes
    except Exception as e:
        print(f"检查进程时出错: {e}")
        return []

def check_common_qmt_ports():
    """检查常见的QMT端口"""
    common_ports = [58610, 58611, 58612, 58613, 58614, 58615, 5000, 8080]
    open_ports = []
    
    print("\n🔍 检查常见QMT端口...")
    for port in common_ports:
        if check_port('127.0.0.1', port):
            open_ports.append(port)
            print(f"  ✅ 端口 {port} 已开放")
        else:
            print(f"  ❌ 端口 {port} 未开放")
    
    return open_ports

def check_xtquant_import():
    """检查xtquant库是否可用"""
    try:
        from xtquant import xttrader, xtdata
        print("  ✅ xtquant库已安装")
        return True, xttrader, xtdata
    except ImportError as e:
        print(f"  ❌ xtquant库未安装: {e}")
        return False, None, None

def test_xtquant_connection():
    """测试xtquant连接"""
    try:
        from xtquant import xttrader
        
        print("\n🔗 尝试连接xtquant...")
        trader = xttrader.XtQuantTrader()
        trader.start()
        
        # 尝试获取账户列表
        try:
            accounts = trader.query_accounts()
            if accounts:
                print(f"  ✅ 连接成功！找到 {len(accounts)} 个账户")
                for acc in accounts:
                    print(f"     - 账户ID: {acc}")
                trader.stop()
                return True, accounts
            else:
                print("  ⚠️  连接成功，但未找到账户")
                trader.stop()
                return True, []
        except Exception as e:
            print(f"  ⚠️  连接成功，但查询账户失败: {e}")
            trader.stop()
            return True, []
            
    except Exception as e:
        print(f"  ❌ 连接失败: {e}")
        return False, None

def check_env_config():
    """检查环境变量配置"""
    print("\n📋 检查环境变量配置...")
    
    from dotenv import load_dotenv
    load_dotenv()
    
    config = {
        'MINIQMT_ENABLED': os.getenv('MINIQMT_ENABLED', '未设置'),
        'MINIQMT_ACCOUNT_ID': os.getenv('MINIQMT_ACCOUNT_ID', '未设置'),
        'MINIQMT_HOST': os.getenv('MINIQMT_HOST', '未设置'),
        'MINIQMT_PORT': os.getenv('MINIQMT_PORT', '未设置'),
    }
    
    for key, value in config.items():
        if value == '未设置':
            print(f"  ⚠️  {key}: {value}")
        else:
            print(f"  ✅ {key}: {value}")
    
    return config

def main():
    print("=" * 60)
    print("QMT连接状态检查工具")
    print("=" * 60)
    print(f"检查时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    # 1. 检查QMT进程
    print("\n1️⃣ 检查QMT进程是否运行...")
    qmt_processes = [
        'XtMiniQmt', 'XtMiniQmt.exe', 'QMT', 'QMT.exe',
        'xtquant', 'xttrader', '国金证券', 'gjzq'
    ]
    running = check_process_by_name(qmt_processes)
    if running:
        print(f"  ✅ 发现运行中的QMT相关进程: {', '.join(running)}")
    else:
        print("  ⚠️  未发现运行中的QMT进程")
        print("     提示: 请确保QMT客户端已启动并登录")
    
    # 2. 检查环境配置
    env_config = check_env_config()
    
    # 3. 检查常见端口
    open_ports = check_common_qmt_ports()
    
    # 4. 检查xtquant库
    print("\n2️⃣ 检查xtquant库...")
    has_xtquant, xttrader, xtdata = check_xtquant_import()
    
    # 5. 测试连接
    if has_xtquant:
        success, accounts = test_xtquant_connection()
        
        if success and accounts:
            print("\n✅ QMT连接状态: 正常")
            print(f"   可用账户数: {len(accounts)}")
            if env_config['MINIQMT_ACCOUNT_ID'] != '未设置':
                account_id = env_config['MINIQMT_ACCOUNT_ID']
                if account_id in accounts:
                    print(f"   ✅ 配置的账户ID '{account_id}' 在可用账户列表中")
                else:
                    print(f"   ⚠️  配置的账户ID '{account_id}' 不在可用账户列表中")
                    print(f"   可用账户: {', '.join(accounts)}")
        elif success:
            print("\n⚠️  QMT连接状态: 已连接但无账户")
        else:
            print("\n❌ QMT连接状态: 连接失败")
    else:
        print("\n⚠️  无法测试连接（xtquant库未安装）")
    
    # 6. 端口总结
    if open_ports:
        print(f"\n📊 开放的端口: {', '.join(map(str, open_ports))}")
        if env_config['MINIQMT_PORT'] != '未设置':
            config_port = int(env_config['MINIQMT_PORT'])
            if config_port in open_ports:
                print(f"   ✅ 配置的端口 {config_port} 已开放")
            else:
                print(f"   ⚠️  配置的端口 {config_port} 未开放")
                print(f"   建议使用已开放的端口: {open_ports[0]}")
    
    # 7. 建议
    print("\n" + "=" * 60)
    print("💡 建议:")
    print("=" * 60)
    
    if not running:
        print("1. 请启动QMT客户端并登录")
    
    if not has_xtquant:
        print("2. 请安装xtquant库:")
        print("   - 从QMT安装目录复制 xtquant 到 Python site-packages")
        print("   - 或使用 pip install xtquant（如果可用）")
    
    if open_ports and env_config['MINIQMT_PORT'] != '未设置':
        config_port = int(env_config['MINIQMT_PORT'])
        if config_port not in open_ports:
            print(f"3. 建议修改 MINIQMT_PORT 为 {open_ports[0]}")
    
    if env_config['MINIQMT_ACCOUNT_ID'] == '未设置':
        print("4. 请在 .env 文件中配置 MINIQMT_ACCOUNT_ID")
    
    print("\n" + "=" * 60)

if __name__ == "__main__":
    main()
