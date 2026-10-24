import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import pytest
from io import BytesIO
from pypdf import PdfWriter
from pypdf.generic import DictionaryObject, NameObject, DecodedStreamObject


@pytest.fixture
def resume_pdf():
    """Build real, in-memory PDFs with text, without external fixtures."""
    def build(*pages, password=None):
        writer = PdfWriter()
        for text in pages:
            page = writer.add_blank_page(width=612, height=792)
            font = DictionaryObject({NameObject('/Type'): NameObject('/Font'),
                                     NameObject('/Subtype'): NameObject('/Type1'),
                                     NameObject('/BaseFont'): NameObject('/Helvetica')})
            page[NameObject('/Resources')] = DictionaryObject({
                NameObject('/Font'): DictionaryObject({NameObject('/F1'): font})})
            stream = DecodedStreamObject()
            escaped = text.replace('\\', '\\\\').replace('(', '\\(').replace(')', '\\)')
            commands = escaped.replace('\n', ') Tj 0 -16 Td (')
            stream.set_data(f'BT /F1 12 Tf 72 720 Td ({commands}) Tj ET'.encode())
            page.replace_contents(stream)
        if password:
            writer.encrypt(password)
        output = BytesIO()
        writer.write(output)
        return output.getvalue()
    return build
