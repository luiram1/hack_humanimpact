import pytest

from matching import suggest
from models import content
from resume import extract_resume, MAX_RESUME_BYTES


def test_all_resume_pages_and_unpunctuated_bullets_are_used(resume_pdf):
    text = extract_resume(resume_pdf('Installed software\nCustomer support', 'Troubleshooting'))
    assert 'Installed software' in text
    assert 'Troubleshooting' in text
    matches = suggest(text, content('career')['skills'])
    assert any('Installed software' in match['sentence'] for match in matches)
    assert any('Troubleshooting' in match['sentence'] for match in matches)


def test_resume_over_old_limit_is_not_truncated(resume_pdf):
    text = extract_resume(resume_pdf('Experience ' * 400 + '\nInstalled software'))
    assert len(text) > 3000
    assert suggest(text, content('career')['skills'])


@pytest.mark.parametrize('data, message', [
    (b'', 'empty'),
    (b'not a PDF', 'not a PDF'),
    (b'%PDF-broken', 'could not be read'),
    (b'%PDF-' + b'x' * MAX_RESUME_BYTES, '5 MB'),
])
def test_invalid_uploads(data, message):
    with pytest.raises(ValueError, match=message):
        extract_resume(data)


def test_encrypted_blank_and_excessive_resumes(resume_pdf):
    for data, message in [
        (resume_pdf('Installed software', password='secret'), 'password protected'),
        (resume_pdf(''), 'no readable text'),
        (resume_pdf('Installed software', ''), 'no readable text'),
        (resume_pdf(*['Experience'] * 11), '10 pages'),
        (resume_pdf('x' * 30_001), '30,000 characters'),
    ]:
        with pytest.raises(ValueError, match=message):
            extract_resume(data)
