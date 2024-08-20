import sqlite3
import pandas as pd

# 设置 pandas 选项以显示所有行
pd.set_option('display.max_rows', None)


def fetch_query_from_db(db_path, query, params):
    """通用数据库查询函数，用于执行SQL查询并返回结果"""
    with sqlite3.connect(db_path) as conn:
        return pd.read_sql_query(query, conn, params=params)


def get_rate_from_db(db_path, product_id, age, gender, payment_term):
    """获取保险费率"""
    query = '''
    SELECT rate 
    FROM insurance_rates
    WHERE product_id = ?
    AND age = ?
    AND gender = ?
    AND payment_term = ?
    '''
    rate = fetch_query_from_db(db_path, query,
                               (product_id, age, gender, payment_term))
    return rate.iloc[0, 0]


def get_cv_table_from_db(db_path, product_id, age, gender, payment_term):
    """获取CV表中的数据"""
    query = '''
    SELECT year, value 
    FROM insurance_cv
    WHERE product_id = ?
    AND age = ?
    AND gender = ?
    AND payment_term = ?
    '''
    cv_table = fetch_query_from_db(db_path, query,
                                   (product_id, age, gender, payment_term))
    cv_table.set_index('year', inplace=True)
    return cv_table


def calculate_insurance_values(start_age, start_withdrawal_age,
                               withdrawal_amount, initial_base_amount,
                               cv_table):
    """计算保险的每年基本保额、有效保额和现金价值"""
    results = []
    current_base_amount = initial_base_amount
    actual_withdrawal_amount = 0

    for age in range(start_age + 1, len(cv_table) + start_age + 1):
        year = age - start_age

        # 如果已经达到领取年龄，开始领取
        if age >= start_withdrawal_age:
            current_cash_value = round(
                current_base_amount * cv_table.loc[year, 'value'] / 1000, 2)

            if withdrawal_amount < current_cash_value:
                reduction_ratio = withdrawal_amount / current_cash_value
                actual_withdrawal_amount = withdrawal_amount
            else:
                actual_withdrawal_amount = current_cash_value
                reduction_ratio = 1

            # 计算减额后的基本保额
            current_base_amount = round(
                current_base_amount * (1 - reduction_ratio), 0)

        # 计算当前年度的现金价值
        current_cash_value = round(
            current_base_amount * cv_table.loc[year, 'value'] / 1000, 2)

        # 有效保额等于当前的基本保额乘年度的复利
        effective_base_amount = round(current_base_amount * 1.03**(year - 1),
                                      2)
        # 存储每年的数据
        results.append({
            "保单年度": year,
            "年龄": age,
            "基本保额": current_base_amount,
            "有效保额": effective_base_amount,
            "现金价值": current_cash_value,
            "实际减保金额": round(actual_withdrawal_amount, 2),
        })

    return pd.DataFrame(results)


def main():
    # 数据库路径
    db_path = 'insurance.db'

    # 示例参数
    product_id = 1
    start_age = 26
    gender = 'F'
    payment_term = 5
    initial_premium = 10000
    start_withdrawal_age = 50
    withdrawal_amount = 8758.2

    # 从数据表中计算基本保额
    rate = get_rate_from_db(db_path, product_id, start_age, gender,
                            payment_term)
    initial_base_amount = rate / 1000 * initial_premium

    # 从数据库中提取CV表数据
    cv_table = get_cv_table_from_db(db_path, product_id, start_age, gender,
                                    payment_term)

    # 计算结果
    results_df = calculate_insurance_values(start_age, start_withdrawal_age,
                                            withdrawal_amount,
                                            initial_base_amount, cv_table)


if __name__ == '__main__':
    main()
