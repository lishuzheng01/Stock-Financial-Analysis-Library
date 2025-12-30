# -*- coding: utf-8 -*-

import sys
import io

# ============ 强制使用 UTF-8 编码（解决 Windows GBK 编码错误） ============
# 这两行必须尽量靠前，确保后续所有 print/output 都走 UTF-8
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')
# ===========================================================================

# 现在开始导入其他模块
from mcp.server.models import InitializationOptions
from mcp.server import Server
import mcp.server.stdio

# 你的股票工具函数导入（保持不变）
from stock_tool.get_stock_data import get_stock_data
from stock_tool.AltmanZScore import analyze_altman_zscore
from stock_tool.BeneishMScore import BeneishMScore_check
from stock_tool.check_benford import check_benford

# ==================== 使用基础的MCP服务器 ====================
server = Server("股票分析MCP服务器")

# ------------------- Tool 1: 获取股票历史数据 -------------------
@server.list_tools()
async def get_tools():
    return [
        {
            "name": "get_stock_data",
            "description": "获取指定股票的历史K线数据（开盘、最高、最低、收盘、成交量），返回数据摘要",
            "inputSchema": {
                "type": "object",
                "properties": {
                    "stock": {"type": "string", "description": "股票代码"},
                    "start": {"type": "string", "description": "开始日期，格式YYYYMMDD", "default": "20200101"},
                    "end": {"type": "string", "description": "结束日期，格式YYYYMMDD", "default": "20251231"}
                },
                "required": ["stock"]
            }
        },
        {
            "name": "analyze_altman_zscore",
            "description": "使用Altman Z-Score模型评估上市公司破产风险，返回最新Z-Score及风险等级",
            "inputSchema": {
                "type": "object",
                "properties": {
                    "stock": {"type": "string", "description": "股票代码"}
                },
                "required": ["stock"]
            }
        },
        {
            "name": "analyze_beneish_mscore",
            "description": "使用Beneish M-Score模型检测财务报表潜在操纵风险，返回完整分析报告",
            "inputSchema": {
                "type": "object",
                "properties": {
                    "stock": {"type": "string", "description": "股票代码"}
                },
                "required": ["stock"]
            }
        },
        {
            "name": "check_benford_law",
            "description": "基于收盘价检查股票数据是否符合Benford定律，用于检测潜在数据异常或操纵",
            "inputSchema": {
                "type": "object",
                "properties": {
                    "stock": {"type": "string", "description": "股票代码"},
                    "start": {"type": "string", "description": "开始日期，格式YYYYMMDD", "default": "20200101"},
                    "end": {"type": "string", "description": "结束日期，格式YYYYMMDD", "default": "20251231"}
                },
                "required": ["stock"]
            }
        }
    ]

@server.call_tool()
async def call_tool(name: str, arguments: dict):
    if name == "get_stock_data":
        stock = arguments.get("stock")
        start = arguments.get("start", "20200101")
        end = arguments.get("end", "20251231")
        
        try:
            df = get_stock_data(stock=stock, start=start, end=end)
            if df.empty:
                return [{"type": "text", "text": f"错误：无法获取股票 {stock} 的历史数据（可能股票代码错误或无数据）"}]
            
            latest_date = df.index[-1].strftime('%Y-%m-%d')
            earliest_date = df.index[0].strftime('%Y-%m-%d')
            latest_close = df['close'].iloc[-1]
            data_points = len(df)
            
            result = (
                f"股票 {stock} 历史数据获取成功！\n"
                f"数据范围：{earliest_date} 至 {latest_date}\n"
                f"数据点数：{data_points}\n"
                f"最新收盘价：{latest_close:.2f}\n"
                f"数据已加载，可用于后续技术分析或检测。"
            )
            return [{"type": "text", "text": result}]
        except Exception as e:
            return [{"type": "text", "text": f"获取股票数据失败：{str(e)}"}]
    
    elif name == "analyze_altman_zscore":
        stock = arguments.get("stock")
        
        try:
            data, _ = analyze_altman_zscore(stock, print_output=False)
            
            if data.empty:
                return [{"type": "text", "text": f"错误：无法获取股票 {stock} 的财务数据（可能不支持该股票或数据缺失）"}]
            
            latest_zscore = data.iloc[0]['Z-Score']
            
            if latest_zscore > 2.99:
                risk_level = "安全区域 (Safe Zone) - 破产风险低"
            elif latest_zscore > 1.81:
                risk_level = "灰色区域 (Grey Zone) - 需要关注"
            else:
                risk_level = "危险区域 (Distress Zone) - 破产风险高"
            
            result = (
                f"股票 {stock} Altman Z-Score 分析结果：\n"
                f"最新 Z-Score：{latest_zscore:.2f}\n"
                f"风险评估：{risk_level}\n"
                f"（基于最新年度财务数据）"
            )
            return [{"type": "text", "text": result}]
        except Exception as e:
            return [{"type": "text", "text": f"Altman Z-Score 分析失败：{str(e)}"}]
    
    elif name == "analyze_beneish_mscore":
        stock = arguments.get("stock")
        
        try:
            result = BeneishMScore_check(stock)
            return [{"type": "text", "text": f"股票 {stock} Beneish M-Score 分析结果：\n{result}"}]
        except Exception as e:
            return [{"type": "text", "text": f"Beneish M-Score 分析失败：{str(e)}"}]
    
    elif name == "check_benford_law":
        stock = arguments.get("stock")
        start = arguments.get("start", "20200101")
        end = arguments.get("end", "20251231")
        
        try:
            df = get_stock_data(stock=stock, start=start, end=end)
            if df.empty:
                return [{"type": "text", "text": f"错误：无法获取股票 {stock} 的数据"}]
            
            close_prices = df['close'].dropna()
            if len(close_prices) < 100:
                return [{"type": "text", "text": f"警告：数据点太少（{len(close_prices)}），Benford检查结果可能不准确"}]
            
            digit_counts, expected_counts = check_benford(close_prices)
            
            total_deviation = sum(
                abs(digit_counts.get(str(d), 0) - expected_counts[d-1]) / expected_counts[d-1]
                for d in range(1, 10)
            )
            avg_deviation = total_deviation / 9
            
            if avg_deviation < 0.1:
                conformity = "高度符合 Benford 定律（数据自然度高）"
            elif avg_deviation < 0.2:
                conformity = "基本符合 Benford 定律（正常范围）"
            else:
                conformity = "显著偏离 Benford 定律（可能存在数据异常或操纵风险）"
            
            result = (
                f"股票 {stock} Benford 定律检查结果：\n"
                f"数据点数：{len(close_prices)}\n"
                f"平均相对偏差：{avg_deviation:.3f}\n"
                f"结论：{conformity}"
            )
            return [{"type": "text", "text": result}]
        except Exception as e:
            return [{"type": "text", "text": f"Benford 定律检查失败：{str(e)}"}]
    
    else:
        return [{"type": "text", "text": f"未知工具：{name}"}]

# ------------------- 启动服务器 -------------------
if __name__ == "__main__":
    # 使用基础的stdio服务器
    mcp.server.stdio.run(server)