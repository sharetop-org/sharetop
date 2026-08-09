import datetime
from typing import List, Union, Dict, Any, Optional
from zoneinfo import ZoneInfo

import pandas as pd


CN_TZ = ZoneInfo("Asia/Shanghai")
US_TZ = ZoneInfo("America/New_York")
HK_TZ = ZoneInfo("Asia/Hong_Kong")

symbol_suffix_region_map = {
    "SH": "CN",
    "SZ": "CN",
    "BJ": "CN",
    "US": "US",
    "HK": "HK",
    "SHF": "CN",
    "DCE": "CN",
    "ZCE": "CN",
    "CFX": "CN",
    "INE": "CN",
    "GFE": "CN",
}

region_timezone_map = {
    "CN": CN_TZ,
    "US": US_TZ,
    "HK": HK_TZ,
}


def get_instrument_region(symbol: str):
    return symbol_suffix_region_map.get(
        symbol.rsplit(".", 1)[-1],
    )


def get_region_timezone(region: str):
    return region_timezone_map.get(region)


def instrument_timestamp_to_datetime(symbol: str, timestamp: int, unit="ms"):
    tz = get_region_timezone(get_instrument_region(symbol))
    if tz is None:
        return None

    dt = (
        datetime.datetime.fromtimestamp(timestamp / 1000, tz)
        if unit == "ms"
        else datetime.datetime.fromtimestamp(timestamp, tz)
    )
    return dt


def instrument_timestamp_to_trade_date(symbol: str, timestamp: int, unit="ms"):
    dt = instrument_timestamp_to_datetime(symbol, timestamp, unit)
    return dt.strftime("%Y-%m-%d")


def instrument_timestamp_to_trade_time(symbol: str, timestamp: int, unit="ms"):
    dt = instrument_timestamp_to_datetime(symbol, timestamp, unit)
    return dt.strftime("%Y-%m-%d %H:%M:%S")


def instrument_iso_datetime_to_local(dt_str: str, symbol: str) -> str:
    """Convert ISO datetime string to local time for the given symbol's region.

    Parameters
    ----------
    dt_str : str
        ISO datetime string, e.g., "2026-05-20T16:00:00.000+00:00"
    symbol : str
        Symbol code to determine the target timezone (e.g., "603435.SH")

    Returns
    -------
    str
        Local datetime string in "%Y-%m-%d %H:%M:%S" format
    """
    from dateutil import parser

    # Parse ISO datetime
    dt = parser.parse(dt_str)
    # Get target timezone based on symbol
    region = get_instrument_region(symbol)
    if region is None:
        return dt_str
    tz = get_region_timezone(region)
    if tz is None:
        return dt_str
    # Convert to target timezone
    dt_local = dt.astimezone(tz)
    return dt_local.strftime("%Y-%m-%d %H:%M:%S")


def is_valid_yyyymmdd(date_str: str) -> bool:
    """
    判断yyyymmdd字符串是否符合日期字符串
    Parameters
    ----------
    date_str

    Returns
    -------

    """
    try:
        datetime.datetime.strptime(date_str, "%Y%m%d")
        return True
    except ValueError:
        return False


def _quotes_to_df(data: List[Union["Quote", dict[str, str]]], ts_code: str = None, unit: str = None) -> "pd.DataFrame":
    """Convert quote data to a pandas DataFrame.

    Parameters
    ----------
    data : list of Quote
        List of quote dictionaries.

    Returns
    -------
    pd.DataFrame
        DataFrame with symbol as index. Includes trade_date, trade_time columns
        and flattened ext fields with "ext." prefix (e.g., ext.limit_up, ext.change_pct).
    """
    import pandas as pd

    if not data:
        return pd.DataFrame()

    # Build rows with flattened ext fields
    rows = []
    for q in data:
        row = {
            k: v
            for k, v in q.items()
            if k not in ("ext", "session")  # Handle ext separately, skip session
        }
        if ts_code:
            q["ts_code"] = ts_code
        # Add trade_date and trade_time
        row["trade_date"] = instrument_timestamp_to_trade_date(
            q["ts_code"], q["timestamp"], unit=unit
        )
        row["trade_time"] = instrument_timestamp_to_trade_time(
            q["ts_code"], q["timestamp"], unit=unit
        )

        # Flatten ext field with "ext." prefix for all fields
        ext = q.get("ext")
        if ext:
            for key, value in ext.items():
                # Skip None values and nested dicts (like bid_ask)
                if value is not None and not isinstance(value, dict):
                    row[f"ext.{key}"] = value

        rows.append(row)

    df = pd.DataFrame(rows)
    return df


def _batch_financials_df(
    data: List[List[Dict[str, Any]]],
) -> Dict[str, "pd.DataFrame"]:
    """Convert batch K-line data to DataFrames with optional name column.

    Parameters
    ----------
    data : dict
        Dictionary mapping symbol codes to compact K-line data.
    names : dict, optional
        Dictionary mapping symbol codes to instrument names.

    Returns
    -------
    dict of str to pd.DataFrame
        Dictionary mapping symbol codes to pandas DataFrames.
    """
    # from .quotes import _quotes_to_dataframe
    # names = names or {}
    sum_df: Dict[str, "pd.DataFrame"] = {}
    for item in data:
        ts_code = item[0]
        df = None
        sum_df[ts_code] = df

    return sum_df
