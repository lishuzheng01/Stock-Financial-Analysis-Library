#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
股票财务分析完整工作流
完整执行所有功能模块，包括数据获取、风险分析和财务分析
"""

# ==========================================
# 配置区 (Configuration)
# ==========================================

# 工作流配置
STOCK_CODE = "600519"  # 股票代码
START_DATE = "20200101"  # 开始日期，格式：YYYYMMDD
END_DATE = None  # 结束日期，格式：YYYYMMDD，默认为当前日期
SILENT_MODE = False  # 是否静默模式，不输出详细信息

# 日志配置
LOG_LEVEL = "INFO"  # 日志级别：DEBUG, INFO, WARNING, ERROR
LOG_FILE = "stock_analysis_workflow.log"  # 日志文件名

# 缓存配置
ENABLE_CACHE = True  # 是否启用数据缓存
CACHE_CLEAR_ON_START = True  # 启动时是否清除缓存

# 报告配置
REPORT_DIR = "reports"  # 报告输出目录
GENERATE_MODULE_REPORTS = True  # 是否生成各模块详细报告

# ==========================================

import logging
import pandas as pd
import os
import sys
import traceback
from datetime import datetime
from functools import wraps

# 导入stock_tool包中的所有函数
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

# 全局数据缓存，用于存储已获取的数据
global_data_cache = {}

# 替换原始的get_report_data函数，使其总是返回缓存的数据
def get_report_data(stock, symbol, transpose=True, source='auto'):
    """自定义get_report_data函数，总是返回缓存的数据，避免重复下载"""
    if not ENABLE_CACHE:
        logger.info(f"缓存已禁用，直接调用原始get_report_data获取数据: {stock}_{symbol}")
        return original_get_report_data(stock, symbol, transpose, source)
    
    cache_key = f"{stock}_{symbol}"
    
    # 检查全局缓存中是否有数据
    if cache_key in global_data_cache:
        logger.info(f"从全局缓存返回数据: {cache_key}")
        return global_data_cache[cache_key]
    
    # 缓存中没有数据，调用原始函数获取数据
    logger.info(f"调用原始get_report_data获取数据: {cache_key}")
    result = original_get_report_data(stock, symbol, transpose, source)
    
    # 将结果存入缓存
    global_data_cache[cache_key] = result
    logger.info(f"数据已存入全局缓存: {cache_key}")
    return result

def clear_data_cache():
    """清除全局数据缓存"""
    global global_data_cache
    global_data_cache.clear()
    logger.info("全局数据缓存已清除")

# 配置日志系统
log_level = getattr(logging, LOG_LEVEL.upper(), logging.INFO)
logging.basicConfig(
    level=log_level,
    format='%(asctime)s - %(name)s - %(funcName)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(LOG_FILE, encoding='utf-8'),
        logging.StreamHandler(sys.stdout)
    ]
)

logger = logging.getLogger('StockAnalysisWorkflow')


class StockAnalysisWorkflow:
    """股票财务分析工作流类
    
    按顺序执行所有功能模块，处理依赖关系，添加日志记录和错误处理
    """
    
    def __init__(self, stock_code, start_date='20200101', end_date=None, silent=False):
        """初始化工作流
        
        参数：
        stock_code: 股票代码
        start_date: 开始日期，格式为YYYYMMDD
        end_date: 结束日期，格式为YYYYMMDD，默认为当前日期
        silent: 是否静默模式，默认为False
        """
        self.stock_code = stock_code
        self.start_date = start_date
        self.end_date = end_date or datetime.now().strftime('%Y%m%d')
        self.silent = silent
        
        # 初始化结果存储字典
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
        
        # 初始化错误记录
        self.errors = []
        
        logger.info(f"初始化股票分析工作流: {stock_code}, 日期范围: {start_date} - {end_date}")
    
    def run(self):
        """执行完整工作流
        
        返回：
        bool: 工作流执行是否成功
        """
        try:
            logger.info("开始执行完整工作流")
            
            # 1. 获取数据
            self.get_data()
            
            # 2. 风险分析
            self.risk_analysis()
            
            # 3. 财务分析
            self.financial_analysis()
            
            # 4. 生成报告
            self.generate_report()
            
            logger.info("完整工作流执行成功")
            return True
        except Exception as e:
            logger.error(f"工作流执行失败: {str(e)}")
            logger.error(traceback.format_exc())
            self.errors.append(f"工作流执行失败: {str(e)}")
            return False
    
    def get_data(self, use_cache=True, force_update=False):
        """获取股票数据和财务报表数据，确保只获取一次
        
        依赖关系：无，为第一步
        
        参数：
        use_cache: 是否使用缓存
        force_update: 是否强制更新缓存
        """
        # 检查数据是否已经获取，如果是则跳过
        if self.results['data'].get('price') is not None and not force_update:
            logger.info("数据已经获取，跳过重复下载")
            return
            
        # 检查是否有缓存数据
        cache_dir = f"cache/{self.stock_code}"
        os.makedirs(cache_dir, exist_ok=True)
        
        # 定义缓存文件路径
        price_cache_path = os.path.join(cache_dir, f"price_{self.start_date}_{self.end_date}.csv")
        balance_cache_path = os.path.join(cache_dir, "balance_sheet.csv")
        income_cache_path = os.path.join(cache_dir, "income_statement.csv")
        cashflow_cache_path = os.path.join(cache_dir, "cashflow.csv")
        
        logger.info("开始获取数据")
        
        try:
            # 获取股票价格数据
            logger.info(f"获取股票 {self.stock_code} 的价格数据")
            
            # 检查价格数据缓存
            if use_cache and os.path.exists(price_cache_path) and not force_update:
                logger.info(f"从缓存加载股票价格数据: {price_cache_path}")
                price_data = pd.read_csv(price_cache_path, index_col=0, parse_dates=True)
            else:
                # 从API获取数据
                price_data = get_stock_data(
                    self.stock_code, 
                    self.start_date, 
                    self.end_date, 
                    source='auto'
                )
                # 保存到缓存
                price_data.to_csv(price_cache_path)
                logger.info(f"股票价格数据已保存到缓存: {price_cache_path}")
            
            self.results['data']['price'] = price_data
            logger.info(f"成功获取股票价格数据，共 {len(price_data)} 条记录")
            
            # 获取财务报表数据
            report_types = ["资产负债表", "利润表", "现金流量表"]
            cache_paths = {
                "资产负债表": balance_cache_path,
                "利润表": income_cache_path,
                "现金流量表": cashflow_cache_path
            }
            
            for report_type in report_types:
                logger.info(f"获取 {report_type} 数据")
                cache_path = cache_paths[report_type]
                
                if use_cache and os.path.exists(cache_path) and not force_update:
                    logger.info(f"从缓存加载 {report_type} 数据: {cache_path}")
                    report_data = pd.read_csv(cache_path, index_col=0)
                else:
                    # 从API获取数据
                    report_data = get_report_data(
                        self.stock_code, 
                        report_type, 
                        transpose=True,
                        source='auto'
                    )
                    # 保存到缓存
                    report_data.to_csv(cache_path)
                    logger.info(f"{report_type} 数据已保存到缓存: {cache_path}")
                
                self.results['data'][report_type] = report_data
                logger.info(f"成功获取 {report_type} 数据，共 {len(report_data)} 条记录")
                
            logger.info("数据获取完成")
        except Exception as e:
            logger.error(f"数据获取失败: {str(e)}")
            logger.error(traceback.format_exc())
            self.errors.append(f"数据获取失败: {str(e)}")
            raise
    
    def risk_analysis(self):
        """执行风险分析
        
        依赖关系：需要先获取数据
        """
        logger.info("开始执行风险分析")
        
        try:
            # 将已获取的数据存入全局缓存，供分析函数使用
            logger.info("将已获取的数据存入全局缓存")
            for report_type in ["资产负债表", "利润表", "现金流量表"]:
                if report_type in self.results['data']:
                    cache_key = f"{self.stock_code}_{report_type}"
                    global_data_cache[cache_key] = self.results['data'][report_type]
                    logger.info(f"已将 {report_type} 存入全局缓存: {cache_key}")
            
            # Altman Z-Score 分析
            logger.info("执行 Altman Z-Score 分析")
            zscore_df, zscore_report = analyze_altman_zscore(self.stock_code)
            self.results['risk_analysis']['altman_zscore'] = {
                'data': zscore_df,
                'report': zscore_report
            }
            logger.info("Altman Z-Score 分析完成")
            
            # Beneish M-Score 分析
            logger.info("执行 Beneish M-Score 分析")
            mscore_df, mscore_report = analyze_beneish_mscore(
                self.stock_code, 
                print_output=not self.silent
            )
            self.results['risk_analysis']['beneish_mscore'] = {
                'data': mscore_df,
                'report': mscore_report
            }
            logger.info("Beneish M-Score 分析完成")
            
            # Benford's Law 验证
            logger.info("执行 Benford's Law 验证")
            # 对所有财务报表进行验证
            benford_results = {}
            for report_type in ["资产负债表", "利润表", "现金流量表"]:
                try:
                    benford_result = check_benford(self.stock_code, report_type)
                    benford_results[report_type] = benford_result
                    logger.info(f"{report_type} Benford's Law 验证完成")
                except Exception as e:
                    logger.warning(f"{report_type} Benford's Law 验证失败: {str(e)}")
                    benford_results[report_type] = f"验证失败: {str(e)}"
            
            self.results['risk_analysis']['benford'] = benford_results
            logger.info("风险分析完成")
        except Exception as e:
            logger.error(f"风险分析失败: {str(e)}")
            logger.error(traceback.format_exc())
            self.errors.append(f"风险分析失败: {str(e)}")
            raise
    
    def financial_analysis(self):
        """执行财务分析
        
        依赖关系：需要先获取数据
        """
        logger.info("开始执行财务分析")
        
        try:
            # 确保数据已存入全局缓存
            logger.info("检查并更新全局数据缓存")
            for report_type in ["资产负债表", "利润表", "现金流量表"]:
                if report_type in self.results['data']:
                    cache_key = f"{self.stock_code}_{report_type}"
                    global_data_cache[cache_key] = self.results['data'][report_type]
                    logger.info(f"已将 {report_type} 存入全局缓存: {cache_key}")
            
            # 1. 杜邦分析
            self.dupont_analysis()
            
            # 2. 盈利能力分析
            self.profitability_analysis()
            
            # 3. 估值分析
            self.valuation_analysis()
            
            # 4. 现金流分析
            self.cashflow_analysis()
            
            logger.info("财务分析完成")
        except Exception as e:
            logger.error(f"财务分析失败: {str(e)}")
            logger.error(traceback.format_exc())
            self.errors.append(f"财务分析失败: {str(e)}")
            raise
    
    def dupont_analysis(self):
        """执行杜邦分析
        """
        logger.info("执行杜邦分析")
        
        try:
            # 3因素杜邦分析
            logger.info("执行3因素杜邦分析")
            roe3_df, roe3_report = analyze_dupont_roe_3factor(self.stock_code)
            self.results['financial_analysis']['dupont']['3factor'] = {
                'data': roe3_df,
                'report': roe3_report
            }
            
            # 5因素杜邦分析
            logger.info("执行5因素杜邦分析")
            roe5_df, roe5_report = analyze_dupont_roe_5factor(self.stock_code)
            self.results['financial_analysis']['dupont']['5factor'] = {
                'data': roe5_df,
                'report': roe5_report
            }
            
            logger.info("杜邦分析完成")
        except Exception as e:
            logger.error(f"杜邦分析失败: {str(e)}")
            logger.error(traceback.format_exc())
            self.errors.append(f"杜邦分析失败: {str(e)}")
            raise
    
    def profitability_analysis(self):
        """执行盈利能力分析
        """
        logger.info("执行盈利能力分析")
        
        try:
            # 毛利率分析
            logger.info("执行毛利率分析")
            gross_df, gross_report = analyze_gross_margin(self.stock_code)
            self.results['financial_analysis']['profitability']['gross_margin'] = {
                'data': gross_df,
                'report': gross_report
            }
            
            # 净利率分析
            logger.info("执行净利率分析")
            net_df, net_report = analyze_net_margin(self.stock_code)
            self.results['financial_analysis']['profitability']['net_margin'] = {
                'data': net_df,
                'report': net_report
            }
            
            # ROE分析
            logger.info("执行ROE分析")
            roe_df, roe_report = analyze_roe(self.stock_code)
            self.results['financial_analysis']['profitability']['roe'] = {
                'data': roe_df,
                'report': roe_report
            }
            
            # ROA分析
            logger.info("执行ROA分析")
            roa_df, roa_report = analyze_roa(self.stock_code)
            self.results['financial_analysis']['profitability']['roa'] = {
                'data': roa_df,
                'report': roa_report
            }
            
            # ROIC分析
            logger.info("执行ROIC分析")
            roic_df, roic_report = analyze_roic(self.stock_code)
            self.results['financial_analysis']['profitability']['roic'] = {
                'data': roic_df,
                'report': roic_report
            }
            
            logger.info("盈利能力分析完成")
        except Exception as e:
            logger.error(f"盈利能力分析失败: {str(e)}")
            logger.error(traceback.format_exc())
            self.errors.append(f"盈利能力分析失败: {str(e)}")
            raise
    
    def valuation_analysis(self):
        """执行估值分析
        """
        logger.info("执行估值分析")
        
        try:
            # PE市盈率分析
            logger.info("执行PE市盈率分析")
            pe_df, pe_report = analyze_pe_ratio(self.stock_code)
            self.results['financial_analysis']['valuation']['pe'] = {
                'data': pe_df,
                'report': pe_report
            }
            
            # PB市净率分析
            logger.info("执行PB市净率分析")
            pb_df, pb_report = analyze_pb_ratio(self.stock_code)
            self.results['financial_analysis']['valuation']['pb'] = {
                'data': pb_df,
                'report': pb_report
            }
            
            # PS市销率分析
            logger.info("执行PS市销率分析")
            ps_df, ps_report = analyze_ps_ratio(self.stock_code)
            self.results['financial_analysis']['valuation']['ps'] = {
                'data': ps_df,
                'report': ps_report
            }
            
            # PEG分析
            logger.info("执行PEG分析")
            peg_df, peg_report = analyze_peg_ratio(self.stock_code)
            self.results['financial_analysis']['valuation']['peg'] = {
                'data': peg_df,
                'report': peg_report
            }
            
            # EV/EBITDA分析
            logger.info("执行EV/EBITDA分析")
            evebitda_df, evebitda_report = analyze_ev_ebitda(self.stock_code)
            self.results['financial_analysis']['valuation']['ev_ebitda'] = {
                'data': evebitda_df,
                'report': evebitda_report
            }
            
            logger.info("估值分析完成")
        except Exception as e:
            logger.error(f"估值分析失败: {str(e)}")
            logger.error(traceback.format_exc())
            self.errors.append(f"估值分析失败: {str(e)}")
            raise
    
    def cashflow_analysis(self):
        """执行现金流分析
        """
        logger.info("执行现金流分析")
        
        try:
            # 经营现金流质量分析
            logger.info("执行经营现金流质量分析")
            opcf_df, opcf_report = analyze_operating_cashflow_quality(self.stock_code)
            self.results['financial_analysis']['cashflow']['operating_quality'] = {
                'data': opcf_df,
                'report': opcf_report
            }
            
            # 自由现金流分析
            logger.info("执行自由现金流分析")
            fcf_df, fcf_report = analyze_free_cashflow(self.stock_code)
            self.results['financial_analysis']['cashflow']['free_cashflow'] = {
                'data': fcf_df,
                'report': fcf_report
            }
            
            # 现金流充足率分析
            logger.info("执行现金流充足率分析")
            adequacy_df, adequacy_report = analyze_cashflow_adequacy(self.stock_code)
            self.results['financial_analysis']['cashflow']['adequacy'] = {
                'data': adequacy_df,
                'report': adequacy_report
            }
            
            # 现金转换周期分析
            logger.info("执行现金转换周期分析")
            cycle_df, cycle_report = analyze_cash_conversion_cycle(self.stock_code)
            self.results['financial_analysis']['cashflow']['conversion_cycle'] = {
                'data': cycle_df,
                'report': cycle_report
            }
            
            logger.info("现金流分析完成")
        except Exception as e:
            logger.error(f"现金流分析失败: {str(e)}")
            logger.error(traceback.format_exc())
            self.errors.append(f"现金流分析失败: {str(e)}")
            raise
    
    def generate_report(self):
        """生成完整分析报告
        
        依赖关系：需要完成数据获取、风险分析和财务分析
        """
        logger.info("开始生成分析报告")
        
        try:
            # 创建报告目录
            report_dir = f"reports/{self.stock_code}"
            os.makedirs(report_dir, exist_ok=True)
            
            # 生成主报告
            main_report_path = os.path.join(report_dir, f"{self.stock_code}_full_report.txt")
            with open(main_report_path, 'w', encoding='utf-8') as f:
                # 报告标题
                f.write("=" * 100 + "\n")
                f.write(f"股票财务分析完整报告\n")
                f.write(f"股票代码: {self.stock_code}\n")
                f.write(f"分析日期: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
                f.write(f"数据日期范围: {self.start_date} - {self.end_date}\n")
                f.write("=" * 100 + "\n\n")
                
                # 1. 执行摘要
                f.write("【执行摘要】\n")
                f.write("-" * 50 + "\n")
                f.write(f"工作流执行状态: {'成功' if len(self.errors) == 0 else '失败'}\n")
                f.write(f"错误数量: {len(self.errors)}\n")
                if self.errors:
                    f.write("错误详情:\n")
                    for error in self.errors:
                        f.write(f"  - {error}\n")
                f.write("\n")
                
                # 2. 数据获取摘要
                f.write("【数据获取摘要】\n")
                f.write("-" * 50 + "\n")
                data_results = self.results['data']
                f.write(f"股票价格数据: {'已获取' if 'price' in data_results else '未获取'}\n")
                if 'price' in data_results:
                    f.write(f"  记录数: {len(data_results['price'])}\n")
                
                report_types = ["资产负债表", "利润表", "现金流量表"]
                for report_type in report_types:
                    f.write(f"{report_type}: {'已获取' if report_type in data_results else '未获取'}\n")
                    if report_type in data_results:
                        f.write(f"  记录数: {len(data_results[report_type])}\n")
                f.write("\n")
                
                # 3. 风险分析摘要
                f.write("【风险分析摘要】\n")
                f.write("-" * 50 + "\n")
                risk_results = self.results['risk_analysis']
                
                if 'altman_zscore' in risk_results and risk_results['altman_zscore']['data'] is not None:
                    latest_zscore = risk_results['altman_zscore']['data'].iloc[-1]['Z-Score']
                    f.write(f"Altman Z-Score: {latest_zscore:.4f}\n")
                
                if 'beneish_mscore' in risk_results and risk_results['beneish_mscore']['data'] is not None:
                    latest_mscore = risk_results['beneish_mscore']['data'].iloc[-1]['M-Score']
                    f.write(f"Beneish M-Score: {latest_mscore:.4f}\n")
                f.write("\n")
                
                # 4. 财务分析摘要
                f.write("【财务分析摘要】\n")
                f.write("-" * 50 + "\n")
                
                # 杜邦分析摘要
                dupont_results = self.results['financial_analysis']['dupont']
                if '5factor' in dupont_results and dupont_results['5factor']['data'] is not None and not dupont_results['5factor']['data'].empty:
                    data_df = dupont_results['5factor']['data']
                    if 'ROE (%)' in data_df.columns and len(data_df) > 0:
                        latest_roe = data_df.iloc[-1]['ROE (%)']
                        f.write(f"5因素杜邦分析ROE: {latest_roe:.4f}%\n")
                
                # 盈利能力摘要
                profit_results = self.results['financial_analysis']['profitability']
                if 'roe' in profit_results and profit_results['roe']['data'] is not None and not profit_results['roe']['data'].empty:
                    data_df = profit_results['roe']['data']
                    if 'ROE (%)' in data_df.columns and len(data_df) > 0:
                        latest_roe = data_df.iloc[-1]['ROE (%)']
                        f.write(f"ROE: {latest_roe:.4f}%\n")
                    
                    if 'roic' in profit_results and profit_results['roic']['data'] is not None and not profit_results['roic']['data'].empty:
                        roic_df = profit_results['roic']['data']
                        if 'ROIC (%)' in roic_df.columns and len(roic_df) > 0:
                            latest_roic = roic_df.iloc[-1]['ROIC (%)']
                            f.write(f"ROIC: {latest_roic:.4f}%\n")
                    
                    # 估值分析摘要
                    val_results = self.results['financial_analysis']['valuation']
                    if 'pe' in val_results and val_results['pe']['data'] is not None and not val_results['pe']['data'].empty:
                        pe_df = val_results['pe']['data']
                        if 'PE' in pe_df.columns and len(pe_df) > 0:
                            latest_pe = pe_df.iloc[-1]['PE']
                            f.write(f"PE: {latest_pe:.4f}\n")
                    
                    if 'pb' in val_results and val_results['pb']['data'] is not None and not val_results['pb']['data'].empty:
                        pb_df = val_results['pb']['data']
                        if 'PB' in pb_df.columns and len(pb_df) > 0:
                            latest_pb = pb_df.iloc[-1]['PB']
                            f.write(f"PB: {latest_pb:.4f}\n")
                    f.write("\n")
                    
                    # 5. 详细报告索引
                    f.write("【详细报告索引】\n")
                    f.write("-" * 50 + "\n")
                    f.write("各模块详细报告已分别保存到以下文件:\n")
                    f.write(f"1. 风险分析报告: {self.stock_code}_risk_report.txt\n")
                    f.write(f"2. 杜邦分析报告: {self.stock_code}_dupont_report.txt\n")
                    f.write(f"3. 盈利能力分析报告: {self.stock_code}_profitability_report.txt\n")
                    f.write(f"4. 估值分析报告: {self.stock_code}_valuation_report.txt\n")
                    f.write(f"5. 现金流分析报告: {self.stock_code}_cashflow_report.txt\n")
                    f.write("\n")
            
            # 6. 生成各模块详细报告
            self._generate_module_reports(report_dir)
            
            logger.info(f"主报告已生成: {main_report_path}")
            logger.info("分析报告生成完成")
        except Exception as e:
            logger.error(f"报告生成失败: {str(e)}")
            logger.error(traceback.format_exc())
            self.errors.append(f"报告生成失败: {str(e)}")
            raise
    
    def _generate_module_reports(self, report_dir):
        """生成各模块详细报告
        
        参数：
        report_dir: 报告目录路径
        """
        # 1. 风险分析报告
        risk_report_path = os.path.join(report_dir, f"{self.stock_code}_risk_report.txt")
        with open(risk_report_path, 'w', encoding='utf-8') as f:
            f.write("=" * 100 + "\n")
            f.write("风险分析详细报告\n")
            f.write("=" * 100 + "\n\n")
            
            # Altman Z-Score
            if 'altman_zscore' in self.results['risk_analysis']:
                f.write("【Altman Z-Score 分析】\n")
                f.write("-" * 50 + "\n")
                f.write(self.results['risk_analysis']['altman_zscore']['report'] + "\n\n")
            
            # Beneish M-Score
            if 'beneish_mscore' in self.results['risk_analysis']:
                f.write("【Beneish M-Score 分析】\n")
                f.write("-" * 50 + "\n")
                f.write(self.results['risk_analysis']['beneish_mscore']['report'] + "\n\n")
            
            # Benford's Law
            if 'benford' in self.results['risk_analysis']:
                f.write("【Benford's Law 验证】\n")
                f.write("-" * 50 + "\n")
                for report_type, result in self.results['risk_analysis']['benford'].items():
                    f.write(f"{report_type}:\n")
                    if isinstance(result, dict):
                        for key, value in result.items():
                            f.write(f"  {key}: {value}\n")
                    else:
                        f.write(f"  {result}\n")
                    f.write("\n")
        
        # 2. 杜邦分析报告
        dupont_report_path = os.path.join(report_dir, f"{self.stock_code}_dupont_report.txt")
        with open(dupont_report_path, 'w', encoding='utf-8') as f:
            f.write("=" * 100 + "\n")
            f.write("杜邦分析详细报告\n")
            f.write("=" * 100 + "\n\n")
            
            if '3factor' in self.results['financial_analysis']['dupont']:
                f.write("【3因素杜邦分析】\n")
                f.write("-" * 50 + "\n")
                f.write(self.results['financial_analysis']['dupont']['3factor']['report'] + "\n\n")
            
            if '5factor' in self.results['financial_analysis']['dupont']:
                f.write("【5因素杜邦分析】\n")
                f.write("-" * 50 + "\n")
                f.write(self.results['financial_analysis']['dupont']['5factor']['report'] + "\n\n")
        
        # 3. 盈利能力分析报告
        profit_report_path = os.path.join(report_dir, f"{self.stock_code}_profitability_report.txt")
        with open(profit_report_path, 'w', encoding='utf-8') as f:
            f.write("=" * 100 + "\n")
            f.write("盈利能力分析详细报告\n")
            f.write("=" * 100 + "\n\n")
            
            profitability = self.results['financial_analysis']['profitability']
            for name, result in profitability.items():
                f.write(f"【{name} 分析】\n")
                f.write("-" * 50 + "\n")
                f.write(result['report'] + "\n\n")
        
        # 4. 估值分析报告
        valuation_report_path = os.path.join(report_dir, f"{self.stock_code}_valuation_report.txt")
        with open(valuation_report_path, 'w', encoding='utf-8') as f:
            f.write("=" * 100 + "\n")
            f.write("估值分析详细报告\n")
            f.write("=" * 100 + "\n\n")
            
            valuation = self.results['financial_analysis']['valuation']
            for name, result in valuation.items():
                f.write(f"【{name} 分析】\n")
                f.write("-" * 50 + "\n")
                f.write(result['report'] + "\n\n")
        
        # 5. 现金流分析报告
        cashflow_report_path = os.path.join(report_dir, f"{self.stock_code}_cashflow_report.txt")
        with open(cashflow_report_path, 'w', encoding='utf-8') as f:
            f.write("=" * 100 + "\n")
            f.write("现金流分析详细报告\n")
            f.write("=" * 100 + "\n\n")
            
            cashflow = self.results['financial_analysis']['cashflow']
            for name, result in cashflow.items():
                f.write(f"【{name} 分析】\n")
                f.write("-" * 50 + "\n")
                f.write(result['report'] + "\n\n")


def main():
    """主函数，支持命令行参数
    
    命令行用法：
    python all_function_demo.py <stock_code> [start_date] [end_date] [--silent]
    """
    import argparse
    
    # 解析命令行参数
    parser = argparse.ArgumentParser(description='股票财务分析完整工作流')
    parser.add_argument('stock_code', type=str, help='股票代码')
    parser.add_argument('start_date', type=str, nargs='?', default='20200101', help='开始日期，格式为YYYYMMDD')
    parser.add_argument('end_date', type=str, nargs='?', default=None, help='结束日期，格式为YYYYMMDD')
    parser.add_argument('--silent', action='store_true', help='静默模式，不打印详细输出')
    
    args = parser.parse_args()
    
    # 执行工作流
    workflow = StockAnalysisWorkflow(
        stock_code=args.stock_code,
        start_date=args.start_date,
        end_date=args.end_date,
        silent=args.silent
    )
    
    success = workflow.run()
    
    # 退出状态码
    sys.exit(0 if success else 1)


# 测试函数，验证工作流在不同输入条件下的稳定性
def test_workflow():
    """测试工作流在不同输入条件下的稳定性"""
    logger.info("开始测试工作流")
    
    # 测试用例1：正常股票代码
    logger.info("测试用例1：正常股票代码 600519")
    workflow1 = StockAnalysisWorkflow("600519", "20200101", "20231231")
    success1 = workflow1.run()
    logger.info(f"测试用例1结果: {'成功' if success1 else '失败'}")
    
    # 测试用例2：较短日期范围
    logger.info("测试用例2：较短日期范围 20230101-20231231")
    workflow2 = StockAnalysisWorkflow("600519", "20230101", "20231231")
    success2 = workflow2.run()
    logger.info(f"测试用例2结果: {'成功' if success2 else '失败'}")
    
    # 测试用例3：静默模式
    logger.info("测试用例3：静默模式")
    workflow3 = StockAnalysisWorkflow("600519", "20230101", "20231231", silent=True)
    success3 = workflow3.run()
    logger.info(f"测试用例3结果: {'成功' if success3 else '失败'}")
    
    logger.info("工作流测试完成")
    
    # 返回测试结果
    return all([success1, success2, success3])


if __name__ == "__main__":
    # 清除缓存（如果配置了）
    if CACHE_CLEAR_ON_START and ENABLE_CACHE:
        clear_data_cache()
    
    # 如果直接运行脚本且没有命令行参数，使用配置的默认值
    if len(sys.argv) > 1:
        main()
    else:
        # 使用配置的默认值执行
        logger.info(f"使用配置的默认值执行工作流: 股票代码={STOCK_CODE}, 开始日期={START_DATE}, 结束日期={END_DATE}")
        workflow = StockAnalysisWorkflow(
            stock_code=STOCK_CODE,
            start_date=START_DATE,
            end_date=END_DATE,
            silent=SILENT_MODE
        )
        success = workflow.run()
        logger.info(f"工作流执行结果: {'成功' if success else '失败'}")
        sys.exit(0 if success else 1)
