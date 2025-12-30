# src/langchain_tools/mcp_silicon_openai_agent.py

import asyncio
import os
import json
import subprocess
from typing import List, Any
from functools import partial

from mcp.client.stdio import stdio_client, StdioServerParameters
from mcp import ClientSession
from mcp.types import Tool, CallToolRequest, CallToolRequestParams
from langchain_core.tools import tool, BaseTool
from langgraph.prebuilt import create_react_agent
from langchain_openai import ChatOpenAI

# ==================== 硅基流动 OpenAI 兼容配置 ====================
os.environ["SILICONFLOW_API_KEY"] = "sk-请替换成你的真实硅基流动API密钥"

llm = ChatOpenAI(
    model="deepseek-ai/DeepSeek-V3.2",
    temperature=0.3,
    max_tokens=4096,
    openai_api_key=os.environ["SILICONFLOW_API_KEY"],
    openai_api_base="https://api.siliconflow.cn/v1",
)

# ==================== MCP 工具包装类 ====================
class MCPTool(BaseTool):
    """包装 MCP 工具为 LangChain BaseTool"""

    mcp_name: str
    session: Any

    def __init__(self, **data):
        super().__init__(**data)

    async def _arun(self, **kwargs) -> str:
        params = CallToolRequestParams(name=self.mcp_name, arguments=kwargs)
        result = await self.session.call_tool(params)
        # 返回工具结果的文本内容
        return "\n".join(c.text for c in result.content if hasattr(c, 'text'))

    def _run(self, **kwargs) -> str:
        raise NotImplementedError("同步调用不支持，请使用异步版本")

# ==================== MCP 服务器启动命令 ====================
MCP_COMMAND = "d:/Files/Code/Stocking/.conda/python.exe"
MCP_ARGS = ["d:/Files/Code/Stocking/src/MCP/server.py"]

# ==================== 创建 LangChain 工具 ====================
async def create_langchain_tools_from_mcp(session) -> List[Any]:
    """从已建立的MCP会话创建 LangChain 工具"""

    try:
        # 获取工具列表（加超时防止卡死）
        tools_result = await asyncio.wait_for(session.list_tools(), timeout=15.0)
        mcp_tools: List[Tool] = tools_result.tools
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

# ==========================================================
async def main():
    print("正在启动 DeepSeek-V3.2 (硅基流动) + 本地 MCP 股票工具 Agent...")

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

                # 创建 ReAct 自规划 Agent
                agent_app = create_react_agent(model=llm, tools=tools)
                print("Agent 创建成功！")

                print("\n=== Agent 已就绪！可以开始提问（输入 exit 退出）===\n")

                while True:
                    user_input = input("你：").strip()
                    if user_input.lower() in {"exit", "quit", "q", ""}:
                        break
                    if not user_input:
                        continue

                    print("\nAgent 正在思考并规划...\n")

                    try:
                        async for chunk in agent_app.astream(
                            {"messages": [{"role": "user", "content": user_input}]},
                            stream_mode="values"
                        ):
                            message = chunk["messages"][-1]
                            if message.type == "ai":
                                if message.content:
                                    print(message.content, end="", flush=True)
                                if hasattr(message, "tool_calls") and message.tool_calls:
                                    print(f"\n[工具调用] {message.tool_calls}\n")
                            elif message.type == "tool":
                                print(f"[工具结果] {message.name}: {message.content}\n")
                    except Exception as e:
                        print(f"Agent 处理出错：{e}")
                        print("继续下一个问题...\n")

                    print("\n" + "-" * 60 + "\n")

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
                except:
                    pass
    except asyncio.TimeoutError:
        print("错误：MCP服务器启动超时，请检查Python路径和服务器文件")
    except Exception as e:
        print(f"stdio_client 创建失败：{e}")
        import traceback
        traceback.print_exc()
    print("MCP 服务器已关闭，程序退出。")

if __name__ == "__main__":
    # Windows 兼容性设置
    if os.name == "nt":
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
    
    asyncio.run(main())