"""A股年报多指标筛选器。

使用 ShareTop 数据源,对全市场上市股票按连续 N 年年报指标做条件筛选。
筛选规则通过 CONFIG 配置化,新增/调整条件无需改动逻辑代码。

规则说明: 年报中的 ROE、毛利率等指标是百分数形式(如 4.94 表示 4.94%),
因此阈值直接使用 25/45 等百分数数值。
"""
from __future__ import annotations
import logging
import time
import operator
from dataclasses import dataclass
from typing import Callable
from tqdm import tqdm
from sharetop import ShareTop

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
log = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# 配置
# ---------------------------------------------------------------------------
# 关注微信公众号 "浔溯de小仓鼠" 获取token
TOKEN = ""
REPORT_TYPE = "年报"
WINDOW_YEARS = 5  # 要求连续满足条件的年报数

MAX_RETRIES = 3          # 单次请求失败后的最大重试次数
RETRY_BACKOFF = 1.5      # 重试间隔起始秒数,每次翻倍
RETRY_BASE_DELAY = 0.5


@dataclass(frozen=True)
class ScreenRule:
    """单条筛选规则: 字段 运算符 阈值。"""

    field: str
    op: str
    threshold: float


SCREEN_RULES: tuple[ScreenRule, ...] = (
    ScreenRule("roe_weighted", ">", 20),           # ROE 加权平均 > 20%
    ScreenRule("gross_profit_margin", ">", 40),    # 毛利率 > 40%
    ScreenRule("current_ratio", ">", 1.5),         # 流动比率 > 1.7
    ScreenRule("quick_ratio", ">=", 1),            # 速动比率 >= 1
)


def _build_rule_checker(rules: tuple[ScreenRule, ...]) -> Callable[[dict], bool]:
    """把规则元组编译成单个年鉴判定函数。"""
    checks: list[Callable[[dict], bool]] = []
    for rule in rules:
        op_fn = getattr(operator, {
            ">": "gt",
            ">=": "ge",
            "<": "lt",
            "<=": "le",
            "==": "eq",
            "!=": "ne",
        }[rule.op])
        checks.append(
            lambda rep, field=rule.field, op_fn=op_fn, thr=rule.threshold: (
                isinstance(rep.get(field), (int, float)) and op_fn(rep[field], thr)
            )
        )
    return lambda report: all(c(report) for c in checks)


# ---------------------------------------------------------------------------
# 数据获取
# ---------------------------------------------------------------------------

def load_stock_universe(client: ShareTop) -> list[dict]:
    """加载全部上市股票(ts_code, name)。"""
    return client.universes.get(
        list_status="L", fields="ts_code,name", as_df=True
    ).to_dict("records")


def _request_with_retry(client: ShareTop, ts_code: str, report_type: str):
    """请求单只股票的财报,失败时指数退避重试,全部失败则返回 None。"""
    for attempt in range(1, MAX_RETRIES + 1):
        try:
            return client.financials.core_financial_indicators(
                symbols=[ts_code], report_type=report_type, as_df=True
            )
        except Exception as exc:  # noqa: BLE001 网络/接口异常需兜底重试
            delay = RETRY_BASE_DELAY * (RETRY_BACKOFF ** (attempt - 1))
            log.warning("请求失败 %s(%s): %s,%.1fs 后重试(%d/%d)",
                        ts_code, type(exc).__name__, exc, delay, attempt, MAX_RETRIES)
            if attempt < MAX_RETRIES:
                time.sleep(delay)
    log.error("重试 %d 次仍失败,跳过 %s", MAX_RETRIES, ts_code)
    return None


def fetch_annual_reports(client: ShareTop, ts_code: str,
                         report_type: str = REPORT_TYPE) -> list[dict]:
    """获取单只股票的全部指定类型财报;请求失败(已重试)则返回空列表。"""
    df = _request_with_retry(client, ts_code, report_type)
    if df is None:
        return []
    if isinstance(df, list):
        return df
    if not isinstance(df, dict):
        log.warning("ts_code=%s 返回了非常规数据类型: %r", ts_code, df)
        return []
    return df[ts_code].to_dict("records")


# ---------------------------------------------------------------------------
# 筛选
# ---------------------------------------------------------------------------

def screen_stocks(
    client: ShareTop,
    *,
    window_years: int = WINDOW_YEARS,
    rules: tuple[ScreenRule, ...] = SCREEN_RULES,
) -> list[dict]:
    """筛选出最近连续 window_years 年年报全部满足 rules 的股票。"""
    pass_check = _build_rule_checker(rules)
    matched: list[dict] = []

    for stock in tqdm(load_stock_universe(client)):
        time.sleep(0.7)
        reports = fetch_annual_reports(client, stock["ts_code"])
        if len(reports) < window_years:
            continue
        recent = reports[-window_years:]
        if all(pass_check(r) for r in recent):
            matched.append(stock)
    return matched


# ---------------------------------------------------------------------------
# 入口
# ---------------------------------------------------------------------------

def main() -> None:
    from pprint import pprint
    print("TOKEN==:", TOKEN)

    client = ShareTop(token=TOKEN)
    results = screen_stocks(client)
    print(f"共筛选出 {len(results)} 家公司:")
    pprint(results)


if __name__ == "__main__":
    main()