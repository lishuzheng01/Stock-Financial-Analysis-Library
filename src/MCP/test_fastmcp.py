from fastmcp import FastMCP

# 创建服务器实例
server = FastMCP('test_server')

# 注册一个简单的工具
@server.tool
def hello(name: str = "World") -> str:
    """打招呼工具"""
    return f"Hello, {name}!"

# 检查工具是否注册
print("=== FastMCP 工具注册测试 ===")
print(f"服务器名称: {server.name}")

# 尝试调用工具
try:
    result = hello("FastMCP")
    print(f"工具调用结果: {result}")
    print("✓ 工具注册和调用成功")
except Exception as e:
    print(f"✗ 工具调用失败: {e}")

# 检查服务器属性
print("\n=== 服务器属性检查 ===")
for attr in dir(server):
    if not attr.startswith('_'):
        print(f"- {attr}")

print("\n测试完成")