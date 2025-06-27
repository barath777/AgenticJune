import os
from langchain_groq import ChatGroq
from langchain_core.output_parsers import StrOutputParser
#from Storage.db_operations import save_alert_summary

class ResponseAgent:
    def __init__(self):
        api_key = os.getenv("GROQ_API_KEY")
        self.llm = ChatGroq(model="llama3-8b-8192", temperature=0.2, api_key=api_key)
        self.output_parser = StrOutputParser()

    def format_user_response_prompt(self, query: str, context: dict) -> str:
        return f"""
You are an assistant helping users understand alerts in a system.

User Query: {query}

Summarize based on the available context:
- RCA: {context.get('rca', 'N/A')}
- Recommendation: {context.get('recommendation', 'N/A')}
- Decision: {context.get('decision', 'N/A')}
- Remediation: {context.get('remediation', 'N/A')}
- SOP Match: {context.get('sop', 'N/A')}
- Similar Incidents: {context.get('similar_incidents', 'N/A')}
- Confidence Score: {context.get('confidence', 'N/A')}

Respond in a clear, helpful, and friendly tone.
"""

    def generate_user_response(self, query: str, context: dict) -> str:
        prompt = self.format_user_response_prompt(query, context)
        chain = self.llm | self.output_parser
        return chain.invoke(prompt)

    def summarize_alert(self, context: dict, alert_id: str) -> str:
        summary_prompt = f"""
You are generating a final summary for an alert incident. Create a concise and professional report that includes:

1. Root Cause Analysis:
{context.get('rca', 'N/A')}

2. Recommendation Steps:
{context.get('recommendation', 'N/A')}

3. Decision Taken:
{context.get('decision', 'N/A')}

4. Remediation Plan:
{context.get('remediation', 'N/A')}

5. SOP Matched:
{context.get('sop', 'N/A')}

6. Similar Past Incidents:
{context.get('similar_incidents', 'N/A')}

7. Confidence Score:
{context.get('confidence', 'N/A')}

End the summary with a short note on whether manual review is needed.
"""
        chain = self.llm | self.output_parser
        summary = chain.invoke(summary_prompt)
        #save_alert_summary(alert_id=alert_id, summary=summary)
        return summary
