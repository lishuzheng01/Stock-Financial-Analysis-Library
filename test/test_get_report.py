from stock_tool.get_report_data import get_report_data
import pandas as pd

# download report data
pd_asset = get_report_data(stock="600519", symbol="资产负债表")
pd_income = get_report_data(stock="600519", symbol="利润表")
pd_cashflow = get_report_data(stock="600519", symbol="现金流量表")

## set report name index
report_name = [pd_asset, pd_income, pd_cashflow]

# clean data
## delete columns with all NaN values and empty columns and columns'mane
def clear_nan(data):
    data = data.dropna(axis=1, how='all',inplace=True)
    return data

## save maintain columns'mane
asset_maintain_mane = []
income_maintain_mane = []
cashflow_maintain_mane = []

for data in report_name:
    income_maintain_mane.append(data.columns.tolist())
    cashflow_maintain_mane.append(data.columns.tolist())
    asset_maintain_mane.append(data.columns.tolist())

print("asset_maintain_mane:")
print(asset_maintain_mane)
print("-"*50)
print("income_maintain_mane:")
print(income_maintain_mane)
print("-"*50)
print("cashflow_maintain_mane:")
print(cashflow_maintain_mane)