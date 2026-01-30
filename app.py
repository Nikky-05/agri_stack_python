from fastapi import FastAPI, HTTPException
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Optional, Dict, Any
from datetime import datetime

# Import our new professional modules
from config import LGD_TO_STATE
from nlp_handler import NLPHandler
from db_handler import DBHandler
from csv_handler import CSVHandler

app = FastAPI(title="AgriStack MIS Analytics - Modular")

# Enable CORS for frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount Frontend Static Files
app.mount("/frontend", StaticFiles(directory="frontend"), name="frontend")

# SETTING: Switch between "database" and "csv" here
DATA_SOURCE = "database" 

# Initialize Handlers
nlp = NLPHandler()
db_engine = DBHandler()
csv_engine = CSVHandler()

class UserQuery(BaseModel):
    query: str
    user_lgd_code: str = "27"

@app.post("/chat")
async def chat(request: UserQuery):
    user_lgd = request.user_lgd_code
    user_state = LGD_TO_STATE.get(user_lgd, f"LGD {user_lgd}")

    # 1. Understand Intent (NLP Layer)
    intent = nlp.classify_intent(request.query)

    # 2. Handle Conversation Mode (LLM generates dynamic response)
    if intent["mode"] == "conversation":
        message = nlp.get_conversation_response(intent["sub_type"], request.query)
        return {
            "title": "AgriStack Assistant",
            "chart_data": {"type": "message", "values": []},
            "narration": message,
            "metadata": {"intent_type": "conversation", "state": user_state}
        }

    # 3. Handle Analytics Mode (Data Layer)
    try:
        # Choose engine dynamically
        if DATA_SOURCE == "csv":
            result = db_engine.execute_analytics(intent, user_lgd)
        else:
            result = csv_engine.execute_analytics(intent, user_lgd)

        # 4. Generate Narration (AI-Powered storytelling)
        narration = nlp.generate_narration(result, user_state, request.query)

        return {
            "title": result["title"],
            "chart_data": {
                "type": result["chart_type"],
                "labels": result["labels"],
                "values": result["values"],
                "unit": result["unit"]
            },
            "narration": narration,
            "metadata": {
                "intent_type": "analytics",
                "source": DATA_SOURCE,
                "state": user_state,
                "timestamp": datetime.now().isoformat()
            }
        }

    except Exception as e:
        return {
            "title": "Error",
            "chart_data": {"type": "message", "values": []},
            "narration": f"Sorry, I encountered an error: {str(e)}",
            "metadata": {"error": True}
        }

@app.get("/health")
def health():
    return {"status": "Active", "mode": DATA_SOURCE}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8001)
