import random
import re
import json
import requests
from typing import Dict, Any, Optional
from config import CONVERSATION_RESPONSES, INDICATORS, DIMENSIONS, DISTRIBUTION_KEYWORDS

class NLPHandler:
    def __init__(self, model_name: str = "gpt-oss:120b-cloud"):
        self.model = model_name
        self.ollama_url = "http://localhost:11434/api/generate"
        self._verify_model()

    def _verify_model(self):
        """Check if requested model exists, else fallback to llama3."""
        try:
            res = requests.get("http://localhost:11434/api/tags", timeout=2)
            models = [m['name'] for m in res.json().get('models', [])]
            if self.model not in models and "llama3:latest" in models:
                print(f"DEBUG: Model {self.model} not found. Falling back to llama3:latest")
                self.model = "llama3:latest"
        except:
            pass

    def _query_llm(self, prompt: str) -> str:
        """Helper to communicate with Ollama."""
        try:
            response = requests.post(
                self.ollama_url,
                json={"model": self.model, "prompt": prompt, "stream": False},
                timeout=15
            )
            return response.json().get("response", "").strip()
        except Exception as e:
            print(f"Ollama Error: {e}")
            return ""

    def classify_intent(self, query: str) -> Dict[str, Any]:
        """
        AI-Powered Intent Detection with Regex protection.
        """
        q = query.lower().strip()
        
        # 1. Professional Prompt for Intent Recognition
        prompt = f"""
        TASK: Classify this Agriculture MIS query: "{query}"
        
        RULES:
        - If greeting or help: mode="conversation"
        - If requesting data: mode="analytics"
        - INDICATORS: {list(INDICATORS.keys())}
        - DIMENSIONS: {list(DIMENSIONS.keys())}
        
        RETURN JSON ONLY:
        {{ "mode": "analytics", "indicator": "...", "dimension": "...", "sub_type": "..." }}
        """
        
        llm_response = self._query_llm(prompt)
        try:
            clean_json = re.search(r'\{.*\}', llm_response, re.DOTALL)
            if clean_json:
                data = json.loads(clean_json.group())
                data["intent_type"] = "distribution" if data.get("dimension") else "summary"
                return data
        except:
            pass

        # === HEURISTIC FALLBACK (Whole Word Matching) ===
        words = set(re.findall(r'\b\w+\b', q))
        conv_hi = {"hi", "hello", "hey", "greetings", "hellow", "helo", "hii", "hai"}
        conv_help = {"help", "guide", "who", "what"}
        
        if any(w in words for w in conv_hi):
            return {"mode": "conversation", "sub_type": "greeting"}
        if any(w in words for w in conv_help):
            return {"mode": "conversation", "sub_type": "help"}

        scores = {k: 0 for k in INDICATORS.keys()}
        for k, meta in INDICATORS.items():
            for kw in meta["keywords"]:
                if kw in q: scores[k] += 3
        
        detected_indicator = max(scores, key=scores.get)
        if scores[detected_indicator] == 0: detected_indicator = "crop_area"

        dim_scores = {k: 0 for k in DIMENSIONS.keys()}
        for k, meta in DIMENSIONS.items():
            for kw in meta["keywords"]:
                if kw in q: dim_scores[k] += 4
        
        detected_dimension = max(dim_scores, key=dim_scores.get)
        if dim_scores[detected_dimension] == 0: detected_dimension = None

        if any(word in q for word in DISTRIBUTION_KEYWORDS) and not detected_dimension:
            detected_dimension = "category" if detected_indicator in ["farmers", "crop_area"] else "district"

        return {
            "mode": "analytics",
            "indicator": detected_indicator,
            "dimension": detected_dimension,
            "intent_type": "distribution" if detected_dimension else "summary"
        }

    def generate_narration(self, data: Dict[str, Any], user_state: str, original_query: str) -> str:
        """AI-Powered Narrative Synthesis."""
        prompt = f"""
        User Query: "{original_query}"
        Data Context: {json.dumps(data)}
        State: {user_state}
        
        Generate a professional, executive-style summary in 2 sentences. 
        Focus on accuracy and insights. Mention the total and the top segment. 
        If the dimension was unavailable, explain it politely.
        """
        
        llm_narration = self._query_llm(prompt)
        if llm_narration:
            return llm_narration

        # Fallback to template narration
        title = data.get("title", "Data")
        unit = data.get("unit", "")
        values = data.get("values", [])
        labels = data.get("labels", [])
        total = sum(values) if values else 0
        note = data.get("note", "")

        if not values: return f"Strategic Insight: No data available for {title} in {user_state}."
        if len(values) == 1:
            msg = f"The total {title.lower()} for {user_state} is {total:,.2f} {unit}."
            return f"{msg} Note: {note}" if note else msg

        top_lab, top_val = labels[0], values[0]
        pct = (top_val / total * 100) if total > 0 else 0
        return (f"Analytical Summary for {user_state}: The {title.lower()} is {total:,.2f} {unit}. "
                f"The leading segment is {top_lab} with {top_val:,.2f} {unit} ({pct:.1f}%).")

    def get_conversation_response(self, sub_type: str, original_query: str = "") -> str:
        """Generate dynamic conversation response using LLM."""

        if sub_type == "greeting":
            prompt = f"""
            User said: "{original_query}"

            You are AgriStack MIS Assistant - an AI that helps with agriculture data analytics.
            Generate a warm, friendly greeting response (1-2 sentences).
            Mention you can help with: crop data, farmer statistics, survey progress, district-wise analysis.
            Keep it professional but friendly.
            """
        else:
            prompt = f"""
            User asked: "{original_query}"

            You are AgriStack MIS Assistant. The user needs help.
            Provide a helpful response suggesting what they can ask about:
            - Survey status, plot completion, validation
            - Farmer registration, demographics, category distribution
            - Crop area, cultivated vs harvested, irrigation status
            - District-wise comparisons, trends, top crops
            Keep response to 2-3 sentences.
            """

        llm_response = self._query_llm(prompt)
        if llm_response:
            return llm_response

        # Fallback to static response if LLM fails
        return random.choice(CONVERSATION_RESPONSES.get(sub_type, CONVERSATION_RESPONSES["help"]))
