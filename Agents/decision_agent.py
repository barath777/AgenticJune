import os
import yaml
from typing import Dict
from groq import Groq 

class DecisionAgent:
    def __init__(self, rules_path: str = "../BusinessRules/business_rules.yml"):
        print("Construtor worked")
        self.rules = self.load_business_rules(rules_path)
        print("Business files loaded")
        self.client = Groq()  # Replace with your LLM client as needed

    def load_business_rules(self, path: str) -> Dict:
        if not os.path.exists(path):
            raise FileNotFoundError(f"Business rules file not found: {path}")
        with open(path, "r") as file:
            return yaml.safe_load(file)

    def query_llm_confidence(self, suggestion: str, severity: str) -> float:
        prompt = f"""
An AI assistant has generated the following remediation plan:

\"\"\"{suggestion}\"\"\"

The alert severity is "{severity}".

On a scale of 0.0 to 1.0, how confident are you that this remediation can be executed automatically without human intervention? 
Return only a number. Example: 0.87
"""
        try:
            response = self.client.chat.completions.create(
                model="llama3-8b-8192",  # or "gpt-4o" etc.
                messages=[{"role": "user", "content": prompt}]
            )
            confidence = float(response.choices[0].message.content.strip())
            return confidence
        except Exception as e:
            print(f"[LLM ERROR] Failed to get confidence: {e}")
            return 0.0  # fallback to low confidence

    def decide_action(self, recommendation_data: Dict) -> Dict:
        try:
            alert_type = recommendation_data.get("alert_type", "")
            severity = recommendation_data.get("severity", "unknown").lower()
            past_resolution_exists = recommendation_data.get("past_resolution_exists", False)
            ai_suggested_fix = recommendation_data.get("ai_suggested_fix", "")
            past_fix = recommendation_data.get("past_fix", "")
            confidence = recommendation_data.get("confidence_score")

            # Step 1: Business Policy Check
            if alert_type in self.rules.get("manual_review_alerts", []):
                return {
                    "decision": "manual_review",
                    "reason": f"Alert type '{alert_type}' always requires manual review per business rules."
                }

            # Step 2: Severity Check
            if severity == "critical":
                return {
                    "decision": "manual_review",
                    "reason": "Critical severity alert. Must be reviewed manually."
                }

            # Step 3: LLM Confidence (if not already available)
            if confidence is None:
                confidence = self.query_llm_confidence(ai_suggested_fix, severity)

            # Step 4: Past Fix Match
            if past_resolution_exists and ai_suggested_fix and ai_suggested_fix.lower() == past_fix.lower():
                if confidence >= self.rules.get("minimum_confidence_for_auto_remediate", 0.85):
                    return {
                        "decision": "auto_remediate",
                        "reason": "Past fix matches and confidence is high. Safe to auto-remediate."
                    }
                else:
                    return {
                        "decision": "review_required",
                        "reason": "Past fix matches, but confidence is below threshold. Human review advised."
                    }

            # Step 5: Confidence threshold (fallback)
            if confidence < self.rules.get("minimum_confidence_for_auto_remediate", 0.85):
                return {
                    "decision": "manual_review",
                    "reason": "Confidence is low. Manual review required."
                }

            # Default fallback
            return {
                "decision": "review_required",
                "reason": "No past resolution match. Review recommended before applying fix."
            }

        except Exception as e:
            return {
                "decision": "error",
                "reason": f"Decision agent failed with exception: {str(e)}"
            }











# from typing import Dict

# class DecisionAgent:
#     def __init__(self):
#         pass

#     def decide_action(self, recommendation_data: Dict) -> Dict:
#         try:
#             # Ensure the confidence_score is present and valid
#             confidence = recommendation_data.get("confidence_score")
#             if confidence is None:
#                 return {"decision": "manual_review", "reason": "No confidence score found in recommendation."}

#             confp = confidence * 100  # Convert to percentage scale

#             if confp >= 65:
#                 decision = "auto_remediate"
#             elif confp < 50:
#                 decision = "escalate"
#             else:
#                 decision = "verify_with_human"

#             return {
#                 "decision": decision,
#                 "Confidence Percentage": confp,
#                 "recommendation_summary": recommendation_data
#             }

#         except Exception as e:
#             return {"error": str(e)}
