# 🤖 HYRIX - AI Recruiter Agent (Indian Tech Recruitment Specialist)

An enterprise-grade, autonomous dual-agent recruitment system designed for modern talent acquisition. HYRIX automates multi-resume batch parsing, Indian engineering pedigree recognition (IIT/NIT/BITS), tech-stack taxonomy matching, candidate pipeline tracking, HackerEarth/Mettl assessments, interview scheduling, and hiring analytics.

---

## ✨ Key Capabilities

- 📑 **Batch Resume Ingestion**: Simultaneous upload and asynchronous parsing of PDF and DOCX resumes.
- 🔍 **Analyzer Agent**:
  - Converts unstructured documents into standardized JSON profiles.
  - Automatically recognizes Indian technical degrees (`B.Tech`, `M.Tech`, `MCA`, `B.E.`).
  - Classifies institutions into **Tier-1** (IITs, NITs, BITS, IIITs, DTU, NSUT), **Tier-2** (VIT, Manipal, Thapar, PES, RVCE), and **Tier-3**.
  - Extracts notice periods (0/Immediate, 15d, 30d, 60d, 90d) and compensation (Current & Expected CTC in LPA).
  - Semantically matches skills using a full-stack tech taxonomy (e.g., Java $\leftrightarrow$ Spring Boot, React $\leftrightarrow$ Next.js).
- 🎯 **Scorer Agent**:
  - Deterministic 50/30/20 multi-dimensional scoring (Skill Fit 50%, Experience 30%, Education 20%).
  - Evaluates Tier-1 pedigree boosts and notice period availability advantages.
  - Generates transparent 3-bullet recruiter assessments powered by Groq `llama-3.3-70b-versatile`.
- 🇮🇳 **Candidate Pipeline & Assessments**:
  - Persistent SQLite candidate pipeline tracking stages: `Applied` $\rightarrow$ `Screened` $\rightarrow$ `Shortlisted` $\rightarrow$ `Assessment Sent` $\rightarrow$ `Assessment Completed` $\rightarrow$ `Interview Scheduled` $\rightarrow$ `Offer Extended` / `Rejected`.
  - Dispatches and evaluates coding assessments via **HackerEarth** and **Mercer | Mettl** with proctoring and anti-plagiarism verification.
- 📊 **Hiring Analytics & Export Hub**:
  - Visual charts showing stage conversion funnels and college tier distributions.
  - One-click export of candidate records into formatted **CSV** and complete **JSON**.
- 📅 **Scheduler & Communication Center**:
  - Calendar slot booking with automatic virtual meeting links (Jitsi / Google Meet).
  - One-click customized recruiter email generators (Interview Invitations, Shortlist Updates, Feedback Rejections).

---

## 🏗️ System Architecture

```
                 [ Recruiter Dashboard (Streamlit UI) ]
                                   │
         ┌─────────────────────────┴─────────────────────────┐
         ▼                                                   ▼
┌───────────────────────────────┐           ┌────────────────────────────────┐
│        ANALYZER AGENT         │           │          SCORER AGENT          │
│ • PDF/DOCX Parser             │           │ • 50/30/20 Weighted Model      │
│ • Structured JSON Maker       │──────────►│ • Tier-1 College Pedigree      │
│ • Indian Tech Recognizer      │           │ • Notice Period Evaluation     │
│ • Tech Skill Taxonomy Matcher │           │ • Recruiter LLM Rationale      │
└───────────────────────────────┘           └───────────────┬────────────────┘
                                                            │
                                                            ▼
                                            ┌────────────────────────────────┐
                                            │      PIPELINE & ANALYTICS      │
                                            │ • SQLite Candidate DB          │
                                            │ • HackerEarth / Mettl API      │
                                            │ • Interview Slot Scheduler     │
                                            │ • CSV / JSON Export Engine     │
                                            └────────────────────────────────┘
```

---

## 🧮 Weighted Scoring Formula

$$\text{Overall Score} = (0.50 \times \text{Skill Fit}) + (0.30 \times \text{Experience Fit}) + (0.20 \times \text{Education Fit}) \pm \text{Notice Period Adj.}$$

- **Skill Fit (50%)**: Match ratio of candidate skills vs required JD skills using technical ecosystem mapping.
- **Experience Fit (30%)**: Evaluation of work history, role seniority, and accomplishments.
- **Education Fit (20%)**: Academic qualification with Tier-1 (IIT/NIT/BITS) and Tier-2 institutional multipliers.
- **Notice Period Adjustment**: $+2.0$ points bonus for immediate/15-day joiners; risk adjustments for 90-day notice periods.

| Score Range | Recommendation Tier | Recommended Action |
| :--- | :--- | :--- |
| **85 – 100** | 🟢 **Strong Hire** | Fast-track to HackerEarth test / Final Interview |
| **70 – 84** | 🔵 **Shortlist** | Send technical coding assessment |
| **50 – 69** | 🟡 **Hold / Secondary Review** | Keep in pool for secondary requirements |
| **< 50** | 🔴 **Reject / Low Match** | Send polite feedback rejection email |

---

## 📁 Project Directory Structure

```text
RecruiterAgent/
├── analyzer/
│   ├── parser/
│   │   ├── pdf_parser.py             # Converts PDF resumes to Markdown (@tool)
│   │   └── docx_parser.py            # Converts DOCX resumes to plain text (@tool)
│   ├── analyzer_agent.py             # Orchestrates ingestion, extraction & matching
│   ├── indian_tech_recognizer.py     # Indian college tier, degree, notice & CTC parsing
│   ├── jd_extractor.py               # Parses unstructured JD into required skills & experience
│   ├── json_maker.py                 # Structured resume JSON generator
│   ├── matcher.py                    # Tech-specific skill taxonomy & synonym matcher
│   └── skills.py                     # Skill extraction from JSON
├── scorer/
│   ├── scorer_agent.py               # Evaluates candidate fit & writes recruiter summary
│   └── score_calculator.py           # Multi-dimensional weighted scoring tool
├── services/
│   ├── assessment_service.py         # HackerEarth & Mercer Mettl test integration & scoring
│   ├── email_templates.py            # Automated recruiter email generator
│   ├── export_service.py             # CSV/JSON candidate exports & pipeline analytics
│   ├── scheduler.py                  # Calendar slot & interview booking service
│   └── validator.py                  # Input validation for JDs and candidate records
├── database/
│   └── database.py                   # SQLite pipeline schema, migrations, and CRUD operations
├── tests/
│   ├── test_indian_recruitment.py    # Test suite for Indian tech features & assessments
│   ├── test_jd_matching.py           # Test suite for JD extraction and skill matching
│   ├── test_scheduler.py             # Test suite for interview scheduling
│   ├── test_email_templates.py       # Test suite for email generation
│   └── test_validation_exports.py    # Test suite for validation, exports, and analytics
├── app.py                            # Streamlit web application with 5 interactive tabs
├── requirements.txt                  # Python dependencies
└── .env                              # Environment secrets (GROQ_API_KEY)
```

---

## 🚀 Quick Start Guide

### 1. Prerequisites & Environment Setup
Clone the repository and verify Python 3.10+ is installed:
```bash
git clone git@github.com:codermuskan-hub/RecruiterAgent.git
cd RecruiterAgent
```

Create and activate a virtual environment:
```bash
python3 -m venv .venv
source .venv/bin/activate
```

Install all required dependencies:
```bash
pip install -r requirements.txt
```

### 2. Configure API Keys
Create a `.env` file in the root directory and add your Groq API key:
```env
GROQ_API_KEY="your_groq_api_key_here"
```
*(Get your free API key at [console.groq.com](https://console.groq.com/keys))*

### 3. Run Automated Tests
Verify all system modules before starting the UI:
```bash
python tests/test_indian_recruitment.py
python tests/test_validation_exports.py
python tests/test_jd_matching.py
python tests/test_scheduler.py
python tests/test_email_templates.py
```

### 4. Launch the Streamlit Application
```bash
streamlit run app.py
```

Open your browser at `http://localhost:8501` to use the HYRIX recruitment dashboard.