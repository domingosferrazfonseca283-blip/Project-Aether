"""Initial API for Project Aether.

This starter version does not execute submitted code or perform live scans.
"""
from typing import Literal

from fastapi import FastAPI
from pydantic import BaseModel, Field

app = FastAPI(
    title="Project Aether API",
    description="Assistente de IA para cibersegurança defensiva e programação.",
    version="0.1.0",
)


class AnalysisRequest(BaseModel):
    content: str = Field(min_length=1, max_length=20_000)
    category: Literal["cybersecurity", "programming", "general"] = "general"


class AnalysisResponse(BaseModel):
    category: str
    status: str
    guidance: list[str]


@app.get("/")
def root() -> dict[str, str]:
    return {
        "project": "Project Aether",
        "description": "Assistente de cibersegurança defensiva e programação",
        "version": "0.1.0",
    }


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


@app.post("/analyze", response_model=AnalysisResponse)
def analyze(request: AnalysisRequest) -> AnalysisResponse:
    """Return safe starter guidance; model/RAG integration comes later."""
    guidance = [
        "Descreve o objetivo e o contexto do código ou sistema.",
        "Remove passwords, tokens, dados pessoais e outros segredos antes de partilhar.",
        "Para avaliações de segurança, trabalha apenas em sistemas com autorização.",
        "Esta versão não executa código, não explora sistemas e não confirma vulnerabilidades.",
    ]
    return AnalysisResponse(
        category=request.category,
        status="starter_mode",
        guidance=guidance,
    )
