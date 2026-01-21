# -*- coding: utf-8 -*-
"""
申请开通QMT请添加微信咨询gjquant，获取更多资料访问https://miniqmt.com/
此代码脚本仅用于软件测试，不能用于实盘交易，以此代码进行交易本人不承担任何损失
"""
import os
import time
import pandas as pd
from xtquant.xttrader import XtQuantTrader
from xtquant.xttype import StockAccount
from datetime import datetime

# 配置文件路径
CONFIG_FILE = "path.txt"

def load_config():
    """加载配置文件"""
    if os.path.exists(CONFIG_FILE):
        with open(CONFIG_FILE, 'r') as f:
            lines = f.readlines()
            if len(lines) >= 2:
                return lines[0].strip(), lines[1].strip()
    return None, None

def save_config(path, acc):
    """保存配置文件"""
    with open(CONFIG_FILE, 'w') as f:
        f.write(f"{path}\n{acc}")

def get_user_input(path=None):
    """获取用户输入"""
    print("请输入QMT配置信息(例如: D:\\QMT\\userdata_mini)")
    if path is None:
        path = input("QMT安装路径 ：").strip()
    acc = input("交易账号: ").strip()
    return path, acc

def initialize_trader(path, acc):
    """初始化交易连接"""
    # 创建交易对象
    session_id = int(time.time())
    xt_trader = XtQuantTrader(path, session_id)

    # 连接miniQMT终端
    xt_trader.start()
    connect_result = xt_trader.connect()
    
    if connect_result == 0:
        print('【软件终端连接成功！】')
    else:
        print('【软件终端连接失败！】', '\n请运行并登录miniQMT.EXE终端。', '\n检查路径是否正确。')
        return None, connect_result, None

    # 订阅账户信息
    account = StockAccount(acc, 'STOCK')
    subscribe_result = xt_trader.subscribe(account)
    if subscribe_result == 0:
        print('【账户信息订阅成功！】')
        return xt_trader, subscribe_result, account
    else:
        print('【账户信息订阅失败！】', '\n账户配置错误，检查账号是否正确。')
        return xt_trader, subscribe_result, account

def print_account_info(xt_trader, account):
    """打印账户信息"""
    asset = xt_trader.query_stock_asset(account)
    print('-'*18, f'【{asset.account_id}】', '-'*18) 
    if asset:
        print(f"资产总额: {asset.total_asset}\n"  
              f"持仓市值：{asset.market_value}\n"
              f"可用资金：{asset.cash}\n"
              f"在途资金：{asset.frozen_cash}")

def get_orders_df(xt_trader, account):
    """获取委托信息"""
    orders = xt_trader.query_stock_orders(account)
    if not orders:
        return pd.DataFrame()
    
    orders_data = [(order.stock_code, order.order_volume, order.price, 
                    order.order_id, order.status_msg,
                    datetime.fromtimestamp(order.order_time).strftime('%H:%M:%S'))
                   for order in orders]
    return pd.DataFrame(orders_data, 
                       columns=['证券代码', '委托数量', '委托价格', '订单编号', '委托状态', '报单时间'])

def get_trades_df(xt_trader, account):
    """获取成交信息"""
    trades = xt_trader.query_stock_trades(account)
    if not trades:
        return pd.DataFrame()
    
    trades_data = [(trade.stock_code, trade.traded_volume, trade.traded_price,
                    trade.traded_amount, trade.order_id, trade.traded_id,
                    datetime.fromtimestamp(trade.traded_time).strftime('%H:%M:%S'))
                   for trade in trades]
    return pd.DataFrame(trades_data,
                       columns=['证券代码', '成交数量', '成交均价', '成交金额', '订单编号', '成交编号', '成交时间'])

def get_positions_df(xt_trader, account):
    """获取持仓信息"""
    positions = xt_trader.query_stock_positions(account)
    if not positions:
        return pd.DataFrame()
    
    positions_data = [(position.stock_code, position.volume, position.can_use_volume,
                       position.frozen_volume, position.open_price, position.market_value,
                       position.on_road_volume, position.yesterday_volume)
                      for position in positions]
    return pd.DataFrame(positions_data,
                        columns=['证券代码', '持仓数量', '可用数量', '冻结数量', '开仓价格', 
                                '持仓市值', '在途股份', '昨夜持股'])

def print_summary_info(orders_df, trades_df, positions_df):
    """打印汇总信息"""
    print('-'*18, '【当日汇总】', '-'*18)
    print(f"委托个数：{len(orders_df)}    成交个数：{len(trades_df)}    持仓数量：{len(positions_df)}")
    
    print('-'*18, "【订单信息】", '-'*18)
    print(orders_df if not orders_df.empty else "无委托信息")

    print('-'*18, "【成交信息】", '-'*18)
    print(trades_df if not trades_df.empty else "无成交信息")

    print('-'*18, "【持仓信息】", '-'*18)
    print(positions_df if not positions_df.empty else "无持仓信息")

def main():
    # 尝试加载已有配置
    saved_path, saved_acc = load_config()
    path, acc = saved_path, saved_acc
    
    # 初始化变量
    xt_trader = None
    account = None
    
    # 如果配置不存在或连接失败，要求用户重新输入
    while True:
        if path and acc:
            print(f"使用已保存配置：\n路径: {path}\n账号: {acc}")
            confirm = input("请选择是否使用此配置？(Y/n): ").strip().lower()
            if confirm == 'y' or confirm == '':
                xt_trader, result, account = initialize_trader(path, acc)
                if result == 0:  # 订阅成功
                    break
                elif result is None:  # 连接失败
                    path, acc = None, None  # 需要重新输入全部信息
                else:  # 仅订阅失败
                    path = path  # 保留路径
                    acc = None   # 仅需要重新输入账号
        
        # 获取新配置
        path, acc = get_user_input(path)  # 如果path不为None，则只输入账号
        save_config(path, acc)
        xt_trader, result, account = initialize_trader(path, acc)
        if result == 0:  # 订阅成功
            break
        
        print("配置失败，请重新输入...\n")

    # 打印账户信息
    print_account_info(xt_trader, account)

    # 获取并打印交易信息
    orders_df = get_orders_df(xt_trader, account)
    trades_df = get_trades_df(xt_trader, account)
    positions_df = get_positions_df(xt_trader, account)
    
    # 打印汇总信息
    print_summary_info(orders_df, trades_df, positions_df)

if __name__ == "__main__":
    main()