# -*- coding: utf-8 -*-
"""
杜邦分析体系 - DuPont Analysis System
ROE深度分析: 三因素模型和五因素模型
ROE Deep Analysis: 3-Factor and 5-Factor Models
"""

import sys
import os
from pathlib import Path
import pandas as pd
import numpy as np
from datetime import datetime

# 添加项目路径
sys.path.insert(0, str(Path(__file__).parent.parent))

from stock_tool.get_stock_data import get_stock_data
from stock_tool.get_report_data import get_report_data


class DuPontAnalysis:
    """
    杜邦分析类
    DuPont Analysis Class

    实现三因素和五因素ROE分解模型
    Implements 3-Factor and 5-Factor ROE decomposition models
    """

    def __init__(self, stock_code, model_type="3factor", silent=False):
        """
        初始化

        Args:
            stock_code: 股票代码
            model_type: 模型类型 ("3factor" or "5factor")
            silent: 是否静默模式 (不打印加载信息)
        """
        self.stock_code = stock_code
        self.model_type = model_type
        self.silent = silent
        self.pd_asset = None
        self.pd_income = None
        self.results = None

    def load_data(self):
        """加载财务数据"""
        if not self.silent:
            print(f"正在加载股票 {self.stock_code} 的财务数据...")

        self.pd_asset = get_report_data(
            stock=self.stock_code,
            symbol="资产负债表",
            transpose=True
        )

        self.pd_income = get_report_data(
            stock=self.stock_code,
            symbol="利润表",
            transpose=True
        )

        if not self.silent:
            print("数据加载完成!")

    def get_column(self, df, cn_name, en_name):
        """
        灵活获取列名 (支持中英文)

        Args:
            df: DataFrame
            cn_name: 中文列名
            en_name: 英文列名

        Returns:
            列名 or None
        """
        if cn_name in df.columns:
            return cn_name
        elif en_name in df.columns:
            return en_name
        return None

    def get_value(self, df, idx, cn_name, en_name, default=0.0):
        """
        安全获取值 (支持中英文列名)

        Args:
            df: DataFrame
            idx: 索引位置
            cn_name: 中文列名
            en_name: 英文列名
            default: 默认值

        Returns:
            float值
        """
        col = self.get_column(df, cn_name, en_name)
        if col and idx < len(df):
            value = df.iloc[idx][col]
            if pd.notna(value) and value != '' and value is not None:
                try:
                    return float(value)
                except:
                    return default
        return default

    def calculate_roe_3factor(self):
        """
        计算三因素杜邦分析
        ROE = 净利率 × 总资产周转率 × 权益乘数

        Returns:
            DataFrame with results
        """
        results = []

        # 限制分析期数为最近12个季度
        max_periods = min(12, len(self.pd_income), len(self.pd_asset))

        for idx in range(max_periods):
            try:
                # 获取报告日期
                report_date = self.get_value(self.pd_income, idx, '报告日', 'Report Date', '')
                if not report_date:
                    continue

                # 从利润表获取数据
                net_profit = self.get_value(self.pd_income, idx, '归属于母公司所有者的净利润', 'Net Profit Attributable to Parent')
                operating_revenue = self.get_value(self.pd_income, idx, '营业收入', 'Operating Revenue')

                # 从资产负债表获取数据
                total_assets = self.get_value(self.pd_asset, idx, '资产总计', 'Total Assets')
                shareholders_equity = self.get_value(self.pd_asset, idx, '归属于母公司股东权益合计', 'Total Equity Attributable to Shareholders of the Parent Company')

                # 如果关键数据缺失,跳过
                if operating_revenue == 0 or total_assets == 0 or shareholders_equity == 0:
                    continue

                # 计算平均总资产和平均股东权益
                if idx < len(self.pd_asset) - 1:
                    prev_total_assets = self.get_value(self.pd_asset, idx + 1, '资产总计', 'Total Assets')
                    prev_shareholders_equity = self.get_value(self.pd_asset, idx + 1, '归属于母公司股东权益合计', 'Total Equity Attributable to Shareholders of the Parent Company')
                    avg_total_assets = (total_assets + prev_total_assets) / 2 if prev_total_assets > 0 else total_assets
                    avg_shareholders_equity = (shareholders_equity + prev_shareholders_equity) / 2 if prev_shareholders_equity > 0 else shareholders_equity
                else:
                    avg_total_assets = total_assets
                    avg_shareholders_equity = shareholders_equity

                # 三因素计算
                # 1. 净利率 (Net Profit Margin)
                net_profit_margin = (net_profit / operating_revenue) * 100 if operating_revenue > 0 else 0

                # 2. 总资产周转率 (Total Asset Turnover)
                total_asset_turnover = operating_revenue / avg_total_assets if avg_total_assets > 0 else 0

                # 3. 权益乘数 (Equity Multiplier)
                equity_multiplier = avg_total_assets / avg_shareholders_equity if avg_shareholders_equity > 0 else 0

                # ROE计算
                roe = net_profit / avg_shareholders_equity * 100 if avg_shareholders_equity > 0 else 0

                # 验证公式: ROE应该等于三因素相乘(考虑百分比转换)
                roe_calculated = (net_profit_margin / 100) * total_asset_turnover * equity_multiplier * 100

                results.append({
                    '报告日 (Report Date)': report_date,
                    'ROE (%)': round(roe, 4),
                    'ROE验算 (%)': round(roe_calculated, 4),
                    '净利率 (Net Profit Margin %)': round(net_profit_margin, 4),
                    '总资产周转率 (Total Asset Turnover)': round(total_asset_turnover, 4),
                    '权益乘数 (Equity Multiplier)': round(equity_multiplier, 4),
                    '净利润 (Net Profit)': net_profit,
                    '营业收入 (Operating Revenue)': operating_revenue,
                    '平均总资产 (Avg Total Assets)': avg_total_assets,
                    '平均股东权益 (Avg Shareholders Equity)': avg_shareholders_equity
                })

            except Exception as e:
                if not self.silent:
                    print(f"期数 {idx} 计算失败: {e}")
                continue

        self.results = pd.DataFrame(results)
        return self.results

    def calculate_roe_5factor(self):
        """
        计算五因素杜邦分析
        ROE = 税负 × 利息负担 × 息税前利润率 × 总资产周转率 × 权益乘数

        Returns:
            DataFrame with results
        """
        results = []

        # 限制分析期数为最近12个季度
        max_periods = min(12, len(self.pd_income), len(self.pd_asset))

        for idx in range(max_periods):
            try:
                # 获取报告日期
                report_date = self.get_value(self.pd_income, idx, '报告日', 'Report Date', '')
                if not report_date:
                    continue

                # 从利润表获取数据
                net_profit = self.get_value(self.pd_income, idx, '归属于母公司所有者的净利润', 'Net Profit Attributable to Parent')
                operating_revenue = self.get_value(self.pd_income, idx, '营业收入', 'Operating Revenue')
                operating_profit = self.get_value(self.pd_income, idx, '营业利润', 'Operating Profit')
                total_profit = self.get_value(self.pd_income, idx, '利润总额', 'Total Profit')
                income_tax = self.get_value(self.pd_income, idx, '所得税费用', 'Income Tax Expenses')
                interest_expense = self.get_value(self.pd_income, idx, '利息费用', 'Interest Expenses')
                financial_expenses = self.get_value(self.pd_income, idx, '财务费用', 'Financial Expenses')

                # 从资产负债表获取数据
                total_assets = self.get_value(self.pd_asset, idx, '资产总计', 'Total Assets')
                shareholders_equity = self.get_value(self.pd_asset, idx, '归属于母公司股东权益合计', 'Total Equity Attributable to Shareholders of the Parent Company')

                # 如果关键数据缺失,跳过
                if operating_revenue == 0 or total_assets == 0 or shareholders_equity == 0:
                    continue

                # 计算平均值
                if idx < len(self.pd_asset) - 1:
                    prev_total_assets = self.get_value(self.pd_asset, idx + 1, '资产总计', 'Total Assets')
                    prev_shareholders_equity = self.get_value(self.pd_asset, idx + 1, '归属于母公司股东权益合计', 'Total Equity Attributable to Shareholders of the Parent Company')
                    avg_total_assets = (total_assets + prev_total_assets) / 2 if prev_total_assets > 0 else total_assets
                    avg_shareholders_equity = (shareholders_equity + prev_shareholders_equity) / 2 if prev_shareholders_equity > 0 else shareholders_equity
                else:
                    avg_total_assets = total_assets
                    avg_shareholders_equity = shareholders_equity

                # 五因素计算
                # 1. 税负 (Tax Burden) = 净利润 / 利润总额
                if total_profit > 0:
                    tax_burden = net_profit / total_profit
                else:
                    # 如果利润总额为0或负数,使用税率估算
                    tax_rate = income_tax / total_profit if total_profit != 0 else 0.25
                    tax_burden = 1 - tax_rate

                # 2. 利息负担 (Interest Burden) = 利润总额 / EBIT
                # EBIT = 利润总额 + 利息费用
                # 优先使用利息费用,如果没有则用财务费用估算
                actual_interest = interest_expense if interest_expense > 0 else (financial_expenses if financial_expenses > 0 else 0)
                ebit = total_profit + actual_interest

                if ebit > 0:
                    interest_burden = total_profit / ebit
                else:
                    interest_burden = 1.0  # 无利息负担

                # 3. 息税前利润率 (EBIT Margin) = EBIT / 营业收入
                ebit_margin = (ebit / operating_revenue) * 100 if operating_revenue > 0 else 0

                # 4. 总资产周转率 (Total Asset Turnover)
                total_asset_turnover = operating_revenue / avg_total_assets if avg_total_assets > 0 else 0

                # 5. 权益乘数 (Equity Multiplier)
                equity_multiplier = avg_total_assets / avg_shareholders_equity if avg_shareholders_equity > 0 else 0

                # ROE计算
                roe = net_profit / avg_shareholders_equity * 100 if avg_shareholders_equity > 0 else 0

                # 验证公式: ROE = 税负 × 利息负担 × 息税前利润率 × 总资产周转率 × 权益乘数
                roe_calculated = tax_burden * interest_burden * (ebit_margin / 100) * total_asset_turnover * equity_multiplier * 100

                results.append({
                    '报告日 (Report Date)': report_date,
                    'ROE (%)': round(roe, 4),
                    'ROE验算 (%)': round(roe_calculated, 4),
                    '税负 (Tax Burden)': round(tax_burden, 4),
                    '利息负担 (Interest Burden)': round(interest_burden, 4),
                    '息税前利润率 (EBIT Margin %)': round(ebit_margin, 4),
                    '总资产周转率 (Total Asset Turnover)': round(total_asset_turnover, 4),
                    '权益乘数 (Equity Multiplier)': round(equity_multiplier, 4),
                    'EBIT': ebit,
                    '净利润 (Net Profit)': net_profit,
                    '利润总额 (Total Profit)': total_profit,
                    '营业收入 (Operating Revenue)': operating_revenue,
                    '平均总资产 (Avg Total Assets)': avg_total_assets,
                    '平均股东权益 (Avg Shareholders Equity)': avg_shareholders_equity
                })

            except Exception as e:
                if not self.silent:
                    print(f"期数 {idx} 计算失败: {e}")
                continue

        self.results = pd.DataFrame(results)
        return self.results

    def generate_report_text(self):
        """
        生成报告文本 (不打印)

        Returns:
            str: 报告文本
        """
        if self.results is None or len(self.results) == 0:
            return "未能生成报告: 无有效数据"

        report_lines = []

        def add_line(text):
            report_lines.append(text)

        # 报告头部
        add_line("=" * 100)
        if self.model_type == "3factor":
            add_line(f"杜邦分析报告 (三因素模型) - DuPont Analysis Report (3-Factor Model)")
        else:
            add_line(f"杜邦分析报告 (五因素模型) - DuPont Analysis Report (5-Factor Model)")
        add_line(f"股票代码 (Stock Code): {self.stock_code}")
        add_line(f"报告生成时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        add_line("=" * 100)
        add_line("")

        # 模型说明
        add_line("【模型说明 (Model Description)】")
        if self.model_type == "3factor":
            add_line("三因素杜邦模型: ROE = 净利率 × 总资产周转率 × 权益乘数")
            add_line("3-Factor DuPont: ROE = Net Profit Margin × Total Asset Turnover × Equity Multiplier")
            add_line("")
            add_line("因素解释:")
            add_line("  净利率: 反映盈利能力 (Profitability)")
            add_line("  总资产周转率: 反映营运效率 (Efficiency)")
            add_line("  权益乘数: 反映财务杠杆 (Leverage)")
        else:
            add_line("五因素杜邦模型: ROE = 税负 × 利息负担 × 息税前利润率 × 总资产周转率 × 权益乘数")
            add_line("5-Factor DuPont: ROE = Tax Burden × Interest Burden × EBIT Margin × Asset Turnover × Equity Multiplier")
            add_line("")
            add_line("因素解释:")
            add_line("  税负: 税收效率 (Tax Efficiency)")
            add_line("  利息负担: 利息成本 (Interest Cost)")
            add_line("  息税前利润率: 经营盈利能力 (Operating Profitability)")
            add_line("  总资产周转率: 营运效率 (Efficiency)")
            add_line("  权益乘数: 财务杠杆 (Leverage)")
        add_line("-" * 100)
        add_line("")

        # 最新数据分析
        latest = self.results.iloc[0]
        add_line("【最新报告期分析】")
        add_line(f"报告日期: {latest['报告日 (Report Date)']}")
        add_line(f"ROE: {latest['ROE (%)']:.4f}%")
        add_line(f"ROE验算: {latest['ROE验算 (%)']:.4f}% (两者应基本一致)")
        add_line("")

        if self.model_type == "3factor":
            add_line("三因素分解:")
            add_line(f"  净利率 (Net Profit Margin):    {latest['净利率 (Net Profit Margin %)']:.4f}%")
            add_line(f"  总资产周转率 (Asset Turnover):  {latest['总资产周转率 (Total Asset Turnover)']:.4f}次")
            add_line(f"  权益乘数 (Equity Multiplier):   {latest['权益乘数 (Equity Multiplier)']:.4f}倍")
        else:
            add_line("五因素分解:")
            add_line(f"  税负 (Tax Burden):              {latest['税负 (Tax Burden)']:.4f}")
            add_line(f"  利息负担 (Interest Burden):      {latest['利息负担 (Interest Burden)']:.4f}")
            add_line(f"  息税前利润率 (EBIT Margin):      {latest['息税前利润率 (EBIT Margin %)']:.4f}%")
            add_line(f"  总资产周转率 (Asset Turnover):   {latest['总资产周转率 (Total Asset Turnover)']:.4f}次")
            add_line(f"  权益乘数 (Equity Multiplier):    {latest['权益乘数 (Equity Multiplier)']:.4f}倍")

        add_line("-" * 100)
        add_line("")

        # 历史趋势
        add_line("【历史趋势分析】")
        add_line(f"分析期数: {len(self.results)} 个报告期")
        add_line(f"ROE平均值: {self.results['ROE (%)'].mean():.4f}%")
        add_line(f"ROE最大值: {self.results['ROE (%)'].max():.4f}% ({self.results.loc[self.results['ROE (%)'].idxmax(), '报告日 (Report Date)']})")
        add_line(f"ROE最小值: {self.results['ROE (%)'].min():.4f}% ({self.results.loc[self.results['ROE (%)'].idxmin(), '报告日 (Report Date)']})")
        add_line(f"ROE标准差: {self.results['ROE (%)'].std():.4f}%")
        add_line("")

        # 因素贡献度分析
        if len(self.results) >= 2:
            add_line("【最近期间变动分析】")
            latest_roe = self.results.iloc[0]['ROE (%)']
            prev_roe = self.results.iloc[1]['ROE (%)']
            roe_change = latest_roe - prev_roe

            add_line(f"ROE变化: {prev_roe:.4f}% → {latest_roe:.4f}% (变动: {roe_change:+.4f}%)")

            if self.model_type == "3factor":
                margin_change = self.results.iloc[0]['净利率 (Net Profit Margin %)'] - self.results.iloc[1]['净利率 (Net Profit Margin %)']
                turnover_change = self.results.iloc[0]['总资产周转率 (Total Asset Turnover)'] - self.results.iloc[1]['总资产周转率 (Total Asset Turnover)']
                multiplier_change = self.results.iloc[0]['权益乘数 (Equity Multiplier)'] - self.results.iloc[1]['权益乘数 (Equity Multiplier)']

                add_line(f"  净利率变动: {margin_change:+.4f}%")
                add_line(f"  总资产周转率变动: {turnover_change:+.4f}")
                add_line(f"  权益乘数变动: {multiplier_change:+.4f}")
            else:
                tax_change = self.results.iloc[0]['税负 (Tax Burden)'] - self.results.iloc[1]['税负 (Tax Burden)']
                interest_change = self.results.iloc[0]['利息负担 (Interest Burden)'] - self.results.iloc[1]['利息负担 (Interest Burden)']
                ebit_change = self.results.iloc[0]['息税前利润率 (EBIT Margin %)'] - self.results.iloc[1]['息税前利润率 (EBIT Margin %)']
                turnover_change = self.results.iloc[0]['总资产周转率 (Total Asset Turnover)'] - self.results.iloc[1]['总资产周转率 (Total Asset Turnover)']
                multiplier_change = self.results.iloc[0]['权益乘数 (Equity Multiplier)'] - self.results.iloc[1]['权益乘数 (Equity Multiplier)']

                add_line(f"  税负变动: {tax_change:+.4f}")
                add_line(f"  利息负担变动: {interest_change:+.4f}")
                add_line(f"  息税前利润率变动: {ebit_change:+.4f}%")
                add_line(f"  总资产周转率变动: {turnover_change:+.4f}")
                add_line(f"  权益乘数变动: {multiplier_change:+.4f}")

        add_line("-" * 100)
        add_line("")

        # 详细数据表
        add_line("【详细历史数据】")
        if self.model_type == "3factor":
            display_cols = ['报告日 (Report Date)', 'ROE (%)', '净利率 (Net Profit Margin %)',
                           '总资产周转率 (Total Asset Turnover)', '权益乘数 (Equity Multiplier)']
        else:
            display_cols = ['报告日 (Report Date)', 'ROE (%)', '税负 (Tax Burden)',
                           '利息负担 (Interest Burden)', '息税前利润率 (EBIT Margin %)',
                           '总资产周转率 (Total Asset Turnover)', '权益乘数 (Equity Multiplier)']

        add_line(self.results[display_cols].to_string(index=False))
        add_line("")
        add_line("=" * 100)

        return "\n".join(report_lines)

    def print_report(self):
        """打印报告到控制台"""
        report_text = self.generate_report_text()
        print(report_text)


def analyze_dupont_roe_3factor(stock_code, print_output=True):
    """
    三因素杜邦分析
    3-Factor DuPont Analysis

    ROE = 净利率 × 总资产周转率 × 权益乘数
    ROE = Net Profit Margin × Total Asset Turnover × Equity Multiplier

    Args:
        stock_code: 股票代码
        print_output: 是否打印输出

    Returns:
        (DataFrame, str): (结果数据, 报告文本)

    Example:
        >>> data, report = analyze_dupont_roe_3factor("600519")
        >>> data, report = analyze_dupont_roe_3factor("600519", print_output=False)
        >>> latest_roe = data.iloc[0]['ROE (%)']
    """
    if print_output:
        print("\n" + "=" * 100)
        print("杜邦分析 (三因素模型) - DuPont Analysis (3-Factor Model)")
        print("=" * 100 + "\n")

    # 创建分析对象
    analyzer = DuPontAnalysis(stock_code, model_type="3factor", silent=not print_output)

    # 加载数据
    analyzer.load_data()

    # 计算指标
    results_df = analyzer.calculate_roe_3factor()

    # 生成报告
    report_text = analyzer.generate_report_text()

    # 根据参数决定是否打印
    if print_output:
        print(report_text)
        print("\n分析完成!")

    return results_df, report_text


def analyze_dupont_roe_5factor(stock_code, print_output=True):
    """
    五因素杜邦分析
    5-Factor DuPont Analysis

    ROE = 税负 × 利息负担 × 息税前利润率 × 总资产周转率 × 权益乘数
    ROE = Tax Burden × Interest Burden × EBIT Margin × Total Asset Turnover × Equity Multiplier

    Args:
        stock_code: 股票代码
        print_output: 是否打印输出

    Returns:
        (DataFrame, str): (结果数据, 报告文本)

    Example:
        >>> data, report = analyze_dupont_roe_5factor("600519")
        >>> data, report = analyze_dupont_roe_5factor("600519", print_output=False)
        >>> latest_roe = data.iloc[0]['ROE (%)']
    """
    if print_output:
        print("\n" + "=" * 100)
        print("杜邦分析 (五因素模型) - DuPont Analysis (5-Factor Model)")
        print("=" * 100 + "\n")

    # 创建分析对象
    analyzer = DuPontAnalysis(stock_code, model_type="5factor", silent=not print_output)

    # 加载数据
    analyzer.load_data()

    # 计算指标
    results_df = analyzer.calculate_roe_5factor()

    # 生成报告
    report_text = analyzer.generate_report_text()

    # 根据参数决定是否打印
    if print_output:
        print(report_text)
        print("\n分析完成!")

    return results_df, report_text


# 使用示例
if __name__ == "__main__":
    # 测试三因素模型
    print("\n" + "="*100)
    print("测试三因素杜邦分析")
    print("="*100)
    data_3f, report_3f = analyze_dupont_roe_3factor("600519")

    # 保存报告
    with open('dupont_3factor_report.txt', 'w', encoding='utf-8') as f:
        f.write(report_3f)

    # 访问数据
    latest_roe_3f = data_3f.iloc[0]['ROE (%)']
    print(f"\n最新ROE (三因素): {latest_roe_3f:.4f}%")

    print("\n\n" + "="*100)
    print("测试五因素杜邦分析")
    print("="*100)

    # 测试五因素模型
    data_5f, report_5f = analyze_dupont_roe_5factor("600519")

    # 保存报告
    with open('dupont_5factor_report.txt', 'w', encoding='utf-8') as f:
        f.write(report_5f)

    # 访问数据
    latest_roe_5f = data_5f.iloc[0]['ROE (%)']
    print(f"\n最新ROE (五因素): {latest_roe_5f:.4f}%")

    # 静默模式测试
    print("\n\n" + "="*100)
    print("静默模式测试")
    print("="*100)
    data_silent, report_silent = analyze_dupont_roe_3factor("000858", print_output=False)
    print(f"静默模式完成,获取到 {len(data_silent)} 期数据")
