import sys
import os

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from Orchestrator.orchestration import graph
from datetime import datetime
import uvicorn
from fastapi import Request 

app = FastAPI()

# Pydantic model for input
class AlertInput(BaseModel):
    alert_json: dict

@app.post("/run-alert")
def run_alert(alert_input: AlertInput):
    try:
        # print("-" * 100)
        # print("Received Alert")
        # print(datetime.now())
        result = graph.invoke({"alert_json": alert_input.alert_json})
        # print("%" * 100)
        # print(result)
        # print("$" * 100)
        # print(datetime.now())
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
# async def run_alert(request: Request):
#     try:
#         alert_json = await request.json()
#         result = graph.invoke({"alert_json": alert_json})
#         return result
#     except Exception as e:
#         raise HTTPException(status_code=500, detail=str(e))

# Run locally with: python app.py
if __name__ == "__main__":
    uvicorn.run("app:app", host="0.0.0.0", port=8000, reload=True)