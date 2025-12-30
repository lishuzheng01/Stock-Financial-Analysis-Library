# -*- coding: utf-8 -*-
"""
盈利能力分析模块 - Profitability Analysis Module
分析企业的盈利能力和质量
Analyze enterprise profitability and quality
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


class ProfitabilityAnalyzer:
    """盈利能力分析器基类"""

    def __init__(self, stock_code, silent=False):
        self.stock_code = stock_code
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
        """灵活获取列名 (支持中英文)"""
        if cn_name in df.columns:
            return cn_name
        elif en_name in df.columns:
            return en_name
        return None

    def get_value(self, df, idx, cn_name, en_name, default=0.0):
        """安全获取值 (支持中英文列名)"""
        col = self.get_column(df, cn_name, en_name)
        if col and idx < len(df):
            value = df.iloc[idx][col]
            if pd.notna(value) and value != '' and value is not None:
                try:
                    return float(value)
                except:
                    return default
        return default


def analyze_gross_margin(stock_code, print_output=True):
    """
    毛利率分析
    Gross Margin Analysis

    毛利率 = (营业收入 - 营业成本) / 营业收入 × 100%
    Gross Margin = (Operating Revenue - Operating Costs) / Operating Revenue × 100%

    Args:
        stock_code: 股票代码
        print_output: 是否打印输出

    Returns:
        (DataFrame, str): (结果数据, 报告文本)
    """
    if print_output:
        print("\n" + "=" * 80)
        print("毛利率分析 - Gross Margin Analysis")
        print("=" * 80 + "\n")

    analyzer = ProfitabilityAnalyzer(stock_code, silent=not print_output)
    analyzer.load_data()

    results = []
    max_periods = min(12, len(analyzer.pd_income))

    for idx in range(max_periods):
        try:
            report_date = analyzer.get_value(analyzer.pd_income, idx, '报告日', 'Report Date', '')
            if not report_date:
                continue

            revenue = analyzer.get_value(analyzer.pd_income, idx, '营业收入', 'Operating Revenue')
            cost = analyzer.get_value(analyzer.pd_income, idx, '营业成本', 'Operating Costs')

            if revenue == 0:
                continue

            # 计算毛利率
            gross_margin = ((revenue - cost) / revenue) * 100

            # 计算同比和环比
            yoy_change = 0
            qoq_change = 0

            # 同比: 与去年同期对比 (通常是4个季度前)
            if idx >= 4 and idx + 4 < len(analyzer.pd_income):
                prev_year_revenue = analyzer.get_value(analyzer.pd_income, idx + 4, '营业收入', 'Operating Revenue')
                prev_year_cost = analyzer.get_value(analyzer.pd_income, idx + 4, '营业成本', 'Operating Costs')
                if prev_year_revenue > 0:
                    prev_year_gm = ((prev_year_revenue - prev_year_cost) / prev_year_revenue) * 100
                    yoy_change = gross_margin - prev_year_gm

            # 环比: 与上一季度对比
            if idx < len(analyzer.pd_income) - 1:
                prev_quarter_revenue = analyzer.get_value(analyzer.pd_income, idx + 1, '营业收入', 'Operating Revenue')
                prev_quarter_cost = analyzer.get_value(analyzer.pd_income, idx + 1, '营业成本', 'Operating Costs')
                if prev_quarter_revenue > 0:
                    prev_quarter_gm = ((prev_quarter_revenue - prev_quarter_cost) / prev_quarter_revenue) * 100
                    qoq_change = gross_margin - prev_quarter_gm

            results.append({
                '报告日 (Report Date)': report_date,
                '毛利率 (Gross Margin %)': round(gross_margin, 4),
                '同比变化 (YoY Change %)': round(yoy_change, 4),
                '环比变化 (QoQ Change %)': round(qoq_change, 4),
                '营业收入 (Revenue)': revenue,
                '营业成本 (Cost)': cost,
                '毛利 (Gross Profit)': revenue - cost
            })

        except Exception as e:
            if not analyzer.silent:
                print(f"期数 {idx} 计算失败: {e}")
            continue

    results_df = pd.DataFrame(results)

    # 生成报告
    report_lines = []
    report_lines.append("=" * 80)
    report_lines.append("毛利率分析报告 - Gross Margin Analysis Report")
    report_lines.append(f"股票代码: {stock_code}")
    report_lines.append(f"生成时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    report_lines.append("=" * 80)
    report_lines.append("")

    if len(results_df) > 0:
        latest = results_df.iloc[0]
        report_lines.append("【最新数据】")
        report_lines.append(f"报告日期: {latest['报告日 (Report Date)']}")
        report_lines.append(f"毛利率: {latest['毛利率 (Gross Margin %)']:.4f}%")
        report_lines.append(f"同比变化: {latest['同比变化 (YoY Change %)']:+.4f}%")
        report_lines.append(f"环比变化: {latest['环比变化 (QoQ Change %)']:+.4f}%")
        report_lines.append("")

        report_lines.append("【统计数据】")
        report_lines.append(f"平均毛利率: {results_df['毛利率 (Gross Margin %)'].mean():.4f}%")
        report_lines.append(f"最高毛利率: {results_df['毛利率 (Gross Margin %)'].max():.4f}%")
        report_lines.append(f"最低毛利率: {results_df['毛利率 (Gross Margin %)'].min():.4f}%")
        report_lines.append(f"标准差: {results_df['毛利率 (Gross Margin %)'].std():.4f}%")
        report_lines.append("")

        report_lines.append("【详细数据】")
        display_cols = ['报告日 (Report Date)', '毛利率 (Gross Margin %)', '同比变化 (YoY Change %)', '环比变化 (QoQ Change %)']
        report_lines.append(results_df[display_cols].to_string(index=False))

    report_lines.append("")
    report_lines.append("=" * 80)
    report_text = "\n".join(report_lines)

    if print_output:
        print(report_text)
        print("\n分析完成!")

    return results_df, report_text


def analyze_net_margin(stock_code, print_output=True):
    """
    净利率分析
    Net Profit Margin Analysis

    净利率 = 净利润 / 营业收入 × 100%
    Net Margin = Net Profit / Operating Revenue × 100%
    """
    if print_output:
        print("\n" + "=" * 80)
        print("净利率分析 - Net Margin Analysis")
        print("=" * 80 + "\n")

    analyzer = ProfitabilityAnalyzer(stock_code, silent=not print_output)
    analyzer.load_data()

    results = []
    max_periods = min(12, len(analyzer.pd_income))

    for idx in range(max_periods):
        try:
            report_date = analyzer.get_value(analyzer.pd_income, idx, '报告日', 'Report Date', '')
            if not report_date:
                continue

            net_profit = analyzer.get_value(analyzer.pd_income, idx, '归属于母公司所有者的净利润', 'Net Profit Attributable to Parent')
            revenue = analyzer.get_value(analyzer.pd_income, idx, '营业收入', 'Operating Revenue')

            if revenue == 0:
                continue

            net_margin = (net_profit / revenue) * 100

            # 同比环比计算
            yoy_change = 0
            qoq_change = 0

            if idx >= 4 and idx + 4 < len(analyzer.pd_income):
                prev_year_profit = analyzer.get_value(analyzer.pd_income, idx + 4, '归属于母公司所有者的净利润', 'Net Profit Attributable to Parent')
                prev_year_revenue = analyzer.get_value(analyzer.pd_income, idx + 4, '营业收入', 'Operating Revenue')
                if prev_year_revenue > 0:
                    prev_year_nm = (prev_year_profit / prev_year_revenue) * 100
                    yoy_change = net_margin - prev_year_nm

            if idx < len(analyzer.pd_income) - 1:
                prev_quarter_profit = analyzer.get_value(analyzer.pd_income, idx + 1, '归属于母公司所有者的净利润', 'Net Profit Attributable to Parent')
                prev_quarter_revenue = analyzer.get_value(analyzer.pd_income, idx + 1, '营业收入', 'Operating Revenue')
                if prev_quarter_revenue > 0:
                    prev_quarter_nm = (prev_quarter_profit / prev_quarter_revenue) * 100
                    qoq_change = net_margin - prev_quarter_nm

            results.append({
                '报告日 (Report Date)': report_date,
                '净利率 (Net Margin %)': round(net_margin, 4),
                '同比变化 (YoY Change %)': round(yoy_change, 4),
                '环比变化 (QoQ Change %)': round(qoq_change, 4),
                '净利润 (Net Profit)': net_profit,
                '营业收入 (Revenue)': revenue
            })

        except Exception as e:
            if not analyzer.silent:
                print(f"期数 {idx} 计算失败: {e}")
            continue

    results_df = pd.DataFrame(results)

    # 生成报告
    report_lines = []
    report_lines.append("=" * 80)
    report_lines.append("净利率分析报告 - Net Margin Analysis Report")
    report_lines.append(f"股票代码: {stock_code}")
    report_lines.append(f"生成时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    report_lines.append("=" * 80)
    report_lines.append("")

    if len(results_df) > 0:
        latest = results_df.iloc[0]
        report_lines.append("【最新数据】")
        report_lines.append(f"报告日期: {latest['报告日 (Report Date)']}")
        report_lines.append(f"净利率: {latest['净利率 (Net Margin %)']:.4f}%")
        report_lines.append(f"同比变化: {latest['同比变化 (YoY Change %)']:+.4f}%")
        report_lines.append(f"环比变化: {latest['环比变化 (QoQ Change %)']:+.4f}%")
        report_lines.append("")

        report_lines.append("【统计数据】")
        report_lines.append(f"平均净利率: {results_df['净利率 (Net Margin %)'].mean():.4f}%")
        report_lines.append(f"最高净利率: {results_df['净利率 (Net Margin %)'].max():.4f}%")
        report_lines.append(f"最低净利率: {results_df['净利率 (Net Margin %)'].min():.4f}%")
        report_lines.append("")

        report_lines.append("【详细数据】")
        display_cols = ['报告日 (Report Date)', '净利率 (Net Margin %)', '同比变化 (YoY Change %)', '环比变化 (QoQ Change %)']
        report_lines.append(results_df[display_cols].to_string(index=False))

    report_lines.append("")
    report_lines.append("=" * 80)
    report_text = "\n".join(report_lines)

    if print_output:
        print(report_text)
        print("\n分析完成!")

    return results_df, report_text


def analyze_roe(stock_code, print_output=True):
    """
    ROE分析 (净资产收益率)
    Return on Equity Analysis

    ROE = 净利润 / 平均股东权益 × 100%
    ROE = Net Profit / Average Shareholders' Equity × 100%
    """
    if print_output:
        print("\n" + "=" * 80)
        print("ROE分析 - Return on Equity Analysis")
        print("=" * 80 + "\n")

    analyzer = ProfitabilityAnalyzer(stock_code, silent=not print_output)
    analyzer.load_data()

    results = []
    max_periods = min(12, len(analyzer.pd_income), len(analyzer.pd_asset))

    for idx in range(max_periods):
        try:
            report_date = analyzer.get_value(analyzer.pd_income, idx, '报告日', 'Report Date', '')
            if not report_date:
                continue

            net_profit = analyzer.get_value(analyzer.pd_income, idx, '归属于母公司所有者的净利润', 'Net Profit Attributable to Parent')
            shareholders_equity = analyzer.get_value(analyzer.pd_asset, idx, '归属于母公司股东权益合计', 'Total Equity Attributable to Shareholders of the Parent Company')

            # 计算平均股东权益
            if idx < len(analyzer.pd_asset) - 1:
                prev_equity = analyzer.get_value(analyzer.pd_asset, idx + 1, '归属于母公司股东权益合计', 'Total Equity Attributable to Shareholders of the Parent Company')
                avg_equity = (shareholders_equity + prev_equity) / 2 if prev_equity > 0 else shareholders_equity
            else:
                avg_equity = shareholders_equity

            if avg_equity == 0:
                continue

            roe = (net_profit / avg_equity) * 100

            # 同比环比
            yoy_change = 0
            qoq_change = 0

            if idx >= 4 and idx + 4 < max_periods:
                prev_year_profit = analyzer.get_value(analyzer.pd_income, idx + 4, '归属于母公司所有者的净利润', 'Net Profit Attributable to Parent')
                prev_year_equity = analyzer.get_value(analyzer.pd_asset, idx + 4, '归属于母公司股东权益合计', 'Total Equity Attributable to Shareholders of the Parent Company')
                if idx + 5 < len(analyzer.pd_asset):
                    prev_prev_equity = analyzer.get_value(analyzer.pd_asset, idx + 5, '归属于母公司股东权益合计', 'Total Equity Attributable to Shareholders of the Parent Company')
                    avg_prev_equity = (prev_year_equity + prev_prev_equity) / 2 if prev_prev_equity > 0 else prev_year_equity
                else:
                    avg_prev_equity = prev_year_equity
                if avg_prev_equity > 0:
                    prev_year_roe = (prev_year_profit / avg_prev_equity) * 100
                    yoy_change = roe - prev_year_roe

            if idx < max_periods - 1:
                prev_quarter_profit = analyzer.get_value(analyzer.pd_income, idx + 1, '归属于母公司所有者的净利润', 'Net Profit Attributable to Parent')
                prev_quarter_equity = analyzer.get_value(analyzer.pd_asset, idx + 1, '归属于母公司股东权益合计', 'Total Equity Attributable to Shareholders of the Parent Company')
                if idx + 2 < len(analyzer.pd_asset):
                    prev_prev_equity = analyzer.get_value(analyzer.pd_asset, idx + 2, '归属于母公司股东权益合计', 'Total Equity Attributable to Shareholders of the Parent Company')
                    avg_prev_equity = (prev_quarter_equity + prev_prev_equity) / 2 if prev_prev_equity > 0 else prev_quarter_equity
                else:
                    avg_prev_equity = prev_quarter_equity
                if avg_prev_equity > 0:
                    prev_quarter_roe = (prev_quarter_profit / avg_prev_equity) * 100
                    qoq_change = roe - prev_quarter_roe

            results.append({
                '报告日 (Report Date)': report_date,
                'ROE (%)': round(roe, 4),
                '同比变化 (YoY Change %)': round(yoy_change, 4),
                '环比变化 (QoQ Change %)': round(qoq_change, 4),
                '净利润 (Net Profit)': net_profit,
                '平均股东权益 (Avg Equity)': avg_equity
            })

        except Exception as e:
            if not analyzer.silent:
                print(f"期数 {idx} 计算失败: {e}")
            continue

    results_df = pd.DataFrame(results)

    # 生成报告
    report_lines = []
    report_lines.append("=" * 80)
    report_lines.append("ROE分析报告 - Return on Equity Analysis Report")
    report_lines.append(f"股票代码: {stock_code}")
    report_lines.append(f"生成时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    report_lines.append("=" * 80)
    report_lines.append("")

    if len(results_df) > 0:
        latest = results_df.iloc[0]
        report_lines.append("【最新数据】")
        report_lines.append(f"报告日期: {latest['报告日 (Report Date)']}")
        report_lines.append(f"ROE: {latest['ROE (%)']:.4f}%")
        report_lines.append(f"同比变化: {latest['同比变化 (YoY Change %)']:+.4f}%")
        report_lines.append(f"环比变化: {latest['环比变化 (QoQ Change %)']:+.4f}%")
        report_lines.append("")

        report_lines.append("【统计数据】")
        report_lines.append(f"平均ROE: {results_df['ROE (%)'].mean():.4f}%")
        report_lines.append(f"最高ROE: {results_df['ROE (%)'].max():.4f}%")
        report_lines.append(f"最低ROE: {results_df['ROE (%)'].min():.4f}%")
        report_lines.append("")

        report_lines.append("【详细数据】")
        display_cols = ['报告日 (Report Date)', 'ROE (%)', '同比变化 (YoY Change %)', '环比变化 (QoQ Change %)']
        report_lines.append(results_df[display_cols].to_string(index=False))

    report_lines.append("")
    report_lines.append("=" * 80)
    report_text = "\n".join(report_lines)

    if print_output:
        print(report_text)
        print("\n分析完成!")

    return results_df, report_text


def analyze_roa(stock_code, print_output=True):
    """
    ROA分析 (总资产收益率)
    Return on Assets Analysis

    ROA = 净利润 / 平均总资产 × 100%
    ROA = Net Profit / Average Total Assets × 100%
    """
    if print_output:
        print("\n" + "=" * 80)
        print("ROA分析 - Return on Assets Analysis")
        print("=" * 80 + "\n")

    analyzer = ProfitabilityAnalyzer(stock_code, silent=not print_output)
    analyzer.load_data()

    results = []
    max_periods = min(12, len(analyzer.pd_income), len(analyzer.pd_asset))

    for idx in range(max_periods):
        try:
            report_date = analyzer.get_value(analyzer.pd_income, idx, '报告日', 'Report Date', '')
            if not report_date:
                continue

            net_profit = analyzer.get_value(analyzer.pd_income, idx, '归属于母公司所有者的净利润', 'Net Profit Attributable to Parent')
            total_assets = analyzer.get_value(analyzer.pd_asset, idx, '资产总计', 'Total Assets')

            # 计算平均总资产
            if idx < len(analyzer.pd_asset) - 1:
                prev_assets = analyzer.get_value(analyzer.pd_asset, idx + 1, '资产总计', 'Total Assets')
                avg_assets = (total_assets + prev_assets) / 2 if prev_assets > 0 else total_assets
            else:
                avg_assets = total_assets

            if avg_assets == 0:
                continue

            roa = (net_profit / avg_assets) * 100

            # 同比环比计算
            yoy_change = 0
            qoq_change = 0

            if idx >= 4 and idx + 4 < max_periods:
                prev_year_profit = analyzer.get_value(analyzer.pd_income, idx + 4, '归属于母公司所有者的净利润', 'Net Profit Attributable to Parent')
                prev_year_assets = analyzer.get_value(analyzer.pd_asset, idx + 4, '资产总计', 'Total Assets')
                if idx + 5 < len(analyzer.pd_asset):
                    prev_prev_assets = analyzer.get_value(analyzer.pd_asset, idx + 5, '资产总计', 'Total Assets')
                    avg_prev_assets = (prev_year_assets + prev_prev_assets) / 2 if prev_prev_assets > 0 else prev_year_assets
                else:
                    avg_prev_assets = prev_year_assets
                if avg_prev_assets > 0:
                    prev_year_roa = (prev_year_profit / avg_prev_assets) * 100
                    yoy_change = roa - prev_year_roa

            if idx < max_periods - 1:
                prev_quarter_profit = analyzer.get_value(analyzer.pd_income, idx + 1, '归属于母公司所有者的净利润', 'Net Profit Attributable to Parent')
                prev_quarter_assets = analyzer.get_value(analyzer.pd_asset, idx + 1, '资产总计', 'Total Assets')
                if idx + 2 < len(analyzer.pd_asset):
                    prev_prev_assets = analyzer.get_value(analyzer.pd_asset, idx + 2, '资产总计', 'Total Assets')
                    avg_prev_assets = (prev_quarter_assets + prev_prev_assets) / 2 if prev_prev_assets > 0 else prev_quarter_assets
                else:
                    avg_prev_assets = prev_quarter_assets
                if avg_prev_assets > 0:
                    prev_quarter_roa = (prev_quarter_profit / avg_prev_assets) * 100
                    qoq_change = roa - prev_quarter_roa

            results.append({
                '报告日 (Report Date)': report_date,
                'ROA (%)': round(roa, 4),
                '同比变化 (YoY Change %)': round(yoy_change, 4),
                '环比变化 (QoQ Change %)': round(qoq_change, 4),
                '净利润 (Net Profit)': net_profit,
                '平均总资产 (Avg Assets)': avg_assets
            })

        except Exception as e:
            if not analyzer.silent:
                print(f"期数 {idx} 计算失败: {e}")
            continue

    results_df = pd.DataFrame(results)

    # 生成报告
    report_lines = []
    report_lines.append("=" * 80)
    report_lines.append("ROA分析报告 - Return on Assets Analysis Report")
    report_lines.append(f"股票代码: {stock_code}")
    report_lines.append(f"生成时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    report_lines.append("=" * 80)
    report_lines.append("")

    if len(results_df) > 0:
        latest = results_df.iloc[0]
        report_lines.append("【最新数据】")
        report_lines.append(f"报告日期: {latest['报告日 (Report Date)']}")
        report_lines.append(f"ROA: {latest['ROA (%)']:.4f}%")
        report_lines.append(f"同比变化: {latest['同比变化 (YoY Change %)']:+.4f}%")
        report_lines.append(f"环比变化: {latest['环比变化 (QoQ Change %)']:+.4f}%")
        report_lines.append("")

        report_lines.append("【统计数据】")
        report_lines.append(f"平均ROA: {results_df['ROA (%)'].mean():.4f}%")
        report_lines.append(f"最高ROA: {results_df['ROA (%)'].max():.4f}%")
        report_lines.append(f"最低ROA: {results_df['ROA (%)'].min():.4f}%")
        report_lines.append("")

        report_lines.append("【详细数据】")
        display_cols = ['报告日 (Report Date)', 'ROA (%)', '同比变化 (YoY Change %)', '环比变化 (QoQ Change %)']
        report_lines.append(results_df[display_cols].to_string(index=False))

    report_lines.append("")
    report_lines.append("=" * 80)
    report_text = "\n".join(report_lines)

    if print_output:
        print(report_text)
        print("\n分析完成!")

    return results_df, report_text


def analyze_roic(stock_code, print_output=True):
    """
    ROIC分析 (投入资本回报率)
    Return on Invested Capital Analysis

    ROIC = NOPAT / 投入资本 × 100%
    NOPAT = EBIT × (1 - 税率)
    投入资本 = 股东权益 + 有息负债 - 现金及现金等价物

    ROIC = NOPAT / Invested Capital × 100%
    NOPAT = EBIT × (1 - Tax Rate)
    Invested Capital = Shareholders' Equity + Interest-bearing Debt - Cash
    """
    if print_output:
        print("\n" + "=" * 80)
        print("ROIC分析 - Return on Invested Capital Analysis")
        print("=" * 80 + "\n")

    analyzer = ProfitabilityAnalyzer(stock_code, silent=not print_output)
    analyzer.load_data()

    results = []
    max_periods = min(12, len(analyzer.pd_income), len(analyzer.pd_asset))

    for idx in range(max_periods):
        try:
            report_date = analyzer.get_value(analyzer.pd_income, idx, '报告日', 'Report Date', '')
            if not report_date:
                continue

            # 计算EBIT
            operating_profit = analyzer.get_value(analyzer.pd_income, idx, '营业利润', 'Operating Profit')
            interest_expense = analyzer.get_value(analyzer.pd_income, idx, '利息费用', 'Interest Expenses')
            financial_expenses = analyzer.get_value(analyzer.pd_income, idx, '财务费用', 'Financial Expenses')

            # 优先使用利息费用,如果没有则用财务费用估算
            actual_interest = interest_expense if interest_expense > 0 else (financial_expenses if financial_expenses > 0 else 0)
            ebit = operating_profit + actual_interest

            # 计算税率
            total_profit = analyzer.get_value(analyzer.pd_income, idx, '利润总额', 'Total Profit')
            income_tax = analyzer.get_value(analyzer.pd_income, idx, '所得税费用', 'Income Tax Expenses')
            tax_rate = income_tax / total_profit if total_profit > 0 else 0.25  # 默认税率25%

            # 计算NOPAT
            nopat = ebit * (1 - tax_rate)

            # 计算投入资本
            shareholders_equity = analyzer.get_value(analyzer.pd_asset, idx, '归属于母公司股东权益合计', 'Total Equity Attributable to Shareholders of the Parent Company')
            long_term_debt = analyzer.get_value(analyzer.pd_asset, idx, '长期借款', 'Long-term Borrowings')
            short_term_debt = analyzer.get_value(analyzer.pd_asset, idx, '短期借款', 'Short-term Borrowings')
            cash = analyzer.get_value(analyzer.pd_asset, idx, '货币资金', 'Cash and Cash Equivalents')

            interest_bearing_debt = long_term_debt + short_term_debt
            invested_capital = shareholders_equity + interest_bearing_debt - cash

            # 计算平均投入资本
            if idx < len(analyzer.pd_asset) - 1:
                prev_equity = analyzer.get_value(analyzer.pd_asset, idx + 1, '归属于母公司股东权益合计', 'Total Equity Attributable to Shareholders of the Parent Company')
                prev_long_debt = analyzer.get_value(analyzer.pd_asset, idx + 1, '长期借款', 'Long-term Borrowings')
                prev_short_debt = analyzer.get_value(analyzer.pd_asset, idx + 1, '短期借款', 'Short-term Borrowings')
                prev_cash = analyzer.get_value(analyzer.pd_asset, idx + 1, '货币资金', 'Cash and Cash Equivalents')
                prev_invested_capital = prev_equity + prev_long_debt + prev_short_debt - prev_cash
                avg_invested_capital = (invested_capital + prev_invested_capital) / 2 if prev_invested_capital > 0 else invested_capital
            else:
                avg_invested_capital = invested_capital

            if avg_invested_capital <= 0:
                continue

            roic = (nopat / avg_invested_capital) * 100

            # 同比环比计算
            yoy_change = 0
            qoq_change = 0

            # 同比计算略过以保持代码简洁

            results.append({
                '报告日 (Report Date)': report_date,
                'ROIC (%)': round(roic, 4),
                'NOPAT': nopat,
                'EBIT': ebit,
                '税率 (Tax Rate %)': round(tax_rate * 100, 4),
                '投入资本 (Invested Capital)': avg_invested_capital,
                '有息负债 (Debt)': interest_bearing_debt,
                '现金 (Cash)': cash
            })

        except Exception as e:
            if not analyzer.silent:
                print(f"期数 {idx} 计算失败: {e}")
            continue

    results_df = pd.DataFrame(results)

    # 生成报告
    report_lines = []
    report_lines.append("=" * 80)
    report_lines.append("ROIC分析报告 - Return on Invested Capital Analysis Report")
    report_lines.append(f"股票代码: {stock_code}")
    report_lines.append(f"生成时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    report_lines.append("=" * 80)
    report_lines.append("")

    report_lines.append("【公式说明】")
    report_lines.append("ROIC = NOPAT / 投入资本")
    report_lines.append("NOPAT = EBIT × (1 - 税率)")
    report_lines.append("投入资本 = 股东权益 + 有息负债 - 现金")
    report_lines.append("")

    if len(results_df) > 0:
        latest = results_df.iloc[0]
        report_lines.append("【最新数据】")
        report_lines.append(f"报告日期: {latest['报告日 (Report Date)']}")
        report_lines.append(f"ROIC: {latest['ROIC (%)']:.4f}%")
        report_lines.append(f"NOPAT: {latest['NOPAT']:,.0f}")
        report_lines.append(f"EBIT: {latest['EBIT']:,.0f}")
        report_lines.append(f"税率: {latest['税率 (Tax Rate %)']:.4f}%")
        report_lines.append(f"投入资本: {latest['投入资本 (Invested Capital)']:,.0f}")
        report_lines.append("")

        report_lines.append("【统计数据】")
        report_lines.append(f"平均ROIC: {results_df['ROIC (%)'].mean():.4f}%")
        report_lines.append(f"最高ROIC: {results_df['ROIC (%)'].max():.4f}%")
        report_lines.append(f"最低ROIC: {results_df['ROIC (%)'].min():.4f}%")
        report_lines.append("")

        report_lines.append("【详细数据】")
        display_cols = ['报告日 (Report Date)', 'ROIC (%)', 'NOPAT', '税率 (Tax Rate %)']
        report_lines.append(results_df[display_cols].to_string(index=False))

    report_lines.append("")
    report_lines.append("=" * 80)
    report_text = "\n".join(report_lines)

    if print_output:
        print(report_text)
        print("\n分析完成!")

    return results_df, report_text


# 使用示例
if __name__ == "__main__":
    # 测试所有函数
    test_stock = "600519"

    print("测试1: 毛利率分析")
    data1, report1 = analyze_gross_margin(test_stock, print_output=False)
    print(f"完成,获取 {len(data1)} 期数据\n")

    print("测试2: 净利率分析")
    data2, report2 = analyze_net_margin(test_stock, print_output=False)
    print(f"完成,获取 {len(data2)} 期数据\n")

    print("测试3: ROE分析")
    data3, report3 = analyze_roe(test_stock, print_output=False)
    print(f"完成,获取 {len(data3)} 期数据\n")

    print("测试4: ROA分析")
    data4, report4 = analyze_roa(test_stock, print_output=False)
    print(f"完成,获取 {len(data4)} 期数据\n")

    print("测试5: ROIC分析")
    data5, report5 = analyze_roic(test_stock, print_output=False)
    print(f"完成,获取 {len(data5)} 期数据\n")

    print("所有盈利能力分析模块测试完成!")
