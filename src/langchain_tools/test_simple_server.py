# src/langchain_tools/test_simple_server.py

import asyncio
import os
import sys

from mcp.client.stdio import stdio_client, StdioServerParameters
from mcp import ClientSession

# ==================== MCP 服务器启动命令 ====================
MCP_COMMAND = "d:/Files/Code/Stocking/.conda/python.exe"
MCP_ARGS = ["d:/Files/Code/Stocking/src/MCP/server_simple.py"]

async def test_simple_server():
    """测试简化版MCP服务器"""
    print("=== 测试简化版MCP服务器 ===")
    
    # 检查文件路径
    if not os.path.exists(MCP_COMMAND):
        print(f"❌ Python路径不存在: {MCP_COMMAND}")
        return False
    
    if not os.path.exists(MCP_ARGS[0]):
        print(f"❌ 服务器文件不存在: {MCP_ARGS[0]}")
        return False
    
    print("✅ 文件路径检查通过")
    
    # 创建服务器参数
    server_params = StdioServerParameters(
        command=MCP_COMMAND,
        args=MCP_ARGS
    )
    
    print("正在启动MCP服务器...")
    
    try:
        async with stdio_client(server_params) as (read_stream, write_stream):
            print("✅ stdio_client连接成功")
            
            session = ClientSession(read_stream, write_stream)
            
            try:
                # 尝试初始化会话
                print("正在初始化会话...")
                await asyncio.wait_for(session.initialize(), timeout=10.0)
                print("✅ 会话初始化成功")
                
                # 尝试获取工具列表
                print("正在获取工具列表...")
                tools_result = await asyncio.wait_for(session.list_tools(), timeout=5.0)
                print(f"✅ 获取到 {len(tools_result.tools)} 个工具")
                
                for tool in tools_result.tools:
                    print(f"  - {tool.name}: {tool.description}")
                
                # 测试一个工具
                if tools_result.tools:
                    print("\n正在测试工具调用...")
                    test_tool = tools_result.tools[0]
                    
                    # 调用工具
                    result = await session.call_tool({
                        "name": test_tool.name,
                        "arguments": {"stock": "000001"}
                    })
                    
                    print(f"✅ 工具调用成功")
                    if result.content:
                        for content in result.content:
                            if hasattr(content, 'text'):
                                print(f"结果: {content.text[:200]}...")
                
                return True
                
            except asyncio.TimeoutError:
                print("❌ 会话初始化或工具获取超时")
                return False
            except Exception as e:
                print(f"❌ 会话操作失败: {e}")
                return False
            finally:
                try:
                    await session.close()
                except:
                    pass
                    
    except asyncio.TimeoutError:
        print("❌ MCP服务器启动超时")
        return False
    except Exception as e:
        print(f"❌ stdio_client创建失败: {e}")
        return False

async def main():
    """主函数"""
    print("开始简化版MCP服务器测试...\n")
    
    success = await test_simple_server()
    
    print("\n" + "="*50)
    if success:
        print("✅ 简化版MCP服务器测试成功！")
        print("服务器可以正常与客户端通信。")
    else:
        print("❌ 简化版MCP服务器测试失败")
        print("问题可能出现在MCP库的版本兼容性上。")
    
    return success

if __name__ == "__main__":
    # Windows 兼容性设置
    if os.name == "nt":
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
    
    result = asyncio.run(main())
    sys.exit(0 if result else 1)