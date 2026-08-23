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
    init_db,
    get_all_users,
    get_all_jobs,
    get_job_by_id,
    create_job,
    update_job_status,
    delete_job,
    save_candidate_pipeline_record,
    get_all_candidates,
    update_candidate_stage,
    update_candidate_manager_decision,
    archive_candidate,
    delete_candidate,
    get_candidate_by_id,
    submit_interview_feedback,
    get_interview_feedback_for_candidate
)
from services.validator import (
    validate_job_description,
    validate_candidate_data
)
from services.assessment_service import (
    generate_assessment_invite,
    simulate_assessment_completion
)
from services.export_service import (
    export_candidates_to_csv,
    export_candidates_to_json,
    compute_hiring_analytics
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
    page_title="HYRIX - Enterprise AI Recruitment Platform",
    page_icon="🤖",
    layout="wide"
)

# Initialize Database
init_db()

# ---------------------------------------------------------
# Sidebar: Role-Based Access Control (RBAC) & Profile Switcher
# ---------------------------------------------------------
st.sidebar.title("🔐 Access Control")

role_options = [
    "🎯 Recruiter (Talent Acquisition)",
    "👔 Hiring Manager (Engineering Lead)",
    "💻 Technical Interviewer / Staff",
    "⚙️ Administrator & HR Ops"
]

selected_role_raw = st.sidebar.selectbox("Active Persona / Role:", options=role_options)
active_role = selected_role_raw.split(" ")[1]  # 'Recruiter', 'Hiring', 'Technical', 'Administrator'

users = get_all_users()
role_user_map = {
    "Recruiter": next((u for u in users if u["role"] == "Recruiter"), None),
    "Hiring": next((u for u in users if u["role"] == "Hiring Manager"), None),
    "Technical": next((u for u in users if u["role"] == "Technical Interviewer"), None),
    "Administrator": next((u for u in users if u["role"] == "Admin"), None)
}
current_user = role_user_map.get(active_role)

if current_user:
    st.sidebar.markdown(f"**Logged In As:** `{current_user['full_name']}`")
    st.sidebar.caption(f"**Department:** {current_user['department']} | **Email:** {current_user['email']}")

st.sidebar.divider()

# ---------------------------------------------------------
# Application Header
# ---------------------------------------------------------
st.title("🤖 HYRIX: Enterprise AI Recruiter & Talent Platform")
st.markdown(
    f"Role-Based Workspace: **{selected_role_raw}** | Indian Tech Ecosystem Specialist & Candidate Pipeline Engine"
)


# ==============================================================================
# WORKSPACE 1: 🎯 RECRUITER WORKSPACE
# ==============================================================================
if active_role == "Recruiter":
    rec_tab1, rec_tab2, rec_tab3, rec_tab4 = st.tabs([
        "🚀 Batch Screening & AI Scoring",
        "🇮🇳 Candidate Pipeline & Actions",
        "📅 Interview Scheduling",
        "✉️ Candidate Communications"
    ])

    # TAB 1: Batch Screening & Scoring
    with rec_tab1:
        st.subheader("🚀 Resume Ingestion & Dual-Agent Evaluation")

        jobs = get_all_jobs(status="Open")
        job_choices = {f"#{j['id']} - {j['title']} ({j['location']})": j for j in jobs}
        
        col_j, col_u = st.columns([1, 1])
        with col_j:
            selected_job_label = st.selectbox("Assign Resumes to Open Job Requisition:", options=list(job_choices.keys()))
            selected_job = job_choices[selected_job_label]
            
            jd_text = st.text_area(
                "Job Description Requirements:",
                value=f"Title: {selected_job['title']}\nDepartment: {selected_job['department']}\nLocation: {selected_job['location']}\nMin Experience: {selected_job['min_experience']} years\nRequired Skills: {selected_job['required_skills']}\nBudget: Up to ₹{selected_job['budget_max_lpa']} LPA\n\n{selected_job['description']}",
                height=180
            )

        with col_u:
            uploaded_files = st.file_uploader(
                f"Upload Batch Resumes (PDF or DOCX) for Job #{selected_job['id']}:",
                type=["pdf", "docx"],
                accept_multiple_files=True
            )

        if st.button("🚀 Analyze, Score & Rank Candidates", type="primary"):
            is_valid_jd, jd_msg = validate_job_description(jd_text)
            if not is_valid_jd:
                st.error(f"❌ {jd_msg}")
            elif not uploaded_files:
                st.warning("⚠️ Please select at least one resume to upload.")
            else:
                candidate_results = []
                progress = st.progress(0)
                status_text = st.empty()

                temp_dir = os.path.join(current_dir, "temp_uploads")
                os.makedirs(temp_dir, exist_ok=True)

                for idx, file in enumerate(uploaded_files):
                    status_text.text(f"Processing candidate {idx + 1}/{len(uploaded_files)}: {file.name}...")
                    file_path = os.path.join(temp_dir, file.name)
                    with open(file_path, "wb") as f:
                        f.write(file.getbuffer())

                    try:
                        # 1. Run Analyzer Pipeline
                        analyzer_res = run_analyzer_pipeline(file_path, jd_text)
                        resume_json = analyzer_res["resume_json"]
                        match_report = analyzer_res["match_report"]
                        indian_profile = analyzer_res.get("indian_tech_profile", {})

                        c_name = resume_json.get("name")
                        if not c_name or c_name == "Unknown":
                            c_name = os.path.splitext(file.name)[0].replace("_", " ").title()

                        contact = resume_json.get("contact", {}) if isinstance(resume_json.get("contact"), dict) else {}
                        c_email = contact.get("email") or resume_json.get("email") or f"{c_name.lower().replace(' ', '.')}@example.com"
                        c_phone = contact.get("phone") or resume_json.get("phone") or "+91-XXXXXXXXXX"

                        # 2. Run Scorer Pipeline
                        scorer_res = run_scorer_pipeline(resume_json, match_report, jd_text, indian_profile=indian_profile)

                        # 3. Save Candidate in SQLite Pipeline linked to Job ID
                        db_cand = {
                            "job_id": selected_job["id"],
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
                            "current_location": indian_profile.get("current_location", "Bengaluru / NCR"),
                            "college_tier": indian_profile.get("college_tier", "Tier-3"),
                            "degree": indian_profile.get("degree", "B.Tech"),
                            "notes": f"Score: {scorer_res['overall_score']}/100. Rec: {scorer_res['recommendation']}"
                        }
                        cand_id = save_candidate_pipeline_record(db_cand)

                        candidate_results.append({
                            "id": cand_id,
                            "name": c_name,
                            "score": scorer_res["overall_score"],
                            "recommendation": scorer_res["recommendation"],
                            "college_tier": indian_profile.get("college_tier", "Tier-3"),
                            "notice_period": indian_profile.get("notice_period_days", 30),
                            "ctc": f"₹{indian_profile.get('current_ctc_lpa', 0.0)}L → ₹{indian_profile.get('expected_ctc_lpa', 0.0)}L",
                            "matched_skills": match_report.get("matched_skills", []),
                            "missing_skills": match_report.get("missing_skills", []),
                            "assessment": scorer_res["assessment_text"],
                            "resume_json": resume_json
                        })
                    except Exception as e:
                        st.error(f"Error processing {file.name}: {str(e)}")

                    progress.progress((idx + 1) / len(uploaded_files))

                status_text.text("✅ Analysis complete! All candidates recorded into the Talent Pipeline.")

                if candidate_results:
                    ranked = sorted(candidate_results, key=lambda x: x["score"], reverse=True)
                    st.subheader(f"🏆 Candidate Leaderboard for Job #{selected_job['id']}: {selected_job['title']}")

                    df_lb = pd.DataFrame([
                        {
                            "Rank": "🥇" if i == 1 else ("🥈" if i == 2 else ("🥉" if i == 3 else f"#{i}")),
                            "Name": c["name"],
                            "Overall Score": f"{c['score']} / 100",
                            "Recommendation": c["recommendation"],
                            "College Tier": f"🎓 {c['college_tier']}",
                            "Notice Period": f"⚡ {c['notice_period']}d (Immediate)" if c['notice_period'] <= 15 else f"{c['notice_period']}d",
                            "CTC Range": c["ctc"],
                            "Matched Skills": len(c["matched_skills"])
                        }
                        for i, c in enumerate(ranked, start=1)
                    ])
                    st.dataframe(df_lb, hide_index=True)

    # TAB 2: Candidate Pipeline & Actions
    with rec_tab2:
        st.subheader("🇮🇳 Talent Pipeline Management & Candidate Operations")

        filter_col1, filter_col2 = st.columns([1, 1])
        with filter_col1:
            all_jobs_opts = {f"Job #{j['id']}: {j['title']}": j['id'] for j in get_all_jobs()}
            all_jobs_opts["All Jobs"] = None
            sel_job_filt_label = st.selectbox("Filter by Job:", options=list(all_jobs_opts.keys()))
            sel_job_id = all_jobs_opts[sel_job_filt_label]

        with filter_col2:
            stg_list = ["All", "Applied", "Screened", "Shortlisted", "Assessment Sent", "Assessment Completed", "Interview Scheduled", "Offer Extended", "Rejected"]
            sel_stage = st.selectbox("Filter by Pipeline Stage:", options=stg_list)

        pipeline_candidates = get_all_candidates(stage_filter=sel_stage, job_id_filter=sel_job_id, include_archived=False)

        if pipeline_candidates:
            df_pipe = pd.DataFrame([
                {
                    "ID": c["id"],
                    "Name": c["name"],
                    "Stage": c["stage"],
                    "Score": f"{c['score']}/100",
                    "College Tier": c["college_tier"],
                    "Notice": f"{c['notice_period_days']}d",
                    "Exp. CTC": f"₹{c['expected_ctc_lpa']}L",
                    "Assessment": f"{c['assessment_provider'] or 'None'} ({c['assessment_status']})"
                }
                for c in pipeline_candidates
            ])
            st.dataframe(df_pipe, hide_index=True)

            st.divider()
            st.subheader("⚙️ Candidate Action Center")

            cand_select_map = {f"#{c['id']} - {c['name']} (Stage: {c['stage']})": c for c in pipeline_candidates}
            selected_cand_label = st.selectbox("Select Candidate to Manage:", options=list(cand_select_map.keys()))
            chosen_c = cand_select_map[selected_cand_label]

            act_col1, act_col2, act_col3 = st.columns(3)

            with act_col1:
                st.markdown("#### 🧪 Technical Assessment")
                prov = st.radio("Platform:", options=["HackerEarth", "Mercer | Mettl"], horizontal=True)
                if st.button("📤 Send Assessment Invite"):
                    ok_inv, inv, err = generate_assessment_invite(chosen_c["id"], chosen_c["name"], chosen_c["email"] or "dev@example.com", "Software Engineer", prov)
                    if ok_inv:
                        st.success(f"Sent {prov} test!")
                        st.info(f"Link: [{inv['invite_url']}]({inv['invite_url']})")
                    else:
                        st.error(err)

                if st.button("⚡ Simulate Completed Test"):
                    ok_s, sim, err_s = simulate_assessment_completion(chosen_c["id"], prov)
                    if ok_s:
                        st.success(f"Completed! Score: {sim['score']}/100 ({sim['percentile']}th percentile)")
                    else:
                        st.error(err_s)

            with act_col2:
                st.markdown("#### 🔄 Pipeline Stage Progression")
                new_stg = st.selectbox(
                    "Advance / Change Stage:",
                    options=["Applied", "Screened", "Shortlisted", "Assessment Sent", "Assessment Completed", "Interview Scheduled", "Offer Extended", "Rejected"],
                    key="rec_new_stage"
                )
                if st.button("Update Candidate Stage"):
                    update_candidate_stage(chosen_c["id"], new_stg)
                    st.success(f"Candidate moved to **{new_stg}**!")

            with act_col3:
                st.markdown("#### 🗑️ Talent Pool Governance (CRUD)")
                if st.button("📦 Soft Archive Candidate"):
                    archive_candidate(chosen_c["id"], True)
                    st.info("Candidate archived to warm talent pool.")

                if st.button("🚨 Permanent Purge (GDPR)", help="Permanently deletes candidate record"):
                    delete_candidate(chosen_c["id"])
                    st.warning("Candidate permanently purged from database.")
        else:
            st.info("No candidates found under this filter.")

    # TAB 3: Interview Scheduling
    with rec_tab3:
        st.subheader("📅 Recruiter Interview Slot Scheduler")
        sch_col1, sch_col2 = st.columns([2, 1])

        with sch_col1:
            st.markdown("#### 📋 Booked Interviews")
            scheduled = list_scheduled_interviews()
            if scheduled:
                df_sch = pd.DataFrame([
                    {
                        "Candidate": s["candidate_name"],
                        "Role": s["role_title"],
                        "Interview Time": s["slot_time"],
                        "Meeting Link": s["meeting_link"],
                        "Status": s["status"]
                    }
                    for s in scheduled
                ])
                st.dataframe(df_sch, hide_index=True)
            else:
                st.info("No interviews booked yet.")

        with sch_col2:
            st.markdown("#### ➕ Add Interview Slot")
            new_slot = st.text_input("Date & Time (e.g. 2026-08-25 04:00 PM):")
            if st.button("Add Slot"):
                if new_slot.strip():
                    sid = create_new_slot(new_slot.strip())
                    st.success(f"Added Slot #{sid}")
                else:
                    st.warning("Enter slot time.")

    # TAB 4: Candidate Communications
    with rec_tab4:
        st.subheader("✉️ Automated Candidate Email Generator")
        all_cands = get_all_candidates()
        if all_cands:
            c_dict = {f"{c['name']} ({c['email']})": c for c in all_cands}
            sel_k = st.selectbox("Select Recipient Candidate:", options=list(c_dict.keys()))
            cand_to_mail = c_dict[sel_k]

            m_type = st.radio("Communication Type:", options=["Interview Invitation", "Shortlist Notification", "Rejection & Feedback"], horizontal=True)

            if m_type == "Interview Invitation":
                mail = generate_interview_invite_email(cand_to_mail["name"], "Tech Role", "2026-08-25 04:00 PM", f"https://meet.jit.si/Interview-{cand_to_mail['name'].replace(' ', '')}")
            elif m_type == "Shortlist Notification":
                mail = generate_shortlist_email(cand_to_mail["name"], "Tech Role", cand_to_mail["score"])
            else:
                mail = generate_rejection_email(cand_to_mail["name"], "Tech Role", cand_to_mail.get("missing_skills", []))

            st.text_input("Subject:", value=mail["subject"])
            st.text_area("Body:", value=mail["body"], height=200)
        else:
            st.info("No candidates in database.")


# ==============================================================================
# WORKSPACE 2: 👔 HIRING MANAGER WORKSPACE
# ==============================================================================
elif active_role == "Hiring":
    mgr_tab1, mgr_tab2 = st.tabs([
        "💼 Job Requisitions Management (CRUD)",
        "🎯 Shortlisted Candidates & Offer Approval"
    ])

    with mgr_tab1:
        st.subheader("💼 Engineering Job Requisitions")
        st.markdown("Create, update, and manage open technical requisitions and team hiring budgets.")

        all_jobs = get_all_jobs()
        if all_jobs:
            df_jobs = pd.DataFrame([
                {
                    "Job ID": j["id"],
                    "Title": j["title"],
                    "Department": j["department"],
                    "Min Exp": f"{j['min_experience']} yrs",
                    "Budget (Max)": f"₹{j['budget_max_lpa']} LPA",
                    "Location": j["location"],
                    "Status": j["status"],
                    "Created By": j["created_by"]
                }
                for j in all_jobs
            ])
            st.dataframe(df_jobs, hide_index=True)

        st.divider()
        st.markdown("### ➕ Create New Technical Job Requisition")
        
        with st.form("create_job_form"):
            j_col1, j_col2 = st.columns(2)
            with j_col1:
                new_title = st.text_input("Job Title:", placeholder="e.g. Senior Machine Learning Engineer")
                new_dept = st.selectbox("Department:", options=["Core Backend", "Platform Engineering", "Data & AI", "Frontend", "Mobile"])
                new_skills = st.text_input("Key Required Skills (comma-separated):", placeholder="Python, PyTorch, Docker, FastAPI, Kubernetes")
                new_exp = st.number_input("Minimum Experience (Years):", min_value=0.0, max_value=20.0, value=3.0, step=0.5)

            with j_col2:
                new_budget = st.number_input("Max Budget CTC (LPA):", min_value=1.0, max_value=150.0, value=25.0, step=1.0)
                new_loc = st.selectbox("Location Model:", options=["Bengaluru (Hybrid)", "Delhi-NCR (On-site)", "Hyderabad (Hybrid)", "Pune (Hybrid)", "Remote"])
                new_desc = st.text_area("Detailed Role Responsibilities & Requirements:", height=130)

            submitted_job = st.form_submit_button("💼 Post Job Requisition")
            if submitted_job:
                if not new_title.strip() or not new_skills.strip():
                    st.error("Please provide both a Job Title and Required Skills.")
                else:
                    new_jid = create_job({
                        "title": new_title.strip(),
                        "department": new_dept,
                        "description": new_desc.strip(),
                        "required_skills": new_skills.strip(),
                        "min_experience": new_exp,
                        "budget_max_lpa": new_budget,
                        "location": new_loc,
                        "status": "Open",
                        "created_by": current_user["full_name"] if current_user else "Hiring Manager"
                    })
                    st.success(f"✅ Job Requisition #{new_jid} ('{new_title}') posted successfully!")

        st.divider()
        st.markdown("### ⚙️ Manage Existing Requisition Status")
        if all_jobs:
            j_options = {f"#{j['id']}: {j['title']} (Status: {j['status']})": j for j in all_jobs}
            sel_job_to_mod = st.selectbox("Select Job to Modify:", options=list(j_options.keys()))
            target_j = j_options[sel_job_to_mod]

            j_btn1, j_btn2 = st.columns(2)
            with j_btn1:
                if st.button("🔒 Close Requisition"):
                    update_job_status(target_j["id"], "Closed")
                    st.info(f"Job #{target_j['id']} marked as Closed.")
            with j_btn2:
                if st.button("🔓 Re-Open Requisition"):
                    update_job_status(target_j["id"], "Open")
                    st.success(f"Job #{target_j['id']} re-opened!")

    with mgr_tab2:
        st.subheader("🎯 Shortlisted Candidates & Executive Offer Approval")
        st.markdown("Review candidates who passed AI screening and technical assessments to approve job offers.")

        manager_candidates = get_all_candidates(include_archived=False)
        shortlisted_cands = [c for c in manager_candidates if c["stage"] in ["Shortlisted", "Assessment Completed", "Interview Scheduled", "Offer Extended"]]

        if shortlisted_cands:
            df_sh = pd.DataFrame([
                {
                    "Candidate ID": c["id"],
                    "Name": c["name"],
                    "Stage": c["stage"],
                    "Score": f"{c['score']}/100",
                    "College Tier": f"🎓 {c['college_tier']}",
                    "Notice": f"{c['notice_period_days']} days",
                    "Exp. CTC": f"₹{c['expected_ctc_lpa']} LPA",
                    "Offer Decision": c.get("offer_status", "Pending"),
                    "Assessment": f"{c['assessment_score']}/100" if c['assessment_score'] > 0 else "N/A"
                }
                for c in shortlisted_cands
            ])
            st.dataframe(df_sh, hide_index=True)

            st.divider()
            st.markdown("### ✍️ Executive Decision & Offer Authorization")
            
            c_opts = {f"#{c['id']} - {c['name']} (Score: {c['score']}/100)": c for c in shortlisted_cands}
            sel_c_label = st.selectbox("Select Candidate for Executive Decision:", options=list(c_opts.keys()))
            cand_eval = c_opts[sel_c_label]

            # Display Candidate Technical Dossier & Scorecards
            st.markdown(f"**Candidate:** `{cand_eval['name']}` | **Pedigree:** `{cand_eval['college_tier']}` ({cand_eval['degree']}) | **Location:** `{cand_eval['current_location']}`")
            
            # Show Interviewer Scorecards if available
            fb_list = get_interview_feedback_for_candidate(cand_eval["id"])
            if fb_list:
                st.markdown("#### 📝 Technical Interviewer Feedback History:")
                for fb in fb_list:
                    st.info(
                        f"**Interviewer:** {fb['interviewer_name']} | **Recommendation:** `{fb['overall_recommendation']}` | "
                        f"**Tech:** {fb['technical_rating']}/5 | **System Design:** {fb['system_design_rating']}/5\n\n"
                        f"*Notes:* {fb['feedback_notes']}"
                    )

            dec_col1, dec_col2 = st.columns([1, 1])
            with dec_col1:
                mgr_action = st.radio(
                    "Manager Authorization Decision:",
                    options=["Approved for Offer", "Hold / Secondary Review", "Rejected"],
                    horizontal=True
                )
            with dec_col2:
                mgr_comment = st.text_input("Offer Compensation / Feedback Notes:", placeholder="e.g. Approved for Senior Backend role. Offer ₹24 LPA + 2L joining bonus.")

            if st.button("Authorize Decision"):
                update_candidate_manager_decision(cand_eval["id"], mgr_action, mgr_comment)
                st.success(f"Candidate #{cand_eval['id']} ({cand_eval['name']}) decision saved as **{mgr_action}**!")
        else:
            st.info("No candidates currently in shortlisted or assessment stages.")


# ==============================================================================
# WORKSPACE 3: 💻 TECHNICAL INTERVIEWER / STAFF WORKSPACE
# ==============================================================================
elif active_role == "Technical":
    st.subheader("💻 Technical Interviewer Cockpit")
    st.markdown("View assigned candidate interviews, join video meetings, and submit official technical scorecards.")

    scheduled_interviews = list_scheduled_interviews()
    
    if scheduled_interviews:
        st.markdown("### 📋 Upcoming Assigned Interviews")
        df_int = pd.DataFrame([
            {
                "Candidate": s["candidate_name"],
                "Role Title": s["role_title"],
                "Slot Time": s["slot_time"],
                "Meeting Link": s["meeting_link"],
                "Status": s["status"]
            }
            for s in scheduled_interviews
        ])
        st.dataframe(df_int, hide_index=True)

        st.divider()
        st.markdown("### 📝 Submit Technical Evaluation Scorecard")

        int_cand_names = {f"{s['candidate_name']} ({s['role_title']})": s for s in scheduled_interviews}
        sel_int_label = st.selectbox("Select Candidate to Evaluate:", options=list(int_cand_names.keys()))
        active_int = int_cand_names[sel_int_label]

        st.markdown(f"**Meeting Link:** [{active_int['meeting_link']}]({active_int['meeting_link']})")

        # Find matching candidate record
        all_cands = get_all_candidates()
        matched_cand = next((c for c in all_cands if c["name"] == active_int["candidate_name"]), None)
        target_cand_id = matched_cand["id"] if matched_cand else 1

        with st.form("scorecard_form"):
            sc_col1, sc_col2, sc_col3 = st.columns(3)
            with sc_col1:
                tech_score = st.slider("Technical Coding & Problem Solving (1-5):", 1, 5, 4)
            with sc_col2:
                sys_score = st.slider("System Design & Architecture (1-5):", 1, 5, 4)
            with sc_col3:
                cult_score = st.slider("Communication & Cultural Fit (1-5):", 1, 5, 4)

            rec_choice = st.selectbox("Overall Hiring Recommendation:", options=["Strong Yes", "Yes", "Neutral", "No"])
            feedback_text = st.text_area("Detailed Interview Feedback & Observations:", placeholder="Candidate demonstrated strong knowledge of concurrency, REST APIs, and indexing. Suggested for immediate hire.")

            submitted_sc = st.form_submit_button("💾 Submit Official Scorecard")
            if submitted_sc:
                submit_interview_feedback({
                    "candidate_id": target_cand_id,
                    "interviewer_name": current_user["full_name"] if current_user else "Technical Interviewer",
                    "technical_rating": tech_score,
                    "system_design_rating": sys_score,
                    "cultural_fit_rating": cult_score,
                    "overall_recommendation": rec_choice,
                    "feedback_notes": feedback_text.strip()
                })
                st.success(f"✅ Technical Scorecard for **{active_int['candidate_name']}** recorded into candidate dossier!")
    else:
        st.info("No candidate interviews are currently assigned.")


# ==============================================================================
# WORKSPACE 4: ⚙️ ADMINISTRATOR & HR OPS WORKSPACE
# ==============================================================================
elif active_role == "Administrator":
    adm_tab1, adm_tab2, adm_tab3 = st.tabs([
        "📊 System Analytics & KPIs",
        "📥 Data Export & Reporting",
        "👥 User Directory & Data Governance"
    ])

    all_cands_db = get_all_candidates(include_archived=True)

    with adm_tab1:
        st.subheader("📊 Enterprise Recruitment KPIs & Funnel Analytics")
        if all_cands_db:
            kpi_data = compute_hiring_analytics(all_cands_db)

            k1, k2, k3, k4 = st.columns(4)
            k1.metric("Total Talent Pool", kpi_data["total_candidates"])
            k2.metric("Average Candidate Score", f"{kpi_data['avg_score']} / 100")
            k3.metric("Average Notice Period", f"{kpi_data['avg_notice_period']} days")
            k4.metric("Assessment Pass Rate", kpi_data["assessment_completion_rate"])

            ch1, ch2 = st.columns(2)
            with ch1:
                st.markdown("#### 📈 Candidate Pipeline Distribution")
                df_stg = pd.DataFrame(list(kpi_data["stage_distribution"].items()), columns=["Stage", "Count"])
                st.bar_chart(df_stg.set_index("Stage"))

            with ch2:
                st.markdown("#### 🎓 College Pedigree Breakdown")
                df_colls = pd.DataFrame(list(kpi_data["tier_distribution"].items()), columns=["College Tier", "Count"])
                st.bar_chart(df_colls.set_index("College Tier"))
        else:
            st.info("Database is currently empty.")

    with adm_tab2:
        st.subheader("📥 Export Pipeline Data & Compliance Backups")
        if all_cands_db:
            exp1, exp2 = st.columns(2)
            with exp1:
                csv_bytes = export_candidates_to_csv(all_cands_db)
                st.download_button(
                    label="📄 Export Candidate Summary (CSV)",
                    data=csv_bytes,
                    file_name="hyrix_recruiter_candidates.csv",
                    mime="text/csv"
                )
            with exp2:
                json_bytes = export_candidates_to_json(all_cands_db)
                st.download_button(
                    label="📦 Export Complete Talent Pool (JSON)",
                    data=json_bytes,
                    file_name="hyrix_recruiter_candidates.json",
                    mime="application/json"
                )

    with adm_tab3:
        st.subheader("👥 System User Accounts & Roles")
        df_users = pd.DataFrame([
            {
                "User ID": u["id"],
                "Username": u["username"],
                "Full Name": u["full_name"],
                "Assigned Role": u["role"],
                "Department": u["department"],
                "Email": u["email"]
            }
            for u in users
        ])
        st.dataframe(df_users, hide_index=True)

        st.divider()
        st.subheader("🛡️ Talent Pool Archival Governance")
        archived_candidates = [c for c in all_cands_db if c.get("is_archived")]
        if archived_candidates:
            st.markdown(f"**Archived Candidates in Talent Pool:** `{len(archived_candidates)}`")
            for ac in archived_candidates:
                a_col1, a_col2 = st.columns([3, 1])
                a_col1.write(f"Candidate #{ac['id']}: **{ac['name']}** ({ac['email']}) - Stage: `{ac['stage']}`")
                if a_col2.button(f"Restore #{ac['id']}", key=f"restore_{ac['id']}"):
                    archive_candidate(ac["id"], False)
                    st.success(f"Candidate #{ac['id']} restored to active pipeline!")
        else:
            st.info("No candidates are currently archived.")