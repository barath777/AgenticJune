import json
from langchain.output_parsers import PydanticOutputParser
from langchain_groq import ChatGroq
from dotenv import load_dotenv
import os
from pydantic import BaseModel, Field

load_dotenv()

api_key = os.getenv("GROQ_API_KEY")
llm = ChatGroq(model="llama3-8b-8192", temperature=0.2, api_key=api_key)

# Pydantic schema for structured output
class ResolutionPlan(BaseModel):
    root_cause: str = Field(..., description="Root cause of the alert")
    fix: list[str] = Field(..., description="List of resolution steps")
    action_type: list[str] = Field(..., description="List of action types to be performed, e.g., 'restart service', 'rollback', 'scale up', 'apply hotfix'")
    confidence_score: float = Field(..., description="Confidence score between 0.0 and 1.0")

# Structured output parser
parser = PydanticOutputParser(pydantic_object=ResolutionPlan)

# Chain with LLM and parser
chain = llm | parser

# RecommendationAgent class that uses the external chain
class RecommendationAgent:
    def __init__(self, chain):
        self.chain = chain
        self.parser = parser

    def generate_suggestions(self, alert_json, rca_summary, similar_alerts, sop_matches):
        try:
            format_instructions = self.parser.get_format_instructions()

            prompt = f"""
You are an AI SRE assistant. Analyze the following alert and generate a resolution plan.

**ALERT DETAILS**:
{json.dumps(alert_json, indent=2)}

**ROOT CAUSE ANALYSIS**:
{rca_summary}

**SIMILAR PAST ALERTS**:
{json.dumps(similar_alerts, indent=2) if similar_alerts else "None found"}

**RELEVANT SOPs**:
{json.dumps(sop_matches, indent=2) if sop_matches else "None matched"}

---

Generate a resolution plan using this JSON format strictly:
{format_instructions}

The 'action_type' field should list the types of actions required to fix the issue, like:
- restart service


The output of action_type must be only within the listed types of action, if it is not related do not print the output of action_type and leave it blank

Be extremely conservative with confidence scoring based on:
- 0.0-0.3 if RCA is vague, app unknown, or no similar alerts
- 0.3-0.5 if partial clues or SOP matches
- 0.5-0.8 if clear RCA but limited historical data
- 0.8-1.0 only if RCA + strong similar alerts + exact SOP matches

Unknown applications = max score 0.3
Vague RCA = reduce score
"""
            recommendation = self.chain.invoke(prompt)
            return recommendation.dict()

        except Exception as e:
            return {"error": f"Error generating remediation: {str(e)}"}