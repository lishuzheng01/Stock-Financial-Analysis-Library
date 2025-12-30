# Changelog

## [1.0.0] - 2025-12-30

### 重大变更
- 🔄 **项目转型**: 从混合AI系统转换为纯Python金融计算库
- ❌ **移除**: 所有LangChain AI集成功能
- ❌ **移除**: MCP (Model Context Protocol) 协议层
- ❌ **移除**: 所有测试文件
- ✅ **保留**: 核心金融计算模块 (20个分析函数)

### 保留功能 (Core Financial Analysis)

#### 数据获取 (2个)
- `get_stock_data` - 多数据源股价数据
- `get_report_data` - 财报数据获取

#### 风险分析 (3个)
- `analyze_altman_zscore` - 破产风险
- `analyze_beneish_mscore` - 财务造假检测
- `check_benford` - 本福特定律验证

#### 杜邦分析 (2个)
- `analyze_dupont_roe_3factor` - 3因素ROE分解
- `analyze_dupont_roe_5factor` - 5因素ROE分解

#### 盈利能力分析 (5个)
- `analyze_gross_margin` - 毛利率
- `analyze_net_margin` - 净利率
- `analyze_roe` - ROE净资产收益率
- `analyze_roa` - ROA总资产收益率
- `analyze_roic` - ROIC投入资本回报率

#### 估值分析 (5个)
- `analyze_pe_ratio` - PE市盈率
- `analyze_pb_ratio` - PB市净率
- `analyze_ps_ratio` - PS市销率
- `analyze_peg_ratio` - PEG比率
- `analyze_ev_ebitda` - EV/EBITDA

#### 现金流分析 (4个)
- `analyze_operating_cashflow_quality` - 经营现金流质量
- `analyze_free_cashflow` - 自由现金流
- `analyze_cashflow_adequacy` - 现金流充足率
- `analyze_cash_conversion_cycle` - 现金循环周期

### 已删除功能
- AI报告生成系统
- LangChain Agent集成
- MCP协议服务器
- 自动化报告规划
- 所有测试文件

### 文件统计
- 删除代码量: ~46,500行
- 保留代码量: ~5,944行
- 删除比例: 89%
