from sharetop import ShareTop

import pandas as pd

client = ShareTop(token="6d5876bf73eb249df43a1748a197798cad3ef3b3ed5dc528de")


def prep_adj(d):
    d = d.copy()
    d["trade_time"] = pd.to_datetime(d["trade_time"])
    return d.sort_values("trade_time").reset_index(drop=True)


def get_name(symbol):
    """根据 ts_code 获取股票简称(universes 返回 list, 取第一个匹配项)。"""
    try:
        rows = client.universes.get(ts_code=symbol, as_df=False)
        if isinstance(rows, list) and rows:
            hit = next((r for r in rows if r.get("ts_code") == symbol), rows[0])
            return hit.get("name", symbol)
        if isinstance(rows, dict):
            return rows.get("name", symbol)
    except Exception:
        pass
    return symbol


def xirr(flows):
    """年化内部收益率(XIRR)。

    flows: [(日期, 金额)]。以最早日期为基准年限,
    求解 r 使 Σ 金额_i / (1+r)^((日期_i-基准)/365.25) = 0。
    区间加倍搜索 + 二分收敛; 失败返回 None。
    """
    if not flows or len(flows) < 2:
        return None
    ref = min(d for d, _ in flows)
    tt = [(d - ref).days / 365.25 for d, _ in flows]
    amts = [a for _, a in flows]

    def f(r):  # 定义 in 范围内单调
        return sum(a * (1 + r) ** (-t) for a, t in zip(amts, tt))

    lo, hi = -1 + 1e-6, 1.0
    flo, fhi = f(lo), f(hi)
    if flo * fhi > 0:                       # 同号 → 拓宽上界
        while flo * fhi > 0 and hi < 1e16:
            hi *= 2
            fhi = f(hi)
    if flo * fhi > 0:                       # 仍同号(例: 全复制/无解)
        return None
    for _ in range(300):
        mid = (lo + hi) / 2
        fm = f(mid)
        if abs(fm) < 1e-12 or hi - lo < 1e-13:
            return mid
        if flo * fm < 0:
            hi, fhi = mid, fm
        else:
            lo, flo = mid, fm
    return (lo + hi) / 2


def backtest(symbol, window_start=None, low_years=5,
             buy_amount=10000.0, lot=100, tax_mode="before"):
    """创low_years年新低买入 策略回测(只买不卖)。

    分工口径:
      - 前复权(before)价判定"创low_years年新低"买入日期
      - 不复权(normal)价作为当天真实成交价下单, 按整手(100股)向下取整
      - 逐年累加现金分红, 并处理送/转股带来的持股数变化
      - 最终资产 = 今日不复权收盘价 x 总股数 + 历年现金分红累计

    window_start: 回测起点。默认 None = 以该公司上市日(首根K线)为起点。
    """
    lookback = low_years * 250
    name = get_name(symbol)

    qjq = prep_adj(client.klines.get_history_data(symbol, period="d",
                                                  count=50000, adjust="before", as_df=True))
    bfq = prep_adj(client.klines.get_history_data(symbol, period="d",
                                                  count=50000, adjust="normal", as_df=True))

    # 回测起点：默认取该股上市日(首根K线时间)
    if window_start is None:
        window_start = qjq["trade_time"].iloc[0]
    else:
        window_start = pd.Timestamp(window_start)

    # 1) 前复权定买入日期
    qjq["low"] = qjq["close"].rolling(lookback, min_periods=lookback).min()
    new_low = qjq["close"] <= qjq["low"]              # 当日创指定年新低
    buy_dates = qjq.loc[new_low & (qjq["trade_time"] >= window_start), "trade_time"].reset_index(drop=True)

    if buy_dates.empty:
        return {"symbol": symbol, "name": name, "low_years": low_years,
                "ihist": qjq["trade_time"].iloc[0].date(),
                "buys": 0, "invested": 0.0, "shares": 0.0,
                "div": 0.0, "assets": 0.0, "profit": 0.0, "ret": 0.0, "annual": 0.0,
                "detail": pd.DataFrame()}

    # 2) 不复权真实价 + 按整手取整下单
    price = bfq.set_index("trade_time")["close"].loc[buy_dates].astype(float)
    qjq_price = qjq.set_index("trade_time")["close"].loc[buy_dates].astype(float)  # 当日前复权价
    lots = (buy_amount / price // lot).astype(int)
    shares_ea = (lots * lot).clip(lower=lot)   # 金额买不起一手时, 直接买一手(100股)
    cost_ea = shares_ea * price

    # 3) 分红 + 送转
    try:
        div = client.financials.stock_dividend(symbols=[symbol], as_df=True)[symbol].copy()
        div["ex"] = pd.to_datetime(div["ex_rights_dividend_date"], errors="coerce")
        div = div.dropna(subset=["ex"])
        div = div[div["current_status"].astype(str) == "5"]    # 仅统计已实施完成(5)的分红/送转
        div = div.sort_values("ex").reset_index(drop=True)
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
    flows = []                                  # XIRR 现金流: 买入为负, 分红为正
    for date, add_shares, cash, mult in events:
        if add_shares is not None:
            # 该笔买入对应花费(按日期对齐到 cost_ea)
            i = (buy_dates == date).idxmax()
            flows.append((date, -cost_ea.iloc[i]))
            shares += add_shares
        else:
            cash_div += shares * cash
            flows.append((date, shares * cash))
            shares *= (1.0 + mult)

    today = bfq["trade_time"].iloc[-1]
    price_now = bfq["close"].iloc[-1]
    invested = cost_ea.sum()
    assets = shares * price_now + cash_div
    profit = assets - invested
    ret = assets / invested - 1 if invested else 0.0
    # 期末市值作为最后一笔正现金流, 用 XIRR 计算资金时间加权年化
    flows.append((today, shares * price_now))
    annual = xirr(flows)
    if annual is None:                      # XIRR 退化为按首笔买入持有期年化
        first_buy = buy_dates.iloc[0]
        annual = (assets / invested) ** (365.25 / (today - first_buy).days) - 1

    # 每次买入明细(时间 + 前复权价)
    buy_detail = pd.DataFrame({
        "买入日期": pd.to_datetime(buy_dates).dt.date.values,
        "前复权价格": qjq_price.round(3).values,
        "不复权价格": price.round(2).values,
        "买入股数": shares_ea.values,
        "实际花费": cost_ea.round(0).astype(int).values,
    })

    return {"symbol": symbol, "name": name, "low_years": low_years,
            "ihist": qjq["trade_time"].iloc[0].date(),
            "buys": int(len(buy_dates)), "invested": invested,
            "shares": shares, "div": cash_div, "assets": assets,
            "profit": profit, "ret": ret, "annual": annual,
            "detail": buy_detail}


if __name__ == "__main__":
    """
    使用样例命令： python buy_and_backtest_cal.py --low_years 3 --buy_amount 10000 --symbols 600036.SH
    """
    import sys
    import argparse

    # --name=value 风格参数:  --symbols 必填
    parser = argparse.ArgumentParser(description="创N年新低买入回测(只买不卖)")
    parser.add_argument("--low_years", type=int, default=5,
                        help="低点年数, 默认5")
    parser.add_argument("--buy_amount", type=float, default=10000.0,
                        help="单次买入金额, 默认10000")
    parser.add_argument("--symbols", type=str, required=True,
                        help="股票代码, 多个用英文逗号分隔, 必填, 如 600054.SH,600519.SH")
    args = parser.parse_args()

    if not args.symbols:
        parser.error("参数 --symbols 必传: 请用 --symbols='600054.SH,600519.SH' 指定要回测的股票代码")

    LOW_YEARS = args.low_years
    BUY_AMOUNT = args.buy_amount
    symbols = [s.strip() for s in args.symbols.split(",") if s.strip()]

    # 外部传入 low_years / buy_amount; 不传则用默认 5 / 10000
    rows = [backtest(s, low_years=LOW_YEARS, buy_amount=BUY_AMOUNT) for s in symbols]
    res = pd.DataFrame(rows)
    low_years = int(res["low_years"].iloc[0])

    pd.set_option("display.width", 250)
    show = res[["symbol", "name", "ihist", "buys", "invested", "div", "assets", "profit"]].copy()
    show["ihist"] = pd.to_datetime(show["ihist"]).dt.strftime("%Y-%m")
    # 金额列转整数, 去掉 .0 避免视觉错位
    for c in ("invested", "div", "assets", "profit"):
        show[c] = show[c].astype("int64")
    show["总收益率%"] = (res["ret"] * 100).round(2)
    show["复合年化%"] = (res["annual"] * 100).round(2)
    show.columns = ["代码", "简称", "行情起始", "买入次", "投入本金", "现金分红", "总资产", "获利", "总收益率(%)", "复合年化(%)"]
    print(f"策略: 创 {low_years} 年新低, 每次买入 {int(BUY_AMOUNT):,} 元(买不起一手则买1手), 只买不卖, 含现金股息, XIRR=复合年化收益率")
    print(show.to_string(index=False, justify="center"))

    # 逐行一一对应打印, 彻底避免列错位
    print("\n===== 单只明细(键值一一对应) =====")
    for _, r in res.iterrows():
        print(f"{r['name']} {r['symbol']}")
        print(f"  低点年限    : {int(r['low_years'])} 年低点")
        print(f"  累计买入次  : {int(r['buys'])} 次")
        print(f"  累计投入本金: {int(r['invested']):,} 元")
        print(f"  当前持股    : {int(r['shares']):,} 股")
        print(f"  现金分红累计: {int(r['div']):,} 元")
        print(f"  最终总资产  : {int(r['assets']):,} 元")
        print(f"  获利金额    : {int(r['profit']):,} 元")
        print(f"  总收益率    : {r['ret']*100:+.2f}%")
        print(f"  复合年化收益率 : {r['annual']*100:+.2f}%(XIRR)")
        if r["detail"] is not None and not r["detail"].empty:
            print("  买入明细(时间 + 前复权价):")
            print(r["detail"].to_string(index=False, justify="center"))
        print()

    print("\n说明:")
    print(f" - 『{low_years}年新低』指当日收盘价 ≤ 前复权近 {low_years} 年(约{low_years*250}个交易日)滚动最低收盘价, 即跌破自己最近 {low_years} 年的低点即买入。")
    print(" - 买入次=0 表示该股为长期上行趋势, 从未创出过低点, 策略自然无信号。")
    print(" - 现金分红按税前元/股累加,送转股已并入持股数。")