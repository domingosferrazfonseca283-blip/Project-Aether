"""Testes de invariantes adicionais dos relatórios Kamba."""
from datetime import datetime, timezone

from fastapi.testclient import TestClient

from app.main import app


client = TestClient(app)


def test_report_timestamp_is_timezone_aware_utc():
    response = client.post(
        "/report",
        json={"content": "value = eval(user_input)"},
    )

    assert response.status_code == 200
    timestamp = datetime.fromisoformat(response.json()["generated_at"])
    assert timestamp.tzinfo is not None
    assert timestamp.utcoffset() == timezone.utc.utcoffset(timestamp)


def test_report_severity_counts_match_returned_findings():
    response = client.post(
        "/report",
        json={
            "content": (
                "value = eval(user_input)\n"
                "password = \"example-secret-value\"\n"
                "print('hello')"
            )
        },
    )

    assert response.status_code == 200
    report = response.json()
    findings = report["findings"]
    counts = report["summary"]["severity_counts"]

    assert report["summary"]["findings_total"] == len(findings)
    assert sum(counts.values()) == len(findings)
    for severity in ("high", "medium", "low"):
        assert counts[severity] == sum(
            finding["severity"] == severity for finding in findings
        )
