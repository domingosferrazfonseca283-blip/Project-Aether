from fastapi.testclient import TestClient

from app.main import app


client = TestClient(app)


def test_review_code_returns_static_findings():
    response = client.post(
        "/review-code",
        json={"content": "result = eval(user_input)"},
    )

    assert response.status_code == 200
    body = response.json()
    assert body["analysis_mode"] == "static_text_only"
    assert body["status"] == "completed"
    assert body["findings"][0]["rule_id"] == "PY001"
    assert body["findings"][0]["line"] == 1


def test_review_code_returns_empty_findings_for_safe_example():
    response = client.post(
        "/review-code",
        json={"content": "print('hello')"},
    )

    assert response.status_code == 200
    assert response.json()["findings"] == []


def test_review_code_rejects_blank_and_oversized_content():
    assert client.post("/review-code", json={"content": "  "}).status_code == 422
    assert client.post("/review-code", json={"content": "x" * 20_001}).status_code == 422
