import os
import sys
import tempfile
import pandas as pd
import streamlit as st

# Add workspace subdirectories to sys.path for clean imports
current_dir = os.path.dirname(os.path.abspath(__file__))
for folder in ["analyzer", "scorer", "services"]:
    fpath = os.path.join(current_dir, folder)
    if fpath not in sys.path:
        sys.path.append(fpath)

from analyzer.analyzer_agent import run_analyzer_pipeline
from analyzer.jd_extractor import extract_jd_requirements
from scorer.scorer_agent import run_scorer_pipeline

st.set_page_config(
    page_title="AI Recruiter Agent - Candidate Matcher & Scorer",
    page_icon="🤖",
    layout="wide"
)

st.title("🤖 AI Recruiter Agent - Candidate Matcher & Scorer")
st.markdown(
    "Upload job descriptions and candidate resumes to analyze skills, compute weighted match scores, "
    "and automatically rank candidates."
)

# ---------------------------------------------------------
# Sidebar Configuration
# ---------------------------------------------------------
st.sidebar.header("📋 Agent Configuration")
st.sidebar.info(
    "**Agent Workflow:**\n"
    "1. **Analyzer Agent**: Parses PDF/DOCX resumes -> Structured JSON -> Extracts JD Requirements -> Matches skills with JD.\n"
    "2. **Scoring Agent**: Evaluates Skill Fit (50%), Experience (30%), Education (20%) -> Calculates final weighted score & generates candidate evaluation."
)

# ---------------------------------------------------------
# Input Section
# ---------------------------------------------------------
col1, col2 = st.columns([1, 1])

with col1:
    st.subheader("1. Job Description")
    job_description = st.text_area(
        "Enter or paste the Job Description (JD):",
        height=200,
        placeholder="e.g. Seeking a Senior Python Developer with experience in FastAPI, Docker, PostgreSQL, and AWS..."
    )

    if job_description.strip():
        with st.expander("📌 Extracted Job Requirements", expanded=True):
            jd_func = extract_jd_requirements.func if hasattr(extract_jd_requirements, "func") else extract_jd_requirements
            jd_reqs = jd_func(job_description)
            st.write(f"**Role Title:** {jd_reqs.get('role_title', 'N/A')}")
            st.write(f"**Required Skills:** {', '.join(jd_reqs.get('required_skills', [])) or 'None'}")
            st.write(f"**Preferred Skills:** {', '.join(jd_reqs.get('preferred_skills', [])) or 'None'}")
            st.write(f"**Min Experience:** {jd_reqs.get('min_experience_years', 0)} year(s)")

with col2:
    st.subheader("2. Upload Candidate Resumes")
    uploaded_files = st.file_uploader(
        "Upload one or multiple resumes (PDF or DOCX):",
        type=["pdf", "docx"],
        accept_multiple_files=True
    )


# ---------------------------------------------------------
# Process Resumes
# ---------------------------------------------------------
if st.button("🚀 Analyze & Rank Candidates", type="primary", use_container_width=True):
    if not job_description or not job_description.strip():
        st.warning("⚠️ Please enter a Job Description before running the analysis.")
    elif not uploaded_files:
        st.warning("⚠️ Please upload at least one candidate resume.")
    else:
        st.divider()
        st.header("📊 Candidate Evaluation & Leaderboard")

        candidate_results = []
        progress_bar = st.progress(0)
        status_text = st.empty()

        temp_dir = os.path.join(current_dir, "temp_uploads")
        os.makedirs(temp_dir, exist_ok=True)

        for idx, file in enumerate(uploaded_files):
            status_text.text(f"Processing candidate {idx + 1}/{len(uploaded_files)}: {file.name}...")
            file_path = os.path.join(temp_dir, file.name)
            
            with open(file_path, "wb") as f:
                f.write(file.getbuffer())

            try:
                # 1. Run Analyzer Agent Pipeline
                analyzer_res = run_analyzer_pipeline(file_path, job_description)
                resume_json = analyzer_res["resume_json"]
                match_report = analyzer_res["match_report"]

                # Extract Candidate Name
                c_name = resume_json.get("name")
                if not c_name or c_name == "Unknown":
                    c_name = os.path.splitext(file.name)[0].replace("_", " ").title()

                # 2. Run Scoring Agent Pipeline
                scorer_res = run_scorer_pipeline(resume_json, match_report, job_description)

                candidate_results.append({
                    "name": c_name,
                    "filename": file.name,
                    "score": scorer_res["overall_score"],
                    "recommendation": scorer_res["recommendation"],
                    "skill_score": scorer_res["skill_fit_score"],
                    "exp_score": scorer_res["experience_fit_score"],
                    "edu_score": scorer_res["education_fit_score"],
                    "matched_skills": match_report.get("matched_skills", []),
                    "missing_skills": match_report.get("missing_skills", []),
                    "assessment": scorer_res["assessment_text"],
                    "resume_json": resume_json
                })
            except Exception as e:
                st.error(f"❌ Error processing {file.name}: {str(e)}")

            progress_bar.progress((idx + 1) / len(uploaded_files))

        status_text.text("✅ Analysis complete!")

        if candidate_results:
            # Sort candidates by overall score descending
            ranked_candidates = sorted(candidate_results, key=lambda x: x["score"], reverse=True)

            # Leaderboard Table
            leaderboard_data = []
            for rank, c in enumerate(ranked_candidates, start=1):
                badge = "🥇" if rank == 1 else ("🥈" if rank == 2 else ("🥉" if rank == 3 else f"#{rank}"))
                leaderboard_data.append({
                    "Rank": badge,
                    "Candidate Name": c["name"],
                    "Overall Score": f"{c['score']} / 100",
                    "Recommendation": c["recommendation"],
                    "Matched Skills": len(c["matched_skills"]),
                    "Missing Skills": len(c["missing_skills"]),
                    "Filename": c["filename"]
                })

            df_leaderboard = pd.DataFrame(leaderboard_data)
            st.subheader("🏆 Recruiter Leaderboard")
            st.dataframe(df_leaderboard, use_container_width=True, hide_index=True)

            # Granular Breakdown Cards
            st.subheader("🔍 Granular Candidate Evaluation & Score Breakdown")

            for rank, c in enumerate(ranked_candidates, start=1):
                with st.expander(f"Rank #{rank}: {c['name']} (Score: {c['score']}/100 - {c['recommendation']})"):
                    m_col1, m_col2, m_col3, m_col4 = st.columns(4)
                    m_col1.metric("Overall Score", f"{c['score']} / 100")
                    m_col2.metric("Skill Fit (50%)", f"{c['skill_score']}%")
                    m_col3.metric("Experience (30%)", f"{c['exp_score']}%")
                    m_col4.metric("Education (20%)", f"{c['edu_score']}%")

                    st.markdown("#### 📝 Recruiter Evaluation & Assessment")
                    st.write(c["assessment"])

                    s_col1, s_col2 = st.columns(2)
                    with s_col1:
                        st.markdown("**✅ Matched Skills:**")
                        if c["matched_skills"]:
                            for s in c["matched_skills"]:
                                st.markdown(f"- `{s}`")
                        else:
                            st.caption("No exact skill matches identified.")

                    with s_col2:
                        st.markdown("**⚠️ Missing Skills:**")
                        if c["missing_skills"]:
                            for s in c["missing_skills"]:
                                st.markdown(f"- `{s}`")
                        else:
                            st.caption("No skill gaps detected.")

                    st.markdown("#### 📄 Extracted Structured JSON")
                    st.json(c["resume_json"])