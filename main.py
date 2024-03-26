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
        gq.product_type = 'Goods' 
        AND gq.status = 'F' 
        AND gq.time_ref BETWEEN '201301' AND '201512'
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

@app.route('/top-trade-surplus-services', methods=['GET'])
def get_top_trade_surplus_services():
    QUERY = """
    WITH TopTimeSlots AS (
        SELECT time_ref
        FROM `assignment1-2-418206.gsquarterlySeptember20.gsquarterlySept20`
        GROUP BY time_ref
        ORDER BY SUM(SAFE_CAST(value AS FLOAT64)) DESC
        LIMIT 10
    ),
    TopCountries AS (
        SELECT gq.country_code
        FROM `assignment1-2-418206.gsquarterlySeptember20.gsquarterlySept20` gq
        JOIN `assignment1-2-418206.country_classification.country_class` cc
        ON gq.country_code = cc.country_code
        WHERE gq.product_type = 'Goods' AND gq.status = 'F' AND gq.time_ref BETWEEN '201301' AND '201512'
        GROUP BY gq.country_code
        ORDER BY SUM(
            CASE WHEN gq.account = 'Imports' THEN SAFE_CAST(gq.value AS FLOAT64)
                 WHEN gq.account = 'Exports' THEN -SAFE_CAST(gq.value AS FLOAT64)
                 ELSE 0 END
        ) DESC
        LIMIT 40
    ),
    TradeSurplusServices AS (
        SELECT 
            sc.service_label,
            SUM(
                CASE
                    WHEN gq.account = 'Exports' THEN SAFE_CAST(gq.value AS FLOAT64)
                    WHEN gq.account = 'Imports' THEN -SAFE_CAST(gq.value AS FLOAT64)
                    ELSE 0
                END
            ) AS trade_surplus_value
        FROM 
            `assignment1-2-418206.gsquarterlySeptember20.gsquarterlySept20` gq
        JOIN 
            `assignment1-2-418206.services_classification.services_class` sc ON gq.code = sc.code
        WHERE 
            gq.product_type = 'Services' 
            AND gq.time_ref IN (SELECT time_ref FROM TopTimeSlots)
            AND gq.country_code IN (SELECT country_code FROM TopCountries)
        GROUP BY 
            sc.service_label
        ORDER BY 
            trade_surplus_value DESC
        LIMIT 
            25
    )
    SELECT * FROM TradeSurplusServices;
    """
    try:
        query_job = client.query(QUERY)
        rows = query_job.result()
        results = [dict(row) for row in rows]
        return jsonify(results)
    except Exception as e:
        print(e)
        return jsonify({"error": str(e)}), 500

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/debug/static')
def debug_static_files():
    import os
    files = os.listdir('static')
    return jsonify(files)

if __name__ == '__main__':
    app.run(debug=True)
