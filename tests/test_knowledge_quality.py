"""Quality checks for curated defensive-security knowledge sources."""
from pathlib import Path
import re

import pytest


KNOWLEDGE_DIR = Path(__file__).resolve().parents[1] / "knowledge"
URL_PATTERN = re.compile(r"https://[^\s)]+", re.IGNORECASE)


@pytest.mark.parametrize(
    ("filename", "trusted_domain"),
    [
        ("application-security.md", "owasp.org"),
        ("incident-response.md", "nist.gov"),
        ("secure-development.md", "nist.gov"),
        ("security-basics.md", "cisa.gov"),
    ],
)
def test_knowledge_documents_have_traceable_https_references(
    filename, trusted_domain
):
    document = (KNOWLEDGE_DIR / filename).read_text(encoding="utf-8")
    urls = URL_PATTERN.findall(document)

    assert urls, f"{filename} must include at least one source URL"
    assert all(url.startswith("https://") for url in urls)
    assert any(trusted_domain in url.lower() for url in urls)


@pytest.mark.parametrize(
    "filename",
    [
        "application-security.md",
        "incident-response.md",
        "secure-development.md",
        "security-basics.md",
    ],
)
def test_knowledge_documents_have_structured_actionable_content(filename):
    document = (KNOWLEDGE_DIR / filename).read_text(encoding="utf-8")
    sections = [line for line in document.splitlines() if line.startswith("## ")]

    assert document.startswith("# ")
    assert len(sections) >= 2
    assert len(document) >= 500
