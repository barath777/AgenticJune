import json

def insert_alert_analysis(cursor, result: dict, alert_file: str = "manual_run"):
    try:
        print("🚨 Preparing to insert data into agents.log_analysis")

        alert_id = result["alert_json"].get("alert_id")

        # Check for duplicate (same alert_id and alert_file)
        cursor.execute("""
            SELECT 1 FROM agents.log_analysis
            WHERE alert_id = %s AND alert_file = %s
            LIMIT 1
        """, (alert_id, alert_file))

        if cursor.fetchone():
            print(f"⚠️ Alert '{alert_id}' from file '{alert_file}' already exists. Skipping insert.")
            return

        # Prepare insert query and parameters
        query = """
            INSERT INTO agents.log_analysis (
                alert_file,
                alert_id,
                alert_type,
                timestamp,
                alert_description,
                sop_matches,
                similar_incidents,
                rca_output,
                recommendation_output,
                confidence_score,
                decision_output,
                remediation_output
            ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        """

        params = (
            alert_file,
            alert_id,
            result["alert_json"].get("alert_type"),
            result["alert_json"].get("timestamp"),
            result["alert_json"].get("description"),
            json.dumps(result.get("sop_matches", [])),
            json.dumps(result.get("similar_alerts", [])),
            #result.get("rca_output", ""),
            json.dumps(result.get("rca_output", [])),
            json.dumps(result.get("recommendation", {})),
            float(result.get("decision", {}).get("average_confidence", 0.0)),
            json.dumps(result.get("decision", {})),
            json.dumps(result.get("remediation_status", {}))

        )

        # Execute insert
        cursor.execute(query, params)

        print("✅ Insert successful for alert:", alert_id)

    except Exception as e:
        print(f"❌ Error during DB insert: {e}")
        raise
