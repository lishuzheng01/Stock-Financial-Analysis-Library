# -*- coding: utf-8 -*-
"""
现金流分析模块 - Cash Flow Analysis Module
分析企业的现金流质量和管理能力
Analyze enterprise cash flow quality and management capability
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


class CashFlowAnalyzer:
    """现金流分析器基类"""

    def __init__(self, stock_code, silent=False, 
                 pd_asset=None, pd_income=None, pd_cashflow=None):
        self.stock_code = stock_code
        self.silent = silent
        self.pd_asset = pd_asset
        self.pd_income = pd_income
        self.pd_cashflow = pd_cashflow
        self.results = None

    def load_data(self):
        """加载财务数据，如果已有外部数据则跳过"""
        if self.pd_asset is not None and self.pd_income is not None and self.pd_cashflow is not None:
            if not self.silent:
                print(f"使用外部提供的数据，跳过API调用...")
            return

        if not self.silent:
            print(f"正在加载股票 {self.stock_code} 的财务数据...")

        if self.pd_asset is None:
            self.pd_asset = get_report_data(
                stock=self.stock_code,
                symbol="资产负债表",
                transpose=True
            )

        if self.pd_income is None:
            self.pd_income = get_report_data(
                stock=self.stock_code,
                symbol="利润表",
                transpose=True
            )

        if self.pd_cashflow is None:
            self.pd_cashflow = get_report_data(
                stock=self.stock_code,
                symbol="现金流量表",
                transpose=True
            )

        if not self.silent:
            print("数据加载完成!")

    def set_data(self, pd_asset=None, pd_income=None, pd_cashflow=None):
        """设置外部数据"""
        if pd_asset is not None:
            self.pd_asset = pd_asset
        if pd_income is not None:
            self.pd_income = pd_income
        if pd_cashflow is not None:
            self.pd_cashflow = pd_cashflow

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


def analyze_operating_cashflow_quality(stock_code, print_output=True, 
                                      pd_asset=None, pd_income=None, pd_cashflow=None):
    """
    经营现金流质量分析
    Operating Cash Flow Quality Analysis

    经营现金流/净利润比率
    理想值 > 1, 表示盈利质量高
    Operating Cash Flow / Net Profit Ratio
    Ideal value > 1, indicating high profit quality

    Args:
        stock_code: 股票代码
        print_output: 是否打印输出
        pd_asset: 外部提供的资产负债表数据
        pd_income: 外部提供的利润表数据
        pd_cashflow: 外部提供的现金流量表数据

    Returns:
        (DataFrame, str): (结果数据, 报告文本)
    """
    if print_output:
        print("\n" + "=" * 80)
        print("经营现金流质量分析 - Operating Cash Flow Quality Analysis")
        print("=" * 80 + "\n")

    analyzer = CashFlowAnalyzer(stock_code, silent=not print_output, 
                               pd_asset=pd_asset, pd_income=pd_income, pd_cashflow=pd_cashflow)
    analyzer.load_data()

    results = []
    max_periods = min(12, len(analyzer.pd_cashflow), len(analyzer.pd_income))

    for idx in range(max_periods):
        try:
            report_date = analyzer.get_value(analyzer.pd_cashflow, idx, '报告日', 'Report Date', '')
            if not report_date:
                continue

            # 获取经营活动现金流
            operating_cf = analyzer.get_value(
                analyzer.pd_cashflow, idx,
                '经营活动产生的现金流量净额',
                'Net Cash Flow from Operating Activities'
            )

            # 获取净利润
            net_profit = analyzer.get_value(
                analyzer.pd_income, idx,
                '归属于母公司所有者的净利润',
                'Net Profit Attributable to Parent'
            )

            # 计算比率
            cf_to_profit_ratio = operating_cf / net_profit if net_profit != 0 else 0

            # 计算应计利润
            accrual = net_profit - operating_cf

            # 应计率 = 应计利润 / 总资产
            total_assets = analyzer.get_value(analyzer.pd_asset, idx, '资产总计', 'Total Assets')
            accrual_ratio = (accrual / total_assets) * 100 if total_assets > 0 else 0

            # 同比变化
            yoy_cf_change = 0
            if idx >= 4 and idx + 4 < len(analyzer.pd_cashflow):
                prev_year_cf = analyzer.get_value(
                    analyzer.pd_cashflow, idx + 4,
                    '经营活动产生的现金流量净额',
                    'Net Cash Flow from Operating Activities'
                )
                if prev_year_cf != 0:
                    yoy_cf_change = ((operating_cf - prev_year_cf) / abs(prev_year_cf)) * 100

            results.append({
                '报告日 (Report Date)': report_date,
                '经营现金流 (Operating CF)': operating_cf,
                '净利润 (Net Profit)': net_profit,
                '现金流/利润比率': round(cf_to_profit_ratio, 4),
                '应计利润 (Accrual)': accrual,
                '应计率 (Accrual Ratio %)': round(accrual_ratio, 4),
                '经营现金流同比 (YoY %)': round(yoy_cf_change, 4)
            })

        except Exception as e:
            if not analyzer.silent:
                print(f"期数 {idx} 计算失败: {e}")
            continue

    results_df = pd.DataFrame(results)

    # 生成报告
    report_lines = []
    report_lines.append("=" * 80)
    report_lines.append("经营现金流质量分析报告 - Operating Cash Flow Quality Report")
    report_lines.append(f"股票代码: {stock_code}")
    report_lines.append(f"生成时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    report_lines.append("=" * 80)
    report_lines.append("")

    report_lines.append("【指标说明】")
    report_lines.append("现金流/利润比率 = 经营现金流 / 净利润")
    report_lines.append("  > 1: 盈利质量高,现金流充足")
    report_lines.append("  < 1: 盈利质量一般,部分利润未实现现金流入")
    report_lines.append("  < 0: 利润为正但现金流为负,存在风险")
    report_lines.append("")
    report_lines.append("应计利润 = 净利润 - 经营现金流")
    report_lines.append("应计率持续过高可能表明盈余操纵")
    report_lines.append("=" * 80)
    report_lines.append("")

    if len(results_df) > 0:
        latest = results_df.iloc[0]
        report_lines.append("【最新数据】")
        report_lines.append(f"报告日期: {latest['报告日 (Report Date)']}")
        report_lines.append(f"经营现金流: {latest['经营现金流 (Operating CF)']:,.0f}")
        report_lines.append(f"净利润: {latest['净利润 (Net Profit)']:,.0f}")
        report_lines.append(f"现金流/利润比率: {latest['现金流/利润比率']:.4f}")
        report_lines.append(f"应计利润: {latest['应计利润 (Accrual)']:,.0f}")
        report_lines.append(f"应计率: {latest['应计率 (Accrual Ratio %)']:.4f}%")
        report_lines.append("")

        report_lines.append("【质量评价】")
        ratio = latest['现金流/利润比率']
        if ratio >= 1.2:
            report_lines.append("盈利质量: 优秀 (比率 ≥ 1.2)")
        elif ratio >= 1:
            report_lines.append("盈利质量: 良好 (1 ≤ 比率 < 1.2)")
        elif ratio >= 0.8:
            report_lines.append("盈利质量: 一般 (0.8 ≤ 比率 < 1)")
        elif ratio > 0:
            report_lines.append("盈利质量: 较差 (0 < 比率 < 0.8)")
        else:
            report_lines.append("盈利质量: 警告 (比率 ≤ 0, 利润未转化为现金)")

        accrual_ratio = latest['应计率 (Accrual Ratio %)']
        if abs(accrual_ratio) > 10:
            report_lines.append(f"警告: 应计率过高 ({accrual_ratio:.2f}%), 需关注盈余质量")
        report_lines.append("")

        report_lines.append("【统计数据】")
        report_lines.append(f"平均现金流/利润比率: {results_df['现金流/利润比率'].mean():.4f}")
        report_lines.append(f"平均应计率: {results_df['应计率 (Accrual Ratio %)'].mean():.4f}%")

        # 计算比率>1的次数
        good_quality_count = len(results_df[results_df['现金流/利润比率'] >= 1])
        report_lines.append(f"盈利质量良好期数: {good_quality_count}/{len(results_df)} ({good_quality_count/len(results_df)*100:.1f}%)")
        report_lines.append("")

        report_lines.append("【详细数据】")
        display_cols = ['报告日 (Report Date)', '现金流/利润比率', '经营现金流同比 (YoY %)', '应计率 (Accrual Ratio %)']
        report_lines.append(results_df[display_cols].to_string(index=False))

    report_lines.append("")
    report_lines.append("=" * 80)
    report_text = "\n".join(report_lines)

    if print_output:
        print(report_text)
        print("\n分析完成!")

    return results_df, report_text


def analyze_free_cashflow(stock_code, print_output=True, 
                         pd_asset=None, pd_income=None, pd_cashflow=None):
    """
    自由现金流分析
    Free Cash Flow Analysis

    自由现金流 = 经营活动现金流 - 资本支出
    Free Cash Flow = Operating Cash Flow - Capital Expenditure

    资本支出 = 购建固定资产、无形资产和其他长期资产支付的现金
    CapEx = Cash Paid for Acquisition of Fixed Assets, Intangible Assets and Other Long-term Assets

    Args:
        stock_code: 股票代码
        print_output: 是否打印输出
        pd_asset: 外部提供的资产负债表数据
        pd_income: 外部提供的利润表数据
        pd_cashflow: 外部提供的现金流量表数据

    Returns:
        (DataFrame, str): (结果数据, 报告文本)
    """
    if print_output:
        print("\n" + "=" * 80)
        print("自由现金流分析 - Free Cash Flow Analysis")
        print("=" * 80 + "\n")

    analyzer = CashFlowAnalyzer(stock_code, silent=not print_output, 
                               pd_asset=pd_asset, pd_income=pd_income, pd_cashflow=pd_cashflow)
    analyzer.load_data()

    results = []
    max_periods = min(12, len(analyzer.pd_cashflow), len(analyzer.pd_income))

    for idx in range(max_periods):
        try:
            report_date = analyzer.get_value(analyzer.pd_cashflow, idx, '报告日', 'Report Date', '')
            if not report_date:
                continue

            # 经营活动现金流
            operating_cf = analyzer.get_value(
                analyzer.pd_cashflow, idx,
                '经营活动产生的现金流量净额',
                'Net Cash Flow from Operating Activities'
            )

            # 资本支出
            capex = analyzer.get_value(
                analyzer.pd_cashflow, idx,
                '购建固定资产、无形资产和其他长期资产支付的现金',
                'Cash Paid for Acquisition of Fixed Assets, Intangible Assets and Other Long-term Assets'
            )

            # 自由现金流 (CapEx通常为正值,需要减去)
            fcf = operating_cf - abs(capex)

            # 获取净利润用于对比
            net_profit = analyzer.get_value(
                analyzer.pd_income, idx,
                '归属于母公司所有者的净利润',
                'Net Profit Attributable to Parent'
            )

            # FCF/净利润比率
            fcf_to_profit = fcf / net_profit if net_profit != 0 else 0

            # 同比变化
            yoy_fcf_change = 0
            if idx >= 4 and idx + 4 < len(analyzer.pd_cashflow):
                prev_year_operating_cf = analyzer.get_value(
                    analyzer.pd_cashflow, idx + 4,
                    '经营活动产生的现金流量净额',
                    'Net Cash Flow from Operating Activities'
                )
                prev_year_capex = analyzer.get_value(
                    analyzer.pd_cashflow, idx + 4,
                    '购建固定资产、无形资产和其他长期资产支付的现金',
                    'Cash Paid for Acquisition of Fixed Assets, Intangible Assets and Other Long-term Assets'
                )
                prev_year_fcf = prev_year_operating_cf - abs(prev_year_capex)

                if prev_year_fcf != 0:
                    yoy_fcf_change = ((fcf - prev_year_fcf) / abs(prev_year_fcf)) * 100

            results.append({
                '报告日 (Report Date)': report_date,
                '自由现金流 (FCF)': fcf,
                '经营现金流 (Operating CF)': operating_cf,
                '资本支出 (CapEx)': abs(capex),
                'FCF/净利润': round(fcf_to_profit, 4),
                'FCF同比 (YoY %)': round(yoy_fcf_change, 4),
                '净利润 (Net Profit)': net_profit
            })

        except Exception as e:
            if not analyzer.silent:
                print(f"期数 {idx} 计算失败: {e}")
            continue

    results_df = pd.DataFrame(results)

    # 生成报告
    report_lines = []
    report_lines.append("=" * 80)
    report_lines.append("自由现金流分析报告 - Free Cash Flow Analysis Report")
    report_lines.append(f"股票代码: {stock_code}")
    report_lines.append(f"生成时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    report_lines.append("=" * 80)
    report_lines.append("")

    report_lines.append("【指标说明】")
    report_lines.append("自由现金流 (FCF) = 经营现金流 - 资本支出")
    report_lines.append("FCF表示企业在维持资产更新后可自由支配的现金")
    report_lines.append("  > 0: 企业有充足现金用于分红、偿债或扩张")
    report_lines.append("  < 0: 企业需要外部融资维持运营")
    report_lines.append("=" * 80)
    report_lines.append("")

    if len(results_df) > 0:
        latest = results_df.iloc[0]
        report_lines.append("【最新数据】")
        report_lines.append(f"报告日期: {latest['报告日 (Report Date)']}")
        report_lines.append(f"自由现金流: {latest['自由现金流 (FCF)']:,.0f}")
        report_lines.append(f"  经营现金流: {latest['经营现金流 (Operating CF)']:,.0f}")
        report_lines.append(f"  资本支出: {latest['资本支出 (CapEx)']:,.0f}")
        report_lines.append(f"FCF/净利润: {latest['FCF/净利润']:.4f}")
        report_lines.append(f"FCF同比变化: {latest['FCF同比 (YoY %)']:+.4f}%")
        report_lines.append("")

        report_lines.append("【现金流健康度】")
        fcf = latest['自由现金流 (FCF)']
        if fcf > 0:
            report_lines.append(f"✓ 自由现金流为正: {fcf:,.0f}")
            report_lines.append("  企业有能力支付股利、偿还债务或进行再投资")
        else:
            report_lines.append(f"✗ 自由现金流为负: {fcf:,.0f}")
            report_lines.append("  企业可能需要外部融资")

        # 计算FCF为正的期数
        positive_fcf_count = len(results_df[results_df['自由现金流 (FCF)'] > 0])
        report_lines.append(f"\nFCF为正期数: {positive_fcf_count}/{len(results_df)} ({positive_fcf_count/len(results_df)*100:.1f}%)")
        report_lines.append("")

        report_lines.append("【统计数据】")
        report_lines.append(f"平均FCF: {results_df['自由现金流 (FCF)'].mean():,.0f}")
        report_lines.append(f"平均资本支出: {results_df['资本支出 (CapEx)'].mean():,.0f}")
        report_lines.append(f"资本支出/经营现金流: {(results_df['资本支出 (CapEx)'].sum() / results_df['经营现金流 (Operating CF)'].sum() * 100):.2f}%")
        report_lines.append("")

        report_lines.append("【详细数据】")
        display_cols = ['报告日 (Report Date)', '自由现金流 (FCF)', 'FCF同比 (YoY %)', 'FCF/净利润']
        report_lines.append(results_df[display_cols].to_string(index=False))

    report_lines.append("")
    report_lines.append("=" * 80)
    report_text = "\n".join(report_lines)

    if print_output:
        print(report_text)
        print("\n分析完成!")

    return results_df, report_text


def analyze_cashflow_adequacy(stock_code, print_output=True, 
                             pd_asset=None, pd_income=None, pd_cashflow=None):
    """
    现金流充足率分析
    Cash Flow Adequacy Analysis

    现金流量充足率 = 近3年经营现金流总和 / (近3年资本支出 + 存货增加 + 现金股利)
    Cash Flow Adequacy Ratio = 3-Year Operating CF / (3-Year CapEx + Inventory Increase + Cash Dividends)

    比率 > 1: 现金流充足
    Ratio > 1: Adequate cash flow

    Args:
        stock_code: 股票代码
        print_output: 是否打印输出
        pd_asset: 外部提供的资产负债表数据
        pd_income: 外部提供的利润表数据
        pd_cashflow: 外部提供的现金流量表数据

    Returns:
        (DataFrame, str): (结果数据, 报告文本)
    """
    if print_output:
        print("\n" + "=" * 80)
        print("现金流充足率分析 - Cash Flow Adequacy Analysis")
        print("=" * 80 + "\n")

    analyzer = CashFlowAnalyzer(stock_code, silent=not print_output, 
                               pd_asset=pd_asset, pd_income=pd_income, pd_cashflow=pd_cashflow)
    analyzer.load_data()

    results = []
    max_periods = min(12, len(analyzer.pd_cashflow), len(analyzer.pd_asset))

    # 需要至少12期数据(3年)才能计算
    if max_periods < 12:
        if print_output:
            print(f"警告: 数据不足12期,仅有{max_periods}期,将使用可用数据计算")

    for idx in range(0, max_periods, 4):  # 每年计算一次(每4个季度)
        try:
            report_date = analyzer.get_value(analyzer.pd_cashflow, idx, '报告日', 'Report Date', '')
            if not report_date:
                continue

            # 计算近3年(12个季度)的累计值
            periods_to_sum = min(12, max_periods - idx)

            # 累计经营现金流
            total_operating_cf = 0
            for i in range(periods_to_sum):
                cf = analyzer.get_value(
                    analyzer.pd_cashflow, idx + i,
                    '经营活动产生的现金流量净额',
                    'Net Cash Flow from Operating Activities'
                )
                total_operating_cf += cf

            # 累计资本支出
            total_capex = 0
            for i in range(periods_to_sum):
                capex = analyzer.get_value(
                    analyzer.pd_cashflow, idx + i,
                    '购建固定资产、无形资产和其他长期资产支付的现金',
                    'Cash Paid for Acquisition of Fixed Assets, Intangible Assets and Other Long-term Assets'
                )
                total_capex += abs(capex)

            # 累计现金股利
            total_dividends = 0
            for i in range(periods_to_sum):
                dividends = analyzer.get_value(
                    analyzer.pd_cashflow, idx + i,
                    '分配股利、利润或偿付利息所支付的现金',
                    'Cash Paid for Distribution of Dividends, Profits or Payment of Interest'
                )
                total_dividends += abs(dividends)

            # 存货增加额 (期初 - 期末)
            if idx + periods_to_sum - 1 < len(analyzer.pd_asset):
                beginning_inventory = analyzer.get_value(
                    analyzer.pd_asset, idx + periods_to_sum - 1,
                    '存货', 'Inventories'
                )
                ending_inventory = analyzer.get_value(
                    analyzer.pd_asset, idx,
                    '存货', 'Inventories'
                )
                inventory_increase = max(0, ending_inventory - beginning_inventory)
            else:
                inventory_increase = 0

            # 现金流充足率
            total_needs = total_capex + inventory_increase + total_dividends
            adequacy_ratio = total_operating_cf / total_needs if total_needs > 0 else 0

            results.append({
                '报告日 (Report Date)': report_date,
                '分析周期 (Years)': periods_to_sum / 4,
                '现金流充足率': round(adequacy_ratio, 4),
                '累计经营现金流': total_operating_cf,
                '累计资本支出': total_capex,
                '存货增加': inventory_increase,
                '累计股利': total_dividends,
                '总需求': total_needs
            })

        except Exception as e:
            if not analyzer.silent:
                print(f"期数 {idx} 计算失败: {e}")
            continue

    results_df = pd.DataFrame(results)

    # 生成报告
    report_lines = []
    report_lines.append("=" * 80)
    report_lines.append("现金流充足率分析报告 - Cash Flow Adequacy Analysis Report")
    report_lines.append(f"股票代码: {stock_code}")
    report_lines.append(f"生成时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    report_lines.append("=" * 80)
    report_lines.append("")

    report_lines.append("【指标说明】")
    report_lines.append("现金流充足率 = 累计经营现金流 / (累计资本支出 + 存货增加 + 累计股利)")
    report_lines.append("  > 1: 现金流充足,能够覆盖投资和分红需求")
    report_lines.append("  < 1: 现金流不足,可能需要融资")
    report_lines.append("=" * 80)
    report_lines.append("")

    if len(results_df) > 0:
        latest = results_df.iloc[0]
        report_lines.append("【最新数据】")
        report_lines.append(f"报告日期: {latest['报告日 (Report Date)']}")
        report_lines.append(f"分析周期: {latest['分析周期 (Years)']:.1f} 年")
        report_lines.append(f"现金流充足率: {latest['现金流充足率']:.4f}")
        report_lines.append("")

        report_lines.append("【现金流来源与用途】")
        report_lines.append(f"累计经营现金流: {latest['累计经营现金流']:,.0f}")
        report_lines.append(f"\n现金需求:")
        report_lines.append(f"  累计资本支出: {latest['累计资本支出']:,.0f}")
        report_lines.append(f"  存货增加: {latest['存货增加']:,.0f}")
        report_lines.append(f"  累计股利: {latest['累计股利']:,.0f}")
        report_lines.append(f"  总需求: {latest['总需求']:,.0f}")
        report_lines.append("")

        ratio = latest['现金流充足率']
        report_lines.append("【充足性评价】")
        if ratio >= 1.5:
            report_lines.append("现金流状况: 非常充足 (比率 ≥ 1.5)")
        elif ratio >= 1:
            report_lines.append("现金流状况: 充足 (1 ≤ 比率 < 1.5)")
        elif ratio >= 0.8:
            report_lines.append("现金流状况: 基本满足 (0.8 ≤ 比率 < 1)")
        else:
            report_lines.append("现金流状况: 不足 (比率 < 0.8), 可能需要外部融资")
        report_lines.append("")

        if len(results_df) > 1:
            report_lines.append("【历史趋势】")
            report_lines.append(f"平均充足率: {results_df['现金流充足率'].mean():.4f}")
            report_lines.append(f"最高充足率: {results_df['现金流充足率'].max():.4f}")
            report_lines.append(f"最低充足率: {results_df['现金流充足率'].min():.4f}")
            report_lines.append("")

        report_lines.append("【详细数据】")
        display_cols = ['报告日 (Report Date)', '现金流充足率', '累计经营现金流', '总需求']
        report_lines.append(results_df[display_cols].to_string(index=False))

    report_lines.append("")
    report_lines.append("=" * 80)
    report_text = "\n".join(report_lines)

    if print_output:
        print(report_text)
        print("\n分析完成!")

    return results_df, report_text


def analyze_cash_conversion_cycle(stock_code, print_output=True, 
                                 pd_asset=None, pd_income=None, pd_cashflow=None):
    """
    现金循环周期分析
    Cash Conversion Cycle Analysis

    现金循环周期 = 存货周转天数 + 应收账款周转天数 - 应付账款周转天数
    Cash Conversion Cycle = Days Inventory Outstanding + Days Sales Outstanding - Days Payable Outstanding

    周期越短,营运资金管理效率越高
    Shorter cycle indicates better working capital management

    Args:
        stock_code: 股票代码
        print_output: 是否打印输出
        pd_asset: 外部提供的资产负债表数据
        pd_income: 外部提供的利润表数据
        pd_cashflow: 外部提供的现金流量表数据

    Returns:
        (DataFrame, str): (结果数据, 报告文本)
    """
    if print_output:
        print("\n" + "=" * 80)
        print("现金循环周期分析 - Cash Conversion Cycle Analysis")
        print("=" * 80 + "\n")

    analyzer = CashFlowAnalyzer(stock_code, silent=not print_output, 
                               pd_asset=pd_asset, pd_income=pd_income, pd_cashflow=pd_cashflow)
    analyzer.load_data()

    results = []
    max_periods = min(12, len(analyzer.pd_income), len(analyzer.pd_asset))

    for idx in range(max_periods):
        try:
            report_date = analyzer.get_value(analyzer.pd_income, idx, '报告日', 'Report Date', '')
            if not report_date:
                continue

            # 获取数据
            revenue = analyzer.get_value(analyzer.pd_income, idx, '营业收入', 'Operating Revenue')
            cogs = analyzer.get_value(analyzer.pd_income, idx, '营业成本', 'Operating Costs')

            # 计算平均值
            if idx < len(analyzer.pd_asset) - 1:
                current_inventory = analyzer.get_value(analyzer.pd_asset, idx, '存货', 'Inventories')
                prev_inventory = analyzer.get_value(analyzer.pd_asset, idx + 1, '存货', 'Inventories')
                avg_inventory = (current_inventory + prev_inventory) / 2

                current_ar = analyzer.get_value(analyzer.pd_asset, idx, '应收账款', 'Accounts Receivable')
                prev_ar = analyzer.get_value(analyzer.pd_asset, idx + 1, '应收账款', 'Accounts Receivable')
                avg_receivables = (current_ar + prev_ar) / 2

                current_ap = analyzer.get_value(analyzer.pd_asset, idx, '应付账款', 'Accounts Payable')
                prev_ap = analyzer.get_value(analyzer.pd_asset, idx + 1, '应付账款', 'Accounts Payable')
                avg_payables = (current_ap + prev_ap) / 2
            else:
                avg_inventory = analyzer.get_value(analyzer.pd_asset, idx, '存货', 'Inventories')
                avg_receivables = analyzer.get_value(analyzer.pd_asset, idx, '应收账款', 'Accounts Receivable')
                avg_payables = analyzer.get_value(analyzer.pd_asset, idx, '应付账款', 'Accounts Payable')

            # 计算周转天数
            # 存货周转天数 = 365 / (营业成本 / 平均存货)
            inventory_turnover = cogs / avg_inventory if avg_inventory > 0 else 0
            days_inventory = 365 / inventory_turnover if inventory_turnover > 0 else 0

            # 应收账款周转天数 = 365 / (营业收入 / 平均应收账款)
            ar_turnover = revenue / avg_receivables if avg_receivables > 0 else 0
            days_receivables = 365 / ar_turnover if ar_turnover > 0 else 0

            # 应付账款周转天数 = 365 / (营业成本 / 平均应付账款)
            ap_turnover = cogs / avg_payables if avg_payables > 0 else 0
            days_payables = 365 / ap_turnover if ap_turnover > 0 else 0

            # 现金循环周期
            ccc = days_inventory + days_receivables - days_payables

            # 同比变化
            yoy_change = 0
            if idx >= 4 and idx + 4 < max_periods:
                # 计算去年同期的CCC (简化计算)
                prev_year_inventory = analyzer.get_value(analyzer.pd_asset, idx + 4, '存货', 'Inventories')
                prev_year_ar = analyzer.get_value(analyzer.pd_asset, idx + 4, '应收账款', 'Accounts Receivable')
                prev_year_ap = analyzer.get_value(analyzer.pd_asset, idx + 4, '应付账款', 'Accounts Payable')
                prev_year_revenue = analyzer.get_value(analyzer.pd_income, idx + 4, '营业收入', 'Operating Revenue')
                prev_year_cogs = analyzer.get_value(analyzer.pd_income, idx + 4, '营业成本', 'Operating Costs')

                prev_inv_days = (prev_year_inventory / prev_year_cogs * 365) if prev_year_cogs > 0 else 0
                prev_ar_days = (prev_year_ar / prev_year_revenue * 365) if prev_year_revenue > 0 else 0
                prev_ap_days = (prev_year_ap / prev_year_cogs * 365) if prev_year_cogs > 0 else 0
                prev_ccc = prev_inv_days + prev_ar_days - prev_ap_days

                yoy_change = ccc - prev_ccc

            results.append({
                '报告日 (Report Date)': report_date,
                '现金循环周期 (CCC Days)': round(ccc, 2),
                '存货周转天数 (DIO)': round(days_inventory, 2),
                '应收账款周转天数 (DSO)': round(days_receivables, 2),
                '应付账款周转天数 (DPO)': round(days_payables, 2),
                'CCC同比变化 (Days)': round(yoy_change, 2),
                '平均存货': avg_inventory,
                '平均应收账款': avg_receivables,
                '平均应付账款': avg_payables
            })

        except Exception as e:
            if not analyzer.silent:
                print(f"期数 {idx} 计算失败: {e}")
            continue

    results_df = pd.DataFrame(results)

    # 生成报告
    report_lines = []
    report_lines.append("=" * 80)
    report_lines.append("现金循环周期分析报告 - Cash Conversion Cycle Analysis Report")
    report_lines.append(f"股票代码: {stock_code}")
    report_lines.append(f"生成时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    report_lines.append("=" * 80)
    report_lines.append("")

    report_lines.append("【指标说明】")
    report_lines.append("现金循环周期 (CCC) = 存货周转天数 + 应收账款周转天数 - 应付账款周转天数")
    report_lines.append("  DIO (Days Inventory Outstanding): 存货转换为销售所需天数")
    report_lines.append("  DSO (Days Sales Outstanding): 应收账款转换为现金所需天数")
    report_lines.append("  DPO (Days Payable Outstanding): 应付账款支付期限")
    report_lines.append("")
    report_lines.append("CCC越短越好,表示营运资金效率高")
    report_lines.append("CCC为负值表示企业占用上下游资金,现金流优势明显")
    report_lines.append("=" * 80)
    report_lines.append("")

    if len(results_df) > 0:
        latest = results_df.iloc[0]
        report_lines.append("【最新数据】")
        report_lines.append(f"报告日期: {latest['报告日 (Report Date)']}")
        report_lines.append(f"现金循环周期: {latest['现金循环周期 (CCC Days)']:.2f} 天")
        report_lines.append("")
        report_lines.append("组成部分:")
        report_lines.append(f"  存货周转天数 (DIO): {latest['存货周转天数 (DIO)']:.2f} 天")
        report_lines.append(f"  应收账款周转天数 (DSO): {latest['应收账款周转天数 (DSO)']:.2f} 天")
        report_lines.append(f"  应付账款周转天数 (DPO): {latest['应付账款周转天数 (DPO)']:.2f} 天")
        report_lines.append(f"CCC同比变化: {latest['CCC同比变化 (Days)']:+.2f} 天")
        report_lines.append("")

        report_lines.append("【效率评价】")
        ccc = latest['现金循环周期 (CCC Days)']
        if ccc < 0:
            report_lines.append(f"营运资金效率: 卓越 (CCC < 0)")
            report_lines.append("企业占用上下游资金,现金流优势明显")
        elif ccc < 30:
            report_lines.append(f"营运资金效率: 优秀 (0 ≤ CCC < 30)")
        elif ccc < 60:
            report_lines.append(f"营运资金效率: 良好 (30 ≤ CCC < 60)")
        elif ccc < 90:
            report_lines.append(f"营运资金效率: 一般 (60 ≤ CCC < 90)")
        else:
            report_lines.append(f"营运资金效率: 较差 (CCC ≥ 90)")
            report_lines.append("建议: 优化存货管理,加快应收账款回收,延长应付账款期限")
        report_lines.append("")

        report_lines.append("【统计数据】")
        report_lines.append(f"平均CCC: {results_df['现金循环周期 (CCC Days)'].mean():.2f} 天")
        report_lines.append(f"最短CCC: {results_df['现金循环周期 (CCC Days)'].min():.2f} 天")
        report_lines.append(f"最长CCC: {results_df['现金循环周期 (CCC Days)'].max():.2f} 天")
        report_lines.append(f"平均DIO: {results_df['存货周转天数 (DIO)'].mean():.2f} 天")
        report_lines.append(f"平均DSO: {results_df['应收账款周转天数 (DSO)'].mean():.2f} 天")
        report_lines.append(f"平均DPO: {results_df['应付账款周转天数 (DPO)'].mean():.2f} 天")
        report_lines.append("")

        report_lines.append("【详细数据】")
        display_cols = ['报告日 (Report Date)', '现金循环周期 (CCC Days)', '存货周转天数 (DIO)', '应收账款周转天数 (DSO)', '应付账款周转天数 (DPO)']
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

    print("测试1: 经营现金流质量分析")
    data1, report1 = analyze_operating_cashflow_quality(test_stock, print_output=False)
    print(f"完成,获取 {len(data1)} 期数据\n")

    print("测试2: 自由现金流分析")
    data2, report2 = analyze_free_cashflow(test_stock, print_output=False)
    print(f"完成,获取 {len(data2)} 期数据\n")

    print("测试3: 现金流充足率分析")
    data3, report3 = analyze_cashflow_adequacy(test_stock, print_output=False)
    print(f"完成,获取 {len(data3)} 期数据\n")

    print("测试4: 现金循环周期分析")
    data4, report4 = analyze_cash_conversion_cycle(test_stock, print_output=False)
    print(f"完成,获取 {len(data4)} 期数据\n")

    print("所有现金流分析模块测试完成!")
