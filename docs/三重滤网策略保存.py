'''
三重滤网交易系统 V2.0
by Alexander Elder (优化版)

核心改进：
1. 第一重滤网：月线MACD金叉/多头（更稳定的趋势判断）
2. 第二重滤网：日线RSI/KDJ超卖回调（放宽条件）
3. 第三重滤网：价格企稳或突破（更灵活的入场）
'''

import jqdata
import numpy as np

## 初始化函数
def initialize(context):
    set_benchmark('000300.XSHG')
    set_option('use_real_price', True)
    set_option('order_volume_ratio', 1)
    set_order_cost(OrderCost(open_tax=0, close_tax=0.001,
                             open_commission=0.0003, close_commission=0.0003,
                             close_today_commission=0, min_commission=5), type='stock')

    # ========== 策略参数 ==========
    g.stocknum = 10             # 增加持仓数
    g.max_position_ratio = 0.98

    # 第一重滤网参数（月线MACD）
    g.macd_fast = 12
    g.macd_slow = 26
    g.macd_signal = 9

    # 第二重滤网参数（日线震荡 - 放宽）
    g.rsi_period = 14
    g.rsi_oversold = 50         # 放宽到50
    g.rsi_low = 35              # 极度超卖
    g.kdj_oversold = 40         # 放宽到40

    # 第三重滤网参数（入场确认 - 放宽）
    g.ma_short = 5              # 5日均线
    g.ma_mid = 20               # 20日均线

    # 止盈止损参数
    g.stop_loss = 0.06
    g.take_profit = 0.20
    g.trailing_stop = 0.08

    # 市值筛选（亿）
    g.min_market_cap = 20
    g.max_market_cap = 1500

    # 记录
    g.highest_profit = {}
    g.hold_days = {}

    # 定时任务
    run_daily(morning_screen, '09:35')
    run_daily(check_positions, '14:00')
    run_daily(afternoon_trade, '14:50')

## 早盘筛选
def morning_screen(context):
    g.buy_list = triple_screen_filter(context)
    log.info("【三重滤网】筛选出 %d 只股票" % len(g.buy_list))

## 三重滤网筛选
def triple_screen_filter(context):
    # 基础选股
    q = query(
            valuation.code,
            valuation.market_cap
        ).filter(
            valuation.market_cap.between(g.min_market_cap, g.max_market_cap)
        ).order_by(
            valuation.market_cap.asc()
        ).limit(500)

    df = get_fundamentals(q)
    if df.empty:
        return []

    stock_list = list(df['code'])
    stock_list = filter_basic(stock_list)

    # 三重滤网筛选
    candidates = []
    for stock in stock_list[:150]:
        result = check_triple_screen(stock)
        if result['pass']:
            candidates.append((stock, result['score']))

    # 按评分排序
    candidates.sort(key=lambda x: x[1], reverse=True)
    return [c[0] for c in candidates[:g.stocknum * 3]]

## 检查三重滤网信号
def check_triple_screen(stock):
    """
    三重滤网检查 V2.0：
    1. 第一重：月线MACD金叉/多头
    2. 第二重：日线RSI/KDJ回调
    3. 第三重：价格企稳或突破
    """
    result = {'pass': False, 'score': 0}

    try:
        # 获取更多日线数据（计算月线MACD需要约130天）
        df = attribute_history(stock, 150, '1d', ['close', 'high', 'low'], skip_paused=True)
        if len(df) < 130:
            return result

        close = df['close'].values
        high = df['high'].values
        low = df['low'].values

        # ========== 第一重滤网：月线MACD ==========
        # 模拟月线：每20天取收盘价（或用月末价格）
        monthly_close = []
        for i in range(19, len(close), 20):
            monthly_close.append(close[i])

        if len(monthly_close) < 6:
            # 数据不足，改用日线MACD判断大趋势
            dif, dea, macd = calculate_macd(close)
            if dif[-1] <= dea[-1]:  # MACD死叉
                return result
            if dif[-1] <= 0:  # DIF在零轴下方
                return result
        else:
            # 计算月线MACD
            m_dif, m_dea, m_macd = calculate_macd(np.array(monthly_close))

            # 月线MACD条件（放宽）：
            # 1. MACD金叉（DIF上穿DEA）或
            # 2. MACD柱由绿变红 或
            # 3. DIF > 0 且 DIF > DEA（多头）
            macd_golden = m_dif[-1] > m_dea[-1] and m_dif[-2] <= m_dea[-2]
            macd_turn_red = m_macd[-1] > 0 and m_macd[-2] <= 0
            macd_bullish = m_dif[-1] > 0 and m_dif[-1] > m_dea[-1]

            if not (macd_golden or macd_turn_red or macd_bullish):
                return result

        result['score'] += 30  # 趋势分

        # ========== 第二重滤网：日线震荡指标 ==========
        rsi = calculate_rsi(close, g.rsi_period)
        k, d, j = calculate_kdj(high, low, close)

        # RSI条件（放宽）：
        # 1. RSI < 50（相对低位）或
        # 2. RSI从低位回升
        rsi_current = rsi[-1] if len(rsi) > 0 else 50
        rsi_prev = rsi[-2] if len(rsi) > 1 else 50

        rsi_signal = (rsi_current < g.rsi_oversold) or \
                     (rsi_prev < g.rsi_low and rsi_current > rsi_prev) or \
                     (rsi_current < 60 and rsi_current > rsi_prev)

        # KDJ条件（放宽）：
        # 1. K < D 后金叉 或
        # 2. J < 40 或
        # 3. K/D都在低位回升
        kdj_golden = k[-1] > d[-1] and k[-2] <= d[-2]
        kdj_oversold = j[-1] < g.kdj_oversold or k[-1] < g.kdj_oversold
        kdj_rising = k[-1] > k[-2] and d[-1] > d[-2] and k[-1] < 60

        kdj_signal = kdj_golden or kdj_oversold or kdj_rising

        if not (rsi_signal or kdj_signal):
            return result

        result['score'] += 30

        # ========== 第三重滤网：入场确认（放宽）==========
        current_price = close[-1]
        ma5 = np.mean(close[-g.ma_short:])
        ma20 = np.mean(close[-g.ma_mid:])

        # 入场条件（满足任一）：
        # 1. 价格站上5日均线
        # 2. 价格接近20日均线（±3%）
        # 3. 价格突破近5日高点
        recent_high = np.max(high[-6:-1])

        price_above_ma5 = current_price > ma5
        price_near_ma20 = abs(current_price - ma20) / ma20 < 0.03
        price_breakout = current_price > recent_high * 0.99

        if not (price_above_ma5 or price_near_ma20 or price_breakout):
            return result

        result['score'] += 40

        # 额外加分
        if rsi_current < 35:
            result['score'] += 15
        if kdj_golden:
            result['score'] += 10
        if current_price > ma5 > ma20:
            result['score'] += 10

        result['pass'] = True
        return result

    except:
        return result

## 计算MACD
def calculate_macd(close, fast=12, slow=26, signal=9):
    ema_fast = calculate_ema(close, fast)
    ema_slow = calculate_ema(close, slow)
    dif = ema_fast - ema_slow
    dea = calculate_ema(dif, signal)
    macd = (dif - dea) * 2
    return dif, dea, macd

## 计算EMA
def calculate_ema(data, period):
    ema = np.zeros(len(data))
    ema[0] = data[0]
    multiplier = 2 / (period + 1)
    for i in range(1, len(data)):
        ema[i] = (data[i] - ema[i-1]) * multiplier + ema[i-1]
    return ema

## 计算RSI
def calculate_rsi(close, period=14):
    delta = np.diff(close)
    gain = np.where(delta > 0, delta, 0)
    loss = np.where(delta < 0, -delta, 0)

    avg_gain = np.zeros(len(delta))
    avg_loss = np.zeros(len(delta))

    avg_gain[period-1] = np.mean(gain[:period])
    avg_loss[period-1] = np.mean(loss[:period])

    for i in range(period, len(delta)):
        avg_gain[i] = (avg_gain[i-1] * (period-1) + gain[i]) / period
        avg_loss[i] = (avg_loss[i-1] * (period-1) + loss[i]) / period

    rs = avg_gain / (avg_loss + 1e-10)
    rsi = 100 - 100 / (1 + rs)
    return rsi

## 计算KDJ
def calculate_kdj(high, low, close, n=9, m1=3, m2=3):
    length = len(close)
    rsv = np.zeros(length)
    k = np.zeros(length)
    d = np.zeros(length)
    j = np.zeros(length)

    for i in range(n-1, length):
        hn = np.max(high[i-n+1:i+1])
        ln = np.min(low[i-n+1:i+1])
        rsv[i] = (close[i] - ln) / (hn - ln + 1e-10) * 100

    k[n-1] = 50
    d[n-1] = 50

    for i in range(n, length):
        k[i] = (m1-1)/m1 * k[i-1] + 1/m1 * rsv[i]
        d[i] = (m2-1)/m2 * d[i-1] + 1/m2 * k[i]
        j[i] = 3 * k[i] - 2 * d[i]

    return k, d, j

## 检查持仓
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
        g.hold_days[stock] = g.hold_days.get(stock, 0) + 1

        if stock not in g.highest_profit:
            g.highest_profit[stock] = profit_ratio
        else:
            g.highest_profit[stock] = max(g.highest_profit[stock], profit_ratio)

        highest = g.highest_profit[stock]

        # === 止损 ===
        if profit_ratio < -g.stop_loss:
            log.info("【止损】%s 亏损 %.2f%%" % (stock, profit_ratio * 100))
            order_target(stock, 0)
            clean_stock_data(stock)
            continue

        # === 趋势反转卖出 ===
        if check_trend_reversal(stock):
            log.info("【趋势反转】%s 周线趋势转弱" % stock)
            order_target(stock, 0)
            clean_stock_data(stock)
            continue

        # === 移动止盈 ===
        if highest >= g.take_profit:
            drawdown = highest - profit_ratio
            allowed_drawdown = min(g.trailing_stop + highest * 0.4, 0.18)
            if drawdown >= allowed_drawdown:
                log.info("【移动止盈】%s 最高%.1f%% 回撤%.1f%%" %
                        (stock, highest*100, drawdown*100))
                order_target(stock, 0)
                clean_stock_data(stock)
                continue

        # === 分批止盈 ===
        if profit_ratio >= g.take_profit * 2:
            sell_amount = int(position.closeable_amount * 0.3 / 100) * 100
            if sell_amount >= 100:
                log.info("【止盈】%s +%.1f%%" % (stock, profit_ratio*100))
                order(stock, -sell_amount)

## 检查趋势反转（使用MACD）
def check_trend_reversal(stock):
    try:
        df = attribute_history(stock, 60, '1d', ['close'], skip_paused=True)
        if len(df) < 50:
            return False

        close = df['close'].values
        dif, dea, macd = calculate_macd(close)

        # MACD死叉且DIF < 0
        if dif[-1] < dea[-1] and dif[-1] < 0:
            return True

        # MACD连续3天下降且为负
        if macd[-1] < 0 and macd[-2] < 0 and macd[-3] < 0:
            if macd[-1] < macd[-2] < macd[-3]:
                return True

        return False
    except:
        return False

## 清理数据
def clean_stock_data(stock):
    for d in [g.highest_profit, g.hold_days]:
        if stock in d:
            del d[stock]

## 尾盘交易
def afternoon_trade(context):
    buy_stocks(context)

## 买入函数
def buy_stocks(context):
    if not hasattr(g, 'buy_list') or not g.buy_list:
        return

    position_count = len(context.portfolio.positions)
    if position_count >= g.stocknum:
        return

    available_cash = context.portfolio.available_cash * g.max_position_ratio
    buy_count = min(g.stocknum - position_count, len(g.buy_list))
    if buy_count <= 0 or available_cash < 10000:
        return

    cash_per_stock = available_cash / buy_count

    bought = 0
    for stock in g.buy_list:
        if bought >= buy_count:
            break
        if stock in context.portfolio.positions:
            continue

        # 再次确认三重滤网信号
        result = check_triple_screen(stock)
        if result['pass']:
            order_value(stock, cash_per_stock)
            log.info("【买入】%s 评分:%.0f" % (stock, result['score']))
            g.highest_profit[stock] = 0
            g.hold_days[stock] = 0
            bought += 1

## 基础过滤
def filter_basic(stock_list):
    if not stock_list:
        return []

    current_data = get_current_data()
    filtered = []

    for stock in stock_list:
        if current_data[stock].paused:
            continue
        if current_data[stock].is_st:
            continue
        if 'ST' in current_data[stock].name or '*' in current_data[stock].name:
            continue
        if stock.startswith('688') or stock.startswith('8') or stock.startswith('4'):
            continue
        if current_data[stock].last_price >= current_data[stock].high_limit:
            continue
        if current_data[stock].last_price <= current_data[stock].low_limit:
            continue

        filtered.append(stock)

    return filtered

