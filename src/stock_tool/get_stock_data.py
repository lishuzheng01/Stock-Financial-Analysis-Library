import akshare as ak
import pandas as pd

def get_stock_data(stock="600519", start="20200101", end="20240101"):
    """
    获取股票数据并处理为 Backtrader 格式
    参数:
        stock: 股票代码
        start: 开始日期 (YYYYMMDD)
        end: 结束日期 (YYYYMMDD)
    返回:
        df = df[['open', 'high', 'low', 'close', 'volume']].astype(float)
    Demo:
    df = get_stock_data(stock="600519", start="20200101", end="20240101")
    """

    # 1. 获取 AKShare 数据
    try:
        df = ak.stock_zh_a_hist(symbol=stock, period="daily", start_date=start, end_date=end, adjust="qfq")
    except KeyError:
        # 某些新股可能没有数据，做个简单容错
        print(f"Error: 无法获取股票 {stock} 的数据")
        return pd.DataFrame()

    # 2. 【关键修复】使用 rename 映射列名，而不是强制覆盖
    # 只要源数据里有这些中文列名，就会被正确识别，多余的列会自动忽略
    rename_dict = {
        '日期': 'date',
        '开盘': 'open',
        '收盘': 'close',
        '最高': 'high',
        '最低': 'low',
        '成交量': 'volume',
        # 以下列可选，Backtrader 默认只需要上面 6 个
        '成交额': 'turnover',
        '换手率': 'turnover_rate'
    }
    df.rename(columns=rename_dict, inplace=True)
    
    # 3. 处理时间索引
    df.index = pd.to_datetime(df['date'])
    
    # 4. 确保数值类型正确
    # 只保留 Backtrader 需要的列，避免其他列干扰
    df = df[['open', 'high', 'low', 'close', 'volume']].astype(float)
    
    return df