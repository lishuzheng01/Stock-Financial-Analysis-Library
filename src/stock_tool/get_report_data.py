# -*- coding: utf-8 -*-
"""
财务报表数据获取模块 - Financial Report Data Module
支持多数据源架构: akshare (primary) + extensible for future sources
Supports multiple data sources: akshare (primary) + extensible for future sources
"""

import akshare as ak
import pandas as pd
import logging
import requests
import urllib3

# 配置日志系统
# Configure logging system
logger = logging.getLogger('stock_tool.get_report_data')
if not logger.handlers:  # 避免重复添加handler
    handler = logging.StreamHandler()
    handler.setFormatter(logging.Formatter('[%(levelname)s] %(message)s'))
    logger.addHandler(handler)
    logger.setLevel(logging.INFO)

# 禁用SSL警告
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)


# ========================================
# 列名映射字典 - Column Translation Maps
# ========================================

# 利润表列名中英文映射字典
# Income Statement Column Translation Map
translation_map_income = {
    # --- 基础信息 ---
    "报告日": "Report Date",
    "公告日期": "Announcement Date",
    "更新日期": "Update Date",
    "数据源": "Data Source",
    "是否审计": "Audit Status",
    "币种": "Currency",
    "类型": "Report Type",

    # --- 收入类 ---
    "营业总收入": "Total Operating Revenue",
    "营业收入": "Operating Revenue",
    "利息收入": "Interest Income",
    "已赚保费": "Earned Premiums",
    "手续费及佣金收入": "Fee and Commission Income",
    "房地产销售收入": "Real Estate Sales Revenue",
    "其他业务收入": "Other Business Revenue",
    "营业外收入": "Non-operating Income",
    "投资收益": "Investment Income",
    "对联营企业和合营企业的投资收益": "Income from Associates and JVs",
    "以摊余成本计量的金融资产终止确认产生的收益": "Gain on Derecognition of Amortized Cost Fin. Assets",
    "汇兑收益": "Exchange Gains",
    "净敞口套期收益": "Net Exposure Hedging Gains",
    "公允价值变动收益": "Fair Value Change Income",
    "期货损益": "Futures Profit/Loss",
    "托管收益": "Custodian Income",
    "补贴收入": "Subsidy Income",
    "其他收益": "Other Income",
    "资产处置收益": "Asset Disposal Income",
    "非流动资产处置利得": "Gain on Disposal of Non-current Assets",

    # --- 成本与费用类 ---
    "营业总成本": "Total Operating Costs",
    "营业成本": "Operating Costs",
    "手续费及佣金支出": "Fee and Commission Expenses",
    "房地产销售成本": "Real Estate Sales Costs",
    "退保金": "Surrender Value",
    "赔付支出净额": "Net Claim Expenses",
    "提取保险合同准备金净额": "Net Provision for Insurance Contracts",
    "保单红利支出": "Policyholder Dividend Expenses",
    "分保费用": "Reinsurance Expenses",
    "其他业务成本": "Other Business Costs",
    "营业税金及附加": "Taxes and Surcharges",
    "研发费用": "R&D Expenses",
    "销售费用": "Selling Expenses",
    "管理费用": "Administrative Expenses",
    "财务费用": "Financial Expenses",
    "利息费用": "Interest Expenses",
    "利息支出": "Interest Payables",
    "营业外支出": "Non-operating Expenses",
    "非流动资产处置损失": "Loss on Disposal of Non-current Assets",
    "所得税费用": "Income Tax Expenses",

    # --- 损失类 ---
    "资产减值损失": "Asset Impairment Loss",
    "信用减值损失": "Credit Impairment Loss",
    "未确认投资损失": "Unrecognized Investment Loss",

    # --- 利润汇总类 ---
    "其他业务利润": "Other Business Profit",
    "营业利润": "Operating Profit",
    "利润总额": "Total Profit",
    "净利润": "Net Profit",
    "持续经营净利润": "Net Profit from Continuing Operations",
    "终止经营净利润": "Net Profit from Discontinued Operations",
    "归属于母公司所有者的净利润": "Net Profit Attributable to Parent",
    "被合并方在合并前实现净利润": "Net Profit of Merged Party Before Merger",
    "少数股东损益": "Minority Interest Income",
    "基本每股收益": "Basic EPS",
    "稀释每股收益": "Diluted EPS",

    # --- 其他综合收益 (OCI) 详细科目 ---
    "其他综合收益": "Other Comprehensive Income (OCI)",
    "归属于母公司所有者的其他综合收益": "OCI Attributable to Parent",
    "归属于少数股东的其他综合收益": "OCI Attributable to Minority Shareholders",
    "综合收益总额": "Total Comprehensive Income",
    "归属于母公司所有者的综合收益总额": "Total Comp. Income Attrib. to Parent",
    "归属于少数股东的综合收益总额": "Total Comp. Income Attrib. to Minority",

    # (一) 不能重分类进损益的项目
    "（一）以后不能重分类进损益的其他综合收益": "(I) Items not to be reclassified to P&L",
    "重新计量设定受益计划变动额": "Remeasurement of Defined Benefit Plans",
    "权益法下不能转损益的其他综合收益": "Share of OCI of Associates (Non-recyclable)",
    "其他权益工具投资公允价值变动": "Fair Value Changes of Other Equity Instruments",
    "企业自身信用风险公允价值变动": "Fair Value Changes due to Own Credit Risk",

    # (二) 将重分类进损益的项目
    "（二）以后将重分类进损益的其他综合收益": "(II) Items to be reclassified to P&L",
    "权益法下可转损益的其他综合收益": "Share of OCI of Associates (Recyclable)",
    "可供出售金融资产公允价值变动损益": "Fair Value Changes of Available-for-Sale Fin. Assets",
    "其他债权投资公允价值变动": "Fair Value Changes of Other Debt Investments",
    "金融资产重分类计入其他综合收益的金额": "Amt. of Fin. Assets Reclassified to OCI",
    "其他债权投资信用减值准备": "Credit Impairment Provision for Other Debt Inv.",
    "持有至到期投资重分类为可供出售金融资产损益": "Gains/Losses on Reclassification of HTM to AFS",
    "现金流量套期储备": "Cash Flow Hedge Reserve",
    "现金流量套期损益的有效部分": "Effective Portion of Cash Flow Hedges",
    "外币财务报表折算差额": "Foreign Currency Translation Differences",

    # --- 兜底 ---
    "其他": "Others"
}

# 资产负债表列名中英文映射字典
# Balance Sheet Column Translation Map
translation_map_asset = {
    "Report Date": "Report Date",
    "流动资产": "Current Assets",
    "货币资金": "Cash and Cash Equivalents",
    "结算备付金": "Provision for Settlement",
    "拆出资金": "Funds Lent",
    "交易性金融资产": "Trading Financial Assets",
    "买入返售金融资产": "Financial Assets Purchased under Resale Agreements",
    "衍生金融资产": "Derivative Financial Assets",
    "应收票据及应收账款": "Notes and Accounts Receivable",
    "应收票据": "Notes Receivable",
    "应收账款": "Accounts Receivable",
    "应收款项融资": "Accounts Receivable Financing",
    "预付款项": "Prepayments",
    "应收股利": "Dividends Receivable",
    "应收利息": "Interest Receivable",
    "应收保费": "Premiums Receivable",
    "应收分保账款": "Reinsurance Accounts Receivable",
    "应收分保合同准备金": "Reinsurance Contract Reserve Receivable",
    "应收出口退税": "Export Tax Rebate Receivable",
    "应收补贴款": "Subsidies Receivable",
    "应收保证金": "Margin Receivable",
    "内部应收款": "Internal Receivables",
    "其他应收款": "Other Receivables",
    "其他应收款(合计)": "Total Other Receivables",
    "存货": "Inventories",
    "划分为持有待售的资产": "Assets Classified as Held for Sale",
    "待摊费用": "Deferred Expenses",
    "待处理流动资产损益": "Gains and Losses on Disposal of Current Assets",
    "一年内到期的非流动资产": "Non-current Assets Due within One Year",
    "其他流动资产": "Other Current Assets",
    "流动资产合计": "Total Current Assets",
    "非流动资产": "Non-current Assets",
    "发放贷款及垫款": "Loans and Advances",
    "债权投资": "Debt Investment",
    "其他债权投资": "Other Debt Investment",
    "以公允价值计量且其变动计入其他综合收益的金融资产": "Financial Assets at Fair Value through Other Comprehensive Income",
    "以摊余成本计量的金融资产": "Financial Assets at Amortized Cost",
    "可供出售金融资产": "Available-for-Sale Financial Assets",
    "长期股权投资": "Long-term Equity Investments",
    "投资性房地产": "Investment Property",
    "长期应收款": "Long-term Receivables",
    "其他权益工具投资": "Other Equity Instrument Investments",
    "其他非流动金融资产": "Other Non-current Financial Assets",
    "其他长期投资": "Other Long-term Investments",
    "固定资产原值": "Cost of Fixed Assets",
    "累计折旧": "Accumulated Depreciation",
    "固定资产净值": "Net Value of Fixed Assets",
    "固定资产减值准备": "Impairment Provision for Fixed Assets",
    "在建工程合计": "Total Construction in Progress",
    "在建工程": "Construction in Progress",
    "工程物资": "Engineering Materials",
    "固定资产净额": "Net Fixed Assets",
    "固定资产清理": "Disposal of Fixed Assets",
    "固定资产及清理合计": "Total Fixed Assets and Disposal",
    "生产性生物资产": "Productive Biological Assets",
    "公益性生物资产": "Public Welfare Biological Assets",
    "油气资产": "Oil and Gas Assets",
    "合同资产": "Contract Assets",
    "使用权资产": "Right-of-Use Assets",
    "无形资产": "Intangible Assets",
    "开发支出": "Development Expenditures",
    "商誉": "Goodwill",
    "长期待摊费用": "Long-term Deferred Expenses",
    "股权分置流通权": "Equity Division and Circulation Rights",
    "递延所得税资产": "Deferred Tax Assets",
    "其他非流动资产": "Other Non-current Assets",
    "非流动资产合计": "Total Non-current Assets",
    "资产总计": "Total Assets",
    "流动负债": "Current Liabilities",
    "短期借款": "Short-term Borrowings",
    "向中央银行借款": "Borrowings from Central Bank",
    "吸收存款及同业存放": "Deposits from Customers and Interbank Deposits",
    "拆入资金": "Funds Borrowed",
    "交易性金融负债": "Trading Financial Liabilities",
    "衍生金融负债": "Derivative Financial Liabilities",
    "应付票据及应付账款": "Notes and Accounts Payable",
    "应付票据": "Notes Payable",
    "应付账款": "Accounts Payable",
    "预收款项": "Advances from Customers",
    "合同负债": "Contract Liabilities",
    "卖出回购金融资产款": "Financial Assets Sold under Repurchase Agreements",
    "应付手续费及佣金": "Fees and Commissions Payable",
    "应付职工薪酬": "Employee Benefits Payable",
    "应交税费": "Taxes Payable",
    "应付利息": "Interest Payable",
    "应付股利": "Dividends Payable",
    "应付保证金": "Margin Payable",
    "内部应付款": "Internal Payables",
    "其他应付款": "Other Payables",
    "其他应付款合计": "Total Other Payables",
    "其他应交款": "Other Taxes Payable",
    "担保责任赔偿准备金": "Provision for Guarantee Compensation",
    "应付分保账款": "Reinsurance Accounts Payable",
    "保险合同准备金": "Insurance Contract Reserves",
    "代理买卖证券款": "Funds for Securities Trading on behalf of Clients",
    "代理承销证券款": "Funds for Securities Underwriting on behalf of Clients",
    "国际票证结算": "International Ticket Settlement",
    "国内票证结算": "Domestic Ticket Settlement",
    "预提费用": "Accrued Expenses",
    "预计流动负债": "Estimated Current Liabilities",
    "应付短期债券": "Short-term Bonds Payable",
    "划分为持有待售的负债": "Liabilities Classified as Held for Sale",
    "一年内的递延收益": "Deferred Income Due within One Year",
    "一年内到期的非流动负债": "Non-current Liabilities Due within One Year",
    "其他流动负债": "Other Current Liabilities",
    "流动负债合计": "Total Current Liabilities",
    "非流动负债": "Non-current Liabilities",
    "长期借款": "Long-term Borrowings",
    "应付债券": "Bonds Payable",
    "应付债券：优先股": "Bonds Payable: Preferred Shares",
    "应付债券：永续债": "Bonds Payable: Perpetual Bonds",
    "租赁负债": "Lease Liabilities",
    "长期应付职工薪酬": "Long-term Employee Benefits Payable",
    "长期应付款": "Long-term Payables",
    "长期应付款合计": "Total Long-term Payables",
    "专项应付款": "Special Payables",
    "预计非流动负债": "Estimated Non-current Liabilities",
    "长期递延收益": "Long-term Deferred Income",
    "递延所得税负债": "Deferred Tax Liabilities",
    "其他非流动负债": "Other Non-current Liabilities",
    "非流动负债合计": "Total Non-current Liabilities",
    "负债合计": "Total Liabilities",
    "所有者权益": "Owner's Equity",
    "实收资本(或股本)": "Paid-in Capital (or Share Capital)",
    "其他权益工具": "Other Equity Instruments",
    "优先股": "Preferred Shares",
    "永续债": "Perpetual Bonds",
    "资本公积": "Capital Reserve",
    "减:库存股": "Less: Treasury Stock",
    "Other Comprehensive Income (OCI)": "Other Comprehensive Income (OCI)",
    "专项储备": "Special Reserve",
    "盈余公积": "Surplus Reserve",
    "一般风险准备": "General Risk Reserve",
    "未确定的投资损失": "Undetermined Investment Losses",
    "未分配利润": "Retained Earnings",
    "拟分配现金股利": "Proposed Cash Dividends",
    "外币报表折算差额": "Foreign Currency Translation Differences",
    "归属于母公司股东权益合计": "Total Equity Attributable to Shareholders of the Parent Company",
    "少数股东权益": "Minority Interest",
    "所有者权益(或股东权益)合计": "Total Owner's Equity (or Shareholders' Equity)",
    "负债和所有者权益(或股东权益)总计": "Total Liabilities and Owner's Equity (or Shareholders' Equity)",
    "Data Source": "Data Source",
    "Audit Status": "Audit Status",
    "Announcement Date": "Announcement Date",
    "Currency": "Currency",
    "Report Type": "Report Type",
    "Update Date": "Update Date"
}

# 现金流量表列名中英文映射字典
# Cash Flow Statement Column Translation Map
translation_map_cashflow = {
    "报告日": "Report Date",
    "经营活动产生的现金流量": "Cash Flows from Operating Activities",
    "销售商品、提供劳务收到的现金": "Cash Received from Sales of Goods and Rendering of Services",
    "客户存款和同业存放款项净增加额": "Net Increase in Customer Deposits and Interbank Deposits",
    "向中央银行借款净增加额": "Net Increase in Borrowings from Central Bank",
    "向其他金融机构拆入资金净增加额": "Net Increase in Funds Borrowed from Other Financial Institutions",
    "收到原保险合同保费取得的现金": "Cash Received from Premiums of Original Insurance Contracts",
    "收到再保险业务现金净额": "Net Cash Received from Reinsurance Business",
    "保户储金及投资款净增加额": "Net Increase in Deposits and Investments from Policyholders",
    "处置交易性金融资产净增加额": "Net Increase in Cash from Disposal of Trading Financial Assets",
    "收取利息、手续费及佣金的现金": "Cash Received from Interest, Fees, and Commissions",
    "拆入资金净增加额": "Net Increase in Funds Borrowed",
    "回购业务资金净增加额": "Net Increase in Funds from Repurchase Business",
    "收到的税费返还": "Tax Refunds Received",
    "收到的其他与经营活动有关的现金": "Other Cash Received Relating to Operating Activities",
    "经营活动现金流入小计": "Subtotal of Cash Inflows from Operating Activities",
    "购买商品、接受劳务支付的现金": "Cash Paid for Goods and Services",
    "客户贷款及垫款净增加额": "Net Increase in Loans and Advances to Customers",
    "存放中央银行和同业款项净增加额": "Net Increase in Deposits with Central Bank and Interbank Deposits",
    "支付原保险合同赔付款项的现金": "Cash Paid for Claims of Original Insurance Contracts",
    "支付利息、手续费及佣金的现金": "Cash Paid for Interest, Fees, and Commissions",
    "支付保单红利的现金": "Cash Paid for Policy Dividends",
    "支付给职工以及为职工支付的现金": "Cash Paid to and for Employees",
    "支付的各项税费": "Taxes Paid",
    "支付的其他与经营活动有关的现金": "Other Cash Paid Relating to Operating Activities",
    "经营活动现金流出小计": "Subtotal of Cash Outflows from Operating Activities",
    "经营活动产生的现金流量净额": "Net Cash Flow from Operating Activities",
    "投资活动产生的现金流量": "Cash Flows from Investing Activities",
    "收回投资所收到的现金": "Cash Received from Return of Investments",
    "取得投资收益收到的现金": "Cash Received from Investment Income",
    "处置固定资产、无形资产和其他长期资产所收回的现金净额": "Net Cash Received from Disposal of Fixed Assets, Intangible Assets, and Other Long-term Assets",
    "处置子公司及其他营业单位收到的现金净额": "Net Cash Received from Disposal of Subsidiaries and Other Business Units",
    "收到的其他与投资活动有关的现金": "Other Cash Received Relating to Investing Activities",
    "减少质押和定期存款所收到的现金": "Cash Received from Decrease in Pledged and Time Deposits",
    "处置可供出售金融资产净增加额": "Net Increase in Cash from Disposal of Available-for-Sale Financial Assets",
    "投资活动现金流入小计": "Subtotal of Cash Inflows from Investing Activities",
    "购建固定资产、无形资产和其他长期资产所支付的现金": "Cash Paid for Acquisition of Fixed Assets, Intangible Assets, and Other Long-term Assets",
    "投资所支付的现金": "Cash Paid for Investments",
    "质押贷款净增加额": "Net Increase in Pledged Loans",
    "取得子公司及其他营业单位支付的现金净额": "Net Cash Paid for Acquisition of Subsidiaries and Other Business Units",
    "增加质押和定期存款所支付的现金": "Cash Paid for Increase in Pledged and Time Deposits",
    "支付的其他与投资活动有关的现金": "Other Cash Paid Relating to Investing Activities",
    "投资活动现金流出小计": "Subtotal of Cash Outflows from Investing Activities",
    "投资活动产生的现金流量净额": "Net Cash Flow from Investing Activities",
    "筹资活动产生的现金流量": "Cash Flows from Financing Activities",
    "吸收投资收到的现金": "Cash Received from Capital Contributions",
    "子公司吸收少数股东投资收到的现金": "Cash Received by Subsidiaries from Minority Shareholders' Investments",
    "取得借款收到的现金": "Cash Received from Borrowings",
    "发行债券收到的现金": "Cash Received from Issuing Bonds",
    "收到其他与筹资活动有关的现金": "Other Cash Received Relating to Financing Activities",
    "筹资活动现金流入小计": "Subtotal of Cash Inflows from Financing Activities",
    "偿还债务支付的现金": "Cash Paid for Repayment of Debts",
    "分配股利、利润或偿付利息所支付的现金": "Cash Paid for Distribution of Dividends, Profits, or Payment of Interest",
    "子公司支付给少数股东的股利、利润": "Dividends and Profits Paid by Subsidiaries to Minority Shareholders",
    "支付其他与筹资活动有关的现金": "Other Cash Paid Relating to Financing Activities",
    "筹资活动现金流出小计": "Subtotal of Cash Outflows from Financing Activities",
    "筹资活动产生的现金流量净额": "Net Cash Flow from Financing Activities",
    "汇率变动对现金及现金等价物的影响": "Effect of Foreign Exchange Rate Changes on Cash and Cash Equivalents",
    "现金及现金等价物净增加额": "Net Increase in Cash and Cash Equivalents",
    "期初现金及现金等价物余额": "Opening Balance of Cash and Cash Equivalents",
    "现金的期末余额": "Closing Balance of Cash",
    "现金的期初余额": "Opening Balance of Cash",
    "现金等价物的期末余额": "Closing Balance of Cash Equivalents",
    "现金等价物的期初余额": "Opening Balance of Cash Equivalents",
    "期末现金及现金等价物余额": "Closing Balance of Cash and Cash Equivalents",
    "数据源": "Data Source",
    "是否审计": "Audit Status",
    "公告日期": "Announcement Date",
    "币种": "Currency",
    "类型": "Report Type",
    "更新日期": "Update Date"
}


# ========================================
# 内部函数 - Internal Functions
# ========================================

def _normalize_report_data(df, symbol, source_name):
    """
    标准化财报数据格式
    Normalize financial report data format to unified standard

    统一输出标准:
    - Columns: 英文列名 (English column names)
    - 验证必需列是否存在 (Verify required columns exist)
    - 处理数据类型转换 (Handle data type conversion)

    Args:
        df: 原始DataFrame (Raw DataFrame)
        symbol: 报表类型 (Report type: "资产负债表", "利润表", "现金流量表")
        source_name: 数据源名称 (Data source name: 'akshare' or 'yfinance')

    Returns:
        pd.DataFrame: 标准化后的DataFrame (Normalized DataFrame)
    """
    if df is None or df.empty:
        return pd.DataFrame()

    try:
        # 应用列名映射 (Apply column name mapping)
        if source_name == 'akshare':
            if symbol == "利润表":
                df = df.rename(columns=translation_map_income)
            elif symbol == "资产负债表":
                df = df.rename(columns=translation_map_asset)
            elif symbol == "现金流量表":
                df = df.rename(columns=translation_map_cashflow)

        # 验证关键列 (Verify key columns)
        required_cols = {
            "利润表": ['Operating Revenue', 'Net Profit Attributable to Parent'],
            "资产负债表": ['Total Assets', 'Total Equity Attributable to Shareholders of the Parent Company'],
            "现金流量表": ['Net Cash Flow from Operating Activities']
        }

        missing_cols = []
        for col in required_cols.get(symbol, []):
            if col not in df.columns:
                missing_cols.append(col)

        if missing_cols:
            logger.warning(f"[数据标准化] {symbol} 缺少部分关键列: {missing_cols}")

        return df

    except Exception as e:
        logger.error(f"[数据标准化错误] {source_name} - {symbol}: {e}")
        return pd.DataFrame()


def _get_report_data_akshare(stock, symbol):
    """
    使用AKShare获取财报 (新浪财经)
    Get financial report using AKShare (Sina Finance)

    Args:
        stock: 股票代码 (Stock code, e.g., "600519")
        symbol: 报表类型 (Report type: "资产负债表", "利润表", "现金流量表")

    Returns:
        pd.DataFrame: 标准化的财报数据 (Normalized financial report data)
    """
    try:
        # 获取AKShare数据 (Fetch data from AKShare)
        df = ak.stock_financial_report_sina(stock=stock, symbol=symbol)

        if df is None or df.empty:
            logger.warning(f"[AKShare] {stock} - {symbol}: 返回空数据")
            return pd.DataFrame()

        # 标准化数据 (Normalize data)
        df = _normalize_report_data(df, symbol, 'akshare')

        if not df.empty:
            logger.info(f"[数据源:AKShare] {stock} - {symbol}: 获取成功 ({len(df)}期)")

        return df

    except requests.Timeout:
        logger.error(f"[AKShare] {stock} - {symbol}: 网络超时")
        return pd.DataFrame()

    except requests.exceptions.SSLError as e:
        logger.error(f"[AKShare] {stock} - {symbol}: SSL连接错误 - {e}")
        return pd.DataFrame()

    except KeyError as e:
        logger.error(f"[AKShare] {stock} - {symbol}: 股票不存在或数据格式错误 - {e}")
        return pd.DataFrame()

    except Exception as e:
        logger.error(f"[AKShare] {stock} - {symbol}: 未知错误 - {e}")
        return pd.DataFrame()


def _get_report_data_yfinance(stock, symbol):
    """
    使用yfinance获取财报 (占位实现)
    Get financial report using yfinance (placeholder implementation)

    注意: yfinance不支持A股财报数据
    Note: yfinance does NOT support A-share financial reports

    Args:
        stock: 股票代码 (Stock code)
        symbol: 报表类型 (Report type)

    Returns:
        pd.DataFrame: 空DataFrame (Empty DataFrame)
    """
    logger.warning(f"[yfinance] {stock} - {symbol}: yfinance不支持A股财报,返回空数据")
    logger.info(f"[提示] 如需备援数据源,建议集成Tushare Pro或Eastmoney")
    return pd.DataFrame()


def _get_report_data_auto(stock, symbol):
    """
    自动备援策略
    Auto fallback strategy

    优先akshare,失败记录日志
    Priority: akshare first, log on failure

    Args:
        stock: 股票代码 (Stock code)
        symbol: 报表类型 (Report type)

    Returns:
        pd.DataFrame: 财报数据 (Financial report data)
    """
    # 优先尝试akshare (Try akshare first)
    df = _get_report_data_akshare(stock, symbol)

    if not df.empty:
        return df

    # akshare失败,记录日志 (akshare failed, log it)
    logger.warning(f"[数据源切换] {stock} - {symbol}: AKShare获取失败")

    # yfinance不支持A股财报,不尝试切换
    # yfinance doesn't support A-share reports, don't try switching
    logger.info(f"[数据源切换] {stock} - {symbol}: 无可用备援数据源 (yfinance不支持A股财报)")

    return pd.DataFrame()


# ========================================
# 主函数 - Main Function
# ========================================

def get_report_data(stock="", symbol="", transpose=True, source='auto'):
    """
    获取股票的财务报告数据并处理为标准格式 (支持多数据源)
    Get stock financial report data and process to standard format (supports multiple data sources)

    参数 / Parameters:
        stock: 股票代码 (Stock code)
               - A股: "600519", "000858"
        symbol: 报告类型 (Report type)
                - 可选: "资产负债表", "利润表", "现金流量表"
        transpose: 是否转置数据 (Whether to transpose data)
                   - 默认True (保持向后兼容)
                   - 注意: 当前版本transpose功能暂未实现,保留参数以兼容现有代码
        source: 数据源选择 (Data source selection)
                - 'auto': 自动选择 (默认: akshare)
                - 'akshare': 仅使用akshare (新浪财经)
                - 'yfinance': 仅使用yfinance (注意: 不支持A股财报)

    返回 / Returns:
        pd.DataFrame:
            columns: 英文列名 (English column names)
            rows: 各期财报数据 (Financial report data for each period)

    示例 / Examples:
        >>> # 基础用法 (默认auto模式)
        >>> df = get_report_data(stock="600519", symbol="利润表")

        >>> # 指定数据源
        >>> df = get_report_data(stock="600519", symbol="资产负债表", source='akshare')

        >>> # 不转置 (参数保留,功能待实现)
        >>> df = get_report_data(stock="600519", symbol="现金流量表", transpose=False)
    """
    # 参数验证 (Parameter validation)
    if not stock:
        logger.error("[参数错误] 股票代码不能为空")
        return pd.DataFrame()

    if symbol not in ["资产负债表", "利润表", "现金流量表"]:
        logger.error(f"[参数错误] 无效的报表类型: {symbol}")
        return pd.DataFrame()

    # 根据source参数选择数据源 (Select data source based on source parameter)
    if source == 'auto':
        df = _get_report_data_auto(stock, symbol)
    elif source == 'akshare':
        df = _get_report_data_akshare(stock, symbol)
    elif source == 'yfinance':
        df = _get_report_data_yfinance(stock, symbol)
    else:
        logger.error(f"[参数错误] 不支持的数据源: {source}。可选: 'auto', 'akshare', 'yfinance'")
        return pd.DataFrame()

    # 最终检查 (Final check)
    if df.empty:
        logger.warning(f"[获取失败] {stock} - {symbol}: 所有数据源均失败,返回空DataFrame")

    # 注意: transpose功能暂未实现,保留参数以兼容现有代码
    # Note: transpose functionality not yet implemented, parameter retained for backward compatibility
    if transpose is False:
        logger.debug(f"[提示] transpose=False参数已接收,但功能暂未实现")

    return df
