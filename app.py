import os
import sys
import tempfile
import pandas as pd
import streamlit as st

# Add workspace subdirectories to sys.path for clean imports
current_dir = os.path.dirname(os.path.abspath(__file__))
for folder in ["analyzer", "scorer", "services", "database"]:
    fpath = os.path.join(current_dir, folder)
    if fpath not in sys.path:
        sys.path.append(fpath)

from analyzer.analyzer_agent import run_analyzer_pipeline
from analyzer.jd_extractor import extract_jd_requirements
from scorer.scorer_agent import run_scorer_pipeline
from database.database import (
    save_candidate_pipeline_record,
    get_all_candidates,
    update_candidate_stage,
    get_candidate_by_id
)
from services.assessment_service import (
    generate_assessment_invite,
    simulate_assessment_completion
)
from services.scheduler import (
    get_available_time_slots,
    schedule_candidate_interview,
    list_scheduled_interviews,
    create_new_slot
)
from services.email_templates import (
    generate_interview_invite_email,
    generate_shortlist_email,
    generate_rejection_email
)


st.set_page_config(
    page_title="HYRIX - Indian Tech Recruitment Specialist",
    page_icon="🤖",
    layout="wide"
)

st.title("🤖 HYRIX: Indian Tech Recruitment Specialist")
st.markdown(
    "Automated resume parsing, Indian college tier recognition (IIT/NIT/BITS), tech-specific skill matching, "
    "notice period & CTC evaluation, and HackerEarth / Mettl assessment workflows."
)

# ---------------------------------------------------------
# Sidebar Configuration
# ---------------------------------------------------------
st.sidebar.header("📋 Agent Configuration")
st.sidebar.info(
    "**Agent Workflow:**\n"
    "1. **Analyzer Agent**: Multi-document ingestion -> Structured JSON -> Indian College Tier recognition -> Tech taxonomy matching.\n"
    "2. **Scorer Agent**: Weighted Scoring (Skill 50%, Experience 30%, Education 20%) + Tier-1 Pedigree & Notice period bonuses.\n"
    "3. **Pipeline & Assessment**: HackerEarth / Mettl coding evaluations and persistent pipeline stages."
)

# ---------------------------------------------------------
# Tabs Navigation
# ---------------------------------------------------------
tab_eval, tab_pipeline, tab_schedule, tab_comm = st.tabs([
    "🚀 Resume Screening & Scoring",
    "🇮🇳 Candidate Pipeline & Assessments",
    "📅 Interview Scheduler",
    "✉️ Communication Center"
])

# =========================================================
# TAB 1: Resume Screening & Scoring
# =========================================================
with tab_eval:
    col1, col2 = st.columns([1, 1])

    with col1:
        st.subheader("1. Job Description")
        job_description = st.text_area(
            "Enter or paste the Job Description (JD):",
            height=200,
            placeholder="e.g. Seeking a Senior Full Stack Engineer with expertise in Java, Spring Boot, React, Next.js, and Docker. Experience with microservices preferred. Location: Bengaluru / Gurgaon..."
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

    if st.button("🚀 Run Indian Tech Analysis & Rank", type="primary"):
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
                    indian_profile = analyzer_res.get("indian_tech_profile", {})

                    # Extract Candidate Name & Contact
                    c_name = resume_json.get("name")
                    if not c_name or c_name == "Unknown":
                        c_name = os.path.splitext(file.name)[0].replace("_", " ").title()

                    contact = resume_json.get("contact", {}) if isinstance(resume_json.get("contact"), dict) else {}
                    c_email = contact.get("email") or resume_json.get("email") or f"{c_name.lower().replace(' ', '.')}@example.com"
                    c_phone = contact.get("phone") or resume_json.get("phone") or "+91-XXXXXXXXXX"

                    # 2. Run Scoring Agent Pipeline with Indian Tech Profile
                    scorer_res = run_scorer_pipeline(resume_json, match_report, job_description, indian_profile=indian_profile)

                    # 3. Save to SQLite Candidate Pipeline DB
                    db_candidate = {
                        "name": c_name,
                        "email": c_email,
                        "phone": c_phone,
                        "skills": analyzer_res.get("skills", []),
                        "experience": resume_json.get("experience", []),
                        "education": resume_json.get("education", []),
                        "score": scorer_res["overall_score"],
                        "matched_skills": match_report.get("matched_skills", []),
                        "missing_skills": match_report.get("missing_skills", []),
                        "resume_text": analyzer_res.get("parsed_text", ""),
                        "stage": "Shortlisted" if scorer_res["overall_score"] >= 70 else "Screened",
                        "notice_period_days": indian_profile.get("notice_period_days", 30),
                        "current_ctc_lpa": indian_profile.get("current_ctc_lpa", 0.0),
                        "expected_ctc_lpa": indian_profile.get("expected_ctc_lpa", 0.0),
                        "current_location": indian_profile.get("current_location", "Delhi-NCR / Remote"),
                        "preferred_locations": "Bengaluru, Hyderabad, NCR, Pune",
                        "relocation_willingness": "Yes",
                        "college_tier": indian_profile.get("college_tier", "Tier-3"),
                        "degree": indian_profile.get("degree", "B.Tech"),
                        "notes": f"Score: {scorer_res['overall_score']}/100. Rec: {scorer_res['recommendation']}"
                    }
                    cand_id = save_candidate_pipeline_record(db_candidate)

                    candidate_results.append({
                        "id": cand_id,
                        "name": c_name,
                        "email": c_email,
                        "phone": c_phone,
                        "filename": file.name,
                        "score": scorer_res["overall_score"],
                        "recommendation": scorer_res["recommendation"],
                        "skill_score": scorer_res["skill_fit_score"],
                        "exp_score": scorer_res["experience_fit_score"],
                        "edu_score": scorer_res["education_fit_score"],
                        "college_tier": indian_profile.get("college_tier", "Tier-3"),
                        "college_name": indian_profile.get("college_name", "College"),
                        "degree": indian_profile.get("degree", "B.Tech"),
                        "notice_period": indian_profile.get("notice_period_days", 30),
                        "current_ctc": indian_profile.get("current_ctc_lpa", 0.0),
                        "expected_ctc": indian_profile.get("expected_ctc_lpa", 0.0),
                        "location": indian_profile.get("current_location", "Delhi-NCR"),
                        "matched_skills": match_report.get("matched_skills", []),
                        "missing_skills": match_report.get("missing_skills", []),
                        "assessment": scorer_res["assessment_text"],
                        "resume_json": resume_json
                    })
                except Exception as e:
                    st.error(f"❌ Error processing {file.name}: {str(e)}")

                progress_bar.progress((idx + 1) / len(uploaded_files))

            status_text.text("✅ Analysis complete & persisted to Candidate Pipeline!")

            if candidate_results:
                # Sort candidates by overall score descending
                ranked_candidates = sorted(candidate_results, key=lambda x: x["score"], reverse=True)

                # Leaderboard Table with Indian Tech Features
                leaderboard_data = []
                for rank, c in enumerate(ranked_candidates, start=1):
                    badge = "🥇" if rank == 1 else ("🥈" if rank == 2 else ("🥉" if rank == 3 else f"#{rank}"))
                    notice_badge = f"⚡ {c['notice_period']}d (Immediate)" if c['notice_period'] <= 15 else f"{c['notice_period']}d"
                    tier_badge = f"🎓 {c['college_tier']}"
                    ctc_str = f"₹{c['current_ctc']}L → ₹{c['expected_ctc']}L" if c['expected_ctc'] > 0 else "Negotiable"

                    leaderboard_data.append({
                        "Rank": badge,
                        "Candidate Name": c["name"],
                        "Overall Score": f"{c['score']} / 100",
                        "Recommendation": c["recommendation"],
                        "College Tier": tier_badge,
                        "Notice Period": notice_badge,
                        "CTC (LPA)": ctc_str,
                        "Location": c["location"],
                        "Matched Skills": len(c["matched_skills"])
                    })

                df_leaderboard = pd.DataFrame(leaderboard_data)
                st.subheader("🏆 Recruiter Leaderboard")
                st.dataframe(df_leaderboard, hide_index=True)

                # Granular Breakdown Cards
                st.subheader("🔍 Granular Candidate Evaluation & Score Breakdown")

                for rank, c in enumerate(ranked_candidates, start=1):
                    with st.expander(f"Rank #{rank}: {c['name']} (Score: {c['score']}/100 - {c['recommendation']})"):
                        m_col1, m_col2, m_col3, m_col4 = st.columns(4)
                        m_col1.metric("Overall Score", f"{c['score']} / 100")
                        m_col2.metric("Skill Fit (50%)", f"{c['skill_score']}%")
                        m_col3.metric("Experience (30%)", f"{c['exp_score']}%")
                        m_col4.metric("Education (20%)", f"{c['edu_score']}%")

                        # Indian Tech Highlights Pill
                        st.markdown(
                            f"**🇮🇳 Indian Tech Profile:** 🎓 **{c['college_tier']}** ({c['college_name']}) | "
                            f"⏱️ **Notice Period:** {c['notice_period']} days | "
                            f"📍 **Location:** {c['location']} | "
                            f"💰 **Expected CTC:** {c['expected_ctc']} LPA"
                        )

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


# =========================================================
# TAB 2: Candidate Pipeline & Assessments (Option A1)
# =========================================================
with tab_pipeline:
    st.subheader("🇮🇳 Candidate Pipeline Management & HackerEarth / Mettl Assessments")
    st.markdown("Manage candidate stages through the recruitment funnel and trigger technical coding assessments.")

    # Filter by pipeline stage
    stages = ["All", "Applied", "Screened", "Shortlisted", "Assessment Sent", "Assessment Completed", "Interview Scheduled", "Offer Extended", "Rejected"]
    selected_stage = st.selectbox("Filter Candidates by Stage:", options=stages)

    candidates_list = get_all_candidates(stage_filter=selected_stage)

    if candidates_list:
        cand_df_data = []
        for cand in candidates_list:
            cand_df_data.append({
                "ID": cand["id"],
                "Name": cand["name"],
                "Stage": cand["stage"],
                "Score": f"{cand['score']}/100",
                "College Tier": cand["college_tier"],
                "Notice (Days)": cand["notice_period_days"],
                "Exp. CTC (LPA)": f"₹{cand['expected_ctc_lpa']}L" if cand['expected_ctc_lpa'] else "N/A",
                "Location": cand["current_location"],
                "Assessment Status": cand["assessment_status"] or "Not Sent",
                "Coding Score": f"{cand['assessment_score']}/100" if cand['assessment_score'] > 0 else "-"
            })

        st.dataframe(pd.DataFrame(cand_df_data), hide_index=True)

        st.divider()
        st.subheader("⚙️ Candidate Actions: Assessments & Stage Transitions")

        action_col1, action_col2 = st.columns([1, 1])

        cand_options = {f"{c['name']} (ID: {c['id']} - Stage: {c['stage']})": c["id"] for c in candidates_list}

        with action_col1:
            st.markdown("#### 🧪 Technical Assessment (HackerEarth / Mettl)")
            selected_cand_label = st.selectbox("Select Candidate for Assessment:", options=list(cand_options.keys()), key="assess_cand_select")
            chosen_cand_id = cand_options[selected_cand_label]
            chosen_cand = next(c for c in candidates_list if c["id"] == chosen_cand_id)

            provider = st.radio("Assessment Platform:", options=["HackerEarth", "Mercer | Mettl"], horizontal=True)

            a_btn_col1, a_btn_col2 = st.columns(2)
            with a_btn_col1:
                if st.button("📤 Send Assessment Invite"):
                    inv = generate_assessment_invite(
                        candidate_id=chosen_cand_id,
                        candidate_name=chosen_cand["name"],
                        candidate_email=chosen_cand["email"] or "candidate@example.com",
                        role_title="Software Engineer",
                        provider=provider
                    )
                    st.success(f"✅ Assessment invite sent via {provider}!")
                    st.info(f"🔗 **Candidate Test Link:** [{inv['invite_url']}]({inv['invite_url']})")

            with a_btn_col2:
                if st.button("⚡ Simulate Assessment Completion"):
                    sim_out = simulate_assessment_completion(chosen_cand_id, provider)
                    st.success(f"🎉 Assessment Completed! Coding Score: **{sim_out['score']}/100** ({sim_out['percentile']}th percentile)")
                    st.info(f"🛡️ Proctoring Check: {sim_out['proctoring_status']}")

        with action_col2:
            st.markdown("#### 🔄 Move Candidate Stage")
            selected_cand_stage_label = st.selectbox("Select Candidate to Move:", options=list(cand_options.keys()), key="stage_cand_select")
            stage_cand_id = cand_options[selected_cand_stage_label]

            new_stage = st.selectbox(
                "Select New Stage:",
                options=["Applied", "Screened", "Shortlisted", "Assessment Sent", "Assessment Completed", "Interview Scheduled", "Offer Extended", "Rejected"],
                key="new_stage_select"
            )

            if st.button("Update Stage"):
                update_candidate_stage(stage_cand_id, new_stage)
                st.success(f"✅ Candidate ID #{stage_cand_id} moved to **{new_stage}**!")
    else:
        st.info("No candidates found in this pipeline stage. Upload and score resumes in Tab 1 to populate the pipeline!")


# =========================================================
# TAB 3: Interview Scheduler
# =========================================================
with tab_schedule:
    st.subheader("📅 Scheduled Interviews & Slot Management")
    
    sch_col1, sch_col2 = st.columns([2, 1])

    with sch_col1:
        st.markdown("#### 📋 Booked Interviews")
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
            st.dataframe(df_scheduled, hide_index=True)
        else:
            st.info("No interviews scheduled yet.")

    with sch_col2:
        st.markdown("#### ➕ Add Interviewer Slot")
        new_slot_input = st.text_input("Enter Slot Date & Time (e.g. 2026-08-10 03:00 PM):")
        if st.button("Add Slot"):
            if new_slot_input.strip():
                new_id = create_new_slot(new_slot_input.strip())
                st.success(f"✅ Added slot ID #{new_id} ({new_slot_input})")
            else:
                st.warning("Please enter a slot time.")


# =========================================================
# TAB 4: Communication Center
# =========================================================
with tab_comm:
    st.subheader("✉️ Recruiter Communication Center")
    all_db_candidates = get_all_candidates()

    if all_db_candidates:
        c_names = {f"{c['name']} ({c['email']})": c for c in all_db_candidates}
        selected_cand_key = st.selectbox("Select Candidate to Contact:", options=list(c_names.keys()))
        cand_obj = c_names[selected_cand_key]

        comm_type = st.radio("Email Type:", options=["Interview Invitation", "Shortlist Notification", "Rejection & Feedback"], horizontal=True)

        if comm_type == "Interview Invitation":
            gen_email = generate_interview_invite_email(cand_obj["name"], "Tech Role", "2026-08-10 10:00 AM", f"https://meet.jit.si/Interview-{cand_obj['name'].replace(' ', '')}")
        elif comm_type == "Shortlist Notification":
            gen_email = generate_shortlist_email(cand_obj["name"], "Tech Role", cand_obj["score"])
        else:
            missing_skills_list = cand_obj.get("missing_skills", [])
            gen_email = generate_rejection_email(cand_obj["name"], "Tech Role", missing_skills_list)

        st.text_input("Email Subject:", value=gen_email["subject"], key="comm_subj_out")
        st.text_area("Email Body:", value=gen_email["body"], height=220, key="comm_body_out")
    else:
        st.info("No candidates in database yet. Analyze resumes in Tab 1 to generate communications!")