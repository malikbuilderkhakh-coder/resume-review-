import io
import re

from docx import Document
from pypdf import PdfReader

MAX_PDF_PAGES = 10  # a resume should never need more than this


def extract_text_from_pdf(file_bytes):
    """Read all text from a PDF file (given as bytes)."""
    try:
        reader = PdfReader(io.BytesIO(file_bytes))

        if reader.is_encrypted:
            # Try opening it with an empty password. 0 means it failed.
            if reader.decrypt("") == 0:
                raise ValueError("This PDF is password protected. Please upload an unprotected copy.")

        pages_text = []
        for page in reader.pages[:MAX_PDF_PAGES]:
            pages_text.append(page.extract_text() or "")
        return "\n".join(pages_text)

    except ValueError:
        raise
    except Exception:
        raise ValueError(
            "Could not read this PDF. It may be damaged. "
            "Try exporting it again as a PDF, or upload a DOCX file instead."
        )


def extract_text_from_docx(file_bytes):
    """Read all text from a DOCX file (given as bytes)."""
    try:
        document = Document(io.BytesIO(file_bytes))

        parts = [paragraph.text for paragraph in document.paragraphs]

        # Some resumes put content inside tables, so read those too.
        for table in document.tables:
            for row in table.rows:
                for cell in row.cells:
                    parts.append(cell.text)

        return "\n".join(parts)

    except Exception:
        raise ValueError(
            "Could not read this DOCX file. It may be damaged. "
            "Try saving it again as .docx or as a PDF."
        )


def extract_resume_text(filename, file_bytes):
    """Pick the right reader based on the file extension."""
    name = filename.lower()
    if name.endswith(".pdf"):
        return extract_text_from_pdf(file_bytes)
    if name.endswith(".docx"):
        return extract_text_from_docx(file_bytes)
    raise ValueError("Unsupported file type. Please upload a PDF or DOCX file.")


def clean_text(text):
    """Remove extra spaces and blank lines."""
    text = (text or "").replace("\x00", " ")
    lines = [re.sub(r"[ \t]+", " ", line).strip() for line in text.splitlines()]
    text = "\n".join(lines)
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text.strip()


def limit_text(text, max_chars):
    """Shorten very long text. Keeps the start (70%) and the end (30%).

    Returns (text, was_shortened).
    """
    if len(text) <= max_chars:
        return text, False

    start_size = int(max_chars * 0.7)
    end_size = max_chars - start_size
    shortened = text[:start_size] + "\n\n[... middle part shortened ...]\n\n" + text[-end_size:]
    return shortened, True
