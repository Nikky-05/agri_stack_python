import csv
import os
import re

BASE_DIR = os.path.dirname(os.path.abspath(__file__))


def _load_state_mapping():
    """Load state_lgd_code -> state name from CSV"""
    mapping = {}
    path = os.path.join(BASE_DIR, "state_lgd_data.csv")
    try:
        with open(path, encoding="utf-8") as f:
            for row in csv.DictReader(f):
                code = str(row["state_lgd_code"]).strip()
                name = row["state_name"].strip().title()
                mapping[code] = name
    except FileNotFoundError:
        print(f"Warning: {path} not found")
    return mapping


def _load_district_mapping():
    """Load district LGD mappings from CSV"""
    name_to_lgd = {}   # {state_lgd: {district_name_lower: district_lgd_code}}
    lgd_to_name = {}   # {district_lgd_code: "District Name Title Case"}

    path = os.path.join(BASE_DIR, "district_lgd_data-1.csv")
    try:
        with open(path, encoding="utf-8") as f:
            for row in csv.DictReader(f):
                d_lgd = str(row["district_lgd_code"]).strip()
                d_name = row["district_name"].strip()
                s_lgd = str(row["state_lgd_code"]).strip()

                if s_lgd not in name_to_lgd:
                    name_to_lgd[s_lgd] = {}

                name_to_lgd[s_lgd][d_name.lower()] = d_lgd
                lgd_to_name[d_lgd] = d_name.title()
    except FileNotFoundError:
        print(f"Warning: {path} not found")

    return name_to_lgd, lgd_to_name


# ── Build all mappings at import time ──
LGD_TO_STATE = _load_state_mapping()
DISTRICT_NAME_TO_LGD, LGD_TO_DISTRICT_NAME = _load_district_mapping()

# Pre-compile regex patterns per state (longest name first for accurate matching)
_DISTRICT_PATTERNS = {}
for _s_lgd, _districts in DISTRICT_NAME_TO_LGD.items():
    _sorted_names = sorted(_districts.keys(), key=len, reverse=True)
    _patterns = []
    for _name in _sorted_names:
        _pat = re.compile(r'\b' + re.escape(_name) + r'\b', re.IGNORECASE)
        _patterns.append((_pat, _name))
    _DISTRICT_PATTERNS[_s_lgd] = _patterns


def detect_district_in_query(query: str, state_lgd: str):
    """
    Detect a district name in the user query for the given state.

    Uses word-boundary regex matching with longest-name-first priority
    to avoid partial/false matches.

    Returns:
        (district_lgd_code, display_name)  if found
        (None, None)                       if not found
    """
    patterns = _DISTRICT_PATTERNS.get(state_lgd, [])
    for pattern, name_lower in patterns:
        if pattern.search(query):
            lgd_code = DISTRICT_NAME_TO_LGD[state_lgd][name_lower]
            display_name = LGD_TO_DISTRICT_NAME.get(lgd_code, name_lower.title())
            return lgd_code, display_name
    return None, None
