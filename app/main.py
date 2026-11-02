"""API do Project Aether. Não executa código nem realiza scans."""
from typing import Literal
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field
from app.ai import get_provider
from app.ai.ollama_provider import OllamaProviderError
from app.rag.retriever import retrieve

app = FastAPI(title="Project Aether API", description="Assistente de IA para cibersegurança defensiva e programação.", version="0.5.0")
provider = get_provider()

class AnalysisRequest(BaseModel):
    content: str = Field(min_length=1, max_length=20_000)
    category: Literal["cybersecurity", "programming", "general"] = "general"
class SourceResponse(BaseModel):
    title: str
    path: str
    excerpt: str
    reference: str
class AnalysisResponse(BaseModel):
    category: str
    status: str
    provider: str
    guidance: list[str]
    sources: list[SourceResponse]

@app.get("/")
def root() -> dict[str, str]:
    return {"project": "Project Aether", "description": "Assistente de cibersegurança defensiva e programação", "version": "0.5.0"}
@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}
@app.post("/analyze", response_model=AnalysisResponse)
def analyze(request: AnalysisRequest) -> AnalysisResponse:
    sources = retrieve(request.content)
    context = "\n\n".join(f"[Documento: {s.path} | Secção: {s.title}]\n{s.excerpt}" for s in sources)
    try:
        guidance = provider.analyze(request.content, request.category, context=context)
    except OllamaProviderError as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc
    return AnalysisResponse(category=request.category,
        status="completed" if provider.name == "ollama_local" else "starter_mode",
        provider=provider.name, guidance=guidance,
        sources=[SourceResponse(title=s.title, path=s.path, excerpt=s.excerpt, reference=s.reference) for s in sources])
