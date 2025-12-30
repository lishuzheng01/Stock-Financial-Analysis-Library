# -*- coding: utf-8 -*-
"""
股票行情数据获取模块 - Stock Price Data Module
支持多数据源: akshare + yfinance
Supports multiple data sources: akshare + yfinance
"""

import akshare as ak
import pandas as pd


def _convert_stock_code(stock, target_source):
    """
    将股票代码转换为目标数据源格式
    Convert stock code to target data source format

    Args:
        stock: 股票代码 (原始格式)
        target_source: 目标数据源 ('akshare' or 'yfinance')

    Returns:
        str: 转换后的股票代码

    Examples:
        输入          AKShare      yfinance
        600519   ->  600519       600519.SS
        000858   ->  000858       000858.SZ
        0700.HK  ->  不支持       0700.HK
        AAPL     ->  不支持       AAPL
    """
    if target_source == 'yfinance':
        # 判断是否为A股代码 (6位纯数字)
        if stock.isdigit() and len(stock) == 6:
            # 上交所: 6开头 -> .SS
            if stock.startswith('6'):
                return f"{stock}.SS"
            # 深交所: 0/3开头 -> .SZ
            else:
                return f"{stock}.SZ"
        # 港股/美股直接返回
        return stock

    # akshare直接返回原代码
    return stock


def _normalize_stock_data(df, source_name):
    """
    标准化股票数据格式
    Normalize stock data format to unified standard

    统一输出标准:
    - Columns: ['open', 'high', 'low', 'close', 'volume']
    - Index: DatetimeIndex
    - Data type: float64

    Args:
        df: 原始DataFrame
        source_name: 数据源名称 ('akshare' or 'yfinance')

    Returns:
        pd.DataFrame: 标准化后的DataFrame
    """
    if df is None or df.empty:
        return pd.DataFrame()

    try:
        if source_name == 'yfinance':
            # yfinance列名: Open, High, Low, Close, Volume
            df = df.rename(columns={
                'Open': 'open',
                'High': 'high',
                'Low': 'low',
                'Close': 'close',
                'Volume': 'volume'
            })
        elif source_name == 'akshare':
            # akshare已在_get_stock_data_akshare中处理列名
            pass

        # 确保索引是DatetimeIndex
        if not isinstance(df.index, pd.DatetimeIndex):
            if 'date' in df.columns:
                df.index = pd.to_datetime(df['date'])
            else:
                df.index = pd.to_datetime(df.index)

        # 只保留需要的列
        required_cols = ['open', 'high', 'low', 'close', 'volume']
        available_cols = [col for col in required_cols if col in df.columns]

        if not available_cols:
            print(f"[数据标准化警告] 未找到必需的列,可用列: {df.columns.tolist()}")
            return pd.DataFrame()

        df = df[available_cols]

        # 转换数据类型为float
        df = df.astype(float)

        # 去除NaN
        df = df.dropna()

        return df

    except Exception as e:
        print(f"[数据标准化错误] {source_name}: {e}")
        return pd.DataFrame()


def _get_stock_data_akshare(stock, start, end):
    """
    使用AKShare获取股票数据
    Get stock data using AKShare

    Args:
        stock: 股票代码 (6位数字)
        start: 开始日期 (YYYYMMDD)
        end: 结束日期 (YYYYMMDD)

    Returns:
        pd.DataFrame: 标准化的股票数据
    """
    try:
        # 获取AKShare数据 (前复权)
        df = ak.stock_zh_a_hist(
            symbol=stock,
            period="daily",
            start_date=start,
            end_date=end,
            adjust="qfq"
        )

        if df is None or df.empty:
            return pd.DataFrame()

        # 列名映射
        rename_dict = {
            '日期': 'date',
            '开盘': 'open',
            '收盘': 'close',
            '最高': 'high',
            '最低': 'low',
            '成交量': 'volume',
            '成交额': 'turnover',
            '换手率': 'turnover_rate'
        }
        df.rename(columns=rename_dict, inplace=True)

        # 标准化
        df = _normalize_stock_data(df, 'akshare')

        return df

    except KeyError as e:
        print(f"[AKShare错误] 股票 {stock} 数据不存在: {e}")
        return pd.DataFrame()
    except Exception as e:
        print(f"[AKShare错误] 获取股票 {stock} 数据失败: {e}")
        return pd.DataFrame()


def _get_stock_data_yfinance(stock, start, end):
    """
    使用yfinance获取股票数据
    Get stock data using yfinance (Yahoo Finance)

    Args:
        stock: 股票代码 (支持A股/港股/美股)
        start: 开始日期 (YYYYMMDD)
        end: 结束日期 (YYYYMMDD)

    Returns:
        pd.DataFrame: 标准化的股票数据
    """
    try:
        import yfinance as yf

        # 转换股票代码
        ticker_symbol = _convert_stock_code(stock, 'yfinance')

        # 转换日期格式: "20200101" -> "2020-01-01"
        start_date = pd.to_datetime(start).strftime('%Y-%m-%d')
        end_date = pd.to_datetime(end).strftime('%Y-%m-%d')

        # 获取数据 (auto_adjust=True 自动复权)
        ticker = yf.Ticker(ticker_symbol)
        df = ticker.history(start=start_date, end=end_date, auto_adjust=True)

        if df is None or df.empty:
            return pd.DataFrame()

        # 标准化
        df = _normalize_stock_data(df, 'yfinance')

        return df

    except ImportError:
        print("[yfinance错误] 未安装yfinance库,请运行: pip install yfinance")
        return pd.DataFrame()
    except Exception as e:
        print(f"[yfinance错误] 获取股票 {stock} 数据失败: {e}")
        return pd.DataFrame()


def _get_stock_data_auto(stock, start, end):
    """
    自动备援策略: 优先akshare,失败切换yfinance
    Auto fallback strategy: akshare first, switch to yfinance on failure

    Args:
        stock: 股票代码
        start: 开始日期 (YYYYMMDD)
        end: 结束日期 (YYYYMMDD)

    Returns:
        pd.DataFrame: 股票数据
    """
    # 判断是否为A股
    is_a_share = stock.isdigit() and len(stock) == 6

    if is_a_share:
        # A股优先使用akshare (速度快)
        try:
            df = _get_stock_data_akshare(stock, start, end)
            if not df.empty:
                return df
            print(f"[数据源切换] AKShare获取失败,尝试yfinance...")
        except Exception as e:
            print(f"[数据源切换] AKShare异常: {e}")

        # 备援: yfinance
        try:
            df = _get_stock_data_yfinance(stock, start, end)
            if not df.empty:
                print(f"[数据源切换] yfinance获取成功")
                return df
        except Exception as e:
            print(f"[数据源切换] yfinance也失败: {e}")
    else:
        # 港股/美股直接使用yfinance
        try:
            df = _get_stock_data_yfinance(stock, start, end)
            if not df.empty:
                return df
        except Exception as e:
            print(f"[yfinance错误] 获取{stock}失败: {e}")

    print(f"[数据源切换] 所有数据源均失败: {stock}")
    return pd.DataFrame()


def get_stock_data(stock="600519", start="20200101", end="20240101", source='auto'):
    """
    获取股票数据并处理为标准格式 (支持多数据源)
    Get stock data and process to standard format (supports multiple data sources)

    参数 / Parameters:
        stock: 股票代码 (Stock code)
               - A股: "600519", "000858"
               - 港股: "0700.HK"
               - 美股: "AAPL"
        start: 开始日期 (YYYYMMDD)
        end: 结束日期 (YYYYMMDD)
        source: 数据源选择 (Data source selection)
                - 'auto': 自动选择 (默认: A股用akshare,失败切yfinance; 港美股用yfinance)
                - 'akshare': 仅使用akshare (仅支持A股)
                - 'yfinance': 仅使用yfinance (支持A股/港股/美股)

    返回 / Returns:
        pd.DataFrame:
            columns: ['open', 'high', 'low', 'close', 'volume']
            index: DatetimeIndex
            dtype: float64

    示例 / Examples:
        >>> # A股自动模式
        >>> df = get_stock_data("600519", "20200101", "20240101")

        >>> # 港股
        >>> df = get_stock_data("0700.HK", "20200101", "20240101")

        >>> # 美股
        >>> df = get_stock_data("AAPL", "20200101", "20240101")

        >>> # 强制使用yfinance
        >>> df = get_stock_data("600519", "20200101", "20240101", source='yfinance')
    """
    if source == 'auto':
        return _get_stock_data_auto(stock, start, end)
    elif source == 'akshare':
        return _get_stock_data_akshare(stock, start, end)
    elif source == 'yfinance':
        return _get_stock_data_yfinance(stock, start, end)
    else:
        raise ValueError(f"不支持的数据源: {source}。可选: 'auto', 'akshare', 'yfinance'")
