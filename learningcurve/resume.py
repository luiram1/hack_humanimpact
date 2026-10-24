"""Extract resume text in memory without saving uploaded documents."""
from io import BytesIO

from matching import MAX_EXPERIENCE_CHARS

MAX_RESUME_BYTES = 5 * 1024 * 1024
MAX_RESUME_PAGES = 10


def extract_resume(data):
    if not data:
        raise ValueError('This file is empty. Upload a PDF resume.')
    if len(data) > MAX_RESUME_BYTES:
        raise ValueError('Upload a PDF resume smaller than 5 MB.')
    if not data.lstrip().startswith(b'%PDF-'):
        raise ValueError('This file is not a PDF. Export your resume as a PDF and try again.')
    try:
        from pypdf import PdfReader
    except ModuleNotFoundError as exc:
        if exc.name != 'pypdf':
            raise
        raise ValueError('PDF resume uploads are unavailable because the server is missing pypdf. Redeploy with the updated requirements.txt, or enter your experience below.') from None
    try:
        reader = PdfReader(BytesIO(data))
        if reader.is_encrypted:
            raise ResumeError('This PDF is password protected. Upload an unprotected copy.')
        if len(reader.pages) > MAX_RESUME_PAGES:
            raise ResumeError('Upload a resume with 10 pages or fewer.')
        pages = []
        for page in reader.pages:
            text = (page.extract_text() or '').replace('\x00', '').strip()
            if not text:
                raise ResumeError('A page has no readable text. Upload a text-based PDF or a copy processed with OCR, or describe your experience below.')
            pages.append(text)
        text = '\n\n'.join(pages)
    except ResumeError:
        raise
    except Exception as exc:
        raise ValueError('This PDF could not be read. Export a new PDF copy and try again.') from exc
    if not text:
        raise ValueError('No readable text was found. Upload a text-based PDF or describe your experience below.')
    if len(text) > MAX_EXPERIENCE_CHARS:
        raise ValueError('This resume exceeds 30,000 characters. Upload a shorter version or enter the relevant experience below.')
    return text


class ResumeError(ValueError):
    """A readable PDF that cannot be imported as experience."""
