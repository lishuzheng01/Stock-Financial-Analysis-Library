import pandas as pd
import numpy as np
from stock_tool.get_report_data import get_report_data
from datetime import datetime
from io import StringIO
import sys

class AltmanZScore:
    """
    Altman Z-Score 破产风险预测模型 (Bankruptcy Risk Prediction Model)
    
    Z-Score = 1.2*X1 + 1.4*X2 + 3.3*X3 + 0.6*X4 + 1.0*X5
    
    其中 (Where):
    X1 = 营运资本 / 总资产 (Working Capital / Total Assets)
    X2 = 留存收益 / 总资产 (Retained Earnings / Total Assets)
    X3 = 息税前利润 / 总资产 (EBIT / Total Assets)
    X4 = 股东权益市值 / 总负债 (Market Value of Equity / Total Liabilities)
    X5 = 销售收入 / 总资产 (Sales / Total Assets)
    
    评分标准 (Scoring Criteria):
    Z > 2.99: 安全区域 (Safe Zone)
    1.81 < Z < 2.99: 灰色区域 (Grey Zone)
    Z < 1.81: 危险区域 (Distress Zone)
    """
    
    def __init__(self, stock_code):
        self.stock_code = stock_code
        self.pd_asset = None
        self.pd_income = None
        self.pd_cashflow = None
        self.results = None
        
    def load_data(self):
        """加载财务数据 (Load Financial Data)"""
        print(f"正在加载股票 {self.stock_code} 的财务数据... (Loading financial data for stock {self.stock_code}...)")
        
        # 加载资产负债表（转置后使用）
        self.pd_asset = get_report_data(
            stock=self.stock_code, 
            symbol="资产负债表", 
            transpose=True
        )
        
        # 加载利润表（转置后使用）
        self.pd_income = get_report_data(
            stock=self.stock_code, 
            symbol="利润表", 
            transpose=True
        )
        
        # 加载现金流量表（转置后使用）
        self.pd_cashflow = get_report_data(
            stock=self.stock_code, 
            symbol="现金流量表", 
            transpose=True
        )
        
        print("数据加载完成！(Data loaded successfully!)")
        print(f"资产负债表行数 (Balance Sheet Rows): {len(self.pd_asset)}")
        print(f"利润表行数 (Income Statement Rows): {len(self.pd_income)}")
        
    def _safe_get_value(self, df, idx, col_name, default=0):
        """安全获取数值，处理缺失值 (Safely get value, handle missing data)"""
        try:
            if col_name not in df.columns:
                return default
            
            value = df.loc[idx, col_name]
            
            if pd.isna(value) or value == '' or value is None:
                return default
                
            return float(value)
        except Exception as e:
            return default
        
    def calculate_zscore(self):
        """计算 Altman Z-Score (Calculate Altman Z-Score)"""
        if self.pd_asset is None or self.pd_income is None:
            raise ValueError("请先加载数据 (Please load data first)")
        
        results = []
        successful_count = 0
        failed_count = 0
        
        # 遍历每个报告期
        for idx in self.pd_asset.index:
            try:
                # 使用英文列名获取数据
                report_date = self._safe_get_value(self.pd_asset, idx, '报告日', '')
                if not report_date:
                    failed_count += 1
                    continue
                
                # 提取资产负债表数据 - 使用英文列名
                total_assets = self._safe_get_value(self.pd_asset, idx, 'Total Assets')
                if total_assets == 0:
                    failed_count += 1
                    continue
                    
                current_assets = self._safe_get_value(self.pd_asset, idx, 'Total Current Assets')
                current_liabilities = self._safe_get_value(self.pd_asset, idx, 'Total Current Liabilities')
                total_liabilities = self._safe_get_value(self.pd_asset, idx, 'Total Liabilities')
                retained_earnings = self._safe_get_value(self.pd_asset, idx, 'Retained Earnings')
                shareholders_equity = self._safe_get_value(self.pd_asset, idx, "Total Owner's Equity (or Shareholders' Equity)")
                
                # 提取利润表数据 - 使用英文列名
                operating_revenue = self._safe_get_value(self.pd_income, idx, 'Operating Revenue')
                operating_profit = self._safe_get_value(self.pd_income, idx, 'Operating Profit')
                interest_expense = self._safe_get_value(self.pd_income, idx, 'Interest Expenses')
                
                # 计算各项指标
                # X1: 营运资本 / 总资产
                working_capital = current_assets - current_liabilities
                x1 = working_capital / total_assets if total_assets != 0 else 0
                
                # X2: 留存收益 / 总资产
                x2 = retained_earnings / total_assets if total_assets != 0 else 0
                
                # X3: 息税前利润(EBIT) / 总资产
                ebit = operating_profit + interest_expense
                x3 = ebit / total_assets if total_assets != 0 else 0
                
                # X4: 股东权益账面价值 / 总负债
                x4 = shareholders_equity / total_liabilities if total_liabilities != 0 else 0
                
                # X5: 销售收入 / 总资产
                x5 = operating_revenue / total_assets if total_assets != 0 else 0
                
                # 计算 Z-Score
                z_score = 1.2 * x1 + 1.4 * x2 + 3.3 * x3 + 0.6 * x4 + 1.0 * x5
                
                # 判断风险等级
                if z_score > 2.99:
                    risk_level = "安全区域 (Safe Zone)"
                    risk_desc = "财务状况良好，破产风险低 (Good financial health, low bankruptcy risk)"
                elif z_score > 1.81:
                    risk_level = "灰色区域 (Grey Zone)"
                    risk_desc = "财务状况一般，需要关注 (Fair financial health, attention needed)"
                else:
                    risk_level = "危险区域 (Distress Zone)"
                    risk_desc = "财务状况堪忧，破产风险高 (Poor financial health, high bankruptcy risk)"
                
                results.append({
                    '报告日 (Report Date)': report_date,
                    'Z-Score': round(z_score, 4),
                    'X1_营运资本比率 (Working Capital Ratio)': round(x1, 4),
                    'X2_留存收益比率 (Retained Earnings Ratio)': round(x2, 4),
                    'X3_EBIT比率 (EBIT Ratio)': round(x3, 4),
                    'X4_权益负债比 (Equity to Debt Ratio)': round(x4, 4),
                    'X5_资产周转率 (Asset Turnover Ratio)': round(x5, 4),
                    '风险等级 (Risk Level)': risk_level,
                    '风险描述 (Risk Description)': risk_desc,
                    '总资产 (Total Assets)': total_assets,
                    '营运资本 (Working Capital)': working_capital,
                    '留存收益 (Retained Earnings)': retained_earnings,
                    'EBIT (息税前利润)': ebit,
                    '股东权益 (Shareholders Equity)': shareholders_equity,
                    '总负债 (Total Liabilities)': total_liabilities,
                    '营业收入 (Operating Revenue)': operating_revenue
                })
                
                successful_count += 1
                
            except Exception as e:
                failed_count += 1
                continue
        
        self.results = pd.DataFrame(results)
        
        print(f"\n计算完成！成功 (Success): {successful_count} 期，失败 (Failed): {failed_count} 期")
        
        if len(self.results) == 0:
            raise ValueError("没有成功计算任何报告期的数据，请检查数据源 (No data calculated successfully)")
        
        return self.results
    
    def generate_report_text(self):
        """生成报告文本内容（不打印，只返回字符串）
        Generate report text content (return string without printing)
        """
        if self.results is None or len(self.results) == 0:
            raise ValueError("请先计算 Z-Score (Please calculate Z-Score first)")
        
        report_lines = []
        
        def add_line(text):
            report_lines.append(text)
        
        add_line("=" * 100)
        add_line(f"Altman Z-Score 财务风险分析报告 (Financial Risk Analysis Report)")
        add_line(f"股票代码 (Stock Code): {self.stock_code}")
        add_line(f"报告生成时间 (Report Generated): {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        add_line("=" * 100)
        add_line("")
        
        # 模型说明
        add_line("【模型说明 (Model Description)】")
        add_line("Altman Z-Score 是用于预测企业破产风险的综合财务指标")
        add_line("(Altman Z-Score is a comprehensive financial metric for predicting corporate bankruptcy risk)")
        add_line("")
        add_line("计算公式 (Formula): Z = 1.2*X.0*X5")
        add_line("")
        add_line("各指标含义 (Indicator Definitions):")
        add_line("  X1 = 营运资本 / 总资产 (Working Capital / Total Assets)")
        add_line("       反映短期偿债能力 (Reflects short-term solvency)")
        add_line("  X2 = 留存收益 / 总资产 (Retained Earnings / Total Assets)")
        add_line("       反映盈利积累能力 (Reflects profit accumulation capability)")
        add_line("  X3 = 息税前利润 / 总资产 (EBIT / Total Assets)")
        add_line("       反映资产盈利能力 (Reflects asset profitability)")
        add_line("  X4 = 股东权益 / 总负债 (Shareholders' Equity / Total Liabilities)")
        add_line("       反映财务杠杆 (Reflects financial leverage)")
        add_line("  X5 = 销售收入 / 总资产 (Sales / Total Assets)")
        add_line("       反映资产使用效率 (Reflects asset utilization efficiency)")
        add_line("")
        add_line("评分标准 (Scoring Criteria):")
        add_line("  Z > 2.99        : 安全区域 (Safe Zone) - 财务健康，破产风险低")
        add_line("                    (Good financial health, low bankruptcy risk)")
        add_line("  1.81 < Z < 2.99 : 灰色区域 (Grey Zone) - 财务状况一般，需要关注")
        add_line("                    (Fair financial condition, attention needed)")
        add_line("  Z < 1.81        : 危险区域 (Distress Zone) - 财务状况差，破产风险高")
        add_line("                    (Poor financial condition, high bankruptcy risk)")
        add_line("-" * 100)
        add_line("")
        
        # 最新报告期分析
        latest = self.results.iloc[0]
        add_line("【最新报告期分析 (Latest Period Analysis)】")
        add_line(f"报告日期 (Report Date): {latest['报告日 (Report Date)']}")
        add_line(f"Z-Score: {latest['Z-Score']:.4f}")
        add_line(f"风险等级 (Risk Level): {latest['风险等级 (Risk Level)']}")
        add_line(f"风险描述 (Risk Description): {latest['风险描述 (Risk Description)']}")
        add_line("")
        
        add_line("各项指标详情 (Detailed Indicators):")
        add_line(f"  X1 (营运资本比率 Working Capital Ratio)       : {latest['X1_营运资本比率 (Working Capital Ratio)']:.4f}")
        add_line(f"  X2 (留存收益比率 Retained Earnings Ratio)     : {latest['X2_留存收益比率 (Retained Earnings Ratio)']:.4f}")
        add_line(f"  X3 (EBIT比率 EBIT Ratio)                      : {latest['X3_EBIT比率 (EBIT Ratio)']:.4f}")
        add_line(f"  X4 (权益负债比 Equity to Debt Ratio)          : {latest['X4_权益负债比 (Equity to Debt Ratio)']:.4f}")
        add_line(f"  X5 (资产周转率 Asset Turnover Ratio)          : {latest['X5_资产周转率 (Asset Turnover Ratio)']:.4f}")
        add_line("")
        
        add_line("财务数据 (Financial Data) [单位:元 Unit: CNY]:")
        add_line(f"  总资产 (Total Assets)                         : {latest['总资产 (Total Assets)']:,.0f}")
        add_line(f"  营运资本 (Working Capital)                    : {latest['营运资本 (Working Capital)']:,.0f}")
        add_line(f"  留存收益 (Retained Earnings)                  : {latest['留存收益 (Retained Earnings)']:,.0f}")
        add_line(f"  息税前利润 (EBIT)                             : {latest['EBIT (息税前利润)']:,.0f}")
        add_line(f"  股东权益 (Shareholders Equity)                : {latest['股东权益 (Shareholders Equity)']:,.0f}")
        add_line(f"  总负债 (Total Liabilities)                    : {latest['总负债 (Total Liabilities)']:,.0f}")
        add_line(f"  营业收入 (Operating Revenue)                  : {latest['营业收入 (Operating Revenue)']:,.0f}")
        add_line("-" * 100)
        add_line("")
        
        # 历史趋势分析
        add_line("【历史趋势分析 (Historical Trend Analysis)】")
        add_line(f"分析期间 (Analysis Period): {self.results.iloc[-1]['报告日 (Report Date)']} 至 (to) {self.results.iloc[0]['报告日 (Report Date)']}")
        add_line(f"报告期数 (Number of Periods): {len(self.results)}")
        add_line("")
        
        # 统计信息
        add_line("Z-Score 统计 (Z-Score Statistics):")
        add_line(f"  平均值 (Mean)     : {self.results['Z-Score'].mean():.4f}")
        max_idx = self.results['Z-Score'].idxmax()
        min_idx = self.results['Z-Score'].idxmin()
        add_line(f"  最大值 (Maximum)  : {self.results['Z-Score'].max():.4f} ({self.results.loc[max_idx, '报告日 (Report Date)']})")
        add_line(f"  最小值 (Minimum)  : {self.results['Z-Score'].min():.4f} ({self.results.loc[min_idx, '报告日 (Report Date)']})")
        add_line(f"  标准差 (Std Dev)  : {self.results['Z-Score'].std():.4f}")
        add_line("")
        
        # 风险等级分布
        risk_dist = self.results['风险等级 (Risk Level)'].value_counts()
        add_line("风险等级分布 (Risk Level Distribution):")
        for level, count in risk_dist.items():
            pct = count / len(self.results) * 100
            add_line(f"  {level}: {count} 期 (periods) ({pct:.1f}%)")
        add_line("")
        
        # 趋势判断
        if len(self.results) >= 2:
            recent_trend = self.results['Z-Score'].iloc[0] - self.results['Z-Score'].iloc[1]
            add_line("最近趋势 (Recent Trend):")
            if recent_trend > 0:
                add_line(f"  Z-Score 上升 (Increased) {abs(recent_trend):.4f} - 财务状况改善 (Financial condition improved)")
            elif recent_trend < 0:
                add_line(f"  Z-Score 下降 (Decreased) {abs(recent_trend):.4f} - 财务状况恶化 (Financial condition deteriorated)")
            else:
                add_line("  Z-Score 持平 (Stable) - 财务状况稳定 (Financial condition stable)")
        add_line("-" * 100)
        add_line("")
        
        # 详细历史数据
        add_line("【详细历史数据 (Detailed Historical Data)】")
        # 显示主要列
        display_cols = ['报告日 (Report Date)', 'Z-Score', '风险等级 (Risk Level)', 
                       'X1_营运资本比率 (Working Capital Ratio)', 
                       'X2_留存收益比率 (Retained Earnings Ratio)', 
                       'X3_EBIT比率 (EBIT Ratio)', 
                       'X4_权益负债比 (Equity to Debt Ratio)', 
                       'X5_资产周转率 (Asset Turnover Ratio)']
        add_line(self.results[display_cols].to_string(index=False))
        add_line("")
        add_line("")
        
        # 投资建议
        add_line("=" * 100)
        add_line("【投资建议 (Investment Recommendation)】")
        latest_score = latest['Z-Score']
        if latest_score > 2.99:
            add_line("该公司财务状况健康，破产风险较低，从财务风险角度看具有投资价值。")
            add_line("(The company has healthy finances with low bankruptcy risk and investment value from a financial risk perspective.)")
            add_line("但仍需结合行业前景、估值水平等因素综合判断。")
            add_line("(However, comprehensive judgment combining industry prospects and valuation levels is still needed.)")
        elif latest_score > 1.81:
            add_line("该公司财务状况一般，处于灰色地带，建议谨慎投资。")
            add_line("(The company's financial condition is fair, in the grey zone, cautious investment recommended.)")
            add_line("需要密切关注公司财务指标变化趋势，特别是现金流和盈利能力。")
            add_line("(Close attention to financial indicator trends is needed, especially cash flow and profitability.)")
        else:
            add_line("该公司财务状况较差，存在较高的破产风险，建议规避投资。")
            add_line("(The company has poor financial condition with high bankruptcy risk, investment avoidance recommended.)")
            add_line("如已持有该股票，建议考虑止损退出。")
            add_line("(If already holding this stock, consider stop-loss exit.)")
        add_line("")
        add_line("免责声明 (Disclaimer):")
        add_line("本报告仅供参考，不构成投资建议。投资者应独立判断并承担投资风险。")
        add_line("(This report is for reference only and does not constitute investment advice. Investors should make independent judgments and bear investment risks.)")
        add_line("=" * 100)
        
        return "\n".join(report_lines)
    
    def print_report(self):
        """打印分析报告到控制台 (Print Analysis Report to Console)"""
        report_text = self.generate_report_text()
        print(report_text)
        

def analyze_altman_zscore(stock_code, print_output=True):
    """
    分析指定股票的Altman Z-Score并返回结果数据和报告文本
    Analyze Altman Z-Score for specified stock and return results data and report text
    
    参数 (Parameters):
        stock_code (str): 股票代码 (Stock code)
        print_output (bool): 是否打印输出到控制台 (Whether to print output to console)
    
    返回 (Returns):
        results_df (DataFrame): 包含所有计算结果的数据框 (DataFrame containing all calculation results)
        report_text (str): 完整的分析报告文本 (Complete analysis report text)
    
    使用示例 (Usage Example):
        # 获取数据和报告
        data, report = analyze_altman_zscore("600519")
        
        # 只获取数据，不打印
        data, report = analyze_altman_zscore("600519", print_output=False)
    """
    
    print("\n" + "="*100)
    print("Altman Z-Score 财务风险分析系统 (Financial Risk Analysis System)")
    print("="*100 + "\n")
    
    # 创建分析对象
    analyzer = AltmanZScore(stock_code)
    
    # 加载数据
    analyzer.load_data()
    
    # 计算 Z-Score
    print("\n开始计算 Z-Score... (Starting Z-Score calculation...)\n")
    results_df = analyzer.calculate_zscore()
    
    # 生成报告文本
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


# 使用示例 (Usage Example)
if __name__ == "__main__":
    # 方式1: 使用便捷函数，打印输出
    results_data, report_content = analyze_altman_zscore("600519")
    
    # 打印返回的数据信息
    print(f"\n返回的数据 (Returned Data):")
    print(f"  - DataFrame 行数 (Rows): {len(results_data)}")
    print(f"  - DataFrame 列数 (Columns): {len(results_data.columns)}")
    print(f"  - 报告文本长度 (Report Text Length): {len(report_content)} 字符 (characters)")
    
    # 可以访问具体数据
    print(f"\n最新Z-Score (Latest Z-Score): {results_data.iloc[0]['Z-Score']}")
    print(f"最新风险等级 (Latest Risk Level): {results_data.iloc[0]['风险等级 (Risk Level)']}")
    
    # 方式2: 不打印输出，只获取数据
    # results_data, report_content = analyze_altman_zscore("600519", print_output=False)
