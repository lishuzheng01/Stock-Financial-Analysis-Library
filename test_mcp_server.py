#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import sys
import subprocess
import time

# 测试 MCP 服务器启动
print("测试 MCP 服务器启动...")

# 启动 MCP 服务器进程
process = subprocess.Popen(
    ["d:/Files/Code/Stocking/.conda/python.exe", "d:/Files/Code/Stocking/src/MCP/server.py"],
    stdin=subprocess.PIPE,
    stdout=subprocess.PIPE,
    stderr=subprocess.PIPE,
    text=True,
    bufsize=1,
    universal_newlines=True,
    encoding='utf-8'
)

# 等待服务器启动
time.sleep(2)

# 检查进程状态
if process.poll() is not None:
    # 进程已退出，读取错误输出
    stdout, stderr = process.communicate()
    print("MCP 服务器已退出")
    print("STDOUT:", stdout)
    print("STDERR:", stderr)
else:
    # 进程仍在运行
    print("MCP 服务器仍在运行")
    
    # 尝试发送简单的 JSON-RPC 初始化消息
    init_message = '{"jsonrpc": "2.0", "id": 1, "method": "initialize", "params": {}}'
    process.stdin.write(init_message + '\n')
    process.stdin.flush()
    
    # 读取响应
    time.sleep(1)
    try:
        response = process.stdout.readline()
        print("服务器响应:", response)
    except Exception as e:
        print("读取响应失败:", e)
    
    # 终止进程
    process.terminate()
    process.wait()

print("测试完成")