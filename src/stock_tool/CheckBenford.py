'''
Benford's Law is a powerful tool for auditing financial statements, 
as fraudulent data often deviates significantly from the expected distribution of leading digits.
'''
import pandas as pd
import numpy as np

# define function to check Benford's Law
def check_benford(data):
    '''
    本福特数据检查
    参数:
        data: 待检查的数据，必须是数值型
    返回:
        digit_counts: 每个前导数字的实际出现次数
        expected_counts: 根据本福特定律预期的前导数字出现次数
    Demo:
    check_benford(data)
    '''
    # 将输入统一为 Series，避免 DataFrame 没有 str 属性
    if isinstance(data, pd.DataFrame):
        # 若传入的是 DataFrame，默认取第一列
        data = data.iloc[:, 0]
    data = pd.Series(data)

    # define Benford's Law distribution
    benford_dist = np.log10(1 + 1 / np.arange(1, 10))
    # extract leading digits
    leading_digits = data.astype(str).str[0]
    # Benford check data clear: delete "-","+"
    leading_digits = leading_digits[leading_digits != "-"]
    leading_digits = leading_digits[leading_digits != "+"]
    # count occurrences of each leading digit
    digit_counts = leading_digits.value_counts().sort_index()
    # calculate expected counts based on Benford's Law
    expected_counts = len(data) * benford_dist
    # plot actual vs. expected counts
    print("Actual vs Expected Counts (Benford's Law)")
    print("Digit | Actual | Expected | Diff")
    print("------|--------|----------|------")
    for d in range(1, 10):
        a = digit_counts.get(str(d), 0)
        e = int(expected_counts[d-1])
        print(f"  {d}   | {a:6d} | {e:8d} | {a-e:+5d}")
    else:
        return digit_counts, expected_counts