import re
import json
from pathlib import Path
from typing import List, Dict, Any

import pdfplumber
import PyPDF2
import docx
try:
    import spacy
    _nlp = spacy.load("en_core_web_sm")
except Exception:
    _nlp = None

def _extract_text_from_pdf(file_path: Path) -> str:
    try:
        with pdfplumber.open(file_path) as pdf:
            return "\n".join(page.extract_text() or "" for page in pdf.pages)
    except Exception:
        reader = PyPDF2.PdfReader(str(file_path))
        return "\n".join(page.extract_text() or "" for page in reader.pages)

def _extract_text_from_docx(file_path: Path) -> str:
    doc = docx.Document(str(file_path))
    return "\n".join(p.text for p in doc.paragraphs)

def _extract_text_from_txt(file_path: Path) -> str:
    return file_path.read_text(encoding="utf-8")

def extract_text(file_path: str) -> str:
    path = Path(file_path)
    ext = path.suffix.lower()
    if ext == ".pdf":
        return _extract_text_from_pdf(path)
    if ext in {".docx", ".doc"}:
        return _extract_text_from_docx(path)
    if ext == ".txt":
        return _extract_text_from_txt(path)
    raise ValueError(f"Unsupported file type: {ext}")

_EMAIL_REGEX = re.compile(r"[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+")
_PHONE_REGEX = re.compile(r"(\+?\d{1,3}[\s-]?)?(\(?\d{3}\)?[\s-]?\d{3}[\s-]?\d{4})")
_LINKEDIN_REGEX = re.compile(r"linkedin\.com/in/[^\s/]+")

def extract_personal_info(text: str) -> Dict[str, str]:
    email_match = _EMAIL_REGEX.search(text)
    phone_match = _PHONE_REGEX.search(text)
    linkedin_match = _LINKEDIN_REGEX.search(text)
    name = None
    if _nlp:
        doc = _nlp(text)
        for ent in doc.ents:
            if ent.label_ == "PERSON":
                name = ent.text.strip()
                break
    if not name:
        first_lines = text.splitlines()[:5]
        for line in first_lines:
            words = line.strip().split()
            if len(words) >= 2 and all(w[0].isupper() for w in words[:2]):
                name = " ".join(words[:2])
                break
    return {
        "name": name or "",
        "email": email_match.group(0) if email_match else "",
        "phone": phone_match.group(0) if phone_match else "",
        "linkedin": linkedin_match.group(0) if linkedin_match else "",
    }

_SKILL_KEYWORDS = {
    "python", "java", "javascript", "c++", "c#", "react", "angular", "vue",
    "node.js", "django", "flask", "sql", "mongodb", "postgresql", "aws",
    "azure", "docker", "kubernetes", "git", "agile", "scrum",
}

def extract_skills(text: str) -> List[str]:
    tokens = {t.lower() for t in re.findall(r"[A-Za-z0-9#+.]+", text)}
    found = _SKILL_KEYWORDS.intersection(tokens)
    return sorted(found)

_DATE_REGEX = re.compile(r"(Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[a-z]*\s+\d{4}", re.IGNORECASE)

def _parse_date_range(section: str) -> List[Dict[str, Any]]:
    experiences = []
    lines = section.splitlines()
    for line in lines:
        dates = _DATE_REGEX.findall(line)
        if len(dates) >= 2:
            start, end = dates[0], dates[1]
            company = ""
            if _nlp:
                doc = _nlp(line)
                orgs = [ent.text for ent in doc.ents if ent.label_ == "ORG"]
                company = orgs[0] if orgs else ""
            title_match = re.search(r"(Senior|Junior|Lead|Manager|Engineer|Developer|Analyst|Architect)", line, re.I)
            title = title_match.group(0) if title_match else ""
            experiences.append({
                "title": title,
                "company": company,
                "start_date": start,
                "end_date": end,
            })
    return experiences

def extract_experience(text: str) -> List[Dict[str, Any]]:
    exp_section_match = re.search(r"experience|work history|professional experience", text, re.I)
    if not exp_section_match:
        return []
    start_idx = exp_section_match.end()
    snippet = text[start_idx:start_idx + 2000]
    return _parse_date_range(snippet)

_DEGREE_REGEX = re.compile(r"(bachelor|master|ph\.d|doctor|associate)[^\n]*", re.I)

def extract_education(text: str) -> List[Dict[str, str]]:
    edu_section_match = re.search(r"education|academic background", text, re.I)
    if not edu_section_match:
        return []
    start = edu_section_match.end()
    snippet = text[start:start + 1500]
    lines = snippet.splitlines()
    educations = []
    for line in lines:
        degree_match = _DEGREE_REGEX.search(line)
        if degree_match:
            university = ""
            if _nlp:
                doc = _nlp(line)
                orgs = [ent.text for ent in doc.ents if ent.label_ == "ORG"]
                university = orgs[0] if orgs else ""
            degree = degree_match.group(0).strip()
            major_match = re.search(r"(?:in|of)\s+([A-Za-z &]+)", line, re.I)
            major = major_match.group(1).strip() if major_match else ""
            educations.append({"degree": degree, "major": major, "university": university})
    return educations

def parse_resume(file_path: str) -> Dict[str, Any]:
    raw_text = extract_text(file_path)
    personal = extract_personal_info(raw_text)
    skills = extract_skills(raw_text)
    experience = extract_experience(raw_text)
    education = extract_education(raw_text)
    total_months = 0
    for exp in experience:
        month_map = {"jan":1,"feb":2,"mar":3,"apr":4,"may":5,"jun":6,"jul":7,"aug":8,"sep":9,"oct":10,"nov":11,"dec":12}
        def _to_month_year(s):
            parts = s.split()
            if len(parts) < 2:
                return 1, 2020
            return month_map.get(parts[0][:3].lower(),1), int(parts[1])
        sm, sy = _to_month_year(exp["start_date"])
        em, ey = _to_month_year(exp["end_date"])
        months = (ey - sy) * 12 + (em - sm)
        total_months += max(months, 0)
    total_years = round(total_months / 12, 2) if total_months else 0.0
    return {
        "name": personal.get("name", ""),
        "email": personal.get("email", ""),
        "phone": personal.get("phone", ""),
        "linkedin": personal.get("linkedin", ""),
        "skills": skills,
        "experience": experience,
        "education": education,
        "total_experience_years": total_years,
    }

if __name__ == "__main__":
    import sys, json
    if len(sys.argv) != 2:
        print("Usage: python parser.py <resume_file>")
        sys.exit(1)
    result = parse_resume(sys.argv[1])
    print(json.dumps(result, indent=2, ensure_ascii=False))
