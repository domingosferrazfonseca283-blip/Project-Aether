"""Testes de regressão para o contrato OpenAPI da API."""
from app.main import app


def test_openapi_documents_expected_api_endpoints():
    schema = app.openapi()

    assert schema["info"]["title"] == "Kamba API"
    assert schema["info"]["version"] == "0.6.0"
    assert set(schema["paths"]) == {"/", "/health", "/analyze", "/review-code", "/report"}
    assert "get" in schema["paths"]["/"]
    assert "get" in schema["paths"]["/health"]
    assert "post" in schema["paths"]["/analyze"]
    assert "post" in schema["paths"]["/review-code"]
    assert "post" in schema["paths"]["/report"]


def test_openapi_analysis_request_constraints_are_documented():
    schema = app.openapi()
    request_schema = schema["components"]["schemas"]["AnalysisRequest"]

    assert request_schema["required"] == ["content"]
    assert request_schema["properties"]["content"]["minLength"] == 1
    assert request_schema["properties"]["content"]["maxLength"] == 20_000
    assert request_schema["properties"]["category"]["enum"] == [
        "cybersecurity",
        "programming",
        "general",
    ]
    assert request_schema["properties"]["category"]["default"] == "general"


def test_openapi_analysis_response_exposes_stable_fields():
    schema = app.openapi()
    response_schema = schema["components"]["schemas"]["AnalysisResponse"]

    assert set(response_schema["properties"]) == {
        "category",
        "status",
        "provider",
        "guidance",
        "sources",
    }
    assert schema["paths"]["/analyze"]["post"]["responses"]["200"]
    assert schema["paths"]["/analyze"]["post"]["responses"]["422"]

def test_openapi_documents_typed_security_report_response():
    schema = app.openapi()
    report_schema = schema["components"]["schemas"]["SecurityReportResponse"]
    summary_schema = schema["components"]["schemas"]["SecurityReportSummary"]
    finding_schema = schema["components"]["schemas"]["FindingResponse"]
    severity_schema = schema["components"]["schemas"]["SeverityCounts"]

    assert set(report_schema["properties"]) == {
        "report_name", "generated_at", "analysis_mode", "summary", "findings"
    }
    assert set(summary_schema["properties"]) == {
        "findings_total", "severity_counts", "limitations"
    }
    assert set(severity_schema["properties"]) == {"high", "medium", "low"}
    assert finding_schema["properties"]["severity"]["enum"] == [
        "high", "medium", "low"
    ]
    assert finding_schema["properties"]["line"]["minimum"] == 1
    assert schema["paths"]["/report"]["post"]["responses"]["200"]

def test_openapi_documents_typed_code_review_response():
    schema = app.openapi()
    review_response = schema["components"]["schemas"]["CodeReviewResponse"]
    finding_schema = schema["components"]["schemas"]["FindingResponse"]

    assert set(review_response["properties"]) == {
        "status", "analysis_mode", "findings"
    }
    assert review_response["properties"]["findings"]["items"]["$ref"].endswith(
        "/FindingResponse"
    )
    assert finding_schema["properties"]["severity"]["enum"] == [
        "high", "medium", "low"
    ]
    assert schema["paths"]["/review-code"]["post"]["responses"]["200"]


def test_openapi_report_timestamp_uses_date_time_format():
    schema = app.openapi()
    report_schema = schema["components"]["schemas"]["SecurityReportResponse"]

    assert report_schema["properties"]["generated_at"]["format"] == "date-time"

