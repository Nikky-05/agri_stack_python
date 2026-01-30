from fastapi import FastAPI, HTTPException
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Optional, Dict, Any
from datetime import datetime

from config import LGD_TO_STATE
from nlp_handler import NLPHandler
from csv_handler import CSVHandler

app = FastAPI(title="AgriStack MIS Analytics - Comprehensive")

# Enable CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount Frontend
app.mount("/frontend", StaticFiles(directory="frontend"), name="frontend")

# Data source setting
DATA_SOURCE = "csv"

# Initialize handlers
nlp = NLPHandler()
csv_engine = CSVHandler()


class UserQuery(BaseModel):
    query: str
    user_lgd_code: str = "27"


@app.post("/chat")
async def chat(request: UserQuery):
    user_lgd = request.user_lgd_code
    user_state = LGD_TO_STATE.get(user_lgd, f"State (LGD: {user_lgd})")

    # 1. Classify Intent
    intent = nlp.classify_intent(request.query)

    # 2. Handle Conversation Mode
    if intent.get("mode") == "conversation":
        message = nlp.get_conversation_response(intent.get("sub_type", "help"), request.query)
        return {
            "title": "AgriStack Assistant",
            "chart_data": {"type": "message", "values": [], "labels": [], "unit": ""},
            "narration": message,
            "metadata": {
                "intent_type": "conversation",
                "state": user_state
            }
        }

    # 3. Execute Analytics
    try:
        result = csv_engine.execute_analytics(intent, user_lgd)

        # 4. Generate Narration
        narration = nlp.generate_narration(result, user_state, request.query)

        # 5. Build Response
        metadata = {
            "intent_type": "analytics",  # Always "analytics" for chart rendering
            "query_type": intent.get("intent_type", "summary"),  # Original type for reference
            "source": DATA_SOURCE,
            "state": user_state,
            "timestamp": datetime.now().isoformat(),
            "indicator": intent.get("indicator"),
            "dimension": intent.get("dimension"),
            "record_count": result.get("record_count", 0)
        }

        # Add optional metadata
        if result.get("crop_filter"):
            metadata["crop_filter"] = result["crop_filter"]
        if result.get("season_filter"):
            metadata["season_filter"] = result["season_filter"]
        if result.get("year_filter"):
            metadata["year_filter"] = result["year_filter"]
        if result.get("farmers_count"):
            metadata["farmers_count"] = result["farmers_count"]
        if result.get("plots_count"):
            metadata["plots_count"] = result["plots_count"]
        if result.get("total"):
            metadata["total"] = result["total"]

        return {
            "title": result.get("title", "Analysis"),
            "chart_data": {
                "type": result.get("chart_type", "kpi"),
                "labels": result.get("labels", []),
                "values": result.get("values", []),
                "unit": result.get("unit", ""),
                "percentages": result.get("percentages", [])
            },
            "narration": narration,
            "metadata": metadata
        }

    except Exception as e:
        print(f"Error: {e}")
        return {
            "title": "Error",
            "chart_data": {"type": "message", "values": [], "labels": [], "unit": ""},
            "narration": f"Sorry, I couldn't process your request: {str(e)}",
            "metadata": {"error": True, "message": str(e)}
        }


@app.get("/health")
def health():
    return {"status": "Active", "mode": DATA_SOURCE, "timestamp": datetime.now().isoformat()}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8001)
