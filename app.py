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
from services.scheduler import (
    get_available_time_slots,
    schedule_candidate_interview,
    list_scheduled_interviews,
    create_new_slot
)


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

                    # ---------------------------------------------------------
                    # Interview Scheduling Action inside Candidate Card
                    # ---------------------------------------------------------
                    st.markdown("#### 📅 Schedule Interview")
                    avail_slots = get_available_time_slots()
                    if avail_slots:
                        slot_options = {f"{s['slot_time']} (ID: {s['id']})": s["id"] for s in avail_slots}
                        selected_slot_label = st.selectbox(
                            f"Select Interview Slot for {c['name']}:",
                            options=list(slot_options.keys()),
                            key=f"slot_select_{rank}_{c['name']}"
                        )
                        c_email = st.text_input("Candidate Email:", value=f"{c['name'].lower().replace(' ', '.')}@example.com", key=f"email_{rank}_{c['name']}")

                        if st.button(f"🗓️ Confirm Schedule for {c['name']}", key=f"btn_sched_{rank}_{c['name']}"):
                            slot_id = slot_options[selected_slot_label]
                            res = schedule_candidate_interview(
                                candidate_name=c["name"],
                                candidate_email=c_email,
                                role_title=jd_reqs.get("role_title", "General Role") if 'jd_reqs' in locals() and jd_reqs else "General Role",
                                slot_id=slot_id
                            )
                            if res["status"] == "Success":
                                st.success(f"✅ Interview scheduled for {c['name']}!")
                                st.info(f"🔗 **Meeting Link:** [{res['booking']['meeting_link']}]({res['booking']['meeting_link']})")
                            else:
                                st.error(f"❌ {res['message']}")
                    else:
                        st.info("No available slots. Add a slot in the Interview Scheduler section below.")

        # ---------------------------------------------------------
        # Interview Scheduler & Slot Management Dashboard
        # ---------------------------------------------------------
        st.divider()
        st.header("📅 Scheduled Interviews & Slot Management")
        
        sch_col1, sch_col2 = st.columns([2, 1])

        with sch_col1:
            st.subheader("📋 Booked Interviews")
            scheduled_list = list_scheduled_interviews()
            if scheduled_list:
                df_scheduled = pd.DataFrame([
                    {
                        "Candidate Name": s["candidate_name"],
                        "Role Title": s["role_title"],
                        "Interview Time": s["slot_time"],
                        "Meeting Link": s["meeting_link"],
                        "Status": s["status"]
                    } for s in scheduled_list
                ])
                st.dataframe(df_scheduled, use_container_width=True, hide_index=True)
            else:
                st.info("No interviews scheduled yet.")

        with sch_col2:
            st.subheader("➕ Add Interviewer Slot")
            new_slot_input = st.text_input("Enter Slot Date & Time (e.g. 2026-08-10 03:00 PM):")
            if st.button("Add Slot"):
                if new_slot_input.strip():
                    new_id = create_new_slot(new_slot_input.strip())
                    st.success(f"✅ Added slot ID #{new_id} ({new_slot_input})")
                else:
                    st.warning("Please enter a slot time.")