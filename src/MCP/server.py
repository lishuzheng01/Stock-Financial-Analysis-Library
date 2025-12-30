# -*- coding: utf-8 -*-

import sys
import io
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')

from mcp.server.fastmcp import FastMCP
from stock_tool.get_stock_data import get_stock_data
from stock_tool.AltmanZScore import analyze_altman_zscore
from stock_tool.BeneishMScore import BeneishMScore_check
from stock_tool.check_benford import check_benford

server = FastMCP(name="股票分析MCP服务器")


@server.tool(
    name="get_stock_data",
    description="获取指定股票的历史K线数据"
)
def get_stock_history(stock: str, start: str = "20200101", end: str = "20251231") -> str:
    try:
        df = get_stock_data(stock=stock, start=start, end=end)
        if df.empty:
            return f"错误：无法获取股票 {stock} 的历史数据"
        
        latest_date = df.index[-1].strftime('%Y-%m-%d')
        latest_close = df['close'].iloc[-1]
        data_points = len(df)
        
        return f"股票 {stock} 数据范围：{latest_date}，数据点数：{data_points}，最新收盘价：{latest_close:.2f}"
    except Exception as e:
        return f"获取股票数据失败：{str(e)}"


@server.tool(
    name="analyze_altman_zscore",
    description="Altman Z-Score 破产风险分析"
)
def analyze_altman_zscore_tool(stock: str) -> str:
    try:
        data, _ = analyze_altman_zscore(stock, print_output=False)
        if data.empty:
            return f"错误：无法获取股票 {stock} 的财务数据"
        
        latest_zscore = data.iloc[0]['Z-Score']
        if latest_zscore > 2.99:
            risk_level = "安全"
        elif latest_zscore > 1.81:
            risk_level = "灰色"
        else:
            risk_level = "危险"
        
        return f"股票 {stock} Z-Score：{latest_zscore:.2f}，风险等级：{risk_level}"
    except Exception as e:
        return f"Altman Z-Score 分析失败：{str(e)}"


@server.tool(
    name="analyze_beneish_mscore",
    description="Beneish M-Score 财务操纵检测"
)
def analyze_beneish_mscore_tool(stock: str) -> str:
    try:
        result = BeneishMScore_check(stock)
        return f"股票 {stock} Beneish M-Score 分析结果：{result}"
    except Exception as e:
        return f"Beneish M-Score 分析失败：{str(e)}"


@server.tool(
    name="check_benford_law",
    description="Benford 定律数据质量检查"
)
def check_benford_law_tool(stock: str, start: str = "20200101", end: str = "20251231") -> str:
    try:
        df = get_stock_data(stock=stock, start=start, end=end)
        if df.empty:
            return f"错误：无法获取股票 {stock} 的数据"
        
        close_prices = df['close'].dropna()
        if len(close_prices) < 100:
            return f"警告：数据点太少（{len(close_prices)}）"
        
        digit_counts, expected_counts = check_benford(close_prices)
        return f"股票 {stock} Benford检查完成，数据点数：{len(close_prices)}"
    except Exception as e:
        return f"Benford 定律检查失败：{str(e)}"


if __name__ == "__main__":
    import asyncio
    asyncio.run(server.run(transport="stdio"))
