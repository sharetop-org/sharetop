"""Financial data resources for ShareTop API."""

from __future__ import annotations
import inspect
import pandas as pd
from typing import Any, Dict, List, Union
from ..aio_utils.aio_quotes import run
from .._types import NOT_GIVEN, NotGiven
from ..utils import instrument_iso_datetime_to_local
from ._base import SyncResource


MAX_FINANCIAL_SYMBOLS = 100

_STMT_ENDPOINTS = {
    "income": "/getData/static/getStockIncomeStatement",
    "balance_sheet": "/getData/static/getStockBalanceSheet",
    "cash_flow": "/getData/static/getStockCashFlowStatement",
    "performance_forecast": "/getData/static/getStockPerformanceForecast",
    "report_appointment": "/getData/static/getStockReportAppointment",
    "core_quarter_indicators": "/getData/static/getStockQuarterIndicators",
    "core_financial_indicators": "/getData/static/getStockFinancialIndicators",
    "stock_dividend": "/getData/static/getStockDividend",
    "stock_factor": "/getData/static/getStockFactorInfo"
}


# Known datetime fields that need conversion
DATETIME_FIELDS = {
    "notice_date",
    "report_date",
    "announce_date",
    "end_date",
    "start_date",
    "operate_time",
    "create_time",
    "update_time",
    "first_appoint_date",
    "actual_publish_date",
    "appoint_publish_date",
    "second_change_date",
    "third_change_date"
}


def _convert_datetime_fields(data: Union[Dict[str, List[dict]], List[dict]]) -> Union[
    Dict[str, List[dict]], List[dict]]:
    """Convert datetime fields to local time for the given data.

    Parameters
    ----------
    data : dict or list
        Financial data, either dict keyed by symbol or list of records.

    Returns
    -------
    dict or list
        Data with datetime fields converted to local time.
    """
    if isinstance(data, list):
        # Handle list response
        if not data:
            return data
        # Check if it's a list of lists (batched) or single list
        if data and isinstance(data[0], list):
            # List of lists - convert each inner list
            converted = []
            for records in data:
                if not records:
                    converted.append(records)
                    continue
                ts_code = records[0].get("ts_code", "")
                converted.append([
                    _convert_record_datetime(r, ts_code) for r in records
                ])
            return converted
        else:
            # Single list - need ts_code from records
            ts_code = data[0].get("ts_code", "") if data else ""
            return [_convert_record_datetime(r, ts_code) for r in data]

    # Handle dict response
    result = {}
    for symbol, records in data.items():
        if not records:
            result[symbol] = records
            continue
        ts_code = records[0].get("ts_code", "") if isinstance(records, list) else symbol
        result[symbol] = [
            _convert_record_datetime(r, ts_code) for r in records
        ]
    return result


def _convert_record_datetime(record: dict, ts_code: str) -> dict:
    """Convert datetime fields in a single record to local time."""
    result = dict(record)
    for field in DATETIME_FIELDS:
        if field in result:
            value = result[field]
            if value and isinstance(value, str):
                result[field] = instrument_iso_datetime_to_local(value, ts_code)
    return result


def _batch_financials_df(data: Any) -> Dict[str, "pd.DataFrame"]:
    """Convert list of symbol data lists or dict to a dict of DataFrames.

    Parameters
    ----------
    data : list of list of dict or dict
        List where each element is a list of records for one symbol, or dict keyed by symbol.
        Example: [[{ts_code: '920211.BJ', ...}, ...], [{ts_code: '603435.SH', ...}, ...]]
        Or: {'920211.BJ': [...], '603435.SH': [...]}

    Returns
    -------
    dict of pd.DataFrame
        Dict mapping symbol to its DataFrame.
        Example: {'920211.BJ': df1, '603435.SH': df2}
    """

    result: Dict[str, "pd.DataFrame"] = {}

    # Handle dict format
    if isinstance(data, dict):
        for symbol, symbol_records in data.items():
            if not symbol_records:
                continue
            # Create DataFrame
            df = pd.DataFrame(symbol_records)
            # Convert datetime fields to local time
            for col in df.columns:
                if col in DATETIME_FIELDS:
                    df[col] = df[col].apply(
                        lambda x: instrument_iso_datetime_to_local(x, symbol)
                        if pd.notna(x) and isinstance(x, str)
                        else x
                    )
            result[symbol] = df
        return result

    # Handle list format
    for symbol_records in data:
        if not symbol_records:
            continue

        # Get symbol from first record
        ts_code = symbol_records[0].get("ts_code", "")
        if not ts_code:
            continue

        # Create DataFrame
        df = pd.DataFrame(symbol_records)

        # Convert datetime fields to local time
        for col in df.columns:
            if col in DATETIME_FIELDS:
                df[col] = df[col].apply(
                    lambda x: instrument_iso_datetime_to_local(x, ts_code)
                    if pd.notna(x) and isinstance(x, str)
                    else x
                )

        result[ts_code] = df

    return result


def _list_to_dataframe(data: Any) -> "pd.DataFrame":
    """Convert list of symbol data lists to a single DataFrame.

    Used when symbols is empty, returns a single DataFrame instead of Dict.

    Parameters
    ----------
    data : list of list of dict
        List where each element is a list of records for one symbol.

    Returns
    -------
    pd.DataFrame
        Single DataFrame with all records.
    """
    import pandas as pd

    # Flatten all records into one list
    all_records = []
    for symbol_records in data:
        if not symbol_records:
            continue
        all_records.extend(symbol_records)

    if not all_records:
        return pd.DataFrame()

    # Create DataFrame
    df = pd.DataFrame(all_records)

    # Get ts_code from first record to determine timezone for conversion
    # (datetime fields should already be converted by _convert_datetime_fields)

    return df


class Financials(SyncResource):
    """Synchronous interface for financial data endpoints.

    Supports four statement types: income, balance_sheet, cash_flow.
    """

    def _query(
            self,
            endpoint: str,
            symbols: List[str],
            start_date: Union[str, None, NotGiven],
            end_date: Union[str, None, NotGiven],
            fields: Union[str, None, NotGiven] = NOT_GIVEN,
            report_class: Union[str, None, NotGiven] = NOT_GIVEN,
            report_type: Union[str, None, NotGiven] = NOT_GIVEN,
            as_df: bool = False
    ) -> Any:
        params: Dict[str, Any] = {}
        if not isinstance(start_date, NotGiven) and start_date is not None:
            params["start_date"] = start_date
        if not isinstance(end_date, NotGiven) and end_date is not None:
            params["end_date"] = end_date
        if not isinstance(fields, NotGiven) and fields is not None:
            params["fields"] = fields
        if not isinstance(report_type, NotGiven) and report_type is not None:
            params["report_type"] = report_type
        if not isinstance(report_class, NotGiven) and report_class is not None:
            params["report_class"] = report_class

        base_url = self._client.base_url
        default_headers = self._client._build_headers()
        quotes_url = f"{base_url}{endpoint}"

        results, msg = run(
            default_headers,
            quotes_url,
            ts_code_list=symbols,
            payload=params,
            max_concurrent=100,
        )

        if msg != "成功":
            return msg

        # Convert datetime fields to local time
        if results:
            results = _convert_datetime_fields(results)

        if as_df and results:
            # When symbols is empty, return a single DataFrame
            if not symbols:
                return _list_to_dataframe(results)
            # When symbols is provided, return Dict[str, DataFrame]
            return _batch_financials_df(results)

        return results

    def stock_dividend(self,
                       symbols: List[str],
                       *,
                       fields: Union[str, None, NotGiven] = NOT_GIVEN,
                       as_df: bool = False,
                       ) -> Union[Dict[str, List[dict]], "pd.DataFrame"]:
        """
        股票分红派息
        Parameters
        ----------
        symbols
        fields
        as_df

        Returns
        -------

        """
        func_name = inspect.currentframe().f_code.co_name
        return self._query(
            _STMT_ENDPOINTS[func_name],
            symbols if symbols else [],
            NOT_GIVEN,
            NOT_GIVEN,
            fields,
            NOT_GIVEN,
            NOT_GIVEN,
            as_df
        )

    def stock_factor(self,
                       symbols: List[str],
                       *,
                       as_df: bool = False,
                       ) -> Union[Dict[str, List[dict]], "pd.DataFrame"]:
        """
        股票分红派息
        Parameters
        ----------
        symbols
        as_df

        Returns
        -------

        """
        func_name = inspect.currentframe().f_code.co_name
        return self._query(
            _STMT_ENDPOINTS[func_name],
            symbols if symbols else [],
            NOT_GIVEN,
            NOT_GIVEN,
            NOT_GIVEN,
            NOT_GIVEN,
            NOT_GIVEN,
            as_df
        )

    def income(
            self,
            symbols: List[str],
            *,
            start_date: Union[str, None, NotGiven] = NOT_GIVEN,
            end_date: Union[str, None, NotGiven] = NOT_GIVEN,
            report_class: Union[str, None, NotGiven] = NOT_GIVEN,
            report_type: Union[str, None, NotGiven] = NOT_GIVEN,
            fields: Union[str, None, NotGiven] = NOT_GIVEN,
            as_df: bool = False,
    ) -> Union[Dict[str, List[dict]], "pd.DataFrame"]:
        """Get performance forecast data (业绩预告).

        Parameters
        ----------
        report_class
        report_type
        as_df
        symbols : list of str, optional
            Symbol codes (e.g., ["600519.SH"]). If None, returns all stocks.
        start_date : str, optional
            Filter: notice_date >= start_date (YYYY-MM-DD).
        end_date : str, optional
            Filter: notice_date <= end_date (YYYY-MM-DD).
        fields : str, optional
            Output fields to return, separated by commas.
            Available fields: ts_code, name, code, notice_date, report_date,
            predict_amt_lower, predict_amt_upper, add_amp_lower, add_amp_upper,
            change_reason_explain, predict_type, preyear_same_period,
            increase_jz, forecast_jz, is_latest, predict_ratio_lower, predict_ratio_upper.

        Returns
        -------
        dict or DataFrame
            Performance forecast data keyed by symbol.
        """
        func_name = inspect.currentframe().f_code.co_name
        return self._query(
            _STMT_ENDPOINTS[func_name],
            symbols if symbols else [],
            start_date,
            end_date,
            fields,
            report_class,
            report_type,
            as_df
        )

    def cash_flow(
            self,
            symbols: List[str],
            *,
            start_date: Union[str, None, NotGiven] = NOT_GIVEN,
            end_date: Union[str, None, NotGiven] = NOT_GIVEN,
            report_class: Union[str, None, NotGiven] = NOT_GIVEN,
            report_type: Union[str, None, NotGiven] = NOT_GIVEN,
            fields: Union[str, None, NotGiven] = NOT_GIVEN,
            as_df: bool = False,
    ) -> Union[Dict[str, List[dict]], "pd.DataFrame"]:
        """Get performance forecast data (业绩预告).

        Parameters
        ----------
        report_class
        report_type
        as_df
        symbols : list of str, optional
            Symbol codes (e.g., ["600519.SH"]). If None, returns all stocks.
        start_date : str, optional
            Filter: notice_date >= start_date (YYYY-MM-DD).
        end_date : str, optional
            Filter: notice_date <= end_date (YYYY-MM-DD).
        fields : str, optional
            Output fields to return, separated by commas.
            Available fields: ts_code, name, code, notice_date, report_date,
            predict_amt_lower, predict_amt_upper, add_amp_lower, add_amp_upper,
            change_reason_explain, predict_type, preyear_same_period,
            increase_jz, forecast_jz, is_latest, predict_ratio_lower, predict_ratio_upper.

        Returns
        -------
        dict or DataFrame
            Performance forecast data keyed by symbol.
        """
        func_name = inspect.currentframe().f_code.co_name
        return self._query(
            _STMT_ENDPOINTS[func_name],
            symbols if symbols else [],
            start_date,
            end_date,
            fields,
            report_class,
            report_type,
            as_df
        )

    def balance_sheet(
            self,
            symbols: List[str],
            *,
            start_date: Union[str, None, NotGiven] = NOT_GIVEN,
            end_date: Union[str, None, NotGiven] = NOT_GIVEN,
            report_type: Union[str, None, NotGiven] = NOT_GIVEN,
            fields: Union[str, None, NotGiven] = NOT_GIVEN,
            as_df: bool = False,
    ) -> Union[Dict[str, List[dict]], "pd.DataFrame"]:
        """Get performance forecast data (业绩预告).

        Parameters
        ----------
        report_type
        as_df
        symbols : list of str, optional
            Symbol codes (e.g., ["600519.SH"]). If None, returns all stocks.
        start_date : str, optional
            Filter: notice_date >= start_date (YYYY-MM-DD).
        end_date : str, optional
            Filter: notice_date <= end_date (YYYY-MM-DD).
        fields : str, optional
            Output fields to return, separated by commas.
            Available fields: ts_code, name, code, notice_date, report_date,
            predict_amt_lower, predict_amt_upper, add_amp_lower, add_amp_upper,
            change_reason_explain, predict_type, preyear_same_period,
            increase_jz, forecast_jz, is_latest, predict_ratio_lower, predict_ratio_upper.

        Returns
        -------
        dict or DataFrame
            Performance forecast data keyed by symbol.
        """
        func_name = inspect.currentframe().f_code.co_name
        return self._query(
            _STMT_ENDPOINTS[func_name],
            symbols if symbols else [],
            start_date,
            end_date,
            fields,
            NOT_GIVEN,
            report_type,
            as_df
        )

    def core_financial_indicators(
            self,
            symbols: List[str],
            *,
            start_date: Union[str, None, NotGiven] = NOT_GIVEN,
            end_date: Union[str, None, NotGiven] = NOT_GIVEN,
            report_type: Union[str, None, NotGiven] = NOT_GIVEN,
            fields: Union[str, None, NotGiven] = NOT_GIVEN,
            as_df: bool = False,
    ) -> Union[Dict[str, List[dict]], "pd.DataFrame"]:
        """Get performance forecast data (业绩预告).

        Parameters
        ----------
        report_type
        as_df
        symbols : list of str, optional
            Symbol codes (e.g., ["600519.SH"]). If None, returns all stocks.
        start_date : str, optional
            Filter: notice_date >= start_date (YYYY-MM-DD).
        end_date : str, optional
            Filter: notice_date <= end_date (YYYY-MM-DD).
        fields : str, optional
            Output fields to return, separated by commas.
            Available fields: ts_code, name, code, notice_date, report_date,
            predict_amt_lower, predict_amt_upper, add_amp_lower, add_amp_upper,
            change_reason_explain, predict_type, preyear_same_period,
            increase_jz, forecast_jz, is_latest, predict_ratio_lower, predict_ratio_upper.

        Returns
        -------
        dict or DataFrame
            Performance forecast data keyed by symbol.
        """
        func_name = inspect.currentframe().f_code.co_name
        return self._query(
            _STMT_ENDPOINTS[func_name],
            symbols if symbols else [],
            start_date,
            end_date,
            fields,
            NOT_GIVEN,
            report_type,
            as_df
        )

    def core_quarter_indicators(
            self,
            symbols: List[str],
            *,
            start_date: Union[str, None, NotGiven] = NOT_GIVEN,
            end_date: Union[str, None, NotGiven] = NOT_GIVEN,
            report_type: Union[str, None, NotGiven] = NOT_GIVEN,
            fields: Union[str, None, NotGiven] = NOT_GIVEN,
            as_df: bool = False,
    ) -> Union[Dict[str, List[dict]], "pd.DataFrame"]:
        """Get performance forecast data (业绩预告).

        Parameters
        ----------
        report_type
        as_df
        symbols : list of str, optional
            Symbol codes (e.g., ["600519.SH"]). If None, returns all stocks.
        start_date : str, optional
            Filter: notice_date >= start_date (YYYY-MM-DD).
        end_date : str, optional
            Filter: notice_date <= end_date (YYYY-MM-DD).
        fields : str, optional
            Output fields to return, separated by commas.
            Available fields: ts_code, name, code, notice_date, report_date,
            predict_amt_lower, predict_amt_upper, add_amp_lower, add_amp_upper,
            change_reason_explain, predict_type, preyear_same_period,
            increase_jz, forecast_jz, is_latest, predict_ratio_lower, predict_ratio_upper.

        Returns
        -------
        dict or DataFrame
            Performance forecast data keyed by symbol.
        """
        func_name = inspect.currentframe().f_code.co_name
        return self._query(
            _STMT_ENDPOINTS[func_name],
            symbols if symbols else [],
            start_date,
            end_date,
            fields,
            NOT_GIVEN,
            report_type,
            as_df
        )

    def report_appointment(
            self,
            symbols: List[str] = None,
            *,
            start_date: Union[str, None, NotGiven] = NOT_GIVEN,
            end_date: Union[str, None, NotGiven] = NOT_GIVEN,
            fields: Union[str, None, NotGiven] = NOT_GIVEN,
            as_df: bool = False,
    ) -> Union[Dict[str, List[dict]], "pd.DataFrame"]:
        """Get performance forecast data (业绩预告).

        Parameters
        ----------
        as_df
        symbols : list of str, optional
            Symbol codes (e.g., ["600519.SH"]). If None, returns all stocks.
        start_date : str, optional
            Filter: notice_date >= start_date (YYYY-MM-DD).
        end_date : str, optional
            Filter: notice_date <= end_date (YYYY-MM-DD).
        fields : str, optional
            Output fields to return, separated by commas.
            Available fields: ts_code, name, code, notice_date, report_date,
            predict_amt_lower, predict_amt_upper, add_amp_lower, add_amp_upper,
            change_reason_explain, predict_type, preyear_same_period,
            increase_jz, forecast_jz, is_latest, predict_ratio_lower, predict_ratio_upper.

        Returns
        -------
        dict or DataFrame
            Performance forecast data keyed by symbol.
        """
        func_name = inspect.currentframe().f_code.co_name
        return self._query(
            _STMT_ENDPOINTS[func_name],
            symbols if symbols else [],
            start_date,
            end_date,
            NOT_GIVEN,
            NOT_GIVEN,
            fields,
            as_df
        )

    def performance_forecast(
            self,
            symbols: List[str] = None,
            *,
            start_date: Union[str, None, NotGiven] = NOT_GIVEN,
            end_date: Union[str, None, NotGiven] = NOT_GIVEN,
            fields: Union[str, None, NotGiven] = NOT_GIVEN,
            as_df: bool = False,
    ) -> Union[Dict[str, List[dict]], "pd.DataFrame"]:
        """Get performance forecast data (业绩预告).

        Parameters
        ----------
        as_df
        symbols : list of str, optional
            Symbol codes (e.g., ["600519.SH"]). If None, returns all stocks.
        start_date : str, optional
            Filter: notice_date >= start_date (YYYY-MM-DD).
        end_date : str, optional
            Filter: notice_date <= end_date (YYYY-MM-DD).
        fields : str, optional
            Output fields to return, separated by commas.
            Available fields: ts_code, name, code, notice_date, report_date,
            predict_amt_lower, predict_amt_upper, add_amp_lower, add_amp_upper,
            change_reason_explain, predict_type, preyear_same_period,
            increase_jz, forecast_jz, is_latest, predict_ratio_lower, predict_ratio_upper.

        Returns
        -------
        dict or DataFrame
            Performance forecast data keyed by symbol.
        """
        func_name = inspect.currentframe().f_code.co_name
        return self._query(
            _STMT_ENDPOINTS[func_name],
            symbols if symbols else [],
            start_date,
            end_date,
            NOT_GIVEN,
            NOT_GIVEN,
            fields,
            as_df
        )
