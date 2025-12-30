# src/langchain_tools/finance_agent_debug.py

import asyncio
import os
import sys
from typing import List, Any

from mcp.client.stdio import stdio_client, StdioServerParameters
from mcp import ClientSession
from mcp.types import Tool, CallToolRequest, CallToolRequestParams
from langchain_core.tools import BaseTool

# ==================== MCP 工具包装类 ====================
class MCPTool(BaseTool):
    """包装 MCP 工具为 LangChain BaseTool"""

    mcp_name: str
    session: Any

    def __init__(self, **data):
        super().__init__(**data)

    async def _arun(self, **kwargs) -> str:
        try:
            params = CallToolRequestParams(name=self.mcp_name, arguments=kwargs)
            result = await self.session.call_tool(params)
            # 返回工具结果的文本内容
            return "\n".join(c.text for c in result.content if hasattr(c, 'text'))
        except Exception as e:
            return f"工具调用失败：{str(e)}"

    def _run(self, **kwargs) -> str:
        raise NotImplementedError("同步调用不支持，请使用异步版本")

# ==================== MCP 服务器启动命令 ====================
MCP_COMMAND = "d:/Files/Code/Stocking/.conda/python.exe"
MCP_ARGS = ["d:/Files/Code/Stocking/src/MCP/server.py"]

# ==================== 创建 LangChain 工具 ====================
async def create_langchain_tools_from_mcp(session) -> List[Any]:
    """从已建立的MCP会话创建 LangChain 工具"""

    try:
        print("正在获取MCP工具列表...")
        # 获取工具列表（加超时防止卡死）
        tools_result = await asyncio.wait_for(session.list_tools(), timeout=20.0)
        mcp_tools: List[Tool] = tools_result.tools
        print(f"成功获取到 {len(mcp_tools)} 个工具")
    except asyncio.TimeoutError:
        print("错误：获取工具列表超时，MCP服务器可能未正确启动")
        return []
    except Exception as e:
        print(f"获取工具列表失败: {e}")
        return []

    if not mcp_tools:
        print("警告：MCP 服务器未暴露任何工具！请检查 server.py 是否正确注册了工具。")
        return []

    langchain_tools = []
    for mcp_tool in mcp_tools:
        tool_name = mcp_tool.name
        tool_description = mcp_tool.description or "无描述"

        langchain_tools.append(MCPTool(name=tool_name, description=tool_description, mcp_name=tool_name, session=session))

    print(f"成功加载 {len(langchain_tools)} 个 MCP 股票工具：")
    for t in langchain_tools:
        print(f"  - {t.name}: {t.description}")

    return langchain_tools

# ==================== 测试工具功能 ====================
async def test_tools(tools, session):
    """测试工具功能"""
    if not tools:
        return
    
    print("\n=== 开始测试工具功能 ===")
    
    # 测试第一个工具（通常是最基本的股票数据获取）
    test_tool = tools[0]
    print(f"测试工具: {test_tool.name}")
    
    try:
        # 使用简单的测试参数
        result = await test_tool._arun(stock="000001")
        print(f"测试结果: {result[:200]}..." if len(result) > 200 else f"测试结果: {result}")
    except Exception as e:
        print(f"工具测试失败: {e}")

# ==========================================================
async def main():
    print("正在启动 MCP 股票工具 Agent (调试版)...")
    print(f"MCP命令: {MCP_COMMAND}")
    print(f"MCP参数: {MCP_ARGS}")

    # 检查Python路径是否存在
    if not os.path.exists(MCP_COMMAND):
        print(f"错误：Python路径不存在: {MCP_COMMAND}")
        return
    
    # 检查服务器文件是否存在
    server_file = MCP_ARGS[0]
    if not os.path.exists(server_file):
        print(f"错误：MCP服务器文件不存在: {server_file}")
        return

    print("创建服务器参数...")
    # 创建服务器参数
    server_params = StdioServerParameters(
        command=MCP_COMMAND,
        args=MCP_ARGS
    )

    print("使用 stdio_client 创建会话...")
    try:
        # 使用 stdio_client 创建会话，添加超时
        async with stdio_client(server_params) as (read_stream, write_stream):
            print("创建 ClientSession...")
            session = ClientSession(read_stream, write_stream)
            try:
                print("初始化会话...")
                # 初始化会话（添加超时）
                await asyncio.wait_for(session.initialize(), timeout=30.0)
                print("会话初始化成功")

                tools = await create_langchain_tools_from_mcp(session)
                if not tools:
                    print("无可用工具，程序退出。")
                    return

                # 测试工具功能
                await test_tools(tools, session)

                print("\n=== MCP 工具连接成功！ ===")
                print("工具已准备就绪，可以集成到LangChain Agent中使用。")
                
                # 保持连接一段时间以便观察
                print("保持连接10秒...")
                await asyncio.sleep(10)

            except asyncio.TimeoutError:
                print("错误：MCP 服务器启动或初始化超时，请检查：")
                print("1. MCP服务器是否依赖正确的Python环境")
                print("2. 股票数据获取模块是否正常")
                print("3. 网络连接是否正常")
            except Exception as e:
                print(f"会话操作失败：{e}")
                import traceback
                traceback.print_exc()
            finally:
                try:
                    await session.close()
                    print("会话已关闭")
                except:
                    print("会话关闭失败")
    except asyncio.TimeoutError:
        print("错误：MCP服务器启动超时，请检查Python路径和服务器文件")
    except Exception as e:
        print(f"stdio_client 创建失败：{e}")
        import traceback
        traceback.print_exc()
    print("程序退出。")

if __name__ == "__main__":
    # Windows 兼容性设置
    if os.name == "nt":
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
    
    asyncio.run(main())