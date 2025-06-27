import os
import yaml
from typing import Dict
from groq import Groq 

class DecisionAgent:
    def __init__(self, rules_path: str = "../BusinessRules/business_rules1.yml"):
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
            ai_suggested_fix = recommendation_data.get("ai_suggested_fix", "")
            severity = recommendation_data.get("severity", "").lower()
            confidence = recommendation_data.get("confidence_score")
            similar_alerts = recommendation_data.get("similar_alerts", [])
            similarity_threshold = self.rules.get("general", {}).get("similarity_threshold", 0.8)
            confidence_threshold = self.rules.get("general", {}).get("confidence_threshold", {}).get("threshold", 0.75)
            # DEBUG print
            print("[DEBUG] Similar Alerts:", similar_alerts)
            print("[DEBUG] Confidence:", confidence)
            
            # Step 1: Get confidence if missing
            if confidence is None:
                confidence = self.query_llm_confidence(ai_suggested_fix, severity)
                print("[DEBUG] Queried confidence from LLM:", confidence)
                
            # Step 2: Determine if similar alert match exists
            similar_match = any(
                float(alert.get("similarity_score", 0.0)) >= similarity_threshold
                for alert in similar_alerts
                )
            print("[DEBUG] Found similar match:", similar_match)
            
            # Step 3: Final decisions
            if similar_match and confidence >= confidence_threshold:
                return {
                    "decision": "auto_remediate",
                    "reason": "Similar past alert found and confidence is high. Proceeding with auto-remediation."
                    }
                
            if similar_match:
                return {
                    "decision": "review_required",
                    "reason": "Similar alert found but confidence is low. Needs review."
                    }
                    
            if confidence >= confidence_threshold:
                return {
                    "decision": "review_required",
                    "reason": "No similar alerts found, but confidence is high. Review before applying fix."
                    }
                
            return {
                "decision": "manual_review",
                "reason": "No similar alerts found and confidence is low. Manual review required."
                }
        except Exception as e:
            return {
                "decision": "error",
                "reason": f"Decision agent failed: {str(e)}"
                }
