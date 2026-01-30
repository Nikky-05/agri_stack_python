import os
from dotenv import load_dotenv

load_dotenv()

# Database Config
DB_HOST = os.getenv("DB_HOST", "localhost")
DB_PORT = os.getenv("DB_PORT", "5432")
DB_USER = os.getenv("DB_USER", "postgres")
DB_PASSWORD = os.getenv("DB_PASSWORD", "NKpallotti@99")
DB_NAME = os.getenv("DB_NAME", "exam_db")

LGD_TO_STATE = {"27": "Maharashtra", "09": "Uttar Pradesh", "24": "Gujarat"}

# ============================================================
# MASTER ANALYTICS REGISTRY (Professional Metadata)
# ============================================================

INDICATORS = {
    "crop_area": {
        "table": "crop_area_data",
        "column": "crop_area_approved",
        "title": "Approved Crop Area",
        "unit": "Hectares",
        "keywords": ["area", "hectare", "land", "acreage"]
    },
    "farmers": {
        "table": "crop_area_data",
        "column": "no_of_farmers",
        "title": "Registered Farmers",
        "unit": "Farmers",
        "keywords": ["farmer", "registration", "beneficiaries", "total farmers", "enrolled"]
    },
    "survey_progress": {
        "table": "aggregate_summary_data",
        "column": "total_plots_surveyed",
        "title": "Survey Progress",
        "unit": "Plots",
        "keywords": ["survey", "plot", "progress", "completion", "surveyed", "status"]
    },
    "irrigation": {
        "table": "cultivated_summary_data",
        "column": "total_irrigated_area",
        "title": "Irrigation Analysis",
        "unit": "Hectares",
        "keywords": ["irrigation", "irrigated", "source", "water", "unirrigated"]
    }
}

DIMENSIONS = {
    "district": {
        "column": "district_lgd_code",
        "title": "District",
        "keywords": ["district", "region", "location", "area wise", "district-wise", "lgd"]
    },
    "season": {
        "column": "season",
        "title": "Season",
        "keywords": ["season", "time period", "kharif", "rabi", "summer", "annual"]
    },
    "category": {
        "column": "crop_name_eng",
        "title": "Crop Category",
        "keywords": ["category", "crop type", "variety", "commodity", "kind of crop"]
    },
    "gender": {
        "column": "gender", # This doesn't exist yet but we'll use it for intent detection
        "title": "Gender",
        "keywords": ["gender", "sex", "male", "female", "men", "women"]
    }
}

# Words that force a "Breakdown/Distribution" intent even if no dimension is explicitly found
DISTRIBUTION_KEYWORDS = ["distribution", "breakdown", "split", "ratio", "comparison", "share", "by", "wise", "category"]


CSV_FILES = {
    "aggregate": "data_for_testing/data-1768987329067mhAgreegatedData.csv",
    "crop_area": "data_for_testing/data-1768987385851mhCropArea.csv",
    "cultivated": "data_for_testing/data-1768987427993mhCultivatedData.csv"
}

CONVERSATION_RESPONSES = {
    "greeting": [
        "Hello! I'm your AgriStack Assistant. How can I help you today?",
        "Hi there! Welcome to AgriStack MIS. Ask me about crops, farmers, or survey progress.",
        "Hello! Ready to help you with agriculture analytics. What would you like to know?"
    ],
    "help": [
        "I can help you analyze agriculture data. Try asking: 'Show farmers by category' or 'District-wise crop area'.",
        "Try: 'Show farmers by category' or 'District-wise survey progress'."
    ]
}
