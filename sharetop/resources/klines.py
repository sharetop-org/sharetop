"""K-line (OHLCV) data resources for ShareTop API."""

from __future__ import annotations

from typing import (
    Any,
    Dict,
    List,
    Optional,
    Tuple,
    Union
)

import pandas as pd

from ..aio_utils.aio_quotes import run
from .._cache import InstrumentNameCache
from .._types import NOT_GIVEN, NotGiven
from ..utils import _quotes_to_df, get_instrument_region, get_region_timezone
from ._base import SyncResource

from ..generated_model import CompactKlineData, ExFactorEntry

# Maximum symbols per batch request (API limit)
MAX_SYMBOLS_PER_BATCH = 100


def _klines_to_dataframe(
    data: "CompactKlineData",
    symbol: Optional[str] = None,
    name: Optional[str] = None,
) -> "pd.DataFrame":
    """Convert compact K-line data to a pandas DataFrame.

    Parameters
    ----------
    data : CompactKlineData
        Compact columnar K-line data from the API.
    symbol : str, optional
        Symbol code to include as a column.
    name : str, optional
        Instrument name to include as a column.

    Returns
    -------
    pd.DataFrame
        DataFrame with columns: timestamp, open, high, low, close, volume, amount.
    """
    timestamps = data["timestamp"]
    n = len(timestamps) if timestamps else 0

    if n == 0:
        trade_dates = []
        trade_times = []
    else:
        region = get_instrument_region(symbol) if symbol else None
        tz = get_region_timezone(region) if region else None

        if tz:
            dt_index = pd.to_datetime(timestamps, unit="ms", utc=True).tz_convert(tz)
            trade_dates = dt_index.strftime("%Y-%m-%d").tolist()
            trade_times = dt_index.strftime("%Y-%m-%d %H:%M:%S").tolist()
        else:
            trade_dates = [None] * n
            trade_times = [None] * n

    amount_data = data.get("amount", [0.0] * n)

    return pd.DataFrame({
        "symbol": [symbol] * n,
        "name": [name] * n,
        "timestamp": timestamps or [],
        "trade_date": trade_dates,
        "trade_time": trade_times,
        "open": data["open"],
        "high": data["high"],
        "low": data["low"],
        "close": data["close"],
        "volume": data["volume"],
        "amount": amount_data,
    })


def _batch_klines_to_dataframes(
    data: Dict[str, "CompactKlineData"],
    names: Optional[Dict[str, str]] = None,
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
    names = names or {}
    dfs: Dict[str, "pd.DataFrame"] = {}
    for symbol, kline_data in data.items():
        df = _klines_to_dataframe(kline_data, symbol=symbol, name=names.get(symbol))
        dfs[symbol] = df

    return dfs


def _batch_klines_to_df_v2(
    data: List[Dict[str, Any]],
    names: Optional[Dict[str, str]] = None,
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
        symbol = item["stockCode"]
        ts_code = symbol[2:] + "." + symbol[:2]
        df = _quotes_to_df(item["klines"], ts_code=ts_code, unit="ms")
        sum_df[ts_code] = df

    return sum_df

def _factors_to_dataframe(
    data: Dict[str, List["ExFactorEntry"]],
) -> "pd.DataFrame":
    """Convert factor response to a single long-format DataFrame."""
    if not data:
        return pd.DataFrame(columns=["symbol", "timestamp", "trade_date", "ex_factor"])

    rows = []
    for symbol, entries in data.items():
        if not entries:
            continue

        region = get_instrument_region(symbol)
        tz = get_region_timezone(region) if region else None
        timestamps = [e["timestamp"] for e in entries]

        if tz:
            ts_series = pd.to_datetime(timestamps, unit="ms", utc=True).tz_convert(tz)
            trade_dates = ts_series.strftime("%Y-%m-%d").tolist()
        else:
            trade_dates = [None] * len(timestamps)

        rows.extend({
            "symbol": symbol,
            "timestamp": e["timestamp"],
            "trade_date": trade_dates[i],
            "ex_factor": e["ex_factor"],
        } for i, e in enumerate(entries))

    return pd.DataFrame(rows) if rows else pd.DataFrame(columns=["symbol", "timestamp", "trade_date", "ex_factor"])


class Klines(SyncResource):
    """Synchronous interface for K-line (OHLCV) data endpoints.

    Supports returning data as raw dicts or pandas DataFrames.
    When returning DataFrames, instrument names are automatically resolved
    from a local cache (fetched from the instruments API on first access).

    """

    _instrument_cache: Optional[InstrumentNameCache]

    def __init__(
        self, client: Any, instrument_cache: Optional[InstrumentNameCache] = None
    ) -> None:
        super().__init__(client)
        self._instrument_cache = instrument_cache

    def _resolve_name(self, symbol: str) -> Optional[str]:
        if not self._instrument_cache:
            return None
        names = self._instrument_cache.resolve_sync([symbol], self._client)
        return names.get(symbol)

    def _resolve_names(self, symbols: List[str]) -> Dict[str, str]:
        if not self._instrument_cache:
            return {}
        return self._instrument_cache.resolve_sync(symbols, self._client)

    def get_history_data(
        self,
        symbol: str,
        *,
        period: Union[str, None, NotGiven] = NOT_GIVEN,
        count: Union[int, None, NotGiven] = NOT_GIVEN,
        adjust: Union[str, None, NotGiven] = NOT_GIVEN,
        start_time: Union[str, None, NotGiven] = NOT_GIVEN,
        end_time: Union[str, None, NotGiven] = NOT_GIVEN,
        as_df: bool = False,
    ) -> Union[Dict[str, Any], "pd.DataFrame", str]:
        """Get historical K-line data from static endpoint.

        Parameters
        ----------
        as_df
        symbol : str
            Stock code (e.g., "300059.SZ"). Required - cannot be empty.
        period : str, optional
            K-line period. Defaults to "1m" if not specified.
            Valid values: "1m", "5m", "10m", "15m", "30m", "60m", "4h", "1d", etc.
        count : int, optional
            Number of K-lines to return. Defaults to 1000 if not specified or > 1000.
        adjust : str, optional
            Adjustment type. Defaults to "normal" if not specified.
            Valid values: "normal" (不复权), "before" (前复权), "after" (后复权).
        start_time : str, optional
            Start date in YYYYMMDD format (e.g., "20260521").
        end_time : str, optional
            End date in YYYYMMDD format (e.g., "20260525").
        Returns
        -------
        dict or pd.DataFrame
            K-line data. If as_dataframe=True, returns DataFrame with columns:
            timestamp, trade_date, trade_time, open, high, low, close, volume, amount.
        """
        if not symbol:
            raise ValueError("symbol cannot be empty")

        if isinstance(period, NotGiven) or period is None or period == "":
            period = "5m"
        if isinstance(adjust, NotGiven) or adjust is None or adjust == "":
            adjust = "normal"
        if isinstance(count, NotGiven) or count is None or count == "":
            count = 1000

        if period in ["w", "m", "q", "y"] and adjust in ["before", "after"]:
            return "周、月、季、年 K线只提供不复权数据"

        params: Dict[str, Any] = {
            "stockCode": symbol,
            "period": period,
            "type": adjust,
            "count": count,
        }

        if not isinstance(start_time, NotGiven) and start_time is not None:
            params["start_time"] = start_time
        if not isinstance(end_time, NotGiven) and end_time is not None:
            params["end_time"] = end_time

        response = self._client.post("/getData/static/getKlineData", json=params)
        respCode = response.get("respCode")
        if respCode != "0000":
            return response.get("respMsg")

        data = response.get("data", {})

        if as_df and data:
            df = pd.DataFrame(data)
            return df

        return data

    def get_batch_real_time(
        self,
        symbols: List[str],
        *,
        period: Union[str, None, NotGiven] = NOT_GIVEN,
        count: Union[int, None, NotGiven] = NOT_GIVEN,
        adjust: Union[str, None, NotGiven] = NOT_GIVEN,
        as_df: bool = False,
        max_concurrent: int = MAX_SYMBOLS_PER_BATCH,
    ) -> Union[List[Dict[str, Any]], Dict[str, "pd.DataFrame"]]:
        """Get batch real-time K-line data for multiple symbols.

        Parameters
        ----------
        as_df
        symbols : list of str
            List of stock codes (e.g., ["300059.SZ", "600000.SH"]).
        period : str, optional
            K-line period. Defaults to "1m" if not specified or empty.
            Valid values: "1m", "5m", "15m", "30m", "60m", "120m".
        count : int, optional
            Number of K-lines to return. Defaults to 1000 if not specified,
            empty, or > 1000.
        adjust : str, optional
            Adjustment type. Defaults to "normal" if not specified or empty.
            Valid values: "normal" (不复权), "before" (前复权), "after" (后复权).
        as_df : bool, optional
            If True, return dict of DataFrames. Default False.
        max_concurrent : int, optional
            Maximum concurrent requests. Default 100.

        Returns
        -------
        list or dict
            If as_dataframe=False: list of K-line data dicts.
            If as_dataframe=True: dict mapping symbol codes to DataFrames.

        """
        if not symbols:
            return [] if not as_df else {}

        # Apply defaults
        _period = "1m" if isinstance(period, NotGiven) or period is None or period == "" else period
        _adjust = "normal" if isinstance(adjust, NotGiven) or adjust is None or adjust == "" else adjust
        _count = 1000 if isinstance(count, NotGiven) or count is None or count == "" or count > 1000 else count

        if not isinstance(_count, int):
            raise ValueError("count must be an integer")

        params: Dict[str, Any] = {
            "period": _period,
            "type": _adjust,
            "count": _count,
        }

        base_url = self._client.base_url
        default_headers = self._client._build_headers()
        quotes_url = f"{base_url}/getData/realtime/stockKline"

        results, msg = run(
            default_headers,
            quotes_url,
            ts_code_list=symbols,
            kline_params=params,
            max_concurrent=max_concurrent,
        )
        if msg != "成功":
            return msg

        if as_df and results:
            names = self._resolve_names(symbols)
            return _batch_klines_to_df_v2(results, names=names)

        return results

    def _fetch_batch_chunk(
        self,
        symbols: List[str],
        params: Dict[str, Any],
        endpoint: str = "/getData/realtime/stockKline",
    ) -> Tuple[Dict[str, "CompactKlineData"], List[Tuple[str, Exception]]]:
        """Fetch a single batch chunk.

        Returns
        -------
        tuple
            (data dict, list of (symbol, error) for failed symbols)
        """
        symbols_str = ",".join(symbols)
        chunk_params = {**params, "stockCode": symbols_str}

        response = self._client.post(endpoint, json=chunk_params)
        return response["data"], []
