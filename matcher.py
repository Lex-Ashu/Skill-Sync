import re
from typing import List, Dict, Any

_SKILL_KEYWORDS = {
    "python", "java", "javascript", "c++", "c#", "react", "angular", "vue",
    "node.js", "django", "flask", "sql", "mongodb", "postgresql", "aws",
    "azure", "docker", "kubernetes", "git", "agile", "scrum",
}

_SKILL_SYNONYMS = {
    "js": "javascript",
    "reactjs": "react",
    "nodejs": "node.js",
    "aws": "aws",
    "docker": "docker",
    "kubernetes": "kubernetes",
}

def _normalize_skill(skill: str) -> str:
    s = skill.lower()
    return _SKILL_SYNONYMS.get(s, s)

def calculate_skills_match(candidate_skills: List[str], required_skills: List[str], preferred_skills: List[str] = None) -> Dict[str, Any]:
    if preferred_skills is None:
        preferred_skills = []
    cand_set = { _normalize_skill(s) for s in candidate_skills }
    req_set = { _normalize_skill(s) for s in required_skills }
    pref_set = { _normalize_skill(s) for s in preferred_skills }

    matched_required = cand_set.intersection(req_set)
    matched_preferred = cand_set.intersection(pref_set)
    missing_required = req_set - cand_set
    missing_preferred = pref_set - cand_set

    req_match_pct = len(matched_required) / len(req_set) if req_set else 1.0
    pref_match_pct = len(matched_preferred) / len(pref_set) if pref_set else 1.0
    skill_score = req_match_pct * 0.8 + pref_match_pct * 0.2

    return {
        "skill_score": skill_score,
        "required_match_pct": req_match_pct,
        "preferred_match_pct": pref_match_pct,
        "matched_required": list(matched_required),
        "missing_required": list(missing_required),
        "matched_preferred": list(matched_preferred),
        "missing_preferred": list(missing_preferred),
    }

def _parse_years_range(range_str: str) -> (int, int):
    parts = re.split(r"[-–]", range_str)
    if len(parts) == 2:
        return int(parts[0].strip()), int(parts[1].strip())
    val = int(parts[0].strip())
    return val, val

def calculate_experience_match(candidate_years: float, required_range: str) -> Dict[str, Any]:
    min_req, max_req = _parse_years_range(required_range)
    if min_req <= candidate_years <= max_req:
        score = 1.0
    elif candidate_years < min_req:
        gap = min_req - candidate_years
        score = max(0.0, 1.0 - (gap * 0.20))
    else:
        excess = candidate_years - max_req
        score = max(0.70, 1.0 - (excess * 0.05))
    return {
        "experience_score": score,
        "candidate_years": candidate_years,
        "required_range": required_range,
    }

def calculate_education_match(candidate_edu: List[Dict[str, str]], required_degree: str) -> Dict[str, Any]:
    required = required_degree.lower()
    matched = any(required in (edu.get("degree", "").lower()) for edu in candidate_edu)
    return {
        "education_score": 1.0 if matched else 0.0,
        "required_degree": required_degree,
        "matched": matched,
    }
