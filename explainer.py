from typing import Dict, Any

def generate_explanation(candidate: Dict[str, Any]) -> str:
    lines = []
    lines.append(f"Candidate: {candidate.get('name', 'N/A')}")
    lines.append(f"Overall Score: {candidate.get('total_score', 0) * 100:.1f}/100 (Rank #{candidate.get('rank')})")
    lines.append("")
    skills = candidate.get('skills_score', 0) * 100
    lines.append(f"✓ Skills Match: {skills:.1f}% (Weight 40%)")
    lines.append(f"  - Matched required: {', '.join(candidate.get('matched_required', [])) or 'None'}")
    lines.append(f"  - Missing required: {', '.join(candidate.get('missing_required', [])) or 'None'}")
    lines.append(f"  - Matched preferred: {', '.join(candidate.get('matched_preferred', [])) or 'None'}")
    lines.append(f"  - Missing preferred: {', '.join(candidate.get('missing_preferred', [])) or 'None'}")
    lines.append("")
    exp_score = candidate.get('experience_score', 0) * 100
    lines.append(f"✓ Experience Match: {exp_score:.1f}% (Weight 25%)")
    lines.append(f"  - Candidate years: {candidate.get('candidate_years', 0)}")
    lines.append(f"  - Required range: {candidate.get('required_range', 'N/A')}")
    lines.append("")
    edu_score = candidate.get('education_score', 0) * 100
    lines.append(f"✓ Education Match: {edu_score:.1f}% (Weight 15%)")
    lines.append(f"  - Required degree: {candidate.get('required_degree', 'N/A')}")
    lines.append(f"  - Matched: {'Yes' if candidate.get('education_score', 0) > 0 else 'No'}")
    lines.append("")
    sem_score = candidate.get('semantic_score', 0) * 100
    lines.append(f"✓ Semantic Similarity: {sem_score:.1f}% (Weight 20%)")
    lines.append("")
    lines.append("Recommendations:")
    missing = candidate.get('missing_required', [])
    if missing:
        lines.append(f"- Consider training on missing critical skills: {', '.join(missing)}")
    else:
        lines.append("- Strong candidate, proceed to interview.")
    return "\n".join(lines)
