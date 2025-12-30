# Altman Z-Score 分析工具
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

# Beneish M-Score 分析工具
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

# 获取股票数据
from stock_tool.get_stock_data import get_stock_data
# 获取股票数据（例如：600519 贵州茅台）
stock_data = get_stock_data("600519")
# 查看数据前五行
print(stock_data.head())

# 检查股票数据的 Benford 分布
from stock_tool.check_benford import check_benford
check_benford(stock_data)
