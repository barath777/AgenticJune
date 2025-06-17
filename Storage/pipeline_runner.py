from Orchestrator.orchestration import graph

def run_pipeline(alert_json: dict, alert_file: str = "manual_run"):
    result = graph.invoke({"alert_json": alert_json})
    result["alert_file"] = alert_file
    return result 