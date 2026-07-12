#Fits the MD file into a specific format
#Returns a json file 
import os
from dotenv import load_dotenv
from langchain_groq import ChatGroq

load_dotenv()
GROQ_API_KEY = os.getenv("GROQ_API_KEY")


def make_json(markdown):
    """
    Input: markdown string (resume content)
    Output: dictionary with structured resume data
    """
    llm = ChatGroq(
        model="openai/gpt-oss-20b",
        api_key=GROQ_API_KEY,
        temperature=0.7,
        max_tokens=500
    )

    prompt = (
        f"Convert this resume: {markdown} to a json that stores all details "
        "like name, contact details and socials, phone, skills, experience, "
        "education, projects, certifications"
    )

    response = llm.invoke(prompt)
    return response.content