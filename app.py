import streamlit as st
import pandas as pd
import re
from pathlib import Path

st.set_page_config(page_title="Skill-Sync: AI Resume Screener", layout="wide")

from parser import parse_resume, extract_text
from matcher import calculate_skills_match, calculate_experience_match, calculate_education_match, _SKILL_KEYWORDS
from embeddings import generate_embedding, cosine_similarity
from scorer import calculate_total_score, rank_candidates
from explainer import generate_explanation

st.markdown("""
<style>
    .reportview-container {
        background: #f0f2f6;
    }
    h1, h2, h3 {
        font-family: 'Helvetica Neue', sans-serif;
        color: #333;
    }
    .stButton>button {
        width: 100%;
        background-color: #4F46E5;
        color: white;
        border-radius: 8px;
        height: 3em;
        font-weight: 600;
        border: none;
        transition: all 0.3s ease;
    }
    .stButton>button:hover {
        background-color: #4338ca;
        box-shadow: 0 4px 6px rgba(0,0,0,0.1);
    }
    .streamlit-expanderHeader {
        background-color: white;
        border-radius: 5px;
        font-weight: 500;
    }
    div[data-testid="stMetricValue"] {
        font-size: 1.5rem;
        color: #4F46E5;
    }
</style>
""", unsafe_allow_html=True)

def _prepare_resume_text(file_path: str) -> str:
    return extract_text(file_path)

def extract_req_experience(job_description: str) -> str:
    # Look for patterns like "0-1 Year", "3-5 years", "2+ years"
    # Handles various dashes (hyphen, en-dash, em-dash)
    pattern = r"(\d+)(?:\s*[-–]\s*(\d+))?\s*(?:years?|yrs?)"
    match = re.search(pattern, job_description, re.IGNORECASE)
    if match:
        min_exp = match.group(1)
        max_exp = match.group(2)
        if max_exp:
            return f"{min_exp}-{max_exp}"
        else:
            # Handle "3+ years" case -> treat as 3-10
            return f"{min_exp}-10"
    return "0-100" # Default fallback if no experience mentioned

def screen_resumes(resume_files, job_description):
    job_emb = generate_embedding(job_description)
    
    # Extract experience requirement dynamically
    req_experience = extract_req_experience(job_description)
    
    candidates = []
    
    progress_bar = st.progress(0)
    status_text = st.empty()
    
    total_files = len(resume_files)
    
    for i, uploaded in enumerate(resume_files):
        status_text.text(f"Processing {uploaded.name}...")
        
        file_path = uploaded.name
        with open(file_path, "wb") as f:
            f.write(uploaded.getbuffer())
            
        parsed = parse_resume(file_path)
        name = parsed.get("name", Path(file_path).stem)
        
        # Use regex to split words, handling punctuation like "Python," correctly
        job_words = {t.lower() for t in re.findall(r"[A-Za-z0-9#+.]+", job_description)}
        required_skills = [s for s in _SKILL_KEYWORDS if s in job_words]
        skill_match = calculate_skills_match(parsed.get("skills", []), required_skills, [])
        
        exp_match = calculate_experience_match(parsed.get("total_experience_years", 0), req_experience)
        edu_match = calculate_education_match(parsed.get("education", []), "bachelor")
        
        resume_text = _prepare_resume_text(file_path)
        semantic_score = cosine_similarity(generate_embedding(resume_text), job_emb)
        
        components = {
            "skills": skill_match["skill_score"],
            "experience": exp_match["experience_score"],
            "education": edu_match["education_score"],
            "semantic": semantic_score,
        }
        total_score = calculate_total_score(components)
        
        candidate = {
            "name": name,
            "total_score": total_score,
            "skills_score": skill_match["skill_score"],
            "matched_required": skill_match["matched_required"],
            "missing_required": skill_match["missing_required"],
            "matched_preferred": skill_match["matched_preferred"],
            "missing_preferred": skill_match["missing_preferred"],
            "experience_score": exp_match["experience_score"],
            "candidate_years": exp_match["candidate_years"],
            "required_range": exp_match["required_range"],
            "education_score": edu_match["education_score"],
            "required_degree": edu_match["required_degree"],
            "semantic_score": semantic_score,
        }
        candidates.append(candidate)
        progress_bar.progress((i + 1) / total_files)

    status_text.empty()
    progress_bar.empty()
    
    ranked = rank_candidates(candidates)
    
    for cand in ranked:
        cand["explanation_text"] = generate_explanation(cand)
        
    return ranked

def main():
    st.title("Skill-Sync")
    st.markdown("### AI-Powered Resume Screening & Ranking System")
    st.markdown("---")

    col1, col2 = st.columns([1, 1.5], gap="large")
    
    with col1:
        st.subheader("Upload Resumes")
        resume_files = st.file_uploader(
            "Drop PDF, DOCX, or TXT files here", 
            accept_multiple_files=True, 
            type=["pdf", "docx", "txt"]
        )
        st.info(f"Uploaded: {len(resume_files)} files" if resume_files else "Waiting for files...")

    with col2:
        st.subheader("Job Description")
        job_description = st.text_area(
            "Paste the job description here...", 
            height=250,
            placeholder="e.g. Senior Software Engineer with Python, React, and AWS experience..."
        )

    st.markdown("---")
    analyze_col1, analyze_col2, analyze_col3 = st.columns([1, 2, 1])
    with analyze_col2:
        analyze_clicked = st.button("Analyze Candidates")

    if analyze_clicked:
        if not resume_files:
            st.warning("Please upload at least one resume.")
        elif not job_description:
            st.warning("Please provide a job description.")
        else:
            candidates = screen_resumes(resume_files, job_description)
            
            st.success(f"Successfully analyzed {len(candidates)} candidates!")
            st.markdown("### Top Candidates")
            
            top_cols = st.columns(3)
            for i, cand in enumerate(candidates[:3]):
                with top_cols[i]:
                    score = cand['total_score'] * 100
                    st.metric(
                        label=f"Rank #{cand['rank']}", 
                        value=f"{score:.1f}%", 
                        delta=cand['name']
                    )
            
            st.markdown("---")
            st.subheader("Detailed Rankings")
            
            summary_data = []
            for cand in candidates:
                summary_data.append({
                    "Rank": cand["rank"],
                    "Name": cand["name"],
                    "Total Score": f"{cand['total_score']*100:.1f}%",
                    "Skills Match": f"{cand['skills_score']*100:.0f}%",
                    "Experience": f"{cand['candidate_years']} yrs",
                })
            st.dataframe(pd.DataFrame(summary_data), use_container_width=True, hide_index=True)
            
            st.markdown("### Candidate Insights")
            for cand in candidates:
                with st.expander(f"#{cand['rank']} {cand['name']} - Score: {cand['total_score']*100:.1f}%"):
                    c1, c2 = st.columns([2, 1])
                    with c1:
                        st.markdown(f"**Recommendation:**")
                        rec = cand['explanation_text'].split('\n')[-1]
                        st.info(rec)
                        
                        st.code(cand['explanation_text'], language="text")
                    
                    with c2:
                        st.progress(cand['total_score'], text="Overall Score")
                        st.progress(cand['skills_score'], text="Skills Match")
                        st.progress(cand['experience_score'], text="Experience Match")
                        st.progress(cand['semantic_score'], text="Semantic Match")

if __name__ == "__main__":
    main()
