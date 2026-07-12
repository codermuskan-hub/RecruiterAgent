#Converting PDF resume to Markdown for LLM to read easily
import pymupdf4llm


def parse_pdf(file_path):
    """
    Input: path to a PDF file
    Output: markdown string
    """
    markdown_string = pymupdf4llm.to_markdown(file_path)
    return markdown_string
