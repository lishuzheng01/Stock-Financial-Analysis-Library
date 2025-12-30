# src/langchain_tools/mcp_server_debug.py

import asyncio
import os
import sys
import subprocess
import time
from typing import List, Any

# ==================== MCP 服务器启动命令 ====================
MCP_COMMAND = "d:/Files/Code/Stocking/.conda/python.exe"
MCP_ARGS = ["d:/Files/Code/Stocking/src/MCP/server.py"]

def test_mcp_server_directly():
    """直接测试MCP服务器是否能正常运行"""
    print("=== 直接测试MCP服务器 ===")
    
    try:
        # 使用subprocess运行MCP服务器，捕获输出
        process = subprocess.Popen(
            [MCP_COMMAND] + MCP_ARGS,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            bufsize=1,
            universal_newlines=True
        )
        
        # 等待几秒钟看是否有输出
        time.sleep(3)
        
        # 检查进程是否还在运行
        if process.poll() is not None:
            # 进程已退出，读取错误输出
            stdout, stderr = process.communicate()
            print("❌ MCP服务器已退出")
            if stdout:
                print(f"标准输出: {stdout}")
            if stderr:
                print(f"错误输出: {stderr}")
            return False
        else:
            print("✅ MCP服务器仍在运行（正常状态）")
            # 终止进程
            process.terminate()
            process.wait()
            return True
            
    except Exception as e:
        print(f"❌ 启动MCP服务器失败: {e}")
        return False

def check_mcp_dependencies():
    """检查MCP相关依赖"""
    print("\n=== 检查MCP依赖 ===")
    
    dependencies = [
        "mcp",
        "mcp.server.fastmcp", 
        "mcp.client.stdio",
        "mcp.types",
        "stock_tool.get_stock_data",
        "stock_tool.AltmanZScore",
        "stock_tool.BeneishMScore",
        "stock_tool.check_benford"
    ]
    
    all_ok = True
    for dep in dependencies:
        try:
            if dep.startswith("stock_tool"):
                # 需要添加src路径
                sys.path.append('src')
                __import__(dep)
            else:
                __import__(dep)
            print(f"✅ {dep}")
        except ImportError as e:
            print(f"❌ {dep}: {e}")
            all_ok = False
    
    return all_ok

def check_server_code():
    """检查服务器代码语法"""
    print("\n=== 检查服务器代码语法 ===")
    
    try:
        # 编译服务器代码检查语法
        with open("src/MCP/server.py", "r", encoding="utf-8") as f:
            code = f.read()
        compile(code, "server.py", "exec")
        print("✅ 服务器代码语法正确")
        return True
    except SyntaxError as e:
        print(f"❌ 服务器代码语法错误: {e}")
        return False
    except Exception as e:
        print(f"❌ 检查代码时出错: {e}")
        return False

async def test_mcp_communication():
    """测试MCP通信协议"""
    print("\n=== 测试MCP通信协议 ===")
    
    try:
        from mcp.client.stdio import stdio_client, StdioServerParameters
        from mcp import ClientSession
        
        server_params = StdioServerParameters(
            command=MCP_COMMAND,
            args=MCP_ARGS
        )
        
        print("启动stdio_client...")
        async with stdio_client(server_params) as (read_stream, write_stream):
            print("创建ClientSession...")
            session = ClientSession(read_stream, write_stream)
            
            try:
                print("初始化会话...")
                # 使用更短的超时
                await asyncio.wait_for(session.initialize(), timeout=5.0)
                print("✅ 会话初始化成功")
                
                # 测试工具列表获取
                print("获取工具列表...")
                tools_result = await asyncio.wait_for(session.list_tools(), timeout=3.0)
                print(f"✅ 获取到 {len(tools_result.tools)} 个工具")
                
                return True
                
            except asyncio.TimeoutError:
                print("❌ 会话初始化超时")
                return False
            except Exception as e:
                print(f"❌ 会话操作失败: {e}")
                return False
            finally:
                try:
                    await session.close()
                except:
                    pass
                    
    except Exception as e:
        print(f"❌ 通信测试失败: {e}")
        return False

async def main():
    """主函数"""
    print("开始MCP服务器深度调试...\n")
    
    # 检查依赖
    deps_ok = check_mcp_dependencies()
    
    # 检查代码语法
    code_ok = check_server_code()
    
    # 直接测试服务器
    server_ok = test_mcp_server_directly()
    
    # 测试通信协议
    comm_ok = await test_mcp_communication()
    
    print("\n" + "="*60)
    print("调试结果汇总:")
    print(f"依赖检查: {'✅ 通过' if deps_ok else '❌ 失败'}")
    print(f"代码语法: {'✅ 通过' if code_ok else '❌ 失败'}")
    print(f"服务器启动: {'✅ 通过' if server_ok else '❌ 失败'}")
    print(f"通信协议: {'✅ 通过' if comm_ok else '❌ 失败'}")
    
    if deps_ok and code_ok and server_ok and comm_ok:
        print("\n✅ 所有测试通过！MCP服务器应该可以正常工作。")
        return True
    else:
        print("\n❌ 部分测试失败，请根据上面的错误信息进行修复。")
        return False

if __name__ == "__main__":
    # Windows 兼容性设置
    if os.name == "nt":
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
    
    result = asyncio.run(main())
    sys.exit(0 if result else 1)