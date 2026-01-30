import os
from dotenv import load_dotenv

load_dotenv()

# Database Config
DB_HOST = os.getenv("DB_HOST", "localhost")
DB_PORT = os.getenv("DB_PORT", "5432")
DB_USER = os.getenv("DB_USER", "postgres")
DB_PASSWORD = os.getenv("DB_PASSWORD", "NKpallotti@99")
DB_NAME = os.getenv("DB_NAME", "exam_db")

LGD_TO_STATE = {
    "27": "Maharashtra",
    "09": "Uttar Pradesh",
    "24": "Gujarat",
    "10": "Bihar",
    "33": "Tamil Nadu",
    "29": "Karnataka"
}

# ============================================================
# COMPREHENSIVE ANALYTICS REGISTRY
# ============================================================

# CSV File Mapping
CSV_FILES = {
    "crop_area": "data_for_testing/data-1768987385851mhCropArea.csv",
    "aggregate": "data_for_testing/data-1768987329067mhAgreegatedData.csv",
    "cultivated": "data_for_testing/data-1768987427993mhCultivatedData.csv"
}

# ============================================================
# INDICATORS - What metrics can be queried
# ============================================================
INDICATORS = {
    # CROP AREA INDICATORS
    "crop_area": {
        "table": "crop_area",
        "column": "crop_area_approved",
        "title": "Approved Crop Area",
        "unit": "Hectares",
        "keywords": ["crop area", "approved area", "crop status", "cultivation", "cultivated", "area"]
    },
    "crop_area_closed": {
        "table": "crop_area",
        "column": "crop_area_closed",
        "title": "Closed Crop Area",
        "unit": "Hectares",
        "keywords": ["closed area", "crop closed", "closed crop"]
    },
    "pending_validation": {
        "table": "crop_area",
        "column": "pending",  # Special calculated column
        "title": "Crops Pending Validation",
        "unit": "Hectares",
        "keywords": ["pending validation", "pending approval", "not approved", "awaiting approval", "pending crops", "under validation", "validation pending"]
    },
    "farmers": {
        "table": "crop_area",
        "column": "no_of_farmers",
        "title": "Registered Farmers",
        "unit": "Farmers",
        "keywords": ["farmer", "farmers", "farmer count", "number of farmers", "total farmers"]
    },
    "plots": {
        "table": "crop_area",
        "column": "no_of_plots",
        "title": "Number of Plots",
        "unit": "Plots",
        "keywords": ["plots recorded", "crop plots", "number of plots"]
    },

    # SURVEY/AGGREGATE INDICATORS
    "total_plots": {
        "table": "aggregate",
        "column": "total_plots",
        "title": "Total Plots",
        "unit": "Plots",
        "keywords": ["total plots", "all plots"]
    },
    "assigned_plots": {
        "table": "aggregate",
        "column": "total_assigned_plots",
        "title": "Assigned Plots for Survey",
        "unit": "Plots",
        "keywords": ["assigned plots", "plots assigned", "assigned for survey"]
    },
    "surveyed_plots": {
        "table": "aggregate",
        "column": "total_plots_surveyed",
        "title": "Plots Surveyed",
        "unit": "Plots",
        "keywords": ["surveyed plots", "plots surveyed", "survey completed", "surveyed so far", "survey progress", "survey status"]
    },
    "unsurveyed_plots": {
        "table": "aggregate",
        "column": "total_plots_unable_to_survey",
        "title": "Unable to Survey Plots",
        "unit": "Plots",
        "keywords": ["unable to survey", "unsurveyed", "not surveyed", "unable"]
    },
    "survey_approved": {
        "table": "aggregate",
        "column": "total_survey_approved",
        "title": "Surveys Approved",
        "unit": "Surveys",
        "keywords": ["survey approved", "approved surveys", "approval"]
    },
    "survey_under_review": {
        "table": "aggregate",
        "column": "total_survey_under_review",
        "title": "Surveys Under Review",
        "unit": "Surveys",
        "keywords": ["under review", "review", "pending review"]
    },
    "today_survey": {
        "table": "aggregate",
        "column": "total_today_survey",
        "title": "Today's Survey Count",
        "unit": "Surveys",
        "keywords": ["today survey", "today's count", "daily survey"]
    },
    "surveyors": {
        "table": "aggregate",
        "column": "total_no_of_surveyors",
        "title": "Number of Surveyors",
        "unit": "Surveyors",
        "keywords": ["surveyors", "surveyor count"]
    },

    # CULTIVATED SUMMARY INDICATORS
    "surveyed_area": {
        "table": "cultivated",
        "column": "total_surveyed_area",
        "title": "Total Surveyed Area",
        "unit": "Hectares",
        "keywords": ["surveyed area", "agricultural area", "surveyed agricultural", "survey summary", "overall survey", "total survey area", "survey area"]
    },
    "surveyable_area": {
        "table": "cultivated",
        "column": "total_surveyable_area",
        "title": "Total Surveyable Area",
        "unit": "Hectares",
        "keywords": ["surveyable area", "surveyable"]
    },
    "fallow_area": {
        "table": "cultivated",
        "column": "total_fallow_area",
        "title": "Fallow Area",
        "unit": "Hectares",
        "keywords": ["fallow", "fallow area", "fallow land"]
    },
    "na_area": {
        "table": "cultivated",
        "column": "total_na_area",
        "title": "NA Area",
        "unit": "Hectares",
        "keywords": ["na area", "not available", "na"]
    },
    "harvested_area": {
        "table": "cultivated",
        "column": "total_harvested_area",
        "title": "Harvested Area",
        "unit": "Hectares",
        "keywords": ["harvested", "harvest area", "harvested area"]
    },
    "irrigated_area": {
        "table": "cultivated",
        "column": "total_irrigated_area",
        "title": "Irrigated Area",
        "unit": "Hectares",
        "keywords": ["irrigated", "irrigation", "irrigated area"]
    },
    "unirrigated_area": {
        "table": "cultivated",
        "column": "total_unirrigated_area",
        "title": "Unirrigated Area",
        "unit": "Hectares",
        "keywords": ["unirrigated", "rainfed", "unirrigated area"]
    },
    "perennial_area": {
        "table": "cultivated",
        "column": "total_perennial_crop_area",
        "title": "Perennial Crop Area",
        "unit": "Hectares",
        "keywords": ["perennial", "perennial crop"]
    },
    "biennial_area": {
        "table": "cultivated",
        "column": "total_biennial_crop_area",
        "title": "Biennial Crop Area",
        "unit": "Hectares",
        "keywords": ["biennial", "biennial crop"]
    },
    "seasonal_area": {
        "table": "cultivated",
        "column": "total_seasonal_crop_area",
        "title": "Seasonal Crop Area",
        "unit": "Hectares",
        "keywords": ["seasonal", "seasonal crop"]
    }
}

# ============================================================
# DIMENSIONS - How to group/breakdown data
# ============================================================
DIMENSIONS = {
    "district": {
        "column": "district_lgd_code",
        "title": "District",
        "keywords": ["district", "district-wise", "by district", "districts"]
    },
    "season": {
        "column": "season",
        "title": "Season",
        "keywords": ["season", "season-wise", "by season", "kharif", "rabi", "summer", "seasonal"]
    },
    "crop": {
        "column": "crop_name_eng",
        "title": "Crop",
        "keywords": ["crop", "crop-wise", "by crop", "crops", "top crops", "top 5 crops"]
    },
    "year": {
        "column": "year",
        "title": "Year",
        "keywords": ["year", "year-wise", "by year", "yearly", "annual"]
    },
    "irrigation": {
        "column": "irrigation_source",
        "title": "Irrigation Source",
        "keywords": ["irrigation", "irrigation source", "water source", "irrigation-wise"]
    },
    "village": {
        "column": "village_lgd_code",
        "title": "Village",
        "keywords": ["village", "village-wise", "by village"]
    }
}

# Keywords that trigger comparison/distribution
DISTRIBUTION_KEYWORDS = [
    "distribution", "breakdown", "split", "comparison", "compare",
    "share", "by", "wise", "top", "highest", "lowest", "which"
]

# Crop names for detection
CROP_NAMES = [
    "wheat", "rice", "maize", "corn", "sorghum", "jowar", "bajra", "pearl millet",
    "chickpea", "gram", "chana", "pigeon pea", "tur", "arhar", "lentil", "moong", "urad",
    "sugarcane", "cotton", "soybean", "groundnut", "mustard", "sunflower", "safflower",
    "onion", "potato", "tomato", "brinjal", "chilli", "turmeric", "ginger",
    "banana", "mango", "orange", "grapes", "pomegranate", "guava", "papaya",
    "ragi", "barley", "oats", "sesame", "castor"
]

# Season names
SEASON_NAMES = ["kharif", "rabi", "summer", "zaid"]

# Conversation responses (fallback)
CONVERSATION_RESPONSES = {
    "greeting": [
        "Hello! I'm your AgriStack Analytics Assistant. Ask me about crop data, survey progress, farmer statistics, or land usage.",
    ],
    "help": [
        "I can help with: crop area analysis, survey progress, farmer counts, irrigation data, district comparisons, and seasonal trends."
    ]
}
