"""Common utilities for limit up resources."""

from __future__ import annotations

from typing import Any, Dict, Union
import datetime
import pandas as pd

from ..._types import NOT_GIVEN, NotGiven
from ...aio_utils.aio_quotes import run


def _build_params(
    start_date: Union[str, None, NotGiven] = NOT_GIVEN,
    end_date: Union[str, None, NotGiven] = NOT_GIVEN,
    fields: Union[str, None, NotGiven] = NOT_GIVEN,
    **kwargs: Any,
) -> Dict[str, Any]:
    """Build request parameters from keyword arguments.

    Parameters
    ----------
    start_date : str, optional
        Start date filter.
    end_date : str, optional
        End date filter.
    fields : str, optional
        Fields to return.
    **kwargs : Any
        Additional parameters.

    Returns
    -------
    dict
        Built parameters dict.
    """
    params: Dict[str, Any] = {}

    if not isinstance(start_date, NotGiven) and start_date is not None:
        params["start_date"] = start_date
    if not isinstance(end_date, NotGiven) and end_date is not None:
        params["end_date"] = end_date
    if not isinstance(fields, NotGiven) and fields is not None:
        params["fields"] = fields

    # Add additional kwargs
    for key, value in kwargs.items():
        if not isinstance(value, NotGiven) and value is not None:
            params[key] = value

    return params


def _build_url(client: Any, endpoint: str) -> str:
    """Build full URL from endpoint."""
    return f"{client.base_url}{endpoint}"


def _convert_to_dataframe(results: Any) -> "pd.DataFrame":
    """Convert API results to DataFrame.

    Handles both list and dict formats, flattens nested lists.
    """

    if not results:
        return pd.DataFrame()

    if isinstance(results, list):
        flat_results = []
        for item in results:
            if isinstance(item, list):
                flat_results.extend(item)
            elif isinstance(item, dict):
                flat_results.append(item)
        return pd.DataFrame(flat_results)
    return pd.DataFrame(results)


def _execute_request(
    client: Any,
    endpoint: str,
    params: Dict[str, Any],
) -> Any:
    """Execute API request."""
    default_headers = client._build_headers()
    quotes_url = _build_url(client, endpoint)

    results, msg = run(
        default_headers,
        quotes_url,
        ts_code_list=[],
        payload=params,
        max_concurrent=100,
    )

    return results, msg


def request_data(
    client: Any,
    endpoint: str,
    start_date: Union[str, None, NotGiven] = NOT_GIVEN,
    end_date: Union[str, None, NotGiven] = NOT_GIVEN,
    fields: Union[str, None, NotGiven] = NOT_GIVEN,
    as_df: bool = False,
    **kwargs: Any,
) -> Union[list, "pd.DataFrame"]:
    """Execute API request with common parameters.

    This is the main helper function that combines all utilities.

    Parameters
    ----------
    client : SyncAPIClient
        API client instance.
    endpoint : str
        API endpoint path.
    start_date : str, optional
        Start date filter.
    end_date : str, optional
        End date filter.
    fields : str, optional
        Fields to return.
    as_df : bool
        Whether to return DataFrame.
    **kwargs : Any
        Additional parameters to pass to _build_params.

    Returns
    -------
    list or DataFrame
        API response data.
    """
    params = _build_params(
        start_date=start_date,
        end_date=end_date,
        fields=fields,
        **kwargs,
    )

    results, msg = _execute_request(client, endpoint, params)

    if msg != "成功":
        return msg

    if as_df:
        return _convert_to_dataframe(results)

    return results


def convert_to_dataframe_with_timestamp(
    results: Any,
    timestamp_column: str = "trade_date",
    time_column: str = "trade_time",
    timestamp_unit: str = "auto",
) -> "pd.DataFrame":
    """Convert API results to DataFrame with timestamp conversion to local time.

    Parameters
    ----------
    results : list
        List of data records from API response.
    timestamp_column : str, optional
        Column name containing timestamp. Default: "trade_date".
    time_column : str, optional
        Column name to store converted local time. Default: "trade_time".
    timestamp_unit : str, optional
        Timestamp unit. Options: "auto", "ms" (milliseconds), "s" (seconds).
        Default: "auto" - automatically determines based on timestamp value.

    Returns
    -------
    DataFrame
        DataFrame with converted local time column.
    """

    if not results:
        return pd.DataFrame()

    df = pd.DataFrame(results)
    if df.empty:
        return df

    # Convert timestamp to local datetime if timestamp column exists
    if timestamp_column in df.columns:
        def convert_timestamp(x):
            if not x:
                return None
            # Auto-detect: if timestamp > 10^10, it's in milliseconds
            if timestamp_unit == "auto":
                divisor = 1000 if x > 10**10 else 1
            elif timestamp_unit == "ms":
                divisor = 1000
            else:
                divisor = 1
            return datetime.datetime.fromtimestamp(x / divisor).strftime("%Y-%m-%d %H:%M:%S")

        df[time_column] = df[timestamp_column].apply(convert_timestamp)

    return df