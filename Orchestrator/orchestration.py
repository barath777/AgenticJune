import sys
import os

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import json
from langgraph.graph import StateGraph, END
from typing import TypedDict, Optional
from Agents.search_agent import SearchAgent
from Agents.rca_agent import RCAAgent
from Agents.recommendation_agent import RecommendationAgent, ResolutionPlan
from Agents.decision_agent import DecisionAgent
from Agents.remediation_agent import RemediationAgent
from Agents.response_agent import ResponseAgent  # NEW
from datetime import datetime
from Embeddings import load_sop
from langchain_groq import ChatGroq
from langchain.output_parsers import PydanticOutputParser
from langchain_core.output_parsers import StrOutputParser
from Storage.file_processing import save_result_to_db
from pathlib import Path

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

llm = ChatGroq(
    model="llama3-8b-8192",
    temperature=0.2,
    api_key=os.getenv("GROQ_API_KEY")
)

parser = PydanticOutputParser(pydantic_object=ResolutionPlan)
chain = llm | parser

# Define the shared state
class AlertState(TypedDict):
    alert_json: dict
    sop_matches: Optional[list[dict]]
    similar_alerts: Optional[list]
    rca_output: Optional[str]
    recommendation: Optional[str]
    decision: Optional[dict]
    remediation_status: Optional[str]
    response_summary: Optional[str]  # NEW

# Initialize agents
search_agent = SearchAgent()
rca_agent = RCAAgent()
recommendation_agent = RecommendationAgent(chain=chain)
decision_agent = DecisionAgent()
remediation_agent = RemediationAgent()
response_agent = ResponseAgent()  # NEW

def load_sopstore(state: AlertState) -> AlertState:
    alert_text = state["alert_json"].get("description", "")
    sop_results = load_sop.search_sop(alert_text)
    state["sop_matches"] = sop_results
    return state

def run_rca(state: AlertState) -> AlertState:
    state["rca_output"] = rca_agent.perform_root_cause_analysis(
        state["alert_json"], state.get("sop_matches", "")
    )
    return state

def run_search(state: AlertState) -> AlertState:
    state["similar_alerts"] = search_agent.search(state["alert_json"])
    return state

def run_recommendation(state: AlertState) -> AlertState:
    state["recommendation"] = recommendation_agent.generate_suggestions(
        alert_json=state["alert_json"],
        rca_summary=state["rca_output"],
        similar_alerts=state.get("similar_alerts", []),
        sop_matches=state.get("sop_matches", "")
    )
    return state

def run_decision(state: AlertState) -> AlertState:
    state["decision"] = decision_agent.decide_action(state["recommendation"])
    return state

def run_remediation(state: AlertState) -> AlertState:
    decision = state.get("decision", {})
    recommendation = state.get("recommendation", {})

    if decision.get("decision") == "auto_remediate":
        action_types = recommendation.get("action_type", [])
        remediation_agent = RemediationAgent(Path(BASE_DIR) / "Mapping" / "mapping.yml")
        remediation_result = remediation_agent.perform_remediation(action_types)
        state["remediation_status"] = remediation_result
    else:
        state["remediation_status"] = "Remediation skipped — decision not approved."

    return state

def run_response_agent(state: AlertState) -> AlertState:
    context = {
        "rca": state.get("rca_output", ""),
        "recommendation": state.get("recommendation", ""),
        "decision": state.get("decision", ""),
        "remediation": state.get("remediation_status", ""),
        "sop": state.get("sop_matches", ""),
        "similar_incidents": state.get("similar_alerts", ""),
        "confidence": state.get("decision", {}).get("confidence", 0)
    }
    alert_id = state["alert_json"].get("alert_id", "UNKNOWN_ALERT_ID")
    summary = response_agent.summarize_alert(context, alert_id=alert_id)
    state["response_summary"] = summary
    return state

# Build the LangGraph pipeline
builder = StateGraph(AlertState)
builder.add_node("sop_loader_node", load_sopstore)
builder.add_node("rca_node", run_rca)
builder.add_node("search_node", run_search)
builder.add_node("recommendation_node", run_recommendation)
builder.add_node("decision_node", run_decision)
builder.add_node("remediation_node", run_remediation)
builder.add_node("response_node", run_response_agent)  # NEW

builder.set_entry_point("sop_loader_node")
builder.add_edge("sop_loader_node", "rca_node")
builder.add_conditional_edges("rca_node", lambda state: "search_node")
builder.add_conditional_edges("search_node", lambda state: "recommendation_node")
builder.add_conditional_edges("recommendation_node", lambda state: "decision_node")
builder.add_edge("recommendation_node", "decision_node")
builder.add_edge("decision_node", "remediation_node")
builder.add_edge("remediation_node", "response_node")  # NEW
builder.add_edge("response_node", END)  # NEW

graph = builder.compile()

if __name__ == "__main__":
    alert_path = os.path.join(BASE_DIR, "Alerts", "ALERT001.json")
    try:
        with open(alert_path, "r") as f:
            alert_data = json.load(f)

        print(datetime.now())
        print("Running Orchestrator")

        result = graph.invoke({"alert_json": alert_data})
        result["alert_file"] = alert_path

        print("\nRemediation Status:", json.dumps(result.get("remediation_status", {})))
        print("\nFinal Response Summary:\n", result.get("response_summary", "No summary generated"))

        # ✅ Save to DB
        save_result_to_db(result, alert_file=alert_path)

    except FileNotFoundError:
        print(f"Error: Alert file '{alert_path}' not found.")
    except json.JSONDecodeError:
        print(f"Error: Invalid JSON format in '{alert_path}'.")
    except Exception as e:
        print(f"Unexpected error: {str(e)}")
