# -*- coding: utf-8 -*-
"""
相对估值分析模块 - Valuation Ratios Analysis Module
分析企业的相对估值水平
Analyze enterprise relative valuation levels
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


class ValuationAnalyzer:
    """估值分析器基类"""

    def __init__(self, stock_code, silent=False):
        self.stock_code = stock_code
        self.silent = silent
        self.pd_asset = None
        self.pd_income = None
        self.price_data = None
        self.results = None

    def load_data(self):
        """加载财务数据和价格数据"""
        if not self.silent:
            print(f"正在加载股票 {self.stock_code} 的财务数据和价格数据...")

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

        # 获取最近2年的价格数据
        from datetime import datetime, timedelta
        end_date = datetime.now().strftime("%Y%m%d")
        start_date = (datetime.now() - timedelta(days=730)).strftime("%Y%m%d")

        try:
            self.price_data = get_stock_data(
                stock=self.stock_code,
                start=start_date,
                end=end_date
            )
        except Exception as e:
            if not self.silent:
                print(f"价格数据加载失败: {e}")
            self.price_data = None

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

    def get_latest_price(self):
        """获取最新收盘价"""
        if self.price_data is None or len(self.price_data) == 0:
            return 0.0
        return float(self.price_data['close'].iloc[-1])


def analyze_pe_ratio(stock_code, print_output=True):
    """
    市盈率分析
    PE Ratio Analysis

    静态PE = 当前股价 / 上年度EPS
    动态PE = 当前股价 / 最近4季度滚动EPS
    Static PE = Current Price / Last Year EPS
    Dynamic PE = Current Price / Rolling 4-Quarter EPS

    Args:
        stock_code: 股票代码
        print_output: 是否打印输出

    Returns:
        (DataFrame, str): (结果数据, 报告文本)
    """
    if print_output:
        print("\n" + "=" * 80)
        print("市盈率分析 - PE Ratio Analysis")
        print("=" * 80 + "\n")

    analyzer = ValuationAnalyzer(stock_code, silent=not print_output)
    analyzer.load_data()

    results = []
    max_periods = min(12, len(analyzer.pd_income))

    latest_price = analyzer.get_latest_price()
    if latest_price == 0:
        if print_output:
            print("警告: 无法获取股价数据")

    for idx in range(max_periods):
        try:
            report_date = analyzer.get_value(analyzer.pd_income, idx, '报告日', 'Report Date', '')
            if not report_date:
                continue

            # 获取EPS
            eps = analyzer.get_value(analyzer.pd_income, idx, '基本每股收益', 'Basic EPS')

            # 计算滚动4季度EPS (动态PE)
            rolling_eps = 0.0
            if idx + 3 < len(analyzer.pd_income):
                for i in range(4):
                    rolling_eps += analyzer.get_value(analyzer.pd_income, idx + i, '基本每股收益', 'Basic EPS')

            # 静态PE: 使用年度EPS
            static_pe = latest_price / eps if eps > 0 else 0

            # 动态PE: 使用滚动EPS
            dynamic_pe = latest_price / rolling_eps if rolling_eps > 0 else 0

            # 计算EPS增长率
            eps_growth = 0
            if idx >= 4 and idx + 4 < len(analyzer.pd_income):
                prev_year_eps = analyzer.get_value(analyzer.pd_income, idx + 4, '基本每股收益', 'Basic EPS')
                if prev_year_eps != 0:
                    eps_growth = ((eps - prev_year_eps) / abs(prev_year_eps)) * 100

            results.append({
                '报告日 (Report Date)': report_date,
                '股价 (Price)': latest_price,
                'EPS': round(eps, 4),
                '滚动EPS (Rolling EPS)': round(rolling_eps, 4),
                '静态PE (Static PE)': round(static_pe, 4),
                '动态PE (Dynamic PE)': round(dynamic_pe, 4),
                'EPS增长率 (EPS Growth %)': round(eps_growth, 4)
            })

        except Exception as e:
            if not analyzer.silent:
                print(f"期数 {idx} 计算失败: {e}")
            continue

    results_df = pd.DataFrame(results)

    # 生成报告
    report_lines = []
    report_lines.append("=" * 80)
    report_lines.append("市盈率分析报告 - PE Ratio Analysis Report")
    report_lines.append(f"股票代码: {stock_code}")
    report_lines.append(f"生成时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    report_lines.append("=" * 80)
    report_lines.append("")

    if len(results_df) > 0:
        latest = results_df.iloc[0]
        report_lines.append("【最新数据】")
        report_lines.append(f"报告日期: {latest['报告日 (Report Date)']}")
        report_lines.append(f"当前股价: {latest['股价 (Price)']:.2f}")
        report_lines.append(f"最新EPS: {latest['EPS']:.4f}")
        report_lines.append(f"滚动EPS (4Q): {latest['滚动EPS (Rolling EPS)']:.4f}")
        report_lines.append(f"静态PE: {latest['静态PE (Static PE)']:.4f}")
        report_lines.append(f"动态PE: {latest['动态PE (Dynamic PE)']:.4f}")
        report_lines.append(f"EPS增长率: {latest['EPS增长率 (EPS Growth %)']:+.4f}%")
        report_lines.append("")

        report_lines.append("【估值评价】")
        dynamic_pe = latest['动态PE (Dynamic PE)']
        if dynamic_pe > 0:
            if dynamic_pe < 15:
                report_lines.append("估值水平: 低估 (PE < 15)")
            elif dynamic_pe < 25:
                report_lines.append("估值水平: 合理 (15 ≤ PE < 25)")
            elif dynamic_pe < 40:
                report_lines.append("估值水平: 偏高 (25 ≤ PE < 40)")
            else:
                report_lines.append("估值水平: 高估 (PE ≥ 40)")
        report_lines.append("")

        report_lines.append("【历史数据】")
        display_cols = ['报告日 (Report Date)', '静态PE (Static PE)', '动态PE (Dynamic PE)', 'EPS增长率 (EPS Growth %)']
        report_lines.append(results_df[display_cols].to_string(index=False))

    report_lines.append("")
    report_lines.append("=" * 80)
    report_text = "\n".join(report_lines)

    if print_output:
        print(report_text)
        print("\n分析完成!")

    return results_df, report_text


def analyze_pb_ratio(stock_code, print_output=True):
    """
    市净率分析
    PB Ratio Analysis

    PB = 股价 / 每股净资产
    PB = Price / Book Value per Share

    Args:
        stock_code: 股票代码
        print_output: 是否打印输出

    Returns:
        (DataFrame, str): (结果数据, 报告文本)
    """
    if print_output:
        print("\n" + "=" * 80)
        print("市净率分析 - PB Ratio Analysis")
        print("=" * 80 + "\n")

    analyzer = ValuationAnalyzer(stock_code, silent=not print_output)
    analyzer.load_data()

    results = []
    max_periods = min(12, len(analyzer.pd_asset))

    latest_price = analyzer.get_latest_price()

    for idx in range(max_periods):
        try:
            report_date = analyzer.get_value(analyzer.pd_asset, idx, '报告日', 'Report Date', '')
            if not report_date:
                continue

            # 获取股东权益和股本
            shareholders_equity = analyzer.get_value(analyzer.pd_asset, idx, '归属于母公司股东权益合计', 'Total Equity Attributable to Shareholders of the Parent Company')
            share_capital = analyzer.get_value(analyzer.pd_asset, idx, '实收资本(或股本)', 'Paid-in Capital (or Share Capital)')

            if share_capital == 0:
                continue

            # 每股净资产 = 股东权益 / 股本
            bvps = shareholders_equity / share_capital

            # PB = 股价 / 每股净资产
            pb_ratio = latest_price / bvps if bvps > 0 else 0

            # 计算净资产收益率
            roe = 0
            if idx < len(analyzer.pd_income):
                net_profit = analyzer.get_value(analyzer.pd_income, idx, '归属于母公司所有者的净利润', 'Net Profit Attributable to Parent')
                if shareholders_equity > 0:
                    roe = (net_profit / shareholders_equity) * 100

            results.append({
                '报告日 (Report Date)': report_date,
                '股价 (Price)': latest_price,
                '每股净资产 (BVPS)': round(bvps, 4),
                'PB市净率': round(pb_ratio, 4),
                'ROE (%)': round(roe, 4),
                '股东权益 (Equity)': shareholders_equity,
                '股本 (Share Capital)': share_capital
            })

        except Exception as e:
            if not analyzer.silent:
                print(f"期数 {idx} 计算失败: {e}")
            continue

    results_df = pd.DataFrame(results)

    # 生成报告
    report_lines = []
    report_lines.append("=" * 80)
    report_lines.append("市净率分析报告 - PB Ratio Analysis Report")
    report_lines.append(f"股票代码: {stock_code}")
    report_lines.append(f"生成时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    report_lines.append("=" * 80)
    report_lines.append("")

    if len(results_df) > 0:
        latest = results_df.iloc[0]
        report_lines.append("【最新数据】")
        report_lines.append(f"报告日期: {latest['报告日 (Report Date)']}")
        report_lines.append(f"当前股价: {latest['股价 (Price)']:.2f}")
        report_lines.append(f"每股净资产: {latest['每股净资产 (BVPS)']:.4f}")
        report_lines.append(f"PB市净率: {latest['PB市净率']:.4f}")
        report_lines.append(f"ROE: {latest['ROE (%)']:.4f}%")
        report_lines.append("")

        report_lines.append("【估值评价】")
        pb = latest['PB市净率']
        roe_val = latest['ROE (%)']
        if pb > 0:
            if pb < 1:
                report_lines.append("估值水平: 破净 (PB < 1), 可能存在投资机会或基本面问题")
            elif pb < 3:
                report_lines.append("估值水平: 合理 (1 ≤ PB < 3)")
            elif pb < 5:
                report_lines.append("估值水平: 偏高 (3 ≤ PB < 5)")
            else:
                report_lines.append("估值水平: 高估 (PB ≥ 5)")

            # PB-ROE合理性检验
            if roe_val > 0:
                pb_roe_ratio = pb / roe_val
                report_lines.append(f"PB/ROE比率: {pb_roe_ratio:.4f} (理论上应接近1)")
        report_lines.append("")

        report_lines.append("【统计数据】")
        report_lines.append(f"平均PB: {results_df['PB市净率'].mean():.4f}")
        report_lines.append(f"最高PB: {results_df['PB市净率'].max():.4f}")
        report_lines.append(f"最低PB: {results_df['PB市净率'].min():.4f}")
        report_lines.append("")

        report_lines.append("【历史数据】")
        display_cols = ['报告日 (Report Date)', 'PB市净率', 'ROE (%)', '每股净资产 (BVPS)']
        report_lines.append(results_df[display_cols].to_string(index=False))

    report_lines.append("")
    report_lines.append("=" * 80)
    report_text = "\n".join(report_lines)

    if print_output:
        print(report_text)
        print("\n分析完成!")

    return results_df, report_text


def analyze_ps_ratio(stock_code, print_output=True):
    """
    市销率分析
    PS Ratio Analysis

    PS = 市值 / 营业收入
    PS = Market Cap / Revenue

    Args:
        stock_code: 股票代码
        print_output: 是否打印输出

    Returns:
        (DataFrame, str): (结果数据, 报告文本)
    """
    if print_output:
        print("\n" + "=" * 80)
        print("市销率分析 - PS Ratio Analysis")
        print("=" * 80 + "\n")

    analyzer = ValuationAnalyzer(stock_code, silent=not print_output)
    analyzer.load_data()

    results = []
    max_periods = min(12, len(analyzer.pd_income), len(analyzer.pd_asset))

    latest_price = analyzer.get_latest_price()

    for idx in range(max_periods):
        try:
            report_date = analyzer.get_value(analyzer.pd_income, idx, '报告日', 'Report Date', '')
            if not report_date:
                continue

            # 获取营业收入
            revenue = analyzer.get_value(analyzer.pd_income, idx, '营业收入', 'Operating Revenue')

            # 获取股本
            share_capital = analyzer.get_value(analyzer.pd_asset, idx, '实收资本(或股本)', 'Paid-in Capital (or Share Capital)')

            if share_capital == 0 or revenue == 0:
                continue

            # 计算市值
            market_cap = latest_price * share_capital

            # PS = 市值 / 营业收入
            ps_ratio = market_cap / revenue if revenue > 0 else 0

            # 每股营收
            revenue_per_share = revenue / share_capital

            # 计算净利率
            net_profit = analyzer.get_value(analyzer.pd_income, idx, '归属于母公司所有者的净利润', 'Net Profit Attributable to Parent')
            net_margin = (net_profit / revenue) * 100 if revenue > 0 else 0

            results.append({
                '报告日 (Report Date)': report_date,
                '股价 (Price)': latest_price,
                'PS市销率': round(ps_ratio, 4),
                '每股营收 (Revenue per Share)': round(revenue_per_share, 4),
                '净利率 (Net Margin %)': round(net_margin, 4),
                '市值 (Market Cap)': market_cap,
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
    report_lines.append("市销率分析报告 - PS Ratio Analysis Report")
    report_lines.append(f"股票代码: {stock_code}")
    report_lines.append(f"生成时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    report_lines.append("=" * 80)
    report_lines.append("")

    if len(results_df) > 0:
        latest = results_df.iloc[0]
        report_lines.append("【最新数据】")
        report_lines.append(f"报告日期: {latest['报告日 (Report Date)']}")
        report_lines.append(f"当前股价: {latest['股价 (Price)']:.2f}")
        report_lines.append(f"PS市销率: {latest['PS市销率']:.4f}")
        report_lines.append(f"每股营收: {latest['每股营收 (Revenue per Share)']:.4f}")
        report_lines.append(f"净利率: {latest['净利率 (Net Margin %)']:.4f}%")
        report_lines.append(f"市值: {latest['市值 (Market Cap)']:,.0f}")
        report_lines.append("")

        report_lines.append("【估值评价】")
        ps = latest['PS市销率']
        if ps > 0:
            if ps < 1:
                report_lines.append("估值水平: 低估 (PS < 1)")
            elif ps < 3:
                report_lines.append("估值水平: 合理 (1 ≤ PS < 3)")
            elif ps < 5:
                report_lines.append("估值水平: 偏高 (3 ≤ PS < 5)")
            else:
                report_lines.append("估值水平: 高估 (PS ≥ 5)")

        report_lines.append("注: PS市销率适用于盈利波动大或亏损企业的估值")
        report_lines.append("")

        report_lines.append("【统计数据】")
        report_lines.append(f"平均PS: {results_df['PS市销率'].mean():.4f}")
        report_lines.append(f"最高PS: {results_df['PS市销率'].max():.4f}")
        report_lines.append(f"最低PS: {results_df['PS市销率'].min():.4f}")
        report_lines.append(f"平均净利率: {results_df['净利率 (Net Margin %)'].mean():.4f}%")
        report_lines.append("")

        report_lines.append("【历史数据】")
        display_cols = ['报告日 (Report Date)', 'PS市销率', '净利率 (Net Margin %)', '每股营收 (Revenue per Share)']
        report_lines.append(results_df[display_cols].to_string(index=False))

    report_lines.append("")
    report_lines.append("=" * 80)
    report_text = "\n".join(report_lines)

    if print_output:
        print(report_text)
        print("\n分析完成!")

    return results_df, report_text


def analyze_peg_ratio(stock_code, print_output=True):
    """
    PEG分析
    PEG Ratio Analysis

    PEG = PE / 净利润增长率
    PEG = PE / Earnings Growth Rate

    PEG < 1: 低估
    PEG = 1: 合理
    PEG > 1: 高估

    Args:
        stock_code: 股票代码
        print_output: 是否打印输出

    Returns:
        (DataFrame, str): (结果数据, 报告文本)
    """
    if print_output:
        print("\n" + "=" * 80)
        print("PEG分析 - PEG Ratio Analysis")
        print("=" * 80 + "\n")

    analyzer = ValuationAnalyzer(stock_code, silent=not print_output)
    analyzer.load_data()

    results = []
    max_periods = min(12, len(analyzer.pd_income))

    latest_price = analyzer.get_latest_price()

    for idx in range(max_periods):
        try:
            report_date = analyzer.get_value(analyzer.pd_income, idx, '报告日', 'Report Date', '')
            if not report_date:
                continue

            # 获取EPS
            eps = analyzer.get_value(analyzer.pd_income, idx, '基本每股收益', 'Basic EPS')

            # 计算PE
            pe_ratio = latest_price / eps if eps > 0 else 0

            # 计算净利润增长率
            net_profit = analyzer.get_value(analyzer.pd_income, idx, '归属于母公司所有者的净利润', 'Net Profit Attributable to Parent')

            # 同比增长率
            yoy_growth = 0
            if idx >= 4 and idx + 4 < len(analyzer.pd_income):
                prev_year_profit = analyzer.get_value(analyzer.pd_income, idx + 4, '归属于母公司所有者的净利润', 'Net Profit Attributable to Parent')
                if prev_year_profit != 0:
                    yoy_growth = ((net_profit - prev_year_profit) / abs(prev_year_profit)) * 100

            # 计算PEG
            peg_ratio = pe_ratio / yoy_growth if yoy_growth > 0 else 0

            results.append({
                '报告日 (Report Date)': report_date,
                '股价 (Price)': latest_price,
                'EPS': round(eps, 4),
                'PE市盈率': round(pe_ratio, 4),
                '净利润增长率 (Growth %)': round(yoy_growth, 4),
                'PEG': round(peg_ratio, 4),
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
    report_lines.append("PEG分析报告 - PEG Ratio Analysis Report")
    report_lines.append(f"股票代码: {stock_code}")
    report_lines.append(f"生成时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    report_lines.append("=" * 80)
    report_lines.append("")

    report_lines.append("【PEG指标说明】")
    report_lines.append("PEG = PE / 净利润增长率")
    report_lines.append("PEG < 1: 低估 (股价增长慢于盈利增长)")
    report_lines.append("PEG = 1: 合理 (股价增长与盈利增长匹配)")
    report_lines.append("PEG > 1: 高估 (股价增长快于盈利增长)")
    report_lines.append("=" * 80)
    report_lines.append("")

    if len(results_df) > 0:
        latest = results_df.iloc[0]
        report_lines.append("【最新数据】")
        report_lines.append(f"报告日期: {latest['报告日 (Report Date)']}")
        report_lines.append(f"当前股价: {latest['股价 (Price)']:.2f}")
        report_lines.append(f"EPS: {latest['EPS']:.4f}")
        report_lines.append(f"PE市盈率: {latest['PE市盈率']:.4f}")
        report_lines.append(f"净利润增长率: {latest['净利润增长率 (Growth %)']:+.4f}%")
        report_lines.append(f"PEG: {latest['PEG']:.4f}")
        report_lines.append("")

        report_lines.append("【估值评价】")
        peg = latest['PEG']
        growth = latest['净利润增长率 (Growth %)']

        if growth <= 0:
            report_lines.append("警告: 净利润负增长,PEG指标不适用")
        elif peg > 0:
            if peg < 0.5:
                report_lines.append("估值水平: 严重低估 (PEG < 0.5)")
            elif peg < 1:
                report_lines.append("估值水平: 低估 (0.5 ≤ PEG < 1)")
            elif peg <= 1.5:
                report_lines.append("估值水平: 合理 (1 ≤ PEG ≤ 1.5)")
            elif peg < 2:
                report_lines.append("估值水平: 偏高 (1.5 < PEG < 2)")
            else:
                report_lines.append("估值水平: 高估 (PEG ≥ 2)")
        report_lines.append("")

        # 过滤有效PEG数据
        valid_peg = results_df[results_df['PEG'] > 0]['PEG']
        if len(valid_peg) > 0:
            report_lines.append("【统计数据】")
            report_lines.append(f"平均PEG: {valid_peg.mean():.4f}")
            report_lines.append(f"最高PEG: {valid_peg.max():.4f}")
            report_lines.append(f"最低PEG: {valid_peg.min():.4f}")
            report_lines.append(f"平均增长率: {results_df['净利润增长率 (Growth %)'].mean():.4f}%")
            report_lines.append("")

        report_lines.append("【历史数据】")
        display_cols = ['报告日 (Report Date)', 'PE市盈率', '净利润增长率 (Growth %)', 'PEG']
        report_lines.append(results_df[display_cols].to_string(index=False))

    report_lines.append("")
    report_lines.append("=" * 80)
    report_text = "\n".join(report_lines)

    if print_output:
        print(report_text)
        print("\n分析完成!")

    return results_df, report_text


def analyze_ev_ebitda(stock_code, print_output=True):
    """
    EV/EBITDA分析
    EV/EBITDA Ratio Analysis

    EV = 市值 + 总负债 - 现金及现金等价物
    EBITDA = EBIT + 折旧 + 摊销
    EBIT = 营业利润 + 利息费用

    EV/EBITDA适用于资本密集型企业估值

    Args:
        stock_code: 股票代码
        print_output: 是否打印输出

    Returns:
        (DataFrame, str): (结果数据, 报告文本)
    """
    if print_output:
        print("\n" + "=" * 80)
        print("EV/EBITDA分析 - EV/EBITDA Ratio Analysis")
        print("=" * 80 + "\n")

    analyzer = ValuationAnalyzer(stock_code, silent=not print_output)
    analyzer.load_data()

    results = []
    max_periods = min(12, len(analyzer.pd_income), len(analyzer.pd_asset))

    latest_price = analyzer.get_latest_price()

    for idx in range(max_periods):
        try:
            report_date = analyzer.get_value(analyzer.pd_income, idx, '报告日', 'Report Date', '')
            if not report_date:
                continue

            # 计算EBIT
            operating_profit = analyzer.get_value(analyzer.pd_income, idx, '营业利润', 'Operating Profit')
            interest_expense = analyzer.get_value(analyzer.pd_income, idx, '利息费用', 'Interest Expenses')
            financial_expenses = analyzer.get_value(analyzer.pd_income, idx, '财务费用', 'Financial Expenses')

            actual_interest = interest_expense if interest_expense > 0 else (financial_expenses if financial_expenses > 0 else 0)
            ebit = operating_profit + actual_interest

            # 计算折旧摊销 (简化: 从现金流量表获取)
            depreciation = 0.0
            if analyzer.pd_income is not None and idx < len(analyzer.pd_income):
                # 尝试从利润表获取
                depreciation = analyzer.get_value(analyzer.pd_income, idx, '折旧费用', 'Depreciation Expenses')

            # 如果没有直接的折旧数据,用固定资产变化估算
            if depreciation == 0:
                if idx < len(analyzer.pd_asset) - 1:
                    current_fa = analyzer.get_value(analyzer.pd_asset, idx, '固定资产净额', 'Net Fixed Assets')
                    prev_fa = analyzer.get_value(analyzer.pd_asset, idx + 1, '固定资产净额', 'Net Fixed Assets')
                    accumulated_dep = analyzer.get_value(analyzer.pd_asset, idx, '累计折旧', 'Accumulated Depreciation')
                    if accumulated_dep > 0:
                        depreciation = accumulated_dep * 0.25  # 简化估算: 年折旧率约25%

            # EBITDA
            ebitda = ebit + depreciation

            # 计算EV (企业价值)
            share_capital = analyzer.get_value(analyzer.pd_asset, idx, '实收资本(或股本)', 'Paid-in Capital (or Share Capital)')
            total_liabilities = analyzer.get_value(analyzer.pd_asset, idx, '负债合计', 'Total Liabilities')
            cash = analyzer.get_value(analyzer.pd_asset, idx, '货币资金', 'Cash and Cash Equivalents')

            market_cap = latest_price * share_capital
            ev = market_cap + total_liabilities - cash

            # EV/EBITDA
            ev_ebitda_ratio = ev / ebitda if ebitda > 0 else 0

            results.append({
                '报告日 (Report Date)': report_date,
                'EV/EBITDA': round(ev_ebitda_ratio, 4),
                '企业价值 (EV)': ev,
                'EBITDA': ebitda,
                'EBIT': ebit,
                '折旧摊销 (D&A)': depreciation,
                '市值 (Market Cap)': market_cap,
                '总负债 (Debt)': total_liabilities,
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
    report_lines.append("EV/EBITDA分析报告 - EV/EBITDA Ratio Analysis Report")
    report_lines.append(f"股票代码: {stock_code}")
    report_lines.append(f"生成时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    report_lines.append("=" * 80)
    report_lines.append("")

    report_lines.append("【指标说明】")
    report_lines.append("EV (企业价值) = 市值 + 总负债 - 现金")
    report_lines.append("EBITDA = EBIT + 折旧 + 摊销")
    report_lines.append("EV/EBITDA消除了资本结构和折旧政策的影响,适合跨公司对比")
    report_lines.append("=" * 80)
    report_lines.append("")

    if len(results_df) > 0:
        latest = results_df.iloc[0]
        report_lines.append("【最新数据】")
        report_lines.append(f"报告日期: {latest['报告日 (Report Date)']}")
        report_lines.append(f"EV/EBITDA: {latest['EV/EBITDA']:.4f}")
        report_lines.append(f"企业价值 (EV): {latest['企业价值 (EV)']:,.0f}")
        report_lines.append(f"EBITDA: {latest['EBITDA']:,.0f}")
        report_lines.append(f"  其中 EBIT: {latest['EBIT']:,.0f}")
        report_lines.append(f"  折旧摊销: {latest['折旧摊销 (D&A)']:,.0f}")
        report_lines.append("")

        report_lines.append("【企业价值构成】")
        report_lines.append(f"市值: {latest['市值 (Market Cap)']:,.0f}")
        report_lines.append(f"总负债: {latest['总负债 (Debt)']:,.0f}")
        report_lines.append(f"现金: {latest['现金 (Cash)']:,.0f}")
        report_lines.append(f"企业价值 = {latest['市值 (Market Cap)']:,.0f} + {latest['总负债 (Debt)']:,.0f} - {latest['现金 (Cash)']:,.0f} = {latest['企业价值 (EV)']:,.0f}")
        report_lines.append("")

        report_lines.append("【估值评价】")
        ev_ebitda = latest['EV/EBITDA']
        if ev_ebitda > 0:
            if ev_ebitda < 5:
                report_lines.append("估值水平: 低估 (EV/EBITDA < 5)")
            elif ev_ebitda < 10:
                report_lines.append("估值水平: 合理 (5 ≤ EV/EBITDA < 10)")
            elif ev_ebitda < 15:
                report_lines.append("估值水平: 偏高 (10 ≤ EV/EBITDA < 15)")
            else:
                report_lines.append("估值水平: 高估 (EV/EBITDA ≥ 15)")
        report_lines.append("注: EV/EBITDA适用于资本密集型行业,如制造业、能源等")
        report_lines.append("")

        # 过滤有效数据
        valid_ev = results_df[results_df['EV/EBITDA'] > 0]['EV/EBITDA']
        if len(valid_ev) > 0:
            report_lines.append("【统计数据】")
            report_lines.append(f"平均EV/EBITDA: {valid_ev.mean():.4f}")
            report_lines.append(f"最高EV/EBITDA: {valid_ev.max():.4f}")
            report_lines.append(f"最低EV/EBITDA: {valid_ev.min():.4f}")
            report_lines.append("")

        report_lines.append("【历史数据】")
        display_cols = ['报告日 (Report Date)', 'EV/EBITDA', 'EBITDA', 'EBIT']
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

    print("测试1: PE市盈率分析")
    data1, report1 = analyze_pe_ratio(test_stock, print_output=False)
    print(f"完成,获取 {len(data1)} 期数据\n")

    print("测试2: PB市净率分析")
    data2, report2 = analyze_pb_ratio(test_stock, print_output=False)
    print(f"完成,获取 {len(data2)} 期数据\n")

    print("测试3: PS市销率分析")
    data3, report3 = analyze_ps_ratio(test_stock, print_output=False)
    print(f"完成,获取 {len(data3)} 期数据\n")

    print("测试4: PEG分析")
    data4, report4 = analyze_peg_ratio(test_stock, print_output=False)
    print(f"完成,获取 {len(data4)} 期数据\n")

    print("测试5: EV/EBITDA分析")
    data5, report5 = analyze_ev_ebitda(test_stock, print_output=False)
    print(f"完成,获取 {len(data5)} 期数据\n")

    print("所有相对估值分析模块测试完成!")
