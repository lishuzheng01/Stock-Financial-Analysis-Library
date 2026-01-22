# stock_tool/__init__.py
from .get_report_data import get_report_data
from .get_stock_data import get_stock_data
from .AltmanZScore import analyze_altman_zscore
from .BeneishMScore import analyze_beneish_mscore, beneish_mscore_check
from .CheckBenford import check_benford

# DuPont Analysis (杜邦分析)
from .DuPontAnalysis import analyze_dupont_roe_3factor, analyze_dupont_roe_5factor

# Profitability Analysis (盈利能力分析)
from .ProfitabilityAnalysis import (
    analyze_gross_margin,
    analyze_net_margin,
    analyze_roe,
    analyze_roa,
    analyze_roic
)

# Valuation Ratios (相对估值分析)
from .ValuationRatios import (
    analyze_pe_ratio,
    analyze_pb_ratio,
    analyze_ps_ratio,
    analyze_peg_ratio,
    analyze_ev_ebitda
)

# Cash Flow Analysis (现金流分析)
from .CashFlowAnalysis import (
    analyze_operating_cashflow_quality,
    analyze_free_cashflow,
    analyze_cashflow_adequacy,
    analyze_cash_conversion_cycle
)

__all__ = [
    # Data acquisition
    'get_report_data',
    'get_stock_data',

    # Risk analysis
    'analyze_altman_zscore',
    'beneish_mscore_check',
    'analyze_beneish_mscore',
    'check_benford',

    # DuPont Analysis
    'analyze_dupont_roe_3factor',
    'analyze_dupont_roe_5factor',

    # Profitability Analysis
    'analyze_gross_margin',
    'analyze_net_margin',
    'analyze_roe',
    'analyze_roa',
    'analyze_roic',

    # Valuation Ratios
    'analyze_pe_ratio',
    'analyze_pb_ratio',
    'analyze_ps_ratio',
    'analyze_peg_ratio',
    'analyze_ev_ebitda',

    # Cash Flow Analysis
    'analyze_operating_cashflow_quality',
    'analyze_free_cashflow',
    'analyze_cashflow_adequacy',
    'analyze_cash_conversion_cycle',
]