#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
股票财务分析完整工作流 (高性能优化版)
集成多线程并行处理、线程安全缓存和优化的I/O操作
"""

# ==========================================
# 配置区 (Configuration)
# ==========================================

# 工作流配置
STOCK_CODE = "600519"  # 股票代码
START_DATE = "20200101"  # 开始日期，格式：YYYYMMDD
END_DATE = None  # 结束日期，格式：YYYYMMDD，默认为当前日期
SILENT_MODE = False  # 是否静默模式

# 性能配置
MAX_WORKERS = 4  # 最大并行工作线程数 (建议设置为CPU核心数)
ENABLE_PARALLEL = True  # 是否启用并行执行

# 日志配置
LOG_LEVEL = "INFO"  # 日志级别：DEBUG, INFO, WARNING, ERROR
LOG_FILE = "stock_analysis_workflow.log"  # 日志文件名

# 缓存配置
ENABLE_CACHE = True  # 是否启用数据缓存
CACHE_CLEAR_ON_START = True  # 启动时是否清除缓存

# 报告配置
REPORT_DIR = "reports"  # 报告输出目录

# ==========================================

import logging
import pandas as pd
import os
import sys
import traceback
import threading
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor, as_completed

# 导入stock_tool包中的所有函数
# 假设 stock_tool 已经安装或在路径中
try:
    from stock_tool import (
        # 数据获取
        get_report_data as original_get_report_data,
        get_stock_data,

        # 风险分析
        analyze_altman_zscore,
        BeneishMScore_check,
        analyze_beneish_mscore,
        check_benford,

        # 杜邦分析
        analyze_dupont_roe_3factor,
        analyze_dupont_roe_5factor,

        # 盈利能力分析
        analyze_gross_margin,
        analyze_net_margin,
        analyze_roe,
        analyze_roa,
        analyze_roic,

        # 估值分析
        analyze_pe_ratio,
        analyze_pb_ratio,
        analyze_ps_ratio,
        analyze_peg_ratio,
        analyze_ev_ebitda,

        # 现金流分析
        analyze_operating_cashflow_quality,
        analyze_free_cashflow,
        analyze_cashflow_adequacy,
        analyze_cash_conversion_cycle
    )
except ImportError:
    print("错误: 未找到 'stock_tool' 包。请确保已安装相关依赖。")
    sys.exit(1)

# ==========================================
# 线程安全的全局缓存系统
# ==========================================

global_data_cache = {}
cache_lock = threading.Lock()  # 读写锁

def get_report_data(stock, symbol, transpose=True, source='auto'):
    """线程安全的自定义get_report_data函数"""
    if not ENABLE_CACHE:
        return original_get_report_data(stock, symbol, transpose, source)
    
    cache_key = f"{stock}_{symbol}"
    
    # 读缓存（加锁）
    with cache_lock:
        if cache_key in global_data_cache:
            # 降低日志级别以减少I/O
            logger.debug(f"从全局缓存返回数据: {cache_key}")
            return global_data_cache[cache_key]
    
    # 缓存未命中，获取数据（释放锁，允许并行网络请求）
    logger.info(f"调用原始API获取数据: {cache_key}")
    result = original_get_report_data(stock, symbol, transpose, source)
    
    # 写缓存（加锁）
    with cache_lock:
        global_data_cache[cache_key] = result
        logger.debug(f"数据已存入全局缓存: {cache_key}")
    
    return result

def clear_data_cache():
    """清除全局数据缓存"""
    with cache_lock:
        global_data_cache.clear()
    logger.info("全局数据缓存已清除")

# ==========================================
# 日志系统配置
# ==========================================

log_level = getattr(logging, LOG_LEVEL.upper(), logging.INFO)
logging.basicConfig(
    level=log_level,
    format='%(asctime)s - [%(threadName)s] - %(levelname)s - %(message)s', # 增加线程名显示
    handlers=[
        logging.FileHandler(LOG_FILE, encoding='utf-8'),
        logging.StreamHandler(sys.stdout)
    ]
)

logger = logging.getLogger('StockAnalysisWorkflow')

# ==========================================
# 主工作流类
# ==========================================

class StockAnalysisWorkflow:
    """股票财务分析工作流类 (优化版)"""
    
    def __init__(self, stock_code, start_date='20200101', end_date=None, silent=False):
        self.stock_code = stock_code
        self.start_date = start_date
        self.end_date = end_date or datetime.now().strftime('%Y%m%d')
        self.silent = silent
        
        # 线程锁，用于保护 self.results 的写入
        self.lock = threading.Lock()
        
        self.results = {
            'data': {},
            'risk_analysis': {},
            'financial_analysis': {
                'dupont': {},
                'profitability': {},
                'valuation': {},
                'cashflow': {}
            }
        }
        
        self.errors = []
        logger.info(f"初始化工作流: {stock_code}, 模式: {'并行' if ENABLE_PARALLEL else '串行'}")
    
    def run(self):
        """执行完整工作流"""
        try:
            logger.info("开始执行完整工作流")
            start_time = datetime.now()
            
            # 1. 获取数据 (IO密集型，本身有网络延迟)
            self.get_data()
            
            # 2. 风险分析 (计算量较小，保持串行或简单优化)
            self.risk_analysis()
            
            # 3. 财务分析 (计算密集型且模块独立，采用并行加速)
            if ENABLE_PARALLEL:
                self.financial_analysis_parallel()
            else:
                self.financial_analysis_serial()
            
            # 4. 生成报告 (IO密集型)
            self.generate_report()
            
            duration = datetime.now() - start_time
            logger.info(f"完整工作流执行成功，耗时: {duration}")
            return True
        except Exception as e:
            logger.error(f"工作流执行失败: {str(e)}")
            logger.error(traceback.format_exc())
            self.errors.append(f"工作流执行失败: {str(e)}")
            return False
    
    def get_data(self, use_cache=True, force_update=False):
        """获取基础数据"""
        # ... (逻辑保持不变，但利用了线程安全的 get_report_data)
        if self.results['data'].get('price') is not None and not force_update:
            return
            
        cache_dir = f"cache/{self.stock_code}"
        os.makedirs(cache_dir, exist_ok=True)
        
        price_cache_path = os.path.join(cache_dir, f"price_{self.start_date}_{self.end_date}.csv")
        balance_cache_path = os.path.join(cache_dir, "balance_sheet.csv")
        income_cache_path = os.path.join(cache_dir, "income_statement.csv")
        cashflow_cache_path = os.path.join(cache_dir, "cashflow.csv")
        
        logger.info("开始获取数据...")
        
        try:
            # 1. 股票价格
            if use_cache and os.path.exists(price_cache_path) and not force_update:
                logger.info("加载价格缓存")
                price_data = pd.read_csv(price_cache_path, index_col=0, parse_dates=True)
            else:
                price_data = get_stock_data(self.stock_code, self.start_date, self.end_date, source='auto')
                price_data.to_csv(price_cache_path)
            
            self.results['data']['price'] = price_data
            
            # 2. 财务报表
            report_types = ["资产负债表", "利润表", "现金流量表"]
            paths = [balance_cache_path, income_cache_path, cashflow_cache_path]
            
            for r_type, path in zip(report_types, paths):
                if use_cache and os.path.exists(path) and not force_update:
                    logger.info(f"加载缓存: {r_type}")
                    data = pd.read_csv(path, index_col=0)
                else:
                    data = get_report_data(self.stock_code, r_type, transpose=True, source='auto')
                    data.to_csv(path)
                
                self.results['data'][r_type] = data
                
                # 预热全局缓存，供后续线程使用
                with cache_lock:
                    global_data_cache[f"{self.stock_code}_{r_type}"] = data

            logger.info("数据获取完成")
        except Exception as e:
            logger.error(f"数据获取失败: {str(e)}")
            self.errors.append(f"数据获取失败: {str(e)}")
            raise

    def risk_analysis(self):
        """执行风险分析"""
        logger.info("开始风险分析")
        try:
            # Altman Z-Score
            zscore_df, zscore_report = analyze_altman_zscore(self.stock_code)
            self.results['risk_analysis']['altman_zscore'] = {'data': zscore_df, 'report': zscore_report}
            
            # Beneish M-Score (注意：并行环境下最好关闭print输出)
            mscore_df, mscore_report = analyze_beneish_mscore(self.stock_code, print_output=False)
            self.results['risk_analysis']['beneish_mscore'] = {'data': mscore_df, 'report': mscore_report}
            
            # Benford
            benford_results = {}
            for r_type in ["资产负债表", "利润表", "现金流量表"]:
                try:
                    res = check_benford(self.stock_code, r_type)
                    benford_results[r_type] = res
                except Exception as e:
                    benford_results[r_type] = f"Error: {str(e)}"
            self.results['risk_analysis']['benford'] = benford_results
            
            logger.info("风险分析完成")
        except Exception as e:
            logger.error(f"风险分析异常: {str(e)}")
            self.errors.append(f"风险分析异常: {str(e)}")

    def financial_analysis_parallel(self):
        """并行执行财务分析 (高性能核心)"""
        logger.info(f"开始并行财务分析 (Workers: {MAX_WORKERS})")
        
        tasks = {
            'dupont': self.dupont_analysis,
            'profitability': self.profitability_analysis,
            'valuation': self.valuation_analysis,
            'cashflow': self.cashflow_analysis
        }
        
        with ThreadPoolExecutor(max_workers=MAX_WORKERS) as executor:
            # 提交所有任务
            future_to_name = {executor.submit(func): name for name, func in tasks.items()}
            
            for future in as_completed(future_to_name):
                name = future_to_name[future]
                try:
                    future.result() # 如果函数中有异常，这里会抛出
                    logger.info(f"模块完成: {name}")
                except Exception as e:
                    logger.error(f"模块失败 {name}: {str(e)}")
                    logger.error(traceback.format_exc())
                    with self.lock:
                        self.errors.append(f"分析模块 {name} 失败: {str(e)}")

    def financial_analysis_serial(self):
        """串行执行财务分析 (备用模式)"""
        logger.info("开始串行财务分析")
        try:
            self.dupont_analysis()
            self.profitability_analysis()
            self.valuation_analysis()
            self.cashflow_analysis()
        except Exception as e:
            self.errors.append(f"财务分析失败: {str(e)}")

    # ==========================================
    # 具体分析子模块 (增加线程安全写入)
    # ==========================================

    def dupont_analysis(self):
        roe3_df, roe3_report = analyze_dupont_roe_3factor(self.stock_code)
        roe5_df, roe5_report = analyze_dupont_roe_5factor(self.stock_code)
        
        # 线程安全写入
        with self.lock:
            self.results['financial_analysis']['dupont']['3factor'] = {'data': roe3_df, 'report': roe3_report}
            self.results['financial_analysis']['dupont']['5factor'] = {'data': roe5_df, 'report': roe5_report}

    def profitability_analysis(self):
        # 依次计算各项指标
        gross = analyze_gross_margin(self.stock_code)
        net = analyze_net_margin(self.stock_code)
        roe = analyze_roe(self.stock_code)
        roa = analyze_roa(self.stock_code)
        roic = analyze_roic(self.stock_code)
        
        # 批量线程安全写入
        with self.lock:
            target = self.results['financial_analysis']['profitability']
            target['gross_margin'] = {'data': gross[0], 'report': gross[1]}
            target['net_margin'] = {'data': net[0], 'report': net[1]}
            target['roe'] = {'data': roe[0], 'report': roe[1]}
            target['roa'] = {'data': roa[0], 'report': roa[1]}
            target['roic'] = {'data': roic[0], 'report': roic[1]}

    def valuation_analysis(self):
        pe = analyze_pe_ratio(self.stock_code)
        pb = analyze_pb_ratio(self.stock_code)
        ps = analyze_ps_ratio(self.stock_code)
        peg = analyze_peg_ratio(self.stock_code)
        evebitda = analyze_ev_ebitda(self.stock_code)
        
        with self.lock:
            target = self.results['financial_analysis']['valuation']
            target['pe'] = {'data': pe[0], 'report': pe[1]}
            target['pb'] = {'data': pb[0], 'report': pb[1]}
            target['ps'] = {'data': ps[0], 'report': ps[1]}
            target['peg'] = {'data': peg[0], 'report': peg[1]}
            target['ev_ebitda'] = {'data': evebitda[0], 'report': evebitda[1]}

    def cashflow_analysis(self):
        opcf = analyze_operating_cashflow_quality(self.stock_code)
        fcf = analyze_free_cashflow(self.stock_code)
        adeq = analyze_cashflow_adequacy(self.stock_code)
        cycle = analyze_cash_conversion_cycle(self.stock_code)
        
        with self.lock:
            target = self.results['financial_analysis']['cashflow']
            target['operating_quality'] = {'data': opcf[0], 'report': opcf[1]}
            target['free_cashflow'] = {'data': fcf[0], 'report': fcf[1]}
            target['adequacy'] = {'data': adeq[0], 'report': adeq[1]}
            target['conversion_cycle'] = {'data': cycle[0], 'report': cycle[1]}

    def generate_report(self):
        """生成报告"""
        logger.info("开始生成报告...")
        try:
            report_dir = f"{REPORT_DIR}/{self.stock_code}"
            os.makedirs(report_dir, exist_ok=True)
            
            # 1. 生成主报告
            main_report_content = self._build_main_report()
            with open(os.path.join(report_dir, f"{self.stock_code}_full_report.txt"), 'w', encoding='utf-8') as f:
                f.write(main_report_content)
            
            # 2. 生成子模块报告
            self._generate_module_reports(report_dir)
            logger.info(f"报告生成完毕: {report_dir}")
            
        except Exception as e:
            logger.error(f"报告生成失败: {str(e)}")
            self.errors.append(f"报告生成失败: {str(e)}")

    def _build_main_report(self):
        """在内存中构建主报告内容"""
        lines = []
        lines.append("=" * 100)
        lines.append(f"股票财务分析完整报告")
        lines.append(f"股票代码: {self.stock_code}")
        lines.append(f"分析时间: {datetime.now()}")
        lines.append("=" * 100 + "\n")
        
        # 摘要信息
        lines.append("【执行摘要】")
        lines.append("-" * 50)
        lines.append(f"错误数量: {len(self.errors)}")
        if self.errors:
            for e in self.errors:
                lines.append(f"  - {e}")
        lines.append("\n")
        
        # 简单的结果预览（这里仅示例部分关键指标）
        lines.append("【关键指标预览】")
        lines.append("-" * 50)
        
        # 安全地访问嵌套字典，防止KeyError
        try:
            if 'altman_zscore' in self.results['risk_analysis']:
                df = self.results['risk_analysis']['altman_zscore']['data']
                if df is not None and not df.empty:
                    lines.append(f"最新 Altman Z-Score: {df.iloc[-1]['Z-Score']:.4f}")
            
            dupont = self.results['financial_analysis']['dupont']
            if '5factor' in dupont and dupont['5factor']['data'] is not None:
                df = dupont['5factor']['data']
                if not df.empty and 'ROE (%)' in df.columns:
                    lines.append(f"最新 ROE (5因子): {df.iloc[-1]['ROE (%)']:.2f}%")
        except Exception as e:
            lines.append(f"读取摘要数据时出错: {str(e)}")
            
        return "\n".join(lines)

    def _generate_module_reports(self, report_dir):
        """生成各分项报告文件"""
        # 定义文件名和数据源的映射
        modules = [
            ("risk", self.results['risk_analysis']),
            ("dupont", self.results['financial_analysis']['dupont']),
            ("profitability", self.results['financial_analysis']['profitability']),
            ("valuation", self.results['financial_analysis']['valuation']),
            ("cashflow", self.results['financial_analysis']['cashflow']),
        ]
        
        for name, data_dict in modules:
            file_path = os.path.join(report_dir, f"{self.stock_code}_{name}_report.txt")
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(f"=== {name.upper()} 分析报告 ===\n\n")
                for key, val in data_dict.items():
                    # 兼容不同结构的存储（benford是直接存dict，其他是{'report': ...}）
                    if isinstance(val, dict) and 'report' in val:
                        f.write(f"--- {key} ---\n")
                        f.write(str(val['report']) + "\n\n")
                    elif isinstance(val, dict):
                        f.write(f"--- {key} ---\n")
                        for sub_k, sub_v in val.items():
                            f.write(f"{sub_k}: {sub_v}\n")
                        f.write("\n")

def main():
    import argparse
    parser = argparse.ArgumentParser(description='股票财务分析工作流 (高性能版)')
    parser.add_argument('stock_code', type=str, help='股票代码')
    parser.add_argument('--start', type=str, default='20200101', help='开始日期 YYYYMMDD')
    parser.add_argument('--end', type=str, default=None, help='结束日期 YYYYMMDD')
    parser.add_argument('--serial', action='store_true', help='强制使用串行模式')
    
    args = parser.parse_args()
    
    # 命令行覆盖配置
    if args.serial:
        global ENABLE_PARALLEL
        ENABLE_PARALLEL = False
    
    workflow = StockAnalysisWorkflow(
        stock_code=args.stock_code,
        start_date=args.start,
        end_date=args.end
    )
    
    if workflow.run():
        sys.exit(0)
    else:
        sys.exit(1)

if __name__ == "__main__":
    # 清除缓存
    if CACHE_CLEAR_ON_START and ENABLE_CACHE:
        clear_data_cache()
    
    if len(sys.argv) > 1:
        main()
    else:
        # 默认执行模式
        logger.info("使用默认配置执行...")
        wf = StockAnalysisWorkflow(STOCK_CODE, START_DATE, END_DATE, silent=SILENT_MODE)
        wf.run()
