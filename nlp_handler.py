import random
import re
import json
import requests
from typing import Dict, Any, Optional, List
from config import (
    CONVERSATION_RESPONSES, INDICATORS, DIMENSIONS,
    DISTRIBUTION_KEYWORDS, CROP_NAMES, SEASON_NAMES
)


class NLPHandler:
    """Comprehensive NLP Handler for AgriStack Analytics"""

    def __init__(self, model_name: str = "llama3:latest"):
        self.model = model_name
        self.ollama_url = "http://localhost:11434/api/generate"
        self._verify_model()

    def _verify_model(self):
        """Check if model exists"""
        try:
            res = requests.get("http://localhost:11434/api/tags", timeout=2)
            models = [m['name'] for m in res.json().get('models', [])]
            if self.model not in models and "llama3:latest" in models:
                self.model = "llama3:latest"
        except:
            pass

    def _query_llm(self, prompt: str, timeout: int = 15) -> str:
        """Query Ollama LLM"""
        try:
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
        """Classify user query into structured intent"""

        q = query.lower().strip()
        words = set(re.findall(r'\b\w+\b', q))

        # Check for conversation mode
        greetings = {"hi", "hello", "hey", "greetings", "hellow", "helo", "hii", "hai", "namaste"}
        help_words = {"help", "guide", "how", "what can"}

        if words & greetings and len(words) <= 5:
            return {"mode": "conversation", "sub_type": "greeting"}
        if words & help_words and len(words) <= 10:
            return {"mode": "conversation", "sub_type": "help"}

        # Check for overview/dashboard queries
        overview_keywords = {"overview", "dashboard", "summary", "statistics", "stats", "overall"}
        if words & overview_keywords:
            return {"mode": "analytics", "indicator": "overview", "intent_type": "overview"}

        # Detect comparison type
        comparison_type = self._detect_comparison(q)

        # Detect indicator (what metric)
        indicator = self._detect_indicator(q)

        # Detect dimension (grouping)
        dimension = self._detect_dimension(q)

        # Detect crop filter
        crop_filter = self._detect_crop(q)

        # Detect season filter
        season_filter = self._detect_season(q)

        # Detect top N
        top_n = self._detect_top_n(q)

        # Detect specific year filter
        year_filter = self._detect_year(q)

        return {
            "mode": "analytics",
            "indicator": indicator,
            "dimension": dimension,
            "crop_filter": crop_filter,
            "season_filter": season_filter,
            "year_filter": year_filter,
            "comparison_type": comparison_type,
            "top_n": top_n,
            "intent_type": "comparison" if comparison_type else ("distribution" if dimension else "summary")
        }

    def _detect_year(self, q: str) -> Optional[str]:
        """Detect specific year filter like 2021-2022, 2022-2023, etc."""

        # Match patterns like "2021-2022", "2022-23", "2021-22"
        year_patterns = [
            r'(\d{4}-\d{4})',  # 2021-2022
            r'(\d{4}-\d{2})',  # 2021-22
        ]

        for pattern in year_patterns:
            match = re.search(pattern, q)
            if match:
                year_str = match.group(1)
                # Normalize to full format (2021-2022)
                if len(year_str) == 7:  # 2021-22 format
                    first_year = year_str[:4]
                    second_year = str(int(first_year) + 1)
                    return f"{first_year}-{second_year}"
                return year_str

        # Check for single year mentions
        single_year = re.search(r'\b(202[0-9]|2019|2018)\b', q)
        if single_year:
            year = single_year.group(1)
            next_year = str(int(year) + 1)
            return f"{year}-{next_year}"

        return None

    def _detect_indicator(self, q: str) -> str:
        """Detect which indicator/metric is being asked"""

        scores = {}
        for key, meta in INDICATORS.items():
            score = 0
            for kw in meta["keywords"]:
                if kw in q:
                    score += len(kw.split())  # Longer matches score higher
            scores[key] = score

        best = max(scores, key=scores.get)
        return best if scores[best] > 0 else "crop_area"

    def _detect_dimension(self, q: str) -> Optional[str]:
        """Detect grouping dimension"""

        for key, meta in DIMENSIONS.items():
            for kw in meta["keywords"]:
                if kw in q:
                    return key

        # Check for distribution keywords without explicit dimension
        if any(w in q for w in DISTRIBUTION_KEYWORDS):
            if "crop" in q:
                return "crop"
            if "season" in q or any(s in q for s in SEASON_NAMES):
                return "season"
            if "district" in q:
                return "district"

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

    def _detect_top_n(self, q: str) -> int:
        """Detect top N requests"""

        match = re.search(r'top\s*(\d+)', q)
        if match:
            return int(match.group(1))
        if "top 5" in q or "top five" in q:
            return 5
        if "top 10" in q or "top ten" in q:
            return 10
        return 10  # Default

    def _detect_comparison(self, q: str) -> Optional[str]:
        """Detect comparison queries"""

        if "irrigated" in q and "unirrigated" in q:
            return "irrigated_vs_unirrigated"
        if ("assigned" in q and "surveyed" in q) or ("assign" in q and "survey" in q):
            return "assigned_vs_surveyed"
        if "approved" in q and "closed" in q:
            return "approved_vs_closed"
        if "surveyable" in q and "surveyed" in q:
            return "surveyable_vs_surveyed"
        if "rabi" in q and "kharif" in q:
            return "rabi_vs_kharif"
        if ("crop" in q and "survey" in q) or ("cultivation" in q and "survey" in q):
            return "crop_vs_survey"
        if "fallow" in q and ("cultivated" in q or "surveyed" in q):
            return "fallow_vs_cultivated"

        return None

    def generate_narration(self, data: Dict[str, Any], user_state: str, original_query: str) -> str:
        """Generate detailed narration with insights"""

        # Try LLM first
        llm_narration = self._generate_llm_narration(data, user_state, original_query)
        if llm_narration and 50 < len(llm_narration.split()) < 150:
            return llm_narration

        # Fallback to template narration
        return self._generate_template_narration(data, user_state)

    def _generate_llm_narration(self, data: Dict, user_state: str, query: str) -> str:
        """Generate narration using LLM"""

        prompt = f"""Generate a professional analytical narration for this agriculture data.
Write 80-120 words with insights.

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
        dimension = data.get("dimension", "")

        if not values:
            return f"No data available for the requested analysis in {user_state}."

        # KPI (single value) narration
        if len(values) == 1:
            narration = f"The {title.lower()} for {user_state}"
            if season_filter:
                narration += f" in {season_filter} season"
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

            # Add survey stats
            if data.get('total_plots_surveyed'):
                surveyed = data.get('total_plots_surveyed', 0)
                approved = data.get('total_survey_approved', 0)
                narration += f" Survey progress shows {surveyed:,} plots surveyed with {approved:,} approved."

            return narration

        # Distribution narration
        top_label = labels[0] if labels else "Unknown"
        top_value = values[0] if values else 0
        top_pct = (top_value / total * 100) if total > 0 else 0

        narration = f"Analysis of {title.lower()} in {user_state}"
        if season_filter:
            narration += f" for {season_filter} season"
        narration += f" reveals a total of {total:,.2f} {unit}."

        narration += f" {top_label} leads with {top_value:,.2f} {unit} ({top_pct:.1f}% share)."

        # Add pattern insight
        if len(values) >= 3:
            top3_total = sum(values[:3])
            top3_pct = (top3_total / total * 100) if total > 0 else 0
            if top3_pct > 60:
                narration += f" The top 3 {dimension.lower()}s account for {top3_pct:.1f}% of the total, indicating concentration."
            else:
                narration += f" Distribution appears relatively balanced across {dimension.lower()}s."

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
