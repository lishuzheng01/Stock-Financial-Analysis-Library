#!/usr/bin/env python3
"""
股票分析 MCP 服务器工具测试脚本
"""

import sys
sys.path.append('..')

from stock_tool import get_stock_data, analyze_altman_zscore, BeneishMScore_check, check_benford

def test_stock_data():
    """测试股票数据获取功能"""
    print("=== 测试股票数据获取 ===")
    try:
        df = get_stock_data(stock="000001", start="20230101", end="20231231")
        if not df.empty:
            print(f"✓ 成功获取股票数据，共 {len(df)} 条记录")
            print(f"  最新收盘价: {df['close'].iloc[-1]:.2f}")
        else:
            print("✗ 获取股票数据失败")
    except Exception as e:
        print(f"✗ 错误: {e}")

def test_altman_zscore():
    """测试 Altman Z-Score 分析"""
    print("\n=== 测试 Altman Z-Score 分析 ===")
    try:
        data, report = analyze_altman_zscore("000001", print_output=False)
        if not data.empty:
            print("✓ Altman Z-Score 分析成功")
            print(f"  Z-Score 值: {data['Z-Score'].iloc[-1]:.2f}")
        else:
            print("✗ Altman Z-Score 分析失败")
    except Exception as e:
        print(f"✗ 错误: {e}")

def test_beneish_mscore():
    """测试 Beneish M-Score 分析"""
    print("\n=== 测试 Beneish M-Score 分析 ===")
    try:
        data, report = BeneishMScore_check("000001")
        if not data.empty:
            print("✓ Beneish M-Score 分析成功")
            print(f"  M-Score 值: {data['M-Score'].iloc[-1]:.2f}")
        else:
            print("✗ Beneish M-Score 分析失败")
    except Exception as e:
        print(f"✗ 错误: {e}")

def test_benford_law():
    """测试 Benford's Law 检查"""
    print("\n=== 测试 Benford's Law 检查 ===")
    try:
        # 首先获取股票数据，然后使用收盘价进行Benford检查
        df = get_stock_data(stock="000001", start="20230101", end="20231231")
        if not df.empty:
            close_prices = df['close']
            result = check_benford(close_prices)
            if result:
                print("✓ Benford's Law 检查成功")
                print("  数据质量检查完成")
            else:
                print("✗ Benford's Law 检查失败")
        else:
            print("✗ 无法获取股票数据用于Benford检查")
    except Exception as e:
        print(f"✗ 错误: {e}")

if __name__ == "__main__":
    print("股票分析工具功能测试")
    print("=" * 50)
    
    test_stock_data()
    test_altman_zscore()
    test_beneish_mscore()
    test_benford_law()
    
    print("\n" + "=" * 50)
    print("测试完成！")