import os
import sys

# Ensure analyzer folder and project root are in sys.path
current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.dirname(current_dir)
analyzer_dir = os.path.join(project_root, "analyzer")
for p in [project_root, analyzer_dir]:
    if p not in sys.path:
        sys.path.append(p)

from analyzer.jd_extractor import extract_jd_requirements
from analyzer.matcher import match_skills

def test_jd_extraction_and_matching():
    sample_jd = """
    We are looking for a Senior Python Developer with at least 4 years of experience.
    Requirements:
    - Python, Docker, SQL, REST API
    Preferred:
    - AWS, Kubernetes
    """

    print("--- Testing JD Requirement Extraction ---")
    jd_func = extract_jd_requirements.func if hasattr(extract_jd_requirements, "func") else extract_jd_requirements
    jd_reqs = jd_func(sample_jd)
    print("Extracted Requirements:", jd_reqs)

    assert "required_skills" in jd_reqs
    assert jd_reqs["min_experience_years"] >= 0

    print("\n--- Testing Skill Matching ---")
    candidate_skills = ["Python", "SQL", "Docker", "Git"]
    match_func = match_skills.func if hasattr(match_skills, "func") else match_skills
    match_result = match_func(jd_reqs, candidate_skills)
    print("Match Result:", match_result)

    assert match_result["score"] > 0
    assert "matched_skills" in match_result

    print("\n✅ All JD Extraction and Matching tests passed!")

if __name__ == "__main__":
    test_jd_extraction_and_matching()
