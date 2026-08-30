import os
import sys
import importlib
import tempfile
import pandas as pd
import streamlit as st

# Ensure project root is first in sys.path
current_dir = os.path.dirname(os.path.abspath(__file__))
if current_dir not in sys.path:
    sys.path.insert(0, current_dir)

for folder in ["analyzer", "scorer", "services"]:
    fpath = os.path.join(current_dir, folder)
    if fpath not in sys.path:
        sys.path.append(fpath)

# Ensure database module is cleanly reloaded in long-running Streamlit processes
import database.database
importlib.reload(database.database)

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
    get_interview_feedback_for_candidate,
    register_user,
    authenticate_user
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

# Page configuration
st.set_page_config(
    page_title="HYRIX - Enterprise Recruiter & Talent Platform",
    page_icon="🏔️",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# Initialize Database
init_db()

# ---------------------------------------------------------
# Custom CSS for Modern Navbar, Hero Card, and Dashboard KPIs
# ---------------------------------------------------------
st.markdown("""
<style>
    /* Hide Streamlit default header decoration */
    header[data-testid="stHeader"] {
        background-color: transparent !important;
    }
    
    /* Global Card & Container Styling */
    .top-nav {
        display: flex;
        align-items: center;
        justify-content: space-between;
        padding: 12px 24px;
        background-color: #ffffff;
        border-bottom: 1px solid #e2e8f0;
        margin-bottom: 24px;
        border-radius: 8px;
    }
    .top-nav-brand {
        display: flex;
        align-items: center;
        gap: 10px;
        font-size: 1.25rem;
        font-weight: 700;
        color: #0f172a;
        text-decoration: none;
    }
    .top-nav-links {
        display: flex;
        gap: 20px;
        font-weight: 500;
        color: #475569;
    }
    
    /* Hero Banner */
    .hero-banner {
        background: linear-gradient(135deg, #1e427a 0%, #173868 100%);
        border-radius: 20px;
        padding: 48px 36px;
        color: #ffffff;
        text-align: center;
        margin-bottom: 30px;
        box-shadow: 0 10px 25px -5px rgba(15, 23, 42, 0.15);
    }
    .hero-pill {
        display: inline-block;
        background-color: rgba(255, 255, 255, 0.2);
        color: #e2e8f0;
        padding: 6px 16px;
        border-radius: 9999px;
        font-size: 0.85rem;
        font-weight: 600;
        margin-bottom: 16px;
    }
    .hero-title {
        font-size: 2.75rem;
        font-weight: 800;
        margin-bottom: 12px;
        color: #ffffff;
        letter-spacing: -0.025em;
    }
    .hero-subtitle {
        font-size: 1.1rem;
        color: #cbd5e1;
        max-width: 680px;
        margin: 0 auto 32px auto;
        line-height: 1.6;
    }
    
    /* Metric Cards (Image 2 style) */
    .kpi-card {
        border-radius: 12px;
        padding: 22px 24px;
        color: #ffffff;
        display: flex;
        flex-direction: column;
        justify-content: space-between;
        min-height: 140px;
        box-shadow: 0 4px 12px rgba(0, 0, 0, 0.08);
        transition: transform 0.2s ease;
    }
    .kpi-card:hover {
        transform: translateY(-2px);
    }
    .kpi-card-blue {
        background-color: #0066ff;
    }
    .kpi-card-green {
        background-color: #059669;
    }
    .kpi-card-cyan {
        background-color: #00b4d8;
    }
    .kpi-card-slate {
        background-color: #1e293b;
    }
    .kpi-label {
        font-size: 0.8rem;
        font-weight: 700;
        letter-spacing: 0.08em;
        text-transform: uppercase;
        opacity: 0.9;
        margin-bottom: 8px;
    }
    .kpi-value {
        font-size: 2.4rem;
        font-weight: 800;
        line-height: 1;
        margin-bottom: 12px;
    }
    .kpi-link {
        font-size: 0.85rem;
        opacity: 0.9;
        text-decoration: none;
        color: #ffffff;
        font-weight: 500;
    }
    
    /* Status Badges */
    .badge-admin {
        background-color: #334155;
        color: #f8fafc;
        padding: 4px 10px;
        border-radius: 6px;
        font-size: 0.75rem;
        font-weight: 700;
    }
    .badge-booked {
        background-color: #059669;
        color: #ffffff;
        padding: 3px 8px;
        border-radius: 4px;
        font-size: 0.75rem;
        font-weight: 700;
    }
    .badge-pending {
        background-color: #d97706;
        color: #ffffff;
        padding: 3px 8px;
        border-radius: 4px;
        font-size: 0.75rem;
        font-weight: 700;
    }
</style>
""", unsafe_allow_html=True)

# ---------------------------------------------------------
# Session State for Authentication & View Routing
# ---------------------------------------------------------
if "user" not in st.session_state:
    st.session_state["user"] = None

if "nav_view" not in st.session_state:
    st.session_state["nav_view"] = "Home"

if "show_auth_modal" not in st.session_state:
    st.session_state["show_auth_modal"] = None  # 'login' or 'signup' or None

if "login_success_alert" not in st.session_state:
    st.session_state["login_success_alert"] = False

# ---------------------------------------------------------
# Top Navigation Bar (Always at top of page)
# ---------------------------------------------------------
top_col1, top_col2, top_col3 = st.columns([3, 5, 4], vertical_alignment="center")

with top_col1:
    st.markdown(
        """
        <div style="display: flex; align-items: center; gap: 8px;">
            <span style="font-size: 1.6rem;">🏔️</span>
            <span style="font-size: 1.3rem; font-weight: 800; color: #0f172a; letter-spacing: -0.02em;">HYRIX Platform</span>
        </div>
        """,
        unsafe_allow_html=True
    )

with top_col2:
    if st.session_state["user"] is not None:
        # Logged-in top navbar tabs matching reference image 2
        dash_cols = st.columns(6)
        with dash_cols[0]:
            if st.button("📊 Dashboard", type="tertiary", key="nav_dash"):
                st.session_state["nav_view"] = "Dashboard"
        with dash_cols[1]:
            if st.button("💼 Jobs", type="tertiary", key="nav_jobs"):
                st.session_state["nav_view"] = "Jobs"
        with dash_cols[2]:
            if st.button("🚀 Screening", type="tertiary", key="nav_screen"):
                st.session_state["nav_view"] = "Screening"
        with dash_cols[3]:
            if st.button("👥 Pipeline", type="tertiary", key="nav_pipe"):
                st.session_state["nav_view"] = "Pipeline"
        with dash_cols[4]:
            if st.button("📅 Schedule", type="tertiary", key="nav_sched"):
                st.session_state["nav_view"] = "Schedule"
        with dash_cols[5]:
            if st.button("📈 Analytics", type="tertiary", key="nav_analytics"):
                st.session_state["nav_view"] = "Analytics"
    else:
        st.caption("Enterprise AI Recruitment & Outdoor Expedition Architecture")

with top_col3:
    if st.session_state["user"] is None:
        auth_c1, auth_c2 = st.columns([1, 1])
        with auth_c1:
            if st.button("🚪 Log In", width="stretch"):
                st.session_state["show_auth_modal"] = "login"
        with auth_c2:
            if st.button("✨ Sign Up", type="primary", width="stretch"):
                st.session_state["show_auth_modal"] = "signup"
    else:
        u = st.session_state["user"]
        u_col1, u_col2 = st.columns([3, 1], vertical_alignment="center")
        with u_col1:
            role_label = u["role"].upper()
            st.markdown(
                f"""
                <div style="text-align: right; display: flex; align-items: center; justify-content: flex-end; gap: 8px;">
                    <span class="badge-admin">{role_label}</span>
                    <span style="font-weight: 600; color: #1e293b; font-size: 0.95rem;">{u['full_name']}</span>
                </div>
                """,
                unsafe_allow_html=True
            )
        with u_col2:
            if st.button("🚪 Logout", key="logout_btn", width="stretch"):
                st.session_state["user"] = None
                st.session_state["nav_view"] = "Home"
                st.session_state["login_success_alert"] = False
                st.rerun()

st.divider()


# ==============================================================================
# AUTHENTICATION OVERLAYS (Log In & Sign Up)
# ==============================================================================
if st.session_state["show_auth_modal"] == "login" and st.session_state["user"] is None:
    with st.container(border=True):
        st.subheader("🔑 Sign In to HYRIX")
        st.caption("Access role-based hiring dashboards and candidate intelligence.")

        l_col1, l_col2 = st.columns([2, 1])
        with l_col1:
            login_user = st.text_input("Username:", placeholder="e.g. recruiter_priya")
            login_pass = st.text_input("Password:", type="password", placeholder="Enter your password")

            b_sub1, b_sub2 = st.columns(2)
            with b_sub1:
                if st.button("Log In Now", type="primary", width="stretch"):
                    user_match = authenticate_user(login_user, login_pass)
                    if user_match:
                        st.session_state["user"] = user_match
                        st.session_state["show_auth_modal"] = None
                        st.session_state["login_success_alert"] = True
                        st.session_state["nav_view"] = "Dashboard"
                        st.rerun()
                    else:
                        st.error("Invalid username or password. Please verify credentials.")
            with b_sub2:
                if st.button("Cancel", width="stretch"):
                    st.session_state["show_auth_modal"] = None
                    st.rerun()

        with l_col2:
            st.info("**Quick Demo Credentials:**\n\n- `recruiter_priya` / `password123`\n- `manager_vikram` / `password123`\n- `interviewer_rahul` / `password123`\n- `superadmin` / `secretadmin123`")

elif st.session_state["show_auth_modal"] == "signup" and st.session_state["user"] is None:
    with st.container(border=True):
        st.subheader("📝 Create New HYRIX Account")
        st.caption("Sign up as a Recruiter, Hiring Manager, or Technical Interviewer.")

        su_col1, su_col2 = st.columns(2)
        with su_col1:
            su_username = st.text_input("Choose Username:", placeholder="e.g. rohit_ta")
            su_fullname = st.text_input("Full Name:", placeholder="e.g. Rohit Mehra")
            su_email = st.text_input("Email Address:", placeholder="e.g. rohit@techcorp.in")

        with su_col2:
            su_role = st.selectbox("Register Role:", options=["Recruiter", "Hiring Manager", "Technical Interviewer"])
            st.caption("🛡️ **Notice:** Administrator accounts cannot be registered publicly. System Admins must be provisioned directly via backend scripts (`scripts/create_admin.py`).")
            su_dept = st.text_input("Department:", value="Engineering")
            su_pass = st.text_input("Password (min 6 chars):", type="password")

        su_btn1, su_btn2 = st.columns(2)
        with su_btn1:
            if st.button("Complete Sign Up", type="primary", width="stretch"):
                ok_reg, msg_reg = register_user(su_username, su_fullname, su_role, su_email, su_pass, su_dept)
                if ok_reg:
                    st.success(msg_reg)
                    st.session_state["show_auth_modal"] = "login"
                    st.rerun()
                else:
                    st.error(msg_reg)
        with su_btn2:
            if st.button("Cancel", width="stretch"):
                st.session_state["show_auth_modal"] = None
                st.rerun()


# ==============================================================================
# VIEW 1: PUBLIC HOMEPAGE & HERO (Matching Reference Image 1)
# ==============================================================================
if st.session_state["user"] is None:
    # Large Deep Blue Hero Card
    st.markdown("""
    <div class="hero-banner">
        <div class="hero-pill">🌲 Explore Engineering Expeditions & Talent</div>
        <div class="hero-title">Find your next technical hire</div>
        <div class="hero-subtitle">
            Discover curated engineering talent, guided Indian college pedigree recognition (IIT/NIT/BITS), 
            and real-time coding assessments managed by autonomous dual agents.
        </div>
    </div>
    """, unsafe_allow_html=True)

    # Search & Filter Container (Card style matching Image 1)
    with st.container(border=True):
        search_col1, search_col2, search_col3, search_col4 = st.columns([5, 3, 3, 2], vertical_alignment="bottom")

        with search_col1:
            search_query = st.text_input(
                "Search Positions or Skills:",
                placeholder="Search by role title, tech stack (Python, Java, React)...",
                label_visibility="collapsed"
            )

        with search_col2:
            loc_filter = st.selectbox(
                "Location Filter:",
                options=["Location: All", "Bengaluru", "Delhi-NCR", "Hyderabad", "Pune", "Remote"],
                label_visibility="collapsed"
            )

        with search_col3:
            diff_filter = st.selectbox(
                "Experience Level:",
                options=["Difficulty / Exp: All", "Junior (0-2 yrs)", "Mid-Level (3-5 yrs)", "Senior / Staff (6+ yrs)"],
                label_visibility="collapsed"
            )

        with search_col4:
            search_btn = st.button("🔍 Search", type="primary", width="stretch")

        st.markdown(
            """
            <div style="display: flex; gap: 10px; align-items: center; margin-top: 12px; font-size: 0.85rem; color: #64748b;">
                <span style="font-weight: 600;">Quick Filters:</span>
                <span style="background: #1e293b; color: #fff; padding: 3px 12px; border-radius: 9999px; font-weight: 500;">All Roles</span>
                <span style="border: 1px solid #cbd5e1; padding: 3px 12px; border-radius: 9999px;">Easy / Junior</span>
                <span style="border: 1px solid #cbd5e1; padding: 3px 12px; border-radius: 9999px;">Medium / Mid</span>
                <span style="border: 1px solid #cbd5e1; padding: 3px 12px; border-radius: 9999px;">Hard / Lead</span>
            </div>
            """,
            unsafe_allow_html=True
        )

    st.markdown("### 💼 Active Open Engineering Positions")
    public_jobs = get_all_jobs(status="Open")
    if public_jobs:
        for j in public_jobs:
            with st.container(border=True):
                pj_col1, pj_col2 = st.columns([4, 1], vertical_alignment="center")
                with pj_col1:
                    st.markdown(f"#### {j['title']}")
                    st.caption(f"📍 **Location:** {j['location']} | 💼 **Department:** {j['department']} | ⏱️ **Min Experience:** {j['min_experience']} yrs | 💰 **Budget:** Up to ₹{j['budget_max_lpa']} LPA")
                    st.markdown(f"**Required Stack:** `{j['required_skills']}`")
                with pj_col2:
                    if st.button("Apply / Sign In", key=f"apply_{j['id']}", width="stretch"):
                        st.session_state["show_auth_modal"] = "login"
                        st.rerun()


# ==============================================================================
# VIEW 2: AUTHENTICATED DASHBOARD (Matching Reference Image 2)
# ==============================================================================
else:
    u = st.session_state["user"]

    # Green alert dismissable banner (Image 2)
    if st.session_state["login_success_alert"]:
        st.success("✅ Logged in successfully as " + u["role"] + " (" + u["full_name"] + ").")
        st.session_state["login_success_alert"] = False

    # Overview Header
    head_col1, head_col2 = st.columns([3, 2], vertical_alignment="center")
    with head_col1:
        st.markdown(f"## {u['role']} Overview")
        st.caption(f"Welcome back, **{u['full_name']}**! Managing talent pipelines, assessments, and engineering appointments.")

    with head_col2:
        btn_c1, btn_c2 = st.columns(2)
        with btn_c1:
            if st.button("+ Add New Job", type="primary", width="stretch"):
                st.session_state["nav_view"] = "Jobs"
                st.rerun()
        with btn_c2:
            if st.button("📋 Pipeline Actions", width="stretch"):
                st.session_state["nav_view"] = "Pipeline"
                st.rerun()

    # 4 Colorful Metric Cards (Image 2 style)
    all_cands_dash = get_all_candidates(include_archived=True)
    all_jobs_dash = get_all_jobs()
    all_users_dash = get_all_users()
    all_slots_dash = list_scheduled_interviews()

    kpi_col1, kpi_col2, kpi_col3, kpi_col4 = st.columns(4)

    with kpi_col1:
        st.markdown(
            f"""
            <div class="kpi-card kpi-card-blue">
                <div class="kpi-label">TOTAL POSITIONS</div>
                <div class="kpi-value">{len(all_jobs_dash)}</div>
                <div class="kpi-link">View All Jobs →</div>
            </div>
            """,
            unsafe_allow_html=True
        )

    with kpi_col2:
        active_candidates_count = len([c for c in all_cands_dash if not c.get("is_archived")])
        st.markdown(
            f"""
            <div class="kpi-card kpi-card-green">
                <div class="kpi-label">TOTAL CANDIDATES</div>
                <div class="kpi-value">{active_candidates_count}</div>
                <div class="kpi-link">Manage Pipeline →</div>
            </div>
            """,
            unsafe_allow_html=True
        )

    with kpi_col3:
        staff_count = len([usr for usr in all_users_dash if usr["role"] in ["Technical Interviewer", "Hiring Manager"]])
        st.markdown(
            f"""
            <div class="kpi-card kpi-card-cyan">
                <div class="kpi-label">APPROVED STAFF</div>
                <div class="kpi-value">{staff_count}</div>
                <div class="kpi-link">View Staff →</div>
            </div>
            """,
            unsafe_allow_html=True
        )

    with kpi_col4:
        st.markdown(
            f"""
            <div class="kpi-card kpi-card-slate">
                <div class="kpi-label">TOTAL BOOKINGS</div>
                <div class="kpi-value">{len(all_slots_dash)}</div>
                <div class="kpi-link">All Bookings →</div>
            </div>
            """,
            unsafe_allow_html=True
        )

    st.markdown("<br>", unsafe_allow_html=True)

    # ---------------------------------------------------------
    # Navigation View Router (Controlled via Top Navbar)
    # ---------------------------------------------------------
    current_view = st.session_state["nav_view"]

    # --- VIEW: DASHBOARD (Default Landing in Logged-In State) ---
    if current_view == "Dashboard":
        st.subheader("🕒 Recent Applications & Candidate Bookings")
        
        if all_cands_dash:
            recent_table_data = []
            for cand in all_cands_dash[:8]:
                stg_color = "badge-booked" if cand["stage"] in ["Shortlisted", "Interview Scheduled", "Offer Extended"] else "badge-pending"
                recent_table_data.append({
                    "Candidate ID": f"#{cand['id']}",
                    "Candidate Name": cand["name"],
                    "Assigned Role": f"Job #{cand.get('job_id', 1)}",
                    "Score": f"{cand['score']}/100",
                    "College Pedigree": cand.get("college_tier", "Tier-3"),
                    "Notice Period": f"{cand.get('notice_period_days', 30)} days",
                    "Pipeline Stage": cand["stage"],
                    "Assessment Status": cand.get("assessment_status", "Not Sent")
                })
            st.dataframe(pd.DataFrame(recent_table_data), hide_index=True)
        else:
            st.info("No candidate applications in the database yet. Click 'Screening' to batch upload resumes.")

    # --- VIEW: JOBS (Job Requisitions CRUD) ---
    elif current_view == "Jobs":
        st.subheader("💼 Technical Job Requisitions (CRUD Management)")
        
        j_crud_tab1, j_crud_tab2 = st.tabs(["📋 Active Open Roles", "➕ Create New Job Requisition"])
        
        with j_crud_tab1:
            jobs_list = get_all_jobs()
            if jobs_list:
                df_all_j = pd.DataFrame([
                    {
                        "ID": j["id"],
                        "Title": j["title"],
                        "Department": j["department"],
                        "Min Exp": f"{j['min_experience']} yrs",
                        "Budget": f"₹{j['budget_max_lpa']} LPA",
                        "Location": j["location"],
                        "Status": j["status"],
                        "Created By": j["created_by"]
                    }
                    for j in jobs_list
                ])
                st.dataframe(df_all_j, hide_index=True)

                st.markdown("### ⚙️ Job Status & Deletion Controls")
                job_map = {f"#{j['id']}: {j['title']}": j for j in jobs_list}
                sel_j_key = st.selectbox("Select Requisition to Update:", options=list(job_map.keys()))
                sel_j_obj = job_map[sel_j_key]

                j_act1, j_act2, j_act3 = st.columns(3)
                with j_act1:
                    if st.button("🔒 Close Position", width="stretch"):
                        update_job_status(sel_j_obj["id"], "Closed")
                        st.success(f"Position #{sel_j_obj['id']} marked as Closed.")
                        st.rerun()
                with j_act2:
                    if st.button("🔓 Re-Open Position", width="stretch"):
                        update_job_status(sel_j_obj["id"], "Open")
                        st.success(f"Position #{sel_j_obj['id']} reopened.")
                        st.rerun()
                with j_act3:
                    if st.button("🗑️ Delete Position", width="stretch"):
                        delete_job(sel_j_obj["id"])
                        st.warning(f"Position #{sel_j_obj['id']} deleted.")
                        st.rerun()
            else:
                st.info("No job requisitions found.")

        with j_crud_tab2:
            st.markdown("#### Post a New Technical Role Requisition")
            with st.form("create_job_form_dash"):
                nj_c1, nj_c2 = st.columns(2)
                with nj_c1:
                    n_title = st.text_input("Job Title:", placeholder="e.g. Lead Distributed Systems Engineer")
                    n_dept = st.selectbox("Department:", options=["Core Backend", "Platform Engineering", "Data & AI", "Frontend", "Mobile"])
                    n_skills = st.text_input("Required Skills (comma-separated):", placeholder="Python, FastAPI, Docker, Kubernetes, AWS")
                    n_exp = st.number_input("Minimum Experience (Years):", min_value=0.0, max_value=20.0, value=4.0, step=0.5)

                with nj_c2:
                    n_budget = st.number_input("Max Budget CTC (LPA):", min_value=1.0, max_value=150.0, value=28.0, step=1.0)
                    n_loc = st.selectbox("Location Model:", options=["Bengaluru (Hybrid)", "Delhi-NCR (On-site)", "Hyderabad (Hybrid)", "Pune (Hybrid)", "Remote"])
                    n_desc = st.text_area("Detailed Job Requirements & Scope:", height=120)

                sub_job = st.form_submit_button("💼 Save & Publish Job Requisition")
                if sub_job:
                    if not n_title.strip() or not n_skills.strip():
                        st.error("Title and skills are required.")
                    else:
                        create_job({
                            "title": n_title.strip(),
                            "department": n_dept,
                            "description": n_desc.strip(),
                            "required_skills": n_skills.strip(),
                            "min_experience": n_exp,
                            "budget_max_lpa": n_budget,
                            "location": n_loc,
                            "status": "Open",
                            "created_by": u["full_name"]
                        })
                        st.success(f"Job '{n_title}' created successfully!")
                        st.rerun()

    # --- VIEW: SCREENING (Batch Resume Ingestion & AI Scoring) ---
    elif current_view == "Screening":
        st.subheader("🚀 Batch Resume Ingestion & Dual-Agent Scoring")

        jobs_avail = get_all_jobs(status="Open")
        if not jobs_avail:
            st.warning("No open job requisitions available. Please create or open a job requisition first.")
        else:
            j_opts = {f"#{j['id']}: {j['title']} ({j['location']})": j for j in jobs_avail}
            col_sel_j, col_up = st.columns([1, 1])

            with col_sel_j:
                active_j_lbl = st.selectbox("Select Target Job Requisition:", options=list(j_opts.keys()))
                target_job = j_opts[active_j_lbl]
                jd_input_text = st.text_area(
                    "Role Job Description (used for AI matching):",
                    value=f"Title: {target_job['title']}\nDepartment: {target_job['department']}\nMin Exp: {target_job['min_experience']} yrs\nSkills: {target_job['required_skills']}\nBudget: ₹{target_job['budget_max_lpa']} LPA\n\n{target_job['description']}",
                    height=200
                )

            with col_up:
                batch_files = st.file_uploader(
                    "Upload Candidate Resumes (PDF / DOCX):",
                    type=["pdf", "docx"],
                    accept_multiple_files=True
                )

            if st.button("🚀 Process Batch & Compute AI Scores", type="primary"):
                is_valid, msg = validate_job_description(jd_input_text)
                if not is_valid:
                    st.error(msg)
                elif not batch_files:
                    st.warning("Please upload at least one resume.")
                else:
                    batch_results = []
                    prog = st.progress(0)
                    st_msg = st.empty()

                    t_dir = os.path.join(current_dir, "temp_uploads")
                    os.makedirs(t_dir, exist_ok=True)

                    for idx, f in enumerate(batch_files):
                        st_msg.text(f"Evaluating {idx + 1}/{len(batch_files)}: {f.name}...")
                        fpath = os.path.join(t_dir, f.name)
                        with open(fpath, "wb") as buff:
                            buff.write(f.getbuffer())

                        try:
                            a_res = run_analyzer_pipeline(fpath, jd_input_text)
                            r_json = a_res["resume_json"]
                            m_rep = a_res["match_report"]
                            i_prof = a_res.get("indian_tech_profile", {})

                            c_name = r_json.get("name")
                            if not c_name or c_name == "Unknown":
                                c_name = os.path.splitext(f.name)[0].replace("_", " ").title()

                            contact = r_json.get("contact", {}) if isinstance(r_json.get("contact"), dict) else {}
                            c_email = contact.get("email") or r_json.get("email") or f"{c_name.lower().replace(' ', '.')}@example.com"
                            c_phone = contact.get("phone") or r_json.get("phone") or "+91-XXXXXXXXXX"

                            s_res = run_scorer_pipeline(r_json, m_rep, jd_input_text, indian_profile=i_prof)

                            db_payload = {
                                "job_id": target_job["id"],
                                "name": c_name,
                                "email": c_email,
                                "phone": c_phone,
                                "skills": a_res.get("skills", []),
                                "experience": r_json.get("experience", []),
                                "education": r_json.get("education", []),
                                "score": s_res["overall_score"],
                                "matched_skills": m_rep.get("matched_skills", []),
                                "missing_skills": m_rep.get("missing_skills", []),
                                "resume_text": a_res.get("parsed_text", ""),
                                "stage": "Shortlisted" if s_res["overall_score"] >= 70 else "Screened",
                                "notice_period_days": i_prof.get("notice_period_days", 30),
                                "current_ctc_lpa": i_prof.get("current_ctc_lpa", 0.0),
                                "expected_ctc_lpa": i_prof.get("expected_ctc_lpa", 0.0),
                                "current_location": i_prof.get("current_location", "Bengaluru"),
                                "college_tier": i_prof.get("college_tier", "Tier-3"),
                                "degree": i_prof.get("degree", "B.Tech"),
                                "notes": f"Score: {s_res['overall_score']}/100. Rec: {s_res['recommendation']}"
                            }
                            new_cid = save_candidate_pipeline_record(db_payload)

                            batch_results.append({
                                "id": new_cid,
                                "name": c_name,
                                "score": s_res["overall_score"],
                                "rec": s_res["recommendation"],
                                "tier": i_prof.get("college_tier", "Tier-3"),
                                "notice": i_prof.get("notice_period_days", 30),
                                "ctc": f"₹{i_prof.get('current_ctc_lpa', 0.0)}L → ₹{i_prof.get('expected_ctc_lpa', 0.0)}L",
                                "assessment": s_res["assessment_text"],
                                "matched": m_rep.get("matched_skills", []),
                                "missing": m_rep.get("missing_skills", []),
                                "json": r_json
                            })
                        except Exception as e:
                            st.error(f"Error processing {f.name}: {str(e)}")

                        prog.progress((idx + 1) / len(batch_files))

                    st_msg.text("✅ Ingestion & Evaluation Complete!")

                    if batch_results:
                        ranked_b = sorted(batch_results, key=lambda x: x["score"], reverse=True)
                        st.subheader(f"🏆 Candidate Ranking for {target_job['title']}")
                        
                        df_res = pd.DataFrame([
                            {
                                "Rank": "🥇" if i == 1 else ("🥈" if i == 2 else ("🥉" if i == 3 else f"#{i}")),
                                "Candidate": b["name"],
                                "Score": f"{b['score']} / 100",
                                "Recommendation": b["rec"],
                                "Pedigree": f"🎓 {b['tier']}",
                                "Notice": f"⚡ {b['notice']}d" if b['notice'] <= 15 else f"{b['notice']}d",
                                "CTC": b["ctc"],
                                "Matched Skills": len(b["matched"])
                            }
                            for i, b in enumerate(ranked_b, start=1)
                        ])
                        st.dataframe(df_res, hide_index=True)

    # --- VIEW: PIPELINE (Funnel Management & Assessment API) ---
    elif current_view == "Pipeline":
        st.subheader("🇮🇳 Candidate Pipeline Management & Technical Assessments")

        all_candidates_pipe = get_all_candidates(include_archived=False)
        if all_candidates_pipe:
            df_pipe_view = pd.DataFrame([
                {
                    "ID": c["id"],
                    "Name": c["name"],
                    "Job Ref": f"Job #{c.get('job_id', 1)}",
                    "Stage": c["stage"],
                    "Score": f"{c['score']}/100",
                    "College Tier": c["college_tier"],
                    "Notice": f"{c['notice_period_days']}d",
                    "Exp. CTC": f"₹{c['expected_ctc_lpa']} LPA",
                    "Assessment": f"{c['assessment_provider'] or 'None'} ({c['assessment_status']})"
                }
                for c in all_candidates_pipe
            ])
            st.dataframe(df_pipe_view, hide_index=True)

            st.divider()
            st.markdown("### ⚙️ Manage Candidate Stages & Trigger Assessments")

            c_options_dict = {f"#{c['id']}: {c['name']} (Stage: {c['stage']})": c for c in all_candidates_pipe}
            chosen_c_label = st.selectbox("Select Candidate to Action:", options=list(c_options_dict.keys()))
            active_cand = c_options_dict[chosen_c_label]

            p_col1, p_col2, p_col3 = st.columns(3)

            with p_col1:
                st.markdown("#### 🧪 Coding Assessment")
                test_platform = st.radio("Provider:", options=["HackerEarth", "Mercer | Mettl"], horizontal=True)
                if st.button("📤 Dispatch Test Invite"):
                    ok_i, inv_data, err_i = generate_assessment_invite(
                        candidate_id=active_cand["id"],
                        candidate_name=active_cand["name"],
                        candidate_email=active_cand["email"] or "candidate@techcorp.in",
                        role_title="Software Engineer",
                        provider=test_platform
                    )
                    if ok_i:
                        st.success(f"Assessment invite dispatched via {test_platform}!")
                        st.info(f"Link: [{inv_data['invite_url']}]({inv_data['invite_url']})")
                    else:
                        st.error(err_i)

                if st.button("⚡ Simulate Completed Test Run"):
                    ok_eval, eval_data, err_eval = simulate_assessment_completion(active_cand["id"], test_platform)
                    if ok_eval:
                        st.success(f"Completed! Coding Score: **{eval_data['score']}/100** ({eval_data['percentile']}th percentile)")
                        st.rerun()
                    else:
                        st.error(err_eval)

            with p_col2:
                st.markdown("#### 🔄 Stage Progression")
                new_stg_choice = st.selectbox(
                    "Move Stage To:",
                    options=["Applied", "Screened", "Shortlisted", "Assessment Sent", "Assessment Completed", "Interview Scheduled", "Offer Extended", "Rejected"],
                    index=2
                )
                if st.button("Update Stage"):
                    update_candidate_stage(active_cand["id"], new_stg_choice)
                    st.success(f"Moved to {new_stg_choice}!")
                    st.rerun()

            with p_col3:
                st.markdown("#### 📦 Talent Pool & Compliance")
                if st.button("📦 Soft Archive Candidate"):
                    archive_candidate(active_cand["id"], True)
                    st.info("Moved to warm talent pool.")
                    st.rerun()

                if st.button("🚨 Permanent Purge (GDPR)"):
                    delete_candidate(active_cand["id"])
                    st.warning("Candidate permanently deleted.")
                    st.rerun()
        else:
            st.info("No candidates in the pipeline.")

    # --- VIEW: SCHEDULE (Calendar Slots & Meetings) ---
    elif current_view == "Schedule":
        st.subheader("📅 Interview Slot Scheduling & Calendar")
        
        sc1, sc2 = st.columns([2, 1])
        with sc1:
            st.markdown("#### 📋 Booked Candidate Interviews")
            sched_items = list_scheduled_interviews()
            if sched_items:
                df_sched_view = pd.DataFrame([
                    {
                        "Candidate": s["candidate_name"],
                        "Role": s["role_title"],
                        "Time": s["slot_time"],
                        "Meeting Room": s["meeting_link"],
                        "Status": s["status"]
                    }
                    for s in sched_items
                ])
                st.dataframe(df_sched_view, hide_index=True)
            else:
                st.info("No interviews scheduled yet.")

        with sc2:
            st.markdown("#### ➕ Add New Interviewer Slot")
            new_slot_str = st.text_input("Date & Time (e.g. 2026-08-30 03:00 PM):")
            if st.button("Create Slot"):
                if new_slot_str.strip():
                    slot_nid = create_new_slot(new_slot_str.strip())
                    st.success(f"Created Slot #{slot_nid}!")
                    st.rerun()
                else:
                    st.warning("Please enter a valid time.")

    # --- VIEW: ANALYTICS (KPIs & CSV/JSON Export) ---
    elif current_view == "Analytics":
        st.subheader("📈 Recruitment Funnel Analytics & Compliance Data Exports")
        
        all_cands_stat = get_all_candidates(include_archived=True)
        if all_cands_stat:
            stats = compute_hiring_analytics(all_cands_stat)

            c1, c2, c3, c4 = st.columns(4)
            c1.metric("Total Applications", stats["total_candidates"])
            c2.metric("Average Score", f"{stats['avg_score']} / 100")
            c3.metric("Avg Notice Period", f"{stats['avg_notice_period']} days")
            c4.metric("Assessment Pass Rate", stats["assessment_completion_rate"])

            chart1, chart2 = st.columns(2)
            with chart1:
                st.markdown("#### 📊 Funnel Stage Distribution")
                df_stg_c = pd.DataFrame(list(stats["stage_distribution"].items()), columns=["Stage", "Count"])
                st.bar_chart(df_stg_c.set_index("Stage"))

            with chart2:
                st.markdown("#### 🎓 Indian College Tier Distribution")
                df_tier_c = pd.DataFrame(list(stats["tier_distribution"].items()), columns=["College Tier", "Count"])
                st.bar_chart(df_tier_c.set_index("College Tier"))

            st.divider()
            st.markdown("### 📥 Export System Records")
            exp_c1, exp_c2 = st.columns(2)
            with exp_c1:
                csv_str = export_candidates_to_csv(all_cands_stat)
                st.download_button(
                    label="📄 Download Candidate Summary (CSV)",
                    data=csv_str,
                    file_name="hyrix_talent_pool.csv",
                    mime="text/csv",
                    width="stretch"
                )
            with exp_c2:
                json_str = export_candidates_to_json(all_cands_stat)
                st.download_button(
                    label="📦 Download Full Candidate Database (JSON)",
                    data=json_str,
                    file_name="hyrix_talent_pool.json",
                    mime="application/json",
                    width="stretch"
                )
        else:
            st.info("No candidates recorded in database yet.")