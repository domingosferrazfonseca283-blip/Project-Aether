"""Quality checks for curated defensive-security knowledge sources."""
from pathlib import Path
import re
from urllib.parse import urlsplit

import pytest


KNOWLEDGE_DIR = Path(__file__).resolve().parents[1] / "knowledge"
URL_PATTERN = re.compile(r"https://[^\s)>\]]+", re.IGNORECASE)


def _is_trusted_https_url(url: str, trusted_domains: tuple[str, ...]) -> bool:
    """Accept HTTPS URLs only when their parsed hostname is an approved domain."""
    try:
        parsed = urlsplit(url)
        hostname = parsed.hostname
        return (
            parsed.scheme.lower() == "https"
            and hostname is not None
            and parsed.username is None
            and parsed.password is None
            and any(
                hostname.lower() == domain
                or hostname.lower().endswith("." + domain)
                for domain in trusted_domains
            )
        )
    except ValueError:
        return False


@pytest.mark.parametrize(
    ("filename", "trusted_domains"),
    [
        ("application-security.md", ("owasp.org",)),
        ("incident-response.md", ("nist.gov", "cisa.gov")),
        ("secure-development.md", ("nist.gov",)),
        ("security-basics.md", ("nist.gov", "cisa.gov", "owasp.org")),
    ],
)
def test_knowledge_documents_have_traceable_https_references(
    filename, trusted_domains
):
    document = (KNOWLEDGE_DIR / filename).read_text(encoding="utf-8")
    urls = URL_PATTERN.findall(document)

    assert urls, f"{filename} must include at least one source URL"
    assert all(
        _is_trusted_https_url(url, trusted_domains) for url in urls
    ), f"{filename} contains a URL outside its approved HTTPS domains"


@pytest.mark.parametrize(
    ("url", "trusted_domains", "expected"),
    [
        ("https://nist.gov/publication", ("nist.gov",), True),
        ("https://csrc.nist.gov/publication", ("nist.gov",), True),
        ("http://nist.gov/publication", ("nist.gov",), False),
        ("https://nist.gov.example.com/publication", ("nist.gov",), False),
        ("https://notnist.gov/publication", ("nist.gov",), False),
        ("https://user:secret@nist.gov/publication", ("nist.gov",), False),
        ("https://example.com/publication", ("nist.gov",), False),
    ],
)
def test_trusted_reference_validation_rejects_untrusted_urls(
    url, trusted_domains, expected
):
    assert _is_trusted_https_url(url, trusted_domains) is expected


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
