import streamlit as st

from parser.pdf_parser import parse_pdf
from services.json_maker import make_json
from nlp.skills import extract_skills
from nlp.matcher import match_skills

st.title("AI Recruiter Agent - Week 1 Testing")

# Job Description input
st.subheader("Job Description")
job_description = st.text_area(
    "Enter the Job Description here",
    height=200,
    placeholder="Paste or type the job description..."
)

# Resume upload
st.subheader("Upload Resume")
uploaded_file = st.file_uploader(
    "Upload a resume (PDF only for now)",
    type=["pdf"]
)

if st.button("Run Tests"):

    #Upload
    if uploaded_file:
        st.success("Uploaded Successfully")

        # Save uploaded file temporarily so pymupdf can read it
        temp_path = "temp_resume.pdf"
        with open(temp_path, "wb") as f:
            f.write(uploaded_file.getbuffer())

        #Parse PDF -> Markdown
        markdown_text = parse_pdf(temp_path)
        st.write("**First 200 characters of Markdown:**")
        st.write(markdown_text[:200])

        #Markdown -> Groq -> JSON
        resume_json = make_json(markdown_text)
        st.write("**Returned JSON:**")
        st.write(resume_json)

        #Extract skills
        skills = extract_skills(resume_json)
        st.write("**Extracted Skills:**")
        st.write(skills)

        #Match against Job Description
        if job_description.strip():
            match_result = match_skills(job_description, skills)
            st.write("**Matched Skills:**")
            st.write(match_result["matched_skills"])
            st.write("**Missing Skills:**")
            st.write(match_result["missing_skills"])
        else:
            st.warning("No Job Description entered.")

    else:
        st.warning("No resume uploaded.")
        