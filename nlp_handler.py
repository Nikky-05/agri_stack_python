import random
import re
from typing import Dict, Any, Optional, List
from config import (
    CONVERSATION_RESPONSES, INDICATORS, DIMENSIONS,
    DISTRIBUTION_KEYWORDS, CROP_NAMES, SEASON_NAMES
)


class NLPHandler:
    """Comprehensive NLP Handler for AgriStack Analytics - Dynamic & Accurate"""

    def __init__(self, model_name: str = "llama3:latest"):
        self.model = model_name
        self.ollama_url = "http://localhost:11434/api/generate"
        self._verify_model()

    def _verify_model(self):
        """Check if model exists"""
        try:
            import requests
            res = requests.get("http://localhost:11434/api/tags", timeout=2)
            models = [m['name'] for m in res.json().get('models', [])]
            if self.model not in models and "llama3:latest" in models:
                self.model = "llama3:latest"
        except:
            pass

    def _query_llm(self, prompt: str, timeout: int = 15) -> str:
        """Query Ollama LLM"""
        try:
            import requests
            response = requests.post(
                self.ollama_url,
                json={"model": self.model, "prompt": prompt, "stream": False},
                timeout=timeout
            )
            return response.json().get("response", "").strip()
        except Exception as e:
            print(f"LLM Error: {e}")
            return ""

    def classify_intent(self, query: str) -> Dict[str, Any]:
        """Classify user query into structured intent - DYNAMIC & ACCURATE"""

        q = query.lower().strip()
        words = set(re.findall(r'\b\w+\b', q))

        # 1. Check for conversation mode (greetings, help)
        greetings = {"hi", "hello", "hey", "greetings", "hellow", "helo", "hii", "hai", "namaste"}
        help_words = {"help", "guide", "what can"}

        if words & greetings and len(words) <= 5:
            return {"mode": "conversation", "sub_type": "greeting"}
        if words & help_words and len(words) <= 8:
            return {"mode": "conversation", "sub_type": "help"}

        # 2. Detect specific year filter FIRST
        year_filter = self._detect_year(q)

        # 3. Detect dimension (how to group data) - IMPORTANT for correct visualization
        dimension = self._detect_dimension(q)

        # 4. Detect indicator (what metric to show)
        indicator = self._detect_indicator(q)

        # 5. Detect filters
        crop_filter = self._detect_crop(q)
        season_filter = self._detect_season(q)

        # 6. Detect comparison type
        comparison_type = self._detect_comparison(q)

        # 7. Detect top N
        top_n = self._detect_top_n(q)

        # 8. Determine intent type
        if comparison_type:
            intent_type = "comparison"
        elif dimension:
            intent_type = "distribution"
        else:
            intent_type = "summary"

        return {
            "mode": "analytics",
            "indicator": indicator,
            "dimension": dimension,
            "crop_filter": crop_filter,
            "season_filter": season_filter,
            "year_filter": year_filter,
            "comparison_type": comparison_type,
            "top_n": top_n,
            "intent_type": intent_type
        }

    def _detect_indicator(self, q: str) -> str:
        """Detect which indicator/metric is being asked - PRIORITY BASED"""

        # PRIORITY 1: Check for specific phrases first (most specific wins)
        priority_mappings = [
            # Pending/Validation queries
            (["pending validation", "pending approval", "not approved", "awaiting approval",
              "validation pending", "crops pending", "pending crops", "under validation"], "pending_validation"),

            # Cultivated/Surveyed Area queries (from cultivated table)
            (["cultivated area", "cultivated summary", "cultivation summary", "cultivated land",
              "total surveyed area", "surveyed area", "survey area", "agricultural area"], "surveyed_area"),

            # Survey Progress queries (from aggregate table)
            (["survey progress", "plots surveyed", "surveyed plots", "survey status",
              "survey completed", "surveyed so far"], "surveyed_plots"),

            # Irrigation queries
            (["irrigated area", "irrigation area", "irrigated land"], "irrigated_area"),
            (["unirrigated area", "unirrigated land", "rainfed area"], "unirrigated_area"),
            (["irrigated vs unirrigated", "irrigation comparison"], "irrigated_area"),

            # Fallow queries
            (["fallow area", "fallow land", "uncultivated"], "fallow_area"),

            # Farmer queries
            (["farmer count", "number of farmers", "total farmers", "registered farmers",
              "how many farmers"], "farmers"),

            # Plot queries
            (["total plots", "number of plots", "plot count"], "total_plots"),
            (["assigned plots", "plots assigned"], "assigned_plots"),

            # Crop area queries
            (["crop area", "approved area", "approved crop", "crop status"], "crop_area"),
            (["closed area", "closed crop", "crop closed"], "crop_area_closed"),

            # Surveyor queries
            (["surveyors", "surveyor count", "number of surveyors"], "surveyors"),

            # Survey approval queries
            (["survey approved", "approved surveys", "surveys approved"], "survey_approved"),
            (["under review", "pending review", "surveys pending"], "survey_under_review"),
        ]

        for keywords, indicator in priority_mappings:
            for kw in keywords:
                if kw in q:
                    return indicator

        # PRIORITY 2: Keyword scoring for remaining cases
        scores = {}
        for key, meta in INDICATORS.items():
            score = 0
            for kw in meta["keywords"]:
                if kw in q:
                    score += len(kw.split()) * 2  # Weight by phrase length
            scores[key] = score

        best = max(scores, key=scores.get)
        if scores[best] > 0:
            return best

        # PRIORITY 3: Default based on context
        if "survey" in q:
            return "surveyed_plots"
        if "cultivat" in q:
            return "surveyed_area"
        if "farmer" in q:
            return "farmers"
        if "plot" in q:
            return "total_plots"

        return "crop_area"  # Final default

    def _detect_dimension(self, q: str) -> Optional[str]:
        """Detect grouping dimension - ACCURATE DETECTION"""

        # Check explicit dimension keywords
        dimension_patterns = [
            # District
            (["district-wise", "district wise", "by district", "districtwise",
              "across districts", "each district", "per district"], "district"),

            # Crop
            (["crop-wise", "crop wise", "by crop", "cropwise", "each crop",
              "per crop", "which crops", "which crop", "top crops"], "crop"),

            # Season
            (["season-wise", "season wise", "by season", "seasonwise",
              "each season", "per season", "which season"], "season"),

            # Year
            (["year-wise", "year wise", "by year", "yearwise", "yearly",
              "annual", "each year", "per year", "which year"], "year"),

            # Village
            (["village-wise", "village wise", "by village", "villagewise"], "village"),

            # Irrigation
            (["irrigation-wise", "by irrigation", "irrigation source"], "irrigation"),
        ]

        for keywords, dimension in dimension_patterns:
            for kw in keywords:
                if kw in q:
                    return dimension

        # Check DIMENSIONS config
        for key, meta in DIMENSIONS.items():
            for kw in meta["keywords"]:
                if kw in q:
                    return key

        # Infer dimension from context
        if any(w in q for w in DISTRIBUTION_KEYWORDS):
            if "crop" in q:
                return "crop"
            if "district" in q:
                return "district"
            if "season" in q:
                return "season"
            if "year" in q:
                return "year"

        return None

    def _detect_crop(self, q: str) -> Optional[str]:
        """Detect specific crop name"""
        for crop in CROP_NAMES:
            if crop in q:
                return crop.title()
        return None

    def _detect_season(self, q: str) -> Optional[str]:
        """Detect season filter"""
        for season in SEASON_NAMES:
            if season in q:
                return season.title()
        return None

    def _detect_year(self, q: str) -> Optional[str]:
        """Detect specific year filter like 2021-2022, 2022-23, etc."""

        # Match patterns like "2021-2022", "2022-23", "2021-22"
        patterns = [
            r'(\d{4}-\d{4})',  # 2021-2022
            r'(\d{4}-\d{2})',  # 2021-22
        ]

        for pattern in patterns:
            match = re.search(pattern, q)
            if match:
                year_str = match.group(1)
                # Normalize to full format (2021-2022)
                if len(year_str) == 7:  # 2021-22 format
                    first_year = year_str[:4]
                    second_year = str(int(first_year) + 1)
                    return f"{first_year}-{second_year}"
                return year_str

        # Check for single year mentions like "year 2021" or "in 2023"
        single_year = re.search(r'\b(202[0-9]|2019|2018)\b', q)
        if single_year:
            year = single_year.group(1)
            next_year = str(int(year) + 1)
            return f"{year}-{next_year}"

        return None

    def _detect_top_n(self, q: str) -> int:
        """Detect top N requests"""
        match = re.search(r'top\s*(\d+)', q)
        if match:
            return int(match.group(1))
        if "top 5" in q or "top five" in q:
            return 5
        if "top 10" in q or "top ten" in q:
            return 10
        if "top 3" in q or "top three" in q:
            return 3
        return 10  # Default

    def _detect_comparison(self, q: str) -> Optional[str]:
        """Detect comparison queries"""

        comparison_patterns = [
            (["irrigated vs unirrigated", "irrigated and unirrigated",
              "irrigated versus unirrigated", "compare irrigated"], "irrigated_vs_unirrigated"),

            (["assigned vs surveyed", "assigned and surveyed", "assign vs survey",
              "assigned versus surveyed"], "assigned_vs_surveyed"),

            (["approved vs closed", "approved and closed",
              "approved versus closed"], "approved_vs_closed"),

            (["surveyable vs surveyed", "surveyable and surveyed"], "surveyable_vs_surveyed"),

            (["rabi vs kharif", "rabi and kharif", "kharif vs rabi",
              "rabi versus kharif", "compare rabi", "compare kharif"], "rabi_vs_kharif"),

            (["fallow vs cultivated", "fallow and cultivated"], "fallow_vs_cultivated"),
        ]

        for keywords, comparison in comparison_patterns:
            for kw in keywords:
                if kw in q:
                    return comparison

        return None

    def generate_narration(self, data: Dict[str, Any], user_state: str, original_query: str) -> str:
        """Generate detailed narration with insights"""

        # Try LLM first
        llm_narration = self._generate_llm_narration(data, user_state, original_query)
        if llm_narration and 30 < len(llm_narration.split()) < 150:
            return llm_narration

        # Fallback to template narration
        return self._generate_template_narration(data, user_state)

    def _generate_llm_narration(self, data: Dict, user_state: str, query: str) -> str:
        """Generate narration using LLM"""

        prompt = f"""Generate a professional analytical narration for this agriculture data.
Write 60-100 words with insights.

Query: "{query}"
State: {user_state}
Title: {data.get('title', '')}
Total: {sum(data.get('values', [0]))} {data.get('unit', '')}
Categories: {data.get('labels', [])}
Values: {data.get('values', [])}

Requirements:
1. Start with context about the data
2. Highlight the key finding (total or top item)
3. Provide one analytical insight or pattern
4. Keep it professional and data-driven
5. Do NOT use bullet points

Write the narration now:"""

        return self._query_llm(prompt, timeout=20)

    def _generate_template_narration(self, data: Dict, user_state: str) -> str:
        """Generate template-based narration"""

        title = data.get("title", "Data Analysis")
        unit = data.get("unit", "")
        values = data.get("values", [])
        labels = data.get("labels", [])
        total = sum(values) if values else 0
        crop_filter = data.get("crop_filter", "")
        season_filter = data.get("season_filter", "")
        year_filter = data.get("year_filter", "")
        dimension = data.get("dimension", "")

        if not values:
            return f"No data available for the requested analysis in {user_state}."

        # KPI (single value) narration
        if len(values) == 1:
            narration = f"The {title.lower()} for {user_state}"
            if year_filter:
                narration += f" in {year_filter}"
            if season_filter:
                narration += f" ({season_filter} season)"
            narration += f" stands at {total:,.2f} {unit}."

            # Add extra stats if available
            extras = []
            if data.get('farmers_count'):
                extras.append(f"{data['farmers_count']:,} farmers")
            if data.get('plots_count'):
                extras.append(f"{data['plots_count']:,} plots")
            if data.get('unique_crops'):
                extras.append(f"{data['unique_crops']} crop varieties")

            if extras:
                narration += f" This encompasses {', '.join(extras)}."

            return narration

        # Distribution narration
        top_label = labels[0] if labels else "Unknown"
        top_value = values[0] if values else 0
        top_pct = (top_value / total * 100) if total > 0 else 0

        narration = f"Analysis of {title.lower()} in {user_state}"
        if year_filter:
            narration += f" for {year_filter}"
        if season_filter:
            narration += f" ({season_filter})"
        narration += f" reveals a total of {total:,.2f} {unit}."

        narration += f" {top_label} leads with {top_value:,.2f} {unit} ({top_pct:.1f}% share)."

        # Add pattern insight
        if len(values) >= 3:
            top3_total = sum(values[:3])
            top3_pct = (top3_total / total * 100) if total > 0 else 0
            if top3_pct > 60:
                narration += f" The top 3 {dimension.lower() if dimension else 'categories'} account for {top3_pct:.1f}% of the total, indicating concentration."
            else:
                narration += f" Distribution appears relatively balanced across {dimension.lower() if dimension else 'categories'}."

        return narration

    def get_conversation_response(self, sub_type: str, original_query: str = "") -> str:
        """Generate conversation response"""

        if sub_type == "greeting":
            prompt = f"""User said: "{original_query}"
You are AgriStack MIS Assistant. Generate a warm greeting (2 sentences).
Mention: crop data, farmer statistics, survey progress, district analysis.
Be professional and helpful."""
        else:
            prompt = f"""User asked: "{original_query}"
You are AgriStack MIS Assistant. Provide helpful guidance (2-3 sentences).
Suggest queries about: survey status, farmer registration, crop area, irrigation, district comparisons."""

        response = self._query_llm(prompt, timeout=10)
        if response:
            return response

        return random.choice(CONVERSATION_RESPONSES.get(sub_type, CONVERSATION_RESPONSES["help"]))


# Singleton instance
nlp_handler = NLPHandler()
