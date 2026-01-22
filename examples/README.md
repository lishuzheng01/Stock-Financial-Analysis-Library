# 示例文件说明

本目录包含了股票财务分析库的使用示例。

## 文件说明

### basic_workflow.py
完整的工作流示例，展示如何使用本库进行全面的股票财务分析。

**功能特性**：
- 数据缓存机制，避免重复API调用
- 完整的日志记录
- 自动生成分析报告
- 涵盖所有21个分析函数

**使用方法**：
```bash
python examples/basic_workflow.py
```

### parallel_workflow.py
高性能优化版工作流，支持多线程并行处理。

**功能特性**：
- 多线程并行分析
- 更快的执行速度
- 适合批量分析多只股票

**使用方法**：
```bash
python examples/parallel_workflow.py
```

### quick_test.py
快速测试脚本，用于验证库的基本功能。

**使用方法**：
```bash
python examples/quick_test.py
```

## 注意事项

1. 首次运行需要从API获取数据，可能需要较长时间
2. 数据会缓存在`cache/`目录中
3. 生成的报告保存在`reports/`目录中
4. 请遵守API使用限制，避免频繁请求
