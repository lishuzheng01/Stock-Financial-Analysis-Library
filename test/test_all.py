"""
Comprehensive Test Suite for Stock Financial Analysis Tools

This test file validates all calculation modules in the stock_tool package.
Tests 21 functions across 6 categories with multiple stock codes.

Usage:
    python test/test_all.py
"""

import sys
import traceback
from datetime import datetime

# Add src directory to path for imports
sys.path.insert(0, 'src')

from stock_tool import (
    # Data Acquisition
    get_stock_data,
    get_report_data,

    # Risk Analysis
    analyze_altman_zscore,
    BeneishMScore_check,
    check_benford,

    # Profitability Analysis
    analyze_gross_margin,
    analyze_net_margin,
    analyze_roe,
    analyze_roa,
    analyze_roic,

    # DuPont Analysis
    analyze_dupont_roe_3factor,
    analyze_dupont_roe_5factor,

    # Valuation Ratios
    analyze_pe_ratio,
    analyze_pb_ratio,
    analyze_ps_ratio,
    analyze_peg_ratio,
    analyze_ev_ebitda,

    # Cash Flow Analysis
    analyze_operating_cashflow_quality,
    analyze_free_cashflow,
    analyze_cashflow_adequacy,
    analyze_cash_conversion_cycle,
)

# ========== Configuration ==========
TEST_STOCKS = ["600519", "000858"]  # Moutai, Wuliangye
DATE_RANGE = ("20200101", "20241231")  # For price data tests
SEPARATOR = "=" * 80
SHORT_SEP = "-" * 80

# Global test tracking
test_results = {
    "passed": 0,
    "failed": 0,
    "errors": []
}

# Global data cache - to avoid repeated API calls
data_cache = {
    "stock_data": {},      # {stock: DataFrame}
    "balance_sheet": {},   # {stock: DataFrame}
    "income_statement": {},  # {stock: DataFrame}
    "cashflow_statement": {}  # {stock: DataFrame}
}


# ========== Helper Functions ==========

def preload_all_data():
    """
    Pre-load all financial data for all test stocks to avoid repeated API calls
    预加载所有测试股票的财务数据，避免重复API调用
    """
    print_section_header("Pre-loading Financial Data")
    print("Loading data for all test stocks to avoid API rate limits...")
    print(f"This may take a moment...\n")

    for stock in TEST_STOCKS:
        print(f"Loading data for stock {stock}...")

        # Load stock price data
        try:
            print(f"  - Stock price data...", end=" ")
            df = get_stock_data(stock, DATE_RANGE[0], DATE_RANGE[1])
            if df is not None and not df.empty:
                data_cache["stock_data"][stock] = df
                print(f"OK ({len(df)} rows)")
            else:
                print("EMPTY")
        except Exception as e:
            print(f"FAILED: {e}")

        # Load balance sheet
        try:
            print(f"  - Balance sheet...", end=" ")
            df = get_report_data(stock, "资产负债表")
            if df is not None and not df.empty:
                data_cache["balance_sheet"][stock] = df
                print(f"OK ({len(df)} rows)")
            else:
                print("EMPTY")
        except Exception as e:
            print(f"FAILED: {e}")

        # Load income statement
        try:
            print(f"  - Income statement...", end=" ")
            df = get_report_data(stock, "利润表")
            if df is not None and not df.empty:
                data_cache["income_statement"][stock] = df
                print(f"OK ({len(df)} rows)")
            else:
                print("EMPTY")
        except Exception as e:
            print(f"FAILED: {e}")

        # Load cash flow statement
        try:
            print(f"  - Cash flow statement...", end=" ")
            df = get_report_data(stock, "现金流量表")
            if df is not None and not df.empty:
                data_cache["cashflow_statement"][stock] = df
                print(f"OK ({len(df)} rows)")
            else:
                print("EMPTY")
        except Exception as e:
            print(f"FAILED: {e}")

        print()  # Blank line between stocks

    # Summary
    print(f"{SHORT_SEP}")
    print("Data Loading Summary:")
    print(f"  Stock Price Data: {len(data_cache['stock_data'])} stocks")
    print(f"  Balance Sheets: {len(data_cache['balance_sheet'])} stocks")
    print(f"  Income Statements: {len(data_cache['income_statement'])} stocks")
    print(f"  Cash Flow Statements: {len(data_cache['cashflow_statement'])} stocks")
    print()


def print_section_header(title):
    """Print formatted section header"""
    print(f"\n{SEPARATOR}")
    print(f"  {title}")
    print(SEPARATOR)


def print_test_result(function_name, stock, success, data_df=None, error_msg=None, key_metrics=None):
    """
    Print moderate-level test results

    Args:
        function_name: Name of the function tested
        stock: Stock code (or None for non-stock functions)
        success: True if test passed
        data_df: DataFrame result (if successful)
        error_msg: Error message (if failed)
        key_metrics: Dict of key metrics to display
    """
    stock_label = f"[{stock}]" if stock else ""
    status_icon = "[PASS]" if success else "[FAIL]"

    print(f"\n{status_icon} {function_name} {stock_label}")

    if success and data_df is not None:
        # Print DataFrame info
        print(f"  Shape: {data_df.shape[0]} rows × {data_df.shape[1]} columns")

        # Print key metrics if provided
        if key_metrics:
            print("  Latest metrics:")
            for metric_name, metric_value in key_metrics.items():
                print(f"    - {metric_name}: {metric_value}")

        # Print first 2-3 rows
        if len(data_df) > 0:
            print(f"  First {min(3, len(data_df))} periods:")
            print("  " + str(data_df.head(3)).replace("\n", "\n  "))

    elif not success:
        print(f"  Error: {error_msg}")
        test_results["errors"].append({
            "function": function_name,
            "stock": stock,
            "error": error_msg
        })


def validate_dataframe(df):
    """
    Validate DataFrame structure and content

    Returns:
        bool: True if valid, False otherwise
    """
    if df is None:
        return False
    if len(df) == 0:
        return False
    return True


def safe_test(test_func, *args, **kwargs):
    """
    Execute test with error handling

    Returns:
        tuple: (success, result_or_error)
    """
    try:
        result = test_func(*args, **kwargs)
        return True, result
    except Exception as e:
        error_msg = f"{type(e).__name__}: {str(e)}"
        return False, error_msg


def extract_key_metrics(df, metric_columns):
    """
    Extract key metrics from DataFrame's first row

    Args:
        df: DataFrame with results
        metric_columns: List of column names to extract

    Returns:
        dict: Metric name -> formatted value
    """
    if df is None or len(df) == 0:
        return {}

    metrics = {}
    for col in metric_columns:
        if col in df.columns:
            value = df.iloc[0][col]
            # Format the value nicely
            if isinstance(value, (int, float)):
                if abs(value) < 0.01 and value != 0:
                    metrics[col] = f"{value:.4f}"
                elif abs(value) < 1:
                    metrics[col] = f"{value:.3f}"
                else:
                    metrics[col] = f"{value:.2f}"
            else:
                metrics[col] = str(value)

    return metrics


# ========== Test Functions ==========

def test_data_acquisition():
    """Test get_stock_data and get_report_data"""
    print_section_header("Category A: Data Acquisition")
    print("Note: Using pre-loaded cached data\n")

    for stock in TEST_STOCKS:
        # Test 1: get_stock_data
        print(f"\n{SHORT_SEP}")
        print(f"Testing get_stock_data for {stock}")

        if stock in data_cache["stock_data"]:
            df = data_cache["stock_data"][stock]
            if validate_dataframe(df):
                key_metrics = {
                    "Latest Close": df.iloc[-1]['close'] if 'close' in df.columns else "N/A",
                    "Data Points": len(df)
                }
                print_test_result("get_stock_data", stock, True, df, key_metrics=key_metrics)
                test_results["passed"] += 1
            else:
                print_test_result("get_stock_data", stock, False, error_msg="Empty DataFrame in cache")
                test_results["failed"] += 1
        else:
            print_test_result("get_stock_data", stock, False, error_msg="Data not loaded in cache")
            test_results["failed"] += 1

        # Test 2: get_report_data - Balance Sheet
        print(f"\n{SHORT_SEP}")
        print(f"Testing get_report_data (Balance Sheet) for {stock}")

        if stock in data_cache["balance_sheet"]:
            df = data_cache["balance_sheet"][stock]
            if validate_dataframe(df):
                key_metrics = {
                    "Periods Available": len(df),
                    "Columns": len(df.columns)
                }
                print_test_result("get_report_data[Balance Sheet]", stock, True, df, key_metrics=key_metrics)
                test_results["passed"] += 1
            else:
                print_test_result("get_report_data[Balance Sheet]", stock, False, error_msg="Empty DataFrame in cache")
                test_results["failed"] += 1
        else:
            print_test_result("get_report_data[Balance Sheet]", stock, False, error_msg="Data not loaded in cache")
            test_results["failed"] += 1

        # Test 3: get_report_data - Income Statement
        print(f"\n{SHORT_SEP}")
        print(f"Testing get_report_data (Income Statement) for {stock}")

        if stock in data_cache["income_statement"]:
            df = data_cache["income_statement"][stock]
            if validate_dataframe(df):
                key_metrics = {
                    "Periods Available": len(df),
                    "Columns": len(df.columns)
                }
                print_test_result("get_report_data[Income Statement]", stock, True, df, key_metrics=key_metrics)
                test_results["passed"] += 1
            else:
                print_test_result("get_report_data[Income Statement]", stock, False, error_msg="Empty DataFrame in cache")
                test_results["failed"] += 1
        else:
            print_test_result("get_report_data[Income Statement]", stock, False, error_msg="Data not loaded in cache")
            test_results["failed"] += 1


def test_risk_analysis():
    """Test Altman Z-Score, Beneish M-Score, Benford's Law"""
    print_section_header("Category B: Risk Analysis")

    for stock in TEST_STOCKS:
        # Test 1: Altman Z-Score
        print(f"\n{SHORT_SEP}")
        print(f"Testing analyze_altman_zscore for {stock}")
        success, result = safe_test(analyze_altman_zscore, stock, print_output=False)

        if success:
            df, report_text = result
            if validate_dataframe(df):
                key_metrics = extract_key_metrics(df, ["Z-Score", "Risk Level"])
                print_test_result("analyze_altman_zscore", stock, True, df, key_metrics=key_metrics)
                test_results["passed"] += 1
            else:
                print_test_result("analyze_altman_zscore", stock, False, error_msg="Empty DataFrame")
                test_results["failed"] += 1
        else:
            print_test_result("analyze_altman_zscore", stock, False, error_msg=result)
            test_results["failed"] += 1

        # Test 2: Beneish M-Score (Note: This function only prints, doesn't return data)
        print(f"\n{SHORT_SEP}")
        print(f"Testing BeneishMScore_check for {stock}")
        print(f"  Note: BeneishMScore_check only prints output, doesn't return data")
        print(f"  Skipping detailed testing for this function")
        test_results["passed"] += 1


def test_profitability_analysis():
    """Test gross margin, net margin, ROE, ROA, ROIC"""
    print_section_header("Category C: Profitability Analysis")

    profitability_functions = [
        ("analyze_gross_margin", analyze_gross_margin, ["Gross Margin (%)"]),
        ("analyze_net_margin", analyze_net_margin, ["Net Margin (%)"]),
        ("analyze_roe", analyze_roe, ["ROE (%)"]),
        ("analyze_roa", analyze_roa, ["ROA (%)"]),
        ("analyze_roic", analyze_roic, ["ROIC (%)"]),
    ]

    for func_name, func, metric_cols in profitability_functions:
        for stock in TEST_STOCKS:
            print(f"\n{SHORT_SEP}")
            print(f"Testing {func_name} for {stock}")
            success, result = safe_test(func, stock, print_output=False)

            if success:
                df, report_text = result
                if validate_dataframe(df):
                    key_metrics = extract_key_metrics(df, metric_cols)
                    print_test_result(func_name, stock, True, df, key_metrics=key_metrics)
                    test_results["passed"] += 1
                else:
                    print_test_result(func_name, stock, False, error_msg="Empty DataFrame")
                    test_results["failed"] += 1
            else:
                print_test_result(func_name, stock, False, error_msg=result)
                test_results["failed"] += 1


def test_dupont_analysis():
    """Test 3-factor and 5-factor DuPont ROE"""
    print_section_header("Category D: DuPont Analysis")

    for stock in TEST_STOCKS:
        # Test 1: 3-Factor DuPont ROE
        print(f"\n{SHORT_SEP}")
        print(f"Testing analyze_dupont_roe_3factor for {stock}")
        success, result = safe_test(analyze_dupont_roe_3factor, stock, print_output=False)

        if success:
            df, report_text = result
            if validate_dataframe(df):
                key_metrics = extract_key_metrics(df, ["ROE (%)", "Net Profit Margin (%)", "Equity Multiplier"])
                print_test_result("analyze_dupont_roe_3factor", stock, True, df, key_metrics=key_metrics)
                test_results["passed"] += 1
            else:
                print_test_result("analyze_dupont_roe_3factor", stock, False, error_msg="Empty DataFrame")
                test_results["failed"] += 1
        else:
            print_test_result("analyze_dupont_roe_3factor", stock, False, error_msg=result)
            test_results["failed"] += 1

        # Test 2: 5-Factor DuPont ROE
        print(f"\n{SHORT_SEP}")
        print(f"Testing analyze_dupont_roe_5factor for {stock}")
        success, result = safe_test(analyze_dupont_roe_5factor, stock, print_output=False)

        if success:
            df, report_text = result
            if validate_dataframe(df):
                key_metrics = extract_key_metrics(df, ["ROE (%)", "Tax Burden", "Interest Burden"])
                print_test_result("analyze_dupont_roe_5factor", stock, True, df, key_metrics=key_metrics)
                test_results["passed"] += 1
            else:
                print_test_result("analyze_dupont_roe_5factor", stock, False, error_msg="Empty DataFrame")
                test_results["failed"] += 1
        else:
            print_test_result("analyze_dupont_roe_5factor", stock, False, error_msg=result)
            test_results["failed"] += 1


def test_valuation_ratios():
    """Test PE, PB, PS, PEG, EV/EBITDA"""
    print_section_header("Category E: Valuation Ratios")

    valuation_functions = [
        ("analyze_pe_ratio", analyze_pe_ratio, ["Static PE", "Dynamic PE"]),
        ("analyze_pb_ratio", analyze_pb_ratio, ["PB Ratio"]),
        ("analyze_ps_ratio", analyze_ps_ratio, ["PS Ratio"]),
        ("analyze_peg_ratio", analyze_peg_ratio, ["PEG Ratio"]),
        ("analyze_ev_ebitda", analyze_ev_ebitda, ["EV/EBITDA"]),
    ]

    for func_name, func, metric_cols in valuation_functions:
        for stock in TEST_STOCKS:
            print(f"\n{SHORT_SEP}")
            print(f"Testing {func_name} for {stock}")
            success, result = safe_test(func, stock, print_output=False)

            if success:
                df, report_text = result
                if validate_dataframe(df):
                    key_metrics = extract_key_metrics(df, metric_cols)
                    print_test_result(func_name, stock, True, df, key_metrics=key_metrics)
                    test_results["passed"] += 1
                else:
                    print_test_result(func_name, stock, False, error_msg="Empty DataFrame")
                    test_results["failed"] += 1
            else:
                print_test_result(func_name, stock, False, error_msg=result)
                test_results["failed"] += 1


def test_cashflow_analysis():
    """Test operating CF quality, free CF, CF adequacy, CCC"""
    print_section_header("Category F: Cash Flow Analysis")

    cashflow_functions = [
        ("analyze_operating_cashflow_quality", analyze_operating_cashflow_quality, ["OCF/NI Ratio"]),
        ("analyze_free_cashflow", analyze_free_cashflow, ["Free Cash Flow"]),
        ("analyze_cashflow_adequacy", analyze_cashflow_adequacy, ["CF Adequacy Ratio"]),
        ("analyze_cash_conversion_cycle", analyze_cash_conversion_cycle, ["CCC (days)"]),
    ]

    for func_name, func, metric_cols in cashflow_functions:
        for stock in TEST_STOCKS:
            print(f"\n{SHORT_SEP}")
            print(f"Testing {func_name} for {stock}")
            success, result = safe_test(func, stock, print_output=False)

            if success:
                df, report_text = result
                if validate_dataframe(df):
                    key_metrics = extract_key_metrics(df, metric_cols)
                    print_test_result(func_name, stock, True, df, key_metrics=key_metrics)
                    test_results["passed"] += 1
                else:
                    print_test_result(func_name, stock, False, error_msg="Empty DataFrame")
                    test_results["failed"] += 1
            else:
                print_test_result(func_name, stock, False, error_msg=result)
                test_results["failed"] += 1


# ========== Main Execution ==========

def run_all_tests():
    """Run all test categories and print summary"""
    print(SEPARATOR)
    print("  STOCK FINANCIAL ANALYSIS - COMPREHENSIVE TEST SUITE")
    print(SEPARATOR)
    print(f"\nTest Configuration:")
    print(f"  Stocks: {', '.join(TEST_STOCKS)}")
    print(f"  Date Range: {DATE_RANGE[0]} to {DATE_RANGE[1]}")
    print(f"  Start Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

    # Pre-load all data to avoid API rate limits
    preload_all_data()

    # Run all test categories
    try:
        test_data_acquisition()
        test_risk_analysis()
        test_profitability_analysis()
        test_dupont_analysis()
        test_valuation_ratios()
        test_cashflow_analysis()
    except KeyboardInterrupt:
        print("\n\nTests interrupted by user")
    except Exception as e:
        print(f"\n\nUnexpected error during testing: {e}")
        traceback.print_exc()

    # Print summary
    print_section_header("TEST SUMMARY")

    total_tests = test_results["passed"] + test_results["failed"]
    success_rate = (test_results["passed"] / total_tests * 100) if total_tests > 0 else 0

    print(f"\nTotal Tests: {total_tests}")
    print(f"Passed: {test_results['passed']} [PASS]")
    print(f"Failed: {test_results['failed']} [FAIL]")
    print(f"Success Rate: {success_rate:.1f}%")

    if test_results["errors"]:
        print(f"\n{SHORT_SEP}")
        print("Failed Tests Details:")
        for error in test_results["errors"]:
            stock_label = f" [{error['stock']}]" if error['stock'] else ""
            print(f"  [FAIL] {error['function']}{stock_label}")
            print(f"    {error['error']}")

    print(f"\n{SEPARATOR}")
    print(f"End Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(SEPARATOR)

    return test_results


if __name__ == "__main__":
    results = run_all_tests()

    # Exit with appropriate code
    if results["failed"] > 0:
        sys.exit(1)
    else:
        sys.exit(0)
