from Storage.db_connect import get_db_connection
from Storage.db_operations import insert_alert_analysis

def save_result_to_db(result: dict, alert_file: str = "manual_run"):
    try:
        print(f"💾 Saving result for alert: {alert_file}")

        conn = get_db_connection()
        cursor = conn.cursor()
        print("🔌 Database connection established")

        try:
            insert_alert_analysis(cursor, result, alert_file)
            conn.commit()
            print(f"✅ Alert '{alert_file}' processed and saved to DB.")

        except Exception as db_err:
            conn.rollback()
            print(f"❌ DB insert failed for alert '{alert_file}': {db_err}")

        finally:
            cursor.close()
            conn.close()

    except Exception as e:
        print(f"❌ Failed to connect or save alert '{alert_file}': {e}")

