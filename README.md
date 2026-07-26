# 🤖 AI Recruiter Agent - HYRIX

An intelligent, multi-agent AI system designed to automate resume parsing, skill matching, candidate scoring, and ranking for recruiters.

---

## ✨ Features

- 📑 **Multi-Resume Batch Support**: Upload multiple PDF and DOCX resumes simultaneously.
- 🔍 **Analyzer Agent**:
  - Parses PDF/DOCX resumes into clean Markdown/Text.
  - Converts unstructured resume content into structured JSON (Contact, Experience, Education, Skills).
  - Matches candidate skills directly against the target Job Description (JD).
- 🎯 **Scorer Agent**:
  - Evaluates candidate fit across 3 weighted dimensions (Skill Fit, Experience, Education).
  - Computes a transparent final candidate score out of 100.
  - Generates 3-bullet recruiter evaluation summaries highlighting candidate strengths, gaps, and score rationale.
- 🏆 **Interactive Leaderboard**: Ranks candidates descending by score with visual badges, score cards, and detailed breakdowns in Streamlit.

---

## 🏗️ System Architecture & Workflow

```
[ Upload Resumes (PDF/DOCX) + Job Description ]
                       │
                       ▼
            ┌──────────────────────┐
            │    Analyzer Agent    │
            │  - PDF/DOCX Parser   │
            │  - JSON Maker        │
            │  - Skill Matcher     │
            └──────────┬───────────┘
                       │
                       ▼
            ┌──────────────────────┐
            │     Scorer Agent     │
            │  - Weighted Scoring  │
            │  - Recommendation    │
            │  - Recruiter Summary │
            └──────────┬───────────┘
                       │
                       ▼
       🏆 Streamlit Leaderboard & Ranking
```

---

## 🧮 Weighted Scoring Model

The Scoring Agent calculates candidate fit using a weighted model:

$$\text{Final Score} = (0.50 \times \text{Skill Fit}) + (0.30 \times \text{Experience}) + (0.20 \times \text{Education})$$

- **Skill Fit (50%)**: Match ratio of candidate skills vs required JD skills.
- **Experience Fit (30%)**: Alignment of work history and responsibilities.
- **Education Fit (20%)**: Academic degree and professional certifications.

| Score Range | Recommendation Tier |
| :--- | :--- |
| **85 – 100** | 🟢 **Strong Hire** |
| **70 – 84** | 🔵 **Shortlist** |
| **50 – 69** | 🟡 **Hold / Secondary Review** |
| **< 50** | 🔴 **Reject / Low Match** |

---

## 📁 Project Structure

```text
RecruiterAgent/
├── analyzer/
│   ├── parser/
│   │   ├── pdf_parser.py      # PDF parsing to Markdown
│   │   └── docx_parser.py     # DOCX parsing to text
│   ├── analyzer_agent.py      # Analyzer Agent (LangChain + ChatGroq)
│   ├── json_maker.py          # Convert resume text into structured JSON
│   ├── matcher.py             # Match skills against Job Description
│   └── skills.py              # Skill extraction from JSON
├── scorer/
│   ├── scorer_agent.py        # Scorer Agent (LangChain + ChatGroq)
│   └── score_calculator.py    # Weighted score calculation tool
├── services/
│   └── score_calculator.py    # Baseline scoring service
├── database/
│   └── database.py            # SQLite candidate storage schema
├── app.py                     # Main Streamlit web application
├── .env                       # API Key configuration
└── requirements.txt           # Python dependencies
```

---

## 🚀 Quick Start Guide

### 1. Prerequisites & Setup
Ensure Python 3.10+ is installed and configure your `.env` file in the root directory:
```env
GROQ_API_KEY="your_groq_api_key_here"
```

### 2. Activate Virtual Environment & Install Dependencies
```bash
source .venv/bin/activate
pip install -r requirements.txt
```

### 3. Launch Streamlit UI
```bash
streamlit run app.py
```

Open your browser at `http://localhost:8501` to use the application!