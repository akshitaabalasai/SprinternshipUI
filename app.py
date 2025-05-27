from flask import Flask, request, jsonify
from flask_cors import CORS
from google.cloud import bigquery

app = Flask(__name__)
CORS(app)  # Enable CORS for all domains
CORS(app, origins="*", supports_credentials=True)

PROJECT_ID = "cloud-professional-services"
DATASET_ID = "sprint"
TABLE_ID = "testing_control"
client = bigquery.Client(project=PROJECT_ID)
table_ref = f"{PROJECT_ID}.{DATASET_ID}.{TABLE_ID}"

@app.route("/")
def home():
    return "Flask API is running. Visit /api/rules to see your data quality rules."

@app.route("/api/rules", methods=["GET"])
def get_rules():
    query = f"SELECT * FROM `{table_ref}` LIMIT 100"
    results = client.query(query).result()
    rules = [dict(row) for row in results]
    return jsonify(rules)


@app.route("/api/rules", methods=["POST"])
def insert():
    row = request.json
    print("Received form submission:", row)

    try:
        table = client.get_table(table_ref)
        errors = client.insert_rows(table, [row])
        if errors:
            print("BigQuery insert errors:", errors)
            return {"error": errors}, 400
        print("Inserted into BigQuery")
        return "Inserted", 201
    except Exception as e:
        print("Exception during insert:", e)
        return {"error": str(e)}, 500


@app.route("/api/rules/<rule_id>", methods=["DELETE"])
def delete_rule(rule_id):
    query = f"DELETE FROM `{table_ref}` WHERE rule_id = @rule_id"
    client.query(query, job_config=bigquery.QueryJobConfig(
        query_parameters=[bigquery.ScalarQueryParameter("rule_id", "STRING", rule_id)]
    )).result()
    return "Deleted", 200

@app.route("/api/rules/<rule_id>", methods=["PUT"])
def update_rule(rule_id):
    body = request.json
    fields = ["source_project_id", "source_dataset_id", "source_table_id",
              "metric_column", "rule_sql", "rule_family", "rule_description"]
    updates = ", ".join([f"{f} = @{f}" for f in fields])
    params = [bigquery.ScalarQueryParameter("rule_id", "STRING", rule_id)] + \
             [bigquery.ScalarQueryParameter(f, "STRING", body.get(f)) for f in fields]

    query = f"UPDATE `{table_ref}` SET {updates} WHERE rule_id = @rule_id"
    client.query(query, job_config=bigquery.QueryJobConfig(query_parameters=params)).result()
    return "Updated", 200

if __name__ == "__main__":
    app.run(debug=True)
