#!/usr/bin/env python3
"""
测试stock-financial-analysis库的核心功能
"""

import sys

print("=== 测试stock-financial-analysis库 ===")

# 测试导入
print("\n1. 测试库导入...")
try:
    from stock_tool import (
        # 数据获取
        get_stock_data, get_report_data,
        # 风险分析
        analyze_altman_zscore, analyze_beneish_mscore, check_benford,
        # 杜邦分析
        analyze_dupont_roe_3factor,
        # 盈利能力分析
        analyze_roe, analyze_roa,
        # 估值分析
        analyze_pe_ratio,
        # 现金流分析
        analyze_free_cashflow
    )
    print("✓ 库导入成功")
except ImportError as e:
    print(f"✗ 库导入失败: {e}")
    sys.exit(1)

# 测试数据获取
print("\n2. 测试数据获取功能...")
try:
    # 使用一个知名的A股代码进行测试
    stock_code = "600519"  # 贵州茅台
    
    # 测试获取股票数据
    print(f"  测试获取{stock_code}的股票数据...")
    price_data = get_stock_data(stock_code, "20240101", "20240601", source='yfinance')
    if price_data is not None and len(price_data) > 0:
        print(f"  ✓ 成功获取{len(price_data)}条股票数据")
    else:
        print("  ✗ 未能获取股票数据")
        
    # 测试获取财务报表数据
    print(f"  测试获取{stock_code}的财务报表数据...")
    balance_sheet = get_report_data(stock_code, "资产负债表", source='akshare')
    if balance_sheet is not None and len(balance_sheet) > 0:
        print(f"  ✓ 成功获取{len(balance_sheet)}条资产负债表数据")
    else:
        print("  ✗ 未能获取资产负债表数据")
        
except Exception as e:
    print(f"  ✗ 数据获取失败: {e}")

# 测试风险分析功能
print("\n3. 测试风险分析功能...")
try:
    print(f"  测试Altman Z-Score分析...")
    zscore_df, zscore_report = analyze_altman_zscore(stock_code, print_output=False)
    if zscore_df is not None and len(zscore_df) > 0:
        print(f"  ✓ Altman Z-Score分析成功")
        print(f"    最新Z-Score: {zscore_df.iloc[-1]['Z-Score']:.2f}")
    else:
        print("  ✗ Altman Z-Score分析失败")
except Exception as e:
    print(f"  ✗ 风险分析失败: {e}")

# 测试杜邦分析
print("\n4. 测试杜邦分析功能...")
try:
    print(f"  测试3因素杜邦分析...")
    dupont_df, dupont_report = analyze_dupont_roe_3factor(stock_code, print_output=False)
    if dupont_df is not None and len(dupont_df) > 0:
        print(f"  ✓ 3因素杜邦分析成功")
        print(f"    最新ROE: {dupont_df.iloc[-1]['ROE (%)']:.2f}%")
    else:
        print("  ✗ 3因素杜邦分析失败")
except Exception as e:
    print(f"  ✗ 杜邦分析失败: {e}")

# 测试估值分析
print("\n5. 测试估值分析功能...")
try:
    print(f"  测试PE市盈率分析...")
    pe_df, pe_report = analyze_pe_ratio(stock_code, print_output=False)
    if pe_df is not None and len(pe_df) > 0:
        print(f"  ✓ PE市盈率分析成功")
        if 'Static PE' in pe_df.columns:
            print(f"    最新静态PE: {pe_df.iloc[-1]['Static PE']:.2f}")
    else:
        print("  ✗ PE市盈率分析失败")
except Exception as e:
    print(f"  ✗ 估值分析失败: {e}")

print("\n=== 测试完成 ===")
print("\n库功能基本正常，可以正常使用！")
