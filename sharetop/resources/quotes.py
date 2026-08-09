"""Real-time quote resources for ShareTop API."""
from __future__ import annotations

import inspect
from urllib.parse import urljoin
from typing import Dict, List, Literal, Union, overload
try:
    from gevent.pool import Pool
except ImportError:
    Pool = None  # type: ignore
from ..utils import (
    instrument_timestamp_to_trade_date,
    instrument_timestamp_to_trade_time,
    _quotes_to_df
)
from .._types import NOT_GIVEN, NotGiven
from .market import Universes
from ._base import SyncResource
from sharetop.aio_utils.aio_quotes import run

import pandas as pd



QUOTE_REALTIME_ENDPOINT_MAP = {
    "stock_fund_flow": "api/getData/realtime/stockFundFlow",
    "stock_deep_quote": "api/getData/realtime/stockQuote"
}


def _quotes_to_dataframe(data: List["Quote"], ts_code: str = None, unit: str = None) -> "pd.DataFrame":
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


class Quotes(SyncResource):
    """Synchronous interface for real-time quote endpoints.

    Supports querying quotes by symbol codes or universe IDs.

    """

    @overload
    def get(
        self,
        *,
        symbols: Union[List[str], str, None] = None,
        exchange: Union[List[str], str, None] = None,
        as_df: Literal[False] = False,
    ) -> List["Quote"]: ...

    @overload
    def get(
        self,
        *,
        symbols: Union[List[str], str, None] = None,
        exchange: Union[List[str], str, None] = None,
        as_df: Literal[True],
    ) -> "pd.DataFrame": ...

    def get(
        self,
        *,
        symbols: Union[List[str], str, None] = None,
        exchange: Union[List[str], str, None] = None,
        as_df: bool = False
    ):
        """Get real-time quotes for symbols or universes.

        Must provide either `symbols` or `universes`, but not both.

        Parameters
        ----------
        fields
        symbols : str or list of str, optional
            Symbol code(s) to query. Can be a single symbol, comma-separated
            string, or list of symbols.
        exchange : str or list of str, optional
            SSE上交所 SZSE深交所 BSE北交所
            Universe ID(s) to query. Can be a single ID, comma-separated
            string, or list of IDs.
        as_df : bool, optional
            If True, return a pandas DataFrame indexed by symbol.
            If False (default), return a list of Quote dicts.

        Returns
        -------
        list of Quote or pd.DataFrame
            Quote data for the requested symbols.

            Each Quote contains:
            - symbol: Symbol code
            - name: Symbol name
            - region: Region code
            - last_price: Latest price
            - prev_close: Previous close
            - open, high, low: OHLC prices
            - volume: Trading volume
            - amount: Trading amount
            - timestamp: Quote timestamp (milliseconds)
            - session: Trading session status
            - ext: Market-specific extension data

        Raises
        ------
        ValueError
            If neither or both of `symbols` and `exchange` are provided.
        """
        base_url = self._client.base_url
        default_headers = self._client._build_headers()

        if (symbols is None) == (exchange is None):
            raise ValueError(
                "Must provide either 'symbols' or 'exchange', but not both"
            )
        if symbols is not None:
            if isinstance(symbols, str):
                symbols_list = [s.strip() for s in symbols.split(",")]
            else:
                symbols_list = symbols
            quotes_url = urljoin(base_url, "api/getData/realtime/stockData")
            results, msg = run(default_headers, quotes_url, symbols_list)
            if msg != "成功":
                return msg
        else:
            if isinstance(exchange, list):
                exchange_str = ",".join(exchange)
            else:
                exchange_str = exchange
            rsp_data = self._client.post(
                "/getData/realtime/stockDataList", json={"exchange": exchange_str}
            )
            respCode = rsp_data.get("respCode")
            if respCode != "0000":
                return rsp_data.get("respMsg")
            results = rsp_data.get("data")
            if not results:
                if rsp_data.get("error"):
                    return rsp_data.get("error")
                else:
                    return "请求失败，请检查传入参数"
        if as_df:
            return _quotes_to_df(results)
        return results

    def export_stock_list(self, market):
        if isinstance(market, str):
            market_list = [s.strip() for s in market.split(",")]
        else:
            market_list = market
        stock_list_obj = Universes(self._client).get(market_sign=market_list, fields="ts_code")
        return [_["ts_code"] for _ in stock_list_obj]

    def realtime_common(self, symbols: Union[List[str], str], endpoint: str, as_df: bool = False):
        base_url = self._client.base_url
        default_headers = self._client._build_headers()
        if isinstance(symbols, str):
            symbols_list = [s.strip() for s in symbols.split(",")]
        else:
            symbols_list = symbols
        quotes_url = urljoin(base_url, endpoint)
        results, msg = run(default_headers, quotes_url, symbols_list)
        if msg != "成功":
            return msg
        if as_df:
            return pd.DataFrame(results)
        return results

    def stock_fund_flow(self, symbols: Union[List[str], str], as_df: bool = False):
        """
        获取个股实时资金流向
        Parameters
        ----------
        symbols
        as_df

        Returns
        -------

        """
        func_name = inspect.currentframe().f_code.co_name
        endpoint = QUOTE_REALTIME_ENDPOINT_MAP[func_name]
        return self.realtime_common(symbols, endpoint, as_df)

    def stock_deep_quote(self, symbols: Union[List[str], str], as_df: bool = False):
        """
        获取个股实时资金流向
        Parameters
        ----------
        symbols
        as_df

        Returns
        -------

        """
        func_name = inspect.currentframe().f_code.co_name
        endpoint = QUOTE_REALTIME_ENDPOINT_MAP[func_name]
        return self.realtime_common(symbols, endpoint, as_df)


    def fetch_one_stock_realtime_data(self, ts_code: str):
        return self._client.post(
                    "/getData/realtime/stockData", json={"stockCode": ts_code}
                )

    def gevent_fetch(self, symbols: Union[List[str], str, None] = None) -> List[Dict[str, str]]:
        if Pool is None:
            raise ImportError(
                "gevent is not installed. Run: pip install sharetop[gevent]"
            )
        if isinstance(symbols, str):
            symbols_list = [s.strip() for s in symbols.split(",")]
        else:
            symbols_list = symbols

        total = len(symbols_list)
        pool = Pool(total)
        results = []
        for data in pool.imap_unordered(lambda sym: self.fetch_one_stock_realtime_data(sym), symbols_list):
            if data is not None:
                in_data = data["data"]
                results.append(in_data)
        return results
