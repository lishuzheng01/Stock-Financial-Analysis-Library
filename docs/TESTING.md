# 测试套件使用说明

## 概述

本测试套件用于验证所有股票财务分析工具的功能完整性。测试涵盖了21个函数，分为6大类别。

## 运行测试

```bash
python test/test_all.py
```

## 核心特性

### 1. **数据预加载缓存机制** ⭐️

为了避免API速率限制，测试套件在开始时会预先加载所有需要的财务数据：

- 股票价格数据
- 资产负债表
- 利润表
- 现金流量表

**优势：**
- 只调用API一次，避免重复请求
- 大幅减少测试时间
- 防止触发AKShare速率限制

### 2. **测试覆盖范围**

#### Category A: 数据获取 (6个测试)
- `get_stock_data` - 股票价格数据
- `get_report_data` - 财务报表数据（资产负债表、利润表）

#### Category B: 风险分析 (4个测试)
- `analyze_altman_zscore` - Altman Z-Score破产风险
- `BeneishMScore_check` - Beneish M-Score财务操纵检测
- `check_benford` - 本福特定律分析

#### Category C: 盈利能力分析 (10个测试)
- `analyze_gross_margin` - 毛利率
- `analyze_net_margin` - 净利率
- `analyze_roe` - 净资产收益率
- `analyze_roa` - 总资产收益率
- `analyze_roic` - 投资资本回报率

#### Category D: 杜邦分析 (4个测试)
- `analyze_dupont_roe_3factor` - 三因素杜邦分析
- `analyze_dupont_roe_5factor` - 五因素杜邦分析

#### Category E: 估值比率 (10个测试)
- `analyze_pe_ratio` - 市盈率
- `analyze_pb_ratio` - 市净率
- `analyze_ps_ratio` - 市销率
- `analyze_peg_ratio` - PEG比率
- `analyze_ev_ebitda` - EV/EBITDA

#### Category F: 现金流分析 (8个测试)
- `analyze_operating_cashflow_quality` - 经营现金流质量
- `analyze_free_cashflow` - 自由现金流
- `analyze_cashflow_adequacy` - 现金流充足性
- `analyze_cash_conversion_cycle` - 现金周转周期

### 3. **测试股票**

默认测试两只股票：
- **600519** - 贵州茅台
- **000858** - 五粮液

可在配置中修改：
```python
TEST_STOCKS = ["600519", "000858"]
```

### 4. **输出格式**

测试输出采用适中详细程度：

**成功测试示例：**
```
[PASS] analyze_gross_margin [600519]
  Shape: 12 rows × 7 columns
  Latest metrics:
    - Gross Margin (%): 91.29
  First 3 periods:
    [显示前3期数据]
```

**失败测试示例：**
```
[FAIL] analyze_pb_ratio [000858]
  Error: Empty DataFrame
```

### 5. **测试摘要**

测试结束时显示完整摘要：
```
TEST SUMMARY
Total Tests: 42
Passed: 27 [PASS]
Failed: 15 [FAIL]
Success Rate: 64.3%

Failed Tests Details:
  [FAIL] analyze_pb_ratio [000858]
    Empty DataFrame
```

## 配置选项

### 修改测试股票

编辑 `test/test_all.py`：
```python
TEST_STOCKS = ["600519", "000001", "000002"]  # 添加更多股票
```

### 修改日期范围

```python
DATE_RANGE = ("20200101", "20241231")  # 调整日期范围
```

## 常见问题

### Q: 为什么有些测试失败？

**A:** 主要原因包括：
1. **API速率限制** - AKShare可能限制请求频率
2. **数据不可用** - 某些股票特定时期的数据可能缺失
3. **网络问题** - 临时网络连接问题

解决方法：
- 等待几分钟后重试
- 检查网络连接
- 使用数据缓存机制（已内置）

### Q: 如何只测试特定类别？

**A:** 注释掉 `run_all_tests()` 中不需要的测试：
```python
def run_all_tests():
    # ...
    test_data_acquisition()
    test_risk_analysis()
    # test_profitability_analysis()  # 跳过这个
    # test_dupont_analysis()         # 跳过这个
    # ...
```

### Q: 测试运行需要多长时间？

**A:**
- **有缓存**: 约2-5分钟（推荐）
- **无缓存**: 约10-15分钟（可能遇到速率限制）

## 技术细节

### 数据缓存机制

测试套件使用全局字典缓存数据：

```python
data_cache = {
    "stock_data": {},       # {stock: DataFrame}
    "balance_sheet": {},    # {stock: DataFrame}
    "income_statement": {}, # {stock: DataFrame}
    "cashflow_statement": {}  # {stock: DataFrame}
}
```

在 `preload_all_data()` 中一次性加载所有数据，后续测试直接使用缓存，避免重复API调用。

### 错误处理

每个测试都有完善的错误处理：
```python
try:
    result = function_to_test(params)
    # 验证结果
except Exception as e:
    # 记录错误但继续测试
```

## 开发说明

### 添加新测试

1. 在相应的测试函数中添加测试逻辑
2. 确保使用 `print_test_result()` 报告结果
3. 更新 `test_results` 计数器

示例：
```python
def test_new_category():
    print_section_header("Category X: New Analysis")

    for stock in TEST_STOCKS:
        success, result = safe_test(new_function, stock, print_output=False)

        if success:
            df, report_text = result
            if validate_dataframe(df):
                key_metrics = extract_key_metrics(df, ["Metric1", "Metric2"])
                print_test_result("new_function", stock, True, df, key_metrics=key_metrics)
                test_results["passed"] += 1
            else:
                print_test_result("new_function", stock, False, error_msg="Empty DataFrame")
                test_results["failed"] += 1
        else:
            print_test_result("new_function", stock, False, error_msg=result)
            test_results["failed"] += 1
```

### 调试模式

如需查看详细错误信息，修改日志级别：
```python
import logging
logging.basicConfig(level=logging.DEBUG)
```

## 最佳实践

1. **定期运行测试** - 在修改代码后运行测试确保功能正常
2. **关注失败测试** - 分析失败原因，区分代码问题和数据问题
3. **使用缓存** - 充分利用内置缓存机制避免API限制
4. **记录结果** - 保存测试输出用于对比分析

## 文件结构

```
test/
├── test_all.py           # 主测试文件
└── README_测试说明.md    # 本说明文档
```

## 更新日志

### v1.1 (当前版本)
- ✅ 添加数据预加载缓存机制
- ✅ 优化输出格式（ASCII兼容）
- ✅ 改进错误处理
- ✅ 添加测试摘要报告

### v1.0
- ✅ 初始版本
- ✅ 覆盖21个函数
- ✅ 支持多股票测试

## 贡献

如需改进测试套件，请：
1. 保持代码简洁易读
2. 确保所有测试独立运行
3. 添加适当的注释
4. 更新本文档

---

**注意：** 所有调试和打印代码仅存在于测试文件中，不会影响原始计算模块。
