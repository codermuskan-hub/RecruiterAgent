#Fits the MD file into a specific format
#Returns a json file 
import os
import json 
from dotenv import load_dotenv
from langchain_groq import ChatGroq
from langchain_core.tools import tool

load_dotenv()
GROQ_API_KEY = os.getenv("GROQ_API_KEY")

def clean_text(text):
    """
    Input: Unclean JSON string returned by LLM
    Output: Cleaned up JSON string, that is acceptable to the "json.loads()" function 
    """
    if text.startswith("```json"):
        text = text.replace("```json", "").replace("```", "").strip()
    elif text.startswith("```"):
        text = text.replace("```", "").strip()

    return text 

@tool
def make_json(markdown):
    """
    Input: markdown string (resume content)
    Output: dictionary with structured resume data
    """
    llm = ChatGroq(
        model="openai/gpt-oss-20b",
        api_key=GROQ_API_KEY,
        temperature=0.0,
        max_tokens=2000,
        model_kwargs = {
            "response_format": {"type": "json_object"}
        }
    )

    prompt = (
        f"Convert this resume: {markdown} to a JSON that stores all details "
        "like name, contact details and socials, phone, skills, experience, "
        "education, projects, certifications etc. Output strictly valid JSON. Do not include markdown formatting, do not use single quotes, do not include trailing commas, and do not add any conversational text. "
    )

    response = llm.invoke(prompt)
    json_string = clean_text(response.content)

    print(repr(json_string))
    profile_dict = json.loads(json_string)
    return  profile_dict

