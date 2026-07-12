import docx


def parse_docx(file_path):
    """
    Input: path to a DOCX file
    Output: plain text string
    """
    document = docx.Document(file_path)
    full_text = []

    for paragraph in document.paragraphs:
        full_text.append(paragraph.text)

    return "\n".join(full_text)