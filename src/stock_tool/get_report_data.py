# -*- coding: utf-8 -*-
"""
财务报表数据获取模块 - Financial Report Data Module
支持多数据源架构: akshare (primary) + extensible for future sources
Supports multiple data sources: akshare (primary) + extensible for future sources
"""

import akshare as ak
import pandas as pd
import logging
import requests
import urllib3
import json
import os

# 配置日志系统
# Configure logging system
logger = logging.getLogger('stock_tool.get_report_data')
if not logger.handlers:  # 避免重复添加handler
    handler = logging.StreamHandler()
    handler.setFormatter(logging.Formatter('[%(levelname)s] %(message)s'))
    logger.addHandler(handler)
    logger.setLevel(logging.INFO)

# 禁用SSL警告
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)


# ========================================
# 加载翻译映射 - Load Translation Maps
# ========================================

def _load_translation_map(filename):
    """
    从JSON文件加载翻译映射
    Load translation map from JSON file

    Args:
        filename: JSON文件名 (JSON filename)

    Returns:
        dict: 翻译映射字典 (Translation map dictionary)
    """
    try:
        current_dir = os.path.dirname(os.path.abspath(__file__))
        json_path = os.path.join(current_dir, filename)

        with open(json_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    except FileNotFoundError:
        logger.error(f"[配置错误] 找不到翻译映射文件: {filename}")
        return {}
    except json.JSONDecodeError as e:
        logger.error(f"[配置错误] JSON文件格式错误 {filename}: {e}")
        return {}
    except Exception as e:
        logger.error(f"[配置错误] 加载翻译映射失败 {filename}: {e}")
        return {}


# 延迟加载翻译映射字典 (Lazy load translation maps)
_translation_maps = {}

def _get_translation_map(report_type):
    """
    获取指定报表类型的翻译映射（带缓存）
    Get translation map for specified report type (with cache)

    Args:
        report_type: 报表类型 (Report type: "利润表", "资产负债表", "现金流量表")

    Returns:
        dict: 翻译映射字典 (Translation map dictionary)
    """
    if report_type not in _translation_maps:
        filename_map = {
            "利润表": "translation_map_income.json",
            "资产负债表": "translation_map_asset.json",
            "现金流量表": "translation_map_cashflow.json"
        }
        filename = filename_map.get(report_type)
        if filename:
            _translation_maps[report_type] = _load_translation_map(filename)
        else:
            _translation_maps[report_type] = {}

    return _translation_maps[report_type]


# ========================================
# 内部函数 - Internal Functions
# ========================================

def _normalize_report_data(df, symbol, source_name):
    """
    标准化财报数据格式
    Normalize financial report data format to unified standard

    统一输出标准:
    - Columns: 英文列名 (English column names)
    - 验证必需列是否存在 (Verify required columns exist)
    - 处理数据类型转换 (Handle data type conversion)

    Args:
        df: 原始DataFrame (Raw DataFrame)
        symbol: 报表类型 (Report type: "资产负债表", "利润表", "现金流量表")
        source_name: 数据源名称 (Data source name: 'akshare' or 'yfinance')

    Returns:
        pd.DataFrame: 标准化后的DataFrame (Normalized DataFrame)
    """
    if df is None or df.empty:
        return pd.DataFrame()

    try:
        # 应用列名映射 (Apply column name mapping)
        if source_name == 'akshare':
            translation_map = _get_translation_map(symbol)
            if translation_map:
                df = df.rename(columns=translation_map)
            else:
                logger.warning(f"[数据标准化] 无法加载 {symbol} 的翻译映射")

        # 验证关键列 (Verify key columns)
        required_cols = {
            "利润表": ['Operating Revenue', 'Net Profit Attributable to Parent'],
            "资产负债表": ['Total Assets', 'Total Equity Attributable to Shareholders of the Parent Company'],
            "现金流量表": ['Net Cash Flow from Operating Activities']
        }

        missing_cols = []
        for col in required_cols.get(symbol, []):
            if col not in df.columns:
                missing_cols.append(col)

        if missing_cols:
            logger.warning(f"[数据标准化] {symbol} 缺少部分关键列: {missing_cols}")

        return df

    except Exception as e:
        logger.error(f"[数据标准化错误] {source_name} - {symbol}: {e}")
        return pd.DataFrame()


def _get_report_data_akshare(stock, symbol):
    """
    使用AKShare获取财报 (新浪财经)
    Get financial report using AKShare (Sina Finance)

    Args:
        stock: 股票代码 (Stock code, e.g., "600519")
        symbol: 报表类型 (Report type: "资产负债表", "利润表", "现金流量表")

    Returns:
        pd.DataFrame: 标准化的财报数据 (Normalized financial report data)
    """
    try:
        # 获取AKShare数据 (Fetch data from AKShare)
        df = ak.stock_financial_report_sina(stock=stock, symbol=symbol)

        if df is None or df.empty:
            logger.warning(f"[AKShare] {stock} - {symbol}: 返回空数据")
            return pd.DataFrame()

        # 标准化数据 (Normalize data)
        df = _normalize_report_data(df, symbol, 'akshare')

        if not df.empty:
            logger.info(f"[数据源:AKShare] {stock} - {symbol}: 获取成功 ({len(df)}期)")

        return df

    except requests.Timeout:
        logger.error(f"[AKShare] {stock} - {symbol}: 网络超时")
        return pd.DataFrame()

    except requests.exceptions.SSLError as e:
        logger.error(f"[AKShare] {stock} - {symbol}: SSL连接错误 - {e}")
        return pd.DataFrame()

    except KeyError as e:
        logger.error(f"[AKShare] {stock} - {symbol}: 股票不存在或数据格式错误 - {e}")
        return pd.DataFrame()

    except Exception as e:
        logger.error(f"[AKShare] {stock} - {symbol}: 未知错误 - {e}")
        return pd.DataFrame()


def _get_report_data_yfinance(stock, symbol):
    """
    使用yfinance获取财报 (占位实现)
    Get financial report using yfinance (placeholder implementation)

    注意: yfinance不支持A股财报数据
    Note: yfinance does NOT support A-share financial reports

    Args:
        stock: 股票代码 (Stock code)
        symbol: 报表类型 (Report type)

    Returns:
        pd.DataFrame: 空DataFrame (Empty DataFrame)
    """
    logger.warning(f"[yfinance] {stock} - {symbol}: yfinance不支持A股财报,返回空数据")
    logger.info(f"[提示] 如需备援数据源,建议集成Tushare Pro或Eastmoney")
    return pd.DataFrame()


def _get_report_data_auto(stock, symbol):
    """
    自动备援策略
    Auto fallback strategy

    优先akshare,失败记录日志
    Priority: akshare first, log on failure

    Args:
        stock: 股票代码 (Stock code)
        symbol: 报表类型 (Report type)

    Returns:
        pd.DataFrame: 财报数据 (Financial report data)
    """
    # 优先尝试akshare (Try akshare first)
    df = _get_report_data_akshare(stock, symbol)

    if not df.empty:
        return df

    # akshare失败,记录日志 (akshare failed, log it)
    logger.warning(f"[数据源切换] {stock} - {symbol}: AKShare获取失败")

    # yfinance不支持A股财报,不尝试切换
    # yfinance doesn't support A-share reports, don't try switching
    logger.info(f"[数据源切换] {stock} - {symbol}: 无可用备援数据源 (yfinance不支持A股财报)")

    return pd.DataFrame()


# ========================================
# 主函数 - Main Function
# ========================================

def get_report_data(stock="", symbol="", transpose=True, source='auto'):
    """
    获取股票的财务报告数据并处理为标准格式 (支持多数据源)
    Get stock financial report data and process to standard format (supports multiple data sources)

    参数 / Parameters:
        stock: 股票代码 (Stock code)
               - A股: "600519", "000858"
        symbol: 报告类型 (Report type)
                - 可选: "资产负债表", "利润表", "现金流量表"
        transpose: 是否转置数据 (Whether to transpose data)
                   - 默认True (保持向后兼容)
                   - 注意: 当前版本transpose功能暂未实现,保留参数以兼容现有代码
        source: 数据源选择 (Data source selection)
                - 'auto': 自动选择 (默认: akshare)
                - 'akshare': 仅使用akshare (新浪财经)
                - 'yfinance': 仅使用yfinance (注意: 不支持A股财报)

    返回 / Returns:
        pd.DataFrame:
            columns: 英文列名 (English column names)
            rows: 各期财报数据 (Financial report data for each period)

    示例 / Examples:
        >>> # 基础用法 (默认auto模式)
        >>> df = get_report_data(stock="600519", symbol="利润表")

        >>> # 指定数据源
        >>> df = get_report_data(stock="600519", symbol="资产负债表", source='akshare')

        >>> # 不转置 (参数保留,功能待实现)
        >>> df = get_report_data(stock="600519", symbol="现金流量表", transpose=False)
    """
    # 参数验证 (Parameter validation)
    if not stock:
        logger.error("[参数错误] 股票代码不能为空")
        return pd.DataFrame()

    if symbol not in ["资产负债表", "利润表", "现金流量表"]:
        logger.error(f"[参数错误] 无效的报表类型: {symbol}")
        return pd.DataFrame()

    # 根据source参数选择数据源 (Select data source based on source parameter)
    if source == 'auto':
        df = _get_report_data_auto(stock, symbol)
    elif source == 'akshare':
        df = _get_report_data_akshare(stock, symbol)
    elif source == 'yfinance':
        df = _get_report_data_yfinance(stock, symbol)
    else:
        logger.error(f"[参数错误] 不支持的数据源: {source}。可选: 'auto', 'akshare', 'yfinance'")
        return pd.DataFrame()

    # 最终检查 (Final check)
    if df.empty:
        logger.warning(f"[获取失败] {stock} - {symbol}: 所有数据源均失败,返回空DataFrame")

    # 注意: transpose功能暂未实现,保留参数以兼容现有代码
    # Note: transpose functionality not yet implemented, parameter retained for backward compatibility
    if transpose is False:
        logger.debug(f"[提示] transpose=False参数已接收,但功能暂未实现")

    return df
