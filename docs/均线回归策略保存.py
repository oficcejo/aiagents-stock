'''
均线回归策略 V3.0 进攻版
优化重点：提高Beta，增强进攻性，减少过度保守

核心改进：
1. 放宽市场择时，只在极端熊市降仓
2. 增加持仓数量，提高资金利用率
3. 放宽买入条件，增加交易机会
4. 优化止盈，让利润奔跑
5. 增加突破买入模式
'''

import jqdata
import numpy as np

## 初始化函数
def initialize(context):
    # 设定沪深300作为基准
    set_benchmark('000300.XSHG')
    # 开启动态复权模式
    set_option('use_real_price', True)
    # 设定成交量比例
    set_option('order_volume_ratio', 1)
    # 设置交易手续费
    set_order_cost(OrderCost(open_tax=0, close_tax=0.001,
                             open_commission=0.0003, close_commission=0.0003,
                             close_today_commission=0, min_commission=5), type='stock')

    # ========== 策略参数（进攻版）==========
    g.stocknum = 8              # 持仓数量增加到8只
    g.max_position_ratio = 0.98 # 最大仓位98%

    # 均线参数
    g.ma_short = 20             # 短期均线
    g.ma_mid = 60               # 中期均线
    g.ma_long = 120             # 长期均线

    # 回调买入参数（放宽条件）
    g.pullback_ratio = 0.035    # 放宽到3.5%
    g.break_tolerance = 0.015   # 允许跌破1.5%

    # 止盈止损参数（让利润奔跑）
    g.base_take_profit = 0.20   # 止盈提高到20%
    g.base_stop_loss = 0.06     # 止损放宽到6%
    g.trailing_stop = 0.08      # 回撤容忍8%

    # 市值筛选（亿）- 扩大范围
    g.min_market_cap = 20
    g.max_market_cap = 1000

    # 行业分散参数
    g.max_industry_stocks = 3   # 同行业最多3只

    # 市场状态
    g.market_state = 'NORMAL'
    g.position_ratio = 1.0

    # 记录
    g.highest_profit = {}
    g.stock_volatility = {}
    g.hold_days = {}            # 持仓天数

    # 定时任务
    run_daily(market_analysis, '09:31')
    run_daily(morning_check, '09:35')
    run_daily(check_positions, '14:00')     # 只检查一次
    run_daily(afternoon_trade, '14:50')

## 市场环境分析（放宽版）
def market_analysis(context):
    """
    只在极端情况下降低仓位，大部分时间保持高仓位
    """
    index_code = '000300.XSHG'

    try:
        df = attribute_history(index_code, 130, '1d', ['close'], skip_paused=True)
        if len(df) < 120:
            g.market_state = 'NORMAL'
            g.position_ratio = 1.0
            return

        close = df['close'].values
        current = close[-1]

        ma20 = np.mean(close[-20:])
        ma60 = np.mean(close[-60:])
        ma120 = np.mean(close[-120:])

        change_5d = (close[-1] - close[-6]) / close[-6]
        change_10d = (close[-1] - close[-11]) / close[-11]

        # 只在极端熊市才降仓（条件更严格）
        if current < ma120 and ma20 < ma60 < ma120 and change_10d < -0.08:
            # 极端熊市：指数跌破120日均线，均线空头，10日跌幅超8%
            g.market_state = 'BEAR'
            g.position_ratio = 0.5
            log.info("【市场】极端熊市，仓位50%%")
        elif change_5d < -0.08:
            # 短期暴跌超8%：暂时减仓
            g.market_state = 'BEAR'
            g.position_ratio = 0.6
            log.info("【市场】短期暴跌，仓位60%%")
        elif current > ma20 and ma20 > ma60:
            # 趋势向上：满仓
            g.market_state = 'BULL'
            g.position_ratio = 1.0
            log.info("【市场】趋势向上，满仓")
        else:
            # 默认高仓位运行
            g.market_state = 'NORMAL'
            g.position_ratio = 0.9
            log.info("【市场】正常状态，仓位90%%")

    except Exception as e:
        g.market_state = 'NORMAL'
        g.position_ratio = 0.9

## 早盘检查
def morning_check(context):
    g.buy_list = check_stocks(context)
    log.info("【选股】%d 只，市场: %s，仓位: %.0f%%" %
             (len(g.buy_list), g.market_state, g.position_ratio * 100))

## 检查持仓 - 优化版（让利润奔跑）
def check_positions(context):
    if len(context.portfolio.positions) == 0:
        return

    for stock in list(context.portfolio.positions.keys()):
        position = context.portfolio.positions[stock]
        if position.closeable_amount <= 0:
            continue

        cost = position.avg_cost
        current_price = position.price
        if cost <= 0:
            continue

        profit_ratio = (current_price - cost) / cost

        # 更新持仓天数
        g.hold_days[stock] = g.hold_days.get(stock, 0) + 1

        # 更新最高盈利
        if stock not in g.highest_profit:
            g.highest_profit[stock] = profit_ratio
        else:
            g.highest_profit[stock] = max(g.highest_profit[stock], profit_ratio)

        highest = g.highest_profit[stock]
        hold_days = g.hold_days.get(stock, 0)

        # 动态止损（根据波动率和持仓时间）
        volatility = g.stock_volatility.get(stock, 0.025)
        # 持仓时间越长，止损越宽松
        time_factor = min(1 + hold_days * 0.01, 1.5)
        dynamic_stop_loss = min(g.base_stop_loss * time_factor, 0.12)

        # === 止损逻辑 ===
        if profit_ratio < -dynamic_stop_loss:
            log.info("【止损】%s 亏损 %.2f%%" % (stock, profit_ratio * 100))
            order_target(stock, 0)
            clean_stock_data(stock)
            continue

        # === 均线破位（只在亏损时卖）===
        if profit_ratio < 0 and check_sell_signal(stock):
            log.info("【均线破位】%s 破位且亏损，卖出" % stock)
            order_target(stock, 0)
            clean_stock_data(stock)
            continue

        # === 移动止盈（让利润奔跑）===
        if highest >= g.base_take_profit:
            drawdown = highest - profit_ratio
            # 盈利越多，允许回撤越大（最多允许回撤15%）
            allowed_drawdown = min(g.trailing_stop + highest * 0.4, 0.18)
            if drawdown >= allowed_drawdown:
                log.info("【移动止盈】%s 最高 %.2f%%，回撤 %.2f%%" %
                        (stock, highest * 100, drawdown * 100))
                order_target(stock, 0)
                clean_stock_data(stock)
                continue

        # === 分批止盈（保守止盈，只卖小部分）===
        if profit_ratio >= g.base_take_profit * 2:
            # 盈利超40%，卖出30%锁定利润
            sell_amount = int(position.closeable_amount * 0.3 / 100) * 100
            if sell_amount >= 100:
                log.info("【大幅止盈】%s 盈利 %.2f%%，卖出30%%" % (stock, profit_ratio * 100))
                order(stock, -sell_amount)

## 清理股票数据
def clean_stock_data(stock):
    for d in [g.highest_profit, g.stock_volatility, g.hold_days]:
        if stock in d:
            del d[stock]

## 尾盘交易
def afternoon_trade(context):
    buy_stocks(context)

## 买入函数（积极版）
def buy_stocks(context):
    if not hasattr(g, 'buy_list') or not g.buy_list:
        return

    position_count = len(context.portfolio.positions)
    adjusted_stocknum = int(g.stocknum * g.position_ratio)
    if adjusted_stocknum <= 0 or position_count >= adjusted_stocknum:
        return

    # 计算资金分配
    available_cash = context.portfolio.available_cash * g.max_position_ratio
    buy_count = min(adjusted_stocknum - position_count, len(g.buy_list))
    if buy_count <= 0 or available_cash < 10000:
        return

    cash_per_stock = available_cash / buy_count
    held_industries = get_held_industries(context)

    bought = 0
    for stock in g.buy_list:
        if bought >= buy_count:
            break
        if stock in context.portfolio.positions:
            continue

        # 行业分散
        stock_industry = get_stock_industry(stock)
        if stock_industry and held_industries.get(stock_industry, 0) >= g.max_industry_stocks:
            continue

        # 简化买入条件检查
        if check_buy_signal(stock):
            order_value(stock, cash_per_stock)
            log.info("【买入】%s" % stock)
            g.highest_profit[stock] = 0
            g.stock_volatility[stock] = 0.025
            g.hold_days[stock] = 0
            if stock_industry:
                held_industries[stock_industry] = held_industries.get(stock_industry, 0) + 1
            bought += 1

## 获取已持仓的行业分布
def get_held_industries(context):
    industries = {}
    for stock in context.portfolio.positions.keys():
        ind = get_stock_industry(stock)
        if ind:
            industries[ind] = industries.get(ind, 0) + 1
    return industries

## 获取股票所属行业
def get_stock_industry(stock):
    try:
        ind_dict = get_industry(stock)
        if ind_dict and stock in ind_dict:
            # 获取申万一级行业
            for ind_code, ind_info in ind_dict[stock].items():
                if ind_code.startswith('sw_l1'):
                    return ind_info.get('industry_name', None)
        return None
    except:
        return None

## 选股函数（进攻版）
def check_stocks(context):
    # 第一步：基础筛选（放宽条件）
    q = query(
            valuation.code,
            valuation.market_cap
        ).filter(
            valuation.market_cap.between(g.min_market_cap, g.max_market_cap)
        ).order_by(
            valuation.market_cap.asc()
        ).limit(500)  # 扩大候选池

    df = get_fundamentals(q)
    if df.empty:
        return []

    stock_list = list(df['code'])
    stock_list = filter_basic(stock_list)

    # 均线信号筛选
    candidates = []
    for stock in stock_list[:200]:  # 检查前200只
        if check_buy_signal(stock):
            score = calculate_trend_score(stock)
            candidates.append((stock, score))

    # 按评分排序
    candidates.sort(key=lambda x: x[1], reverse=True)
    buy_list = [c[0] for c in candidates[:g.stocknum * 3]]

    return buy_list

## 计算趋势强度评分
def calculate_trend_score(stock):
    """
    评分因素：
    1. 均线发散程度
    2. 价格距离MA20的位置
    3. 成交量配合
    """
    try:
        df = attribute_history(stock, 130, '1d', ['close', 'volume'], skip_paused=True)
        if len(df) < 120:
            return 0

        close = df['close'].values
        volume = df['volume'].values

        ma20 = np.mean(close[-20:])
        ma60 = np.mean(close[-60:])
        ma120 = np.mean(close[-120:])
        current = close[-1]

        score = 0

        # 均线发散程度（20分）
        spread = (ma20 - ma120) / ma120
        score += min(spread * 100, 20)

        # 价格位置（30分）- 越接近MA20越好
        distance = abs(current - ma20) / ma20
        score += max(0, 30 - distance * 500)

        # 成交量（20分）- 回调缩量为佳
        vol_ma5 = np.mean(volume[-5:])
        vol_ma20 = np.mean(volume[-20:])
        if vol_ma5 < vol_ma20 * 0.8:
            score += 20  # 缩量回调
        elif vol_ma5 < vol_ma20:
            score += 10

        # 趋势持续性（30分）
        ma20_slope = (ma20 - np.mean(close[-25:-5])) / np.mean(close[-25:-5])
        if ma20_slope > 0:
            score += min(ma20_slope * 300, 30)

        return score

    except:
        return 0

## 基础过滤
def filter_basic(stock_list):
    if not stock_list:
        return []

    current_data = get_current_data()
    filtered = []

    for stock in stock_list:
        # 过滤停牌
        if current_data[stock].paused:
            continue
        # 过滤ST
        if current_data[stock].is_st:
            continue
        if 'ST' in current_data[stock].name or '*' in current_data[stock].name:
            continue
        # 过滤科创板、北交所
        if stock.startswith('688') or stock.startswith('8') or stock.startswith('4'):
            continue
        # 过滤涨跌停
        if current_data[stock].last_price >= current_data[stock].high_limit:
            continue
        if current_data[stock].last_price <= current_data[stock].low_limit:
            continue

        filtered.append(stock)

    return filtered

## 检查买入信号（放宽版）
def check_buy_signal(stock):
    """
    放宽买入条件，增加交易机会
    """
    try:
        df = attribute_history(stock, g.ma_long + 10, '1d', ['close'], skip_paused=True)
        if len(df) < g.ma_long:
            return False

        close = df['close'].values
        current_price = close[-1]

        # 计算均线
        ma20 = np.mean(close[-g.ma_short:])
        ma60 = np.mean(close[-g.ma_mid:])
        ma120 = np.mean(close[-g.ma_long:])

        # 条件1：均线多头排列（核心条件）
        if not (ma20 > ma60 > ma120):
            return False

        # 条件2：MA20向上
        ma20_5d_ago = np.mean(close[-g.ma_short-5:-5])
        if ma20 <= ma20_5d_ago:
            return False

        # 条件3：价格在MA20附近（放宽范围）
        distance = (current_price - ma20) / ma20
        # 允许在MA20上方5%以内，或跌破2%以内
        if distance > 0.05 or distance < -0.02:
            return False

        # 条件4：价格不能离MA60太远
        if current_price > ma60 * 1.30:
            return False

        return True

    except:
        return False

## 检查卖出信号（均线破位）
def check_sell_signal(stock):
    """
    卖出条件：
    1. 价格跌破MA60
    2. MA20下穿MA60（死叉）
    3. 价格跌破MA20且持续3天
    """
    try:
        df = attribute_history(stock, g.ma_mid + 5, '1d', ['close'], skip_paused=True)
        if len(df) < g.ma_mid:
            return False

        close = df['close'].values
        current_price = close[-1]

        ma20 = np.mean(close[-g.ma_short:])
        ma60 = np.mean(close[-g.ma_mid:])

        # 价格跌破MA60超过2%
        if current_price < ma60 * 0.98:
            return True

        # MA20下穿MA60（死叉）
        ma20_yesterday = np.mean(close[-g.ma_short-1:-1])
        ma60_yesterday = np.mean(close[-g.ma_mid-1:-1])
        if ma20_yesterday > ma60_yesterday and ma20 < ma60:
            return True

        # 连续3天收盘在MA20下方
        ma20_3d = [np.mean(close[-g.ma_short-i:-i]) if i > 0 else ma20 for i in range(3)]
        below_ma20_count = sum(1 for i in range(3) if close[-1-i] < ma20_3d[i] * 0.99)
        if below_ma20_count >= 3:
            return True

        return False

    except:
        return False

