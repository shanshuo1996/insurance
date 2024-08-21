from flask import Flask, request, render_template
import sqlite3
import pandas as pd
from calculateValue import get_cv_table_from_db, get_rate_from_db, calculate_insurance_values

app = Flask(__name__)


# 将之前优化的代码整合到Flask应用中
def fetch_query_from_db(db_path, query, params):
    with sqlite3.connect(db_path) as conn:
        return pd.read_sql_query(query, conn, params=params)


@app.route('/', methods=['GET', 'POST'])
def index():
    if request.method == 'POST':
        start_age = int(request.form['start_age'])
        gender = request.form['gender']
        payment_term = int(request.form['payment_term'])
        initial_premium = float(request.form['initial_premium'])
        start_withdrawal_age = int(request.form['start_withdrawal_age'])
        withdrawal_amount = float(request.form['withdrawal_amount'])

        db_path = 'insurance.db'
        product_id = 1  # 假设使用的产品ID
        rate = get_rate_from_db(db_path, product_id, start_age, gender,
                                payment_term)
        initial_base_amount = rate / 1000 * initial_premium
        cv_table = get_cv_table_from_db(db_path, product_id, start_age, gender,
                                        payment_term)
        results_df = calculate_insurance_values(start_age,
                                                start_withdrawal_age,
                                                withdrawal_amount,
                                                initial_base_amount, cv_table)

        # 渲染模板并传递表单数据和计算结果
        return render_template('index.html',
                               start_age=start_age,
                               gender=gender,
                               payment_term=payment_term,
                               initial_premium=initial_premium,
                               start_withdrawal_age=start_withdrawal_age,
                               withdrawal_amount=withdrawal_amount,
                               tables=results_df.to_html(classes='data',
                                                         header="true"))

    return render_template('index.html')


if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)
