# ShareTop Python SDK

[![Python Version](https://img.shields.io/badge/python-3.9+-blue.svg?style=flat)](https://pypi.org/project/sharetop/)
[![PyPI Package](https://img.shields.io/pypi/v/sharetop.svg?maxAge=60)](https://pypi.org/project/sharetop/)
[![PyPI Downloads](https://img.shields.io/pypi/dm/sharetop.svg?maxAge=2592000&label=downloads&color=%2327B1FF)](https://pypi.org/project/sharetop/)
[![Docs](https://img.shields.io/badge/docs-docs.sharetop.org-blue)](https://sharetop.top)
[![GitHub Stars](https://img.shields.io/github/stars/sharetop-org/sharetop.svg?style=social&label=Star&maxAge=60)](https://github.com/sharetop-org/sharetop)
[![License](https://img.shields.io/badge/license-MIT-green.svg)](LICENSE)


凡是数据皆有价值，前提是要放到正确位置，同时在正确的时间被使用。

ShareTop 是一个开源数据社区，主要为个人及科研团队在金融、宏观、汽车、石油等领域的科学研究提供数据清洗、结构化的API接口服务，它不以盈利为主要目的，不做任何荐股或者提供投资方向。

ShareTop Python SDK 是 ShareTop 数据长期维护的 Python 客户端，提供 金融、宏观、汽车等相关行业存量和增量数据。

“数据仅供参考，不构成投资建议”

> **完整文档**：<https://sharetop.top>

---

## 安装

使用 pip 安装 ShareTop Python SDK：

```bash
pip install sharetop --upgrade
```

SDK 支持 Python 3.9+，推荐使用 Python 3.10 或更高版本。

---

## 获取token


### 关注公众号“浔溯de小仓鼠”并点击获取token

<img src="img/scan.png" alt="微信公众号二维码" width="300">


## 初始化客户端

### 免费服务

如果你只需要日K线数据和股票基础信息，可以直接使用免费服务：

```python
from sharetop import ShareTop

# 从微信公众号里面获取token
token = ""

client = ShareTop(token=token)

# 查询日K线数据
symbol = "601717.SH"

df = client.klines.get_history_data(symbol=symbol, count=500000, period="d", adjust="before", as_df=True)
print(df)
```

**免费服务特点：**
- ✅ 关注微信公众号，获取token，直接使用
- ✅ 提供历史日K线数据（d、w、m、q、y）
- ✅ 提供标的信息、交易所、标的池查询
- ❌ 不提供实时行情
- ❌ 不提供分钟级K线（1m、5m、15m、30m、60m、120m）
- ⚠️ 日K数据为历史数据，盘中不会实时更新

如果你需要实时行情、盘中实时更新的K线或更高频率访问，请使用完整服务。

---

### 完整服务

```python
from sharetop import ShareTop

# 从微信公众号里面获取token
token = ""

client = ShareTop(token=token)

# 获取沪深 A 股实时行情
df = client.quotes.get(symbols="600000.SH,002522.SZ,000006.SZ,688003.SH,002534.SZ", as_df=True)

print(df)
```

如果看到股票价格输出，说明 SDK 已配置成功！

**完整服务优势：**
- ✅ 实时行情数据
- ✅ 分钟级K线（5m、15m、30m、60m、120m）
- ✅ 日内分时数据
- ✅ 财报数据
- ✅ 更高的调用频率
- ✅ 打板专题数据

---

## 标的代码格式与支持市场

所有按标的查询的接口（行情、K 线等）均使用**统一标的代码**，格式为：**`代码.市场后缀`**（中间为英文点号）。

### 标的代码格式

- 格式：`代码.市场后缀`
- 示例：
  - 股票：`600000.SH`（浦发银行）、`000001.SZ`（平安银行）、`920662.BJ`（方盛股份）

代码部分使用交易所官方代码（如 6 位 A 股代码、合约代码等），**市场后缀**见下表。

### 支持的市场（后缀）

| 后缀 | 市场 | 说明 |
|------|------|------|
| **SH** | 上海证券交易所 | 沪市 A 股、ETF、债券等 |
| **SZ** | 深圳证券交易所 | 深市 A 股、创业板、ETF 等 |
| **BJ** | 北京证券交易所 | 北交所股票 |

### 目前支持状态

- **A 股（SH / SZ / BJ）**：已支持。可查实时行情、日 K、分钟 K、日内分时、财务数据等。

按标的查询时传入上述格式的字符串或列表即可：

```python
from sharetop import ShareTop

token = ""

client = ShareTop(token=token)

# 上交所整体实时数据
df = client.quotes.get(exchange=["SSE"], as_df=True)

print(df)
```

---

## 基础用法

### K 线获取

**单个或者批量获取分钟k线**：

```python
from sharetop import ShareTop

token = ""

client = ShareTop(token=token)

symbols = ["601717.SH", "601928.SH"]

# 获取分钟 K 线，返回原始数据
kline_data = client.klines.get_batch_real_time(symbols=symbols, period="1m", count=5, adjust="before", as_df=True)
print(f"601717.SH最新的1min k线数据: {kline_data['601717.SH']}")

```

### 获取实时行情

**按标的代码查询**

```python
from sharetop import ShareTop

token = ""

client = ShareTop(token=token)

symbols = ["600000.SH", "002534.SZ", "688003.SH"]

df = client.quotes.get(symbols=symbols, as_df=True)

print(df)
```

**按标的池查询**

```python
# 获取全部 上交所 A 股行情
quotes_a = client.quotes.get(exchange=["SSE"], as_df=True)

print(quotes_a)


# 获取全部 上交所 深交所 A 股行情
quotes = client.quotes.get(exchange=["SSE", "SZSE"], as_df=True)

print(quotes)

```

### 获取打板数据

**炸板池查询**

```python

from sharetop import ShareTop

token = ""

client = ShareTop(token=token)

# 获取实时炸板池数据
df = client.limit_up.limit_up_down_pool.broken_limit(as_df=True)

print(df)

```

**强势股池查询**

```python

from sharetop import ShareTop

token = ""

client = ShareTop(token=token)

# 获取实时强势股池数据
df = client.limit_up.limit_up_down_pool.strong(as_df=True)

print(df)

```

---

## License

MIT
