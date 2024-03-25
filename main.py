from flask import Flask, jsonify, render_template
from google.cloud import bigquery

app = Flask(__name__)
client = bigquery.Client(project='assignment1-2-418206', location='australia-southeast1')

@app.route('/top-time-slots', methods=['GET'])
def get_top_time_slots():
    QUERY = """
    SELECT 
        time_ref, 
        SUM(SAFE_CAST(value AS FLOAT64)) AS trade_value
    FROM 
        `assignment1-2-418206.gsquarterlySeptember20.gsquarterlySept20`
    GROUP BY 
        time_ref
    ORDER BY 
        trade_value DESC
    LIMIT 
        10;
    """
    query_job = client.query(QUERY)
    rows = query_job.result()
    results = [dict(row) for row in rows]
    return jsonify(results)

@app.route('/top-trade-deficits', methods=['GET'])
def get_top_trade_deficits():
    QUERY = """
    SELECT 
        cc.country_label,
        gq.product_type,
        SUM(
            CASE 
                WHEN gq.account = 'Imports' THEN SAFE_CAST(gq.value AS FLOAT64)
                WHEN gq.account = 'Exports' THEN -SAFE_CAST(gq.value AS FLOAT64)
                ELSE 0 
            END
        ) AS trade_deficit_value,
        gq.status
    FROM 
        `assignment1-2-418206.gsquarterlySeptember20.gsquarterlySept20` AS gq
    JOIN 
        `assignment1-2-418206.country_classification.country_class` AS cc
    ON 
        gq.country_code = cc.country_code
    WHERE 
        gq.time_ref BETWEEN '201301' AND '201512'
        AND gq.status = 'F'
    GROUP BY 
        cc.country_label, gq.product_type, gq.status
    ORDER BY 
        trade_deficit_value DESC
    LIMIT 
        40;
    """
    query_job = client.query(QUERY)
    rows = query_job.result()
    results = [
        {
            'country_label': row.country_label, 
            'product_type': row.product_type, 
            'trade_deficit_value': row.trade_deficit_value, 
            'status': row.status
        } for row in rows
    ]
    return jsonify(results)


@app.route('/')
def index():
    return render_template('index.html')

if __name__ == '__main__':
    app.run(debug=True)
