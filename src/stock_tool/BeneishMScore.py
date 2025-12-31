import pandas as pd
import numpy as np
from stock_tool.get_report_data import get_report_data

class BeneishMScore:
    def __init__(self, stock_code, silent=False):
        self.stock = stock_code
        self.silent = silent
        self.load_data()
        self.results = None
        
    def get_column(self, df, cn_name, en_name):
        """获取列，支持中英文 / Get column with CN/EN support"""
        if cn_name in df.columns:
            return cn_name
        elif en_name in df.columns:
            return en_name
        else:
            return None
    
    def load_data(self):
        """加载财务数据 / Load financial data"""
        if not self.silent:
            print(f"正在加载股票 {self.stock} 的财务数据... (Loading financial data for stock {self.stock}...)")
        
        self.pd_asset = get_report_data(stock=self.stock, symbol="资产负债表", transpose=True)
        self.pd_income = get_report_data(stock=self.stock, symbol="利润表", transpose=True)
        self.pd_cashflow = get_report_data(stock=self.stock, symbol="现金流量表", transpose=True)
        
        # 找到日期列
        date_col_asset = self.get_column(self.pd_asset, '报告日', 'Report Date')
        date_col_income = self.get_column(self.pd_income, '报告日', 'Report Date')
        date_col_cashflow = self.get_column(self.pd_cashflow, '报告日', 'Report Date')
        
        # 确保数据按日期排序
        if date_col_asset:
            self.pd_asset = self.pd_asset.sort_values(date_col_asset).reset_index(drop=True)
        if date_col_income:
            self.pd_income = self.pd_income.sort_values(date_col_income).reset_index(drop=True)
        if date_col_cashflow:
            self.pd_cashflow = self.pd_cashflow.sort_values(date_col_cashflow).reset_index(drop=True)
        
        # 保存日期列名
        self.date_col_asset = date_col_asset
        self.date_col_income = date_col_income
        self.date_col_cashflow = date_col_cashflow
        
        if not self.silent:
            print("数据加载完成！(Data loaded successfully!)")
    
    def get_value(self, df, idx, cn_name, en_name):
        """获取数值，支持中英文列名 / Get value with CN/EN column support"""
        col = self.get_column(df, cn_name, en_name)
        if col and idx < len(df):
            value = df.iloc[idx][col]
            try:
                return float(value) if pd.notna(value) and value != '' else 0.0
            except:
                return 0.0
        return 0.0
    
    def calculate_dsri(self, current_idx, prior_idx):
        """Days Sales in Receivables Index (应收账款天数指数 / DSRI)"""
        current_receivables = self.get_value(self.pd_asset, current_idx, '应收账款', 'Accounts Receivable')
        prior_receivables = self.get_value(self.pd_asset, prior_idx, '应收账款', 'Accounts Receivable')
        
        current_revenue = self.get_value(self.pd_income, current_idx, '营业收入', 'Operating Revenue')
        prior_revenue = self.get_value(self.pd_income, prior_idx, '营业收入', 'Operating Revenue')
        
        if prior_revenue == 0 or current_revenue == 0:
            return np.nan
        
        current_ratio = current_receivables / current_revenue
        prior_ratio = prior_receivables / prior_revenue
        
        if prior_ratio == 0:
            return 1.0
        
        return current_ratio / prior_ratio
    
    def calculate_gmi(self, current_idx, prior_idx):
        """Gross Margin Index (毛利率指数 / GMI)"""
        current_revenue = self.get_value(self.pd_income, current_idx, '营业收入', 'Operating Revenue')
        prior_revenue = self.get_value(self.pd_income, prior_idx, '营业收入', 'Operating Revenue')
        
        current_cost = self.get_value(self.pd_income, current_idx, '营业成本', 'Operating Costs')
        prior_cost = self.get_value(self.pd_income, prior_idx, '营业成本', 'Operating Costs')
        
        if current_revenue == 0 or prior_revenue == 0:
            return np.nan
        
        prior_margin = (prior_revenue - prior_cost) / prior_revenue
        current_margin = (current_revenue - current_cost) / current_revenue
        
        if current_margin == 0:
            return 1.0
        
        return prior_margin / current_margin
    
    def calculate_aqi(self, current_idx, prior_idx):
        """Asset Quality Index (资产质量指数 / AQI)"""
        current_total_assets = self.get_value(self.pd_asset, current_idx, '资产总计', 'Total Assets')
        prior_total_assets = self.get_value(self.pd_asset, prior_idx, '资产总计', 'Total Assets')
        
        current_current_assets = self.get_value(self.pd_asset, current_idx, '流动资产合计', 'Total Current Assets')
        prior_current_assets = self.get_value(self.pd_asset, prior_idx, '流动资产合计', 'Total Current Assets')
        
        current_fixed_assets = self.get_value(self.pd_asset, current_idx, '固定资产净额', 'Net Fixed Assets')
        prior_fixed_assets = self.get_value(self.pd_asset, prior_idx, '固定资产净额', 'Net Fixed Assets')
        
        if current_total_assets == 0 or prior_total_assets == 0:
            return np.nan
        
        current_ratio = (current_total_assets - current_current_assets - current_fixed_assets) / current_total_assets
        prior_ratio = (prior_total_assets - prior_current_assets - prior_fixed_assets) / prior_total_assets
        
        if prior_ratio == 0:
            return 1.0
        
        return current_ratio / prior_ratio
    
    def calculate_sgi(self, current_idx, prior_idx):
        """Sales Growth Index (销售增长指数 / SGI)"""
        current_revenue = self.get_value(self.pd_income, current_idx, '营业收入', 'Operating Revenue')
        prior_revenue = self.get_value(self.pd_income, prior_idx, '营业收入', 'Operating Revenue')
        
        if prior_revenue == 0:
            return np.nan
        
        return current_revenue / prior_revenue
    
    def calculate_depi(self, current_idx, prior_idx):
        """Depreciation Index (折旧指数 / DEPI)"""
        current_depreciation = abs(self.get_value(self.pd_asset, current_idx, '累计折旧', 'Accumulated Depreciation'))
        prior_depreciation = abs(self.get_value(self.pd_asset, prior_idx, '累计折旧', 'Accumulated Depreciation'))
        
        current_gross_ppe = current_depreciation + self.get_value(self.pd_asset, current_idx, '固定资产净额', 'Net Fixed Assets')
        prior_gross_ppe = prior_depreciation + self.get_value(self.pd_asset, prior_idx, '固定资产净额', 'Net Fixed Assets')
        
        current_cost = self.get_value(self.pd_asset, current_idx, '固定资产原值', 'Cost of Fixed Assets')
        prior_cost = self.get_value(self.pd_asset, prior_idx, '固定资产原值', 'Cost of Fixed Assets')
        
        if current_cost > 0:
            current_gross_ppe = current_cost
        if prior_cost > 0:
            prior_gross_ppe = prior_cost
        
        if current_gross_ppe == 0 or prior_gross_ppe == 0:
            return 1.0
        
        prior_rate = prior_depreciation / prior_gross_ppe
        current_rate = current_depreciation / current_gross_ppe
        
        if current_rate == 0:
            return 1.0
        
        return prior_rate / current_rate
    
    def calculate_sgai(self, current_idx, prior_idx):
        """Sales, General and Administrative Expenses Index (销售及管理费用指数 / SGAI)"""
        current_selling = self.get_value(self.pd_income, current_idx, '销售费用', 'Selling Expenses')
        prior_selling = self.get_value(self.pd_income, prior_idx, '销售费用', 'Selling Expenses')
        
        current_admin = self.get_value(self.pd_income, current_idx, '管理费用', 'Administrative Expenses')
        prior_admin = self.get_value(self.pd_income, prior_idx, '管理费用', 'Administrative Expenses')
        
        current_revenue = self.get_value(self.pd_income, current_idx, '营业收入', 'Operating Revenue')
        prior_revenue = self.get_value(self.pd_income, prior_idx, '营业收入', 'Operating Revenue')
        
        if prior_revenue == 0 or current_revenue == 0:
            return np.nan
        
        current_ratio = (current_selling + current_admin) / current_revenue
        prior_ratio = (prior_selling + prior_admin) / prior_revenue
        
        if prior_ratio == 0:
            return 1.0
        
        return current_ratio / prior_ratio
    
    def calculate_lvgi(self, current_idx, prior_idx):
        """Leverage Index (杠杆指数 / LVGI)"""
        current_current_liab = self.get_value(self.pd_asset, current_idx, '流动负债合计', 'Total Current Liabilities')
        prior_current_liab = self.get_value(self.pd_asset, prior_idx, '流动负债合计', 'Total Current Liabilities')
        
        current_noncurrent_liab = self.get_value(self.pd_asset, current_idx, '非流动负债合计', 'Total Non-current Liabilities')
        prior_noncurrent_liab = self.get_value(self.pd_asset, prior_idx, '非流动负债合计', 'Total Non-current Liabilities')
        
        current_total_assets = self.get_value(self.pd_asset, current_idx, '资产总计', 'Total Assets')
        prior_total_assets = self.get_value(self.pd_asset, prior_idx, '资产总计', 'Total Assets')
        
        if prior_total_assets == 0 or current_total_assets == 0:
            return np.nan
        
        current_ratio = (current_current_liab + current_noncurrent_liab) / current_total_assets
        prior_ratio = (prior_current_liab + prior_noncurrent_liab) / prior_total_assets
        
        if prior_ratio == 0:
            return 1.0
        
        return current_ratio / prior_ratio
    
    def calculate_tata(self, current_idx):
        """Total Accruals to Total Assets (总应计项目与总资产比 / TATA)"""
        operating_cashflow = self.get_value(self.pd_cashflow, current_idx, '经营活动产生的现金流量净额', 'Net Cash Flow from Operating Activities')
        
        if current_idx == 0:
            return 0.0
        
        current_working_capital = (
            self.get_value(self.pd_asset, current_idx, '流动资产合计', 'Total Current Assets') - 
            self.get_value(self.pd_asset, current_idx, '流动负债合计', 'Total Current Liabilities')
        )
        prior_working_capital = (
            self.get_value(self.pd_asset, current_idx-1, '流动资产合计', 'Total Current Assets') - 
            self.get_value(self.pd_asset, current_idx-1, '流动负债合计', 'Total Current Liabilities')
        )
        
        working_capital_change = current_working_capital - prior_working_capital
        total_assets = self.get_value(self.pd_asset, current_idx, '资产总计', 'Total Assets')
        
        if total_assets == 0:
            return 0.0
        
        return (working_capital_change - operating_cashflow) / total_assets
    
    def calculate_mscore(self, period_idx):
        """计算M-Score / Calculate M-Score"""
        if period_idx == 0:
            return None
        
        dsri = self.calculate_dsri(period_idx, period_idx-1)
        gmi = self.calculate_gmi(period_idx, period_idx-1)
        aqi = self.calculate_aqi(period_idx, period_idx-1)
        sgi = self.calculate_sgi(period_idx, period_idx-1)
        depi = self.calculate_depi(period_idx, period_idx-1)
        sgai = self.calculate_sgai(period_idx, period_idx-1)
        lvgi = self.calculate_lvgi(period_idx, period_idx-1)
        tata = self.calculate_tata(period_idx)
        
        # 使用默认值处理NaN
        dsri_val = dsri if not pd.isna(dsri) else 1.0
        gmi_val = gmi if not pd.isna(gmi) else 1.0
        aqi_val = aqi if not pd.isna(aqi) else 1.0
        sgi_val = sgi if not pd.isna(sgi) else 1.0
        depi_val = depi if not pd.isna(depi) else 1.0
        sgai_val = sgai if not pd.isna(sgai) else 1.0
        lvgi_val = lvgi if not pd.isna(lvgi) else 1.0
        tata_val = tata if not pd.isna(tata) else 0.0
        
        m_score = (-4.84 + 0.920 * dsri_val + 0.528 * gmi_val + 0.404 * aqi_val + 
                   0.892 * sgi_val + 0.115 * depi_val - 0.172 * sgai_val + 
                   4.679 * tata_val - 0.327 * lvgi_val)
        
        # 判断风险等级
        if m_score > -2.22:
            risk_level = "高风险 (High Risk)"
            risk_desc = "M-Score高于阈值，可能存在财务操纵风险 (Possible financial manipulation)"
        else:
            risk_level = "低风险 (Low Risk)"
            risk_desc = "M-Score低于阈值，财务操纵风险较低 (Low manipulation risk)"
        
        # 分析异常指标
        warnings = []
        if not pd.isna(dsri) and dsri > 1.05:
            warnings.append(f"DSRI({dsri:.2f}): 应收账款增长快于收入")
        if not pd.isna(gmi) and gmi > 1.05:
            warnings.append(f"GMI({gmi:.2f}): 毛利率下降")
        if not pd.isna(aqi) and aqi > 1.05:
            warnings.append(f"AQI({aqi:.2f}): 资产质量下降")
        if not pd.isna(sgi) and sgi > 1.1:
            warnings.append(f"SGI({sgi:.2f}): 快速销售增长")
        if not pd.isna(depi) and depi > 1.05:
            warnings.append(f"DEPI({depi:.2f}): 折旧率下降")
        if not pd.isna(sgai) and sgai > 1.05:
            warnings.append(f"SGAI({sgai:.2f}): 费用率上升")
        if not pd.isna(lvgi) and lvgi > 1.05:
            warnings.append(f"LVGI({lvgi:.2f}): 杠杆率上升")
        if not pd.isna(tata) and abs(tata) > 0.05:
            warnings.append(f"TATA({tata:.2f}): 应计项目异常")
        
        return {
            'DSRI': dsri,
            'GMI': gmi,
            'AQI': aqi,
            'SGI': sgi,
            'DEPI': depi,
            'SGAI': sgai,
            'LVGI': lvgi,
            'TATA': tata,
            'M-Score': m_score,
            'Risk Level (风险等级)': risk_level,
            'Risk Description (风险描述)': risk_desc,
            'Warnings (预警)': '; '.join(warnings) if warnings else '各指标正常 (All indicators normal)'
        }
    
    def calculate_all_periods(self):
        """计算所有期间的M-Score"""
        date_col = self.date_col_income
        if not date_col:
            return pd.DataFrame()
        
        all_results = []
        report_dates = self.pd_income[date_col].tolist()
        
        for i in range(1, len(report_dates)):
            result = self.calculate_mscore(i)
            if result:
                result['报告日 (Report Date)'] = report_dates[i]
                # 重新排序，将日期放在第一列
                result = {'报告日 (Report Date)': result['报告日 (Report Date)'], **{k: v for k, v in result.items() if k != '报告日 (Report Date)'}}
                all_results.append(result)
        
        self.results = pd.DataFrame(all_results)
        return self.results
    
    def generate_report_text(self):
        """生成报告文本（不打印，只返回）"""
        if self.results is None or len(self.results) == 0:
            # 如果还没计算，先计算
            self.calculate_all_periods()
        
        if len(self.results) == 0:
            return "数据不足，无法生成报告 (Insufficient data to generate report)"
        
        report_lines = []
        
        def add_line(text):
            report_lines.append(text)
        
        add_line("=" * 100)
        add_line(f"Beneish M-Score 财务操纵风险分析报告 (Financial Manipulation Risk Analysis Report)")
        add_line(f"股票代码 (Stock Code): {self.stock}")
        add_line("=" * 100)
        add_line("\nM-Score 判断标准 (Threshold):")
        add_line("  M-Score < -2.22: 低操纵风险 (Low Manipulation Risk)")
        add_line("  M-Score > -2.22: 可能存在财务操纵 (Possible Financial Manipulation)")
        add_line("\n" + "=" * 100)
        
        # 最新期分析
        latest = self.results.iloc[-1]
        add_line(f"\n【最新报告期分析 (Latest Period Analysis)】")
        add_line(f"报告日期 (Report Date): {latest['报告日 (Report Date)']}")
        add_line(f"M-Score: {latest['M-Score']:.4f}")
        add_line(f"风险等级 (Risk Level): {latest['Risk Level (风险等级)']}")
        add_line(f"风险描述 (Risk Description): {latest['Risk Description (风险描述)']}")
        add_line("")
        
        # 修复格式化问题：先计算值，再格式化
        add_line("各项指标详情 (Detailed Indicators):")
        dsri_str = f"{latest['DSRI']:.4f}" if not pd.isna(latest['DSRI']) else 'N/A'
        gmi_str = f"{latest['GMI']:.4f}" if not pd.isna(latest['GMI']) else 'N/A'
        aqi_str = f"{latest['AQI']:.4f}" if not pd.isna(latest['AQI']) else 'N/A'
        sgi_str = f"{latest['SGI']:.4f}" if not pd.isna(latest['SGI']) else 'N/A'
        depi_str = f"{latest['DEPI']:.4f}" if not pd.isna(latest['DEPI']) else 'N/A'
        sgai_str = f"{latest['SGAI']:.4f}" if not pd.isna(latest['SGAI']) else 'N/A'
        lvgi_str = f"{latest['LVGI']:.4f}" if not pd.isna(latest['LVGI']) else 'N/A'
        tata_str = f"{latest['TATA']:.4f}" if not pd.isna(latest['TATA']) else 'N/A'
        
        add_line(f"  DSRI (应收账款天数指数)       : {dsri_str}")
        add_line(f"  GMI  (毛利率指数)             : {gmi_str}")
        add_line(f"  AQI  (资产质量指数)           : {aqi_str}")
        add_line(f"  SGI  (销售增长指数)           : {sgi_str}")
        add_line(f"  DEPI (折旧指数)               : {depi_str}")
        add_line(f"  SGAI (销管费用指数)           : {sgai_str}")
        add_line(f"  LVGI (杠杆指数)               : {lvgi_str}")
        add_line(f"  TATA (总应计项目比率)         : {tata_str}")
        add_line("")
        
        add_line("异常指标预警 (Warning Indicators):")
        add_line(f"  {latest['Warnings (预警)']}")
        add_line("-" * 100)
        add_line("")
        
        # 历史趋势
        add_line("【历史趋势分析 (Historical Trend Analysis)】")
        add_line(f"分析期间 (Analysis Period): {self.results.iloc[0]['报告日 (Report Date)']} 至 (to) {self.results.iloc[-1]['报告日 (Report Date)']}")
        add_line(f"报告期数 (Number of Periods): {len(self.results)}")
        add_line("")
        
        # M-Score统计
        add_line("M-Score 统计 (M-Score Statistics):")
        add_line(f"  平均值 (Mean)     : {self.results['M-Score'].mean():.4f}")
        add_line(f"  最大值 (Maximum)  : {self.results['M-Score'].max():.4f}")
        add_line(f"  最小值 (Minimum)  : {self.results['M-Score'].min():.4f}")
        add_line(f"  标准差 (Std Dev)  : {self.results['M-Score'].std():.4f}")
        add_line("")
        
        # 风险等级分布
        risk_dist = self.results['Risk Level (风险等级)'].value_counts()
        add_line("风险等级分布 (Risk Level Distribution):")
        for level, count in risk_dist.items():
            pct = count / len(self.results) * 100
            add_line(f"  {level}: {count} 期 (periods) ({pct:.1f}%)")
        add_line("")
        
        # 详细历史数据
        add_line("【详细历史数据 (Detailed Historical Data)】")
        display_cols = ['报告日 (Report Date)', 'M-Score', 'Risk Level (风险等级)', 
                       'DSRI', 'GMI', 'AQI', 'SGI', 'DEPI', 'SGAI', 'LVGI', 'TATA']
        add_line(self.results[display_cols].to_string(index=False))
        add_line("")
        add_line("")
        
        # 投资建议
        add_line("=" * 100)
        add_line("【投资建议 (Investment Recommendation)】")
        latest_score = latest['M-Score']
        high_risk_count = len(self.results[self.results['M-Score'] > -2.22])
        high_risk_pct = high_risk_count / len(self.results) * 100
        
        if latest_score > -2.22:
            add_line("  当前M-Score高于阈值，存在财务操纵风险，建议谨慎投资。")
            add_line("(Current M-Score above threshold, manipulation risk exists, caution advised.)")
        else:
            add_line("✓  当前M-Score低于阈值，财务操纵风险较低。")
            add_line("(Current M-Score below threshold, low manipulation risk.)")
        
        add_line(f"\n历史数据显示：{high_risk_pct:.1f}%的报告期M-Score高于阈值。")
        add_line(f"(Historical data shows {high_risk_pct:.1f}% of periods had M-Score above threshold.)")
        
        if high_risk_pct > 50:
            add_line("\n该公司多数报告期存在财务操纵风险信号，建议深入调查或回避投资。")
            add_line("(Majority of periods show manipulation risk signals, thorough investigation or avoidance advised.)")
        elif high_risk_pct > 25:
            add_line("\n该公司部分报告期存在财务操纵风险信号，需要密切关注财务质量。")
            add_line("(Some periods show manipulation risk signals, close attention to financial quality needed.)")
        else:
            add_line("\n该公司大多数报告期财务质量良好，但仍需结合其他指标综合判断。")
            add_line("(Most periods show good financial quality, but comprehensive analysis with other metrics still needed.)")
        
        add_line("")
        add_line("注意 (Note):")
        add_line("M-Score仅为预警工具，不能单独作为投资决策依据。")
        add_line("建议结合现金流分析、审计报告、行业对比等方法进行综合评估。")
        add_line("(M-Score is only a warning tool and should not be used alone for investment decisions.)")
        add_line("(Comprehensive evaluation combining cash flow analysis, audit reports, and industry comparison is recommended.)")
        add_line("=" * 100)
        
        return "\n".join(report_lines)
    
    def print_report(self):
        """打印报告到控制台"""
        report_text = self.generate_report_text()
        print(report_text)
    
    def generate_report(self):
        """保持向后兼容的方法名"""
        self.print_report()


def analyze_beneish_mscore(stock_code, print_output=True):
    """
    分析指定股票的Beneish M-Score并返回结果数据和报告文本
    Analyze Beneish M-Score for specified stock and return results data and report text
    
    参数 (Parameters):
        stock_code (str): 股票代码 (Stock code)
        print_output (bool): 是否打印输出到控制台 (Whether to print output to console)
    
    返回 (Returns):
        results_df (DataFrame): 包含所有计算结果的数据框 (DataFrame containing all calculation results)
        report_text (str): 完整的分析报告文本 (Complete analysis report text)
    
    使用示例 (Usage Example):
        # 获取数据和报告，打印到控制台
        data, report = analyze_beneish_mscore("600519")
        
        # 只获取数据，不打印
        data, report = analyze_beneish_mscore("600519", print_output=False)
        
        # 访问数据
        latest_mscore = data.iloc[-1]['M-Score']
        
        # 保存报告到文件
        with open('mscore_report.txt', 'w', encoding='utf-8') as f:
            f.write(report)
    """
    
    # 根据print_output参数决定是否创建静默模式的分析器
    analyzer = BeneishMScore(stock_code, silent=not print_output)
    
    if print_output:
        print("\n" + "="*100)
        print("Beneish M-Score 财务操纵风险分析系统 (Financial Manipulation Risk Analysis System)")
        print("="*100 + "\n")
        print("开始计算 M-Score... (Starting M-Score calculation...)\n")
    
    # 计算所有期间的M-Score
    results_df = analyzer.calculate_all_periods()
    
    if len(results_df) == 0:
        if print_output:
            print("数据不足，无法计算M-Score (Insufficient data to calculate M-Score)")
        return None, "数据不足 (Insufficient data)"
    
    # 生成报告文本
    if print_output:
        print("\n" + "="*100)
        print("开始生成报告... (Starting report generation...)")
        print("="*100 + "\n")
    
    report_text = analyzer.generate_report_text()
    
    # 根据参数决定是否打印
    if print_output:
        print(report_text)
        print("\n" + "="*100)
        print("分析完成！(Analysis completed!)")
        print("="*100 + "\n")
    
    return results_df, report_text


def beneish_mscore_check(stock):
    """
    检查股票的Beneish M-Score（保持向后兼容）
    Check stock's Beneish M-Score (backward compatibility)
    
    参数 (Parameters):
        stock: 股票代码 (Stock code)
    
    Demo:
        beneish_mscore_check("600519")
    """
    analyzer = BeneishMScore(stock, silent=False)
    analyzer.generate_report()


# 使用示例 (Usage Example)
if __name__ == "__main__":
    # 方式1: 使用便捷函数，打印输出
    print("\n【示例1: 打印输出模式 (Example 1: Print Output Mode)】")
    results_data, report_content = analyze_beneish_mscore("600519")
    
    if results_data is not None:
        print(f"\n返回的数据 (Returned Data):")
        print(f"  - DataFrame 行数 (Rows): {len(results_data)}")
        print(f"  - DataFrame 列数 (Columns): {len(results_data.columns)}")
        print(f"  - 报告文本长度 (Report Text Length): {len(report_content)} 字符 (characters)")
        print(f"\n最新M-Score (Latest M-Score): {results_data.iloc[-1]['M-Score']:.4f}")
        print(f"最新风险等级 (Latest Risk Level): {results_data.iloc[-1]['Risk Level (风险等级)']}")
    
    # 方式2: 静默模式，不打印输出
    print("\n" + "="*100)
    print("\n【示例2: 静默模式 (Example 2: Silent Mode)】")
    data, report = analyze_beneish_mscore("600519", print_output=False)
    print("静默模式完成，数据已获取但未打印详细报告 (Silent mode completed, data retrieved without printing detailed report)")
    
    # 方式3: 保存报告到文件
    print("\n【示例3: 保存报告到文件 (Example 3: Save Report to File)】")
    with open('beneish_mscore_report.txt', 'w', encoding='utf-8') as f:
        f.write(report)
    print("报告已保存到 beneish_mscore_report.txt (Report saved to beneish_mscore_report.txt)")
