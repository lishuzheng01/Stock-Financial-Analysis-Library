import sys
sys.path.append('..')

from server import server

# 检查服务器基本信息
print("=== MCP服务器配置检查 ===")
print(f"服务器名称: {server.name}")
print(f"服务器版本: {server.version}")
print(f"服务器说明: {server.instructions}")

# 检查工具注册情况
print("\n=== 注册的工具 ===")
tool_names = []
for attr_name in dir(server):
    if not attr_name.startswith('_'):
        attr = getattr(server, attr_name)
        # 检查是否是函数工具
        if hasattr(attr, '__name__') and hasattr(attr, '__wrapped__'):
            tool_names.append(attr_name)
            print(f"- {attr_name}")

print(f"\n总共注册了 {len(tool_names)} 个工具")

# 测试工具功能（可选）
print("\n=== 工具功能测试 ===")
try:
    # 测试股票数据获取工具
    result = server.get_stock_history("600519")
    print("✓ 股票数据获取工具测试成功")
    print(f"  结果: {result[:100]}...")
except Exception as e:
    print(f"✗ 股票数据获取工具测试失败: {e}")

try:
    # 测试Altman Z-Score工具
    result = server.analyze_altman_zscore_tool("600519")
    print("✓ Altman Z-Score工具测试成功")
    print(f"  结果: {result[:100]}...")
except Exception as e:
    print(f"✗ Altman Z-Score工具测试失败: {e}")

print("\n=== 服务器测试完成 ===")