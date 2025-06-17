import pandas as pd
from pathlib import Path
from datetime import timedelta
from dotenv import load_dotenv
from langchain_groq import ChatGroq
from langchain_core.prompts import PromptTemplate
from langchain.output_parsers import PydanticOutputParser
from pydantic import BaseModel, Field
import os
import json

# Load environment variables
load_dotenv()
api_key = os.getenv("GROQ_API_KEY")

# Initialize LLM
llm = ChatGroq(model="llama3-8b-8192", temperature=0.2, api_key=api_key)

# File paths
BASE_DIR = Path(__file__).parent.parent
DATA_DIR = BASE_DIR / "Data"

# Load data
logs_df = pd.read_csv(DATA_DIR / "application_logs.csv")
metrics_df = pd.read_csv(DATA_DIR / "kpi_metrics.csv")
deployments_df = pd.read_csv(DATA_DIR / "production_deployment.csv")

# Parse timestamps
logs_df["timestamp"] = pd.to_datetime(logs_df["timestamp"], utc=True)
metrics_df["Timestamp"] = pd.to_datetime(metrics_df["Timestamp"], utc=True)
deployments_df["deployment_timestamp"] = pd.to_datetime(
    deployments_df["deployment_timestamp"], utc=True, dayfirst=True
)

# Pydantic schema for output parsing
class RCAOutput(BaseModel):
    root_cause: str = Field(description="Detailed root cause analysis")
    correlation: str = Field(description="Explanation of correlation with logs, metrics, deployments")
    recommended_action: str = Field(description="Steps to resolve the issue")

# Initialize output parser
parser = PydanticOutputParser(pydantic_object=RCAOutput)
format_instructions = parser.get_format_instructions()

class RCAAgent:
    def __init__(self):
        self.llm = llm
        self.logs_df = logs_df
        self.metrics_df = metrics_df
        self.deployments_df = deployments_df

        self.rca_prompt_template = PromptTemplate.from_template("""
You are an SRE assistant. Based on the inputs below, perform a root cause analysis.

Only respond with a **pure JSON object** that matches the structure exactly as shown.

### Alert Details:
- Timestamp: {timestamp}
- Alert Type: {alert_type}
- Application: {application}
- Environment: {environment}
- Severity: {severity}

### Logs (last 30 minutes):
{matched_logs}

### Metrics (last 30 minutes):
{matched_metrics}

### Deployments (last 3 days):
{matched_deployments}

### Matching SOP Titles:
{sop_titles}

{format_instructions}

Do not add any extra comments or formatting like 'Here is the JSON'. Respond with only the JSON object.
""")

        self.chain = self.rca_prompt_template.partial(format_instructions=format_instructions) | self.llm | parser

    def perform_root_cause_analysis(self, alert_json: dict, sop_matches: list = []) -> dict:
        try:
            alert_time = pd.to_datetime(alert_json["timestamp"])
        except Exception:
            print("⚠️ Invalid alert timestamp format.")
            return {"error": "Invalid alert timestamp."}

        logs_window_start = alert_time - timedelta(minutes=30)
        deployments_window_start = alert_time - timedelta(days=3)

        logs_recent = self.logs_df[
            (self.logs_df["timestamp"] >= logs_window_start) &
            (self.logs_df["timestamp"] <= alert_time)
        ]
        metrics_recent = self.metrics_df[
            (self.metrics_df["Timestamp"] >= logs_window_start) &
            (self.metrics_df["Timestamp"] <= alert_time)
        ]
        deployments_recent = self.deployments_df[
            (self.deployments_df["deployment_timestamp"] >= deployments_window_start) &
            (self.deployments_df["deployment_timestamp"] <= alert_time)
        ]

        input_data = {
            "timestamp": alert_json.get("timestamp", "Unknown"),
            "alert_type": alert_json.get("alert_type", "Unknown"),
            "application": alert_json.get("application", "Unknown"),
            "environment": alert_json.get("environment", "Unknown"),
            "severity": alert_json.get("severity", "Unknown"),
            "matched_logs": "\n".join(logs_recent["message"].dropna().unique()) if not logs_recent.empty else "None",
            "matched_metrics": "\n".join(metrics_recent["Application Name"].dropna().unique()) if not metrics_recent.empty else "None",
            "matched_deployments": "\n".join(deployments_recent["affected_modules"].dropna().unique()) if not deployments_recent.empty else "None",
            "sop_titles": "\n".join([m['title'] for m in sop_matches]) if sop_matches else "None"
        }

        try:
            result = self.chain.invoke(input_data)
            return result.dict()  # .dict() to convert Pydantic object to standard Python dict
        except Exception as e:
            return {"error": f"❌ RCA LLM failed: {str(e)}"}
