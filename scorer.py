from typing import List, Dict, Any

WEIGHTS = {
    "skills": 0.40,
    "experience": 0.25,
    "education": 0.15,
    "semantic": 0.20,
}

def calculate_total_score(components: Dict[str, float]) -> float:
    total = 0.0
    for key, weight in WEIGHTS.items():
        total += components.get(key, 0.0) * weight
    return total

def rank_candidates(candidates: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    sorted_candidates = sorted(candidates, key=lambda x: x.get("total_score", 0), reverse=True)
    for idx, cand in enumerate(sorted_candidates, start=1):
        cand["rank"] = idx
    return sorted_candidates
