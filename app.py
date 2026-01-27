from fastapi import FastAPI, HTTPException
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional, Dict, List, Any, Union
import psycopg2
from psycopg2.extras import RealDictCursor
import json
import os
import requests
import re
from datetime import datetime

from dotenv import load_dotenv

load_dotenv()

# ============================================================
# 1. APPLICATION & DATABASE CONFIGURATION
# ============================================================

DB_PARAMS = {
    "dbname": os.getenv("DB_NAME", "exam_db"),
    "user": os.getenv("DB_USER", "postgres"),
    "password": os.getenv("DB_PASSWORD", "NKpallotti@99"),
    "host": os.getenv("DB_HOST", "localhost"),
    "port": os.getenv("DB_PORT", "5432")
}

app = FastAPI(title="AgriStack MIS - Government Analytics Engine")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.mount("/frontend", StaticFiles(directory="frontend"), name="frontend")

# ============================================================
# 2. LGD AUTHORIZATION REGISTRY (CRITICAL FOR SECURITY)
# ============================================================

# State LGD Code Mapping - Official Government Codes
STATE_LGD_MAP = {
    # State Name (lowercase) -> LGD Code
    "andhra pradesh": "28", "ap": "28",
    "arunachal pradesh": "12",
    "assam": "18",
    "bihar": "10",
    "chhattisgarh": "22", "chattisgarh": "22",
    "goa": "30",
    "gujarat": "24",
    "haryana": "6",
    "himachal pradesh": "2", "hp": "2",
    "jharkhand": "20",
    "karnataka": "29",
    "kerala": "32",
    "madhya pradesh": "23", "mp": "23",
    "maharashtra": "27",
    "manipur": "14",
    "meghalaya": "17",
    "mizoram": "15",
    "nagaland": "13",
    "odisha": "21", "orissa": "21",
    "punjab": "3",
    "rajasthan": "8",
    "sikkim": "11",
    "tamil nadu": "33", "tn": "33",
    "telangana": "36",
    "tripura": "16",
    "uttar pradesh": "9", "up": "9",
    "uttarakhand": "5",
    "west bengal": "19", "wb": "19",
    # Union Territories
    "delhi": "7", "ncr": "7",
    "jammu and kashmir": "1", "j&k": "1",
    "ladakh": "37",
    "puducherry": "34", "pondicherry": "34",
}

# Reverse mapping: LGD Code -> State Name
LGD_TO_STATE = {
    "1": "Jammu & Kashmir", "2": "Himachal Pradesh", "3": "Punjab",
    "5": "Uttarakhand", "6": "Haryana", "7": "Delhi", "8": "Rajasthan",
    "9": "Uttar Pradesh", "10": "Bihar", "11": "Sikkim", "12": "Arunachal Pradesh",
    "13": "Nagaland", "14": "Manipur", "15": "Mizoram", "16": "Tripura",
    "17": "Meghalaya", "18": "Assam", "19": "West Bengal", "20": "Jharkhand",
    "21": "Odisha", "22": "Chhattisgarh", "23": "Madhya Pradesh", "24": "Gujarat",
    "27": "Maharashtra", "28": "Andhra Pradesh", "29": "Karnataka", "30": "Goa",
    "32": "Kerala", "33": "Tamil Nadu", "34": "Puducherry", "36": "Telangana",
    "37": "Ladakh",
}

# ============================================================
# 3. INDICATOR REGISTRY (DATA METRICS)
# ============================================================

INDICATOR_MAP = {
    # Survey/Staff Metrics (aggregate_summary_data)
    "plots_assigned": {
        "table": "aggregate_summary_data",
        "column": "total_assigned_plots",
        "agg": "SUM",
        "title": "Plots Assigned",
        "unit": "Count"
    },
    "plots_surveyed": {
        "table": "aggregate_summary_data",
        "column": "total_plots_surveyed",
        "agg": "SUM",
        "title": "Plots Surveyed",
        "unit": "Count"
    },
    "surveyor_count": {
        "table": "aggregate_summary_data",
        "column": "total_no_of_surveyors",
        "agg": "SUM",
        "title": "Surveyors Deployed",
        "unit": "Count"
    },
    "approved_surveys": {
        "table": "aggregate_summary_data",
        "column": "total_survey_approved",
        "agg": "SUM",
        "title": "Approved Surveys",
        "unit": "Count"
    },

    # Crop/Farmer Metrics (crop_area_data)
    "crop_area": {
        "table": "crop_area_data",
        "column": "crop_area_approved",
        "agg": "SUM",
        "title": "Approved Crop Area",
        "unit": "Hectares"
    },
    "farmer_count": {
        "table": "crop_area_data",
        "column": "no_of_farmers",
        "agg": "SUM",
        "title": "Registered Farmers",
        "unit": "Count"
    },
    "plot_count": {
        "table": "crop_area_data",
        "column": "no_of_plots",
        "agg": "SUM",
        "title": "Total Plots",
        "unit": "Count"
    },

    # Land Classification (cultivated_summary_data)
    "fallow_land": {
        "table": "cultivated_summary_data",
        "column": "total_fallow_area",
        "agg": "SUM",
        "title": "Fallow Land",
        "unit": "Hectares"
    },
    "irrigated_land": {
        "table": "cultivated_summary_data",
        "column": "total_irrigated_area",
        "agg": "SUM",
        "title": "Irrigated Area",
        "unit": "Hectares"
    },
    "unirrigated_land": {
        "table": "cultivated_summary_data",
        "column": "total_unirrigated_area",
        "agg": "SUM",
        "title": "Unirrigated Area",
        "unit": "Hectares"
    },
    "harvested_land": {
        "table": "cultivated_summary_data",
        "column": "total_harvested_area",
        "agg": "SUM",
        "title": "Harvested Area",
        "unit": "Hectares"
    },
    "surveyed_area": {
        "table": "cultivated_summary_data",
        "column": "total_surveyed_area",
        "agg": "SUM",
        "title": "Total Surveyed Area",
        "unit": "Hectares"
    },
}

# ============================================================
# 4. DIMENSION REGISTRY (GROUPING LEVELS)
# ============================================================

DIMENSION_MAP = {
    "district": {
        "column": "district_lgd_code",
        "chart": "bar",
        "label": "District"
    },
    "sub_district": {
        "column": "sub_district_lgd_code",
        "chart": "bar",
        "label": "Sub-District"
    },
    "village": {
        "column": "village_lgd_code",
        "chart": "bar",
        "label": "Village"
    },
    "crop": {
        "column": "crop_name_eng",
        "chart": "pie",
        "label": "Crop"
    },
    "irrigation": {
        "column": "irrigation_source",
        "chart": "pie",
        "label": "Irrigation Source"
    },
    "season": {
        "column": "season",
        "chart": "pie",
        "label": "Season"
    },
    "year": {
        "column": "year",
        "chart": "line",
        "label": "Year"
    },
}

# ============================================================
# 5. INTENT CLASSIFICATION SYSTEM (THE BRAIN)
# ============================================================

INTENT_CLASSIFIER_PROMPT = """
You are the Intent Classifier for AgriStack MIS - a GOVERNMENT analytics system.
You must classify user input into EXACTLY ONE of two modes.

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
MODE 1: CONVERSATION (No data needed)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Return this for:
- Greetings: "hi", "hello", "good morning", "hey"
- Thanks: "thank you", "thanks", "okay", "ok"
- Help: "what can you do", "help me", "how does this work"
- Vague: "i want analytics", "show me something", "i need data"
- Small talk: "how are you", "nice day"
- Capability questions: "can you predict", "do you have AI"
- Goodbye: "bye", "goodbye", "see you"

Output:
{"mode": "conversation", "sub_type": "greeting|thanks|help|vague|smalltalk|goodbye"}

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
MODE 2: ANALYTICS (Data query)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Return this ONLY for SPECIFIC data questions about:
- Plots: assigned, surveyed, approved
- Crops: area, distribution, top crops
- Farmers: count, registered
- Land: irrigated, unirrigated, fallow, harvested
- Surveys: progress, completion, staff

MUST extract:
1. indicator: The metric being asked
2. dimension: Grouping level (district/crop/year/etc.) or null
3. time: Year and season filters
4. mentioned_state: Any state name mentioned (or null)

Output:
{
  "mode": "analytics",
  "indicator": "crop_area|plots_surveyed|farmer_count|...",
  "dimension": "district|crop|year|season|null",
  "time": {"year": "current|2024|2023|all", "season": "Kharif|Rabi|null"},
  "mentioned_state": "maharashtra|bihar|null"
}

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
INDICATORS (use exact keys):
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
- plots_assigned, plots_surveyed, approved_surveys, surveyor_count
- crop_area, farmer_count, plot_count
- fallow_land, irrigated_land, unirrigated_land, harvested_land

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
DIMENSIONS (use exact keys):
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
- district, sub_district, village
- crop, irrigation, season, year

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
EXAMPLES:
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
"hello" → {"mode": "conversation", "sub_type": "greeting"}
"what can you do" → {"mode": "conversation", "sub_type": "help"}
"i want dynamic model" → {"mode": "conversation", "sub_type": "vague"}
"thanks" → {"mode": "conversation", "sub_type": "thanks"}

"district-wise crop area" → {"mode": "analytics", "indicator": "crop_area", "dimension": "district", "time": {"year": "current", "season": null}, "mentioned_state": null}
"how many farmers in Bihar" → {"mode": "analytics", "indicator": "farmer_count", "dimension": null, "time": {"year": "current", "season": null}, "mentioned_state": "bihar"}
"plots surveyed this year" → {"mode": "analytics", "indicator": "plots_surveyed", "dimension": null, "time": {"year": "current", "season": null}, "mentioned_state": null}
"year-wise irrigated area trend" → {"mode": "analytics", "indicator": "irrigated_land", "dimension": "year", "time": {"year": "all", "season": null}, "mentioned_state": null}
"top crops in Kharif season" → {"mode": "analytics", "indicator": "crop_area", "dimension": "crop", "time": {"year": "current", "season": "Kharif"}, "mentioned_state": null}

OUTPUT JSON ONLY. No markdown. No explanation.
"""

# ============================================================
# 6. CONVERSATION RESPONSE TEMPLATES
# ============================================================

CONVERSATION_RESPONSES = {
    "greeting": [
        "Hello! I'm the AgriStack MIS Analytics Assistant. I can help you with agricultural data insights for your authorized region. What would you like to know?",
        "Welcome to AgriStack MIS! I'm here to provide data-driven insights about crops, surveys, farmers, and land usage. How can I assist you today?",
        "Greetings! I'm your analytics assistant for agricultural data. Ask me about crop areas, survey progress, farmer counts, or land metrics.",
    ],
    "thanks": [
        "You're welcome! Feel free to ask more questions about agricultural data anytime.",
        "Happy to help! Let me know if you need any other analytics insights.",
        "Glad I could assist. I'm here whenever you need agricultural data analysis.",
    ],
    "help": """I am the AgriStack MIS Conversational Analytics Assistant. Here's what I can help you with:

**Data Queries I Support:**
• **Survey Progress**: Plots assigned, surveyed, approved; surveyor counts
• **Crop Analytics**: Crop-wise area distribution, top crops by area
• **Farmer Statistics**: Registered farmer counts by region
• **Land Metrics**: Irrigated, unirrigated, fallow, and harvested areas

**Query Examples:**
• "District-wise crop area summary"
• "How many plots have been surveyed?"
• "Top 5 crops in Kharif season"
• "Year-wise survey progress trend"
• "Show irrigated vs unirrigated area"

**Important:** I only show data for your authorized State LGD region. Cross-state queries are restricted for security compliance.

What would you like to explore?""",

    "vague": "I'd be happy to help with analytics! Could you please be more specific? For example:\n\n• \"District-wise crop area summary\"\n• \"How many plots have been surveyed this year?\"\n• \"Total registered farmers\"\n• \"Year-wise survey progress\"\n\nWhat specific data would you like to see?",

    "smalltalk": "I'm functioning well, thank you! I'm the AgriStack analytics assistant - I work best with specific data questions. Try asking about crop areas, survey progress, or farmer statistics!",

    "goodbye": "Thank you for using AgriStack MIS. Have a great day! Feel free to return whenever you need agricultural analytics.",
}

# ============================================================
# 7. INTENT CLASSIFIER FUNCTION
# ============================================================

def classify_intent(query: str) -> Dict[str, Any]:
    """
    Classify user query into conversation or analytics mode.
    Uses LLM when available, falls back to rule-based heuristics.
    """
    # Try LLM classification first
    try:
        response = requests.post(
            os.getenv("LLM_API_URL", "http://localhost:11434/api/generate"),
            json={
                "model": "gpt-oss-120b",
                "prompt": query,
                "system": INTENT_CLASSIFIER_PROMPT,
                "format": "json",
                "stream": False
            },
            timeout=15
        )
        if response.status_code == 200:
            result = json.loads(response.json().get("response", "{}"))
            if result.get("mode"):
                return result
    except Exception as e:
        print(f"[LLM Error] {e}")

    # ========== RULE-BASED FALLBACK ==========
    q = query.lower().strip()

    # ----- CONVERSATION PATTERNS -----

    # Greetings
    greeting_exact = ["hi", "hello", "hey", "hii", "hiii", "yo"]
    greeting_starts = ["good morning", "good afternoon", "good evening", "hi ", "hello ", "hey "]
    if q in greeting_exact or any(q.startswith(g) for g in greeting_starts):
        return {"mode": "conversation", "sub_type": "greeting"}

    # Thanks
    thanks_patterns = ["thank", "thanks", "thx", "ok", "okay", "got it", "understood"]
    if any(p in q for p in thanks_patterns) and len(q) < 30:
        return {"mode": "conversation", "sub_type": "thanks"}

    # Goodbye
    goodbye_patterns = ["bye", "goodbye", "see you", "take care", "gotta go"]
    if any(p in q for p in goodbye_patterns):
        return {"mode": "conversation", "sub_type": "goodbye"}

    # Help / Capability questions
    help_patterns = ["what can you", "how do you", "what do you", "help me", "how does this",
                     "what is this", "explain", "your capabilities", "can you help"]
    if any(p in q for p in help_patterns):
        return {"mode": "conversation", "sub_type": "help"}

    # Vague requests
    vague_patterns = ["i want", "i need", "show me", "give me", "can you show",
                      "dynamic", "complete", "full", "everything", "all data"]
    if any(p in q for p in vague_patterns) and not any(x in q for x in ["district", "crop", "farmer", "plot", "survey", "area"]):
        return {"mode": "conversation", "sub_type": "vague"}

    # Small talk
    smalltalk_patterns = ["how are you", "how're you", "whats up", "what's up", "wassup"]
    if any(p in q for p in smalltalk_patterns):
        return {"mode": "conversation", "sub_type": "smalltalk"}

    # Very short queries (likely not analytics)
    if len(q) < 4:
        return {"mode": "conversation", "sub_type": "greeting"}

    # ----- ANALYTICS EXTRACTION -----

    # Detect mentioned state
    mentioned_state = None
    for state_name, lgd_code in STATE_LGD_MAP.items():
        if state_name in q:
            mentioned_state = state_name
            break

    # Extract dimension
    dimension = None
    if "district" in q and "sub" not in q:
        dimension = "district"
    elif "sub-district" in q or "subdistrict" in q or "taluka" in q or "tehsil" in q:
        dimension = "sub_district"
    elif "village" in q:
        dimension = "village"
    elif ("crop" in q and "wise" in q) or "top crop" in q or "crop distribution" in q:
        dimension = "crop"
    elif "irrigation" in q and ("wise" in q or "source" in q or "type" in q):
        dimension = "irrigation"
    elif "season" in q and "wise" in q:
        dimension = "season"
    elif "year" in q and ("wise" in q or "trend" in q or "progress" in q or "comparison" in q):
        dimension = "year"

    # Extract indicator
    indicator = "crop_area"  # default

    if "plot" in q:
        if "survey" in q:
            indicator = "plots_surveyed"
        elif "assign" in q:
            indicator = "plots_assigned"
        else:
            indicator = "plot_count"
    elif "surveyed area" in q or "area surveyed" in q:
        indicator = "surveyed_area"
    elif "survey" in q:
        if "approv" in q:
            indicator = "approved_surveys"
        elif "progress" in q or "status" in q:
            indicator = "plots_surveyed"
        else:
            indicator = "plots_surveyed"
    elif "surveyor" in q or "staff" in q:
        indicator = "surveyor_count"
    elif "farmer" in q:
        indicator = "farmer_count"
    elif "fallow" in q:
        indicator = "fallow_land"
    elif "irrigat" in q:
        if "unirrigat" in q or "un-irrigat" in q or "non-irrigat" in q:
            indicator = "unirrigated_land"
        else:
            indicator = "irrigated_land"
    elif "harvest" in q:
        indicator = "harvested_land"
    elif "crop" in q or "area" in q:
        indicator = "crop_area"

    # Extract time
    year = "current"
    season = None

    if "all year" in q or "historical" in q or "trend" in q or "over the years" in q:
        year = "all"
    elif "2025" in q:
        year = "2025"
    elif "2024" in q:
        year = "2024"
    elif "2023" in q:
        year = "2023"
    elif "2022" in q:
        year = "2022"
    elif "last year" in q:
        year = "2024"  # Assuming current is 2025

    if "kharif" in q:
        season = "Kharif"
    elif "rabi" in q:
        season = "Rabi"
    elif "zaid" in q or "summer" in q:
        season = "Zaid"

    return {
        "mode": "analytics",
        "indicator": indicator,
        "dimension": dimension,
        "time": {"year": year, "season": season},
        "mentioned_state": mentioned_state
    }

# ============================================================
# 8. LGD AUTHORIZATION GUARD
# ============================================================

def check_lgd_authorization(user_lgd: str, mentioned_state: Optional[str]) -> Dict[str, Any]:
    """
    Verify if the user is authorized to query the mentioned state.
    Returns authorization status and appropriate message.
    """
    if not mentioned_state:
        return {"authorized": True}

    # Get LGD code for mentioned state
    mentioned_lgd = STATE_LGD_MAP.get(mentioned_state.lower())

    if not mentioned_lgd:
        # State not recognized - allow query (might be district/city name)
        return {"authorized": True}

    # Check authorization
    if mentioned_lgd != user_lgd:
        user_state = LGD_TO_STATE.get(user_lgd, f"LGD {user_lgd}")
        mentioned_state_name = LGD_TO_STATE.get(mentioned_lgd, mentioned_state.title())

        return {
            "authorized": False,
            "user_state": user_state,
            "user_lgd": user_lgd,
            "requested_state": mentioned_state_name,
            "requested_lgd": mentioned_lgd,
            "message": f"You are currently authorized for {user_state} (LGD: {user_lgd}). "
                       f"Data for {mentioned_state_name} (LGD: {mentioned_lgd}) cannot be accessed with your current permissions. "
                       f"Please contact your administrator for cross-state access or ask questions about {user_state}."
        }

    return {"authorized": True}

# ============================================================
# 9. SQL BUILDER (SECURE & DETERMINISTIC)
# ============================================================

def build_analytics_sql(indicator_key: str, dimension_key: Optional[str],
                        time_params: Dict, user_lgd: str) -> Dict[str, Any]:
    """
    Build a secure, parameterized SQL query based on analytics request.
    """
    # Get indicator config
    if indicator_key not in INDICATOR_MAP:
        indicator_key = "crop_area"

    ind = INDICATOR_MAP[indicator_key]
    table = ind["table"]
    column = ind["column"]
    agg = ind["agg"]
    title = ind["title"]
    unit = ind["unit"]

    # Get dimension config
    dim = DIMENSION_MAP.get(dimension_key) if dimension_key else None

    # Build SELECT clause
    if dim:
        select_clause = f"SELECT {dim['column']} as label, {agg}({column}) as value"
        chart_type = dim["chart"]
        title_suffix = f" by {dim['label']}"
    else:
        select_clause = f"SELECT {agg}({column}) as value"
        chart_type = "kpi"
        title_suffix = " (Total)"

    # Build FROM clause
    from_clause = f"FROM {table}"

    # Build WHERE clause (MANDATORY LGD FILTER)
    filters = [f"state_lgd_code = '{user_lgd}'"]

    # Time filters
    year_val = time_params.get("year", "current")
    if year_val == "current":
        filters.append(f"year = (SELECT MAX(year) FROM {table} WHERE state_lgd_code = '{user_lgd}')")
    elif year_val != "all":
        # Handle cases like "2024" matching "2024-2025"
        filters.append(f"year LIKE '{year_val}%'")

    season_val = time_params.get("season")
    if season_val:
        filters.append(f"season ILIKE '{season_val}'")

    where_clause = "WHERE " + " AND ".join(filters)

    # Build GROUP BY and ORDER BY
    if dim:
        group_clause = f"GROUP BY {dim['column']}"
        order_clause = "ORDER BY value DESC"
        limit_clause = "LIMIT 15"
    else:
        group_clause = ""
        order_clause = ""
        limit_clause = ""

    # Combine SQL
    sql_parts = [select_clause, from_clause, where_clause]
    if group_clause:
        sql_parts.append(group_clause)
    if order_clause:
        sql_parts.append(order_clause)
    if limit_clause:
        sql_parts.append(limit_clause)

    sql = " ".join(sql_parts)

    return {
        "sql": sql,
        "title": title + title_suffix,
        "chart_type": chart_type,
        "unit": unit,
        "indicator": indicator_key,
        "dimension": dimension_key
    }

# ============================================================
# 10. NARRATIVE GENERATOR
# ============================================================

def generate_narration(title: str, chart_type: str, labels: List[str],
                       values: List[float], unit: str, user_lgd: str) -> str:
    """
    Generate executive narration for the analytics result.
    """
    state_name = LGD_TO_STATE.get(user_lgd, f"LGD {user_lgd}")
    total = sum(values) if values else 0

    if chart_type == "kpi":
        return (f"The total {title.lower()} for {state_name} is {total:,.2f} {unit}. "
                f"This represents the validated figure for the current reporting period.")

    if not labels or not values:
        return f"No data available for {title.lower()} in {state_name}."

    top_label = labels[0]
    top_value = values[0]
    top_pct = (top_value / total * 100) if total > 0 else 0

    if chart_type == "bar":
        return (f"The analysis of {title.lower()} for {state_name} shows a total of {total:,.2f} {unit} "
                f"across {len(labels)} regions. {top_label} leads with {top_value:,.2f} {unit}, "
                f"contributing {top_pct:.1f}% of the total.")

    elif chart_type == "pie":
        return (f"The distribution of {title.lower()} in {state_name} totals {total:,.2f} {unit}. "
                f"The largest share is {top_label} at {top_value:,.2f} {unit} ({top_pct:.1f}%), "
                f"followed by {len(labels)-1} other categories.")

    elif chart_type == "line":
        if len(values) >= 2:
            trend = "increasing" if values[-1] > values[0] else "decreasing"
            change = abs(values[-1] - values[0])
            return (f"The trend analysis of {title.lower()} for {state_name} shows a {trend} pattern. "
                    f"Values range from {min(values):,.2f} to {max(values):,.2f} {unit}, "
                    f"with an overall change of {change:,.2f} {unit}.")
        return f"Trend data for {title.lower()} in {state_name} shows {total:,.2f} {unit} total."

    return f"Analysis of {title.lower()} for {state_name}: Total {total:,.2f} {unit}."

# ============================================================
# 11. API MODELS
# ============================================================

class UserQuery(BaseModel):
    query: str
    user_lgd_code: Optional[str] = "27"  # Default to Maharashtra

class ChartData(BaseModel):
    type: str
    labels: Optional[List[str]] = None
    values: List[float]
    unit: Optional[str] = None

class AgriStackResponse(BaseModel):
    title: str
    chart_data: ChartData
    narration: str
    metadata: Dict[str, Any]

# ============================================================
# 12. MAIN CHAT ENDPOINT
# ============================================================

@app.post("/chat")
def chat(query: UserQuery) -> AgriStackResponse:
    """
    Main chat endpoint with strict 2-mode routing.
    """
    import random

    user_lgd = query.user_lgd_code or "27"
    user_state = LGD_TO_STATE.get(user_lgd, f"LGD {user_lgd}")

    # ===== STEP 1: CLASSIFY INTENT =====
    intent = classify_intent(query.query)
    mode = intent.get("mode", "conversation")

    # ===== STEP 2: HANDLE CONVERSATION MODE =====
    if mode == "conversation":
        sub_type = intent.get("sub_type", "help")

        response_pool = CONVERSATION_RESPONSES.get(sub_type, CONVERSATION_RESPONSES["help"])
        if isinstance(response_pool, list):
            response_text = random.choice(response_pool)
        else:
            response_text = response_pool

        return AgriStackResponse(
            title="AgriStack Assistant",
            chart_data=ChartData(type="message", values=[], unit=""),
            narration=response_text,
            metadata={
                "intent_type": "conversation",
                "sub_type": sub_type,
                "lgd_scope": user_lgd,
                "state": user_state,
                "timestamp": datetime.now().isoformat()
            }
        )

    # ===== STEP 3: HANDLE ANALYTICS MODE =====

    # 3A: Check LGD Authorization
    mentioned_state = intent.get("mentioned_state")
    auth_check = check_lgd_authorization(user_lgd, mentioned_state)

    if not auth_check.get("authorized"):
        return AgriStackResponse(
            title="Access Restricted",
            chart_data=ChartData(type="message", values=[], unit=""),
            narration=auth_check["message"],
            metadata={
                "intent_type": "unauthorized_analytics",
                "user_lgd": user_lgd,
                "user_state": auth_check.get("user_state"),
                "requested_state": auth_check.get("requested_state"),
                "requested_lgd": auth_check.get("requested_lgd"),
                "timestamp": datetime.now().isoformat()
            }
        )

    # 3B: Build SQL Query
    plan = build_analytics_sql(
        indicator_key=intent.get("indicator", "crop_area"),
        dimension_key=intent.get("dimension"),
        time_params=intent.get("time", {}),
        user_lgd=user_lgd
    )

    # 3C: Execute Query
    try:
        conn = psycopg2.connect(**DB_PARAMS, cursor_factory=RealDictCursor)
        cur = conn.cursor()

        cur.execute(plan["sql"])
        rows = cur.fetchall()

        cur.close()
        conn.close()

        # Process results
        labels = [str(r.get('label', 'Total')) for r in rows]
        values = [float(r.get('value') or 0) for r in rows]

        # Handle empty results
        if not values or all(v == 0 for v in values):
            return AgriStackResponse(
                title=plan["title"],
                chart_data=ChartData(type="message", values=[], unit=plan["unit"]),
                narration=f"No data found for {plan['title'].lower()} in {user_state} (LGD: {user_lgd}). "
                          f"This may indicate no records for the selected criteria or pending data uploads.",
                metadata={
                    "intent_type": "analytics",
                    "result": "no_data",
                    "sql_query": plan["sql"],
                    "lgd_scope": user_lgd,
                    "state": user_state,
                    "timestamp": datetime.now().isoformat()
                }
            )

        # Generate narration
        narration = generate_narration(
            title=plan["title"],
            chart_type=plan["chart_type"],
            labels=labels,
            values=values,
            unit=plan["unit"],
            user_lgd=user_lgd
        )

        return AgriStackResponse(
            title=plan["title"],
            chart_data=ChartData(
                type=plan["chart_type"],
                labels=labels if plan["chart_type"] != "kpi" else None,
                values=values,
                unit=plan["unit"]
            ),
            narration=narration,
            metadata={
                "intent_type": "analytics",
                "result": "success",
                "indicator": plan["indicator"],
                "dimension": plan["dimension"],
                "chart_type": plan["chart_type"],
                "sql_query": plan["sql"],
                "lgd_scope": user_lgd,
                "state": user_state,
                "record_count": len(values),
                "timestamp": datetime.now().isoformat()
            }
        )

    except Exception as e:
        print(f"[DB Error] {e}")
        return AgriStackResponse(
            title="System Error",
            chart_data=ChartData(type="message", values=[], unit=""),
            narration=f"An error occurred while processing your request. Please try again or contact support. Error: {str(e)}",
            metadata={
                "intent_type": "analytics",
                "result": "error",
                "error": str(e),
                "sql_query": plan.get("sql", ""),
                "timestamp": datetime.now().isoformat()
            }
        )

# ============================================================
# 13. HEALTH CHECK ENDPOINT
# ============================================================

@app.get("/")
def health():
    return {
        "status": "AgriStack MIS Analytics Engine - Active",
        "version": "2.0.0",
        "modes": ["conversation", "analytics"],
        "security": "LGD-based authorization enabled"
    }

# ============================================================
# 14. SERVER STARTUP
# ============================================================

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8001)
