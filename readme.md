# Stock Financial Analysis Library

一个纯Python的中国股票财务分析库,提供全面的财务指标计算和风险分析功能。

## 功能特性

### 数据获取
- 多数据源股票价格数据 (akshare + yfinance)
- 财务报表数据获取 (资产负债表/利润表/现金流量表)

### 风险分析
- Altman Z-Score 破产风险分析
- Beneish M-Score 财务造假检测
- Benford's Law 数据真实性验证

### 财务分析
- **杜邦分析**: 3因素和5因素ROE分解
- **盈利能力**: 毛利率/净利率/ROE/ROA/ROIC
- **估值分析**: PE/PB/PS/PEG/EV/EBITDA
- **现金流分析**: 经营现金流质量/自由现金流/充足率/周期

## 安装

### 使用pip
```bash
pip install -e .
```

### 手动安装依赖
```bash
pip install -r requirements.txt
```

## 快速开始

### 1. 数据获取

```python
from stock_tool import get_stock_data, get_report_data

# 获取股票价格数据
price_data = get_stock_data("600519", "20230101", "20231231", source='auto')

# 获取财务报表
balance_sheet = get_report_data("600519", "资产负债表", source='akshare')
income_statement = get_report_data("600519", "利润表")
cashflow = get_report_data("600519", "现金流量表")
```

### 2. 风险分析

```python
from stock_tool import analyze_altman_zscore, analyze_beneish_mscore

# Altman Z-Score 破产风险
results_df, report = analyze_altman_zscore("600519")
print(report)

# Beneish M-Score 造假风险
results_df, report = analyze_beneish_mscore("600519")
print(report)
```

### 3. 杜邦分析

```python
from stock_tool import analyze_dupont_roe_3factor, analyze_dupont_roe_5factor

# 3因素杜邦分析
results_df, report = analyze_dupont_roe_3factor("600519")

# 5因素杜邦分析
results_df, report = analyze_dupont_roe_5factor("600519")
```

### 4. 盈利能力分析

```python
from stock_tool import (
    analyze_gross_margin,
    analyze_net_margin,
    analyze_roe,
    analyze_roa,
    analyze_roic
)

# 毛利率分析
results_df, report = analyze_gross_margin("600519")

# ROE分析
results_df, report = analyze_roe("600519")
```

### 5. 估值分析

```python
from stock_tool import (
    analyze_pe_ratio,
    analyze_pb_ratio,
    analyze_ps_ratio,
    analyze_peg_ratio,
    analyze_ev_ebitda
)

# PE市盈率分析
results_df, report = analyze_pe_ratio("600519")

# PEG分析
results_df, report = analyze_peg_ratio("600519")
```

### 6. 现金流分析

```python
from stock_tool import (
    analyze_operating_cashflow_quality,
    analyze_free_cashflow,
    analyze_cashflow_adequacy,
    analyze_cash_conversion_cycle
)

# 经营现金流质量
results_df, report = analyze_operating_cashflow_quality("600519")

# 自由现金流分析
results_df, report = analyze_free_cashflow("600519")
```

## API文档

### 数据获取函数

#### get_stock_data(stock, start, end, source='auto')
获取股票价格数据

**参数**:
- `stock`: 股票代码 (A股6位数字,如600519; 港股如0700.HK; 美股如AAPL)
- `start`: 开始日期 (YYYYMMDD格式)
- `end`: 结束日期 (YYYYMMDD格式)
- `source`: 数据源 ('auto'/'akshare'/'yfinance')

**返回**: pandas.DataFrame

#### get_report_data(stock, symbol, transpose=True, source='auto')
获取财务报表数据

**参数**:
- `stock`: 股票代码
- `symbol`: 报表类型 ("资产负债表"/"利润表"/"现金流量表")
- `transpose`: 是否转置数据
- `source`: 数据源

**返回**: pandas.DataFrame

### 分析函数返回值
所有分析函数返回 `(DataFrame, str)` 元组:
- `DataFrame`: 详细计算结果数据
- `str`: 格式化的分析报告文本

## 数据源说明

| 数据源 | 行情数据 | 财报数据 | 备注 |
|--------|---------|---------|------|
| akshare | ✅ A股 | ✅ A股 | 默认数据源 |
| yfinance | ✅ 全球 | ❌ 不支持A股财报 | 行情数据备援 |

## 依赖要求

- Python >= 3.8
- pandas >= 1.3.0
- numpy >= 1.20.0
- akshare >= 1.10.0
- yfinance >= 0.2.0

## 许可证

MIT License

## 贡献

欢迎提交Issue和Pull Request!
