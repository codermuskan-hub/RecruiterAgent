#Converting PDF resume to Markdown for LLM to read easily
import pymupdf4llm
from langchain_core.tools import tool

@tool
def parse_pdf(file_path: str) -> str:
    """
    Input: path to a PDF file
    Output: markdown string
    """
    markdown_string = pymupdf4llm.to_markdown(file_path)
    return markdown_string

