from stock_tool import get_report_data
import pandas as pd

# 获取资产负债表
balance_sheet = get_report_data("600519", "资产负债表", source='akshare')
print("\n资产负债表:")
print(balance_sheet.head())

# 获取利润表
income_statement = get_report_data("600519", "利润表")
print("\n利润表:")
print(income_statement.head())

# 获取现金流量表
cashflow = get_report_data("600519", "现金流量表")
print("\n现金流量表:")
print(cashflow.head())

# 分别保存表头
balance_sheet_headers = balance_sheet.columns.tolist()
income_statement_headers = income_statement.columns.tolist()
cashflow_headers = cashflow.columns.tolist()

print("\n资产负债表表头:")
print(balance_sheet_headers)
print("\n利润表表头:")
print(income_statement_headers)
print("\n现金流量表表头:")
print(cashflow_headers)