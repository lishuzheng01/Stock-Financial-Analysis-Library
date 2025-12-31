# Stock Financial Analysis Library

一个纯Python的中国股票财务分析库，提供全面的财务指标计算和风险分析功能。

## 项目概述

### 项目名称

Stock Financial Analysis Library

### 一句话描述

一个功能全面、易用的纯Python股票财务分析库，专为中国A股市场设计，提供从数据获取到深度分析的完整解决方案。

### 目标用户

- 股票投资者：用于个股财务分析和风险评估
- 金融分析师：提高财务分析效率，生成标准化报告
- 量化研究者：作为量化策略开发的基础财务数据模块
- 金融专业学生：学习财务分析方法和Python应用

## 核心功能介绍

### 数据获取

- **多数据源支持**：集成akshare和yfinance，自动切换最优数据源
- **股票价格数据**：支持A股、港股、美股的历史行情数据获取
- **财务报表数据**：自动获取资产负债表、利润表、现金流量表
- **数据格式统一**：标准化输出格式，便于后续分析和处理

### 风险分析

- **Altman Z-Score**：经典破产风险预测模型，评估企业财务健康度
- **Beneish M-Score**：财务造假检测模型，识别可能的盈余管理行为
- **Benford's Law**：数据真实性验证，检测财务数据异常

### 财务分析

- **杜邦分析**：3因素和5因素ROE分解，深入分析盈利能力驱动因素
- **盈利能力**：毛利率、净利率、ROE、ROA、ROIC等核心指标计算
- **估值分析**：PE、PB、PS、PEG、EV/EBITDA等估值指标分析
- **现金流分析**：经营现金流质量、自由现金流、充足率、现金转换周期

## 技术栈说明

| 类别 | 技术/依赖 | 版本要求 | 用途 |
|------|-----------|----------|------|
| 编程语言 | Python | >= 3.8 | 核心开发语言 |
| 数据处理 | pandas | >= 1.3.0 | 数据结构和分析 |
| 数值计算 | numpy | >= 1.20.0 | 数学计算 |
| 数据获取 | akshare | >= 1.10.0 | A股数据获取 |
| 数据获取 | yfinance | >= 0.2.0 | 全球市场数据获取 |
| 网络请求 | requests | >= 2.26.0 | HTTP请求处理 |
| 网络请求 | urllib3 | >= 1.26.0 | HTTP客户端库 |
| 测试框架 | pytest | 最新版 | 单元测试和集成测试 |

## 环境搭建步骤

### 1. Python环境安装

#### Windows系统

1. 访问[Python官网](https://www.python.org/downloads/windows/)下载Python 3.8+安装包
2. 运行安装包，勾选"Add Python to PATH"
3. 选择"Customize installation"，确保勾选pip
4. 完成安装后，打开命令提示符验证：
   ```bash
   python --version
   pip --version
   ```

#### macOS系统

1. 推荐使用Homebrew安装：
   ```bash
   /bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"
   brew install python@3.10
   ```
2. 验证安装：
   ```bash
   python3 --version
   pip3 --version
   ```

#### Linux系统

1. 使用系统包管理器安装：
   ```bash
   # Ubuntu/Debian
   sudo apt update
   sudo apt install python3 python3-pip python3-venv
   
   # CentOS/RHEL
   sudo yum install python3 python3-pip
   ```
2. 验证安装：
   ```bash
   python3 --version
   pip3 --version
   ```

### 2. 虚拟环境创建（推荐）

```bash
# 创建虚拟环境
python -m venv venv

# 激活虚拟环境
# Windows
venv\Scripts\activate
# macOS/Linux
source venv/bin/activate

# 退出虚拟环境
deactivate
```

## 详细的安装与配置指南

### 方式一：使用pip安装

```bash
# 安装库（开发模式，便于修改）
pip install -e .

# 或直接安装（生产环境）
pip install stock-financial-analysis
```

### 方式二：手动安装依赖

```bash
# 克隆仓库
git clone https://github.com/your_username/stock-financial-analysis.git
cd stock-financial-analysis

# 安装依赖
pip install -r requirements.txt

# 安装库
pip install -e .
```

### 开发环境设置

```bash
# 安装开发依赖
pip install pytest pytest-cov black flake8

# 运行测试
pytest

# 运行测试并生成覆盖率报告
pytest --cov=stock_tool

# 代码格式化
black .

# 代码检查
flake8
```

## 使用方法及示例

### 1. 数据获取

```python
from stock_tool import get_stock_data, get_report_data

# 获取股票价格数据
price_data = get_stock_data("600519", "20230101", "20231231", source='auto')
print("股票价格数据:")
print(price_data.head())

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
```

### 2. 风险分析

```python
from stock_tool import analyze_altman_zscore, analyze_beneish_mscore, check_benford

# Altman Z-Score 破产风险分析
zscore_df, zscore_report = analyze_altman_zscore("600519")
print("Altman Z-Score分析结果:")
print(zscore_df)
print("\nZ-Score报告:")
print(zscore_report)

# Beneish M-Score 造假风险分析
mscore_df, mscore_report = analyze_beneish_mscore("600519")
print("\nBeneish M-Score分析结果:")
print(mscore_df)
print("\nM-Score报告:")
print(mscore_report)

# Benford's Law 数据真实性验证
benford_result = check_benford("600519", "利润表")
print("\nBenford's Law验证结果:")
print(benford_result)
```

### 3. 杜邦分析

```python
from stock_tool import analyze_dupont_roe_3factor, analyze_dupont_roe_5factor

# 3因素杜邦分析
roe3_df, roe3_report = analyze_dupont_roe_3factor("600519")
print("3因素杜邦分析结果:")
print(roe3_df)
print("\n3因素杜邦分析报告:")
print(roe3_report)

# 5因素杜邦分析
roe5_df, roe5_report = analyze_dupont_roe_5factor("600519")
print("\n5因素杜邦分析结果:")
print(roe5_df)
print("\n5因素杜邦分析报告:")
print(roe5_report)
```

### 4. 盈利能力分析

```python
from stock_tool import (
    analyze_gross_margin, analyze_net_margin,
    analyze_roe, analyze_roa, analyze_roic
)

# 毛利率分析
gross_df, gross_report = analyze_gross_margin("600519")
print("毛利率分析:")
print(gross_report)

# 净利率分析
net_df, net_report = analyze_net_margin("600519")
print("\n净利率分析:")
print(net_report)

# ROE分析
roe_df, roe_report = analyze_roe("600519")
print("\nROE分析:")
print(roe_report)

# ROA分析
roa_df, roa_report = analyze_roa("600519")
print("\nROA分析:")
print(roa_report)

# ROIC分析
roic_df, roic_report = analyze_roic("600519")
print("\nROIC分析:")
print(roic_report)
```

### 5. 估值分析

```python
from stock_tool import (
    analyze_pe_ratio, analyze_pb_ratio,
    analyze_ps_ratio, analyze_peg_ratio, analyze_ev_ebitda
)

# PE市盈率分析
pe_df, pe_report = analyze_pe_ratio("600519")
print("PE市盈率分析:")
print(pe_report)

# PB市净率分析
pb_df, pb_report = analyze_pb_ratio("600519")
print("\nPB市净率分析:")
print(pb_report)

# PS市销率分析
ps_df, ps_report = analyze_ps_ratio("600519")
print("\nPS市销率分析:")
print(ps_report)

# PEG分析
peg_df, peg_report = analyze_peg_ratio("600519")
print("\nPEG分析:")
print(peg_report)

# EV/EBITDA分析
evebitda_df, evebitda_report = analyze_ev_ebitda("600519")
print("\nEV/EBITDA分析:")
print(evebitda_report)
```

### 6. 现金流分析

```python
from stock_tool import (
    analyze_operating_cashflow_quality, analyze_free_cashflow,
    analyze_cashflow_adequacy, analyze_cash_conversion_cycle
)

# 经营现金流质量分析
opcf_df, opcf_report = analyze_operating_cashflow_quality("600519")
print("经营现金流质量分析:")
print(opcf_report)

# 自由现金流分析
fcf_df, fcf_report = analyze_free_cashflow("600519")
print("\n自由现金流分析:")
print(fcf_report)

# 现金流充足率分析
adequacy_df, adequacy_report = analyze_cashflow_adequacy("600519")
print("\n现金流充足率分析:")
print(adequacy_report)

# 现金转换周期分析
cycle_df, cycle_report = analyze_cash_conversion_cycle("600519")
print("\n现金转换周期分析:")
print(cycle_report)
```

### 7. 完整工作流示例

```python
from stock_tool import (
    get_stock_data, get_report_data,
    analyze_altman_zscore, analyze_beneish_mscore,
    analyze_dupont_roe_5factor, analyze_roic,
    analyze_pe_ratio, analyze_free_cashflow
)

# 定义股票代码和日期范围
stock_code = "600519"
start_date = "20200101"
end_date = "20231231"

print(f"=== {stock_code} 完整财务分析报告 ===")

# 1. 获取基础数据
print("\n1. 获取基础数据...")
price_data = get_stock_data(stock_code, start_date, end_date)
balance_sheet = get_report_data(stock_code, "资产负债表")
income_statement = get_report_data(stock_code, "利润表")
cashflow = get_report_data(stock_code, "现金流量表")

# 2. 风险分析
print("\n2. 风险分析...")
_, zscore_report = analyze_altman_zscore(stock_code)
print("\nAltman Z-Score报告:")
print(zscore_report)

_, mscore_report = analyze_beneish_mscore(stock_code)
print("\nBeneish M-Score报告:")
print(mscore_report)

# 3. 财务核心分析
print("\n3. 财务核心分析...")
_, roe_report = analyze_dupont_roe_5factor(stock_code)
print("\n5因素杜邦分析报告:")
print(roe_report)

_, roic_report = analyze_roic(stock_code)
print("\nROIC分析报告:")
print(roic_report)

# 4. 估值分析
print("\n4. 估值分析...")
_, pe_report = analyze_pe_ratio(stock_code)
print("\nPE市盈率分析报告:")
print(pe_report)

# 5. 现金流分析
print("\n5. 现金流分析...")
_, fcf_report = analyze_free_cashflow(stock_code)
print("\n自由现金流分析报告:")
print(fcf_report)

print("\n=== 分析完成 ===")
```

## API接口文档

### 1. 数据获取函数

#### get_stock_data(stock, start, end, source='auto')

获取股票价格数据。

**参数**:
- `stock`: 股票代码 (A股6位数字,如600519; 港股如0700.HK; 美股如AAPL)
- `start`: 开始日期 (YYYYMMDD格式)
- `end`: 结束日期 (YYYYMMDD格式)
- `source`: 数据源 ('auto'/'akshare'/'yfinance'), 默认自动选择

**返回**:
- `pandas.DataFrame`: 包含日期、开盘价、收盘价、最高价、最低价、成交量等字段的行情数据

#### get_report_data(stock, symbol, transpose=True, source='auto')

获取财务报表数据。

**参数**:
- `stock`: 股票代码
- `symbol`: 报表类型 ("资产负债表"/"利润表"/"现金流量表")
- `transpose`: 是否转置数据, 默认True
- `source`: 数据源, 默认自动选择

**返回**:
- `pandas.DataFrame`: 财务报表数据

### 2. 风险分析函数

#### analyze_altman_zscore(stock)

计算Altman Z-Score破产风险指标。

**参数**:
- `stock`: 股票代码

**返回**:
- `(pandas.DataFrame, str)`: 详细计算结果和格式化报告

#### analyze_beneish_mscore(stock)

计算Beneish M-Score财务造假风险指标。

**参数**:
- `stock`: 股票代码

**返回**:
- `(pandas.DataFrame, str)`: 详细计算结果和格式化报告

#### check_benford(stock, report_type)

使用Benford定律验证财务数据真实性。

**参数**:
- `stock`: 股票代码
- `report_type`: 报表类型 ("资产负债表"/"利润表"/"现金流量表")

**返回**:
- `dict`: 包含拟合度、异常值等验证结果

### 3. 财务分析函数

#### 杜邦分析

- `analyze_dupont_roe_3factor(stock)`: 3因素杜邦分析
- `analyze_dupont_roe_5factor(stock)`: 5因素杜邦分析

**参数**:
- `stock`: 股票代码

**返回**:
- `(pandas.DataFrame, str)`: 详细计算结果和格式化报告

#### 盈利能力分析

- `analyze_gross_margin(stock)`: 毛利率分析
- `analyze_net_margin(stock)`: 净利率分析
- `analyze_roe(stock)`: 净资产收益率分析
- `analyze_roa(stock)`: 总资产收益率分析
- `analyze_roic(stock)`: 投入资本回报率分析

**参数**:
- `stock`: 股票代码

**返回**:
- `(pandas.DataFrame, str)`: 详细计算结果和格式化报告

#### 估值分析

- `analyze_pe_ratio(stock)`: PE市盈率分析
- `analyze_pb_ratio(stock)`: PB市净率分析
- `analyze_ps_ratio(stock)`: PS市销率分析
- `analyze_peg_ratio(stock)`: PEG分析
- `analyze_ev_ebitda(stock)`: EV/EBITDA分析

**参数**:
- `stock`: 股票代码

**返回**:
- `(pandas.DataFrame, str)`: 详细计算结果和格式化报告

#### 现金流分析

- `analyze_operating_cashflow_quality(stock)`: 经营现金流质量分析
- `analyze_free_cashflow(stock)`: 自由现金流分析
- `analyze_cashflow_adequacy(stock)`: 现金流充足率分析
- `analyze_cash_conversion_cycle(stock)`: 现金转换周期分析

**参数**:
- `stock`: 股票代码

**返回**:
- `(pandas.DataFrame, str)`: 详细计算结果和格式化报告

### 4. 返回值说明

所有分析函数均返回 `(DataFrame, str)` 元组:
- **DataFrame**: 包含年度/季度的详细计算结果，便于进一步分析和可视化
- **str**: 格式化的分析报告文本，包含指标解释、趋势分析和风险提示

## 项目目录结构说明

```
stock-financial-analysis/
├── src/
│   └── stock_tool/
│       ├── __init__.py           # 包入口，导出所有公共函数
│       ├── get_stock_data.py      # 股票价格数据获取
│       ├── get_report_data.py     # 财务报表数据获取
│       ├── AltmanZScore.py        # Altman Z-Score实现
│       ├── BeneishMScore.py       # Beneish M-Score实现
│       ├── DuPontAnalysis.py      # 杜邦分析实现
│       ├── ProfitabilityAnalysis.py # 盈利能力分析
│       ├── ValuationRatios.py     # 估值比率分析
│       ├── CashFlowAnalysis.py    # 现金流分析
│       └── check_benford.py       # Benford定律验证
├── test/
│   ├── __init__.py
│   ├── test_all.py                # 综合测试
│   └── test_get_report.py         # 报表数据获取测试
├── .gitignore                     # Git忽略文件配置
├── CHANGELOG.md                   # 版本变更记录
├── LICENSE                        # MIT许可证
├── pyproject.toml                 # 项目配置
├── pytest.ini                     # pytest配置
├── README.md                      # 项目说明文档
├── requirements.txt               # 依赖列表
└── setup.py                       # 安装配置
```

### 核心文件说明

- **src/stock_tool/__init__.py**: 定义了包的公共API，所有对外函数都从这里导出
- **src/stock_tool/get_stock_data.py**: 实现多数据源股票价格获取逻辑
- **src/stock_tool/get_report_data.py**: 实现财务报表数据获取和格式标准化
- **src/stock_tool/AltmanZScore.py**: 实现Altman Z-Score计算和分析
- **src/stock_tool/DuPontAnalysis.py**: 实现3因素和5因素杜邦分析
- **test/**: 包含所有测试文件，确保代码质量和功能正确性

## 贡献指南

### 开发流程

1. Fork仓库到自己的GitHub账户
2. 创建新的功能分支：`git checkout -b feature/your-feature-name`
3. 实现功能并编写测试用例
4. 运行测试确保通过：`pytest`
5. 提交代码并推送到自己的仓库
6. 创建Pull Request到主仓库

### 代码规范

- 遵循PEP 8编码规范
- 使用black进行代码格式化
- 使用flake8进行代码检查
- 函数和类使用明确的文档字符串
- 添加适当的注释说明复杂逻辑

### 测试要求

- 所有新功能必须添加对应的测试用例
- 测试覆盖率要求达到80%以上
- 使用pytest框架编写测试
- 测试用例应该覆盖正常情况和异常情况

### Pull Request指南

- 标题清晰描述所做的更改
- 描述中说明功能实现和解决的问题
- 确保所有测试通过
- 提供使用示例（如果适用）
- 遵循代码审查反馈进行修改

## 许可证信息

本项目采用MIT许可证，详情请查看[LICENSE](LICENSE)文件。

## 联系方式

- **GitHub仓库**: https://github.com/your_username/stock-financial-analysis
- **Issue提交**: https://github.com/your_username/stock-financial-analysis/issues
- **反馈邮箱**: your_email@example.com

## 版本历史

### v1.0.0 (2024-01-01)

- 初始版本发布
- 实现核心功能：数据获取、风险分析、财务分析
- 支持A股市场数据

### v1.1.0 (2024-03-15)

- 添加多数据源支持（akshare + yfinance）
- 优化数据获取逻辑
- 增加现金流分析功能

### v1.2.0 (2024-06-30)

- 增强风险分析模块
- 添加Benford's Law验证
- 优化报告生成功能

## 常见问题

### Q: 为什么获取不到某些股票的数据？

A: 可能的原因包括：
- 股票代码格式不正确（请使用6位数字，如600519）
- 数据源暂时不可用（尝试切换数据源）
- 该股票可能已退市或暂停交易

### Q: 如何处理API速率限制？

A: 库内部已实现了自动重试和速率控制机制，建议：
- 避免短时间内频繁请求大量数据
- 合理设置请求间隔
- 考虑缓存已获取的数据

### Q: 可以用于港股或美股分析吗？

A: 是的，支持港股和美股的价格数据获取，但财务报表分析主要针对A股市场。

### Q: 如何贡献代码？

A: 请参考贡献指南部分，按照开发流程提交Pull Request。

## 致谢

- 感谢akshare和yfinance提供的数据源支持
- 感谢所有为项目做出贡献的开发者
- 感谢用户的反馈和建议，帮助我们不断改进

---

**Stock Financial Analysis Library** - 让财务分析变得简单高效！
