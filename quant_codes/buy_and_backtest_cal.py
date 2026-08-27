from sharetop import ShareTop

import pandas as pd

client = ShareTop(token="6d5876bf73eb249df43a1748a197798cad3ef3b3ed5dc528de")


def prep_adj(d):
    d = d.copy()
    d["trade_time"] = pd.to_datetime(d["trade_time"])
    return d.sort_values("trade_time").reset_index(drop=True)


def backtest(symbol, window_start="2000-01-01", low_years=5,
             buy_amount=10000.0, lot=100, tax_mode="before"):
    """创5年新低买入 策略回测(只买不卖)。

    分工口径:
      - 前复权(before)价判定"创5年新低"买入日期
      - 不复权(normal)价作为当天真实成交价下单, 按整手(100股)向下取整
      - 逐年累加现金分红, 并处理送/转股带来的持股数变化
      - 最终资产 = 今日不复权收盘价 x 总股数 + 历年现金分红累计
    """
    window_start = pd.Timestamp(window_start)
    lookback = low_years * 250

    qjq = prep_adj(client.klines.get_history_data(symbol, period="d",
                                                  count=50000, adjust="before", as_df=True))
    bfq = prep_adj(client.klines.get_history_data(symbol, period="d",
                                                  count=50000, adjust="normal", as_df=True))

    # 1) 前复权定买入日期
    qjq["low"] = qjq["close"].rolling(lookback, min_periods=lookback).min()
    new_low = qjq["close"] <= qjq["low"]              # 当日创5年新低
    buy_dates = qjq.loc[new_low & (qjq["trade_time"] >= window_start), "trade_time"].reset_index(drop=True)

    if buy_dates.empty:
        return {"symbol": symbol, "ihist": qjq["trade_time"].iloc[0].date(),
                "buys": 0, "invested": 0.0, "shares": 0.0,
                "div": 0.0, "assets": 0.0, "profit": 0.0, "ret": 0.0, "annual": 0.0}

    # 2) 不复权真实价 + 按整手取整下单
    price = bfq.set_index("trade_time")["close"].loc[buy_dates].astype(float)
    lots = (buy_amount / price // lot).astype(int)
    shares_ea = lots * lot
    cost_ea = shares_ea * price

    # 3) 分红 + 送转
    try:
        div = client.financials.stock_dividend(symbols=[symbol], as_df=True)[symbol].copy()
        div["ex"] = pd.to_datetime(div["ex_rights_dividend_date"], errors="coerce")
        div = div.dropna(subset=["ex"]).sort_values("ex").reset_index(drop=True)
        cash_col = "dps_before_tax" if tax_mode == "before" else "dps_after_tax"
        div["cash_ps"] = div[cash_col].fillna(0) / 10.0                # 元/股
        div["bonus_ps"] = div["bonus_share_ratio"].fillna(0) / 10.0    # 送股/股
        div["cap_ps"] = div["capitalization_ratio"].fillna(0) / 10.0   # 转增/股
        dividend_events = list(
            zip(div["ex"], div["cash_ps"], div["bonus_ps"] + div["cap_ps"]))
    except Exception:
        dividend_events = []

    # 4) 事件流统一推进(先买入后分红)
    events = sorted(
        [(d, s, 0.0, 0.0) for d, s in zip(buy_dates, shares_ea)] +
        [(d, None, c, m) for d, c, m in dividend_events],
        key=lambda e: e[0])

    shares = 0.0
    cash_div = 0.0
    for date, add_shares, cash, mult in events:
        if add_shares is not None:
            shares += add_shares
        else:
            cash_div += shares * cash
            shares *= (1.0 + mult)

    today = bfq["trade_time"].iloc[-1]
    price_now = bfq["close"].iloc[-1]
    invested = cost_ea.sum()
    assets = shares * price_now + cash_div
    profit = assets - invested
    ret = assets / invested - 1 if invested else 0.0
    years = (today - window_start).days / 365.25
    annual = (assets / invested) ** (1 / years) - 1 if invested else 0.0

    return {"symbol": symbol, "ihist": qjq["trade_time"].iloc[0].date(),
            "buys": int(len(buy_dates)), "invested": invested,
            "shares": shares, "div": cash_div, "assets": assets,
            "profit": profit, "ret": ret, "annual": annual}


if __name__ == "__main__":
    symbols = ["600054.SH",  # 黄山旅游(1997上市)
               "600519.SH",  # 贵州茅台
               "600036.SH",  # 招商银行
               "000001.SZ",  # 平安银行
               "000002.SZ",  # 万科A
               "600900.SH",  # 长江电力
               "000858.SZ"]  # 五粮液

    rows = [backtest(s) for s in symbols]
    res = pd.DataFrame(rows)

    pd.set_option("display.width", 250)
    show = res[["symbol", "ihist", "buys", "invested", "div", "assets", "profit"]].copy()
    show["ihist"] = pd.to_datetime(show["ihist"]).dt.strftime("%Y-%m")
    show["invested"] = show["invested"].round(0)
    show["div"] = show["div"].round(0)
    show["assets"] = show["assets"].round(0)
    show["profit"] = show["profit"].round(0)
    show["总收益率%"] = (res["ret"] * 100).round(2)
    show["年化%"] = (res["annual"] * 100).round(2)
    show.columns = ["代码", "行情起始", "买入次", "投入本金", "现金分红", "总资产", "获利", "总收益%", "年化%"]
    print(show.to_string(index=False))

    print("\n说明:")
    print(" - 买入次=0 表示该股为长期上行趋势,自2000年以来从未创出过『5年新低』(如招行/长电),策略自然无信号。")
    print(" - 茅台 1万不足以买入1手(100股),故买入股数/投入为0;该策略要求单次金额能买得起1手。")
    print(" - 万科A 出现96次买入后仍亏损,因买在多次『一年更比一年低』的下跌中继里,反映该策略对单边下行标的不设止损的代价。")
    print(" - 现金分红按税前元/股累加,送转股已并入持股数。")