"""
utils.py
Utility functions for data handling, JSON I/O, and label management.
"""

import json
from pathlib import Path
from typing import Dict, List, Tuple

# ----------------------------
# LABEL MAPPINGS
# ----------------------------
LABEL_DISPLAY_TO_CODE = {
    "i. Full alignment p(D, R)": "pdr",
    "ii. Property expressed with correct Domain p(D, ?)": "pd",
    "iii. Property expressed with correct Range p(?, R)": "pr",
    "iv. Property expressed with incorrect domain and range p(?, ?)": "p",
    "v. No alignment": "n",
}

CODE_TO_LABEL_DISPLAY = {v: k for k, v in LABEL_DISPLAY_TO_CODE.items()}
LABEL_CHOICES = list(LABEL_DISPLAY_TO_CODE.keys())

INFO_LEGEND = """**Legend → code mapping**
- i. Full alignment p(D, R) → `pdr`  
- ii. Correct Domain p(D, ?) → `pd`  
- iii. Correct Range p(?, R) → `pr`  
- iv. Incorrect D & R p(?, ?) → `p`  
- v. No alignment → `n`
"""

# ----------------------------
# JSON I/O
# ----------------------------
def load_json(file_path: str) -> dict:
    """Load JSON from file path."""
    with open(file_path, "r", encoding="utf-8") as f:
        return json.load(f)

def save_json(data: dict, file_path: str) -> None:
    """Save dictionary as JSON to file path."""
    with open(file_path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

# ----------------------------
# DATA PROCESSING
# ----------------------------
def normalize_input_data(raw_data: dict) -> dict:
    """
    Normalize input JSON structure.
    Ensures each property has 'domain', 'range', and 'texts' (as list).
    """
    normalized = {}
    for prop, body in raw_data.items():
        if not isinstance(body, dict):
            continue
        
        domain = body.get("domain", "")
        rng = body.get("range", "")
        texts = body.get("texts", [])
        
        # If texts is a dict (from labeled output), extract keys
        if isinstance(texts, dict):
            texts = list(texts.keys())
        elif not isinstance(texts, list):
            texts = []
        
        normalized[prop] = {
            "domain": domain,
            "range": rng,
            "texts": texts
        }
    
    return normalized

def initialize_labels(data_raw: dict, existing_labels: dict = None) -> dict:
    """
    Initialize label dictionary for all properties.
    If existing_labels provided, merge them in.
    """
    labels = {}
    for prop, body in data_raw.items():
        texts = body["texts"]
        labels[prop] = {text: "" for text in texts}
        
        # Merge existing labels if provided
        if existing_labels and prop in existing_labels:
            for text in texts:
                if text in existing_labels[prop]:
                    labels[prop][text] = existing_labels[prop][text] or ""
    
    return labels

def load_existing_labels(file_path: str, data_raw: dict) -> dict:
    """
    Load labels from an existing output JSON file.
    Returns a labels dictionary compatible with data_raw.
    """
    try:
        existing_out = load_json(file_path)
        labels = {}
        
        for prop in data_raw.keys():
            texts = data_raw[prop]["texts"]
            labels[prop] = {text: "" for text in texts}
            
            if prop in existing_out and isinstance(existing_out[prop], dict):
                text_dict = existing_out[prop].get("texts", {})
                if isinstance(text_dict, dict):
                    for text in texts:
                        if text in text_dict:
                            labels[prop][text] = text_dict[text] or ""
        
        return labels
    except Exception:
        return {}

def create_output_object(data_raw: dict, labels: dict) -> dict:
    """
    Create output JSON structure.
    Mirrors input but 'texts' becomes a dict: {sentence: label_code}
    """
    output = {}
    for prop, body in data_raw.items():
        output[prop] = {
            "domain": body["domain"],
            "range": body["range"],
            "texts": labels.get(prop, {})
        }
    return output

# ----------------------------
# STATISTICS & NAVIGATION
# ----------------------------
def calculate_stats(texts: List[str], labels: Dict[str, str]) -> Tuple[int, int, float]:
    """
    Calculate labeling statistics for a property.
    Returns: (labeled_count, total_count, percentage)
    """
    total = len(texts)
    labeled = sum(1 for text in texts if labels.get(text, "") != "")
    percentage = round((labeled / total * 100.0), 2) if total else 0.0
    return labeled, total, percentage

def find_first_unlabeled(texts: List[str], labels: Dict[str, str]) -> int:
    """Find index of first unlabeled sentence, or 0 if all labeled."""
    for i, text in enumerate(texts):
        if labels.get(text, "") == "":
            return i
    return 0

def find_next_unlabeled(texts: List[str], labels: Dict[str, str], current_idx: int) -> int:
    """
    Find next unlabeled sentence after current_idx.
    Returns current_idx if none found.
    """
    for i in range(current_idx + 1, len(texts)):
        if labels.get(texts[i], "") == "":
            return i
    return current_idx

def find_prev_unlabeled(texts: List[str], labels: Dict[str, str], current_idx: int) -> int:
    """
    Find previous unlabeled sentence before current_idx.
    Returns current_idx if none found.
    """
    for i in range(current_idx - 1, -1, -1):
        if labels.get(texts[i], "") == "":
            return i
    return current_idx
