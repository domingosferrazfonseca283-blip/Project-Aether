"""API do Project Aether. Não executa código nem realiza scans."""
from logging import getLogger
from time import perf_counter
from typing import Literal
from uuid import uuid4

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field, field_validator

from app.ai import get_provider
from app.ai.ollama_provider import OllamaProviderError
from app.core.config import get_settings
from app.rag.embeddings import OllamaEmbedder, OllamaEmbeddingError
from app.rag.retriever import retrieve


settings = get_settings()
logger = getLogger("project_aether.api")
app = FastAPI(
    title="Project Aether API",
    description="Assistente de IA para cibersegurança defensiva e programação.",
    version="0.6.0",
)


@app.middleware("http")
async def request_observability(request, call_next):
    """Regista metadados mínimos e aplica cabeçalhos HTTP de segurança."""
    request_id = str(uuid4())
    started = perf_counter()
    try:
        response = await call_next(request)
    except Exception as exc:
        logger.error(
            "request_failed request_id=%s method=%s path=%s error_type=%s duration_ms=%.2f",
            request_id,
            request.method,
            request.url.path,
            type(exc).__name__,
            (perf_counter() - started) * 1000,
        )
        raise

    response.headers["X-Request-ID"] = request_id
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["Referrer-Policy"] = "no-referrer"
    response.headers["Permissions-Policy"] = "camera=(), microphone=(), geolocation=()"
    if request.url.path == "/analyze":
        response.headers["Cache-Control"] = "no-store"

    logger.info(
        "request_completed request_id=%s method=%s path=%s status_code=%s duration_ms=%.2f",
        request_id,
        request.method,
        request.url.path,
        response.status_code,
        (perf_counter() - started) * 1000,
    )
    return response


provider = get_provider()
embedder = (
    OllamaEmbedder(settings)
    if settings.rag_provider == "ollama"
    else None
)


class AnalysisRequest(BaseModel):
    content: str = Field(min_length=1, max_length=20_000)
    category: Literal["cybersecurity", "programming", "general"] = "general"

    @field_validator("content")
    @classmethod
    def content_must_not_be_blank(cls, value: str) -> str:
        if not value.strip():
            raise ValueError("O conteúdo não pode conter apenas espaços.")
        return value


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
    return {
        "project": "Project Aether",
        "description": "Assistente de cibersegurança defensiva e programação",
        "version": "0.6.0",
    }


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


@app.post("/analyze", response_model=AnalysisResponse)
def analyze(request: AnalysisRequest) -> AnalysisResponse:
    try:
        sources = retrieve(request.content, embedder=embedder)
    except (OllamaEmbeddingError, ValueError):
        # A indisponibilidade de embeddings nunca impede a análise lexical.
        sources = retrieve(request.content)

    context = "\n\n".join(
        f"[Documento: {source.path} | Secção: {source.title}]\n{source.excerpt}"
        for source in sources
    )
    try:
        guidance = provider.analyze(
            request.content, request.category, context=context
        )
    except OllamaProviderError as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc

    return AnalysisResponse(
        category=request.category,
        status="completed" if provider.name == "ollama_local" else "starter_mode",
        provider=provider.name,
        guidance=guidance,
        sources=[
            SourceResponse(
                title=source.title,
                path=source.path,
                excerpt=source.excerpt,
                reference=source.reference,
            )
            for source in sources
        ],
    )
