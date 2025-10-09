#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
通知系统诊断工具
用于排查邮件通知问题
"""

import sqlite3
from notification_service import notification_service
from monitor_db import monitor_db
from datetime import datetime

def check_database():
    """检查数据库中的通知"""
    print("\n" + "="*60)
    print("1. 检查数据库中的通知记录")
    print("="*60)
    
    conn = sqlite3.connect('stock_monitor.db')
    cursor = conn.cursor()
    
    # 检查所有通知
    cursor.execute('''
        SELECT n.id, s.symbol, s.name, n.type, n.message, n.triggered_at, n.sent
        FROM notifications n
        JOIN monitored_stocks s ON n.stock_id = s.id
        ORDER BY n.triggered_at DESC
        LIMIT 20
    ''')
    
    notifications = cursor.fetchall()
    if notifications:
        print(f"\n最近20条通知记录:")
        for row in notifications:
            sent_status = "✅已发送" if row[6] else "⏳待发送"
            print(f"  [{sent_status}] {row[1]} - {row[3]} - {row[4]}")
            print(f"        时间: {row[5]}")
    else:
        print("  ❌ 数据库中没有任何通知记录")
    
    # 检查待发送通知
    cursor.execute('''
        SELECT COUNT(*) FROM notifications WHERE sent = FALSE
    ''')
    pending_count = cursor.fetchone()[0]
    print(f"\n待发送通知数量: {pending_count}")
    
    conn.close()

def check_email_config():
    """检查邮件配置"""
    print("\n" + "="*60)
    print("2. 检查邮件配置")
    print("="*60)
    
    config = notification_service.get_email_config_status()
    
    print(f"\n邮件启用: {'✅ 是' if config['enabled'] else '❌ 否'}")
    print(f"SMTP服务器: {config['smtp_server']}")
    print(f"SMTP端口: {config['smtp_port']}")
    print(f"发件人: {config['email_from']}")
    print(f"收件人: {config['email_to']}")
    print(f"配置完整: {'✅ 是' if config['configured'] else '❌ 否'}")
    
    return config['configured']

def test_email_connection():
    """测试邮件连接"""
    print("\n" + "="*60)
    print("3. 测试邮件连接")
    print("="*60)
    
    print("\n正在发送测试邮件...")
    success, message = notification_service.send_test_email()
    
    if success:
        print(f"✅ {message}")
        return True
    else:
        print(f"❌ {message}")
        return False

def send_pending_notifications():
    """尝试发送待发送的通知"""
    print("\n" + "="*60)
    print("4. 尝试发送待发送的通知")
    print("="*60)
    
    pending = monitor_db.get_pending_notifications()
    
    if not pending:
        print("\n没有待发送的通知")
        return
    
    print(f"\n找到 {len(pending)} 条待发送通知:")
    for notif in pending:
        print(f"  - {notif['symbol']}: {notif['message']}")
    
    print("\n开始发送...")
    notification_service.send_notifications()
    
    # 再次检查
    pending_after = monitor_db.get_pending_notifications()
    print(f"\n发送后剩余待发送通知: {len(pending_after)}")

def check_stock_prices():
    """检查监测股票的当前价格和触发条件"""
    print("\n" + "="*60)
    print("5. 检查监测股票状态")
    print("="*60)
    
    stocks = monitor_db.get_monitored_stocks()
    
    if not stocks:
        print("\n没有监测股票")
        return
    
    print(f"\n共有 {len(stocks)} 只股票在监测:")
    
    for stock in stocks:
        print(f"\n📊 {stock['symbol']} - {stock['name']}")
        print(f"  当前价格: {stock['current_price']}")
        
        entry_range = stock['entry_range']
        print(f"  进场区间: {entry_range['min']} - {entry_range['max']}")
        
        if stock['take_profit']:
            print(f"  止盈位: {stock['take_profit']}")
        if stock['stop_loss']:
            print(f"  止损位: {stock['stop_loss']}")
        
        print(f"  通知启用: {'✅' if stock['notification_enabled'] else '❌'}")
        print(f"  最后检查: {stock['last_checked'] or '从未'}")
        
        # 检查是否满足触发条件
        if stock['current_price']:
            price = float(stock['current_price'])
            
            # 检查进场区间
            if price >= entry_range['min'] and price <= entry_range['max']:
                print(f"  🟢 当前价格在进场区间内")
                
                # 检查最近是否有通知
                if monitor_db.has_recent_notification(stock['id'], 'entry', minutes=60):
                    print(f"     ⚠️ 但最近60分钟内已发送过进场通知（防重复机制）")
                else:
                    print(f"     ❗ 应该触发通知但没有！")
            else:
                if price < entry_range['min']:
                    print(f"  ⬇️ 当前价格低于进场区间 (差 {entry_range['min'] - price:.2f})")
                else:
                    print(f"  ⬆️ 当前价格高于进场区间 (高出 {price - entry_range['max']:.2f})")
            
            # 检查止盈
            if stock['take_profit'] and price >= stock['take_profit']:
                print(f"  🟡 已达到止盈位")
                if monitor_db.has_recent_notification(stock['id'], 'take_profit', minutes=60):
                    print(f"     ⚠️ 最近60分钟内已发送过止盈通知")
            
            # 检查止损
            if stock['stop_loss'] and price <= stock['stop_loss']:
                print(f"  🔴 已达到止损位")
                if monitor_db.has_recent_notification(stock['id'], 'stop_loss', minutes=60):
                    print(f"     ⚠️ 最近60分钟内已发送过止损通知")

def main():
    """主函数"""
    print("\n" + "="*60)
    print("股票监测通知系统诊断工具")
    print("="*60)
    print(f"诊断时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    # 1. 检查数据库
    check_database()
    
    # 2. 检查邮件配置
    email_configured = check_email_config()
    
    # 3. 测试邮件连接
    if email_configured:
        email_ok = test_email_connection()
    else:
        print("\n⚠️ 邮件未配置，跳过邮件测试")
        email_ok = False
    
    # 4. 检查股票价格和触发条件
    check_stock_prices()
    
    # 5. 尝试发送待发送通知
    send_pending_notifications()
    
    # 总结
    print("\n" + "="*60)
    print("诊断总结")
    print("="*60)
    
    if email_configured and email_ok:
        print("✅ 邮件系统正常")
    elif email_configured:
        print("⚠️ 邮件已配置但发送失败，请检查配置参数")
    else:
        print("❌ 邮件未配置")
    
    print("\n建议:")
    print("1. 确保监测服务正在运行")
    print("2. 检查股票价格是否在触发区间内")
    print("3. 注意60分钟防重复机制")
    print("4. 查看终端日志中的详细错误信息")
    print("5. 如果邮件测试成功但监测通知收不到，检查.env配置")
    
    print("\n" + "="*60)

if __name__ == "__main__":
    main()

