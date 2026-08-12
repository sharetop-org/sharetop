import asyncio
from typing import Any, Dict, List, Optional, Union

import aiohttp
from aiohttp import ClientTimeout, TCPConnector


DEFAULT_TIMEOUT = 20  # 默认超时时间（秒）


def _create_session(timeout=None):
    """创建一个配置好的 ClientSession，跳过 SSL 验证以兼容自签名/证书不匹配的服务器"""
    connector = TCPConnector(ssl=False)
    return aiohttp.ClientSession(timeout=timeout, connector=connector)


async def fetch_single_request(
    session: aiohttp.ClientSession,
    headers: Dict[str, str],
    quotes_url: str,
    payload: Dict[str, Any],
    timeout: Optional[ClientTimeout] = None,
):
    """直接使用 payload 请求 quotes_url，适用于无 ts_code_list 的情况"""
    try:
        async with session.post(quotes_url, json=payload, headers=headers, timeout=timeout) as resp:
            result = await resp.json(content_type=None)
            if resp.status == 200:
                return {
                    "status": "success",
                    "http_status": resp.status,
                    "rsp_data": result,
                    "data": result.get("data")
                }
            else:
                return {
                    "status": "failed",
                    "http_status": resp.status,
                    "error": f"HTTP {resp.status}",
                    "rsp_data": result,
                    "data": None
                }
    except asyncio.TimeoutError:
        return {"status": "failed", "error": "请求超时", "data": None}
    except aiohttp.ClientError as e:
        return {"status": "failed", "error": f"网络错误: {str(e)}", "data": None}
    except Exception as e:
        return {"status": "failed", "error": f"未知错误: {str(e)}", "data": None}


async def fetch_ts_code_list(
    session: aiohttp.ClientSession,
    headers: Dict[str, str],
    payload: Dict[str, Any],
    stock_list_url: str,
    timeout: Optional[ClientTimeout] = None,
):
    """异步获取股票代码列表"""
    try:
        async with session.post(stock_list_url, json=payload, headers=headers, timeout=timeout) as resp:
            result = await resp.json(content_type=None)
            if resp.status == 200 and "data" in result:
                data = result["data"]
                ts_code_list = [item["ts_code"] for item in data]
                print(f"成功获取 {len(ts_code_list)} 个股票代码")
                return ts_code_list
            else:
                print(f"获取股票列表失败，HTTP状态码: {resp.status}, 返回内容: {result}")
                return []
    except Exception as e:
        print(f"获取股票列表时发生异常: {e}")
        return []


async def fetch_one(
    session: aiohttp.ClientSession,
    ts_code: str,
    headers: Dict[str, str],
    quotes_url: str,
    params: Optional[Dict[str, Any]] = None,
    timeout: Optional[ClientTimeout] = None,
):
    """异步请求单个 tsCode 的数据"""
    payload = {"ts_code": ts_code}
    if params:
        payload.update(params)
    try:
        async with session.post(quotes_url, json=payload, headers=headers, timeout=timeout) as resp:
            result = await resp.json(content_type=None)
            if resp.status == 200:
                data = {
                    "tsCode": ts_code,
                    "status": "success",
                    "http_status": resp.status,
                    "rsp_data": result
                }
            else:
                data = {
                    "tsCode": ts_code,
                    "status": "failed",
                    "http_status": resp.status,
                    "error": f"HTTP {resp.status}",
                    "rsp_data": result
                }
            return data
    except asyncio.TimeoutError:
        return {"tsCode": ts_code, "status": "failed", "error": "请求超时"}
    except aiohttp.ClientError as e:
        return {"tsCode": ts_code, "status": "failed", "error": f"网络错误: {str(e)}"}
    except Exception as e:
        return {"tsCode": ts_code, "status": "failed", "error": f"未知错误: {str(e)}"}


async def fetch_all_with_semaphore(
    ts_codes: List[str],
    max_concurrent: int,
    headers: Dict[str, str],
    quotes_url: str,
    kline_params: Dict[str, Any],
    timeout: Optional[ClientTimeout] = None,
):
    """使用信号量控制并发数"""
    semaphore = asyncio.Semaphore(max_concurrent)

    async def fetch_with_limit(session: aiohttp.ClientSession, code: str, params: Dict[str, Any]):
        async with semaphore:
            return await fetch_one(session, code, headers, quotes_url, params, timeout)

    async with _create_session(timeout=timeout) as session:
        tasks = [fetch_with_limit(session, code, kline_params) for code in ts_codes]
        results = await asyncio.gather(*tasks, return_exceptions=True)
        final_results = []
        for result in results:
            if isinstance(result, Exception):
                final_results.append({"status": "failed", "error": f"任务异常: {str(result)}"})
            else:
                final_results.append(result)
        return final_results


async def main(
    headers: Dict[str, str],
    ts_code_list: List[str],
    payload: Dict[str, Any],
    stock_list_url: Optional[str],
    quotes_url: str,
    kline_params: Dict[str, Any],
    max_concurrent: int = 2000,
    timeout: float = DEFAULT_TIMEOUT,
):
    """主函数"""
    # 创建超时配置
    client_timeout = ClientTimeout(total=timeout)

    # 当没有 ts_code_list 时，优先使用 payload 直接请求
    if not ts_code_list and not stock_list_url:
        async with _create_session(timeout=client_timeout) as session:
            result = await fetch_single_request(session, headers, quotes_url, payload, client_timeout)
            if result.get("status") == "success":
                data = result.get("data")
                rsp_data = result['rsp_data']
                respCode = rsp_data.get("respCode")
                msg = rsp_data.get("respMsg")
                if respCode == "0000":
                    success_dict_results = [data] if data is not None else []
                    return success_dict_results, msg
                else:
                    return [], msg
            else:
                msg = result['rsp_data'].get("respMsg")
                return [], msg

    if not ts_code_list and payload and stock_list_url:
        # 先获取股票代码列表
        async with _create_session(timeout=client_timeout) as session:
            ts_code_list = await fetch_ts_code_list(session, headers, payload, stock_list_url, client_timeout)

    if not ts_code_list:
        return [], "未获取到任何股票代码"

    if len(ts_code_list) <= max_concurrent:
        max_concurrent = len(ts_code_list)

    last_params = kline_params if kline_params else payload
    results = await fetch_all_with_semaphore(
        ts_code_list,
        max_concurrent,
        headers,
        quotes_url,
        last_params,
        client_timeout,
    )

    success_results = [_["rsp_data"]["data"] for _ in results if _.get('status') == 'success' and _["rsp_data"].get("data")]
    failed_count = len(results) - len(success_results)
    if failed_count > 0:
        rsp_data = results[0]["rsp_data"]
        msg = rsp_data.get("respMsg")
        return success_results, msg

    return success_results, "成功"


def run(
    headers: Dict[str, str],
    quotes_url: str,
    ts_code_list: Union[List[str], None] = None,
    stock_list_url: Optional[str] = None,
    payload: Optional[Dict[str, Any]] = None,
    kline_params: Optional[Dict[str, Any]] = None,
    max_concurrent: int = 2000,
    timeout: float = DEFAULT_TIMEOUT,
):
    """同步入口，运行异步主函数

    Parameters
    ----------
    headers : dict
        请求头，包含 Authorization 等信息。
    quotes_url : str
        行情数据接口 URL。
    ts_code_list : list, optional
        股票代码列表。如果为 None 或空，将根据其他参数决定请求方式。
    stock_list_url : str, optional
        股票列表接口 URL（当 ts_code_list 为空时使用）。
    payload : dict, optional
        请求参数。
    kline_params : dict, optional
        K线参数。
    max_concurrent : int, optional
        最大并发数，默认 2000。
    timeout : float, optional
        请求超时时间（秒），默认 10 秒。

    Returns
    -------
    tuple
        (成功结果列表, 状态消息)
    """
    return asyncio.run(main(
        headers,
        ts_code_list if ts_code_list else [],
        payload if payload else {},
        stock_list_url,
        quotes_url,
        kline_params if kline_params else {},
        max_concurrent,
        timeout,
    ))
