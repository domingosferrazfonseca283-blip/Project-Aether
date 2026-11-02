from fastapi.testclient import TestClient

from app.main import app


client = TestClient(app)


def test_report_contains_summary_findings_and_limitations():
    response = client.post(
        "/report",
        json={"content": "result = eval(user_input)\npassword = \"example-secret-value\""},
    )

    assert response.status_code == 200
    report = response.json()
    assert report["report_name"].startswith("Kamba")
    assert report["analysis_mode"] == "static_text_only"
    assert report["summary"]["findings_total"] == 2
    assert report["summary"]["severity_counts"]["high"] == 1
    assert report["summary"]["severity_counts"]["medium"] == 1
    assert len(report["summary"]["limitations"]) >= 2
    assert set(report["summary"]["severity_counts"]) == {"high", "medium", "low"}
    assert all(item["line"] >= 1 for item in report["findings"])
    assert all(item["severity"] in {"high", "medium", "low"} for item in report["findings"])
    assert all(
        set(item) == {"rule_id", "severity", "line", "message", "recommendation"}
        for item in report["findings"]
    )
    assert all("example-secret-value" not in str(item) for item in report["findings"])


def test_report_rejects_blank_or_oversized_content():
    assert client.post("/report", json={"content": " "}).status_code == 422
    assert client.post("/report", json={"content": "x" * 20_001}).status_code == 422
