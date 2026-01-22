# 项目结构说明

## 重构后的目录结构

```
Stocking/
├── src/                          # 源代码目录
│   └── stock_tool/               # 核心包
│       ├── __init__.py           # 包入口，导出所有公共API
│       ├── get_stock_data.py     # 股票价格数据获取
│       ├── get_report_data.py    # 财务报表数据获取
│       ├── AltmanZScore.py       # Altman Z-Score破产风险分析
│       ├── BeneishMScore.py      # Beneish M-Score财务造假检测
│       ├── CheckBenford.py       # Benford定律数据真实性验证
│       ├── DuPontAnalysis.py     # 杜邦分析（3因素和5因素）
│       ├── ProfitabilityAnalysis.py  # 盈利能力分析
│       ├── ValuationRatios.py    # 估值比率分析
│       └── CashFlowAnalysis.py   # 现金流分析
│
├── test/                         # 测试目录
│   ├── __init__.py               # 测试包初始化
│   ├── test_all.py               # 综合测试套件（6个测试类别）
│   └── test_get_report.py        # 报表数据获取脚本
│
├── examples/                     # 示例目录
│   ├── README.md                 # 示例使用说明
│   ├── basic_workflow.py         # 完整工作流示例
│   ├── parallel_workflow.py      # 高性能并行工作流
│   └── quick_test.py             # 快速测试脚本
│
├── docs/                         # 文档目录
│   ├── PROJECT_STRUCTURE.md      # 项目结构说明（本文件）
│   ├── TESTING.md                # 测试文档
│   └── report_header.txt         # 报告头模板
│
├── cache/                        # 数据缓存目录（.gitignore）
├── reports/                      # 报告输出目录（.gitignore）
│
├── .gitignore                    # Git忽略配置
├── LICENSE                       # MIT许可证
├── readme.md                     # 项目主文档
├── CHANGELOG.md                  # 更新日志
├── setup.py                      # 安装脚本
├── pyproject.toml                # 项目配置
├── pytest.ini                    # pytest配置
└── requirements.txt              # 依赖列表
```

## 重构改进

### 1. 清理冗余文件
- 删除了空文件 `nul`
- 删除了日志文件 `stock_analysis_workflow.log`
