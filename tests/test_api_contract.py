"""Testes de regressão para o contrato OpenAPI da API."""
from app.main import app


def test_openapi_documents_expected_api_endpoints():
    schema = app.openapi()

    assert schema["info"]["title"] == "Project Aether API"
    assert schema["info"]["version"] == "0.6.0"
    assert set(schema["paths"]) == {"/", "/health", "/analyze", "/review-code"}
    assert "get" in schema["paths"]["/"]
    assert "get" in schema["paths"]["/health"]
    assert "post" in schema["paths"]["/analyze"]
    assert "post" in schema["paths"]["/review-code"]


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
