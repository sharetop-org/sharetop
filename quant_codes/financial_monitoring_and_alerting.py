#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""创N年新低 邮箱报警监测工具。

快速上手:
    python financial_monitoring_and_alerting.py --symbols 600036.SH,600519.SH --low_years 5

逻辑(与 buy_and_backtest_cal.py 口径一致):
  对每只指定股票取前复权(before)日K, 当日收盘价 ≤ 近 low_years 年(约 low_years*250 个
  交易日)滚动最低收盘价, 即判定为"达到指定年限的股价低位", 触发邮箱报警。

邮箱(SMTP)配置通过环境变量给出(推荐), 也可改下方 EMAIL_DEFAULT 默认值:
    SMTP_HOST   SMTP_PORT   SMTP_USER   SMTP_PASS   SMTP_FROM   MAIL_TO
    SMTP_SSL=1 表示 465 端口 SSL, 否则 587 STARTTLS。

默认只在价格创出「比上次报警更低的新低」时才再次发信(由状态文件去重), 避免反复轰炸。
"""

from sharetop import ShareTop

import argparse
import json
import os
import time
from datetime import datetime

import pandas as pd

# 默认行情 token(可被环境变量 SHARETOP_TOKEN 覆盖)
SHARETOP_TOKEN = os.environ.get(
    "SHARETOP_TOKEN", "6d5876bf73eb249df43a1748a197798cad3ef3b3ed5dc528de")

# ============================ 邮箱(SMTP)配置 ============================
# 优先读取环境变量; 留空则用括号中的占位默认值。
#   SMTP_HOST / SMTP_PORT / SMTP_USER / SMTP_PASS / SMTP_FROM / MAIL_TO
#   SMTP_FROM 缺省取 SMTP_USER; MAIL_TO 可用英文逗号分隔多个收件人。
EMAIL_DEFAULT = {
    "host": os.environ.get("SMTP_HOST", "smtp.qq.com"),
    "port": int(os.environ.get("SMTP_PORT", "587")),
    "user": os.environ.get("SMTP_USER", ""),        # 发件邮箱账号
    "pass": os.environ.get("SMTP_PASS", ""),        # 授权码
    "from_": os.environ.get("SMTP_FROM", ""),       # 为空则取 user
    "to": os.environ.get("MAIL_TO", ""),            # 收件人, 逗号分隔
    "use_ssl": os.environ.get("SMTP_SSL", "0") == "1",  # 1=465 SSL, 0=587 STARTTLS
}

# 状态文件: 记录已对每只股票报警过的低位价, 避免重复发信
STATE_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "alert_state.json")


def get_client() -> ShareTop:
    return ShareTop(token=SHARETOP_TOKEN)


def prep_adj(d: pd.DataFrame) -> pd.DataFrame:
    """把 K线原始 DataFrame 规整为按时间升序。"""
    d = d.copy()
    d["trade_time"] = pd.to_datetime(d["trade_time"])
    return d.sort_values("trade_time").reset_index(drop=True)


def get_name(client: ShareTop, symbol: str) -> str:
    """根据 ts_code 获取股票简称。"""
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


def check_low(client: ShareTop, symbol: str, low_years: int) -> dict:
    """监测指定股票是否创出 low_years 年低位。

    口径(与 buy_and_backtest_cal 一致): 前复权日K, '当日收盘 ≤ 近 low_years 年滚动
    最低收盘价' 判定为创新低。数据不足 low_years 年时返回 status='insufficient'。

    返回 dict 关键字段:
      status : 'hit' | 'no' | 'insufficient'
      hit    : 是否创出 low_years 年新低(仅 status=hit/no 有意义)
      latest_* : 最新交易日价格与日期
      low_threshold : 近 low_years 年滚动最低收盘价(前复权)
      prior_hist_low : 今日更早前的历史最低收盘价
      below_pct : 最新收盘相对 prior_hist_low 的涨跌幅(%)
    """
    lookback = low_years * 250
    qjq = prep_adj(client.klines.get_history_data(
        symbol, period="d", count=50000, adjust="before", as_df=True))

    if len(qjq) < lookback:
        return {"symbol": symbol, "name": get_name(client, symbol),
                "status": "insufficient",
                "ihist": qjq["trade_time"].iloc[0].date(),
                "hit": False}

    low = qjq["close"].rolling(lookback, min_periods=lookback).min()
    new_low = (qjq["close"] <= low)                  # 当日是否创 low_years 年新低
    last = qjq.iloc[-1]

    prev_behind = qjq["close"].iloc[:-1]             # 今日之前的历史收盘
    prior_hist_low = float(prev_behind.min())        # 今日更早前的最低收盘价

    latest_close = float(last["close"])
    latest_date = pd.to_datetime(last["trade_time"]).date()
    low_threshold = float(low.iloc[-1])              # 近 low_years 年滚动最低价
    hit = bool(new_low.iloc[-1])

    if len(low) > 1:
        low_idx = int(low.iloc[:-1].idxmin())        # 前期最低位所在行
        low_hist_date = pd.to_datetime(qjq["trade_time"].iloc[low_idx]).date()
    else:
        low_hist_date = latest_date

    below_pct = (latest_close / prior_hist_low - 1) * 100 if prior_hist_low else 0.0

    return {"symbol": symbol, "name": get_name(client, symbol),
            "status": "hit" if hit else "no", "hit": hit,
            "latest_date": latest_date, "latest_close": latest_close,
            "low_threshold": low_threshold, "low_hist_date": low_hist_date,
            "prior_hist_low": prior_hist_low, "below_pct": below_pct}


def load_state(path: str) -> dict:
    try:
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        return {}


def save_state(path: str, state: dict) -> None:
    with open(path, "w", encoding="utf-8") as f:
        json.dump(state, f, ensure_ascii=False, indent=2)


def should_alert(symbol: str, latest_close: float, state: dict) -> bool:
    """去重: 仅当价格创下低于已报警价位的新低时才再次报警。"""
    prev_low = (state.get(symbol) or {}).get("low")
    if prev_low is None:
        return True
    return latest_close < prev_low - 1e-9


def send_mail(cfg: dict, subject: str, html: str, text: str) -> None:
    """smtplib 发信(支持 465 SSL / 587 STARTTLS)。"""
    import smtplib
    from email.mime.text import MIMEText

    from_addr = cfg["from_"] or cfg.get("user", "")
    to_list = [t.strip() for t in cfg["to"].split(",") if t.strip()]
    if not cfg.get("user") or not cfg.get("pass") or not to_list:
        raise ValueError("邮箱未配置完整: 请设置 SMTP_USER/SMTP_PASS/MAIL_TO(环境变量或 EMAIL_DEFAULT)。")

    msg = MIMEText(html, _subtype="html", _charset="utf-8")
    msg["Subject"] = subject
    msg["From"] = f"股票低位报警 <{from_addr}>"

    if cfg.get("use_ssl"):
        server = smtplib.SMTP_SSL(cfg["host"], cfg["port"], timeout=20)
    else:
        server = smtplib.SMTP(cfg["host"], cfg["port"], timeout=20)
    server.ehlo()
    if not cfg.get("use_ssl"):
        server.starttls()
        server.ehlo()
    server.login(cfg["user"], cfg["pass"])
    server.sendmail(from_addr, to_list, msg.as_string())
    server.quit()


def notify_hits(rows, low_years, state, cfg) -> int:
    """组装命中的报警邮件并发信; 记录去重状态。返回实际发送数量。"""
    to_alert = [r for r in rows
                if r.get("status") == "hit"
                and should_alert(r["symbol"], r["latest_close"], state)]
    if not to_alert:
        return 0

    stamp = datetime.now().strftime("%Y-%m-%d %H:%M")
    subject = f"[低位报警] {len(to_alert)} 只股票创{low_years}年新低 {stamp}"

    text_rows = []
    html_rows = []
    for r in to_alert:
        text_rows.append(
            f"{r['name']}({r['symbol']})  现价 {r['latest_close']:.2f} 元, "
            f"低于近 {low_years} 年低点, 较历史最低价 {r['below_pct']:+.2f}%")
        html_rows.append(
            f"<tr><td>{r['symbol']}</td><td>{r['name']}</td>"
            f"<td>{r['latest_date']}</td><td>{r['latest_close']:.2f}</td>"
            f"<td>{r['low_threshold']:.2f}</td><td>{r['below_pct']:+.2f}%</td></tr>")
        state[r["symbol"]] = {"low": round(r["latest_close"], 4), "date": r["latest_date"].isoformat()}

    text = stamp + "\n" + "\n".join(text_rows)
    html = ("<h3>股票创 N 年新低报警</h3><table border='1' cellpadding='6' cellspacing='0'>"
            "<tr><th>代码</th><th>名称</th><th>日期</th><th>现价</th>"
            "<th>N年低点阈值</th><th>较历史最低</th></tr>"
            + "".join(html_rows) + "</table>")

    send_mail(cfg, subject, html, text)
    return len(to_alert)


def main():
    parser = argparse.ArgumentParser(description="创N年新低 邮箱报警(监测)")
    parser.add_argument("--symbols", type=str, default=None,
                        help="股票代码, 多个英文逗号分隔, 如 600036.SH,600519.SH")
    parser.add_argument("--low_years", type=int, default=5, help="低点年数, 默认5")
    parser.add_argument("--interval", type=int, default=0,
                        help="轮询间隔秒, 0=只跑一次即退出")
    parser.add_argument("--state", type=str, default=STATE_FILE, help="去重状态文件路径")
    args = parser.parse_args()

    symbols = [s.strip() for s in (args.symbols or "").split(",") if s.strip()]
    if not symbols:
        symbols = [s.strip() for s in
                   os.environ.get("WATCH_SYMBOLS", "600036.SH").split(",") if s.strip()]
    if not symbols:
        parser.error("请用 --symbols='600054.SH,600519.SH' 指定要监测的股票代码")

    client = get_client()
    cfg = dict(EMAIL_DEFAULT)

    while True:
        state = load_state(args.state)
        rows = [check_low(client, s, args.low_years) for s in symbols]
        for r in rows:
            if r["status"] == "insufficient":
                print(f"  {r['name']}({r['symbol']}) 上市不足{args.low_years}年({r['ihist']}至今), 跳过")
            elif r["status"] == "no":
                print(f"  {r['name']}({r['symbol']}) 现价 {r['latest_close']:.2f}, 未创{args.low_years}年新低")
            else:
                print(f"  {r['name']}({r['symbol']}) 现价 {r['latest_close']:.2f} 已创{args.low_years}年新低")

        n = notify_hits(rows, args.low_years, state, cfg)
        save_state(args.state, state)
        stamp = datetime.now().strftime("%H:%M:%S")
        if n:
            print(f"[{stamp}] 已发送 {n} 只报警邮件")
        else:
            print(f"[{stamp}] 无新报警")
        if not args.interval:
            break
        time.sleep(args.interval)


if __name__ == "__main__":
    main()