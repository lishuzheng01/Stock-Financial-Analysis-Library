
# Altman Z-Score 分析工具

```python
from stock_tool.AltmanZScore import analyze_altman_zscore
# 获取数据和报告
data, report = analyze_altman_zscore("600519")
# 访问数据
latest_zscore = data.iloc[0]['Z-Score']
# 保存报告到文件
with open('report.txt', 'w', encoding='utf-8') as f:
    f.write(report)
# 不打印到控制台，静默模式
data, report = analyze_altman_zscore("600519", print_output=False)
```

# Beneish M-Score 分析工具

``` python
# 从其他文件导入
from stock_tool.BeneishMScore import analyze_beneish_mscore

# 获取数据和报告（打印输出）
data, report = analyze_beneish_mscore("600519")

# 访问数据
latest_mscore = data.iloc[-1]['M-Score']

# 保存报告到文件
with open('report.txt', 'w', encoding='utf-8') as f:
    f.write(report)

# 静默模式（不打印任何输出）
data, report = analyze_beneish_mscore("600519", print_output=False)

```

```python
# get stock data
from stock_tool.StockData import get_stock_data
# 获取股票数据（例如：600519 贵州茅台）
获取股票数据并处理为 Backtrader 格式
    参数:
        stock: 股票代码
        start: 开始日期 (YYYYMMDD)
        end: 结束日期 (YYYYMMDD)
    返回:
        df = df[['open', 'high', 'low', 'close', 'volume']].astype(float)
    Demo:
    df = get_stock_data(stock="600519", start="20200101", end="20240101")
    # 查看数据前五行
    print(df.head())

```

```python
# get stock data
from stock_tool.StockData import get_stock_data
# 获取股票数据（例如：600519 贵州茅台）
stock_data = get_stock_data("600519")
# 查看数据前五行
print(stock_data.head())

```

```python
# check_benford
from stock_tool.BenfordCheck import check_benford
# 检查股票数据的 Benford 分布
check_benford(stock_data)
```