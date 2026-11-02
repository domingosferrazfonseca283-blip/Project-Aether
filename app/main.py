"""API inicial do Project Aether.

Esta versão não executa código submetido nem realiza scans em sistemas.
"""
from typing import Literal

from fastapi import FastAPI
from pydantic import BaseModel, Field

from app.ai import get_provider

app = FastAPI(
    title="Project Aether API",
    description="Assistente de IA para cibersegurança defensiva e programação.",
    version="0.2.0",
)
provider = get_provider()


class AnalysisRequest(BaseModel):
    content: str = Field(min_length=1, max_length=20_000)
    category: Literal["cybersecurity", "programming", "general"] = "general"


class AnalysisResponse(BaseModel):
    category: str
    status: str
    provider: str
    guidance: list[str]


@app.get("/")
def root() -> dict[str, str]:
    return {
        "project": "Project Aether",
        "description": "Assistente de cibersegurança defensiva e programação",
        "version": "0.2.0",
    }


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


@app.post("/analyze", response_model=AnalysisResponse)
def analyze(request: AnalysisRequest) -> AnalysisResponse:
    """Devolve orientação inicial sem executar o conteúdo submetido."""
    return AnalysisResponse(
        category=request.category,
        status="starter_mode",
        provider="rule_based_placeholder",
        guidance=provider.guidance_for(request.category),
    )
